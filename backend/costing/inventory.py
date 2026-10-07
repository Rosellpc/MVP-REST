"""Inventory sheets are immutable counts, separate from stock and recipe inputs."""
import hashlib
import io
import posixpath
import zipfile
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from xml.etree import ElementTree as ET
from django.db import transaction
from rest_framework import serializers
from .models import InventoryCount, InventoryCountLine

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class CountLineSerializer(serializers.ModelSerializer):
    quantity = serializers.DecimalField(max_digits=16, decimal_places=4, min_value=Decimal(0))
    unit_cost = serializers.DecimalField(max_digits=16, decimal_places=4, min_value=Decimal(0))

    class Meta:
        model = InventoryCountLine
        fields = ("code", "family", "location", "product", "unit", "quantity", "unit_cost", "source_row", "source_extra")


class CountSerializer(serializers.ModelSerializer):
    lines = CountLineSerializer(many=True, allow_empty=False, max_length=1000)
    currency = serializers.ChoiceField(choices=("", "PEN", "USD", "EUR", "COP"), required=False, default="")

    class Meta:
        model = InventoryCount
        fields = ("establishment", "department", "inventory_date", "employee", "currency", "is_example", "notes", "lines")


def read_xlsx(content, sheet_name=None):
    """Read only cached values from the supplied template; never execute formulas."""
    if len(content) > 5_000_000:
        raise serializers.ValidationError({"detail": "El Excel supera 5 MB."})
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if sum(info.file_size for info in archive.infolist()) > 30_000_000:
                raise ValueError("Libro demasiado grande descomprimido.")
            def xml(path):
                raw = archive.read(path)
                if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
                    raise ValueError("XML no permitido.")
                return ET.fromstring(raw)
            strings = ["".join(node.itertext()) for node in xml("xl/sharedStrings.xml")] if "xl/sharedStrings.xml" in archive.namelist() else []
            workbook = xml("xl/workbook.xml")
            relations = {node.get("Id"): node.get("Target") for node in xml("xl/_rels/workbook.xml.rels")}
            choices = []
            for sheet in workbook.findall("m:sheets/m:sheet", NS):
                name = sheet.get("name")
                if sheet_name and name != sheet_name:
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
                        text = "".join(cell.find("m:is", NS).itertext())
                    cells[cell.get("r")] = text.strip()
                if cells.get("C8", "").lower() not in ("codigo", "código") or cells.get("F8", "").lower() != "producto":
                    continue
                lines = []
                for row in range(9, 287):
                    product = cells.get(f"F{row}", "")
                    if not product or product.lower() == "producto":
                        continue
                    def number(column):
                        value = Decimal(cells.get(f"{column}{row}", ""))
                        if not value.is_finite() or value < 0:
                            raise ValueError(f"Fila {row}: número inválido en {column}.")
                        return str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
                    lines.append({"code": cells.get(f"C{row}", ""), "family": cells.get(f"D{row}", ""),
                                  "location": cells.get(f"E{row}", ""), "product": product,
                                  "unit": cells.get(f"I{row}", ""), "quantity": number("K"), "unit_cost": number("L"),
                                  "source_row": row, "source_extra": {col: cells.get(f"{col}{row}", "") for col in ("G", "H", "J", "M")}})
                if lines:
                    date = cells.get("L5", "")
                    properties = workbook.find("m:workbookPr", NS)
                    epoch = datetime(1904, 1, 1) if properties is not None and properties.get("date1904") in ("1", "true") else datetime(1899, 12, 30)
                    inventory_date = (epoch + timedelta(days=float(date))).date().isoformat() if date else None
                    choices.append((name, {"establishment": cells.get("E5", ""), "department": cells.get("E6", ""),
                                          "employee": cells.get("L6", ""), "inventory_date": inventory_date,
                                          "currency": "", "is_example": "ejemplo" in name.lower(),
                                          "notes": "Importado del Excel. Moneda no indicada; unidades originales sin convertir. Conteo de referencia, no kardex.", "lines": lines}))
            if len(choices) != 1:
                raise ValueError("Selecciona una única hoja con datos usando su nombre. Las hojas vacías no se importan.")
            return choices[0]
    except (zipfile.BadZipFile, KeyError, IndexError, AttributeError, ValueError, TypeError, InvalidOperation, ET.ParseError, OverflowError) as exc:
        raise serializers.ValidationError({"detail": f"No se pudo leer la plantilla: {exc}"}) from exc


@transaction.atomic
def store_count(payload, actor=None, source_name="", source_sheet="", digest=None):
    serializer = CountSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    values = dict(serializer.validated_data)
    lines = values.pop("lines")
    if digest:
        count, created = InventoryCount.objects.get_or_create(source_digest=digest, defaults={**values, "created_by": actor, "source_name": source_name, "source_sheet": source_sheet})
        if not created:
            return count, False
    else:
        count = InventoryCount.objects.create(**values, created_by=actor, source_name=source_name, source_sheet=source_sheet)
    InventoryCountLine.objects.bulk_create([InventoryCountLine(inventory=count, **line) for line in lines])
    return count, True


def import_workbook(content, filename, actor=None, sheet_name=None):
    sheet, payload = read_xlsx(content, sheet_name)
    digest = hashlib.sha256(content + sheet.encode()).hexdigest()
    return store_count(payload, actor, filename[:250], sheet, digest)


def count_payload(count):
    lines = []
    total = Decimal(0)
    for item in count.lines.all():
        if item.archived:
            continue
        line = dict(CountLineSerializer(item).data)
        line["id"] = item.pk
        value = item.quantity * item.unit_cost
        total += value
        line["inventory_value"] = str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
        lines.append(line)
    return {"id": count.pk, "establishment": count.establishment, "department": count.department,
            "inventory_date": count.inventory_date, "employee": count.employee, "currency": count.currency,
            "is_example": count.is_example, "notes": count.notes, "source_name": count.source_name,
            "source_sheet": count.source_sheet, "created_at": count.created_at, "lines": lines,
            "total": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))}
