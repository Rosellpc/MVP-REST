"""Network operations outside transactions; locked state transitions claim each POST once."""
import hashlib
import json
from django.db import transaction
from django.utils import timezone
from orders.models import Order
from orders.services import OrderConflict
from stock.services import control_lock, bump
from . import culqi
from .models import Payment, PaymentAttempt, StockReservation
from .services import begin_attempt


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def update_state(attempt, status):
    attempt.status = status
    attempt.save(update_fields=["status", "updated_at"])
    Payment.objects.filter(pk=attempt.payment_id).update(status=status, updated_at=timezone.now())
    Order.objects.filter(pk=attempt.payment.order_id).update(payment_status=status)


@transaction.atomic
def finish_non_success(attempt_id, status):
    reference = PaymentAttempt.objects.select_related("payment").get(pk=attempt_id)
    order = Order.objects.select_for_update().get(pk=reference.payment.order_id)
    control = control_lock()
    attempt = PaymentAttempt.objects.select_related("payment").get(pk=attempt_id)
    if attempt.status in ("PAID", "FAILED"):
        return
    # An old uncertain response must not overwrite a later REVIEW or completed 3DS POST.
    if status == "UNKNOWN" and attempt.status != "PROCESSING":
        return
    update_state(attempt, status)
    if status == "FAILED":
        StockReservation.objects.filter(order=order, status="PROCESSING").update(status="RELEASED", updated_at=timezone.now())
        order.status = "CANCELLED"
        order.save(update_fields=["status"])
        bump(control)


def submit_charge(order_id, key, data):
    culqi.require_configured()
    source_hash = digest(data["source_id"])
    fingerprint = digest(json.dumps({k: data[k] for k in ("source_id", "email", "device_id")}, sort_keys=True))
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        attempt = begin_attempt(order.pk, key)
        if attempt.request_fingerprint and attempt.request_fingerprint != fingerprint:
            raise OrderConflict("No cambies tarjeta, correo o dispositivo durante el mismo intento.")
        authentication = data.get("authentication_3DS")
        if attempt.request_fingerprint:
            if not authentication or attempt.status != "REQUIRES_ACTION":
                return
            update_state(attempt, "PROCESSING")
        elif authentication:
            raise OrderConflict("Primero inicia el cargo antes de enviar la autenticación 3DS.")
        attempt.request_fingerprint = fingerprint
        attempt.source_fingerprint = source_hash
        attempt.save(update_fields=["request_fingerprint", "source_fingerprint"])
        payment = attempt.payment
        body = {"amount": payment.amount_minor, "currency_code": payment.currency,
                "email": data["email"], "source_id": data["source_id"], "capture": True,
                "description": f"Pedido {order.pk} - integracion",
                "metadata": {"order_code": str(order.public_code), "attempt_key": str(attempt.key)},
                "antifraud_details": {"device_finger_print_id": data["device_id"]}}
        if authentication:
            body["authentication_3DS"] = authentication
    try:
        status, response = culqi.api("POST", "charges", body)
        if response.get("action_code") == "REVIEW" and status in (200, 201):
            finish_non_success(attempt.pk, "REQUIRES_ACTION")
        elif response.get("id", "").startswith("chr_test_") or response.get("charge_id", "").startswith("chr_test_"):
            charge_id = response.get("id") or response["charge_id"]
            # Record reference before GET, so an interrupted verification remains recoverable.
            with transaction.atomic():
                Order.objects.select_for_update().get(pk=order_id)
                current = PaymentAttempt.objects.get(pk=attempt.pk)
                if current.provider_charge_id and current.provider_charge_id != charge_id:
                    raise OrderConflict("El intento tiene otra referencia de cargo. Requiere revisión.")
                current.provider_charge_id = charge_id
                current.save(update_fields=["provider_charge_id"])
            verify_charge(attempt.pk, culqi.get_charge(charge_id))
        elif status in (401, 403):
            finish_non_success(attempt.pk, "FAILED")
        elif response.get("type") == "card_error" and response.get("decline_code") in (
            "insufficient_funds", "card_expired", "incorrect_cvv", "stolen_card", "lost_card",
        ):
            finish_non_success(attempt.pk, "FAILED")
        else:
            finish_non_success(attempt.pk, "UNKNOWN")
    except culqi.CulqiUnavailable:
        finish_non_success(attempt.pk, "UNKNOWN")
        raise


@transaction.atomic
def verify_charge(attempt_id, charge):
    """Only call with an authenticated provider GET result, never a browser/webhook body."""
    reference = PaymentAttempt.objects.select_related("payment").get(pk=attempt_id)
    order = Order.objects.select_for_update().get(pk=reference.payment.order_id)
    control = control_lock()
    attempt = PaymentAttempt.objects.select_related("payment").get(pk=attempt_id)
    payment = attempt.payment
    metadata = charge.get("metadata") or {}
    source = charge.get("source") or {}
    if (charge.get("object") != "charge" or not str(charge.get("id", "")).startswith("chr_test_")
        or payment.environment != "test" or charge.get("amount") != payment.amount_minor
        or charge.get("currency_code") != payment.currency
        or metadata.get("order_code") != str(order.public_code) or metadata.get("attempt_key") != str(attempt.key)
        or digest(str(source.get("id", ""))) != attempt.source_fingerprint
        or (attempt.provider_charge_id and attempt.provider_charge_id != charge.get("id"))):
        raise OrderConflict("El cargo no coincide con este intento. Se conserva para conciliación.")
    if attempt.status == "PAID":
        return
    outcome = charge.get("outcome") or {}
    success = outcome.get("type") in ("venta_exitosa", "succesfull_request") and charge.get("capture") is True
    if not success:
        if outcome.get("type") == "operacion_denegada":
            finish_non_success(attempt.pk, "FAILED")
        return
    if charge.get("amount_refunded", 0) != 0 or attempt.status == "FAILED":
        raise OrderConflict("El cargo requiere revisión de devolución; no se libera a producción automáticamente.")
    reservation = StockReservation.objects.get(order=order)
    if not control.enabled or reservation.status != "PROCESSING" or reservation.shift.closed_at is not None:
        raise OrderConflict("Pago detectado sin reserva activa. Requiere conciliación antes de preparar.")
    attempt.provider_charge_id = charge["id"]
    attempt.verified_at = timezone.now()
    attempt.save(update_fields=["provider_charge_id", "verified_at"])
    update_state(attempt, "PAID")
    order.status, order.payment_status = "CONFIRMED", "PAID"
    order.save(update_fields=["status", "payment_status"])
    reservation.status = "CONSUMED"
    reservation.save(update_fields=["status", "updated_at"])
    # Remove only this hold before consumption, inside the same stock/order transaction.
    from production.services import release_paid_test_order
    release_paid_test_order(order.pk)
    # consume_order already advanced the stock revision in the same transaction.


def reconcile(attempt_id):
    attempt = PaymentAttempt.objects.select_related("payment__order").get(pk=attempt_id)
    if attempt.status in ("PAID", "FAILED") or not attempt.source_fingerprint:
        return
    if attempt.provider_charge_id:
        return verify_charge(attempt.pk, culqi.get_charge(attempt.provider_charge_id))
    # Bounded pagination; absence is NOT evidence of failure. Never issue another POST.
    after = None
    for _ in range(10):
        page = culqi.list_charges(attempt.created_at, after)
        rows = page["data"]
        for charge in rows:
            if (charge.get("metadata") or {}).get("attempt_key") == str(attempt.key):
                return verify_charge(attempt.pk, culqi.get_charge(charge["id"]))
        if not rows or not (page.get("paging") or {}).get("next"):
            return
        next_after = rows[-1].get("id")
        if not next_after or next_after == after:
            return
        after = next_after


@transaction.atomic
def abandon_unsubmitted(order_id):
    """Only before a POST or after explicit REVIEW while no 3DS POST is in flight."""
    order = Order.objects.select_for_update().get(pk=order_id)
    control = control_lock()
    payment = Payment.objects.get(order=order)
    if payment.status not in ("PENDING", "REQUIRES_ACTION"):
        raise OrderConflict("El cargo ya está en proceso o necesita conciliación. No se puede liberar la reserva.")
    if payment.attempts.filter(status__in=["PROCESSING", "UNKNOWN", "PAID"]).exists():
        raise OrderConflict("Hay un intento sin resultado definitivo.")
    payment.attempts.filter(status="REQUIRES_ACTION").update(status="FAILED", updated_at=timezone.now())
    payment.status = "FAILED"
    payment.save(update_fields=["status", "updated_at"])
    order.status, order.payment_status = "CANCELLED", "FAILED"
    order.save(update_fields=["status", "payment_status"])
    StockReservation.objects.filter(order=order, status__in=["HELD", "PROCESSING"]).update(status="RELEASED", updated_at=timezone.now())
    bump(control)
