from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError
from costing.inventory import import_workbook, count_payload


class Command(BaseCommand):
    help = "Importa un conteo de la plantilla Excel sin afectar stock ni recetas; repetir el mismo archivo no duplica datos."

    def add_arguments(self, parser):
        parser.add_argument("file")
        parser.add_argument("--sheet")

    def handle(self, *args, **options):
        path = Path(options["file"])
        try:
            if path.stat().st_size > 5_000_000:
                raise CommandError("Máximo 5 MB.")
            count, created = import_workbook(path.read_bytes(), path.name, sheet_name=options["sheet"])
        except (OSError, ValidationError) as exc:
            raise CommandError(str(exc)) from exc
        data = count_payload(count)
        self.stdout.write(f'ID={count.pk}; created={created}; example={count.is_example}; rows={len(data["lines"])}; total={data["total"]}; currency={count.currency or "unspecified"}')
