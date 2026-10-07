from decimal import Decimal
from rest_framework import serializers
from .models import Ingredient, CostStudy

UNITS = ("g", "kg", "ml", "l", "unit")


class IngredientSerializer(serializers.ModelSerializer):
    purchase_unit = serializers.ChoiceField(choices=UNITS)
    purchase_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    purchase_price = serializers.DecimalField(max_digits=12, decimal_places=4, min_value=Decimal("0"))
    yield_percent = serializers.DecimalField(max_digits=6, decimal_places=3, min_value=Decimal("0.001"), max_value=Decimal("100"))

    class Meta:
        model = Ingredient
        fields = ("id", "name", "purchase_unit", "purchase_quantity", "purchase_price", "yield_percent", "created_at")
        read_only_fields = ("id", "created_at")


class LineSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    unit = serializers.ChoiceField(choices=UNITS)
    basis = serializers.ChoiceField(choices=("gross", "usable"))


class RecipeInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    portions = serializers.IntegerField(min_value=1, max_value=100000)
    lines = LineSerializer(many=True, allow_empty=False, max_length=200)


class StudySerializer(serializers.ModelSerializer):
    class Meta:
        model = CostStudy
        fields = ("id", "name", "snapshot", "created_at")


class TechnicalRecipeSerializer(RecipeInputSerializer):
    category = serializers.CharField(max_length=100, allow_blank=True, default="")
    portion_size = serializers.CharField(max_length=100, allow_blank=True, default="")
    preparation_minutes = serializers.IntegerField(min_value=0, max_value=100000, default=0, allow_null=True)
    cooking_minutes = serializers.IntegerField(min_value=0, max_value=100000, default=0, allow_null=True)
    temperature = serializers.CharField(max_length=100, allow_blank=True, default="")
    preparation = serializers.CharField(max_length=20000, allow_blank=True, default="")
    presentation = serializers.CharField(max_length=10000, allow_blank=True, default="")
    allergens = serializers.CharField(max_length=2000, allow_blank=True, default="")
    selling_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"), default=Decimal("0"))
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100"), default=Decimal("0"))
    expected_version = serializers.IntegerField(min_value=1, required=False)


class IngredientEditSerializer(IngredientSerializer):
    reason = serializers.CharField(max_length=250, write_only=True)

    class Meta(IngredientSerializer.Meta):
        fields = IngredientSerializer.Meta.fields + ("reason",)
