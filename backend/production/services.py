from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from orders.models import Order
from .models import ProductionTicket, ProductionTicketItem, TicketEvent
from .permissions import require_permission


class Conflict(APIException):
    status_code = 409
    default_detail = "La operación no es compatible con el estado actual."


def require_demo_enabled():
    if not getattr(settings, "PRODUCTION_DEMO_ENABLED", False):
        raise PermissionDenied("La producción de demostración no está habilitada.")


@transaction.atomic
def release_order_to_production(order_id, actor):
    require_permission(actor, "release_order")
    return _release_order(order_id, actor)


@transaction.atomic
def release_checkout_order(order_id):
    """Internal checkout operation; never exposed as a public release endpoint."""
    return _release_order(order_id, None)


def _release_order(order_id, actor):
    require_demo_enabled()
    order = get_object_or_404(Order.objects.select_for_update(), pk=order_id)
    if order.status != "DEMO_CONFIRMED" or order.payment_status != "SIMULATED":
        raise Conflict("Solo se admiten pedidos confirmados de demostración.")
    if order.released_at:
        return list(order.tickets.all()), False
    lines = list(order.items.all())
    if not lines:
        raise Conflict("El pedido no contiene productos.")
    if any(line.station_code not in ("KITCHEN", "BAR") for line in lines):
        raise Conflict("El pedido contiene una estación no soportada (por ejemplo DELIVERY). No se ha liberado ningún producto.")
    tickets = []
    for station in sorted({line.station_code for line in lines}):
        ticket = ProductionTicket.objects.create(order=order, station_code=station)
        ProductionTicketItem.objects.bulk_create([
            ProductionTicketItem(ticket=ticket, order_item=line, name=line.name, quantity=line.quantity)
            for line in lines if line.station_code == station
        ])
        TicketEvent.objects.create(ticket=ticket, actor=actor, to_status="PENDING", source="STAFF" if actor else "CHECKOUT")
        tickets.append(ticket)
    order.production_status = "PENDING"
    order.released_at = timezone.now()
    order.released_by = actor
    order.save(update_fields=["production_status", "released_at", "released_by"])
    return tickets, True


def aggregate_status(order):
    states = set(order.tickets.values_list("status", flat=True))
    if states == {"CANCELLED"}:
        return "CANCELLED"
    if "CANCELLED" in states:
        return "PARTIALLY_CANCELLED"
    if states == {"READY"}:
        return "READY"
    if states.intersection({"IN_PROGRESS", "READY"}):
        return "IN_PROGRESS"
    return "PENDING"


@transaction.atomic
def finalize_ticket(ticket_id, actor):
    require_demo_enabled()
    reference = get_object_or_404(ProductionTicket, pk=ticket_id)
    require_permission(actor, f"advance_{reference.station_code.lower()}_ticket")
    Order.objects.select_for_update().get(pk=reference.order_id)
    ticket = ProductionTicket.objects.select_for_update().get(pk=ticket_id)
    if ticket.status != "READY":
        raise Conflict("Solo puedes finalizar tickets listos.")
    if ticket.archived_at is None:
        ticket.archived_at = timezone.now()
        ticket.save(update_fields=["archived_at"])
        TicketEvent.objects.create(ticket=ticket, actor=actor, from_status="READY", to_status="READY", reason="Finalizado y archivado del tablero")
    return ticket


@transaction.atomic
def transition_ticket(ticket_id, actor, target_status, reason=""):
    require_demo_enabled()
    # All operations acquire the order lock first, serializing cross-station aggregation.
    reference = get_object_or_404(ProductionTicket, pk=ticket_id)
    permission = "cancel_ticket" if target_status == "CANCELLED" else f"advance_{reference.station_code.lower()}_ticket"
    require_permission(actor, permission)
    order = Order.objects.select_for_update().get(pk=reference.order_id)
    ticket = ProductionTicket.objects.select_for_update().get(pk=ticket_id)
    reason = reason.strip()
    if target_status == "CANCELLED" and (not reason or len(reason) > 500):
        raise ValidationError({"reason": "Indica un motivo de entre 1 y 500 caracteres."})
    if ticket.status == target_status:
        return ticket
    allowed = {"PENDING": {"IN_PROGRESS", "CANCELLED"}, "IN_PROGRESS": {"READY", "CANCELLED"}}
    if target_status not in allowed.get(ticket.status, set()):
        raise Conflict("El ticket cambió de estado o la transición no está permitida. Actualiza la lista.")
    previous = ticket.status
    ticket.status = target_status
    timestamp_field = {"IN_PROGRESS": "started_at", "READY": "completed_at", "CANCELLED": "cancelled_at"}[target_status]
    setattr(ticket, timestamp_field, timezone.now())
    ticket.save(update_fields=["status", timestamp_field])
    TicketEvent.objects.create(ticket=ticket, actor=actor, from_status=previous, to_status=target_status, reason=reason)
    order.production_status = aggregate_status(order)
    order.save(update_fields=["production_status"])
    return ticket
