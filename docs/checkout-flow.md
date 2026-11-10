# Carrito, pago simulado y seguimiento

El flujo de demostración tiene tres pasos:

1. `/cart`: una tarjeta reúne los productos, sus cantidades, el nombre del cliente,
   consumo en mesa o recogida, la mesa cuando corresponde y el total verificado.
   `Pagar` abre el checkout; `Seguir comprando` está inmediatamente debajo.
2. `/checkout`: muestra el resumen, la entrega y los métodos ficticios de tarjeta
   y billetera. No solicita datos bancarios, carga SDK de un proveedor ni cobra
   dinero en el flujo simulado. El botón final confirma el pago de demostración.
3. `/orders/:publicCode`: presenta el estado y actualiza el progreso de preparación
   mediante la consulta existente del pedido.

El borrador de entrega se guarda en `sessionStorage` al pulsar `Pagar` en el
carrito. No se crea un pedido en ese momento. El checkout exige que los productos
y cantidades coincidan con el borrador y vuelve a comprobar precios y stock.
Cuando el total cambia, el nuevo importe se muestra antes de confirmar.

Al confirmar se guarda un intento con una clave de idempotencia antes del POST a
`/api/v1/orders/`. La API existente crea el pedido simulado y sus tickets de prueba.
Si se pierde la respuesta, `Recuperar confirmación` reutiliza esa clave, incluso
después de recargar. El carrito y el borrador se limpian únicamente después de que
la API confirma el pedido. Ante un rechazo de validación o disponibilidad se
permite revisar el carrito y obtener una nueva cotización.

La configuración de pagos existente continúa seleccionando el checkout de
demostración cuando Culqi está desactivado. No se modifican sus endpoints ni el
procesamiento de intentos antiguos de Culqi. El nuevo diseño corresponde al flujo
simulado solicitado.

## Publicación

Desplegar los cambios del frontend en Vercel. Este cambio no requiere migraciones
ni actualización de datos en Supabase. El backend debe conservar habilitado el
flujo de pedidos de demostración para poder cotizar y confirmar.

## Comprobaciones

- Compilación TypeScript y Vite, y lint del frontend.
- Pruebas de `tests/checkout-draft.test.mjs`: datos de entrega, recuperación del
  borrador, carrito modificado, borradores corruptos y almacenamiento bloqueado.
- Prueba local en Chromium con API interceptada: carrito → pago → estado, mesa y
  recogida, tarjeta y billetera, doble clic, recarga y recuperación con la misma
  clave, error de disponibilidad, acceso directo sin borrador y vista móvil sin
  desbordamiento horizontal. No crea pedidos en la base compartida.
