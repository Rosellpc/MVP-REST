# Catálogo de práctica: Campo

Fuente: [carta digital de Campo, Grupo Morena](https://grupomorena.com/wp-content/uploads/2025/12/CAMPO-CARTA-ESP-DIGITAL_compressed.pdf).
Revisión visual: 28 de septiembre de 2026. El PDF tiene 11 páginas sin texto
extraíble. `pdf_pages` usa la posición de página en el archivo, empezando en 1,
no el número impreso al pie. Los precios son los de ese documento; no se afirma
que sean los precios actuales del restaurante.

`campo_menu.json` contiene nombres y precios para un catálogo de demostración:

| Categoría | Productos |
|---|---:|
| Cócteles de autor | 8 |
| Cócteles clásicos | 4 |
| Para comenzar | 5 |
| Entradas | 6 |
| Sopas | 3 |
| Vegetarianos | 2 |
| Fondos | 12 |
| Postres | 4 |
| Bebidas calientes | 15 |
| Bebidas frías | 12 |
| Total | 71 |

## Criterios de adaptación

- La fuente indica precios en soles, impuestos incluidos. Se conservan esos
  importes finales sin añadir impuestos ni inventar tasas. La moneda es metadato
  de esta carga; no cambia la configuración global ni el contrato de la API.
- Cócteles se divide en dos categorías para representar sus subgrupos en el
  modelo actual, que no tiene subcategorías.
- Cada infusión y aromática tiene su propio producto. Aguas con/sin gas y las
  tres variedades de Cusqueña también se separan. Se usa el precio común que
  figura en su grupo. No se inventan volúmenes ni tamaños.
- Los SKU `CAMPO-*` son identificadores locales de esta carga, no códigos del
  restaurante original. No renombrarlos si se quiere conservar la idempotencia.
- Asignación operativa de práctica: 32 platos/postres a KITCHEN y 39 bebidas a
  BAR, incluidas las embotelladas. La carta no prescribe estas estaciones.
- Se normaliza capitalización y se añaden prefijos descriptivos a variantes.
  Se conservan los nombres de la carta, incluido «Estiradito al estilo José».
- Las descripciones quedan vacías: esta carga no reproduce el texto comercial,
  no define recetas, ingredientes ni alérgenos. Tampoco añade imágenes.
- Los nuevos productos se crean publicados y disponibles para probar la API.

## Uso (Git Bash, entorno virtual activado)

Desde `backend/`, comprobar primero qué se cargaría:

```bash
python manage.py seed_campo_menu --dry-run
```

La simulación usa la base configurada, valida los registros y revierte toda la
transacción antes de salir. Para guardar el catálogo en esa base:

```bash
python manage.py seed_campo_menu
```

La operación es atómica. Si falla, no deja una carga parcial. Al repetirla,
reutiliza categorías por nombre y estaciones por código, y conserva los productos
con el mismo SKU. No borra registros ni sobrescribe precios, nombres o estados
editados. Si una categoría o estación existente está inactiva, no se reactiva:
sus productos seguirán ocultos en la API hasta que se habilite desde el admin.

No requiere migraciones nuevas ni paquetes adicionales.

```bash
python manage.py test catalog --settings=core.test_settings
```

Estas pruebas usan una base temporal y no escriben en Supabase.
