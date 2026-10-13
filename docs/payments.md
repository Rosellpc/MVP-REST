# Culqi: Checkout Custom, cargos de prueba, 3DS y conciliación

Integración exclusivamente de **pruebas**. Las llaves live están bloqueadas. Los
pagos aprobados en Culqi test generan tickets de demostración y descuentan stock
operativo; no representan ingresos reales. No se han implementado reembolsos ni
habilitado cobros comerciales.

## Activar después de validar las credenciales

En backend/.env (no reemplazar el resto del archivo):

```dotenv
PAYMENTS_ENABLED=True
PAYMENTS_ENVIRONMENT=test
PAYMENT_RESERVATION_MINUTES=10
CULQI_PUBLIC_KEY=tu_pk_test
CULQI_SECRET_KEY=tu_sk_test
PRODUCTION_DEMO_ENABLED=True
```

Las llaves deben ser del mismo comercio y entorno. La secreta permanece en Django;
no usar VITE_ para ella. Reiniciar Django tras cambiar .env. Aplicar las migraciones
con `python manage.py migrate`. El stock debe estar habilitado, con turno abierto.

Con PAYMENTS_ENABLED=False, /checkout conserva el flujo demo previo. Si se activa
sin configuración válida se muestra configuración pendiente; no se sustituye un
pago fallido por una confirmación demo. Los intentos demo anteriores se recuperan
por su circuito original.

Culqi respondió HTTP 401 a la consulta de credenciales del 12/10/2026. Corregir o
regenerar la llave secreta en CulqiPanel antes de activar el flujo. No se hizo un
cargo externo ni se validó el formulario contra una cuenta autorizada en esta sesión.

## Flujo

1. React consulta la configuración pública y el resumen calculado por Django.
2. Preparar crea el pedido pendiente y reserva stock de forma idempotente.
3. Custom Checkout obtiene el token de tarjeta; PAN y CVV no pasan por Django.
4. Django reclama un intento en transacción y luego hace el POST fuera del bloqueo.
5. Ante REVIEW, React inicia 3DS y devuelve sus parámetros con el mismo token,
   correo y dispositivo. El backend comprueba esa vinculación por huellas SHA-256.
6. Django consulta el cargo con su llave secreta. Verifica importe, PEN, entorno,
   fuente y metadata del pedido/intento. Un mensaje del navegador no acredita pagos.
7. Un cargo capturado y exitoso convierte la reserva en salida de stock y genera
   tickets exactamente una vez. El cliente accede al seguimiento existente.

No se decide éxito solo por HTTP 200/201: las páginas de documentación muestran
una discrepancia entre esos códigos. Se comprueba el objeto, outcome y capture.
El campo paid de Culqi no se utiliza como prueba del cobro del cliente: los ejemplos
incluyen cargos capturados exitosos con paid=false.

## API bajo /api/v1/payments/

| Método/ruta | Función |
| --- | --- |
| GET config/ | Disponibilidad y llave pública; nunca llave secreta |
| POST preview/ | Precios y disponibilidad, sin reservar |
| POST prepare/ | Pedido pendiente y reserva; Idempotency-Key UUID |
| GET {public_code}/ | Estado público limitado, sin nombre ni mesa |
| POST {public_code}/charge/ | Cargo o continuación 3DS; clave UUID del intento |
| POST {public_code}/reconcile/ | Consulta al proveedor; jamás vuelve a cobrar |
| POST {public_code}/abandon/ | Libera antes del cargo o durante REVIEW sin POST en curso |
| POST culqi/webhook/ | Notificación usada como pista; comprueba el cargo mediante GET autenticado |

Preparar recibe items (product_id, quantity), customer_name, fulfillment,
table_label si es DINE_IN y expected_total. Los ID/precios son los del menú actual.
La integración con 3DS limita este circuito a S/ 3.00–9,999.00.

Cargo recibe source_id de prueba, email y device_id; la continuación añade
`authentication_3DS` (eci, xid, cavv, protocolVersion y, cuando corresponda,
directoryServerTransactionId). El servidor fija el importe, moneda y metadata.
No almacena tokens, PAN, CVV, datos 3DS ni respuestas completas del proveedor.

## Recuperación y stock

Se preserva en sessionStorage la referencia del pedido y clave del intento antes
de enviar solicitudes. El token/dispositivo para continuar 3DS queda solo en memoria.
La recarga consulta el pedido; no repite el POST de cobro. Una autenticación
interrumpida puede abandonarse únicamente mientras el servidor siga en REVIEW.
PROCESSING y UNKNOWN nunca se abandonan o vencen automáticamente.

Un timeout conserva stock y exige consulta; no se interpreta como rechazo. La
conciliación busca por referencia conocida o recorre hasta 10 páginas de cargos
recientes buscando metadata y validando el resultado. No encontrar un cargo no
prueba que no exista: el intento sigue pendiente para revisión. No se marca
pagado un cargo de otra moneda, importe, fuente o comercio/entorno.

Balance.quantity sigue representando existencia física. El menú resta reservas
HELD/PROCESSING. Ventas demo, mermas y ajustes no pueden consumirlas, y el turno
no puede cerrarse mientras existan. Pedidos Culqi test aprobados aparecen en Admin
identificados como integración; el dashboard de ventas demo anterior no los suma
como ingresos reales. Cancelar producción no ejecuta un reembolso.

## Webhooks y tarea periódica

En CulqiPanel → Eventos → Webhooks registrar la URL HTTPS pública del backend:
`https://tu-dominio/api/v1/payments/culqi/webhook/`, para eventos de cargos. Culqi no
puede acceder a 127.0.0.1. Se necesita un túnel o entorno HTTPS de pruebas.
El webhook nunca confía en importes, metadata o éxito enviados en la notificación:
recupera el cargo directamente de Culqi. Las notificaciones duplicadas son inocuas.

Programar cada minuto, sin solapar ejecuciones:

```powershell
python manage.py reconcile_payments
```

Consulta hasta 50 intentos pendientes y vence hasta 500 reservas sin cobro iniciado.
También sigue disponible `python manage.py expire_payment_reservations` para vencer
reservas únicamente. No se instaló una tarea permanente en Windows. Antes de poner
el circuito en uso hay que configurar esa tarea y probar la URL de webhook.

Los registros financieros son de solo lectura en Django Admin. Si no se puede
verificar un cargo, no liberar stock ni forzar PAID manualmente: revisar CulqiPanel
con su referencia y resolver la conciliación. Las consultas no devuelven payloads
privados ni claves. Para despliegue se requieren rate limits globales y protección
contra abuso de reservas; los límites por caché local no sustituyen esos controles.

## Pruebas y límites

Validación del 12/10/2026: migración payments.0002 aplicada; 136 pruebas backend
correctas y 8 entradas de concurrencia omitidas por SQLite. Se ejecutaron aparte
las 6 pruebas de PaymentConcurrencyTests en PostgreSQL aislado, todas correctas
(incluyen las dos regresiones demo que SQLite enumera también por separado).
Frontend: 19 pruebas correctas, build y lint correctos. El esquema temporal fue
eliminado y no se crearon pedidos de prueba en la base del restaurante.

`python manage.py test --settings=core.test_settings` verifica estados, vinculación
3DS, timeouts, rechazo, rollback, notificaciones duplicadas y privacidad con Culqi
simulado. `payments.test_concurrency` usa PostgreSQL aislado para doble envío de
cargo, verificación concurrente y competencia por stock. Frontend incluye pruebas
del origen de mensajes 3DS y cancelación de listeners, además de build y lint.

Falta la prueba real de integración en navegador con llaves aceptadas: aprobación,
rechazo, reto 3DS, recarga, webhook y conciliación. No equivale a habilitar
producción. Devoluciones, conciliación de abonos y operación live son otra etapa.

Yape permanece desactivado en este checkout de integración: la guía de entornos
de Culqi especifica tarjetas de prueba. No se solicita un código Yape real para
simular pagos. Su activación requiere confirmar con Culqi el entorno y las pruebas
habilitadas para el comercio antes de ofrecerlo al cliente.

## Referencias oficiales consultadas

- [Custom Checkout](https://docs.culqi.com/es/documentacion/checkout/checkout-custom)
- [Configuración 3DS](https://docs.culqi.com/es/documentacion/culqi-3ds/v1/configuracion/)
- [Uso de 3DS](https://docs.culqi.com/es/documentacion/culqi-3ds/v1/uso-libreria/)
- [API de cargos y consultas](https://apidocs.culqi.com/)
- [Entorno de integración](https://docs.culqi.com/es/documentacion/pagos-online/integracion-vs-produccion/)
