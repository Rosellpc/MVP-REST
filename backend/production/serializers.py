from rest_framework import serializers
from orders.models import Order
from .models import ProductionTicket, ProductionTicketItem


class TicketItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionTicketItem
        fields = ["id", "name", "quantity"]


class TicketSerializer(serializers.ModelSerializer):
    items = TicketItemSerializer(many=True, read_only=True)
    public_code = serializers.UUIDField(source="order.public_code", read_only=True)
    fulfillment = serializers.CharField(source="order.fulfillment", read_only=True)
    table_label = serializers.CharField(source="order.table_label", read_only=True)

    class Meta:
        model = ProductionTicket
        fields = ["id", "public_code", "fulfillment", "table_label", "station_code", "status", "demo", "created_at", "started_at", "completed_at", "cancelled_at", "archived_at", "items"]


class StaffOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "public_code", "fulfillment", "table_label", "status", "payment_status", "production_status", "created_at", "released_at"]


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)
