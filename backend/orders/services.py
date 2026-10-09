import hashlib
import json
from decimal import Decimal
from django.conf import settings

from django.db import IntegrityError, transaction
from rest_framework.exceptions import APIException, ValidationError

from catalog.models import Product
from .models import Order, OrderItem


class OrderConflict(APIException):
    status_code = 409
    default_detail = "El pedido cambió. Revisa el resumen antes de confirmar."


def build_quote(items, *, lock=False):
    products = Product.objects.filter(
        pk__in=[item["product_id"] for item in items],
        published=True, available=True, category__active=True, station__active=True,
    ).select_related("category", "station").order_by("pk")
    if lock:
        # Preserve price consistency without blocking stock ledger foreign-key inserts.
        products = products.select_for_update(of=("self",), no_key=True)
    catalog = {product.pk: product for product in products}
    missing = [item["product_id"] for item in items if item["product_id"] not in catalog]
    if missing:
        raise ValidationError({"detail": "Hay productos que ya no están disponibles. Regresa al carrito y retíralos.",
                               "unavailable_product_ids": missing})

    total = Decimal("0.00")
    lines = []
    for item in items:
        product = catalog[item["product_id"]]
        line_total = product.sale_price * item["quantity"]
        total += line_total
        lines.append({"product_id": product.pk, "name": product.name,
                      "station_code": product.station.code, "quantity": item["quantity"],
                      "unit_price": product.sale_price, "line_total": line_total})
    return lines, total


def create_demo_order(data, idempotency_key):
    payload_hash = hashlib.sha256(
        json.dumps(data, sort_keys=True, default=str, ensure_ascii=False).encode()
    ).hexdigest()

    def replay(order):
        if order.request_hash != payload_hash:
            raise OrderConflict("La clave de este intento ya se utilizó con otro pedido.")
        return order, False

    existing = Order.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        return replay(existing)

    if not getattr(settings, "PRODUCTION_DEMO_ENABLED", False):
        raise ValidationError({"detail": "La preparación de demostración no está habilitada. No se ha creado el pedido."})

    try:
        with transaction.atomic():
            # La unicidad de la clave también protege dos solicitudes concurrentes.
            order = Order.objects.create(
                idempotency_key=idempotency_key, request_hash=payload_hash,
                customer_name=data["customer_name"], fulfillment=data["fulfillment"],
                table_label=data["table_label"],
            )
            lines, total = build_quote(data["items"], lock=True)
            if any(line["station_code"] not in ("KITCHEN", "BAR") for line in lines):
                raise ValidationError({"detail": "Hay productos sin estación de cocina o barra. Retíralos del carrito o consulta al personal."})
            if total != data["expected_total"]:
                raise OrderConflict("Los precios cambiaron. Actualiza el resumen y confirma el nuevo total.")
            OrderItem.objects.bulk_create([OrderItem(order=order, **line) for line in lines])
            order.total = total
            order.save(update_fields=["total"])
            from production.services import release_checkout_order
            release_checkout_order(order.pk)
            order.refresh_from_db()
            return order, True
    except IntegrityError:
        existing = Order.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return replay(existing)
        raise
