from uuid import UUID

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import Order
from .serializers import CartInputSerializer, CreateOrderSerializer, PublicOrderSerializer
from .services import build_quote, create_demo_order


class OrderThrottle(AnonRateThrottle):
    scope = "demo_orders"
    rate = "30/min"


class DemoOrderView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [OrderThrottle]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not getattr(settings, "ORDER_DEMO_ENABLED", False):
            raise PermissionDenied("La compra de demostración no está habilitada.")


class PreviewOrderView(DemoOrderView):
    def post(self, request):
        serializer = CartInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lines, total = build_quote(serializer.validated_data["items"])
        return Response({
            "items": [{key: (str(value) if key in ("unit_price", "line_total") else value)
                       for key, value in line.items() if key != "station_code"} for line in lines],
            "total": str(total), "currency": "PEN", "prices_include_taxes": True, "demo": True,
        })


class CreateOrderView(DemoOrderView):
    def post(self, request):
        try:
            key = UUID(request.headers.get("Idempotency-Key", ""))
        except (ValueError, TypeError, AttributeError):
            raise ValidationError({"detail": "Envía una Idempotency-Key UUID válida."})
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, created = create_demo_order(serializer.validated_data, key)
        return Response(PublicOrderSerializer(order).data, status=201 if created else 200)


class OrderDetailView(DemoOrderView):
    def get(self, request, public_code):
        order = get_object_or_404(Order.objects.prefetch_related("items"), public_code=public_code)
        return Response(PublicOrderSerializer(order).data)
