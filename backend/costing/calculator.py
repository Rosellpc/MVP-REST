from decimal import Decimal, ROUND_HALF_UP, localcontext
from rest_framework.exceptions import ValidationError
from .models import Ingredient

UNITS = {"g": ("mass", 1), "kg": ("mass", 1000), "ml": ("volume", 1), "l": ("volume", 1000), "unit": ("count", 1)}


def calculate(data, precise=False):
    ingredients = Ingredient.objects.filter(archived=False).in_bulk(line["ingredient_id"] for line in data["lines"])
    with localcontext() as context:
        context.prec = 40
        total = Decimal(0)
        lines = []
        for line in data["lines"]:
            ingredient = ingredients.get(line["ingredient_id"])
            if ingredient is None:
                raise ValidationError({"detail": "Uno de los insumos ya no existe."})
            dimension, factor = UNITS[line["unit"]]
            purchase_dimension, purchase_factor = UNITS[ingredient.purchase_unit]
            if dimension != purchase_dimension:
                raise ValidationError({"detail": f"{ingredient.name}: las unidades de compra y receta no son compatibles."})
            purchased = ingredient.purchase_quantity * purchase_factor
            usable = purchased * ingredient.yield_percent / 100
            denominator = usable if line["basis"] == "usable" else purchased
            cost = line["quantity"] * factor * ingredient.purchase_price / denominator
            total += cost
            lines.append({
                "ingredient_id": ingredient.pk, "name": ingredient.name,
                "quantity": str(line["quantity"]), "unit": line["unit"], "basis": line["basis"],
                "purchase_quantity": str(ingredient.purchase_quantity), "purchase_unit": ingredient.purchase_unit,
                "purchase_price": str(ingredient.purchase_price), "yield_percent": str(ingredient.yield_percent),
                "cost": str(cost.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)),
            })
        money = lambda value: str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        return {"name": data["name"], "portions": data["portions"], "currency": "PEN", "algorithm_version": 1,
                "lines": lines, "total": money(total), "per_portion": str(total / data["portions"]) if precise else money(total / data["portions"])}
