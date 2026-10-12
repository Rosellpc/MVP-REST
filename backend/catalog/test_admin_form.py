from django.test import TestCase

from .forms import ALLERGENS, ProductAdminForm
from .models import Category, Product, Station


class ProductAllergenFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Entradas")
        self.station = Station.objects.create(code="KITCHEN", name="Cocina")
        self.data = {
            "sku": "TEST-ALLERGEN", "name": "Plato", "category": self.category.pk,
            "station": self.station.pk, "sale_price": "20.00",
            "selected_allergens": ["Huevo", "Lácteos"],
            "allergens": "Puede contener sésamo.",
        }

    def test_save_and_reopen_then_remove_selection_preserves_notes(self):
        form = ProductAdminForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.allergens, "Huevo\nLácteos\nPuede contener sésamo.")
        reopened = ProductAdminForm(instance=product)
        self.assertEqual(reopened.initial["selected_allergens"], ["Huevo", "Lácteos"])
        self.assertEqual(reopened.initial["allergens"], "Puede contener sésamo.")
        form = ProductAdminForm(data={**self.data, "selected_allergens": []}, instance=product)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().allergens, "Puede contener sésamo.")

    def test_legacy_declarations_are_not_interpreted_as_presence(self):
        declaration = "Sin gluten. Puede contener huevo."
        form = ProductAdminForm(instance=Product(allergens=declaration))
        self.assertEqual(form.initial["selected_allergens"], [])
        self.assertEqual(form.initial["allergens"], declaration)
        self.assertEqual(len(ALLERGENS), 14)

    def test_unknown_choice_is_rejected(self):
        form = ProductAdminForm(data={**self.data, "selected_allergens": ["Inventado"]})
        self.assertFalse(form.is_valid())
        self.assertIn("selected_allergens", form.errors)
