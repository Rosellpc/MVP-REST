# API pública del menú

`GET /api/v1/menu/` permite consultar el catálogo sin iniciar sesión.
Usa la base configurada en Django (PostgreSQL en Supabase en desarrollo).
No necesita habilitar la Data API de Supabase ni instalar paquetes adicionales.

## Visibilidad

Solo devuelve productos publicados y disponibles, con categoría y estación activas,
siguiendo el alcance actual del README. Los productos agotados no aparecen en esta
primera versión del endpoint. La edición se realiza desde Django Admin.

Devuelve únicamente ID, nombre, descripción, categoría (ID y nombre) y precio.
No expone SKU, estación, fechas internas ni otros campos administrativos.
La moneda del piloto sigue pendiente de confirmación; el endpoint no inventa una.

## Consultas y respuesta

- `/api/v1/menu/`: primera página, hasta 20 productos.
- `/api/v1/menu/?page=2`: página siguiente.
- `/api/v1/menu/?category=1`: productos de la categoría con ID 1.
- `/api/v1/menu/?category=1&page=2`: ambos parámetros se pueden combinar.

Orden: posición de categoría, nombre de categoría, nombre de producto e ID como
desempate. `count` es el total después de aplicar los filtros. Los enlaces `next`
y `previous` conservan el filtro de categoría.

Ejemplo ilustrativo (no son datos sembrados):

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Pasta",
      "description": "Pasta con verduras",
      "category": {"id": 1, "name": "Platos"},
      "sale_price": "25.50"
    }
  ]
}
```

El precio es una cadena decimal con dos posiciones, no un número de coma flotante.
Un menú sin productos visibles devuelve HTTP 200 con `count: 0` y `results: []`.
Un ID de categoría inexistente también devuelve una lista vacía. Un parámetro
`category` inválido devuelve 400; una página inexistente devuelve 404.
Los demás parámetros no modifican las reglas de visibilidad.

Se admiten GET, HEAD y OPTIONS. POST, PUT, PATCH y DELETE devuelven 405.
El límite inicial es de 120 peticiones por minuto y dirección IP (429 al excederlo).
Usa la caché de Django; con la configuración local, el contador es por proceso.
Antes de desplegar varios procesos, configurar caché compartida y la detección de
IP detrás del proxy. Este límite básico no sustituye controles de tráfico del hosting.

## Comprobación manual en Git Bash

Con el entorno virtual activado:

```bash
cd /c/Dev/MVP-REST/backend
python manage.py check
python manage.py runserver 127.0.0.1:8000
```

En otra terminal, o abriendo la URL en el navegador:

```bash
curl -H 'Accept: application/json' 'http://127.0.0.1:8000/api/v1/menu/'
```

No requiere migraciones nuevas. Para ver un producto, créalo en `/admin/` con
categoría y estación activas y marca `publicado` y `disponible`.
Al desmarcar cualquiera, debe desaparecer de la siguiente consulta del menú.
Las imágenes no forman parte del modelo actual.

## Pruebas aisladas

```bash
python manage.py test catalog --settings=core.test_settings
```

Estas pruebas usan SQLite en memoria, crean datos temporales y no cargan `.env`
ni acceden a Supabase. Comprueban el contrato público, visibilidad, validación,
paginación, consultas, rechazo de escrituras y límite de solicitudes.
La configuración `core.test_settings` es exclusiva para pruebas; no usarla para
arrancar el servidor del restaurante. La prueba HTTP manual usa la configuración
real y complementa la verificación con PostgreSQL.
