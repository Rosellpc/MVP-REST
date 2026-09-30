from rest_framework import serializers

from .models import Category, Product


class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")
        read_only_fields = fields


class MenuProductSerializer(serializers.ModelSerializer):
    category = MenuCategorySerializer(read_only=True)
    sale_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=True, read_only=True
    )

    class Meta:
        model = Product
        fields = ("id", "name", "description", "image_url","category", "sale_price")
        read_only_fields = fields


class MenuQuerySerializer(serializers.Serializer):
    category = serializers.IntegerField(
        required=False, min_value=1, max_value=9223372036854775807
    )
