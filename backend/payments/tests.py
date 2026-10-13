from datetime import timedelta
from uuid import uuid4

from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from catalog.models import Category, Product, Station
from orders.models import Order
from orders.services import OrderConflict
from production.models import ProductionTicket
from stock.models import Balance, Movement, Shift, ShiftItem, StockControl
from stock.services import StockConflict, operate
from .models import Payment, PaymentAttempt, StockReservation
from .services import begin_attempt, expire_reservations


@override_settings(PAYMENTS_ENABLED=True, PAYMENTS_ENVIRONMENT="test")
class PaymentPreparationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="operator")
        category = Category.objects.create(name="Fondos")
        station = Station.objects.create(code="KITCHEN", name="Cocina")
        self.product = Product.objects.create(sku="PAY-1", name="Plato", category=category,
                                              station=station, published=True, sale_price="12.30")
        StockControl.objects.update_or_create(pk=1, defaults={"enabled": True})
        self.shift = Shift.objects.create(opened_by=self.user)
        Balance.objects.create(product=self.product, quantity=3)
        ShiftItem.objects.create(shift=self.shift, product=self.product, name="Plato", sku="PAY-1", initial=3)
        self.payload = {"customer_name": "Cliente", "fulfillment": "PICKUP",
                        "items": [{"product_id": self.product.pk, "quantity": 2}], "expected_total": "24.60"}

    def prepare(self, key=None, payload=None):
        return self.client.post("/api/v1/payments/prepare/", payload or self.payload,
                                format="json", HTTP_IDEMPOTENCY_KEY=str(key or uuid4()))

    def test_prepare_idempotent_private_and_no_production_or_consumption(self):
        key = uuid4()
        response = self.prepare(key)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["amount_minor"], 2460)
        self.assertEqual(response.data["payment_status"], "PENDING")
        self.assertFalse(response.data["charging_available"])
        self.assertEqual(self.prepare(key).status_code, 200)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(StockReservation.objects.count(), 1)
        self.assertEqual(Balance.objects.get().quantity, 3)
        self.assertFalse(Movement.objects.exists())
        self.assertFalse(ProductionTicket.objects.exists())
        menu = self.client.get("/api/v1/menu/")
        self.assertEqual(menu.data["results"][0]["stock_quantity"], 1)
        detail = self.client.get(f"/api/v1/payments/{response.data['public_code']}/")
        self.assertEqual(detail.status_code, 200)
        for secret in ["customer_name", "table_label", "request_hash", "idempotency_key"]:
            self.assertNotIn(secret, detail.data)
        self.assertEqual(self.client.get(f"/api/v1/orders/{response.data['public_code']}/").status_code, 404)
        self.assertEqual(self.prepare(key, {**self.payload, "customer_name": "Otro"}).status_code, 409)

    def test_other_reservations_demo_and_adjustments_cannot_take_held_units(self):
        self.assertEqual(self.prepare().status_code, 201)
        self.assertEqual(self.prepare().status_code, 409)
        response = self.client.post("/api/v1/orders/", {**self.payload, "accept_demo": True},
                                    format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))
        self.assertEqual(response.status_code, 409, response.data)
        with self.assertRaises(StockConflict):
            operate("movement", {"key": uuid4(), "shift_id": self.shift.pk,
                                 "product_id": self.product.pk, "quantity": 2, "kind": "WASTE", "reason": "Prueba"}, self.user)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Balance.objects.get().quantity, 3)

    def test_expiration_releases_without_movements_and_replay_does_not_recreate(self):
        key = uuid4()
        self.prepare(key)
        StockReservation.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(expire_reservations(), 1)
        self.assertEqual(expire_reservations(), 0)
        response = self.prepare(key)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["payment_status"], "EXPIRED")
        self.assertEqual(self.client.get("/api/v1/menu/").data["results"][0]["stock_quantity"], 3)
        self.assertFalse(Movement.objects.exists())

    def test_processing_is_not_expired_and_cannot_start_twice(self):
        self.prepare()
        order = Order.objects.get()
        key = uuid4()
        attempt = begin_attempt(order.pk, key)
        self.assertEqual(begin_attempt(order.pk, key).pk, attempt.pk)
        with self.assertRaises(OrderConflict):
            begin_attempt(order.pk, uuid4())
        StockReservation.objects.update(expires_at=timezone.now() - timedelta(days=1))
        self.assertEqual(expire_reservations(), 0)
        self.assertEqual(PaymentAttempt.objects.count(), 1)
        self.assertEqual(StockReservation.objects.get().status, "PROCESSING")
        self.assertFalse(ProductionTicket.objects.exists())

    def test_expired_reservation_cannot_start_payment(self):
        self.prepare()
        StockReservation.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        with self.assertRaises(OrderConflict):
            begin_attempt(Order.objects.get().pk, uuid4())
        self.assertFalse(PaymentAttempt.objects.exists())

    def test_shift_cannot_close_with_reservations(self):
        self.prepare()
        with self.assertRaises(StockConflict):
            operate("close", {"key": uuid4(), "revision": StockControl.objects.get(pk=1).revision,
                              "shift_id": self.shift.pk, "items": [], "notes": ""}, self.user)
        self.shift.refresh_from_db()
        self.assertIsNone(self.shift.closed_at)

    def test_price_change_or_inactive_control_rolls_back(self):
        self.assertEqual(self.prepare(payload={**self.payload, "expected_total": "1.00"}).status_code, 409)
        StockControl.objects.filter(pk=1).update(enabled=False)
        self.assertEqual(self.prepare().status_code, 409)
        self.assertFalse(Order.objects.exists())

    @override_settings(PAYMENTS_ENABLED=False)
    def test_disabled_by_default(self):
        self.assertEqual(self.prepare().status_code, 403)
        self.assertFalse(Order.objects.exists())

    @override_settings(PAYMENTS_ENVIRONMENT="live")
    def test_live_not_yet_available(self):
        self.assertEqual(self.prepare().status_code, 403)
        self.assertFalse(Order.objects.exists())
