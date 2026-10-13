from django.core.management.base import BaseCommand
from rest_framework.exceptions import APIException
from payments.models import PaymentAttempt
from payments.processing import reconcile
from payments.services import expire_reservations


class Command(BaseCommand):
    help = "Consulta hasta 50 intentos pendientes en Culqi y vence reservas sin cobro. Nunca crea cargos."

    def handle(self, *args, **options):
        failures = 0
        attempts = PaymentAttempt.objects.filter(status__in=["PROCESSING", "UNKNOWN", "REQUIRES_ACTION"]).order_by("updated_at")[:50]
        for attempt in attempts:
            try:
                reconcile(attempt.pk)
            except APIException:
                failures += 1
                self.stderr.write(f"Intento {attempt.key}: pendiente de conciliación; revisar configuración o cargo.")
        self.stdout.write(f"Reservas vencidas liberadas: {expire_reservations()}. Consultas pendientes: {failures}.")
