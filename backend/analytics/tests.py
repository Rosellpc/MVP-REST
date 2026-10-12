from datetime import datetime, timezone as tz, timedelta
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework.test import APIClient
from catalog.models import Product, Category, Station
from costing.models import Recipe, RecipeVersion
from orders.models import Order, OrderItem
from production.models import ProductionTicket


class DashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("manager")
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label="accounts", codename="access_staff"))
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        category = Category.objects.create(name="Platos")
        station = Station.objects.create(code="KITCHEN", name="Cocina")
        self.product = Product.objects.create(name="Plato", sku="METRIC", sale_price=10, category=category, station=station, published=True)
        self.url = "/api/v1/dashboard/summary/?start=2025-01-02&end=2025-01-03"

    def order(self, total=10, status="READY", date=None):
        order = Order.objects.create(idempotency_key=uuid4(), request_hash="x", customer_name="Private", fulfillment="PICKUP", total=total, production_status=status)
        Order.objects.filter(pk=order.pk).update(created_at=date or datetime(2025, 1, 2, 5, tzinfo=tz.utc))
        OrderItem.objects.create(order=order, product=self.product, name="Plato histórico", station_code="KITCHEN", quantity=1, unit_price=total, line_total=total)
        return order

    def test_permissions_read_only_and_no_customer_data(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        other = get_user_model().objects.create_user("kitchen")
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_authenticate(self.user)
        self.order()
        self.assertEqual(self.client.post(self.url, {}).status_code, 405)
        self.assertNotIn("Private", str(self.client.get(self.url).data))

    def test_period_timezone_cancelled_and_previous_period(self):
        self.order(10)
        self.order(20, "PENDING", datetime(2025, 1, 4, 4, 59, tzinfo=tz.utc))
        self.order(70, "CANCELLED")
        self.order(80, "PARTIALLY_CANCELLED")
        self.order(15, date=datetime(2025, 1, 2, 4, 59, tzinfo=tz.utc))
        self.order(100, date=datetime(2025, 1, 4, 5, tzinfo=tz.utc))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["metrics"]["amount"], "30.00")
        self.assertEqual(data["metrics"]["average_ticket"], "15.00")
        self.assertEqual(data["metrics"]["orders"], 2)
        self.assertEqual(data["metrics"]["all_orders"], 4)
        self.assertEqual(data["metrics"]["cancelled"], 1)
        self.assertEqual(data["metrics"]["partial_excluded"], 1)
        self.assertEqual(data["metrics"]["change_percent"], "100.00")
        self.assertEqual([row["amount"] for row in data["trend"]], ["10.00", "20.00"])
        self.assertEqual(data["top_products"][0]["quantity"], 2)
        self.assertEqual(data["top_products"][0]["amount"], "30.00")
        self.assertEqual(data["channels"][0]["count"], 2)

    def test_empty_data_and_pending_costs_are_not_zero_cost(self):
        recipe = Recipe.objects.create(name="Draft", current_version=1)
        RecipeVersion.objects.create(recipe=recipe, number=1, snapshot={"per_portion": None, "pending_costing": True, "food_cost_percent": None})
        data = self.client.get(self.url).data
        self.assertEqual(data["metrics"]["amount"], "0.00")
        self.assertIsNone(data["metrics"]["average_ticket"])
        self.assertIsNone(data["metrics"]["change_percent"])
        self.assertEqual(data["costing"]["pending"], 1)
        self.assertEqual(data["costing"]["costed"], 0)
        self.assertIsNone(data["costing"]["average_food_cost"])
        self.assertEqual(len(data["trend"]), 2)
        self.assertFalse(data["stock"]["enabled"])

    def test_preparation_time_uses_completed_tickets_not_creation_date(self):
        order = self.order(date=datetime(2024, 12, 31, 12, tzinfo=tz.utc))
        start = datetime(2025, 1, 2, 10, tzinfo=tz.utc)
        ticket = ProductionTicket.objects.create(order=order, station_code="KITCHEN", status="READY", started_at=start, completed_at=start + timedelta(minutes=12), archived_at=start + timedelta(minutes=15))
        ProductionTicket.objects.filter(pk=ticket.pk).update(created_at=start - timedelta(minutes=5))
        data = self.client.get(self.url).data
        kitchen = data["stations"][0]
        self.assertEqual(kitchen["average_minutes"], 17)
        self.assertEqual(kitchen["completed_sample"], 1)
        self.assertEqual(kitchen["ready"], 0)

    def test_invalid_ranges(self):
        for query in ["start=bad", "start=2025-02-01&end=2025-01-01", "start=2023-01-01&end=2025-01-01", "end=2999-01-01"]:
            self.assertEqual(self.client.get("/api/v1/dashboard/summary/?" + query).status_code, 400)
