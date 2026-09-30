from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Category, Product, Station
from .views import MenuThrottle


class MenuAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Platos", display_order=2)
        cls.drinks = Category.objects.create(name="Bebidas", display_order=1)
        cls.station = Station.objects.create(code="KITCHEN", name="Cocina")
        cls.product = Product.objects.create(
            sku="TEST-001",
            name="Pasta",
            description="Pasta con verduras",
            category=cls.category,
            station=cls.station,
            sale_price=Decimal("25.50"),
            published=True,
        )

    def setUp(self):
        cache.clear()
        self.url = reverse("catalog:menu")

    def test_anonymous_menu_contract_and_decimal_price(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [{
                "id": self.product.pk,
                "name": "Pasta",
                "description": "Pasta con verduras",
                "image_url": "",
                "category": {"id": self.category.pk, "name": "Platos"},
                "sale_price": "25.50",
            }],
        })

    def test_unpublished_and_unavailable_products_cannot_be_requested(self):
        for field in ("published", "available"):
            with self.subTest(field=field):
                Product.objects.filter(pk=self.product.pk).update(**{field: False})
                response = self.client.get(self.url, {
                    "category": self.category.pk,
                    "published": "false",
                    "available": "false",
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["results"], [])
                Product.objects.filter(pk=self.product.pk).update(**{field: True})

    def test_inactive_categories_and_stations_are_excluded(self):
        for instance in (self.category, self.station):
            with self.subTest(model=type(instance).__name__):
                instance.active = False
                instance.save(update_fields=["active"])
                self.assertEqual(self.client.get(self.url).json()["count"], 0)
                instance.active = True
                instance.save(update_fields=["active"])

    def test_category_filter(self):
        response = self.client.get(self.url, {"category": self.category.pk})
        self.assertEqual(response.json()["count"], 1)
        for category_id in (self.drinks.pk, 9223372036854775807):
            with self.subTest(category_id=category_id):
                response = self.client.get(self.url, {"category": category_id})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["results"], [])

    def test_invalid_category_returns_400(self):
        for value in ("abc", "", "0", "-1", "1.5", "9223372036854775808"):
            with self.subTest(value=value):
                response = self.client.get(self.url, {"category": value})
                self.assertEqual(response.status_code, 400)
                self.assertIn("category", response.json())

    def test_empty_menu(self):
        Product.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "count": 0, "next": None, "previous": None, "results": [],
        })

    def test_write_methods_are_rejected_without_changing_products(self):
        before = list(Product.objects.values())
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    self.url, {"name": "Changed", "sale_price": "0.00"}, format="json"
                )
                self.assertEqual(response.status_code, 405)
        self.assertEqual(list(Product.objects.values()), before)

    def test_pagination_category_order_and_no_repeated_category_queries(self):
        Product.objects.bulk_create([
            Product(
                sku=f"DRINK-{index:02d}", name="Agua", category=self.drinks,
                station=self.station, sale_price=Decimal("3.00"), published=True,
            )
            for index in range(21)
        ])
        with self.assertNumQueries(2):
            first = self.client.get(self.url).json()
        self.assertEqual(first["count"], 22)
        self.assertEqual(len(first["results"]), 20)
        self.assertIsNotNone(first["next"])
        self.assertIsNone(first["previous"])
        self.assertTrue(all(p["category"]["id"] == self.drinks.pk for p in first["results"]))

        second = self.client.get(self.url, {"page": 2}).json()
        self.assertEqual(len(second["results"]), 2)
        self.assertIsNone(second["next"])
        self.assertIsNotNone(second["previous"])
        self.assertEqual(second["results"][-1]["id"], self.product.pk)
        ids = [p["id"] for p in first["results"] + second["results"]]
        self.assertEqual(len(set(ids)), 22)
        self.assertEqual(self.client.get(self.url, {"page": 3}).status_code, 404)

    def test_rate_limit(self):
        with patch.object(MenuThrottle, "rate", "2/min"):
            self.assertEqual(self.client.get(self.url).status_code, 200)
            self.assertEqual(self.client.get(self.url).status_code, 200)
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)
