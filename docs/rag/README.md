# Chat RAG experimental

El chat de la página de menú llama a `POST /api/v1/assistant/chat/`. Django conserva la clave de OpenAI y consulta el vector store con File Search. El navegador recibe únicamente la respuesta, las etiquetas de fuentes y los errores públicos.

## Configuración local

Añade a `backend/.env`:

```dotenv
OPENAI_API_KEY=tu_clave_de_api
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_VECTOR_STORE_ID=
```

Desde la carpeta `backend/`, con las dependencias instaladas:

```bash
python manage.py create_knowledge_base
```

El comando sube los DOCX de `docs/rag/` a un nuevo vector store de OpenAI, espera a que terminen de indexarse y muestra `OPENAI_VECTOR_STORE_ID`. Copia ese valor a `backend/.env` y reinicia Django. No ejecutes el comando en cada arranque: crea un vector store nuevo cada vez.

Para actualizar la documentación, vuelve a ejecutar el comando y reemplaza `OPENAI_VECTOR_STORE_ID` con el nuevo valor. El vector store anterior no se elimina automáticamente.

En Render, configura `OPENAI_API_KEY` y `OPENAI_VECTOR_STORE_ID` como variables privadas del servicio backend. Nunca configures la clave en variables `VITE_*` ni en el frontend.

## Fuentes de conocimiento

- `catalogo_productos_rag.docx` contiene las 72 fichas de productos de la carta activa, incluidas descripciones, ingredientes y alérgenos genéricos de demostración. El chat los usa para responder como atención al cliente. Los nombres, precios actuales y disponibilidad se leen de la base de datos en cada consulta.
- `politicas_cancelacion_reembolso_rag.docx` contiene las condiciones simuladas de cancelación, devolución y reembolso que el chat comunica a los clientes.
- Las condiciones simuladas permiten solicitar cancelación durante los primeros 5 minutos si la preparación no ha comenzado; reportar pedidos incompletos, equivocados o en mal estado dentro de 24 horas; y contemplan reembolso al medio de pago original en 5 a 10 días hábiles cuando corresponda.
- El historial se envía desde el navegador para mantener el contexto. No se guarda en la base de datos ni se conserva como conversación en Responses (`store=False`).
- Al crear el vector store, los DOCX se envían a OpenAI para indexación. Cada consulta también usa la API de OpenAI y puede generar cargos.

## Operación

El endpoint es público, acepta preguntas de hasta 500 caracteres y hasta ocho mensajes previos, y limita a 10 solicitudes por minuto según el throttle anónimo de Django REST Framework. Los límites basados en caché local pueden ser por instancia si el backend escala horizontalmente.
