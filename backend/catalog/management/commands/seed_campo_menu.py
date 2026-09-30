import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from catalog.models import Category, Product, Station

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "campo_menu.json"


class Command(BaseCommand):
    help = "Carga el catálogo de práctica de Campo sin duplicar ni editar registros existentes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Valida y simula la carga;",
        )
        parser.add_argument(
            "--update-images",
            action="store_true",
            help="Actualiza las URLs de imágenes de productos existentes.",
        )

    def load_catalog(self):
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))

    def handle(self, *args, **options):
        try:
            catalog = self.load_catalog()
            if catalog["currency"] != "PEN" or not catalog["prices_include_taxes"]:
                raise CommandError("La fuente debe indicar precios en PEN con impuestos incluidos.")
            totals = {"categories": 0, "stations": 0, "products": 0, "existing": 0}
            seen_skus = set()
            station_names = {Station.Code.KITCHEN: "Cocina", Station.Code.BAR: "Barra"}
            with transaction.atomic():
                stations = {}
                for code, name in station_names.items():
                    stations[code], created = Station.objects.get_or_create(
                        code=code, defaults={"name": name, "active": True}
                    )
                    totals["stations"] += int(created)

                for position, group in enumerate(catalog["categories"], start=1):
                    category, created = Category.objects.get_or_create(
                        name=group["name"],
                        defaults={"display_order": position, "active": True},
                    )
                    totals["categories"] += int(created)
                    for row in group["products"]:
                        sku = row["sku"]
                        if not sku.startswith("CAMPO-") or sku in seen_skus:
                            raise CommandError(f"SKU de origen inválido o duplicado: {sku}")
                        seen_skus.add(sku)
                        defaults = {
                            "name": row["name"],
                            "description": "",
                            "image_url": row.get("image_url", ""),
                            "category": category,
                            "station": stations[group["station"]],
                            "sale_price": Decimal(row["price"]),
                            "published": True,
                            "available": True,
                        }
                        # Validate field values locally; database constraints protect
                        # references and uniqueness when the record is inserted.
                        Product(sku=sku, **defaults).full_clean(
                            exclude=["category", "station"],
                            validate_unique=False, validate_constraints=False,
                        )
                        product, created = Product.objects.get_or_create(
                            sku=sku,
                            defaults=defaults,
                        )
                        if (
                            options["update_images"]
                            and not created
                            and row.get("image_url")
                            and product.image_url != row["image_url"]
                        ):
                            product.image_url = row["image_url"]
                            product.save(update_fields=["image_url", "updated_at"])

                        totals["products"] += int(created)
                        totals["existing"] += int(not created)
                if options["dry_run"]:
                    transaction.set_rollback(True)
        except (OSError, ValueError, KeyError, InvalidOperation, ValidationError, IntegrityError) as exc:
            raise CommandError(f"No se completó la carga; se revirtieron sus cambios: {exc}") from exc

        mode = "SIMULACIÓN SIN GUARDAR" if options["dry_run"] else "CARGA COMPLETADA"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: categorías nuevas={totals['categories']}, "
            f"estaciones nuevas={totals['stations']}, productos nuevos={totals['products']}, "
            f"productos existentes conservados={totals['existing']}."
        ))
