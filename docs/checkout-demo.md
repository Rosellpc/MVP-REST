# Carrito y checkout de demostración

## Alcance acordado

- Pago simulado, identificado en checkout y confirmación.
- Consumo en mesa o recojo para llevar.
- PEN y precios finales con impuestos incluidos: no se añade un impuesto extra.
- Pedido persistido en Django con `DEMO_CONFIRMED` y pago `SIMULATED`.
- No se cobra dinero, no se capturan tarjetas, no se envían tickets a cocina y no se descuenta inventario.

Esto completa el recorrido **del cliente en modo demostración**. Un restaurante
operando con pedidos reales todavía necesita el flujo de cobro, producción y stock
descrito en el README. Los pedidos demo deben quedar fuera de métricas de ventas reales.

## 1. Archivos del frontend

| Archivo | Responsabilidad |
|---|---|
| `src/features/cart/cartState.ts` | Tipos, cantidades entre 1 y 99, subtotal en centavos y recuperación de carrito. |
| `src/features/cart/CartContext.ts` | Contrato compartido y hook `useCart`. |
| `src/features/cart/CartProvider.tsx` | Estado global del carrito y persistencia en `sessionStorage`. |
| `src/components/products/DishCard.tsx` | Recibe el producto completo y permite agregarlo. |
| `src/components/products/DishesSection.tsx` | Entrega cada producto a su tarjeta. |
| `src/components/layout/Header.tsx` | Enlace al carrito con contador de unidades. |
| `src/pages/CartPage.tsx` | Cantidades, eliminación, vaciado, subtotal y acceso al checkout. |
| `src/features/orders/orderApi.ts` | Consulta de resumen, creación idempotente y consulta de confirmación. |
| `src/features/orders/useOrderQuote.ts` | Carga, errores y reintento del total verificado por Django. |
| `src/features/orders/checkoutAttempt.ts` | Conserva el intento de confirmación para recuperarlo tras una interrupción. |
| `src/pages/CheckoutPage.tsx` | Datos de entrega, aceptación de demostración y envío. |
| `src/pages/OrderConfirmationPage.tsx` | Confirmación persistida consultada por código público. |
| `src/styles/checkout.css` | Diseño carbón y vidrio, con adaptación a móvil. |
| `src/main.tsx` | Monta `CartProvider` y carga la nueva hoja de estilos. |
| `src/App.tsx` | Registra carrito, checkout y confirmación. |
| `tests/cart.test.mjs` | Pruebas del estado del carrito y almacenamiento dañado. |

El carrito sobrevive a recargas en la misma pestaña. Si el navegador bloquea el
almacenamiento, puede usarse en memoria, pero confirmar requiere conservar la clave
del intento. El almacenamiento de sesión no sustituye un pedido guardado en Django.

Rutas:

```text
/menu                 → elegir productos
/cart                 → revisar cantidades
/checkout             → verificar precios y confirmar pago simulado
/orders/:publicCode   → consultar la confirmación guardada
```

## 2. Archivos del backend

La nueva aplicación `backend/orders/` contiene:

- `models.py`: pedido, líneas y fotografías de nombre, precio y estación.
- `serializers.py`: valida productos, cantidades y datos de entrega.
- `services.py`: verifica disponibilidad y recalcula el total; guarda pedido y líneas en una transacción.
- `views.py` / `urls.py`: endpoints de resumen, creación y consulta pública.
- `admin.py`: permite inspeccionar pedidos demo sin editar sus importes.
- `migrations/0001_initial.py`: crea las tablas y restricciones.
- `tests.py`: pruebas de importes, disponibilidad, validaciones, recuperación y privacidad.

Se registra la aplicación en `core/settings.py`, `core/test_settings.py` y sus rutas
en `core/urls.py`. La prueba de paginación de catálogo ahora utiliza el tamaño
configurado (100), en lugar de asumir el valor antiguo de 20.

## 3. Activación local: pasos pendientes en tu base configurada

Los archivos ya están implementados. **La migración no se ha aplicado a Supabase**:
la validación automatizada utiliza SQLite aislado y una base temporal de navegador.

En Git Bash:

```bash
cd /c/Dev/MVP-REST/backend
source .venv/Scripts/activate
python manage.py check
python manage.py migrate --plan
python manage.py migrate
```

`migrate` actúa sobre la base definida en tu `backend/.env`; comprueba el entorno
de destino antes de ejecutarlo. Es una migración aditiva de pedidos y sus líneas.

En `backend/.env`, agrega o ajusta **solo** esta variable:

```dotenv
ORDER_DEMO_ENABLED=True
```

Sin esa variable, el valor predeterminado coincide con `DEBUG`. Si la demostración
está deshabilitada, la API de pedidos responde 403. No reemplaces el resto del `.env`.

Después:

```bash
python manage.py runserver 127.0.0.1:8000
```

En otra terminal:

```bash
cd /c/Dev/MVP-REST/frontend
pnpm run dev
```

Abre `http://127.0.0.1:5173/menu`. No se añadieron dependencias de runtime.
El proxy de Vite sigue enviando `/api` al backend local.

## 4. Contrato de la API

### POST `/api/v1/orders/preview/`

```json
{"items": [{"product_id": 1, "quantity": 2}]}
```

Devuelve `items`, `total`, `currency: "PEN"`, `prices_include_taxes: true` y
`demo: true`. Cada línea contiene `product_id`, `name`, `quantity`, `unit_price`
y `line_total`. Los importes son cadenas decimales calculadas por Django.

### POST `/api/v1/orders/`

Cabecera `Idempotency-Key: <UUID aleatorio>` y cuerpo:

```json
{
  "items": [{"product_id": 1, "quantity": 2}],
  "customer_name": "Cliente",
  "fulfillment": "DINE_IN",
  "table_label": "12",
  "expected_total": "51.00",
  "accept_demo": true
}
```

El ID y el total del ejemplo son ilustrativos: utiliza los recibidos en tu carta
y resumen. Para recoger, usa `PICKUP`; no se requiere mesa.

`expected_total` solo sirve para detectar un cambio de precio desde la revisión;
**no determina el total guardado**. Django lo recalcula desde el catálogo.

- 201: pedido creado.
- 200: mismo intento ya registrado; devuelve el mismo pedido.
- 400: datos inválidos o productos no disponibles.
- 403: modo demo deshabilitado.
- 409: cambió el precio o se reutilizó una clave con otro contenido.
- 429: demasiadas solicitudes; conserva la clave para reintentar.

### GET `/api/v1/orders/<publicCode>/`

Devuelve código público aleatorio, fecha, modalidad, líneas, total y estados demo.
No expone nombre del cliente, mesa, ID interno, estación ni clave idempotente.
Un código inexistente responde 404. El enlace funciona como acceso a esa
confirmación: quien lo conoce puede consultar ese resumen limitado.

## 5. Recuperación y cambios de precio

1. El checkout verifica precios y disponibilidad antes de habilitar confirmación.
2. Guarda una clave aleatoria y el contenido del intento antes del POST.
3. Bloquea envíos repetidos mientras la petición está en curso.
4. Si la respuesta se pierde o tarda más de 10 segundos, conserva el intento.
5. «Recuperar confirmación» reenvía exactamente la misma clave y contenido.
6. Django devuelve el pedido existente si ya lo había guardado.
7. Solo tras recibir la confirmación se vacía el carrito.

Mientras exista una confirmación incierta no se puede modificar ese carrito.
Si Django rechaza un precio cambiado, se recarga el resumen y el usuario debe
volver a aceptar el nuevo total. Un reintento de consulta desde la confirmación
solo realiza un GET y nunca crea otro pedido.

## 6. Verificación

Backend, sin acceder a Supabase:

```bash
cd /c/Dev/MVP-REST/backend
source .venv/Scripts/activate
python manage.py test orders catalog --settings=core.test_settings
python manage.py makemigrations --check --dry-run --settings=core.test_settings
```

Frontend (Node 22.14 o compatible con `--experimental-strip-types`):

```bash
cd /c/Dev/MVP-REST/frontend
pnpm test
pnpm run build
pnpm run lint
```

Comprobaciones manuales:

1. Agrega el mismo producto dos veces: una fila y cantidad 2.
2. Cambia cantidades, elimina productos y vacía el carrito.
3. Recarga la pestaña: conserva el carrito.
4. Abre `/checkout` con carrito vacío: vuelve a `/cart`.
5. Confirma en mesa: exige nombre, mesa y aceptación demo.
6. Confirma para recoger: no exige mesa.
7. Cambia el precio antes de confirmar: rechaza y muestra el resumen actualizado.
8. Deshabilita un producto antes de confirmar: rechaza sin guardar un pedido parcial.
9. Consulta y recarga la URL de confirmación: conserva el pedido guardado.
10. Comprueba escritorio, móvil y navegación con teclado.

Las pruebas SQLite cubren idempotencia secuencial y rollback. El bloqueo concurrente
entre varias conexiones PostgreSQL debe validarse en un entorno de staging antes
de habilitar pedidos reales. La protección implementada combina transacción,
restricción única de clave idempotente y bloqueo de productos al confirmar.
