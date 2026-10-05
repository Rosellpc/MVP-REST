from django.contrib import admin
from .models import ProductionTicket, ProductionTicketItem, TicketEvent


class AuditAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductionTicket)
class TicketAdmin(AuditAdmin):
    list_display = ["id", "order", "station_code", "status", "demo", "created_at"]
    list_filter = ["station_code", "status"]


admin.site.register(ProductionTicketItem, AuditAdmin)
admin.site.register(TicketEvent, AuditAdmin)
