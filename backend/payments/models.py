import uuid

from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        PROCESSING = "PROCESSING", "Procesando"
        REQUIRES_ACTION = "REQUIRES_ACTION", "Requiere autenticación"
        UNKNOWN = "UNKNOWN", "Resultado por conciliar"
        PAID = "PAID", "Pagado"
        FAILED = "FAILED", "Fallido"
        EXPIRED = "EXPIRED", "Vencido"
        REFUND_PENDING = "REFUND_PENDING", "Reembolso pendiente"
        REFUNDED = "REFUNDED", "Reembolsado"

    order = models.OneToOneField("orders.Order", on_delete=models.PROTECT, related_name="payment")
    provider = models.CharField(max_length=16, default="CULQI", editable=False)
    environment = models.CharField(max_length=8, default="test", editable=False)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3, default="PEN", editable=False)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount_minor__gt=0), name="payment_positive_amount"),
            models.CheckConstraint(condition=models.Q(environment__in=["test", "live"]), name="payment_valid_environment"),
            models.CheckConstraint(condition=models.Q(status__in=["PENDING", "PROCESSING", "REQUIRES_ACTION", "UNKNOWN", "PAID", "FAILED", "EXPIRED", "REFUND_PENDING", "REFUNDED"]), name="payment_valid_status"),
        ]


class PaymentAttempt(models.Model):
    # Internal attempts only. No token, PAN, CVV or provider payload is stored here.
    key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="attempts")
    status = models.CharField(max_length=24, choices=Payment.Status.choices, default=Payment.Status.PROCESSING)
    provider_charge_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    request_fingerprint = models.CharField(max_length=64, blank=True, editable=False)
    source_fingerprint = models.CharField(max_length=64, blank=True, editable=False)
    verified_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["payment"], condition=models.Q(status__in=["PROCESSING", "REQUIRES_ACTION", "UNKNOWN", "PAID"]), name="payment_one_unresolved_attempt"),
        ]


class StockReservation(models.Model):
    class Status(models.TextChoices):
        HELD = "HELD", "Reservado"
        PROCESSING = "PROCESSING", "Cobro iniciado: pendiente de conciliación"
        EXPIRED = "EXPIRED", "Vencido"
        CONSUMED = "CONSUMED", "Aplicado a venta"
        RELEASED = "RELEASED", "Liberado"

    order = models.OneToOneField("orders.Order", on_delete=models.PROTECT, related_name="stock_reservation")
    shift = models.ForeignKey("stock.Shift", on_delete=models.PROTECT, related_name="reservations")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.HELD)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(status__in=["HELD", "PROCESSING", "EXPIRED", "CONSUMED", "RELEASED"]), name="reservation_valid_status")]


class ReservationLine(models.Model):
    reservation = models.ForeignKey(StockReservation, on_delete=models.PROTECT, related_name="lines")
    order_item = models.OneToOneField("orders.OrderItem", on_delete=models.PROTECT)
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["reservation", "product"], name="reservation_unique_product"),
            models.CheckConstraint(condition=models.Q(quantity__gte=1, quantity__lte=99), name="reservation_valid_quantity"),
        ]
