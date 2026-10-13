from uuid import UUID
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from orders.models import Order
from .serializers import PreparePaymentSerializer, public_payment
from .services import create_pending_order, require_payment_preparation
from . import culqi
from .models import PaymentAttempt
from .processing import submit_charge, reconcile, verify_charge, abandon_unsubmitted
from .serializers import ChargeSerializer
from django.conf import settings
from orders.serializers import CartInputSerializer
from orders.services import build_quote


class PaymentThrottle(AnonRateThrottle):
    scope = "payment_preparation"
    rate = "10/min"


class PaymentReadThrottle(AnonRateThrottle):
    scope = "payment_read"
    rate = "120/min"


class WebhookThrottle(AnonRateThrottle):
    scope = "culqi_webhook"
    rate = "120/min"


class PaymentView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PaymentThrottle]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        require_payment_preparation()

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response


class PreparePaymentView(PaymentView):
    def post(self, request):
        try:
            key = UUID(request.headers.get("Idempotency-Key", ""))
        except (ValueError, TypeError, AttributeError):
            raise ValidationError({"detail": "Envía una Idempotency-Key UUID válida."})
        serializer = PreparePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, created = create_pending_order(serializer.validated_data, key)
        return Response(public_payment(order), status=201 if created else 200)


class PaymentQuoteView(PaymentView):
    def post(self, request):
        serializer = CartInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lines, total = build_quote(serializer.validated_data["items"])
        return Response({"items": [{key: value for key, value in line.items() if key != "station_code"} for line in lines],
                         "total": str(total), "currency": "PEN", "demo": True, "prices_include_taxes": True})


class PaymentDetailView(PaymentView):
    throttle_classes = [PaymentReadThrottle]
    def get(self, request, public_code):
        order = get_object_or_404(Order.objects.select_related("payment", "stock_reservation"),
                                  public_code=public_code, payment__isnull=False)
        return Response(public_payment(order))


class PaymentConfigView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PaymentReadThrottle]

    def get(self, request):
        ready = culqi.configured()
        response = Response({"enabled": getattr(settings, "PAYMENTS_ENABLED", False),
                             "ready": ready, "environment": "test",
                             "public_key": settings.CULQI_PUBLIC_KEY if ready else ""})
        response["Cache-Control"] = "no-store"
        return response


class ChargeView(PaymentView):
    def post(self, request, public_code):
        order = get_object_or_404(Order, public_code=public_code, payment__isnull=False)
        try:
            key = UUID(request.headers.get("Idempotency-Key", ""))
        except (ValueError, TypeError, AttributeError):
            raise ValidationError({"detail": "Envía una Idempotency-Key UUID válida."})
        serializer = ChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submit_charge(order.pk, key, serializer.validated_data)
        return Response(public_payment(Order.objects.get(pk=order.pk)))


class ReconcileView(PaymentView):
    def post(self, request, public_code):
        order = get_object_or_404(Order, public_code=public_code, payment__isnull=False)
        attempt = order.payment.attempts.order_by("-created_at").first()
        if attempt:
            reconcile(attempt.pk)
        return Response(public_payment(Order.objects.get(pk=order.pk)))


class AbandonPaymentView(PaymentView):
    def post(self, request, public_code):
        order = get_object_or_404(Order, public_code=public_code, payment__isnull=False)
        abandon_unsubmitted(order.pk)
        return Response(public_payment(Order.objects.get(pk=order.pk)))


class WebhookView(PaymentView):
    throttle_classes = [WebhookThrottle]
    def post(self, request):
        # Notification is an untrusted hint, not proof of payment. Validate via secret-key GET.
        import json
        data = request.data.get("data", {})
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                data = {}
        charge_id = data.get("id", "") if isinstance(data, dict) else ""
        if not isinstance(charge_id, str) or not charge_id.startswith("chr_test_"):
            return Response({"received": True})
        charge = culqi.get_charge(charge_id)
        attempt_key = (charge.get("metadata") or {}).get("attempt_key")
        try:
            key = UUID(str(attempt_key))
        except ValueError:
            return Response({"received": True})
        attempt = PaymentAttempt.objects.filter(key=key).first()
        if attempt:
            verify_charge(attempt.pk, charge)
        return Response({"received": True})
