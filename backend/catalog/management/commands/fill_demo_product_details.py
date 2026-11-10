import json
from datetime import datetime, timezone as utc_timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.demo_details import ROWS, demo_fields
from catalog.forms import ALLERGENS
from catalog.models import Product


class Command(BaseCommand):
    help = "Completa campos vacíos de la carta con ejemplos ficticios y respaldo local."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Guarda; sin esta opción solo muestra el plan.")
        parser.add_argument("--restore", type=Path, help="Restaura un respaldo, si esos campos siguen sin editarse.")

    def handle(self, *args, **options):
        if options["restore"]:
            if not options["apply"]:
                raise CommandError("La restauración requiere --apply.")
            return self.restore(options["restore"])
        catalog = {row[0]: row for row in ROWS}
        if len(catalog) != len(ROWS):
            raise CommandError("Hay SKU duplicados en los ejemplos.")
        if any(set(row[4]) - set(ALLERGENS) for row in ROWS):
            raise CommandError("Un ejemplo utiliza un alérgeno no registrado.")
        with transaction.atomic():
            products = list(Product.objects.select_for_update().filter(
                published=True, category__active=True, station__active=True,
            ).order_by("pk"))
            changes, unmatched = [], []
            for product in products:
                row = catalog.get(product.sku)
                if row is None or product.name.strip().casefold() != row[1].strip().casefold():
                    unmatched.append(product.sku)
                    continue
                values = demo_fields(row)
                after = {key: value for key, value in values.items() if not getattr(product, key).strip()}
                if after:
                    changes.append({
                        "id": product.pk, "sku": product.sku, "name": product.name,
                        "before": {key: getattr(product, key) for key in after}, "after": after,
                    })
            self.stdout.write(f"Menu={len(products)}, productos a completar={len(changes)}, campos={sum(len(c['after']) for c in changes)}, sin ejemplo coincidente={len(unmatched)}")
            if unmatched:
                self.stdout.write("SKU conservados sin coincidencia: " + ", ".join(unmatched))
            if not options["apply"] or not changes:
                return
            folder = settings.BASE_DIR.parent / ".artifacts" / "catalog-backups"
            folder.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(utc_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup = folder / f"demo-details-{stamp}.json"
            backup.write_text(json.dumps({"version": 1, "changes": changes}, ensure_ascii=False, indent=2), encoding="utf-8")
            for change in changes:
                Product.objects.filter(pk=change["id"], sku=change["sku"]).update(
                    **change["after"], updated_at=timezone.now(),
                )
            # Verify the exact saved fields before committing this transaction.
            for change in changes:
                saved = Product.objects.values(*change["after"]).get(pk=change["id"])
                if saved != change["after"]:
                    raise CommandError("La verificación falló; se revirtieron los cambios.")
        self.stdout.write(self.style.SUCCESS("Aplicado y verificado. Respaldo: " + str(backup)))

    def restore(self, path):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            changes = payload["changes"]
            if payload["version"] != 1:
                raise ValueError("version")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CommandError("Respaldo inválido.") from exc
        allowed = {"description", "ingredients", "nutritional_information", "allergens"}
        with transaction.atomic():
            for change in changes:
                before, after = change["before"], change["after"]
                if not before or set(before) != set(after) or not set(before).issubset(allowed):
                    raise CommandError("El respaldo contiene campos inesperados.")
                product = Product.objects.select_for_update().filter(pk=change["id"], sku=change["sku"]).first()
                if product is None or any(getattr(product, key) != value for key, value in after.items()):
                    raise CommandError("Hay ediciones posteriores; no se restauró ningún producto.")
                Product.objects.filter(pk=product.pk).update(**before, updated_at=timezone.now())
        self.stdout.write(self.style.SUCCESS(f"Restaurados {len(changes)} productos."))
