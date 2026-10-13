from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import override_settings

from orders.models import Order
from orders.services import OrderConflict, create_demo_order
from stock.models import Balance, Movement
from stock.services import StockConflict
from stock import test_concurrency as stock_concurrency
from .models import StockReservation
from .services import create_pending_order
from .processing import submit_charge, verify_charge, digest
from .models import PaymentAttempt
from production.models import ProductionTicket


@override_settings(PAYMENTS_ENABLED=True, PAYMENTS_ENVIRONMENT="test")
class PaymentConcurrencyTests(stock_concurrency.StockConcurrencyTests):
    # Reuse isolated last-unit setup and retain demo concurrency regression tests.
    def race(self, callbacks):
        barrier = Barrier(len(callbacks))
        def run(callback):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return callback()
            finally:
                connection.close()
        with ThreadPoolExecutor(max_workers=len(callbacks)) as pool:
            return list(pool.map(run, callbacks))

    def payload(self):
        return dict(customer_name="Test", fulfillment="PICKUP", table_label="",
                    expected_total=Decimal("10"), items=[dict(product_id=self.product.pk, quantity=1)])

    def test_reservation_and_demo_compete_for_last_unit(self):
        def reserve():
            try:
                create_pending_order(self.payload(), uuid4())
                return "reserved"
            except OrderConflict:
                return "out"
        def buy():
            try:
                create_demo_order(self.payload(), uuid4())
                return "sold"
            except StockConflict:
                return "out"
        results = self.race([reserve, buy])
        self.assertEqual(results.count("out"), 1)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(StockReservation.objects.count() + Movement.objects.filter(kind="SALE").count(), 1)

    def test_same_key_reserves_once(self):
        key = uuid4()
        def reserve():
            order, created = create_pending_order(self.payload(), key)
            return order.pk, created
        results = self.race([reserve, reserve])
        self.assertEqual(results[0][0], results[1][0])
        self.assertCountEqual([result[1] for result in results], [True, False])
        self.assertEqual(StockReservation.objects.count(), 1)
        self.assertEqual(Balance.objects.get(product=self.product).quantity, 1)

    @override_settings(CULQI_PUBLIC_KEY="pk_test_fixture", CULQI_SECRET_KEY="sk_test_fixture")
    def test_simultaneous_charge_requests_only_post_once(self):
        order, _ = create_pending_order(self.payload(), uuid4())
        key = uuid4()
        data = {"source_id": "tkn_test_fixture", "email": "test@example.com", "device_id": "device"}
        with patch("payments.culqi.api", return_value=(200, {"action_code": "REVIEW"})) as api:
            self.race([lambda: submit_charge(order.pk, key, data)] * 2)
            self.assertEqual(api.call_count, 1)

    def test_simultaneous_verifications_release_once(self):
        order, _ = create_pending_order(self.payload(), uuid4())
        from .services import begin_attempt
        attempt = begin_attempt(order.pk, uuid4())
        attempt.source_fingerprint = digest("tkn_test_fixture")
        attempt.save(update_fields=["source_fingerprint"])
        charge = {"object": "charge", "id": "chr_test_fixture", "amount": 1000, "currency_code": "PEN",
                  "capture": True, "source": {"id": "tkn_test_fixture"}, "amount_refunded": 0,
                  "metadata": {"order_code": str(order.public_code), "attempt_key": str(attempt.key)},
                  "outcome": {"type": "venta_exitosa"}}
        self.race([lambda: verify_charge(attempt.pk, charge)] * 2)
        self.assertEqual(ProductionTicket.objects.count(), 1)
        self.assertEqual(Movement.objects.filter(kind="SALE").count(), 1)
        self.assertEqual(PaymentAttempt.objects.get().status, "PAID")
