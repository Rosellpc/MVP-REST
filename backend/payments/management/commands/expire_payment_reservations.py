from django.core.management.base import BaseCommand
from payments.services import expire_reservations


class Command(BaseCommand):
    help = "Libera hasta 500 reservas vencidas sin intento de cobro. Ejecutar periódicamente."

    def handle(self, *args, **options):
        self.stdout.write(f"Reservas vencidas liberadas: {expire_reservations()}")
