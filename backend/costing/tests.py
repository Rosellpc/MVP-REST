from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Ingredient, CostStudy


class CostingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cost-admin", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label="costing", codename="use_costing"))
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.ingredient = Ingredient.objects.create(name="Pollo", purchase_unit="kg", purchase_quantity="1", purchase_price="20", yield_percent="80")
        self.recipe = {"name": "Prueba", "portions": 2, "lines": [{"ingredient_id": self.ingredient.pk, "quantity": "200", "unit": "g", "basis": "usable"}]}

    def test_yield_and_conversion(self):
        response = self.client.post("/api/v1/costing/preview/", self.recipe, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], "5.00")
        self.assertEqual(response.data["per_portion"], "2.50")
        self.assertEqual(CostStudy.objects.count(), 0)

    def test_gross_does_not_apply_yield_twice(self):
        self.recipe["lines"][0]["basis"] = "gross"
        response = self.client.post("/api/v1/costing/preview/", self.recipe, format="json")
        self.assertEqual(response.data["total"], "4.00")

    def test_incompatible_units_and_invalid_inputs(self):
        self.recipe["lines"][0]["unit"] = "ml"
        self.assertEqual(self.client.post("/api/v1/costing/preview/", self.recipe, format="json").status_code, 400)
        self.recipe["lines"] = []
        self.assertEqual(self.client.post("/api/v1/costing/preview/", self.recipe, format="json").status_code, 400)
        payload = {"name": "Aceite", "purchase_unit": "l", "purchase_quantity": "1", "purchase_price": "10", "yield_percent": "0"}
        self.assertEqual(self.client.post("/api/v1/costing/ingredients/", payload, format="json").status_code, 400)

    def test_saved_snapshot_is_immutable(self):
        response = self.client.post("/api/v1/costing/studies/", self.recipe, format="json")
        self.assertEqual(response.status_code, 201)
        Ingredient.objects.filter(pk=self.ingredient.pk).update(purchase_price="40")
        self.assertEqual(CostStudy.objects.get().snapshot["total"], "5.00")
        self.assertEqual(CostStudy.objects.get().created_by, self.user)
        self.assertEqual(self.client.post("/api/v1/costing/preview/", self.recipe, format="json").data["total"], "10.00")

    def test_permission_required(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/costing/ingredients/").status_code, 403)
        other = get_user_model().objects.create_user(username="kitchen")
        self.client.force_authenticate(other)
        self.assertEqual(self.client.post("/api/v1/costing/studies/", self.recipe, format="json").status_code, 403)

    def test_session_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post("/api/v1/costing/studies/", self.recipe, format="json").status_code, 403)

    def test_recipe_version_conflict_and_historical_prices(self):
        payload = {**self.recipe, "selling_price": "11.80", "tax_percent": "18", "preparation": "Mezclar", "allergens": "Leche"}
        first = self.client.post("/api/v1/costing/recipes/", payload, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.data["snapshot"]["net_price"], "10.00")
        self.assertEqual(first.data["snapshot"]["margin"], "7.50")
        self.assertEqual(first.data["snapshot"]["food_cost_percent"], "25.00")
        Ingredient.objects.filter(pk=self.ingredient.pk).update(purchase_price="40")
        path = f'/api/v1/costing/recipes/{first.data["recipe_id"]}/'
        payload["expected_version"] = 1
        second = self.client.post(path, payload, format="json")
        self.assertEqual(second.status_code, 201)
        self.assertEqual(second.data["number"], 2)
        self.assertEqual(second.data["snapshot"]["total"], "10.00")
        self.assertEqual(self.client.post(path, payload, format="json").status_code, 409)
        history = self.client.get(path).data
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["snapshot"]["total"], "5.00")
        self.assertEqual(history[1]["snapshot"]["preparation"], "Mezclar")
        self.assertEqual(len(self.client.get("/api/v1/costing/recipes/").data), 1)

    def test_edit_ingredient_audits_old_and_new_reference(self):
        from .models import IngredientRevision
        payload = {"name": "Pollo", "purchase_unit": "kg", "purchase_quantity": "1", "purchase_price": "30", "yield_percent": "75", "reason": "Nuevo proveedor"}
        path = f"/api/v1/costing/ingredients/{self.ingredient.pk}/"
        self.assertEqual(self.client.put(path, payload, format="json").status_code, 200)
        self.assertEqual(IngredientRevision.objects.count(), 2)
        history = self.client.get(path).data["history"]
        self.assertEqual(history[0]["snapshot"]["purchase_price"], "30.0000")
        self.assertEqual(history[1]["snapshot"]["purchase_price"], "20.0000")
        payload.pop("reason")
        self.assertEqual(self.client.put(path, payload, format="json").status_code, 400)

    def test_import_is_atomic_and_rejects_duplicates(self):
        row = {"name": "Aceite", "purchase_unit": "l", "purchase_quantity": "1", "purchase_price": "10", "yield_percent": "100"}
        path = "/api/v1/costing/import/"
        self.assertEqual(self.client.post(path, {"ingredients": [row, {**row, "name": "aceite"}]}, format="json").status_code, 400)
        self.assertEqual(Ingredient.objects.count(), 1)
        self.assertEqual(self.client.post(path, {"ingredients": [row, {**row, "name": "Sal", "yield_percent": "0"}]}, format="json").status_code, 400)
        self.assertEqual(Ingredient.objects.count(), 1)
        self.assertEqual(self.client.post(path, {"ingredients": [row]}, format="json").status_code, 201)
        self.assertEqual(Ingredient.objects.count(), 2)

    def test_summary_excludes_unpriced_recipes(self):
        self.client.post("/api/v1/costing/recipes/", self.recipe, format="json")
        self.client.post("/api/v1/costing/recipes/", {**self.recipe, "selling_price": "10"}, format="json")
        summary = self.client.get("/api/v1/costing/summary/").data
        self.assertEqual(summary["recipes"], 2)
        self.assertEqual(summary["priced_recipes"], 1)
        self.assertEqual(summary["average_food_cost"], "25.00")

    def test_simulation_uses_unrounded_cost_and_does_not_save(self):
        self.recipe["portions"] = 3
        response = self.client.post("/api/v1/costing/recipes/preview/", {**self.recipe, "selling_price": "10"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["food_cost_percent"], "16.67")
        from .models import Recipe
        self.assertEqual(Recipe.objects.count(), 0)

    def test_new_endpoints_require_permission_and_csrf(self):
        self.client.force_authenticate(None)
        for path in ("recipes", "summary", "ingredients/1"):
            self.assertEqual(self.client.get(f"/api/v1/costing/{path}/").status_code, 403)
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        for path in ("recipes", "recipes/1", "recipes/preview", "import"):
            self.assertEqual(client.post(f"/api/v1/costing/{path}/", self.recipe, format="json").status_code, 403)
