from rest_framework import serializers

from .models import Order, OrderItem


class CartItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=99)


class CartInputSerializer(serializers.Serializer):
    items = CartItemInputSerializer(many=True, allow_empty=False, max_length=100)

    def validate_items(self, items):
        ids = [item["product_id"] for item in items]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("No repitas un producto; ajusta su cantidad.")
        return sorted(items, key=lambda item: item["product_id"])


class CreateOrderSerializer(CartInputSerializer):
    customer_name = serializers.CharField(max_length=80)
    fulfillment = serializers.ChoiceField(choices=Order.Fulfillment.choices)
    table_label = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    expected_total = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    accept_demo = serializers.BooleanField()

    def validate(self, attrs):
        if not attrs["accept_demo"]:
            raise serializers.ValidationError({"accept_demo": "Debes aceptar que es un pago simulado."})
        if attrs["fulfillment"] == Order.Fulfillment.DINE_IN and not attrs["table_label"]:
            raise serializers.ValidationError({"table_label": "Indica el número o nombre de la mesa."})
        if attrs["fulfillment"] == Order.Fulfillment.PICKUP:
            attrs["table_label"] = ""
        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product_id", "name", "quantity", "unit_price", "line_total"]


class PublicOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    demo = serializers.SerializerMethodField()
    prices_include_taxes = serializers.SerializerMethodField()

    def get_demo(self, obj):
        return True

    def get_prices_include_taxes(self, obj):
        return True

    class Meta:
        model = Order
        # La consulta pública no expone nombre del cliente, mesa ni clave idempotente.
        fields = ["public_code", "status", "payment_status", "currency", "total",
                  "created_at", "fulfillment", "items", "demo", "prices_include_taxes"]
