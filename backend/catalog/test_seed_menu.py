from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from .management.commands.seed_campo_menu import Command
from .models import Category, Product, Station


class SeedCampoMenuTests(TestCase):
    def seed(self, **options):
        call_command("seed_campo_menu", stdout=StringIO(), **options)

    def test_full_catalog_prices_stations_and_visibility(self):
        self.seed()
        self.assertEqual(Category.objects.count(), 10)
        self.assertEqual(Product.objects.count(), 71)
        self.assertEqual(Product.objects.filter(station__code="KITCHEN").count(), 32)
        self.assertEqual(Product.objects.filter(station__code="BAR").count(), 39)
        self.assertEqual(Product.objects.filter(published=True, available=True).count(), 71)
        self.assertEqual(Product.objects.get(sku="CAMPO-FO-004").sale_price, Decimal("72.00"))
        self.assertEqual(Product.objects.get(sku="CAMPO-BC-006").sale_price, Decimal("15.00"))
        self.assertEqual(Product.objects.get(sku="CAMPO-BF-011").sale_price, Decimal("14.00"))

    def test_repeat_preserves_edits_and_unrelated_data(self):
        self.seed()
        product = Product.objects.get(sku="CAMPO-FO-001")
        product.sale_price = Decimal("65.00")
        product.published = False
        product.name = "Nombre editado"
        product.save()
        category = product.category
        category.active = False
        category.display_order = 100
        category.save()
        station = product.station
        station.active = False
        station.save()
        other = Product.objects.create(
            sku="OWN-001", name="Propio", category=category,
            station=station, sale_price=Decimal("10.00"),
        )

        self.seed()

        product.refresh_from_db()
        category.refresh_from_db()
        station.refresh_from_db()
        self.assertEqual(Product.objects.count(), 72)
        self.assertEqual(Category.objects.count(), 10)
        self.assertEqual(product.sale_price, Decimal("65.00"))
        self.assertEqual(product.name, "Nombre editado")
        self.assertFalse(product.published)
        self.assertFalse(category.active)
        self.assertEqual(category.display_order, 100)
        self.assertFalse(station.active)
        self.assertTrue(Product.objects.filter(pk=other.pk).exists())

    def test_dry_run_does_not_persist_any_records(self):
        self.seed(dry_run=True)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Station.objects.count(), 0)

    def test_invalid_last_product_rolls_back_entire_import(self):
        data = Command().load_catalog()
        data["categories"][-1]["products"][-1]["price"] = "-1.00"
        with patch.object(Command, "load_catalog", return_value=data):
            with self.assertRaises(CommandError):
                self.seed()
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Station.objects.count(), 0)

    def test_duplicate_source_sku_rolls_back_import(self):
        data = Command().load_catalog()
        data["categories"][-1]["products"][-1]["sku"] = "CAMPO-CA-001"
        with patch.object(Command, "load_catalog", return_value=data):
            with self.assertRaises(CommandError):
                self.seed()
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Station.objects.count(), 0)
