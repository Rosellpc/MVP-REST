import uuid

from django.db import models


class Order(models.Model):
    class Fulfillment(models.TextChoices):
        DINE_IN = "DINE_IN", "En mesa"
        PICKUP = "PICKUP", "Para recoger"

    public_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    idempotency_key = models.UUIDField(unique=True, editable=False)
    request_hash = models.CharField(max_length=64, editable=False)
    customer_name = models.CharField(max_length=80)
    fulfillment = models.CharField(max_length=10, choices=Fulfillment.choices)
    table_label = models.CharField(max_length=20, blank=True)
    # El checkout no libera producción; requiere una acción interna explícita.
    status = models.CharField(max_length=20, default="DEMO_CONFIRMED", editable=False)
    payment_status = models.CharField(max_length=20, default="SIMULATED", editable=False)
    currency = models.CharField(max_length=3, default="PEN", editable=False)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    production_status = models.CharField(max_length=24, default="NOT_RELEASED", editable=False)
    released_at = models.DateTimeField(null=True, blank=True, editable=False)
    released_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.PROTECT, related_name="released_orders", editable=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(production_status__in=["NOT_RELEASED", "PENDING", "IN_PROGRESS", "READY", "CANCELLED", "PARTIALLY_CANCELLED"]), name="order_valid_production_status"),
            models.CheckConstraint(condition=models.Q(total__gte=0), name="order_total_nonnegative"),
            models.CheckConstraint(
                condition=models.Q(fulfillment__in=["DINE_IN", "PICKUP"]),
                name="order_valid_fulfillment",
            ),
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    # Fotografías del catálogo al confirmar; no cambian con ediciones posteriores.
    name = models.CharField(max_length=150)
    station_code = models.CharField(max_length=20)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveSmallIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["order", "product"], name="order_unique_product"),
            models.CheckConstraint(condition=models.Q(quantity__gte=1, quantity__lte=99), name="order_item_valid_quantity"),
            models.CheckConstraint(condition=models.Q(unit_price__gte=0, line_total__gte=0), name="order_item_nonnegative"),
        ]
