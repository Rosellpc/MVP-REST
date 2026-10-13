from rest_framework import serializers
from orders.models import Order
from orders.serializers import CartInputSerializer
from .culqi import configured


class PreparePaymentSerializer(CartInputSerializer):
    customer_name = serializers.CharField(max_length=80)
    fulfillment = serializers.ChoiceField(choices=Order.Fulfillment.choices)
    table_label = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    expected_total = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)

    def validate(self, attrs):
        if attrs["fulfillment"] == "DINE_IN" and not attrs["table_label"]:
            raise serializers.ValidationError({"table_label": "Indica la mesa."})
        if attrs["fulfillment"] == "PICKUP":
            attrs["table_label"] = ""
        return attrs


def public_payment(order):
    payment = order.payment
    reservation = order.stock_reservation
    return {
        "public_code": str(order.public_code), "status": order.status,
        "payment_status": payment.status, "production_status": order.production_status,
        "total": str(order.total), "amount_minor": payment.amount_minor,
        "currency": payment.currency, "environment": payment.environment,
        "provider": payment.provider, "reservation_status": reservation.status,
        "reservation_expires_at": reservation.expires_at.isoformat(),
        "charging_available": configured(),
    }


class Authentication3DSSerializer(serializers.Serializer):
    eci = serializers.CharField(max_length=10)
    xid = serializers.CharField(max_length=1024)
    cavv = serializers.CharField(max_length=1024)
    protocolVersion = serializers.CharField(max_length=20)
    directoryServerTransactionId = serializers.CharField(max_length=100, required=False, allow_blank=True)


class ChargeSerializer(serializers.Serializer):
    source_id = serializers.RegexField(r"^(tkn|ype)_test_[A-Za-z0-9]+$", max_length=100)
    email = serializers.EmailField(max_length=254)
    device_id = serializers.CharField(max_length=200)
    authentication_3DS = Authentication3DSSerializer(required=False)
