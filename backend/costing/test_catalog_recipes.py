from io import StringIO
from django.core.management import call_command, CommandError
from django.test import TestCase
from catalog.models import Category, Station, Product
from costing.models import Recipe, RecipeVersion


class CatalogRecipeImportTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            sku="TEST-BAR", name="Bebida", published=True, sale_price="15.50",
            category=Category.objects.create(name="Bebidas"),
            station=Station.objects.create(code="BAR", name="Barra"),
        )

    def run_import(self, count=1):
        call_command("import_catalog_recipes", ids=str(self.product.pk), expected_count=count, stdout=StringIO())

    def test_pending_costs_preserve_price_and_menu_and_are_idempotent(self):
        before = Product.objects.values().get(pk=self.product.pk)
        self.run_import()
        self.run_import()
        self.assertEqual(Recipe.objects.count(), 1)
        snapshot = RecipeVersion.objects.get().snapshot
        self.assertEqual(snapshot["selling_price"], "15.50")
        self.assertEqual(snapshot["category"], "Bebidas")
        for field in ["total", "per_portion", "margin", "net_price", "food_cost_percent"]:
            self.assertIsNone(snapshot[field])
        self.assertEqual(snapshot["lines"], [])
        self.assertTrue(snapshot["pending_costing"])
        self.assertEqual(Product.objects.values().get(pk=self.product.pk), before)

    def test_wrong_count_or_conflict_does_not_import(self):
        with self.assertRaises(CommandError):
            self.run_import(39)
        self.assertEqual(Recipe.objects.count(), 0)
        Recipe.objects.create(name=self.product.name)
        with self.assertRaises(CommandError):
            self.run_import()
        self.assertEqual(RecipeVersion.objects.count(), 0)
