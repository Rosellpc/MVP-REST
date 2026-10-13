from copy import deepcopy
from unittest.mock import patch
from uuid import uuid4
from django.test import override_settings
from rest_framework.test import APITestCase
from orders.models import Order
from orders.services import OrderConflict
from production.models import ProductionTicket
from stock.models import Balance, Movement
from . import tests as preparation, culqi
from .models import Payment, PaymentAttempt, StockReservation
from .processing import submit_charge, verify_charge, reconcile, abandon_unsubmitted


@override_settings(PAYMENTS_ENABLED=True, PAYMENTS_ENVIRONMENT="test", CULQI_PUBLIC_KEY="pk_test_fixture", CULQI_SECRET_KEY="sk_test_fixture")
class ChargeTests(APITestCase):
    setUp = preparation.PaymentPreparationTests.setUp
    prepare = preparation.PaymentPreparationTests.prepare

    def start(self, response=None):
        self.prepare()
        self.order = Order.objects.get()
        self.key = uuid4()
        self.data = {"source_id": "tkn_test_fixture", "email": "test@example.com", "device_id": "device-fixture"}
        with patch("payments.culqi.api", return_value=response or (200, {"action_code": "REVIEW"})):
            submit_charge(self.order.pk, self.key, self.data)
        self.attempt = PaymentAttempt.objects.get()

    def charge(self):
        return {"object": "charge", "id": "chr_test_fixture", "amount": 2460, "currency_code": "PEN",
                "metadata": {"order_code": str(self.order.public_code), "attempt_key": str(self.key)},
                "source": {"id": self.data["source_id"]}, "capture": True, "amount_refunded": 0,
                "outcome": {"type": "venta_exitosa"}, "paid": False}

    def test_verified_charge_consumes_once_and_releases_test_tickets(self):
        self.start()
        verify_charge(self.attempt.pk, self.charge())
        verify_charge(self.attempt.pk, self.charge())
        self.assertEqual(Payment.objects.get().status, "PAID")
        self.assertEqual(StockReservation.objects.get().status, "CONSUMED")
        self.assertEqual(Balance.objects.get().quantity, 1)
        self.assertEqual(Movement.objects.filter(kind="SALE").count(), 1)
        self.assertEqual(ProductionTicket.objects.count(), 1)
        result = self.client.get(f"/api/v1/orders/{self.order.public_code}/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["payment_environment"], "test")

    def test_configuration_never_exposes_secret_key(self):
        result = self.client.get("/api/v1/payments/config/")
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data["ready"])
        self.assertEqual(result.data["public_key"], "pk_test_fixture")
        self.assertNotIn("sk_test_fixture", str(result.data))

    def test_foreign_amount_currency_source_metadata_and_live_are_rejected(self):
        self.start()
        for field, value in [("amount", 1), ("currency_code", "USD"), ("source", {"id": "tkn_test_other"}),
                             ("metadata", {}), ("id", "chr_live_no")]:
            with self.subTest(field=field), self.assertRaises(OrderConflict):
                verify_charge(self.attempt.pk, {**self.charge(), field: value})
        self.assertFalse(ProductionTicket.objects.exists())
        self.assertEqual(Balance.objects.get().quantity, 3)

    def test_authorization_without_capture_does_not_release(self):
        self.start()
        verify_charge(self.attempt.pk, {**self.charge(), "capture": False})
        self.assertFalse(ProductionTicket.objects.exists())
        self.assertNotEqual(Payment.objects.get().status, "PAID")

    def test_3ds_reuses_binding_and_initial_replay_does_not_post(self):
        self.start()
        authentication = {"eci": "05", "xid": "x", "cavv": "c", "protocolVersion": "2.1.0"}
        with patch("payments.culqi.api") as api:
            submit_charge(self.order.pk, self.key, self.data)
            api.assert_not_called()
            with self.assertRaises(OrderConflict):
                submit_charge(self.order.pk, self.key, {**self.data, "device_id": "different", "authentication_3DS": authentication})
            api.assert_not_called()
        with patch("payments.culqi.api", return_value=(201, self.charge())) as api, patch("payments.culqi.get_charge", return_value=self.charge()):
            submit_charge(self.order.pk, self.key, {**self.data, "authentication_3DS": authentication})
            body = api.call_args.args[2]
            self.assertEqual(body["authentication_3DS"], authentication)
            self.assertEqual(body["amount"], 2460)
            self.assertEqual(body["antifraud_details"]["device_finger_print_id"], self.data["device_id"])
        self.assertEqual(Payment.objects.get().status, "PAID")

    def test_timeout_retains_stock_and_never_reposts(self):
        self.prepare()
        order = Order.objects.get()
        key = uuid4()
        data = {"source_id": "tkn_test_fixture", "email": "test@example.com", "device_id": "device"}
        with patch("payments.culqi.api", side_effect=culqi.CulqiUnavailable()) as api:
            with self.assertRaises(culqi.CulqiUnavailable):
                submit_charge(order.pk, key, data)
            submit_charge(order.pk, key, data)
            self.assertEqual(api.call_count, 1)
        self.assertEqual(Payment.objects.get().status, "UNKNOWN")
        self.assertEqual(StockReservation.objects.get().status, "PROCESSING")

    def test_reconcile_finds_charge_after_lost_response(self):
        self.start((202, {}))
        with patch("payments.culqi.list_charges", return_value={"data": [self.charge()]}), patch("payments.culqi.get_charge", return_value=self.charge()):
            reconcile(self.attempt.pk)
        self.assertEqual(Payment.objects.get().status, "PAID")

    def test_no_charge_found_does_not_release_uncertain_reservation(self):
        self.start((202, {}))
        with patch("payments.culqi.list_charges", return_value={"data": []}):
            reconcile(self.attempt.pk)
        self.assertEqual(Payment.objects.get().status, "UNKNOWN")
        self.assertEqual(StockReservation.objects.get().status, "PROCESSING")

    def test_decline_releases_hold_without_tickets(self):
        self.start((400, {"type": "card_error", "decline_code": "insufficient_funds"}))
        self.assertEqual(Payment.objects.get().status, "FAILED")
        self.assertEqual(StockReservation.objects.get().status, "RELEASED")
        self.assertFalse(ProductionTicket.objects.exists())
        self.assertEqual(Balance.objects.get().quantity, 3)

    def test_abandoned_authentication_releases_but_unknown_payment_does_not(self):
        self.start()
        abandon_unsubmitted(self.order.pk)
        self.assertEqual(StockReservation.objects.get().status, "RELEASED")
        self.assertEqual(Payment.objects.get().status, "FAILED")
        with patch("payments.culqi.api") as api:
            submit_charge(self.order.pk, self.key, {**self.data, "authentication_3DS": {"eci": "05"}})
            api.assert_not_called()

    def test_cannot_abandon_unknown_payment(self):
        self.start((202, {}))
        with self.assertRaises(OrderConflict):
            abandon_unsubmitted(self.order.pk)
        self.assertEqual(StockReservation.objects.get().status, "PROCESSING")

    def test_production_failure_rolls_back_settlement_then_reconciles(self):
        self.start()
        with patch("production.services.TicketEvent.objects.create", side_effect=RuntimeError("failed")):
            with self.assertRaises(RuntimeError):
                verify_charge(self.attempt.pk, self.charge())
        self.assertNotEqual(Payment.objects.get().status, "PAID")
        self.assertEqual(StockReservation.objects.get().status, "PROCESSING")
        self.assertFalse(Movement.objects.exists())
        verify_charge(self.attempt.pk, self.charge())
        self.assertEqual(ProductionTicket.objects.count(), 1)

    def test_webhook_uses_fetched_charge_not_notification_values(self):
        self.start()
        forged = deepcopy(self.charge())
        with patch("payments.culqi.get_charge", return_value={**forged, "amount": 1}):
            result = self.client.post("/api/v1/payments/culqi/webhook/", {"data": forged}, format="json")
            self.assertEqual(result.status_code, 409)
        self.assertFalse(ProductionTicket.objects.exists())
        with patch("payments.culqi.get_charge", return_value=forged):
            for _ in range(2):
                self.assertEqual(self.client.post("/api/v1/payments/culqi/webhook/", {"data": forged}, format="json").status_code, 200)
        self.assertEqual(ProductionTicket.objects.count(), 1)

    @override_settings(CULQI_SECRET_KEY="sk_live_not_allowed")
    def test_live_credentials_never_sent(self):
        with patch("payments.culqi.build_opener") as opener:
            with self.assertRaises(culqi.CulqiUnavailable):
                culqi.api("POST", "charges", {})
            opener.assert_not_called()
