from django.conf import settings
from django.db import models


class ProductionTicket(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        IN_PROGRESS = "IN_PROGRESS", "En preparación"
        READY = "READY", "Listo"
        CANCELLED = "CANCELLED", "Cancelado"

    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="tickets")
    station_code = models.CharField(max_length=20, choices=[("KITCHEN", "Cocina"), ("BAR", "Barra")])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    demo = models.BooleanField(default=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["created_at", "pk"]
        permissions = [
            ("release_order", "Puede liberar pedidos de demostración"),
            ("view_kitchen_ticket", "Puede consultar tickets de cocina"),
            ("advance_kitchen_ticket", "Puede avanzar tickets de cocina"),
            ("view_bar_ticket", "Puede consultar tickets de barra"),
            ("advance_bar_ticket", "Puede avanzar tickets de barra"),
            ("cancel_ticket", "Puede cancelar tickets"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["order", "station_code"], name="ticket_unique_order_station"),
            models.CheckConstraint(condition=models.Q(station_code__in=["KITCHEN", "BAR"]), name="ticket_valid_station"),
            models.CheckConstraint(condition=models.Q(status__in=["PENDING", "IN_PROGRESS", "READY", "CANCELLED"]), name="ticket_valid_status"),
            models.CheckConstraint(condition=models.Q(demo=True), name="ticket_demo_only"),
        ]


class ProductionTicketItem(models.Model):
    ticket = models.ForeignKey(ProductionTicket, on_delete=models.PROTECT, related_name="items")
    order_item = models.OneToOneField("orders.OrderItem", on_delete=models.PROTECT, related_name="ticket_item")
    name = models.CharField(max_length=150)
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["pk"]
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gte=1, quantity__lte=99), name="ticket_item_valid_quantity")]


class TicketEvent(models.Model):
    ticket = models.ForeignKey(ProductionTicket, on_delete=models.PROTECT, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    source = models.CharField(max_length=20, default="STAFF", choices=[("STAFF", "Personal"), ("CHECKOUT", "Checkout automático")])
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    reason = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]


class CancellationRequest(models.Model):
    order = models.OneToOneField("orders.Order", on_delete=models.PROTECT, related_name="cancellation_request")
    ticket = models.ForeignKey(ProductionTicket, on_delete=models.PROTECT)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cancellation_requests")
    reason = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="approved_cancellations")
