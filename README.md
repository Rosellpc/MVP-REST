# RestaurantOS — Plataforma Full Stack de autoservicio y gestión de restaurante

**Acceso del personal:** autenticación por sesión, CSRF, roles ADMIN/KITCHEN/BAR y
rutas internas protegidas. [Activación, permisos y pruebas](docs/production-flow.md).
**Producción de demostración:** API interna de tickets por estación, liberación manual
y transiciones auditadas. [Activación y contrato](docs/production-api.md).
Las pantallas de Cocina y Barra muestran tickets y permiten avanzar su preparación.
Administración libera pedidos de prueba; el cliente consulta el estado agregado.

**Menú por categorías y fichas de producto:** barra lateral, enlaces individuales e
información alimentaria editable. [Activación y pruebas](docs/menu-product-details.md).

**Flujo del cliente de demostración:** menú → carrito → checkout → confirmación
persistida en Django. Pago simulado, mesa o recojo, PEN e impuestos incluidos.
La migración de pedidos debe aplicarse a la base configurada antes de probarlo.
Consulta los [cambios, activación y pruebas del checkout](docs/checkout-demo.md).
Esta implementación no realiza cobros reales ni activa producción o inventario.

> **Estado:** base local implementada; dominio y Supabase pendientes · **Versión:** 0.1.0 · **Tipo:** MVP (producto mínimo viable)  
> **Stack principal:** React + TypeScript + React Router · Django + Django REST Framework · PostgreSQL (Supabase)  
> **Despliegue propuesto:** Vercel (frontend) + Railway o Render (backend) + Supabase (base de datos)

**API pública del menú implementada:** `GET /api/v1/menu/` consulta el catálogo
persistente configurado en Django. Contrato, filtros, comandos de Git Bash y pruebas
en [backend/catalog/API.md](backend/catalog/API.md). Esta implementación sustituye
la carta temporal descrita en la sección de arranque; el frontend ya consume esta API.

## Tabla de contenidos

1. [Visión del proyecto](#1-visión-del-proyecto)
2. [Objetivos y usuarios](#2-objetivos-y-usuarios)
3. [Alcance del MVP y decisiones de producto](#3-alcance-del-mvp-y-decisiones-de-producto)
4. [Arquitectura de alto nivel](#4-arquitectura-de-alto-nivel)
5. [Stack tecnológico](#5-stack-tecnológico)
6. [Módulos y requisitos funcionales](#6-módulos-y-requisitos-funcionales)
7. [Flujos de negocio y reglas críticas](#7-flujos-de-negocio-y-reglas-críticas)
8. [Modelo de dominio y base de datos](#8-modelo-de-dominio-y-base-de-datos)
9. [API REST propuesta](#9-api-rest-propuesta)
10. [Estructura del repositorio](#10-estructura-del-repositorio)
11. [Seguridad, permisos e integridad de datos](#11-seguridad-permisos-e-integridad-de-datos)
12. [Despliegue y observabilidad](#12-despliegue-y-observabilidad)
13. [Plan de implementación por fases](#13-plan-de-implementación-por-fases)
14. [Primeros pasos: instalación y arranque](#14-primeros-pasos-instalación-y-arranque)
15. [Criterios de aceptación del MVP](#15-criterios-de-aceptación-del-mvp)
16. [Decisiones pendientes y evolución](#16-decisiones-pendientes-y-evolución)
17. [Glosario](#17-glosario)

---

## 1. Visión del proyecto

RestaurantOS es una aplicación web Full Stack para un restaurante con atención de autoservicio: el cliente explora el menú digital, configura su pedido y lo confirma sin intervención de un mozo. El sistema distribuye automáticamente las preparaciones a cocina y barra, registra los movimientos de inventario asociados a recetas estandarizadas y centraliza indicadores operativos y comerciales en un dashboard.

**Propuesta de valor:** una única fuente de datos para conectar venta → producción → consumo de insumos → costos → indicadores.

**No es solamente un menú digital.** Es la base de un sistema de gestión de restaurante con KDS (*Kitchen Display System*), kardex e inteligencia de negocio. El diseño inicial debe ser lo bastante simple para completar un MVP sin comprometer la trazabilidad de pedidos e inventario.

### Problemas que busca resolver

- Reducir la intervención manual en el registro de pedidos.
- Evitar que cocina y barra dependan de tickets transcritos a mano.
- Conocer qué productos se venden, cuánto tardan en prepararse y a qué costo teórico.
- Registrar ingresos, salidas, mermas y ajustes de inventario con una referencia verificable.
- Mostrar indicadores coherentes con las transacciones realmente registradas.

## 2. Objetivos y usuarios

| Actor | Objetivo | Interfaz principal |
|---|---|---|
| Cliente | Consultar menú, personalizar pedido, confirmar y seguir su estado | Autoservicio |
| Personal de cocina | Recibir preparaciones, iniciar y terminar tickets | KDS cocina |
| Personal de barra | Recibir bebidas y marcar su preparación | KDS barra |
| Encargado de inventario | Registrar compras, mermas, ajustes y conteos; revisar kardex | Inventario |
| Administrador / gerente | Gestionar catálogo, recetas, costos, usuarios y métricas | Administración y dashboard |

**Supuesto del MVP:** una sede y una sola moneda operativa. Preparar el modelo para múltiples estaciones; el soporte completo multi-sede es una fase posterior.

## 3. Alcance del MVP y decisiones de producto

### Incluido en la primera versión

- Menú digital con categorías, fotografías opcionales, precios y disponibilidad.
- Carrito y creación de pedidos de autoservicio.
- Número o código público de pedido y pantalla de seguimiento.
- Enrutamiento de ítems a cocina y/o barra según su estación de preparación.
- KDS de cocina y barra con estados independientes.
- Alta y edición administrativa de ingredientes, platos, recetas y costos teóricos.
- Kardex basado en movimientos inmutables o reversados mediante contramovimientos.
- Registro de entradas, consumo teórico por ventas, mermas y ajustes autorizados.
- Dashboard básico: ventas registradas, número de pedidos, ticket promedio, tiempos y costo teórico.
- Usuarios internos con roles y control de acceso.

### Fuera del MVP, salvo que resulte imprescindible

- Facturación electrónica, obligaciones fiscales y contabilidad general.
- CRM, puntos de fidelidad, cupones y campañas.
- Compras y cuentas por pagar avanzadas, integración directa con proveedores.
- Optimización de producción, previsión de demanda y modelos predictivos.
- Gestión integral de múltiples locales.
- Aplicaciones móviles nativas.

### Decisión necesaria antes de vender de verdad: cobro

Un pedido **confirmado** no debe confundirse con un pedido **pagado**. Para un prototipo sin transacciones reales puede usarse un pago simulado, claramente identificado como tal. Para operar en un restaurante real, integrar una pasarela o un proceso de cobro validado antes de liberar pedidos a producción; no almacenar datos de tarjeta en la aplicación.

Estados de pago sugeridos: `UNPAID`, `PENDING`, `PAID`, `FAILED`, `REFUNDED`. La implementación concreta de cobros y reembolsos queda fuera del MVP técnico si se trabaja con simulación.

## 4. Arquitectura de alto nivel

```mermaid
flowchart TD
    C[Cliente / kiosco React] --> API[Django + DRF]
    K[KDS cocina React] <-->|HTTP / actualizaciones| API
    B[KDS barra React] <-->|HTTP / actualizaciones| API
    A[Administración y dashboard React] --> API
    API --> DB[(PostgreSQL en Supabase)]
    API --> AUTH[Autenticación, permisos y reglas de negocio]
    API -. fase posterior .-> WS[Django Channels + Redis]
    WS -. eventos .-> K
    WS -. eventos .-> B
```

**Responsabilidades:**

- **React:** experiencia de usuario, formularios, navegación, estado local de carrito y representación de datos.
- **Django + DRF:** autenticación de personal, autorización, validación, precios definitivos, transiciones de estados, creación de tickets, inventario y cálculos del dominio.
- **PostgreSQL:** persistencia relacional, restricciones, transacciones e integridad referencial.
- **Supabase:** alojamiento administrado de PostgreSQL; no exponer credenciales de la base de datos en React.
- **Comunicación en tiempo real:** primero *polling* controlado; posteriormente WebSockets si aportan valor operacional.

**Regla de arquitectura:** React nunca registra por su cuenta una venta o un movimiento de stock. Toda operación con efectos de negocio pasa por el backend, que valida permisos y ejecuta transacciones.

### ¿Una o varias aplicaciones React?

Para el MVP, **una aplicación React con rutas y layouts separados**:

```text
/menu                   menú público
/cart                   carrito
/checkout               confirmación y flujo de cobro del MVP
/orders/:publicCode     seguimiento público del pedido
/login                  acceso de personal
/kitchen                KDS cocina, protegido
/bar                    KDS barra, protegido
/inventory              kardex y movimientos, protegido
/recipes                recetas y costos, protegido
/dashboard              indicadores, protegido
/admin                  mantenimiento interno, protegido
```

La ruta pública de seguimiento empleará un identificador aleatorio no secuencial (`publicCode`), con información limitada y sin revelar datos personales ni rutas administrativas. Cada área tiene un layout y permisos específicos.

## 5. Stack tecnológico

| Capa | Tecnología | Función |
|---|---|---|
| Frontend | React + TypeScript | Componentes tipados e interfaces |
| Navegación | React Router | Rutas, layouts y protección de vistas |
| Datos del servidor | TanStack Query | Solicitudes, caché e invalidación |
| Estado local | Zustand (opcional) | Carrito temporal y estado de interfaz |
| Formularios | React Hook Form + Zod (opcional al inicio) | Formularios y validación de UX |
| Estilos | Tailwind CSS | Sistema visual y diseño adaptable |
| Backend | Python + Django | Modelos, ORM, autenticación y reglas de negocio |
| API | Django REST Framework | Serializadores, endpoints, permisos y validación |
| Base de datos | PostgreSQL en Supabase | Datos relacionales y transacciones |
| Frontend deploy | Vercel | Hosting de la SPA |
| Backend deploy | Railway o Render | Servicio Python persistente |
| Control de versiones | Git + GitHub | Historial y colaboración |
| Infraestructura local | Docker (opcional al inicio) | Entornos reproducibles |
| Actualizaciones KDS | Polling inicialmente | Refrescar órdenes sin recargar manualmente |
| Tiempo real posterior | Django Channels + Redis | WebSockets y mensajería |
| Tareas diferidas posteriores | Celery + Redis u otra cola | Procesamiento asíncrono cuando exista un caso real |

**Por qué no duplicar funciones con Supabase:** Django administrará cuentas del personal, autorización, ORM y API. Usar Supabase como PostgreSQL administrado; no introducir Supabase Auth, sus APIs automáticas o lógica de negocio paralela sin una decisión arquitectónica explícita.

**Nota sobre despliegue:** Vercel aloja el frontend; Django se despliega por separado. Las características de planes y límites de proveedores pueden cambiar: verificarlas al desplegar.

## 6. Módulos y requisitos funcionales

### 6.1. Autoservicio del cliente

**Flujo:** abrir menú → explorar categorías → seleccionar ítems y opciones → añadir al carrito → confirmar datos de la orden → completar/simular cobro → recibir código → consultar estado.

**Requisitos:**

- Listar únicamente productos publicados y disponibles para venta.
- Mostrar precio final, descripción, alérgenos cuando se hayan registrado y opciones válidas.
- Validar en servidor precio, disponibilidad y cantidades antes de aceptar la orden: nunca confiar en los importes calculados por el navegador.
- Evitar duplicados si el cliente pulsa dos veces «Confirmar» (clave de idempotencia).
- Entregar código público para seguimiento, sin exponer un ID interno predecible.
- Definir si el restaurante permite pedidos sin cuenta, para llevar y/o para consumir en el local.

### 6.2. KDS de cocina y barra

Cada producto vendible tiene una **estación de preparación** asignada: `KITCHEN`, `BAR` o, para productos sin preparación, una estación de entrega explícita definida por negocio. Un mismo pedido genera uno o varios tickets por estación; cada ticket contiene solamente los ítems pertinentes.

**Estados de ticket:** `PENDING` → `IN_PROGRESS` → `READY`; `CANCELLED` sólo mediante una operación autorizada y registrada. Marcar un ticket como listo no convierte automáticamente todo el pedido en listo si faltan otras estaciones.

**Requisitos:** cola de tickets; hora de recepción; contador de tiempo; identificación de ítems y modificadores; cambios de estado autorizados; aviso de ticket nuevo; trazabilidad de quién cambió cada estado.

**MVP técnico:** consultar tickets activos cada 3–5 segundos con TanStack Query (intervalo configurable, detener o ajustar cuando la pestaña no esté activa). **Evolución:** WebSockets con Django Channels y Redis si el volumen, la latencia requerida o las notificaciones lo justifican.

### 6.3. Catálogo, recetas y costos

Distinguir estrictamente:

- **Ingrediente / insumo:** inventariable (pisco, limón, papa, aceite).
- **Producto vendible / plato:** ítem visible en el menú (Pisco Sour, Lomo Saltado).
- **Receta:** composición estandarizada del producto; incorpora cantidades, unidad y rendimiento.
- **Versión de receta:** fotografía de la formulación vigente al confirmar una venta, para que cambiar una receta no altere consumos y costos históricos.

**Ejemplo de receta por porción (cantidades ilustrativas, a validar en operación):**

| Producto vendible | Insumo | Cantidad estándar | Unidad |
|---|---|---:|---|
| Pisco Sour | Pisco quebranta | 60 | ml |
| Pisco Sour | Jugo de limón | 30 | ml |
| Pisco Sour | Jarabe | 20 | ml |
| Pisco Sour | Clara de huevo | 20 | ml |
| Pisco Sour | Amargo aromático | 3 | ml |

Los ejemplos no representan una receta comercial validada ni un cálculo de alérgenos completo. Mantener unidades canónicas por insumo (por ejemplo, ml, g o unidades) y conversiones explícitas de compra a consumo. Registrar el rendimiento real de preparaciones intermedias y mermas estándar cuando corresponda.

**Costeo:** costo teórico por porción = suma de `cantidad consumida del insumo × costo unitario aplicable`, considerando conversiones, rendimiento y merma estándar. La política de valorización de inventario (promedio ponderado, FIFO u otra) debe definirse antes del kardex valorizado. Evitar confundir costo teórico con costo real.

### 6.4. Inventario y kardex

El inventario se explica mediante **movimientos de stock**, no mediante cambios aislados de `current_stock` sin historial. El saldo puede mantenerse como dato derivado o cacheado, pero debe reconciliar con los movimientos.

| Tipo de movimiento | Efecto habitual | Ejemplo |
|---|---|---|
| `PURCHASE_RECEIPT` | Entrada | Recepción de 10 kg de papa |
| `SALE_CONSUMPTION` | Salida | Ingredientes consumidos por una orden |
| `WASTE` | Salida | Insumo descartado por deterioro |
| `ADJUSTMENT_IN` | Entrada | Corrección documentada de conteo |
| `ADJUSTMENT_OUT` | Salida | Corrección documentada de conteo |
| `RETURN_IN` / `RETURN_OUT` | Según caso | Devolución registrada |
| `TRANSFER_IN` / `TRANSFER_OUT` | Según almacén | Traslado entre ubicaciones, si se habilita |

**Ejemplo:** compra `+10 kg` → consumo `−2 kg` → merma `−0,5 kg` → ajuste `+0,2 kg` = saldo `7,7 kg`.

**Requisitos:** fecha/hora, insumo, cantidad firmada o tipo + magnitud, unidad base, costo unitario, referencia de negocio, usuario responsable, motivo cuando aplique y estado contable. No borrar movimientos confirmados: revertir con contramovimiento enlazado. Conciliar entradas/salidas y movimientos físicos mediante conteos.

**Punto crítico:** decidir y documentar **cuándo se reconoce el consumo teórico**: al aceptar el pago, al enviar a producción o al finalizar la preparación. Para el primer MVP, definir un único evento transaccional para registrar consumo y un mecanismo de reversión por cancelación, reembolso o rehacer plato. Si se usa «pedido pagado y liberado a producción», el registro debe ser idempotente y consistente con la creación de tickets. La ejecución física y el consumo real pueden diferir del teórico; registrar mermas/ajustes por separado.

### 6.5. Dashboard

**Versión inicial:**

| Indicador | Definición inicial |
|---|---|
| Ventas registradas | Importe neto de pedidos pagados y no reembolsados, según reglas definidas |
| Pedidos | Conteo de pedidos válidos en el periodo |
| Ticket promedio | Ventas registradas / número de pedidos incluidos |
| Productos vendidos | Cantidades por producto y categoría |
| Tiempo de preparación | Desde recepción en estación hasta `READY` |
| Costo teórico | Consumo estándar de ítems vendidos × costo histórico aplicable |
| Margen bruto teórico | Ventas netas − costo teórico de insumos (no incluye todos los costos operativos) |
| Inventario | Saldo y valor según movimientos y método de valorización adoptado |

Establecer rango de fechas, zona horaria del restaurante, tratamiento de impuestos, descuentos, anulaciones y reembolsos antes de comparar métricas. Todas las métricas financieras se calculan en backend con valores decimales, no con números de coma flotante del navegador.

**Ejemplo de desviación:** 100 Pisco Sours × 60 ml = **6 L de consumo teórico**. Si el inventario físico reconciliado muestra **6,8 L de consumo real** para el mismo periodo e insumo, la desviación es **0,8 L**. Para concluir la causa se necesitan entradas, inventario inicial/final, mermas, cortesías, ajustes y periodo correctamente conciliados.

## 7. Flujos de negocio y reglas críticas

### 7.1. Ciclo de vida del pedido

```text
DRAFT/CART (solo frontend; no representa venta)
  → PENDING_PAYMENT (si hay cobro)
  → CONFIRMED (autorizado para producción)
  → IN_PROGRESS (alguna estación inició producción)
  → READY (todas las preparaciones requeridas están listas)
  → DELIVERED / PICKED_UP

CANCELLED: transición explícita y autorizada, según estado y política.
```

Separar `payment_status` de `order_status`. `READY` de cocina no significa `READY` del pedido si barra sigue preparando. Los productos sin preparación deben contemplar una regla explícita de entrega.

### 7.2. Distribución por estación

Pedido `#105`: 2 Lomo Saltado, 1 Ceviche, 2 Pisco Sour y 1 gaseosa.

- **Ticket cocina:** 2 Lomo Saltado + 1 Ceviche.
- **Ticket barra/entrega:** 2 Pisco Sour + 1 gaseosa, si esa es la estación configurada para la gaseosa.
- Estado agregado del pedido: `READY` solo cuando todos los tickets requeridos estén listos; `IN_PROGRESS` si alguno está en progreso y el conjunto aún no está listo.

La estación del ítem debe **copiarse al detalle/ticket al confirmar el pedido**. Si un administrador cambia mañana la estación de un producto, los pedidos históricos no deben cambiar de destino.

### 7.3. Confirmación segura de pedido

1. Recibir solicitud con clave de idempotencia.
2. Validar catálogo, opciones, cantidades y disponibilidad de venta.
3. Calcular precios e impuestos en backend y crear fotografía del detalle.
4. Verificar pago o aplicar la política explícita de simulación.
5. En **transacción atómica**, confirmar la orden, generar tickets, registrar el consumo teórico si ese es el evento elegido y guardar evento para notificación.
6. Responder con código público y estado. Publicar notificaciones **después del commit**, o mediante una tabla *outbox*, para no anunciar datos que luego se reviertan.

Controlar intentos simultáneos y política de stock insuficiente. Si no se permitirá vender por debajo de cero, bloquear/validar saldos y aplicar la actualización dentro de la misma transacción; no confiar en una comprobación previa desde React.

### 7.4. Cancelaciones y reprocesos

Definir qué ocurre antes y después de enviar el pedido a producción. La cancelación no debe borrar tickets, pedidos ni consumos históricos: conserva auditoría, anula o revierte movimientos cuando proceda y registra responsable/motivo. Rehacer una preparación puede causar consumo adicional y debe reflejarse como tal, no como una segunda venta.

## 8. Modelo de dominio y base de datos

> Esquema conceptual inicial; **no** es todavía una migración final. Los nombres pueden ajustarse al implementar Django. Usar `Decimal`/`numeric` para dinero y cantidades de inventario.

```mermaid
 erDiagram
    PRODUCT ||--o{ RECIPE_VERSION : has
    RECIPE_VERSION ||--o{ RECIPE_INGREDIENT : contains
    INGREDIENT ||--o{ RECIPE_INGREDIENT : used_in
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : sold_as
    ORDER ||--o{ PRODUCTION_TICKET : generates
    PRODUCTION_TICKET ||--|{ PRODUCTION_TICKET_ITEM : contains
    ORDER_ITEM ||--o{ PRODUCTION_TICKET_ITEM : routed_to
    INGREDIENT ||--o{ INVENTORY_MOVEMENT : moves
    ORDER ||--o{ INVENTORY_MOVEMENT : references
    USER ||--o{ INVENTORY_MOVEMENT : records
```

### Entidades mínimas

| Entidad | Campos orientativos | Consideraciones |
|---|---|---|
| `User` / `Role` | id, username/email, role, active | Autenticación de personal y permisos de backend |
| `Station` | id, code, name, active | Cocina, barra y estación de entrega si procede |
| `Category` | id, name, display_order | Agrupación del menú |
| `Product` | id, sku, category_id, name, sale_price, station_id, published, available | Producto vendible; precio de venta no equivale a costo |
| `Ingredient` | id, sku, name, base_unit, active | Insumo almacenado; no mezclar producto vendible e insumo sin una regla explícita |
| `RecipeVersion` | id, product_id, version, yield_quantity, effective_from, status | Versionado y rendimiento por preparación |
| `RecipeIngredient` | id, recipe_version_id, ingredient_id, quantity_base_unit, waste_factor | Cantidad normalizada; definir si merma ya está incluida |
| `Order` | id, public_code, status, payment_status, subtotal, discount, tax, total, created_at | Totales históricos; fechas con zona horaria |
| `OrderItem` | id, order_id, product_id, name_snapshot, unit_price_snapshot, qty, recipe_version_id, station_id | Historial independiente de cambios futuros |
| `ProductionTicket` | id, order_id, station_id, status, created_at, started_at, ready_at | Un ticket por estación y orden en la versión simple |
| `ProductionTicketItem` | id, ticket_id, order_item_id, quantity | Asignación de cantidades a estación |
| `InventoryMovement` | id, ingredient_id, quantity_base_unit, unit_cost, type, reference, user_id, created_at, reversal_of_id | Ledger con trazabilidad y reversión |
| `InventoryBalance` (opcional) | ingredient_id, location_id, quantity_base_unit | Saldo cacheado consistente con ledger |
| `Payment` (si aplica) | id, order_id, provider_ref, amount, status | No guardar números completos de tarjeta |

### Relaciones y restricciones importantes

- `Order` 1:N `OrderItem`; `Order` 1:N `ProductionTicket`.
- `RecipeVersion` 1:N `RecipeIngredient`; cada detalle vendido referencia una versión concreta de receta.
- `InventoryMovement` referencia un insumo, tipo, cantidad, evento de negocio y responsable cuando exista.
- Restricciones únicas en SKU, `public_code`, versión de receta por producto y clave de idempotencia por ámbito.
- Índices sobre fechas, estados de orden/ticket, estación e insumo para consultas operativas.
- No usar `float` para precios, impuestos ni valoración.
- Si existen almacenes o múltiples ubicaciones, añadir `InventoryLocation` antes de implementar transferencias entre ellas.

### Valorización del kardex

El kardex puede ser **físico** (cantidades) o **físico-valorizado** (cantidades y valor monetario). Para este proyecto se busca ambos: antes de programarlo, escoger y documentar un método de costo (por ejemplo, promedio ponderado móvil) y cómo se calculan compras, ajustes, devoluciones, rendimientos y saldo valorizado. No asumir que el precio de la última compra representa automáticamente el costo histórico de todas las salidas.

## 9. API REST propuesta

Prefijo: `/api/v1/`. Las rutas son un contrato preliminar; se formalizarán con serializadores, permisos, paginación y documentación OpenAPI.

| Método | Endpoint | Propósito | Acceso |
|---|---|---|---|
| `GET` | `/api/v1/menu/` | Menú publicado y disponible | Público |
| `POST` | `/api/v1/orders/` | Crear pedido y obtener identificador | Público con controles antiabuso |
| `GET` | `/api/v1/orders/public/{code}/` | Consultar estado público limitado | Público con token/código seguro |
| `POST` | `/api/v1/orders/{id}/confirm/` | Confirmación tras política de pago | Interno o flujo validado de cobro |
| `GET` | `/api/v1/production-tickets/?station=kitchen` | Cola de estación | Personal de estación |
| `POST` | `/api/v1/production-tickets/{id}/start/` | Iniciar preparación | Estación autorizada |
| `POST` | `/api/v1/production-tickets/{id}/ready/` | Marcar listo | Estación autorizada |
| `GET` | `/api/v1/ingredients/` | Listar insumos | Inventario / administración |
| `GET` | `/api/v1/recipes/` | Consultar formulaciones y costos | Administración autorizada |
| `GET` | `/api/v1/inventory/movements/` | Consultar kardex | Inventario / gerencia |
| `POST` | `/api/v1/inventory/movements/` | Registrar movimiento manual validado | Inventario autorizado |
| `GET` | `/api/v1/dashboard/summary/` | KPI del periodo | Gerencia autorizada |

**Reglas de API:** paginar listados, filtrar por fechas/estado/estación, definir formato consistente de errores, validar todo en servidor, versionar contrato, registrar auditoría, limitar peticiones de endpoints públicos y documentar la clave de idempotencia de creación/confirmación de pedidos.

## 10. Estructura del repositorio

Recomendación inicial: **monorepo** con frontend y backend separados, pero con una única documentación y control de versiones.

```text
restaurant-os/
├── README.md
├── .gitignore
├── .env.example                # Solo nombres y valores de ejemplo; sin secretos
├── frontend/
│   ├── src/
│   │   ├── app/                # Router, proveedores, configuración
│   │   ├── layouts/            # Customer, Production, Admin
│   │   ├── pages/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── catalog/
│   │   │   ├── cart/
│   │   │   ├── orders/
│   │   │   ├── kitchen/
│   │   │   ├── bar/
│   │   │   ├── inventory/
│   │   │   ├── recipes/
│   │   │   └── analytics/
│   │   ├── components/         # UI compartida
│   │   ├── lib/                # Cliente HTTP y utilidades
│   │   └── types/
│   └── package.json
├── backend/
│   ├── manage.py
│   ├── config/                 # settings, urls, wsgi/asgi
│   ├── apps/
│   │   ├── accounts/
│   │   ├── catalog/
│   │   ├── recipes/
│   │   ├── orders/
│   │   ├── production/
│   │   ├── inventory/
│   │   └── analytics/
│   ├── requirements.txt
│   └── .env.example
├── docs/
│   ├── adr/                    # Decisiones de arquitectura
│   ├── domain-model.md
│   ├── api-contract.md
│   └── roadmap.md
└── .github/
```

Separar **modelos**, **serializadores/API** y **servicios de dominio** en Django. Las acciones complejas (confirmar pedido, consumir stock, cancelar orden) no deben quedar dispersas entre señales, vistas y componentes de React; implementar servicios explícitos y probar sus transacciones.

## 11. Seguridad, permisos e integridad de datos

- **Roles sugeridos:** `ADMIN`, `MANAGER`, `KITCHEN`, `BAR`, `INVENTORY`; `CUSTOMER` puede ser anónimo con acceso restringido a su orden mediante código seguro.
- Proteger rutas React para UX, **y proteger cada endpoint DRF**: ocultar un botón no autoriza ni bloquea operaciones.
- El servidor determina precios, costo, estados y permisos. No aceptar `unit_cost`, `role`, `station` ni `total` arbitrarios de clientes públicos.
- Elegir una estrategia de autenticación para personal: sesiones/cookies seguras o tokens correctamente gestionados. Configurar CSRF si aplica, CORS por orígenes permitidos y HTTPS en producción.
- Guardar secretos únicamente en variables de entorno del backend/proveedor. Nunca poner credenciales de PostgreSQL o claves privadas en variables `VITE_*`.
- Usar transacciones de PostgreSQL (`transaction.atomic`) para confirmar pedidos, crear tickets y afectar stock cuando forman una sola operación de negocio.
- Aplicar restricciones y bloqueo/concurrencia donde corresponda para prevenir consumo duplicado y saldos incoherentes.
- Auditoría de cambios de receta, cancelaciones, ajustes y reversos de stock.
- Copias de seguridad y procedimiento probado de restauración antes de operar con datos reales.
- Si se integran pagos reales, utilizar proveedor especializado y verificar sus notificaciones de servidor; no considerar pagada una orden por una respuesta alterable del navegador.

## 12. Despliegue y observabilidad

```text
Navegador / kiosco
       │
       ├── frontend (Vercel, dominio web)
       └── API HTTPS (Railway o Render, subdominio api)
                              │
                              └── PostgreSQL (Supabase)
```

**Variables orientativas (no son valores reales):**

```dotenv
# frontend/.env.example
VITE_API_BASE_URL=http://localhost:8000/api/v1

# backend/.env.example
DJANGO_SECRET_KEY=replace-in-local-env
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@host:5432/database
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

En producción: `DEBUG=False`, hosts y orígenes explícitos, HTTPS, secretos administrados por la plataforma, migraciones controladas, static files del backend servidos apropiadamente, logs estructurados, alertas ante errores y monitoreo de tiempos de respuesta.

**Supabase:** crear proyecto y obtener su cadena PostgreSQL desde el panel; conectar **solo desde Django**, configurar SSL y elegir correctamente conexión directa o pooler según el entorno. Si la red/plataforma requiere una modalidad específica (por ejemplo, IPv4), revisar la documentación del proveedor al desplegar.

## 13. Plan de implementación por fases

### Fase 0 — Definición del dominio y decisiones obligatorias

- [ ] Confirmar una sede, moneda, impuestos y zona horaria.
- [ ] Definir qué significa «pedido confirmado» y en qué punto se simula o verifica el pago.
- [ ] Definir cuándo se registra el consumo teórico y cómo se revierte.
- [ ] Decidir si se permite stock negativo y cómo tratar faltantes.
- [ ] Elegir valorización del kardex y unidades base de medida.
- [ ] Definir roles, estaciones, preparación de ítems sin cocina y política de cancelaciones.
- [ ] Escribir 5–10 historias de usuario y sus criterios de aceptación.

**Entregable:** reglas de negocio documentadas y primer modelo entidad–relación.

### Fase 1 — Base del repositorio y backend

- [x] Crear monorepo, Git y documentación.
- [ ] Inicializar Django y DRF, configurar PostgreSQL y migraciones.
- [ ] Crear `accounts`, `catalog`, `recipes`, `orders`, `production` e `inventory` por iteraciones.
- [ ] Configurar admin, roles y permisos.
- [ ] Sembrar catálogo de ejemplo y probar endpoints con cliente HTTP.

**Entregable:** API para consultar menú, con modelos persistentes y autenticación interna.

### Fase 2 — Autoservicio vertical completo

- [x] Inicializar React + TypeScript + React Router.
- [ ] Crear layouts, menú, carrito, checkout y seguimiento.
- [x] Conectar API mediante TanStack Query (menú de demostración).
- [ ] Implementar creación de pedido idempotente, cálculo de precios en backend y confirmación/simulación de cobro.

**Entregable:** cliente crea una orden completa y recibe código de seguimiento.

### Fase 3 — Producción

- [ ] Crear tickets por estación en una única operación transaccional.
- [ ] Implementar KDS de cocina y barra con polling.
- [ ] Implementar transiciones de estado y cálculo agregado del pedido.
- [ ] Probar dos estaciones con tiempos de finalización diferentes.

**Entregable:** pedido visible automáticamente y marcado listo cuando todas las estaciones terminen.

### Fase 4 — Recetas, kardex y costos

- [ ] Versionar recetas e implementar conversiones de unidades.
- [ ] Registrar entradas y salidas; añadir mermas, ajustes y reversos.
- [ ] Conectar un evento de pedido confirmado con consumo teórico, según la política definida.
- [ ] Calcular costo histórico aplicable; comprobar saldo y valorización.
- [ ] Implementar pruebas de concurrencia, idempotencia y cancelación.

**Entregable:** cada consumo y ajuste puede rastrearse a su origen.

### Fase 5 — Dashboard, pruebas y despliegue

- [ ] Crear KPIs básicos con definiciones y rangos temporales consistentes.
- [ ] Añadir pruebas de permisos, flujos E2E y estados de error.
- [ ] Desplegar frontend, backend y base de datos con migraciones seguras.
- [ ] Verificar HTTPS, variables, logs, backups y restauración.

**Entregable:** demostración completa accesible en entorno de prueba.

### Evolución posterior

WebSockets, compras a proveedores, múltiples almacenes/locales, integración de pagos real, facturación, contabilidad y analítica más avanzada. Priorizar según datos de uso reales.

## 14. Primeros pasos: instalación y arranque

La base del proyecto ya está creada. Trabajar en este repositorio; no volver a
generar las carpetas con create-vite o django startproject.

### Paso 1. Herramientas

Entorno verificado: Git 2.48.1, Node 22.14.0, pnpm 11.20.0 y Python 3.13.6.
Dependencias fijadas en `frontend/pnpm-lock.yaml` y `backend/requirements.txt`.

### Paso 2. Repositorio

Monorepo inicializado con `frontend/`, `backend/` y `docs/`.
El `.gitignore` excluye `.env`, `.venv/`, `node_modules/`, bases SQLite y artefactos.

### Pasos 3 y 4. Arrancar frontend y backend

Desde la raíz, en **PowerShell**, preparar el backend:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python.exe backend/setup_local.py
backend/.venv/Scripts/python.exe backend/manage.py migrate
backend/.venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000
```

En otra terminal, desde la raíz:

```powershell
cd frontend
pnpm.cmd install --frozen-lockfile
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
pnpm.cmd run dev
```

Abrir **http://127.0.0.1:5173/menu**. Si las dependencias ya están instaladas,
solo es necesario ejecutar los comandos `runserver` y `pnpm.cmd run dev`.

### Paso 5. Supabase — pendiente

La instalación local usa SQLite exclusivamente para las migraciones predeterminadas
de Django. No hay modelos de negocio ni catálogo persistente todavía.
Configurar PostgreSQL de desarrollo mediante `DATABASE_URL` antes de implementarlos.
Seguir [la guía de conexión y arranque](docs/local-development.md).

### Paso 6. Primer hito funcional — implementado

```text
GET /api/v1/health/  → {"status": "ok"}
GET /api/v1/menu/    → carta de demostración desde Django
React /menu         → consulta la API, muestra y filtra productos
```

La carta declara `demo: true`, precios ilustrativos en PEN y no permite comprar.
Los datos son una lista temporal de Django, no registros PostgreSQL.
País confirmado: Perú. Moneda operativa, impuestos, canal y cobro siguen pendientes.
La zona horaria local propuesta es America/Lima.

Validación y pruebas: [docs/local-development.md](docs/local-development.md).
Estado y siguientes tareas: [docs/roadmap.md](docs/roadmap.md).
Decisiones técnicas: [ADR 0001](docs/adr/0001-local-foundation.md).

### Paso 7. Primer commit

Comprobar con `git status` que los secretos y archivos generados estén excluidos.
El primer commit contiene la base técnica y la documentación; no implica publicación
en GitHub ni despliegue.

## 15. Criterios de aceptación del MVP

- [ ] Un cliente puede completar un pedido sin intervención del personal.
- [ ] El servidor recalcula precios y rechaza entradas inválidas o manipuladas.
- [ ] Un doble envío de confirmación no crea dos pedidos ni consume inventario dos veces.
- [ ] Un pedido mixto genera tickets correctamente separados entre cocina y barra.
- [ ] Cada estación puede cambiar únicamente los estados de sus propios tickets.
- [ ] El pedido no aparece como listo hasta que todas sus preparaciones requeridas estén listas.
- [ ] Cambiar el precio, la receta o la estación de un producto no modifica órdenes históricas.
- [ ] Las entradas, salidas, mermas y ajustes de un insumo quedan reflejados en su kardex.
- [ ] Los movimientos de consumo pueden auditarse por pedido y reversarse correctamente.
- [ ] Un usuario de cocina no puede modificar inventario ni acceder a métricas reservadas a gerencia.
- [ ] El dashboard calcula sus indicadores desde datos persistidos y muestra el periodo consultado.
- [ ] El sistema se puede levantar localmente desde un clon nuevo siguiendo la documentación.

## 16. Decisiones pendientes y evolución

Estas decisiones **no deben inventarse durante la implementación**; registrarlas como ADR (*Architecture Decision Record*) cuando se resuelvan:

1. ¿Kiosco fijo, web accesible por QR o ambos? ¿Mesa, número de recojo o pedido para llevar?
2. ¿Cobro simulado, cobro al retirar o pasarela digital? ¿Qué evento libera producción?
3. ¿Pedidos anónimos o cuentas de clientes? ¿Cómo se protege la consulta del pedido?
4. ¿Política de stock negativo y criterio de disponibilidad de menú?
5. ¿Qué evento descuenta consumo teórico? ¿Cómo se tratan cortesías, cancelaciones y reprocesos?
6. ¿Cómo se asignan los productos de entrega inmediata y los modificadores a estaciones?
7. ¿Inventario por un almacén o por estaciones/almacenes separados?
8. ¿Cuál es el método de valorización, periodicidad del conteo y tratamiento de mermas?
9. ¿Qué impuestos, moneda y zona horaria corresponden al restaurante piloto?
10. ¿Qué datos requiere el dashboard y quién puede consultarlos?

**Orden recomendado para comenzar:** resolver decisiones 1–5 → dibujar entidades y estados → preparar repositorio y backend → exponer menú → conectar React → completar primer pedido de extremo a extremo. Priorizar el flujo vertical completo por encima de crear muchas pantallas sin lógica conectada.

## 17. Glosario

- **MVP:** versión mínima útil para comprobar de extremo a extremo la propuesta de valor.
- **API REST:** interfaz HTTP para consultar y modificar recursos con reglas definidas.
- **DRF:** Django REST Framework; herramientas para crear APIs sobre Django.
- **KDS:** Kitchen Display System; pantalla de recepción y seguimiento de preparaciones.
- **Kardex:** registro cronológico de entradas, salidas y saldos de inventario; puede incluir valoración monetaria.
- **ORM:** capa que permite consultar y modificar tablas mediante objetos del lenguaje.
- **Consumo teórico:** cantidad estándar que debería utilizarse según ventas y recetas.
- **Consumo real:** diferencia de existencias físicamente conciliadas, ajustada por entradas y otros movimientos.
- **Idempotencia:** repetir una misma solicitud no duplica su efecto de negocio.
- **Transacción atómica:** conjunto de cambios que se confirma completo o se revierte completo.
- **Polling:** consultar periódicamente una API para detectar información nueva.
- **WebSocket:** canal persistente bidireccional para transmitir eventos con baja latencia.

---

**Próximo entregable técnico:** completar el borrador [docs/domain-model.md](docs/domain-model.md) con las decisiones del piloto, conectar PostgreSQL e implementar el catálogo persistente. El dominio definitivo incluirá estados, unidades y reglas de inventario antes de crear pedidos y consumos.
# Laboratorio independiente de costeo

Primera etapa en `/costing`: insumos, rendimiento, formulación y cálculos guardados.
[Alcance, activación y fórmulas](docs/costing.md). No modifica menú, pedidos ni inventario.

