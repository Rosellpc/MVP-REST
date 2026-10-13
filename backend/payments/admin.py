from django.contrib import admin
from .models import Payment, PaymentAttempt, StockReservation


class ReadOnlyPaymentAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(ReadOnlyPaymentAdmin):
    list_display = ["id", "order", "environment", "amount_minor", "currency", "status", "created_at"]
    list_filter = ["status", "environment"]
    list_select_related = ["order"]


@admin.register(PaymentAttempt)
class AttemptAdmin(ReadOnlyPaymentAdmin):
    list_display = ["key", "payment", "status", "provider_charge_id", "created_at"]


@admin.register(StockReservation)
class ReservationAdmin(ReadOnlyPaymentAdmin):
    list_display = ["id", "order", "shift", "status", "expires_at"]
    list_filter = ["status"]
