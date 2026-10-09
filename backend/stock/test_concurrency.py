from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import TransactionTestCase, skipUnlessDBFeature
from catalog.models import Category, Station, Product
from orders.models import Order
from orders.services import create_demo_order
from .models import StockControl, Balance, Movement
from .services import operate, StockConflict


@skipUnlessDBFeature("has_select_for_update")
class StockConcurrencyTests(TransactionTestCase):
    def setUp(self):
        StockControl.objects.get_or_create(pk=1)
        self.actor = get_user_model().objects.create_user("stock-test")
        category = Category.objects.create(name="Concurrency")
        station = Station.objects.create(code="KITCHEN", name="Cocina")
        self.product = Product.objects.create(sku="CONCURRENT", name="Last unit", sale_price=10, category=category, station=station, published=True)
        operate("open", dict(key=uuid4(), revision=0, notes="", items=[dict(product_id=self.product.pk, keep=0, production=1, reason="")]), self.actor)

    def test_two_checkouts_cannot_sell_the_same_last_unit(self):
        barrier = Barrier(2)
        def buy(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                create_demo_order(dict(customer_name="Test", fulfillment="PICKUP", table_label="", expected_total=Decimal("10"), items=[dict(product_id=self.product.pk, quantity=1)]), uuid4())
                return "sold"
            except StockConflict:
                return "out"
            finally:
                connection.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(buy, range(2)))
        self.assertCountEqual(results, ["sold", "out"])
        self.assertEqual(Balance.objects.get(product=self.product).quantity, 0)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Movement.objects.filter(kind="SALE").count(), 1)

    def test_repeated_simultaneous_request_consumes_once(self):
        barrier, key = Barrier(2), uuid4()
        def buy(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                order, created = create_demo_order(dict(customer_name="Test", fulfillment="PICKUP", table_label="", expected_total=Decimal("10"), items=[dict(product_id=self.product.pk, quantity=1)]), key)
                return order.pk, created
            finally:
                connection.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(buy, range(2)))
        self.assertEqual(results[0][0], results[1][0])
        self.assertCountEqual([r[1] for r in results], [True, False])
        self.assertEqual(Movement.objects.filter(kind="SALE").count(), 1)
