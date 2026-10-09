from decimal import Decimal
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient
from catalog.models import Product, Category, Station
from orders.models import Order
from orders.services import create_demo_order
from production.services import approve_cancellation, transition_ticket
from .models import StockControl, Shift, Movement, Balance


class StockTests(TestCase):
    def setUp(self):
        cache.clear()
        call_command("setup_roles", verbosity=0)
        self.root = get_user_model().objects.create_superuser("root", password="test")
        self.chef = get_user_model().objects.create_user("chef", password="test")
        self.chef.groups.add(Group.objects.get(name="CHEF"))
        self.bar = get_user_model().objects.create_user("bar", password="test")
        self.bar.groups.add(Group.objects.get(name="BAR"))
        category = Category.objects.create(name="Platos")
        kitchen = Station.objects.create(code="KITCHEN", name="Cocina")
        bar = Station.objects.create(code="BAR", name="Barra")
        self.food = Product.objects.create(name="Plato", sku="P1", category=category, station=kitchen, sale_price=10, published=True)
        self.drink = Product.objects.create(name="Bebida", sku="B1", category=category, station=bar, sale_price=5, published=True)
        self.client = APIClient()
        self.client.force_authenticate(self.chef)

    def dash(self):
        response = self.client.get("/api/v1/stock/")
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def post(self, action, data):
        return self.client.post(f"/api/v1/stock/{action}/", data, format="json")

    def open(self, quantity=10):
        data = self.dash()
        payload = dict(key=str(uuid4()), revision=data["revision"], notes="Apertura", items=[dict(product_id=r["product_id"], keep=r["quantity"], production=quantity, reason="") for r in data["rows"]])
        response = self.post("open", payload)
        self.assertEqual(response.status_code, 200, response.data)
        return payload

    def checkout(self, qty=1, key=None):
        data = dict(customer_name="Cliente", fulfillment="PICKUP", table_label="", expected_total=Decimal(15 * qty), items=[dict(product_id=self.food.pk, quantity=qty), dict(product_id=self.drink.pk, quantity=qty)])
        return create_demo_order(data, key or uuid4())

    def movement(self, kind, quantity, key=None):
        return self.post("movements", dict(key=str(key or uuid4()), shift_id=self.dash()["shift"]["id"], product_id=self.food.pk, kind=kind, quantity=quantity, reason="Verificado"))

    def close_payload(self):
        data = self.dash()
        return dict(key=str(uuid4()), revision=data["revision"], shift_id=data["shift"]["id"], notes="Cierre", items=[dict(product_id=r["product_id"], counted=r["quantity"], reason="") for r in data["rows"]])

    def test_permissions_and_csrf(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/stock/").status_code, 403)
        self.client.force_authenticate(self.bar)
        self.assertEqual(self.client.get("/api/v1/stock/").status_code, 200)
        self.assertEqual(self.post("open", {}).status_code, 403)
        csrf = APIClient(enforce_csrf_checks=True)
        csrf.force_login(self.chef)
        self.assertEqual(csrf.post("/api/v1/stock/open/", {}).status_code, 403)

    def test_activation_idempotency_and_stock_formula(self):
        payload = self.open(20)
        self.assertEqual(self.post("open", payload).status_code, 200)
        self.assertEqual(Shift.objects.count(), 1)
        key = uuid4()
        self.assertEqual(self.movement("PRODUCTION", 10, key).status_code, 200)
        self.assertEqual(self.movement("PRODUCTION", 10, key).status_code, 200)
        self.assertEqual(self.movement("PRODUCTION", 11, key).status_code, 409)
        self.assertEqual(self.movement("WASTE", 2).status_code, 200)
        self.assertEqual(self.movement("ADJUST", -1).status_code, 200)
        row = next(r for r in self.dash()["rows"] if r["product_id"] == self.food.pk)
        self.assertEqual(row["quantity"], 27)
        self.assertEqual(row["initial"] + row["production"] - row["sales"] - row["waste"] + row["adjustments"], 27)
        self.assertEqual(self.movement("WASTE", 28).status_code, 409)
        self.assertEqual(Balance.objects.get(product=self.food).quantity, 27)

    def test_checkout_once_and_rejection_rolls_back_whole_order(self):
        self.open(1)
        key = uuid4()
        order, created = self.checkout(key=key)
        self.assertTrue(created)
        self.assertFalse(self.checkout(key=key)[1])
        self.assertEqual(Movement.objects.filter(kind="SALE").count(), 2)
        self.assertEqual(order.tickets.count(), 2)
        from .services import StockConflict
        with self.assertRaises(StockConflict):
            self.checkout()
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(list(Balance.objects.values_list("quantity", flat=True)), [0, 0])

    def test_cancellation_returns_only_unstarted_items_and_is_idempotent(self):
        self.open()
        order, _ = self.checkout(2)
        ticket = order.tickets.get(station_code="KITCHEN")
        transition_ticket(ticket.pk, self.chef, "IN_PROGRESS")
        approve_cancellation(order.pk, self.root, "Cliente cancela")
        approve_cancellation(order.pk, self.root, "Reintento")
        self.assertEqual(Balance.objects.get(product=self.food).quantity, 8)
        self.assertEqual(Balance.objects.get(product=self.drink).quantity, 10)
        self.assertEqual(Movement.objects.filter(kind="RETURN").count(), 1)
        self.assertEqual(Movement.objects.filter(kind="CANCEL_WASTE").count(), 1)
        data = self.dash()
        self.assertEqual(data["summary"]["sales"], 0)
        self.assertEqual(data["summary"]["waste"], 2)
        for row in data["rows"]:
            self.assertEqual(row["initial"] + row["production"] - row["sales"] - row["waste"] + row["adjustments"], row["quantity"])

    def test_later_line_shortage_rolls_back_earlier_consumption(self):
        self.open(1)
        payload = dict(key=str(uuid4()), shift_id=self.dash()["shift"]["id"], product_id=self.drink.pk, kind="WASTE", quantity=1, reason="Descarte")
        self.assertEqual(self.post("movements", payload).status_code, 200)
        from .services import StockConflict
        with self.assertRaises(StockConflict):
            self.checkout()
        self.assertEqual(Balance.objects.get(product=self.food).quantity, 1)
        self.assertFalse(Movement.objects.filter(kind="SALE").exists())
        self.assertFalse(Order.objects.exists())

    def test_stale_close_discrepancy_and_carryover_discard(self):
        self.open(5)
        stale = self.close_payload()
        self.movement("PRODUCTION", 1)
        self.assertEqual(self.post("close", stale).status_code, 409)
        close = self.close_payload()
        food = next(r for r in close["items"] if r["product_id"] == self.food.pk)
        food["counted"] = 4
        self.assertEqual(self.post("close", close).status_code, 400)
        food["reason"] = "Diferencia de conteo"
        self.assertEqual(self.post("close", close).status_code, 200)
        self.assertEqual(self.post("close", close).status_code, 200)
        from .services import StockConflict
        with self.assertRaises(StockConflict):
            self.checkout()
        data = self.dash()
        opened = dict(key=str(uuid4()), revision=data["revision"], items=[dict(product_id=r["product_id"], keep=0, production=0, reason="Caducidad") for r in data["rows"]])
        self.assertEqual(self.post("open", opened).status_code, 200)
        self.assertEqual(self.dash()["summary"]["waste"], 9)
        self.assertEqual(self.dash()["summary"]["quantity"], 0)
        history = self.client.get(f'/api/v1/stock/shifts/{close["shift_id"]}/').data
        row = next(r for r in history["rows"] if r["product_id"] == self.food.pk)
        self.assertEqual((row["theoretical"], row["counted"], row["difference"]), (6, 4, -2))

    def test_cannot_close_with_active_order_and_no_second_consumption_on_ready(self):
        self.open()
        order, _ = self.checkout()
        self.assertEqual(self.post("close", self.close_payload()).status_code, 409)
        for ticket in order.tickets.all():
            transition_ticket(ticket.pk, self.root, "IN_PROGRESS")
            transition_ticket(ticket.pk, self.root, "READY")
        self.assertEqual(Movement.objects.filter(kind="SALE").count(), 2)
        self.assertEqual(self.post("close", self.close_payload()).status_code, 200)

    def test_public_availability_and_history_remain_after_deactivation(self):
        self.assertIsNone(self.client.get("/api/v1/menu/stock/").data[self.food.pk])
        self.open(1)
        self.assertEqual(self.client.get("/api/v1/menu/stock/").data[self.food.pk], 1)
        self.checkout()
        self.assertEqual(self.client.get(f"/api/v1/menu/{self.food.pk}/").data["stock_quantity"], 0)
        self.food.published = False
        self.food.save()
        self.assertNotIn(self.food.pk, self.client.get("/api/v1/menu/stock/").data)
        history = self.client.get(f"/api/v1/stock/history/?product={self.food.pk}").data
        self.assertEqual(history["count"], 2)
        self.assertIn(self.food.pk, [r["product_id"] for r in self.dash()["rows"]])
