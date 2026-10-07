# Laboratorio de costeo independiente

Módulo disponible en `/costing`, fuera de los layouts de menú y Staff.
Comparte autenticación e infraestructura, pero no enlaza insumos a productos,
pedidos ni tickets. No modifica existencias. No se importaron archivos Excel/PDF.

## Activación

Desde `backend`, con el entorno virtual activo:

```powershell
python manage.py migrate
python manage.py setup_roles
```

Ingresar en `/costing` con un superusuario o usuario del grupo ADMIN.
El permiso del servidor es `costing.use_costing`; Cocina y Barra no lo reciben.
No se crean usuarios ni se ejecutan migraciones sobre tu base remota automáticamente.

## Alcance

La navegación tiene cuatro secciones: Resumen, Insumos, Recetario e Inventario.
Se mantienen los estudios independientes de la primera etapa en el Resumen.

- Edición de insumos con motivo obligatorio, autor y fotografía de cada referencia.
- Recetas con versiones inmutables. Cada edición/recalculo crea otra versión.
- Ficha técnica: categoría, porciones, tamaño, tiempos, temperatura, preparación,
  presentación y alérgenos declarados. Un campo vacío indica revisión pendiente.
- Simulación de venta con precio final, impuesto incluido, venta neta, margen
  teórico por porción y food cost. Venta neta = precio final / (1 + tasa / 100).
- Resumen de insumos, recetas y versiones, y promedio simple del food cost de las
  últimas versiones con precio. No son resultados reales ni ponderados por ventas.
- Importación JSON de insumos (1–500 por lote) validada en servidor y transaccional.
  Campos: name, purchase_unit, purchase_quantity, purchase_price, yield_percent.
  Exporta o descarga la plantilla desde Insumos. No importa directamente XLSX.
- Exportación JSON de insumos/fichas, CSV de listado compatible con Excel y ficha
  imprimible (seleccionar Guardar como PDF en el navegador).

La migración `0002_recipe_ingredientrevision_recipeversion` crea las tablas nuevas
sin convertir ni borrar estudios anteriores. Ejecutar `migrate` antes de abrir la UI.
La edición de recetas exige `expected_version`; si otra persona guardó antes,
devuelve 409 y pide volver a abrir la ficha. Los importes históricos no cambian
al modificar un insumo. Para obtener costos actuales, editar/recalcular la receta
y guardar una versión nueva.

- Alta de insumos con precio total de compra en PEN, cantidad, unidad y rendimiento.
- Formulación con varias líneas y número entero de porciones.
- Cantidades brutas o aprovechables explícitas.
- Vista previa y guardado de cálculos independientes con autor, fecha y fotografía
  de precios, cantidades, rendimientos y versión del algoritmo.
- Consulta de los últimos 100 cálculos guardados; sin modificación de históricos.

Costo de una línea bruta = cantidad base de receta × precio / cantidad base comprada.
Para una línea aprovechable, el denominador se multiplica por rendimiento / 100.
Ejemplo: 1 kg a S/ 20 con 80% aprovechable y consumo neto de 200 g cuesta S/ 5.
Conversiones: kg/g, l/ml y unidades. No convierte volumen en peso.
Los cálculos usan Decimal en el servidor; redondeo HALF_UP, totales a 2 decimales,
líneas a 4. El total se calcula antes de redondear las líneas.

El precio de compra se utiliza tal cual. No se deducen automáticamente impuestos
de compra. El simulador permite indicar el impuesto incluido del precio de venta;
no determina tasas legales ni calcula mano de obra, energía o inventario.
El rendimiento es una referencia de compra/limpieza, no una pérdida adicional
automática por cocción. Las porciones obtenidas las define el usuario.

API protegida por sesión y CSRF:
- GET/POST `/api/v1/costing/ingredients/`
- POST `/api/v1/costing/preview/`
- GET/POST `/api/v1/costing/studies/`

API adicional:
- GET/PUT `/api/v1/costing/ingredients/{id}/` (detalle e historial)
- POST `/api/v1/costing/import/`
- GET/POST `/api/v1/costing/recipes/`
- GET/POST `/api/v1/costing/recipes/{id}/` (versiones / nueva versión)
- POST `/api/v1/costing/recipes/preview/`
- GET `/api/v1/costing/summary/`

Pendientes para siguientes etapas: preparaciones intermedias, otros formatos
de Excel/CSV, paginación de listados grandes y vinculación opcional al catálogo.
La importación actual rechaza duplicados; no actualiza insumos existentes.
Las recetas e insumos no se eliminan desde esta interfaz para conservar referencias.

Pruebas: `python manage.py test costing --settings=core.test_settings`.

## Inventario de la plantilla Excel

En `/costing?view=inventory` se pueden ingresar conteos manualmente o importar
la plantilla `.xlsx` proporcionada. No es un kardex: no crea compras, movimientos,
existencias operativas ni insumos de receta automáticamente.

Campos: establecimiento, departamento, fecha de inventario, empleado; por fila:
código (texto, conserva ceros), familia, ubicación, producto, unidad/presentación,
cantidad, coste unidad y valor de inventario calculado. El total se deriva en
el servidor con Decimal. Añadidos: moneda, marca de ejemplo, notas y procedencia.

El lector admite la disposición de esta plantilla (encabezados C8/F8 y filas
hasta 286). No ejecuta fórmulas; conserva los valores auxiliares G/H/J/M en
`source_extra`, pero recalcula la valoración desde cantidad y coste. Rechaza libros
inválidos y filas sin cantidades/precios válidos. Máximo 5 MB y 30 MB descomprimido.
Si hay varias hojas con datos, debe indicarse el nombre. Las hojas vacías se omiten.
La huella del archivo y hoja evita duplicar exactamente la misma importación.

Los conteos guardados son referencias inmutables; un conteo nuevo no se suma
a los anteriores. La exportación CSV incluye encabezado y detalle completo.

Endpoints protegidos: GET/POST `/api/v1/costing/inventory/`.
POST admite JSON para conteos manuales o multipart (`file`, `sheet` opcional).
El comando administrativo `python manage.py import_inventory "ruta.xlsx" --sheet
"Inventario Ejemplo"` utiliza la misma validación; deja created_by vacío para
distinguir la importación administrativa de una acción atribuida a un usuario.

### Carga efectuada el 6 de octubre de 2026

Se aplicó `costing.0003_inventorycount_inventorycountline` en la base configurada
y se importó el archivo original solicitado, sin modificarlo:

- Registro ID 1, hoja `Inventario Ejemplo`.
- Establecimiento El Mirador, departamento Cocina, empleado Manuel Angel.
- Fecha que contiene el Excel: 2026-07-03.
- 64 filas, incluidas 17 con cantidad cero; código inicial `0390` conservado.
- Total recalculado y redondeado: 1520.79; moneda no indicada en el Excel.
- Marcado como ejemplo. La hoja `Plantilla` está vacía.

No se interpretaron presentaciones ambiguas como conversiones de compra, ni se
asumió PEN para un archivo sin moneda. Los dos productos con igual nombre y
códigos distintos se conservan como filas independientes.

## Importar recetario JSON

En Recetario, abrir «Importar / exportar recetario JSON» y descargar la plantilla.
El formato es `{"recipes": [...]}`. Cada receta incluye la ficha técnica y `lines`;
cada línea usa `ingredient_name` (nombre de un insumo registrado), `quantity`,
`unit` (`g`, `kg`, `ml`, `l`, `unit`) y `basis` (`gross`, `usable`). También se admiten
IDs en `ingredient_id`. Las cantidades y precios pueden enviarse como cadenas
decimales. Máximo 100 recetas por lote, 2 MB en el formulario.

POST `/api/v1/costing/recipes/import/` valida todas las recetas, unidades y nombres
antes de crear registros. Un error cancela todo el lote; nombres duplicados se
rechazan para evitar sobrescribir recetas. Cada receta entra como versión 1,
atribuida al usuario autenticado. Los importes se calculan con precios actuales;
los totales proporcionados por el archivo no se aceptan como fuente del costo.
Exportar un recetario no garantiza que pueda reimportarse en la misma base: los
nombres existentes se rechazan intencionalmente. Para modificar recetas, usar
el editor versionado. Los ingredientes deben existir antes de importar recetas.

## Importación del Excel de costeo

En Recetario, «Excel de costeo e informes de importación» permite subir la
plantilla `costos-recetas.xlsx` (hasta 10 MB). Usa la hoja `Lista de Ingredientes`
y las hojas `Receta...`. No ejecuta fórmulas, macros ni instrucciones del archivo.
El importador almacena los valores de origen y un informe de registros creados,
duplicados y pendientes. La misma huella SHA-256 no vuelve a importarse.

Reglas específicas de esta plantilla:

- Precio de compra D; cantidad comprada = E × G; merma H → rendimiento 100 − H×100.
- Formato LT → litros; KG → kg. Para envases con peso bruto G, se usa kg, con
  advertencia de revisión. No se infiere una densidad para convertir masa/volumen.
- Las cantidades G de las recetas se interpretan como aprovechables porque el
  Excel las multiplica por costo ajustado por merma. Se pasan a g/ml para preservar
  cantidades pequeñas. Este supuesto se muestra explícitamente en cada ficha.
- Se aplica la fórmula del módulo para merma e impuesto incluido. Se conserva
  K13 como costo original, por lo que las diferencias son visibles y auditables.
- Nombres se comparan sin acentos y sin distinguir mayúsculas; los duplicados
  idénticos se consolidan. Referencias existentes con otro precio no se sobrescriben.
- Preparaciones que solo figuran en la lista de insumos entran como insumos con
  precio de referencia; no se inventa su composición ni se crean subrecetas.
- Tiempos no numéricos (p. ej. «Plato frío») quedan sin especificar; se conserva
  el texto original. No se deducen alérgenos de casillas gráficas.
- Una receta con insumos desconocidos queda pendiente en el informe, conservando
  su hoja original en la base. Las restantes recetas válidas sí se cargan.

GET/POST `/api/v1/costing/recipes/workbook/`, protegido con el mismo permiso.
El POST usa multipart con `file`. El comando administrativo equivalente es:

```powershell
python manage.py import_recipe_workbook "ruta\costos-recetas.xlsx"
```

Las importaciones administrativas llevan actor nulo y se muestran como
«Importación administrativa»; no se atribuyen a una cuenta arbitraria.
La migración `0004` añade el informe y permite ese origen en versiones/historiales.

### Carga de costos-recetas.xlsx completada el 6 de octubre de 2026

- 188 insumos nuevos y 35 recetas como versión 1, en la base configurada.
- La fila duplicada de Pechuga pollo se consolidó.
- La Palta existente conservó sus valores. Se creó `Palta [Excel costos-recetas.xlsx]`
  para la referencia diferente del libro y se usó en las recetas importadas.
- `Habla causita` quedó pendiente por `Condimento/brasa`, ausente en el catálogo
  del libro. El usuario autorizó omitirla; no se inventaron precios.
- Se conservaron las 36 hojas de receta y el catálogo original en el lote ID 1.
- Las fichas muestran las diferencias entre costo original y recalculado y sus
  supuestos de revisión. No se importaron imágenes, macros ni casillas gráficas.

Cuando una referencia de insumo existente tiene otros valores, el adaptador crea
una referencia separada con sufijo del archivo; no sobrescribe la existente.
`--resume` en el comando reintenta las recetas pendientes del mismo lote sin
duplicar las que ya creó. Las referencias todavía desconocidas deben resolverse
en el origen antes de volver a importar un libro corregido o usando el editor.
