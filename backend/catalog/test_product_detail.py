from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Category, Product, Station


class ProductDetailTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Platos")
        cls.station = Station.objects.create(code="KITCHEN", name="Cocina")
        cls.product = Product.objects.create(
            sku="DETAIL-001", name="Producto de prueba", sale_price="25.50",
            category=cls.category, station=cls.station, published=True,
            description="Descripción de prueba", ingredients="Ingrediente A\nIngrediente B",
            nutritional_information="Información de prueba por porción: 100 kcal.",
            allergens="Declaración de prueba: contiene leche.",
        )

    def setUp(self):
        cache.clear()
        self.url = reverse("catalog:product-detail", args=[self.product.pk])

    def test_public_detail_returns_registered_information(self):
        with self.assertNumQueries(1):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ingredients"], self.product.ingredients)
        self.assertEqual(response.data["nutritional_information"], self.product.nutritional_information)
        self.assertEqual(response.data["allergens"], self.product.allergens)
        self.assertEqual(response.data["sale_price"], "25.50")
        self.assertEqual(response.data["category"]["name"], "Platos")
        self.assertNotIn("station", response.data)

    def test_unknown_information_is_blank_not_fabricated(self):
        Product.objects.filter(pk=self.product.pk).update(
            ingredients="", nutritional_information="", allergens="",
        )
        response = self.client.get(self.url)
        for field in ["ingredients", "nutritional_information", "allergens"]:
            self.assertEqual(response.data[field], "")

    def test_hidden_or_unavailable_products_cannot_be_opened_directly(self):
        for field in ["published", "available"]:
            with self.subTest(field=field):
                Product.objects.filter(pk=self.product.pk).update(**{field: False})
                self.assertEqual(self.client.get(self.url).status_code, 404)
                Product.objects.filter(pk=self.product.pk).update(**{field: True})
        for instance in [self.category, self.station]:
            with self.subTest(model=type(instance).__name__):
                instance.active = False
                instance.save()
                self.assertEqual(self.client.get(self.url).status_code, 404)
                instance.active = True
                instance.save()

    def test_detail_is_read_only_and_missing_id_returns_404(self):
        for method in ["post", "put", "patch", "delete"]:
            self.assertEqual(getattr(self.client, method)(self.url, {}, format="json").status_code, 405)
        self.assertEqual(self.client.get(reverse("catalog:product-detail", args=[999999])).status_code, 404)
