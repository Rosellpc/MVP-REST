from decimal import Decimal
from uuid import uuid4

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from catalog.models import Category, Product, Station
from .models import Order, OrderItem


class DemoCheckoutTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Platos")
        cls.station = Station.objects.create(code="KITCHEN", name="Cocina")
        cls.product = Product.objects.create(
            sku="ORDER-001", name="Ceviche", sale_price=Decimal("25.50"),
            category=cls.category, station=cls.station, published=True,
        )

    def setUp(self):
        cache.clear()
        self.payload = {
            "items": [{"product_id": self.product.pk, "quantity": 2}],
            "customer_name": "Cliente de prueba", "fulfillment": "DINE_IN",
            "table_label": "12", "expected_total": "51.00", "accept_demo": True,
        }
        self.key = str(uuid4())

    def create_order(self, payload=None, key=None):
        return self.client.post(reverse("orders:create"), payload or self.payload,
                                format="json", HTTP_IDEMPOTENCY_KEY=key or self.key)

    def test_preview_recalculates_prices_and_does_not_create_order(self):
        response = self.client.post(reverse("orders:preview"), {
            "items": [{"product_id": self.product.pk, "quantity": 2, "unit_price": "0.01"}],
            "total": "0.02",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], "51.00")
        self.assertEqual(response.data["items"][0]["unit_price"], "25.50")
        self.assertEqual(Order.objects.count(), 0)

    def test_confirm_and_public_lookup_preserve_snapshot_and_hide_personal_data(self):
        response = self.create_order()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["demo"])
        self.assertEqual(response.data["payment_status"], "SIMULATED")
        self.assertEqual(response.data["status"], "DEMO_CONFIRMED")
        self.assertEqual(response.data["currency"], "PEN")
        self.assertEqual(response.data["total"], "51.00")
        self.assertEqual(OrderItem.objects.get().station_code, "KITCHEN")
        Product.objects.filter(pk=self.product.pk).update(name="Nombre nuevo", sale_price="99.00")
        detail = self.client.get(reverse("orders:detail", args=[response.data["public_code"]]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["items"][0]["name"], "Ceviche")
        self.assertEqual(detail.data["total"], "51.00")
        for field in ["customer_name", "table_label", "idempotency_key", "id"]:
            self.assertNotIn(field, detail.data)

    def test_retry_returns_same_order_even_if_product_becomes_unavailable(self):
        first = self.create_order()
        Product.objects.filter(pk=self.product.pk).update(available=False)
        repeated = self.create_order()
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(first.data["public_code"], repeated.data["public_code"])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_same_key_with_other_payload_is_rejected(self):
        self.create_order()
        self.payload["customer_name"] = "Otra persona"
        self.assertEqual(self.create_order().status_code, 409)
        self.assertEqual(Order.objects.count(), 1)

    def test_price_change_rolls_back_and_requires_new_confirmation(self):
        Product.objects.filter(pk=self.product.pk).update(sale_price="30.00")
        self.assertEqual(self.create_order().status_code, 409)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(OrderItem.objects.exists())

    def test_unavailable_product_rolls_back_order(self):
        Product.objects.filter(pk=self.product.pk).update(available=False)
        self.assertEqual(self.create_order().status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_inactive_category_and_station_are_rejected(self):
        for obj in [self.category, self.station]:
            with self.subTest(model=type(obj).__name__):
                obj.active = False
                obj.save()
                self.assertEqual(self.create_order().status_code, 400)
                self.assertFalse(Order.objects.exists())
                obj.active = True
                obj.save()

    def test_empty_duplicate_and_invalid_quantities_are_rejected(self):
        for items in [[], self.payload["items"] * 2,
                      [{"product_id": self.product.pk, "quantity": 0}],
                      [{"product_id": self.product.pk, "quantity": 100}],
                      [{"product_id": self.product.pk, "quantity": 1.5}]]:
            with self.subTest(items=items):
                self.assertEqual(self.create_order({**self.payload, "items": items}).status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_requires_name_table_demo_acceptance_and_idempotency_key(self):
        for overrides in [{"customer_name": " "}, {"table_label": ""}, {"accept_demo": False}]:
            with self.subTest(overrides=overrides):
                self.assertEqual(self.create_order({**self.payload, **overrides}).status_code, 400)
        self.assertEqual(self.client.post(reverse("orders:create"), self.payload, format="json").status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_pickup_does_not_require_table(self):
        self.payload.update(fulfillment="PICKUP", table_label="")
        self.assertEqual(self.create_order().status_code, 201)
        self.assertEqual(Order.objects.get().table_label, "")

    def test_random_public_code_is_not_found(self):
        self.assertEqual(self.client.get(reverse("orders:detail", args=[uuid4()])).status_code, 404)

    @override_settings(ORDER_DEMO_ENABLED=False)
    def test_demo_can_be_disabled(self):
        self.assertEqual(self.create_order().status_code, 403)
        self.assertFalse(Order.objects.exists())
