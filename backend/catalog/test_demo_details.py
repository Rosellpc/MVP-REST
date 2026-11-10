import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from catalog.demo_details import NOTICE, ROWS, demo_fields
from catalog.forms import ALLERGENS
from catalog.models import Category, Product, Station


class DemoDetailsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Ejemplo")
        self.station = Station.objects.create(code="BAR", name="Barra")
        self.product = Product.objects.create(sku=ROWS[0][0], name=ROWS[0][1],
            category=self.category, station=self.station, sale_price=25, published=True)

    def test_examples_cover_72_unique_products_and_registered_allergens(self):
        self.assertEqual(len(ROWS), 72)
        self.assertEqual(len({row[0] for row in ROWS}), 72)
        for row in ROWS:
            self.assertFalse(set(row[4]) - set(ALLERGENS))
            for value in demo_fields(row).values():
                self.assertIn("DEMOSTRACIÓN", value)

    def test_dry_run_preserves_data(self):
        call_command("fill_demo_product_details", stdout=StringIO())
        self.product.refresh_from_db()
        self.assertEqual(self.product.description, "")

    def test_apply_preserves_existing_fields_and_restore_is_reversible(self):
        self.product.description = "Mi descripción real"
        self.product.save()
        with TemporaryDirectory() as folder:
            with override_settings(BASE_DIR=Path(folder) / "backend"):
                call_command("fill_demo_product_details", apply=True, stdout=StringIO())
                self.product.refresh_from_db()
                self.assertEqual(self.product.description, "Mi descripción real")
                self.assertIn(NOTICE, self.product.ingredients)
                self.assertEqual(self.product.sale_price, 25)
                backups = list((Path(folder) / ".artifacts" / "catalog-backups").glob("*.json"))
                self.assertEqual(len(backups), 1)
                call_command("fill_demo_product_details", apply=True, stdout=StringIO())
                self.assertEqual(len(list(backups[0].parent.glob("*.json"))), 1)
                call_command("fill_demo_product_details", apply=True, restore=backups[0], stdout=StringIO())
                self.product.refresh_from_db()
                self.assertEqual(self.product.ingredients, "")
                self.assertEqual(self.product.description, "Mi descripción real")

    def test_different_name_and_unpublished_products_are_preserved(self):
        self.product.name = "Otro producto con el mismo SKU"
        self.product.save()
        call_command("fill_demo_product_details", apply=True, stdout=StringIO())
        self.product.refresh_from_db()
        self.assertEqual(self.product.ingredients, "")

    def test_restore_refuses_to_overwrite_subsequent_edits(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "backup.json"
            path.write_text(json.dumps({"version": 1, "changes": [{"id": self.product.pk,
                "sku": self.product.sku, "before": {"description": ""},
                "after": {"description": "Previously applied example"}}]}), encoding="utf-8")
            self.product.description = "Edición posterior"
            self.product.save()
            with self.assertRaises(CommandError):
                call_command("fill_demo_product_details", apply=True, restore=path, stdout=StringIO())
            self.product.refresh_from_db()
            self.assertEqual(self.product.description, "Edición posterior")
