# Tickets de demostración: activación y API

## Tableros y controles actuales

Cocina/Barra mantiene cuatro columnas. Un ticket con cancellation_pending=true
se muestra en Cancelados con la etiqueta Pendiente de cancelación; el estado de
preparación persistido no se cancela hasta la aprobación. La solicitud pausa todo
el pedido y solo puede originarse desde Pendientes o En preparación.

Admin dispone de dos filas: filtros por estado y gestión de cancelaciones.
Ítems por cancelar muestra las solicitudes; Cancelar órdenes permite al superusuario
cancelar directamente un pedido PENDING/IN_PROGRESS con motivo obligatorio, enviando
POST /api/v1/staff/orders/{id}/cancel/ con {"reason": "motivo"}. Sin solicitud previa,
se crea y aprueba una solicitud auditada dentro de la misma transacción. No se ofrece
el filtro Cancelado parcialmente. La unidad de cancelación continúa siendo el pedido
completo, no una línea individual. No requiere migraciones adicionales.

## Cancelación con aprobación del superusuario

El flujo vigente reemplaza la cancelación directa descrita en las secciones anteriores:
POST /production/tickets/{id}/cancel/ ahora solicita cancelar el pedido completo,
con motivo obligatorio. Cocina y Barra solo pueden solicitar desde su estación.
La solicitud es persistente y única por pedido; mientras está pendiente se bloquean
avances y finalización de sus tickets. Administración la muestra con prioridad.

POST /staff/orders/{id}/cancel/ aprueba la solicitud únicamente si el usuario activo
es superusuario (is_superuser). El grupo ADMIN por sí solo no basta. Se cancelan y
archivan todos los tickets en una transacción, con usuario y motivo en auditoría.
El cliente ve CANCELLED y no recibe el agradecimiento de pedido listo.

GET /production/cancellation-notices/?station=KITCHEN (o BAR) devuelve avisos
paginados de aprobaciones de pedidos que correspondan a la estación autorizada.
Los tableros consultan cada cinco segundos y muestran «Cancelación aprobada por el
administrador». Entendido oculta el aviso durante la visita actual.

Se retiraron la opción Pendiente de aceptación y la liberación manual de la pantalla
administrativa. Aplicar `python manage.py migrate` para crear CancellationRequest.
Esta versión no incorpora rechazo de solicitudes: una solicitud pendiente permanece
pausada hasta su aprobación. No se cancelan pedidos completamente listos mediante
solicitudes nuevas.

## Finalizar tickets listos

El botón «Finalizado» en Cocina y Barra llama a
POST /api/v1/production/tickets/{id}/finalize/. Solo admite tickets READY de una
estación que el usuario pueda operar. Archiva el ticket con fecha y evento de auditoría;
el listado deja de mostrarlo también al recargar. No elimina registros ni cambia el
estado READY del pedido del cliente. Repetir la petición no duplica eventos.
Aplicar `python manage.py migrate` para crear archived_at.

## Checkout automático

Confirmar el checkout ahora crea el pedido y sus tickets en una única transacción.
Abrir /checkout o visitar el carrito no crea tickets. Cada producto se enruta según
su estación guardada. Los reintentos con la misma clave no duplican pedidos ni tickets.
La auditoría distingue CHECKOUT (actor nulo) de acciones STAFF del personal.
El cliente ve una línea verde: Recibido → En preparación → Listo. El último estado
requiere que todas las estaciones terminen. Cancelaciones se muestran como interrupciones.

Aplicar la nueva migración con `python manage.py migrate` antes de probar.
PRODUCTION_DEMO_ENABLED hereda ORDER_DEMO_ENABLED (o DEBUG) si no se especifica.
Si se configura explícitamente False, un checkout nuevo se rechaza sin crear pedido.
Configúralo en True para probar este flujo. DELIVERY continúa rechazado hasta definir
su tratamiento. La liberación manual queda disponible para pedidos antiguos pendientes.

## Activar

Con el entorno virtual de backend activo:

```sh
python manage.py migrate
python manage.py setup_roles
```

Configura en el entorno del backend `PRODUCTION_DEMO_ENABLED=True` y reinicia Django
solo cuando quieras probar producción simulada. El checkout también necesita ORDER_DEMO_ENABLED.
Desactivar producción bloquea todas sus mutaciones; los usuarios autorizados aún
pueden consultar los registros para auditoría. No se ejecutaron migraciones remotas.

## Contrato

Todas las rutas requieren sesión. POST requiere X-CSRFToken. Primero obtén un token
en GET /api/v1/auth/csrf/ e inicia sesión. No uses cuentas compartidas.

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | /api/v1/staff/orders/ | production.release_order |
| POST | /api/v1/staff/orders/{id}/release/ | production.release_order |
| GET | /api/v1/production/tickets/ | view_kitchen_ticket o view_bar_ticket |
| GET | /api/v1/production/tickets/{id}/ | Consulta de su estación |
| POST | /api/v1/production/tickets/{id}/start/ | advance_kitchen_ticket o advance_bar_ticket |
| POST | /api/v1/production/tickets/{id}/complete/ | Avance de su estación |
| POST | /api/v1/production/tickets/{id}/cancel/ | cancel_ticket y consulta de la estación |

Listados paginados: 50 elementos, formato count/next/previous/results. Tickets acepta
`?station=KITCHEN&status=PENDING` o BAR y otros estados válidos. Los filtros nunca
amplían permisos. La consulta de un ID de otra estación devuelve 404.
La lista administrativa incluye pedidos demo liberados y pendientes, diferenciados
por production_status y released_at. No incluye nombre del cliente ni claves idempotentes.

Release/start/complete aceptan cuerpo vacío. Cancel exige:

```json
{"reason": "Faltan insumos para preparar este producto"}
```

Release devuelve un arreglo de tickets con 201; repetir devuelve los existentes con
200. Start/complete/cancel devuelven el ticket actualizado con 200. Repetir el estado
actual no crea eventos nuevos ni cambia el motivo original. Una transición incompatible
devuelve 409. Motivo vacío o mayor a 500 caracteres devuelve 400. Sin permiso: 403.

Cada ticket muestra id, public_code, fulfillment, table_label, station_code, status,
demo=true, fechas y líneas con nombre/cantidad. No expone precios, identidad del cliente
ni auditoría interna. El cliente no controla estación, actor, demo ni estado destino.

## Integridad

- Solo pedidos DEMO_CONFIRMED con pago SIMULATED son admitidos. No hay producción real.
- DELIVERY o cualquier estación desconocida rechaza el pedido completo sin efectos.
- Se usan las estaciones y nombres guardados en OrderItem, no el catálogo actual.
- Restricción única pedido/estación y línea de pedido única entre tickets.
- Creación y transiciones transaccionales; todas bloquean primero el pedido.
- Al terminar ambas estaciones se calcula READY bajo el mismo bloqueo.
- Cancelaciones parciales conservan PARTIALLY_CANCELLED incluso si el resto termina.
- TicketEvent registra actor, transición, fecha y motivo; el admin es de solo lectura.
- payment_status y status originales permanecen intactos; production_status es separado.
- No hay descuento de stock, reembolso, envío a equipos físicos ni seguimiento público nuevo.

## Pruebas

```sh
python manage.py test accounts catalog orders production --settings=core.test_settings
python manage.py makemigrations --check --dry-run --settings=core.test_settings
```

Las pruebas locales usan SQLite aislado. Validan permisos, CSRF, reintentos, rollback,
estaciones, estados y auditoría. SQLite no valida select_for_update: antes de operar
con múltiples estaciones, ejecutar pruebas concurrentes contra PostgreSQL de pruebas
(dos liberaciones simultáneas y dos finalizaciones del mismo pedido). Nunca usar la
base de producción para pruebas destructivas.

## Pantallas y seguimiento

- /staff/admin: pedidos pendientes y liberación manual de demostración.
- /kitchen y /bar: columnas pendientes, en preparación, listos y cancelados.
- Iniciar y marcar listo respetan permisos; administración puede cancelar con motivo.
- /orders/:publicCode: seguimiento automático del estado agregado de preparación.

Las consultas se repiten cada cinco segundos sin solaparse, se pausan con la pestaña
oculta y se reanudan al volver. Las acciones solicitan una actualización inmediata.
Los fallos de conexión conservan la última respuesta con un aviso de datos antiguos.
Los listados recorren todas las páginas; para grandes historiales será necesario
incorporar un filtro temporal y archivo de tickets antes de operar a escala.

El endpoint público añade production_status; no expone tickets, usuarios ni auditoría.
Una estación terminada no marca el pedido listo si falta la otra. Cancelaciones parciales
se muestran expresamente y el pago permanece SIMULATED.

Prueba manual: crea un pedido mixto, inicia sesión como ADMIN y libéralo; abre cocina y
barra con sus respectivas cuentas, inicia/termina sus tickets y observa el enlace público.
Prueba además cancelar un ticket con motivo, perder la conexión y volver a la pestaña.
