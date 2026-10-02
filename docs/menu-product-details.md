# Menú por categorías y detalle de producto

## Cambios

- El menú solo filtra por categoría. Se retiró el buscador de nombre y su componente `SearchBox`.
- En escritorio, las categorías de todos los productos disponibles aparecen a la izquierda,
  con cantidad de productos y opción «Toda la carta». No se reducen al filtrar.
- En móvil, las opciones se distribuyen en dos columnas sobre los productos, sin desplegable.
- La selección usa `/menu?category=<id>` y se conserva al volver desde una ficha.
- Toda la tarjeta es un enlace accesible a `/menu/<id>`, que también se puede abrir directamente.
- La ficha muestra descripción, ingredientes, información nutricional, alérgenos y precio.
- «Añadir al carrito» está en la ficha y utiliza el carrito y checkout existentes.
- Los datos no registrados aparecen como información no disponible; no se deducen alérgenos
  ni valores nutricionales a partir del nombre o fotografía del plato.

## Activación del backend

Se añade una migración con tres campos de texto opcionales en `catalog.Product`:
`ingredients`, `nutritional_information` y `allergens`.
La migración no se ha aplicado a la base configurada de Supabase durante el desarrollo.

Desde Git Bash:

```bash
cd /c/Dev/MVP-REST/backend
source .venv/Scripts/activate
python manage.py migrate --plan
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Luego entra en Django Admin → Productos → selecciona un producto →
«Ingredientes e información alimentaria». Completa los datos verificados del restaurante:

- Ingredientes: texto, con saltos de línea si se desean.
- Nutrición: texto que indique la porción de referencia, cantidades y unidades.
- Alérgenos: declaración verificada; dejarlo vacío no significa que no existan alérgenos.

Los valores se presentan tal como están registrados. Estos campos son información
para el cliente, no sustituyen el módulo de recetas, costos o inventario del README.

## API

`GET /api/v1/menu/<id>/` devuelve los campos del producto del listado y los tres campos
informativos nuevos. El listado paginado conserva su contrato anterior.

La ficha solo permite GET, HEAD y OPTIONS y aplica la misma visibilidad que el menú:
producto publicado y disponible, con categoría y estación activas. Un producto oculto,
agotado o inexistente devuelve 404 incluso si se abre su enlace directamente.

## Verificación

```bash
# Desde backend con su entorno virtual activado:
python manage.py test catalog orders --settings=core.test_settings

# Desde frontend:
pnpm test
pnpm run build
pnpm run lint
```

Prueba elegir una categoría, abrir un producto, añadirlo, volver a la misma categoría,
abrir una ficha directamente, recargarla y continuar hacia carrito y checkout. Comprueba
también productos sin información, IDs inexistentes y pantalla móvil.
