from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.roles import ROLE_PERMISSIONS


class Command(BaseCommand):
    help = "Configura grupos internos. Ejecutar después de migrate. No crea usuarios."

    @transaction.atomic
    def handle(self, *args, **options):
        for name, codes in ROLE_PERMISSIONS.items():
            permissions = list(Permission.objects.filter(
                content_type__app_label="accounts", codename__in=codes,
            ))
            if len(permissions) != len(codes):
                raise CommandError("Faltan permisos. Ejecuta migrate primero.")
            if name == "ADMIN":
                permissions += list(Permission.objects.filter(content_type__app_label="catalog"))
            production_codes = {
                "ADMIN": {"release_order", "view_kitchen_ticket", "advance_kitchen_ticket", "view_bar_ticket", "advance_bar_ticket", "cancel_ticket", "view_productionticket", "view_productionticketitem", "view_ticketevent"},
                "KITCHEN": {"view_kitchen_ticket", "advance_kitchen_ticket"},
                "BAR": {"view_bar_ticket", "advance_bar_ticket"},
            }[name]
            production_permissions = list(Permission.objects.filter(content_type__app_label="production", codename__in=production_codes))
            if len(production_permissions) != len(production_codes):
                raise CommandError("Faltan permisos de producción. Ejecuta migrate primero.")
            permissions += production_permissions
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS("Roles ADMIN, KITCHEN y BAR configurados."))
