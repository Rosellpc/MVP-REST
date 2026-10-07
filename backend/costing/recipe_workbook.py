"""Adapter for the supplied recipe workbook. Cached source is retained for audit."""
import hashlib
import io
import posixpath
import re
import unicodedata
import zipfile
from decimal import Decimal, ROUND_HALF_UP
from xml.etree import ElementTree as ET
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Ingredient, IngredientRevision, Recipe, RecipeVersion, RecipeWorkbookImport
from .serializers import IngredientSerializer, TechnicalRecipeSerializer
from .recipe_views import recipe_snapshot

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def normalize(value):
    return ''.join(c for c in unicodedata.normalize("NFD", value.strip().casefold()) if not unicodedata.combining(c))


def decimal(value, places="0.001"):
    result = Decimal(value).quantize(Decimal(places), rounding=ROUND_HALF_UP)
    if not result.is_finite():
        raise ValueError("Número no finito")
    return result


def read_recipe_book(content):
    if len(content) > 10_000_000:
        raise ValidationError({"detail": "Máximo 10 MB."})
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if sum(entry.file_size for entry in archive.infolist()) > 50_000_000:
                raise ValueError("Libro demasiado grande")
            def xml(path):
                raw = archive.read(path)
                if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
                    raise ValueError("XML no permitido")
                return ET.fromstring(raw)
            strings = [''.join(node.itertext()) for node in xml("xl/sharedStrings.xml")] if "xl/sharedStrings.xml" in archive.namelist() else []
            relations = {row.get("Id"): row.get("Target") for row in xml("xl/_rels/workbook.xml.rels")}
            sheets = {}
            for sheet in xml("xl/workbook.xml").find("m:sheets", NS):
                name = sheet.get("name")
                if not (name.startswith("Receta") or name == "Lista de Ingredientes"):
                    continue
                target = relations[sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")]
                path = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
                cells = {}
                for cell in xml(path).findall(".//m:sheetData/m:row/m:c", NS):
                    value = cell.find("m:v", NS)
                    text = value.text if value is not None and value.text else ""
                    if cell.get("t") == "s":
                        text = strings[int(text)]
                    elif cell.get("t") == "inlineStr":
                        text = ''.join(cell.find("m:is", NS).itertext())
                    if text.strip():
                        cells[cell.get("r")] = text.strip()
                sheets[name] = cells
            if "Lista de Ingredientes" not in sheets:
                raise ValueError("Falta la hoja Lista de Ingredientes")
            return sheets
    except (zipfile.BadZipFile, KeyError, IndexError, AttributeError, ValueError, ET.ParseError) as exc:
        raise ValidationError({"detail": f"Plantilla de recetas inválida: {exc}"}) from exc


@transaction.atomic
def import_recipe_book(content, filename, actor=None, resume=False):
    sheets = read_recipe_book(content)
    batch, created = RecipeWorkbookImport.objects.get_or_create(digest=hashlib.sha256(content).hexdigest(), defaults={"filename": filename[:250], "actor": actor})
    if not created and not resume:
        return batch, False
    batch = RecipeWorkbookImport.objects.select_for_update().get(pk=batch.pk)
    previous = batch.report if not created else {}
    report = {"ingredients_created": 0, "ingredients_reused": 0, "recipes_created": 0, "duplicates": [], "pending": [], "recipes": [], "warnings": [
        "Cantidades de receta tratadas como aprovechables, por el uso del coste con merma en Excel; revisar antes de uso operativo.",
        "Merma recalculada como rendimiento = 100 - merma%; impuesto incluido por división. Los costos pueden diferir del Excel.",
        "Formatos de envase con peso bruto se interpretan en kg; LT en litros. Revisar especialmente presentaciones ambiguas.",
        "Sin inferir alérgenos de casillas o ingredientes. Campos vacíos quedan pendientes de revisión. Moneda PEN del módulo.",
    ]}
    report["ingredients_created"] = previous.get("ingredients_created", 0)
    report["recipes"] = previous.get("recipes", [])
    report["recipes_created"] = len(report["recipes"])
    completed = {normalize(row["name"]) for row in report["recipes"]}
    by_name = {}
    existing = {}
    for item in Ingredient.objects.all():
        existing.setdefault(normalize(item.name), []).append(item)
    catalog = sheets["Lista de Ingredientes"]
    source_rows = {}
    for row in range(6, 207):
        name = catalog.get(f"B{row}", "")
        if not name:
            continue
        key = normalize(name)
        raw = {col: catalog.get(f"{col}{row}", "") for col in "BCDEFGHI"}
        try:
            if key in source_rows:
                if all(raw[col] == source_rows[key][col] for col in "DEFGH"):
                    report["duplicates"].append({"name": name, "row": row})
                    continue
                raise ValueError("Nombre duplicado con otra referencia de compra")
            source_rows[key] = raw
            unit = "l" if raw["F"] == "LT" else "kg"
            if raw["F"] not in ("KG", "LT", "UNIDAD", "BANDEJA", "ATADO", "MOLDE", "CAJA", "PAQUETE", "LATA", "PLANCHA", "POTE", "SOBRE"):
                raise ValueError("Formato de compra desconocido")
            payload = {"name": name, "purchase_unit": unit,
                       "purchase_quantity": str(decimal(raw["G"]) * decimal(raw["E"] or "1")),
                       "purchase_price": str(decimal(raw["D"], "0.0001")),
                       "yield_percent": str(100 - decimal(raw["H"] or "0", "0.00001") * 100)}
            payload["purchase_quantity"] = str(decimal(payload["purchase_quantity"]))
            payload["yield_percent"] = str(decimal(payload["yield_percent"]))
            matches = existing.get(key, [])
            if matches:
                if len(matches) != 1:
                    raise ValueError("Varios insumos existentes coinciden con el nombre")
                item = matches[0]
                if item.purchase_unit != unit or any(getattr(item, field) != Decimal(payload[field]) for field in ("purchase_quantity", "purchase_price", "yield_percent")):
                    payload["name"] = f"{name} [Excel {filename}]"[:160]
                    variant = Ingredient.objects.filter(name=payload["name"]).first()
                    if variant:
                        if variant.purchase_unit != unit or any(getattr(variant, field) != Decimal(payload[field]) for field in ("purchase_quantity", "purchase_price", "yield_percent")):
                            raise ValueError("La referencia Excel existente tiene otros valores; requiere revisión")
                        item = variant
                        report["ingredients_reused"] += 1
                    else:
                        serializer = IngredientSerializer(data=payload)
                        serializer.is_valid(raise_exception=True)
                        item = serializer.save()
                        IngredientRevision.objects.create(ingredient=item, actor=actor, reason=f"Referencia separada de Excel, fila {row}", snapshot={**dict(serializer.data), "source": raw})
                        report["ingredients_created"] += 1
                    report["warnings"].append(f"{name}: se utilizó la referencia separada {item.name}; no se modificó la anterior.")
                else:
                    report["ingredients_reused"] += 1
            else:
                serializer = IngredientSerializer(data=payload)
                serializer.is_valid(raise_exception=True)
                item = serializer.save()
                IngredientRevision.objects.create(ingredient=item, actor=actor, reason=f"Excel: {filename[:160]}, fila {row}", snapshot={**dict(serializer.data), "source": raw})
                report["ingredients_created"] += 1
            by_name[key] = item
        except (ValueError, ArithmeticError, ValidationError) as exc:
            report["pending"].append({"type": "ingredient", "name": name, "row": row, "reason": str(exc)})
    recipe_names = {normalize(name) for name in Recipe.objects.values_list("name", flat=True)}
    for sheet, cells in sheets.items():
        if not sheet.startswith("Receta") or not cells.get("E5"):
            continue
        name = cells["E5"]
        if normalize(name) in completed:
            continue
        try:
            if normalize(name) in recipe_names:
                raise ValueError("Receta existente: no se sobrescribió")
            lines = []
            for row in range(19, 65):
                if not cells.get(f"E{row}") or not cells.get(f"G{row}"):
                    continue
                ingredient_name = cells[f"E{row}"]
                item = by_name.get(normalize(ingredient_name))
                if item is None:
                    raise ValueError(f"Insumo faltante o pendiente: {ingredient_name} (fila {row})")
                lines.append({"ingredient_id": item.pk, "quantity": str(decimal(str(Decimal(cells[f"G{row}"]) * 1000))), "unit": "ml" if item.purchase_unit == "l" else "g", "basis": "usable"})
            def minutes(address):
                value = cells.get(address, "0")
                match = re.fullmatch(r"(\d+)\s*(?:minutos?|min)?", value, re.I)
                if not match:
                    return None
                return int(match[1])
            def section(label, stop):
                starts = [int(key[1:]) for key, value in cells.items() if key.startswith("E") and value == label]
                if not starts:
                    return ""
                start = starts[0]
                ends = [int(key[1:]) for key, value in cells.items() if key.startswith("E") and value in stop and int(key[1:]) > start]
                end = min(ends) if ends else start + 1
                return '\n'.join(value for key, value in cells.items() if re.fullmatch(r"[E-K]\d+", key) and start < int(key[1:]) < end)
            payload = {"name": name, "category": cells.get("K7", ""), "portions": int(Decimal(cells["F11"])),
                       "portion_size": cells.get("F10", ""), "preparation_minutes": minutes("F13"), "cooking_minutes": minutes("F14"),
                       "temperature": cells.get("F15", ""), "preparation": section("Elaboración", ("Presentación",)),
                       "presentation": section("Presentación", ("Equipo necesario para elaboración", "Alérgenos")), "allergens": "",
                       "selling_price": str(decimal(cells["K9"], "0.01")), "tax_percent": str(decimal(str(Decimal(cells["K10"]) * 100), "0.01")), "lines": lines}
            serializer = TechnicalRecipeSerializer(data=payload)
            serializer.is_valid(raise_exception=True)
            snapshot = recipe_snapshot(serializer.validated_data)
            snapshot["import_source"] = {"batch_id": batch.pk, "file": filename, "sheet": sheet, "original_total": cells.get("K13"), "review_required": True, "notes": report["warnings"], "original_preparation_time": cells.get("F13"), "original_cooking_time": cells.get("F14"), "restaurant": cells.get("F7"), "excel_date": cells.get("F9")}
            recipe = Recipe.objects.create(name=name, current_version=1)
            RecipeVersion.objects.create(recipe=recipe, number=1, snapshot=snapshot, actor=actor)
            recipe_names.add(normalize(name))
            report["recipes_created"] += 1
            report["recipes"].append({"id": recipe.pk, "name": name, "sheet": sheet, "original_total": cells.get("K13"), "recalculated_total": snapshot["total"]})
        except (ValueError, KeyError, ArithmeticError, ValidationError) as exc:
            report["pending"].append({"type": "recipe", "name": name, "sheet": sheet, "reason": str(exc)})
    batch.source = sheets
    batch.report = report
    batch.save(update_fields=["source", "report"])
    return batch, True
