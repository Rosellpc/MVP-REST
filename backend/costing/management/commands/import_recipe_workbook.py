from pathlib import Path
import json
from django.core.management.base import BaseCommand, CommandError
from costing.recipe_workbook import import_recipe_book


class Command(BaseCommand):
    help = "Importa la plantilla costos-recetas.xlsx con informe de pendientes y origen."

    def add_arguments(self, parser):
        parser.add_argument("file")
        parser.add_argument("--resume", action="store_true", help="Reintenta solo recetas pendientes del mismo archivo.")

    def handle(self, *args, **options):
        path = Path(options["file"])
        if path.stat().st_size > 10_000_000:
            raise CommandError("Máximo 10 MB")
        batch, created = import_recipe_book(path.read_bytes(), path.name, resume=options["resume"])
        self.stdout.write(json.dumps({"batch_id": batch.pk, "created": created, "report": batch.report}, ensure_ascii=True))
