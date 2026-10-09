import hashlib
import json
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from catalog.models import Product
from .models import StockControl, Shift, ShiftItem, Balance, Movement, Operation


class StockConflict(APIException):
    status_code = 409
    default_detail = "El stock cambió. Actualiza antes de continuar."


def control_lock():
    return StockControl.objects.select_for_update().get(pk=1)


def bump(control):
    control.revision += 1
    control.save(update_fields=["revision", "enabled"])


def active_shift():
    shift = Shift.objects.filter(closed_at__isnull=True).first()
    if not shift:
        raise StockConflict("No hay un turno de stock abierto. Solicita la apertura al responsable.")
    return shift


def move(shift, balance, kind, delta, reason, actor=None, order_item=None, reversal=None, quantity=None, pending=None):
    after = balance.quantity + delta
    if after < 0 or after > 1000000:
        raise StockConflict(f"Stock insuficiente o fuera de rango para {balance.product.name}. Disponible: {balance.quantity}.")
    balance.quantity = after
    balance.updated_at = timezone.now()
    movement = Movement(shift=shift, product=balance.product, kind=kind, delta=delta,
                                  quantity=abs(delta) if quantity is None else quantity,
                                  balance_after=after, reason=reason, actor=actor,
                                  order_item=order_item, reversal_of=reversal)
    if pending is not None:
        pending.append(movement)
    else:
        balance.save(update_fields=["quantity", "updated_at"])
        movement.save()
    return movement


def check_revision(control, data):
    if data["revision"] != control.revision:
        raise StockConflict()


@transaction.atomic
def operate(action, data, actor):
    control = control_lock()
    fingerprint = hashlib.sha256(json.dumps([action, actor.pk, data], sort_keys=True, default=str).encode()).hexdigest()
    previous = Operation.objects.filter(key=data["key"]).first()
    if previous:
        if previous.fingerprint != fingerprint:
            raise StockConflict("Esta clave ya se utilizó con otra operación.")
        return previous.result
    if action == "open":
        check_revision(control, data)
        if Shift.objects.filter(closed_at__isnull=True).exists():
            raise StockConflict("Ya existe un turno abierto.")
        products = list(Product.objects.filter(published=True, station__code__in=["KITCHEN", "BAR"]).order_by("pk"))
        # Retain inactive products with carried stock so nothing disappears silently.
        ids = {p.pk for p in products}
        products += list(Product.objects.filter(stock_balance__quantity__gt=0).exclude(pk__in=ids))
        rows = {row["product_id"]: row for row in data["items"]}
        if len(rows) != len(data["items"]) or set(rows) != {p.pk for p in products}:
            raise ValidationError({"detail": "Revisa y confirma todos los productos de la apertura."})
        shift = Shift.objects.create(opened_by=actor, opening_notes=data["notes"])
        balances = {b.product_id: b for b in Balance.objects.select_related("product")}
        Balance.objects.bulk_create([Balance(product=p) for p in products if p.pk not in balances])
        balances = {b.product_id: b for b in Balance.objects.select_related("product")}
        pending, entries = [], []
        for product in products:
            balance = balances[product.pk]
            row = rows[product.pk]
            if row["keep"] > balance.quantity:
                raise ValidationError({"detail": "La cantidad apta no puede superar el saldo anterior. Usa producción para los ingresos."})
            if row["keep"] < balance.quantity and not row["reason"].strip():
                raise ValidationError({"detail": "Justifica el descarte de sobrantes (caducidad, conservación u otro motivo)."})
            entries.append(ShiftItem(shift=shift, product=product, name=product.name, sku=product.sku, initial=balance.quantity))
            if row["keep"] != balance.quantity:
                move(shift, balance, "WASTE", row["keep"] - balance.quantity, row["reason"], actor, pending=pending)
            if row["production"]:
                move(shift, balance, "PRODUCTION", row["production"], "Producción de apertura", actor, pending=pending)
        ShiftItem.objects.bulk_create(entries)
        Movement.objects.bulk_create(pending)
        Balance.objects.bulk_update([balances[p.pk] for p in products], ["quantity", "updated_at"])
        control.enabled = True
        result = {"shift_id": shift.pk}
    elif action == "movement":
        shift = active_shift()
        if data["shift_id"] != shift.pk:
            raise StockConflict("El turno cambió. Actualiza la página.")
        item = ShiftItem.objects.filter(shift=shift, product_id=data["product_id"]).first()
        if not item:
            raise ValidationError({"detail": "El producto no pertenece al turno."})
        delta = data["quantity"]
        if data["kind"] == "WASTE":
            delta = -delta
        movement = move(shift, Balance.objects.select_related("product").get(product_id=item.product_id), data["kind"], delta, data["reason"], actor)
        result = {"movement_id": movement.pk}
    else:
        check_revision(control, data)
        shift = active_shift()
        if data["shift_id"] != shift.pk:
            raise StockConflict("El turno cambió.")
        # Await every pending/preparing order that consumed this shift, including mixed orders.
        if Movement.objects.filter(shift=shift, kind="SALE", order_item__order__production_status__in=["PENDING", "IN_PROGRESS", "PARTIALLY_CANCELLED"]).exists():
            raise StockConflict("Completa o cancela los pedidos en preparación antes de cerrar el turno.")
        items = list(shift.items.all())
        rows = {row["product_id"]: row for row in data["items"]}
        if len(rows) != len(data["items"]) or set(rows) != {item.product_id for item in items}:
            raise ValidationError({"detail": "Debes contar todos los productos del turno."})
        balances = {b.product_id: b for b in Balance.objects.select_related("product")}
        pending = []
        for item in items:
            row = rows[item.product_id]
            balance = balances[item.product_id]
            item.theoretical = balance.quantity
            item.counted = row["counted"]
            item.difference = item.counted - item.theoretical
            item.reason = row["reason"]
            if item.difference and not item.reason.strip():
                raise ValidationError({"detail": f"Justifica la diferencia de {item.name}."})
            if item.difference:
                move(shift, balance, "COUNT", item.difference, item.reason, actor, pending=pending)
        ShiftItem.objects.bulk_update(items, ["theoretical", "counted", "difference", "reason"])
        Movement.objects.bulk_create(pending)
        Balance.objects.bulk_update([balances[item.product_id] for item in items], ["quantity", "updated_at"])
        shift.closed_at = timezone.now()
        shift.closed_by = actor
        shift.notes = data["notes"]
        shift.save(update_fields=["closed_at", "closed_by", "notes"])
        result = {"shift_id": shift.pk}
    bump(control)
    Operation.objects.create(key=data["key"], fingerprint=fingerprint, result=result)
    return result


def consume_order(order, lines, actor):
    """Called once by release_order, inside its transaction and order lock."""
    control = control_lock()
    if not control.enabled:
        return
    shift = active_shift()
    for line in sorted(lines, key=lambda item: item.product_id):
        balance = Balance.objects.select_related("product").filter(product_id=line.product_id).first()
        if balance is None or not ShiftItem.objects.filter(shift=shift, product_id=line.product_id).exists():
            raise StockConflict(f"{line.name} aún no tiene stock registrado en este turno.")
        if Movement.objects.filter(kind="SALE", order_item=line).exists():
            continue
        move(shift, balance, "SALE", -line.quantity, "Checkout confirmado (pago simulado)", actor, line)
    bump(control)


def cancel_stock(order, actor):
    """Return unstarted items; reclassify prepared consumption as waste, without adding stock."""
    control = control_lock()
    sales = list(Movement.objects.filter(kind="SALE", order_item__order=order).select_related("order_item"))
    if not sales:
        return
    states = dict(order.tickets.values_list("station_code", "status"))
    for sale in sales:
        if Movement.objects.filter(reversal_of=sale).exists():
            continue
        shift = active_shift()
        if shift.pk != sale.shift_id:
            raise StockConflict("El pedido pertenece a otro turno. Requiere conciliación del responsable.")
        pending = states[sale.order_item.station_code] == "PENDING"
        balance = Balance.objects.select_related("product").get(product_id=sale.product_id)
        move(shift, balance, "RETURN" if pending else "CANCEL_WASTE", sale.quantity if pending else 0,
             "Cancelación aprobada: sin preparar" if pending else "Cancelación aprobada: preparación iniciada, sin reposición",
             actor, sale.order_item, sale, sale.quantity)
    bump(control)
