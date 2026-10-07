import io
import zipfile
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from .inventory import import_workbook, read_xlsx, count_payload
from .models import InventoryCount, Ingredient, Recipe


def workbook():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Inventario Ejemplo" r:id="rId1"/></sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        cells = {"C8": "Codigo", "F8": "Producto", "E5": "Prueba", "E6": "Cocina", "L6": "Empleado", "C9": "0039", "F9": "Aceite", "I9": "ENV 5 L"}
        content = ''.join(f'<c r="{key}" t="inlineStr"><is><t>{value}</t></is></c>' for key, value in cells.items())
        content += '<c r="K9"><v>2</v></c><c r="L9"><v>5.67</v></c><c r="M9"><f>K9*L9</f><v>999</v></c>'
        archive.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row>{content}</row></sheetData></worksheet>')
    return stream.getvalue()


class ImportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="importer")
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label="costing", codename="use_costing"))
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_excel_preserves_codes_units_and_is_idempotent(self):
        content = workbook()
        count, created = import_workbook(content, "test.xlsx", self.user)
        self.assertTrue(created)
        self.assertTrue(count.is_example)
        self.assertEqual(count.currency, "")
        payload = count_payload(count)
        self.assertEqual(payload["lines"][0]["code"], "0039")
        self.assertEqual(payload["lines"][0]["unit"], "ENV 5 L")
        self.assertEqual(payload["total"], "11.34")
        self.assertEqual(payload["lines"][0]["source_extra"]["M"], "999")
        second, created = import_workbook(content, "renamed.xlsx", self.user)
        self.assertFalse(created)
        self.assertEqual(count.pk, second.pk)
        self.assertEqual(InventoryCount.objects.count(), 1)
        self.assertEqual(Ingredient.objects.count(), 0)

    def test_invalid_excel_and_missing_sheet(self):
        for content, sheet in ((b"invalid", None), (workbook(), "Missing")):
            with self.assertRaises(ValidationError):
                read_xlsx(content, sheet)

    def test_manual_count_validation_and_derived_total(self):
        payload = {"establishment": "Local", "department": "Bar", "employee": "Ana", "inventory_date": "2026-10-06", "currency": "PEN", "lines": [{"code": "001", "family": "Frutas", "location": "Bar", "product": "Limon", "unit": "kg", "quantity": "2.5", "unit_cost": "4", "inventory_value": "999"}]}
        response = self.client.post("/api/v1/costing/inventory/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["inventory"]["total"], "10.00")
        self.assertEqual(InventoryCount.objects.get().created_by, self.user)
        payload["lines"][0]["quantity"] = "-1"
        self.assertEqual(self.client.post("/api/v1/costing/inventory/", payload, format="json").status_code, 400)
        self.assertEqual(InventoryCount.objects.count(), 1)

    def test_recipe_import_names_atomicity_and_duplicate_rejection(self):
        Ingredient.objects.create(name="Arroz", purchase_unit="kg", purchase_quantity="1", purchase_price="10", yield_percent="100")
        recipe = {"name": "Arroz blanco", "portions": 2, "lines": [{"ingredient_name": "Arroz", "quantity": "200", "unit": "g", "basis": "gross"}], "total": "999"}
        path = "/api/v1/costing/recipes/import/"
        bad = {**recipe, "name": "Otro", "lines": [{"ingredient_name": "No existe", "quantity": "1", "unit": "g", "basis": "gross"}]}
        self.assertEqual(self.client.post(path, {"recipes": [recipe, bad]}, format="json").status_code, 400)
        self.assertEqual(Recipe.objects.count(), 0)
        self.assertEqual(self.client.post(path, {"recipes": [recipe]}, format="json").status_code, 201)
        self.assertEqual(Recipe.objects.get().versions.get().snapshot["total"], "2.00")
        self.assertEqual(self.client.post(path, {"recipes": [recipe]}, format="json").status_code, 400)
        self.assertEqual(Recipe.objects.count(), 1)

    def test_new_imports_require_permission_and_csrf(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/costing/inventory/").status_code, 403)
        for path in ("inventory", "recipes/import"):
            self.assertEqual(self.client.post(f"/api/v1/costing/{path}/", {}, format="json").status_code, 403)
            client = APIClient(enforce_csrf_checks=True)
            client.force_login(self.user)
            self.assertEqual(client.post(f"/api/v1/costing/{path}/", {}, format="json").status_code, 403)
