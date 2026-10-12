# Revisión del proyecto — 12 de octubre de 2026

## Alcance y conclusión

Revisión de código, contratos, permisos, documentación, pruebas automatizadas e
integridad de datos. Se revisaron menú, compra demo, sesión del personal,
producción, cancelaciones, stock, costeo y dashboard. No equivale a una auditoría
de seguridad independiente ni a pruebas completas de navegador o carga.

El proyecto tiene una base coherente de MVP integrado: Django concentra reglas y
permisos, PostgreSQL conserva operaciones e históricos y React presenta los
flujos. Es adecuado para seguir validando el circuito de demostración. Todavía
no está terminado para operar comercialmente ni medir utilidad real.

## Inconsistencias corregidas

- El resumen del checkout ahora comprueba disponibilidad de stock y turno antes
  de confirmar. Comparte la consulta con el menú; la transacción de confirmación
  sigue siendo la autoridad final y vuelve a validar ante ventas simultáneas.
- El catálogo público solo ofrece estaciones compatibles con el checkout:
  Cocina y Barra. Una estación DELIVERY no implementada no se anuncia como vendible.
- Editar recetas conserva la procedencia almacenada del producto o Excel,
  sin permitir su sustitución mediante datos enviados por el cliente. Los tiempos
  desconocidos siguen siendo null, no cero.
- La exportación JSON separa formulaciones completas, en lotes de hasta 100,
  del respaldo de fichas con pendientes. El importador exige insumos activos.
- Los conteos de inventario usan precisión decimal suficiente para cantidades
  e importes grandes, incluso al sumar 1000 líneas.
- Cocina/Barra vuelven a mostrar avisos de cancelación aprobada, con número de
  pedido y descarte durante la visita, sin restaurar tarjetas canceladas.
- Se eliminó configuración duplicada de cookies/CSRF, se añadió un ejemplo de
  entorno sin credenciales y se actualizaron README y contratos desfasados.

No se modificaron pedidos, precios, saldos ni usuarios durante esta revisión.
Los cambios no requieren migraciones nuevas.

## Verificación

- Backend: 112 pruebas ejecutadas; 110 correctas y 2 omitidas porque requieren
  bloqueos concurrentes de PostgreSQL, no disponibles en SQLite.
- Frontend: 17 pruebas correctas, lint y compilación de producción correctos.
- `makemigrations --check --dry-run`: sin cambios de esquema pendientes.
- `git diff --check`: sin errores de espacios.
- Consulta de la base configurada en transacción de solo lectura y snapshot
  consistente: 23 pedidos, 71 saldos, 148 movimientos, 74 recetas activas y
  71 productos publicados. Sin discrepancias detectadas en totales de pedidos,
  cadena de movimientos/saldos, diferencias de cierre, estaciones de tickets o
  versiones vigentes. No se encontraron procedencias históricas perdidas.

No se realizaron pruebas visuales E2E ni de carga en esta revisión. Las pruebas
de concurrencia deben ejecutarse en PostgreSQL aislado antes de un despliegue.

## Prioridades pendientes

1. Validar con el restaurante fotos, descripciones, ingredientes, alérgenos y
   nutrición de los platos renombrados. El código no puede certificar esos datos.
2. Definir vínculo explícito producto–receta y guardar versión/costo por venta.
   Tener 71 productos y 74 fichas no es por sí mismo un error: no son la misma
   entidad. El dashboard actual no representa rentabilidad histórica real.
3. Incorporar consumo y kardex de insumos si se desea inventario de materias
   primas. Los conteos de costeo y stock de platos terminados tienen fines distintos.
4. Integrar pago real, conciliación, reembolsos y confirmación de entrega física.
   Un pedido SIMULATED sigue siendo demostración, aunque genere trabajo y stock.
5. Preparar despliegue con HTTPS, orígenes/cookies, estáticos, copias y restauración
   probada, monitoreo y CI; probar permisos y recorridos completos en navegador,
   dispositivos y carga concurrente.

La siguiente etapa aconsejable es validar los datos y cerrar el vínculo entre
receta, producto y costo histórico antes de ampliar indicadores financieros.
