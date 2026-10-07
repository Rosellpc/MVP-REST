from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Ingredient, Recipe, RecipeVersion, InventoryCount, InventoryCountLine, CostingChange


class ItemActionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="editor")
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label="costing", codename="use_costing"))
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_removing_ingredient_preserves_reference_and_recipe_history(self):
        item = Ingredient.objects.create(name="Sal", purchase_unit="kg", purchase_quantity=1, purchase_price=2, yield_percent=100)
        payload = {"name": "Receta", "portions": 1, "lines": [{"ingredient_id": item.pk, "unit": "g", "quantity": "10", "basis": "gross"}]}
        recipe = self.client.post("/api/v1/costing/recipes/", payload, format="json")
        before = RecipeVersion.objects.get().snapshot
        self.assertEqual(self.client.delete(f"/api/v1/costing/ingredients/{item.pk}/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/costing/ingredients/").data, [])
        self.assertTrue(Ingredient.objects.get().archived)
        self.assertEqual(RecipeVersion.objects.get().snapshot, before)
        self.assertEqual(self.client.post("/api/v1/costing/recipes/preview/", payload, format="json").status_code, 400)
        self.assertEqual(self.client.delete(f'/api/v1/costing/recipes/{recipe.data["recipe_id"]}/').status_code, 200)
        self.assertEqual(self.client.get("/api/v1/costing/recipes/").data, [])
        self.assertTrue(Recipe.objects.get().archived)
        self.assertEqual(RecipeVersion.objects.count(), 1)
        self.assertEqual(CostingChange.objects.filter(actor=self.user).count(), 2)

    def test_inventory_edit_and_delete_recalculate_total_and_audit(self):
        count = InventoryCount.objects.create(establishment="Local", department="Bar", employee="Ana")
        line = InventoryCountLine.objects.create(inventory=count, product="Limon", unit="kg", quantity=2, unit_cost=3, source_extra={"M": "6"})
        url = f"/api/v1/costing/inventory/{count.pk}/lines/{line.pk}/"
        response = self.client.put(url, {"product": "Limon", "unit": "kg", "quantity": "4", "unit_cost": "3", "source_extra": {}}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], "12.00")
        line.refresh_from_db()
        self.assertEqual(line.source_extra, {"M": "6"})
        response = self.client.delete(url)
        self.assertEqual(response.data["total"], "0.00")
        self.assertEqual(response.data["lines"], [])
        self.assertEqual(InventoryCountLine.objects.count(), 1)
        self.assertEqual(CostingChange.objects.count(), 2)
        self.assertEqual(self.client.put(url, {}, format="json").status_code, 404)

    def test_delete_requires_session_permission_and_csrf(self):
        self.client.force_authenticate(None)
        for url in ("ingredients/1", "recipes/1", "inventory/1/lines/1"):
            self.assertEqual(self.client.delete(f"/api/v1/costing/{url}/").status_code, 403)
            client = APIClient(enforce_csrf_checks=True)
            client.force_login(self.user)
            self.assertEqual(client.delete(f"/api/v1/costing/{url}/").status_code, 403)
