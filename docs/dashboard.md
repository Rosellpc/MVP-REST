# Dashboard de operación

Acceso: `/dashboard`, desde el Header del personal, Mis áreas o Costeo.
API: `GET /api/v1/dashboard/summary/?start=YYYY-MM-DD&end=YYYY-MM-DD`.
Reutiliza la sesión y el permiso `accounts.access_staff` de ADMIN/superusuario.
La API también comprueba el permiso; no admite escrituras ni expone nombres de
clientes o códigos de seguimiento. No requiere migraciones ni nuevas dependencias.

## Periodos e indicadores

Fechas inclusivas en `America/Lima`, máximo 366 días, sin fechas futuras.
Por defecto últimos 7 días incluyendo hoy. Comparación con el intervalo
inmediatamente anterior de igual duración. Los días sin pedidos aparecen en cero.

| Indicador | Cálculo |
|---|---|
| Importe demo | Suma decimal de `Order.total` de pedidos DEMO_CONFIRMED/SIMULATED no cancelados, por fecha de creación |
| Pedidos válidos | Número de pedidos incluidos en ese importe, aunque sigan en preparación |
| Ticket promedio | Importe / pedidos válidos; sin pedidos se muestra Sin datos |
| Variación | (Actual − anterior) / anterior; sin base anterior se omite el porcentaje |
| Unidades y ranking | Cantidades y totales históricos de OrderItem, para los mismos pedidos válidos |
| Modalidades | Pedidos e importes por consumo en mesa o recojo |
| Tiempo de preparación | Promedio de recepción del ticket (`created_at`) a `completed_at`, para tickets READY completados en el periodo, incluidos los archivados |
| Producción y merma | Unidades de movimientos ocurridos en el periodo; WASTE y CANCEL_WASTE cuentan como merma |

Pedidos CANCELLED y PARTIALLY_CANCELLED se excluyen de importes, unidades,
ranking y ticket promedio. Los parciales antiguos no tienen una asignación
monetaria por cancelación confiable y se muestran como exclusión separada.
Los totales reflejan el estado actual: cancelar hoy puede modificar cifras de
un día anterior. Son importes finales PEN con impuestos, **no ventas netas
contables, cobros reales ni dinero recibido**. Los cálculos monetarios se hacen
con Decimal en Django; React solo da formato y dibuja la serie.

## Estado actual, separado del filtro de fechas

- Colas de Cocina/Barra: tickets no archivados por estado. Listos significa
  pendientes de finalizar en el tablero, no una entrega física verificada.
- Solicitudes de cancelación pendientes de aprobación/rechazo.
- Stock: saldos físicos de productos publicados con categoría/estación activa,
  turno abierto, productos sin registro, agotados y stock bajo (1–5 unidades).
  Un turno cerrado puede conservar saldos físicos, pero la venta está pausada.
- Recetario: versiones vigentes de recetas no archivadas, costeadas y pendientes,
  insumos activos y porcentaje medio de costo teórico sobre venta neta.
  El promedio es simple y muestra la cantidad de fichas incluidas; no está
  ponderado por ventas. Una ficha pendiente nunca se cuenta como costo cero.

El inventario importado de Excel conserva su alcance independiente. No se suman
sus cantidades o valores al stock de productos terminados. El ingreso de prueba
de 20 unidades por producto aparece como producción porque es un movimiento
registrado, y no se confunde con ventas.

## Límites actuales

La utilidad y el costo histórico de las ventas **no se calculan todavía**:
OrderItem no conserva una versión de receta con costo aplicable. Vincular por
nombre o usar el costo actual daría cifras históricas incorrectas. El dashboard
expone esta brecha y permite abrir las fichas para completar el costeo.
La valorización de inventario requiere definir y aplicar un método de costo;
no se fabrica multiplicando saldos por precios de venta.

Actualización cada 30 segundos con la página visible; conserva datos ante errores
temporales y muestra su fecha de consulta. La gráfica puede explorarse por día
y tiene una tabla accesible. CSV exporta la serie del periodo efectivamente
mostrado, incluyendo días en cero. Los paneles operativos se consultan en varias
consultas breves, no constituyen un cierre contable congelado.

## Verificación

`python manage.py test analytics --settings=core.test_settings`: autorización,
solo lectura, exclusión de cancelados, agregación sin duplicados, límites de fecha
y zona horaria, comparación, vacíos, recetas pendientes y tiempos de estación.
Frontend: `pnpm build`, `pnpm lint`, `pnpm test`.
