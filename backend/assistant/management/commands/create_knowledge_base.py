from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from openai import APIError, OpenAI


class Command(BaseCommand):
    help = "Crea un vector store de OpenAI y carga los DOCX de docs/rag."

    def handle(self, *args, **options):
        if not settings.OPENAI_API_KEY:
            raise CommandError("Configura OPENAI_API_KEY antes de crear el vector store.")

        docs_dir = Path(settings.BASE_DIR).parent / "docs" / "rag"
        files = sorted(docs_dir.glob("*.docx"))
        if not files:
            raise CommandError(f"No se encontraron archivos DOCX en {docs_dir}.")

        try:
            with OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60.0, max_retries=1) as client:
                store = client.vector_stores.create(name="RestaurantOS public chat knowledge base")
                for path in files:
                    with path.open("rb") as file_stream:
                        uploaded = client.files.create(
                            file=file_stream,
                            purpose="assistants",
                        )
                    indexed = client.vector_stores.files.create_and_poll(
                        vector_store_id=store.id,
                        file_id=uploaded.id,
                    )
                    if indexed.status != "completed":
                        raise CommandError(
                            f"OpenAI no terminó de indexar {path.name}: {indexed.status}."
                        )
        except APIError as exc:
            raise CommandError(
                "No se pudo crear o indexar la base de conocimiento en OpenAI. "
                "Revisa la conexión y las credenciales del proyecto."
            ) from exc

        self.stdout.write(self.style.SUCCESS(
            "Vector store creado. Añade esta variable al entorno del backend: "
            f"OPENAI_VECTOR_STORE_ID={store.id}"
        ))
