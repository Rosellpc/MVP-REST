from decimal import Decimal, ROUND_HALF_UP, localcontext
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .views import CostingView
from .models import Ingredient, IngredientRevision, Recipe, RecipeVersion, CostingChange
from .serializers import IngredientSerializer, IngredientEditSerializer, TechnicalRecipeSerializer
from .calculator import calculate


def money(value):
    with localcontext() as context:
        context.prec = 50
        return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def recipe_snapshot(data):
    result = calculate(data, precise=True)
    for key, value in data.items():
        if key not in ("lines", "expected_version"):
            result[key] = str(value) if isinstance(value, Decimal) else value
    net = data["selling_price"] / (1 + data["tax_percent"] / 100)
    cost = Decimal(result["per_portion"])
    result.update(net_price=money(net), margin=money(net - cost),
                  food_cost_percent=money(cost / net * 100) if net else None)
    result["per_portion"] = money(cost)
    return result


def version_payload(version):
    return {"id": version.pk, "recipe_id": version.recipe_id, "number": version.number,
            "snapshot": version.snapshot, "created_at": version.created_at,
            "author": version.actor.get_username() if version.actor else "Importación administrativa"}


class IngredientDetailView(CostingView):
    @transaction.atomic
    def delete(self, request, pk):
        item = get_object_or_404(Ingredient.objects.select_for_update(), pk=pk, archived=False)
        CostingChange.objects.create(entity="ingredient", object_id=item.pk, action="delete", before=dict(IngredientSerializer(item).data), actor=request.user)
        item.archived = True
        item.save(update_fields=["archived"])
        return Response({"deleted": True})

    def get(self, request, pk):
        item = get_object_or_404(Ingredient, pk=pk)
        return Response({"ingredient": IngredientSerializer(item).data, "history": [
            {"snapshot": row.snapshot, "reason": row.reason, "created_at": row.created_at,
             "author": row.actor.get_username() if row.actor else "Importación administrativa"} for row in item.history.select_related("actor").order_by("-pk")
        ]})

    @transaction.atomic
    def put(self, request, pk):
        item = get_object_or_404(Ingredient.objects.select_for_update(), pk=pk, archived=False)
        serializer = IngredientEditSerializer(item, data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.pop("reason")
        if not item.history.exists():
            IngredientRevision.objects.create(ingredient=item, snapshot=dict(IngredientSerializer(item).data), reason="Referencia previa a la primera edición", actor=request.user)
        serializer.save()
        IngredientRevision.objects.create(ingredient=item, snapshot=dict(IngredientSerializer(item).data), reason=reason, actor=request.user)
        return Response(IngredientSerializer(item).data)


class ImportIngredientsView(CostingView):
    @transaction.atomic
    def post(self, request):
        rows = request.data.get("ingredients") if isinstance(request.data, dict) else None
        if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
            raise ValidationError({"detail": "Envía entre 1 y 500 insumos en ingredients."})
        names = {name.strip().casefold() for name in Ingredient.objects.values_list("name", flat=True)}
        validated = []
        for index, row in enumerate(rows):
            serializer = IngredientSerializer(data=row)
            if not serializer.is_valid():
                raise ValidationError({"detail": f"Fila {index + 1}: {serializer.errors}"})
            name = serializer.validated_data["name"].casefold()
            if name in names:
                raise ValidationError({"detail": f"Fila {index + 1}: nombre duplicado."})
            names.add(name)
            validated.append(serializer)
        for serializer in validated:
            item = serializer.save()
            IngredientRevision.objects.create(ingredient=item, snapshot=dict(serializer.data), reason="Importación JSON", actor=request.user)
        return Response({"imported": len(validated)}, status=201)


class RecipePreviewView(CostingView):
    def post(self, request):
        serializer = TechnicalRecipeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(recipe_snapshot(serializer.validated_data))


class RecipesView(CostingView):
    def get(self, request):
        # One query for current versions; historical snapshots are never recalculated.
        from django.db.models import F
        rows = RecipeVersion.objects.filter(number=F("recipe__current_version"), recipe__archived=False).select_related("actor").order_by("-created_at")
        return Response([version_payload(row) for row in rows])

    @transaction.atomic
    def post(self, request):
        serializer = TechnicalRecipeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        snapshot = recipe_snapshot(serializer.validated_data)
        recipe = Recipe.objects.create(name=snapshot["name"], current_version=1)
        version = RecipeVersion.objects.create(recipe=recipe, number=1, snapshot=snapshot, actor=request.user)
        return Response(version_payload(version), status=201)


class RecipeDetailView(CostingView):
    @transaction.atomic
    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe.objects.select_for_update(), pk=pk, archived=False)
        CostingChange.objects.create(entity="recipe", object_id=recipe.pk, action="delete", before={"name": recipe.name, "current_version": recipe.current_version}, actor=request.user)
        recipe.archived = True
        recipe.save(update_fields=["archived"])
        return Response({"deleted": True})

    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response([version_payload(row) for row in recipe.versions.select_related("actor")])

    @transaction.atomic
    def post(self, request, pk):
        recipe = get_object_or_404(Recipe.objects.select_for_update(), pk=pk, archived=False)
        serializer = TechnicalRecipeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("expected_version") != recipe.current_version:
            return Response({"detail": "La receta cambió. Vuelve a abrir su última versión antes de guardar."}, status=409)
        snapshot = recipe_snapshot(serializer.validated_data)
        recipe.current_version += 1
        recipe.name = snapshot["name"]
        recipe.save(update_fields=["current_version", "name"])
        version = RecipeVersion.objects.create(recipe=recipe, number=recipe.current_version, snapshot=snapshot, actor=request.user)
        return Response(version_payload(version), status=201)


class SummaryView(CostingView):
    def get(self, request):
        from django.db.models import F
        rows = list(RecipeVersion.objects.filter(number=F("recipe__current_version"), recipe__archived=False).values_list("snapshot", flat=True))
        priced = [row for row in rows if row["food_cost_percent"] is not None]
        return Response({"ingredients": Ingredient.objects.filter(archived=False).count(), "recipes": len(rows),
                         "versions": RecipeVersion.objects.count(), "priced_recipes": len(priced),
                         "average_food_cost": money(sum((Decimal(row["food_cost_percent"]) for row in priced), Decimal(0)) / len(priced)) if priced else None})
