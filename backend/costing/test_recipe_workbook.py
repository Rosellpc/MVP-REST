from unittest.mock import patch
from django.test import TestCase
from .models import Ingredient, Recipe, RecipeWorkbookImport
from .recipe_workbook import import_recipe_book


class RecipeWorkbookTests(TestCase):
    def data(self):
        return {"Lista de Ingredientes": {"B6": "Pollo", "D6": "20", "E6": "1", "F6": "KG", "G6": "1", "H6": "0.2"},
                "Receta 1": {"E5": "Pollo asado", "F11": "1", "K9": "11.80", "K10": "0.18", "E19": "Pollo", "G19": "0.2", "F14": "Plato frío", "K13": "4.8"}}

    def test_corrected_cost_source_and_idempotence(self):
        with patch("costing.recipe_workbook.read_recipe_book", return_value=self.data()):
            batch, created = import_recipe_book(b"test", "recetas.xlsx")
            self.assertTrue(created)
            self.assertEqual(batch.report["recipes_created"], 1)
            snapshot = Recipe.objects.get().versions.get().snapshot
            self.assertEqual(snapshot["total"], "5.00")
            self.assertEqual(snapshot["net_price"], "10.00")
            self.assertIsNone(snapshot["cooking_minutes"])
            self.assertEqual(snapshot["import_source"]["original_total"], "4.8")
            self.assertIsNone(Recipe.objects.get().versions.get().actor)
            again, created = import_recipe_book(b"test", "renamed.xlsx")
            self.assertFalse(created)
            self.assertEqual(again.pk, batch.pk)
            self.assertEqual(Ingredient.objects.count(), 1)
            self.assertEqual(Recipe.objects.count(), 1)

    def test_missing_ingredient_retains_pending_source(self):
        data = self.data()
        data["Receta 1"]["E19"] = "Unknown"
        with patch("costing.recipe_workbook.read_recipe_book", return_value=data):
            batch, _ = import_recipe_book(b"test", "recetas.xlsx")
        self.assertEqual(Recipe.objects.count(), 0)
        self.assertEqual(batch.report["pending"][0]["name"], "Pollo asado")
        self.assertEqual(batch.source, data)

    def test_existing_price_is_not_overwritten(self):
        Ingredient.objects.create(name="Pollo", purchase_quantity="1", purchase_unit="kg", purchase_price="99", yield_percent="80")
        with patch("costing.recipe_workbook.read_recipe_book", return_value=self.data()):
            batch, _ = import_recipe_book(b"test", "recetas.xlsx")
        self.assertEqual(str(Ingredient.objects.get(name="Pollo").purchase_price), "99.0000")
        self.assertEqual(Ingredient.objects.count(), 2)
        self.assertEqual(len(batch.report["pending"]), 0)
        self.assertEqual(batch.report["recipes_created"], 1)
        self.assertEqual(RecipeWorkbookImport.objects.count(), 1)
        with patch("costing.recipe_workbook.read_recipe_book", return_value=self.data()):
            batch, _ = import_recipe_book(b"test", "recetas.xlsx", resume=True)
        self.assertEqual(Ingredient.objects.count(), 2)
        self.assertEqual(Recipe.objects.count(), 1)
