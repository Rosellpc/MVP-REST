from django.db import transaction
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .views import CostingView
from .inventory import import_workbook, store_count, count_payload
from .models import InventoryCount, Ingredient, Recipe, RecipeVersion
from .serializers import TechnicalRecipeSerializer
from .recipe_views import recipe_snapshot


class InventoryView(CostingView):
    def get(self, request):
        return Response([count_payload(row) for row in InventoryCount.objects.prefetch_related("lines")])

    def post(self, request):
        upload = request.FILES.get("file")
        if upload:
            if upload.size > 5_000_000:
                raise ValidationError({"detail": "Máximo 5 MB."})
            count, created = import_workbook(upload.read(), upload.name, request.user, request.data.get("sheet") or None)
        else:
            count, created = store_count(request.data, request.user)
        return Response({"created": created, "inventory": count_payload(count)}, status=201 if created else 200)


class RecipeImportView(CostingView):
    @transaction.atomic
    def post(self, request):
        rows = request.data.get("recipes") if isinstance(request.data, dict) else None
        if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
            raise ValidationError({"detail": "Envía entre 1 y 100 recetas en recipes."})
        by_name = {item.name.casefold(): item.pk for item in Ingredient.objects.all()}
        names = {name.casefold() for name in Recipe.objects.values_list("name", flat=True)}
        snapshots = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or not isinstance(row.get("lines"), list):
                raise ValidationError({"detail": f"Receta {index + 1}: falta la lista lines."})
            data = dict(row)
            data["lines"] = []
            for line in row["lines"]:
                if not isinstance(line, dict):
                    raise ValidationError({"detail": f"Receta {index + 1}: ingrediente inválido."})
                item = dict(line)
                if "ingredient_name" in item:
                    name = item.pop("ingredient_name")
                    if not isinstance(name, str) or name.strip().casefold() not in by_name:
                        raise ValidationError({"detail": f"Receta {index + 1}: insumo inexistente: {name}. Regístralo primero en Insumos."})
                    item["ingredient_id"] = by_name[name.strip().casefold()]
                data["lines"].append(item)
            serializer = TechnicalRecipeSerializer(data=data)
            if not serializer.is_valid():
                raise ValidationError({"detail": f"Receta {index + 1}: {serializer.errors}"})
            name = serializer.validated_data["name"].casefold()
            if name in names:
                raise ValidationError({"detail": f"Receta {index + 1}: nombre duplicado. Usa el editor para crear otra versión."})
            names.add(name)
            snapshots.append(recipe_snapshot(serializer.validated_data))
        for snapshot in snapshots:
            recipe = Recipe.objects.create(name=snapshot["name"], current_version=1)
            RecipeVersion.objects.create(recipe=recipe, number=1, snapshot=snapshot, actor=request.user)
        return Response({"imported": len(snapshots)}, status=201)


class RecipeWorkbookView(CostingView):
    def get(self, request):
        from .models import RecipeWorkbookImport
        return Response([{"id": row.pk, "filename": row.filename, "created_at": row.created_at, "report": row.report} for row in RecipeWorkbookImport.objects.order_by("-pk")[:50]])

    def post(self, request):
        from .recipe_workbook import import_recipe_book
        upload = request.FILES.get("file")
        if upload is None or upload.size > 10_000_000:
            raise ValidationError({"detail": "Adjunta un Excel de recetas de hasta 10 MB."})
        batch, created = import_recipe_book(upload.read(), upload.name, request.user)
        return Response({"id": batch.pk, "created": created, "report": batch.report}, status=201 if created else 200)
