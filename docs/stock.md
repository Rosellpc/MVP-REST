# Stock de productos terminados

Página `/stock`, accesible desde el Header del personal y desde Costeo. API en
`/api/v1/stock/`. Controla **unidades de venta de productos del catálogo**, no
existencias de insumos ni el costo de recetas. Actualmente hay 71 productos
vendibles y 74 fichas de recetas; los indicadores consultan el catálogo, no esos
números fijos. El inventario Excel de ejemplo no se convierte en existencias.

## Activación y responsables

1. Aplicar `python manage.py migrate` y `python manage.py setup_roles`.
2. ADMIN y superusuarios pueden gestionar stock. El nuevo grupo CHEF puede
   gestionar stock y operar Cocina. KITCHEN y BAR solo consultan Stock.
   Asignar CHEF a la cuenta responsable desde Django Admin; no se crean usuarios
   ni se elevan cuentas de cocina automáticamente.
3. Abrir `/stock`, elegir **Abrir turno** e ingresar cantidades reales.
   Antes de la primera apertura, el checkout conserva su comportamiento previo.
   Confirmar la apertura activa el control de todos los productos publicados de
   Cocina y Barra. Cantidad cero implica agotado.
4. Durante el turno, registrar producción adicional, merma o ajuste con motivo.
5. Terminar/cancelar los pedidos pendientes antes de cerrar. Contar físicamente
   todos los productos y justificar diferencias. El cierre pausa las ventas
   hasta abrir otro turno. Se conserva tanto el teórico como el físico.
6. En la siguiente apertura confirmar cuántos sobrantes siguen aptos. Cualquier
   descarte genera una merma con causa (caducidad, conservación, etc.). No hay
   conservación automática ni fechas de caducidad inventadas.

Un turno comprende ambas áreas en esta versión de una sola sede. Los productos
publicados después de abrirlo deben incorporarse en la siguiente apertura;
no se venden sin su registro de stock. Los productos desactivados conservan
historial y los sobrantes siguen requiriendo conciliación.

## Evento de venta y cancelaciones

- El descuento se hace **una vez al liberar producción en el checkout** dentro
  de la misma transacción que crea pedido, ítems y tickets. Marcar listo o
  finalizado no vuelve a descontar. El pago continúa siendo simulado.
- Sin stock suficiente se revierte todo el pedido. Cerrar un turno no permite
  vender sus sobrantes hasta confirmar una nueva apertura.
- Solo la aprobación del superusuario activa la cancelación. Para cada ticket:
  pendiente sin preparación devuelve unidades; preparación iniciada o lista
  reclasifica el consumo como merma, sin sumar unidades. Solicitar o rechazar
  cancelación no cambia el stock.
- Las ventas del resumen son netas de cancelaciones. Una cancelación preparada
  resta ventas y suma merma, con variación física cero. Las ventas originales
  permanecen en el historial.
- Los pedidos confirmados existentes no tienen edición de líneas: para corregir
  el pedido se usa cancelación y uno nuevo. No hay una edición silenciosa de
  cantidades. Una devolución física excepcional requiere ajuste justificado
  del responsable, indicando referencia y aptitud; no hay reembolso real.
- Los pedidos anteriores a activar Stock no se descuentan retroactivamente.

Fórmula: inicial + producción − ventas netas − mermas + ajustes = actual.
La conciliación genera un movimiento COUNT por la diferencia. El físico
validado pasa a ser saldo disponible para la revisión del próximo turno.
Stock bajo usa un umbral visible de 5 unidades. No se ha implementado control
por lotes ni vencimiento automático: los descartes se registran explícitamente.

## Integridad y arquitectura

App Django `stock`, con servicios explícitos llamados desde `production`:

- StockControl: activación, revisión y bloqueo global para esta sede.
- Balance: saldo por producto, no negativo.
- Shift / ShiftItem: responsables, apertura/cierre, nombres/SKU históricos,
  inicial, teórico, físico, diferencia y justificación.
- Movement: entradas/salidas inmutables por API, saldo posterior, responsable,
  pedido y contramovimiento único. Actor nulo identifica el checkout automático.
- Operation: clave UUID y huella del contenido para reintentos idempotentes.

Las transacciones PostgreSQL bloquean StockControl al registrar movimientos o
confirmar turnos. El checkout bloquea producto sin bloquear inserciones de claves
foráneas del kardex. Un solo turno abierto y una sola salida por OrderItem se
garantizan también mediante restricciones de base de datos. La revisión evita
confirmar un conteo si hubo ventas/movimientos desde que se abrió el formulario.
Abrir/cerrar escribe los productos por lotes para evitar cientos de consultas.

Las API de escritura requieren sesión, CSRF y `stock.manage_stock`; lectura,
`stock.view_stock`. No existe PUT/DELETE para saldos, movimientos o cierres.
No se ha añadido edición libre de estos modelos a Django Admin.

| Método | Ruta (bajo `/api/v1/`) | Uso |
|---|---|---|
| GET | stock/ | Estado, revisión, indicadores y productos |
| POST | stock/open/ | Apertura; key, revision, notes, items(product_id, keep, production, reason) |
| POST | stock/movements/ | key, shift_id, product_id, kind, quantity, reason |
| POST | stock/close/ | key, revision, shift_id, notes, items(product_id, counted, reason) |
| GET | stock/history/ | Historial paginado; product, shift, start, end, page |
| GET | stock/shifts/ | Turnos paginados |
| GET | stock/shifts/{id}/ | Conciliación e histórico del turno |
| GET | menu/stock/ | Solo disponibilidad pública por ID; sin datos de ventas ni responsables |

El menú conserva la caché de catálogo y consulta cantidades cada 15 segundos
cuando está visible. Stock actualiza cada 10 segundos sin reiniciar la pantalla.
El checkout siempre valida el saldo real, aunque la información visible esté
unos segundos atrasada. La navegación a detalles conserva fotos y contenido.

## Verificación

`python manage.py test --settings=core.test_settings` usa SQLite aislado para
permisos/CSRF, fórmula, activación, reintentos, faltantes y rollback, cancelaciones
mixtas, cierre obsoleto, diferencias, transferencia y conservación del historial.
`stock.test_concurrency` requiere PostgreSQL y comprueba venta concurrente de la
última unidad y dos solicitudes simultáneas con la misma clave. SQLite omite
estas dos pruebas porque no implementa los bloqueos utilizados.

Frontend: `pnpm build`, `pnpm lint`, `pnpm test`. Comprobación operativa: abrir
con cantidades reales, comprar una unidad, observar el movimiento; probar ambas
reglas de cancelación, realizar conteo y reabrir revisando los sobrantes.
