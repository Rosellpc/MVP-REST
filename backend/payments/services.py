"""Payment preparation only: no provider calls or public payment confirmation yet."""
import hashlib
import json
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from orders.models import Order, OrderItem
from orders.services import OrderConflict, build_quote
from stock.models import Balance, ShiftItem
from stock.services import active_shift, bump, control_lock
from .models import Payment, PaymentAttempt, ReservationLine, StockReservation


def require_payment_preparation():
    if not getattr(settings, "PAYMENTS_ENABLED", False):
        raise PermissionDenied("La preparación de pagos no está habilitada.")
    if getattr(settings, "PAYMENTS_ENVIRONMENT", "test") != "test":
        raise PermissionDenied("Este bloque solo admite integración de prueba; el cobro real no está implementado.")


def create_pending_order(data, idempotency_key):
    require_payment_preparation()
    fingerprint = hashlib.sha256(json.dumps(
        {"flow": "culqi-test", "data": data}, sort_keys=True, default=str, ensure_ascii=False,
    ).encode()).hexdigest()

    def replay(order):
        if order.request_hash != fingerprint or not Payment.objects.filter(order=order).exists():
            raise OrderConflict("La clave ya pertenece a otro intento de compra.")
        return order, False

    previous = Order.objects.filter(idempotency_key=idempotency_key).first()
    if previous:
        return replay(previous)
    try:
        with transaction.atomic():
            order = Order.objects.create(
                idempotency_key=idempotency_key, request_hash=fingerprint,
                customer_name=data["customer_name"], fulfillment=data["fulfillment"],
                table_label=data["table_label"], status="PENDING_PAYMENT", payment_status="PENDING",
            )
            lines, total = build_quote(data["items"], lock=True)
            if total != data["expected_total"] or total <= 0:
                raise OrderConflict("Revisa el total: debe ser positivo y coincidir con los precios actuales.")
            if not 300 <= int(total * 100) <= 999900:
                raise OrderConflict("Esta integración con 3DS admite pedidos entre S/ 3.00 y S/ 9,999.00.")
            # Same persisted mutex as demo checkout, adjustments and shift changes.
            control = control_lock()
            if not control.enabled:
                raise OrderConflict("Activa el control de stock antes de reservar un pedido para pago.")
            shift = active_shift()
            from stock.reservations import reserved_quantity
            for line in lines:
                balance = Balance.objects.filter(product_id=line["product_id"]).first()
                if balance is None or not ShiftItem.objects.filter(shift=shift, product_id=line["product_id"]).exists():
                    raise OrderConflict("Hay productos sin stock registrado en el turno.")
                if line["quantity"] > balance.quantity - reserved_quantity(line["product_id"]):
                    raise OrderConflict(f"Stock disponible insuficiente para {line['name']}.")
            order.total = total
            order.save(update_fields=["total"])
            items = [OrderItem.objects.create(order=order, **line) for line in lines]
            Payment.objects.create(order=order, amount_minor=int(total * 100), environment="test")
            minutes = max(1, min(30, getattr(settings, "PAYMENT_RESERVATION_MINUTES", 10)))
            reservation = StockReservation.objects.create(order=order, shift=shift, expires_at=timezone.now() + timedelta(minutes=minutes))
            ReservationLine.objects.bulk_create([
                ReservationLine(reservation=reservation, order_item=item, product_id=item.product_id, quantity=item.quantity)
                for item in items
            ])
            bump(control)
            return order, True
    except IntegrityError:
        previous = Order.objects.filter(idempotency_key=idempotency_key).first()
        if previous:
            return replay(previous)
        raise


@transaction.atomic
def begin_attempt(order_id, key):
    """Internal boundary for the future provider adapter; never exposed as a public action."""
    require_payment_preparation()
    order = Order.objects.select_for_update().get(pk=order_id)
    control = control_lock()
    payment = Payment.objects.get(order=order)
    previous = PaymentAttempt.objects.filter(key=key).first()
    if previous:
        if previous.payment_id != payment.pk:
            raise OrderConflict("La clave pertenece a otro pago.")
        return previous
    reservation = StockReservation.objects.get(order=order)
    if payment.status != "PENDING" or reservation.status != "HELD" or reservation.expires_at <= timezone.now():
        raise OrderConflict("El pago ya comenzó o su reserva venció. Consulta el estado antes de reintentar.")
    if not control.enabled or reservation.shift_id != active_shift().pk:
        raise OrderConflict("El turno de la reserva ya no está disponible.")
    attempt = PaymentAttempt.objects.create(payment=payment, key=key)
    payment.status = "PROCESSING"
    payment.save(update_fields=["status", "updated_at"])
    order.payment_status = "PROCESSING"
    order.save(update_fields=["payment_status"])
    reservation.status = "PROCESSING"
    reservation.save(update_fields=["status", "updated_at"])
    bump(control)
    return attempt


def expire_reservations(*, limit=500):
    """Expire only untouched reservations; uncertain/provider-started payments retain stock."""
    ids = list(StockReservation.objects.filter(status="HELD", expires_at__lte=timezone.now())
               .order_by("expires_at").values_list("order_id", flat=True)[:limit])
    expired = 0
    for order_id in ids:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order_id)
            control = control_lock()
            reservation = StockReservation.objects.get(order=order)
            payment = Payment.objects.get(order=order)
            if reservation.status != "HELD" or reservation.expires_at > timezone.now() or payment.status != "PENDING":
                continue
            # Even an anomalous attempt must be reconciled rather than automatically released.
            if payment.attempts.exists():
                continue
            reservation.status = "EXPIRED"
            reservation.save(update_fields=["status", "updated_at"])
            payment.status = "EXPIRED"
            payment.save(update_fields=["status", "updated_at"])
            order.status = "EXPIRED"
            order.payment_status = "EXPIRED"
            order.save(update_fields=["status", "payment_status"])
            bump(control)
            expired += 1
    return expired
