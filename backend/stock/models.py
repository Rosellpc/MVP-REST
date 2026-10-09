from django.conf import settings
from django.db import models


class StockControl(models.Model):
    # One persisted mutex serializes checkout, manual movements and shift changes.
    enabled = models.BooleanField(default=False)
    revision = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(pk=1), name="stock_single_control")]
        permissions = [("view_stock", "Consultar stock"), ("manage_stock", "Gestionar stock y turnos")]


class Shift(models.Model):
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True)
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_openings")
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_closings", null=True)
    notes = models.TextField(blank=True)
    opening_notes = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(models.Value(1), condition=models.Q(closed_at__isnull=True), name="stock_one_open_shift")]


class Balance(models.Model):
    product = models.OneToOneField("catalog.Product", on_delete=models.PROTECT, related_name="stock_balance")
    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


class ShiftItem(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50)
    initial = models.PositiveIntegerField()
    theoretical = models.PositiveIntegerField(null=True)
    counted = models.PositiveIntegerField(null=True)
    difference = models.IntegerField(null=True)
    reason = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["shift", "product"], name="stock_unique_shift_product")]


class Movement(models.Model):
    class Kind(models.TextChoices):
        PRODUCTION = "PRODUCTION", "Producción"
        SALE = "SALE", "Venta (demostración)"
        RETURN = "RETURN", "Cancelación sin preparar"
        CANCEL_WASTE = "CANCEL_WASTE", "Cancelación preparada"
        WASTE = "WASTE", "Merma / descarte"
        ADJUST = "ADJUST", "Ajuste"
        COUNT = "COUNT", "Conciliación de cierre"

    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name="movements")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    delta = models.IntegerField()
    quantity = models.PositiveIntegerField()
    balance_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.PROTECT, null=True)
    reversal_of = models.OneToOneField("self", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        indexes = [models.Index(fields=["product", "created_at"])]
        constraints = [models.UniqueConstraint(fields=["order_item"], condition=models.Q(kind="SALE"), name="stock_sale_once")]


class Operation(models.Model):
    key = models.UUIDField(unique=True)
    fingerprint = models.CharField(max_length=64)
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
