from rest_framework import serializers
from orders.models import Order
from orders.serializers import OrderItemSerializer
from .models import ProductionTicket, ProductionTicketItem, CancellationRequest


class CancellationSerializer(serializers.ModelSerializer):
    public_code = serializers.UUIDField(source="order.public_code", read_only=True)
    station = serializers.CharField(source="ticket.station_code", read_only=True)
    requested_by = serializers.CharField(source="requested_by.username", read_only=True)

    class Meta:
        model = CancellationRequest
        fields = ["id", "public_code", "station", "requested_by", "reason", "created_at", "approved_at", "rejected_at", "rejection_reason"]


class TicketItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionTicketItem
        fields = ["id", "name", "quantity"]


class TicketSerializer(serializers.ModelSerializer):
    cancellation_pending = serializers.SerializerMethodField()

    def get_cancellation_pending(self, obj):
        cancellation = getattr(obj.order, "cancellation_request", None)
        return cancellation is not None and cancellation.approved_at is None and cancellation.rejected_at is None
    order_number = serializers.IntegerField(source="order_id", read_only=True)
    cancellation_request = CancellationSerializer(source="order.cancellation_request", read_only=True)
    items = TicketItemSerializer(many=True, read_only=True)
    public_code = serializers.UUIDField(source="order.public_code", read_only=True)
    fulfillment = serializers.CharField(source="order.fulfillment", read_only=True)
    table_label = serializers.CharField(source="order.table_label", read_only=True)

    class Meta:
        model = ProductionTicket
        fields = ["id", "order_number", "public_code", "fulfillment", "table_label", "station_code", "status", "demo", "created_at", "started_at", "completed_at", "cancelled_at", "archived_at", "items", "cancellation_pending", "cancellation_request"]


class StaffOrderSerializer(serializers.ModelSerializer):
    cancellation_request = CancellationSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "public_code", "fulfillment", "table_label", "status", "payment_status", "production_status", "created_at", "released_at", "total", "currency", "items", "tickets", "cancellation_request"]


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)


class DirectCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False)
