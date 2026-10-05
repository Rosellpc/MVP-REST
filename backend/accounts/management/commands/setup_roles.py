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
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS("Roles ADMIN, KITCHEN y BAR configurados."))
