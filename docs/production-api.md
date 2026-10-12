# API de producción y cancelaciones

Todos los endpoints están bajo `/api/v1/`, requieren sesión y aplican permisos
de estación. Las mutaciones requieren CSRF y producción demo habilitada.

## Flujo actual

El checkout crea el pedido y sus tickets de Cocina/Barra de forma transaccional.
La liberación manual permanece como API administrativa para pedidos demo previos;
no es un paso del checkout habitual. Repetir la liberación no duplica tickets.

Los tickets avanzan PENDING → IN_PROGRESS → READY. Finalizar archiva el ticket
listo y lo retira del tablero; no acredita pago ni entrega física. El pedido está
listo cuando todas sus áreas requeridas están listas.

Cocina/Barra pueden solicitar cancelación solo desde PENDING o IN_PROGRESS, con
motivo obligatorio. La tarjeta pasa visualmente a Cancelados con etiqueta
«Pendiente de cancelación»; el estado técnico se conserva hasta la decisión.
La solicitud afecta al pedido completo y bloquea su avance mientras se resuelve.
Solo un superusuario puede aprobar o rechazar. Aprobar cancela todos sus tickets,
los retira de los tableros y conserva el historial. Rechazar permite continuar.
No se ofrece cancelación parcial; PARTIALLY_CANCELLED queda como compatibilidad
histórica y no como filtro o acción nueva.

Stock devuelve unidades de tickets que aún no iniciaron preparación; para los que
ya iniciaron registra pérdida sin devolución. Consultar [reglas de stock](stock.md).

## Endpoints

| Método y ruta | Función |
| --- | --- |
| GET `staff/orders/` | Historial demo paginado, 20 por página |
| GET `staff/orders/counts/` | Contadores por estado y solicitudes pendientes |
| POST `staff/orders/{id}/release/` | Liberación administrativa idempotente |
| POST `staff/orders/{id}/cancel/` | Aprobación exclusiva de superusuario |
| POST `staff/orders/{id}/reject-cancellation/` | Rechazo exclusivo de superusuario con motivo |
| GET `production/tickets/` | Tickets visibles de las estaciones autorizadas, 50 por página |
| GET `production/tickets/{id}/` | Detalle autorizado, incluido historial archivado |
| POST `production/tickets/{id}/start/` | Iniciar preparación |
| POST `production/tickets/{id}/complete/` | Marcar listo |
| POST `production/tickets/{id}/finalize/` | Archivar ticket listo |
| POST `production/tickets/{id}/cancel/` | Crear solicitud, no aprobarla |
| GET `production/cancellation-notices/` | Avisos de cancelaciones aprobadas |

El historial acepta `status=PENDING|IN_PROGRESS|READY|CANCELLED` y
`pending_cancellation=true`. Los tickets aceptan `station=KITCHEN|BAR` y `status`;
la lista siempre excluye archivados y cancelaciones aprobadas. Seguir `next` para
obtener páginas adicionales; un filtro nunca amplía permisos de estación.

Los POST de solicitud/rechazo usan `{"reason":"Motivo"}`. La API permite también
cancelación directa de superusuario con motivo cuando el pedido es elegible,
aunque el panel se centra en resolver solicitudes. Las respuestas de cancelación
son objetos CancellationRequest, no tickets. Un conflicto de estado devuelve 409;
los permisos insuficientes devuelven 403.

Los avisos aceptan `station` y `approved_since` (fecha ISO con zona horaria).
Incluyen `order_number`. El tablero consulta cada 10 segundos desde cinco minutos
antes de su apertura y permite descartarlos durante la visita. No vuelve a
mostrar tarjetas de trabajo canceladas ni presenta todo el historial como nuevo.

El cliente consulta el seguimiento mediante su código público de pedido. Los
eventos y solicitudes se conservan para auditoría; no se borran al limpiar tableros.

## Verificación

```sh
python manage.py test production orders stock accounts --settings=core.test_settings
```

SQLite prueba reglas, permisos y rollback secuencial; las pruebas de bloqueo
concurrente requieren PostgreSQL aislado. Las comprobaciones de navegador y carga
operativa siguen siendo necesarias antes de un despliegue comercial.
