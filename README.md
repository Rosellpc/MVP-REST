# RestaurantOS — Autoservicio y gestión de restaurante

Plataforma para conectar menú → pedido → Cocina/Barra → stock → indicadores,
con un laboratorio de costeo y recetas versionadas.

**Estado actual:** MVP integrado de demostración. El backend usa PostgreSQL
(Supabase en el entorno de desarrollo configurado); SQLite se usa únicamente
en pruebas aisladas. El pago es simulado y los importes del dashboard no son
cobros reales. La operación comercial con cobros sigue pendiente.

## Arquitectura implementada

- **Frontend:** React, TypeScript, React Router y Vite. Diseño CSS charcoal/cristal;
  plugin Tailwind instalado. Caché propia de menú/detalles, carrito con Context y
  sessionStorage. No se utiliza TanStack Query ni Zustand.
- **Backend:** Django y DRF; servicios explícitos, Decimal para importes,
  transacciones, restricciones y bloqueos PostgreSQL.
- **Autenticación:** sesiones Django, CSRF y roles. Sin registro público de empleados.
- **Actualización:** polling controlado que se pausa con la pestaña oculta.
  Fotos y detalles conservan su caché mientras la disponibilidad se actualiza.
- React no se conecta directamente a Supabase ni contiene sus credenciales.

```text
frontend/src/
  router/       rutas y protección
  layouts/      MainLayout y StaffLayout
  pages/        menú, detalle, carrito, checkout, seguimiento y acceso
  features/     auth, catalog, cart, orders, production, stock, costing, dashboard
  components/   interfaz compartida
backend/
  core/         configuración y rutas
  accounts/     usuarios, sesiones y roles
  catalog/      productos, categorías y estaciones
  orders/       confirmación idempotente y precios históricos
  production/   tickets, transiciones y cancelaciones
  stock/        turnos, saldos, movimientos y conciliación
  costing/      insumos, recetas e inventarios de referencia
  analytics/    consultas del dashboard, sin modelos propios
```

Dependencias fijadas en `backend/requirements.txt` y `frontend/pnpm-lock.yaml`.

## Módulos y rutas

| Ruta | Funcionalidad | Acceso |
|---|---|---|
| `/`, `/menu` | Categorías, productos y disponibilidad | Público |
| `/menu/:productId` | Detalles y añadir al carrito | Público |
| `/cart`, `/checkout` | Resumen validado y pago simulado | Público |
| `/orders/:publicCode` | Seguimiento y despedida al estar listo | Código aleatorio |
| `/login`, `/staff` | Acceso y áreas autorizadas | Personal |
| `/kitchen`, `/bar` | Tableros de producción | Permiso de estación |
| `/staff/admin` | Historial y cancelaciones | Administración |
| `/stock` | Turnos, ingresos, mermas, ajustes y cierres | ADMIN/CHEF gestionan; KITCHEN/BAR consultan |
| `/costing` | Resumen, Insumos, Recetario e Inventario | costing.use_costing |
| `/dashboard` | Indicadores y acceso a módulos | accounts.access_staff |
| Backend `/admin/` | Usuarios y catálogo | is_staff y permisos |

NotFoundPage queda fuera de los layouts compartidos. Stock y dashboard utilizan
StaffLayout; Costeo mantiene su navegación propia con enlaces entre módulos.

## Reglas operativas vigentes

### Compra y producción

1. El servidor valida productos, cantidades, precios y disponibilidad. La vista
   previa consulta stock sin reservar; la confirmación lo verifica bajo bloqueo.
2. Confirmar checkout crea pedido, líneas y tickets en una transacción. La clave
   de idempotencia evita duplicados al reintentar.
3. OrderItem conserva nombre, precio y estación históricos. DELIVERY aún no admite
   pedidos y no se ofrece en la carta pública.
4. Tickets: PENDING → IN_PROGRESS → READY. Finalizado archiva la tarjeta lista.
   El pedido está listo cuando terminan todas sus estaciones. No hay todavía
   confirmación física independiente de entrega.
5. Cocina/Barra solicitan cancelar desde pendiente o preparación, pausando el pedido.
   Solo un superusuario aprueba o rechaza; ADMIN no implica superusuario.
   La cancelación vigente afecta al pedido completo. Los estados parciales antiguos
   permanecen como histórico, sin nuevas cancelaciones parciales.

### Stock y conteos

- La primera apertura activa el control con cantidades registradas por el responsable.
  El stock representa unidades de venta, no insumos de receta.
- El checkout descuenta una vez; marcar listo/finalizado no vuelve a descontar.
  No se permite stock negativo: un faltante revierte toda la compra.
- Cancelación aprobada: sin preparar devuelve unidades; preparación iniciada
  reclasifica como merma sin reposición física.
- Cada movimiento tiene responsable, fecha y motivo. El cierre compara teórico y
  físico, justifica diferencias y rechaza conteos desactualizados. Un turno cerrado
  pausa las ventas hasta abrir el siguiente.
- Los sobrantes requieren revisar su aptitud. Caducidad y descarte son mermas
  explícitas; no hay vencimiento automático por lotes.
- Los conteos Excel de Costeo pueden editarse/archivarse con auditoría y no se
  convierten automáticamente en stock operativo.

### Recetas e indicadores

- Las recetas tienen versiones y fotografías de precios/rendimientos. Cada nueva
  versión recalcula con insumos activos y conserva la procedencia registrada.
- Fichas incompletas tienen costos pendientes, no cero. Las exportaciones para
  recalcular excluyen borradores y se dividen en lotes de 100; un respaldo separado
  conserva todas las fichas vigentes para consulta.
- Dashboard muestra importes demo, pedidos, ticket promedio, tendencias, tiempos,
  stock y cobertura de costeo. Moneda PEN y fechas en America/Lima.
- Falta conservar una receta y costo histórico aplicable en cada venta para calcular
  utilidad real. No se vinculan recetas y productos por similitud de nombres.

## Arranque local

Entorno utilizado: Python 3.13, Node 22 y pnpm; PostgreSQL accesible desde Django.
No crear nuevamente el proyecto con startproject/create-vite.

Desde la raíz, en PowerShell:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
if (-not (Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
```

Completar localmente `backend/.env`. La conexión utiliza DB_NAME, DB_USER,
DB_PASSWORD, DB_HOST y DB_PORT, no DATABASE_URL. No sobrescribir credenciales
existentes ni publicarlas. La conexión PostgreSQL exige SSL.

```powershell
backend/.venv/Scripts/python.exe backend/manage.py migrate
backend/.venv/Scripts/python.exe backend/manage.py setup_roles
backend/.venv/Scripts/python.exe backend/manage.py createsuperuser
backend/.venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000
```

Crear superusuario solo en una instalación que lo necesite. setup_roles configura
ADMIN, CHEF, KITCHEN y BAR sin asignar grupos a usuarios. Las migraciones actúan
sobre la base configurada. La revisión del 12/10/2026 no requiere nuevas migraciones.

En otra terminal:

```powershell
cd frontend
pnpm.cmd install --frozen-lockfile
pnpm.cmd dev
```

Abrir `http://127.0.0.1:5173/menu`. Vite redirige `/api` a Django:8000. No se necesita
una URL ni credenciales de Supabase en React. En Git Bash, desde backend, activar
Python con `source .venv/Scripts/activate`.

## Verificación

```powershell
backend/.venv/Scripts/python.exe backend/manage.py test --settings=core.test_settings
backend/.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run --settings=core.test_settings
```

Desde frontend: `pnpm.cmd test`, `pnpm.cmd lint`, `pnpm.cmd build`.
Las pruebas normales no leen .env y usan SQLite en memoria. Las pruebas concurrentes
requieren PostgreSQL aislado; SQLite las omite porque no soporta esos bloqueos.
No ejecutar pruebas destructivas contra los datos del restaurante.

## Documentación

- [API de menú](backend/catalog/API.md) y [fichas de producto](docs/menu-product-details.md).
- [Checkout](docs/checkout-demo.md) y [acceso y roles](docs/production-flow.md).
- [Producción y cancelaciones](docs/production-api.md).
- [Stock y cierres](docs/stock.md), [Costeo](docs/costing.md).
- [Dashboard y fórmulas](docs/dashboard.md).
- [Revisión del proyecto — 12/10/2026](docs/project-review-2026-10-12.md).

## Próximas etapas

1. Validar fichas alimentarias, ingredientes cuantificados, precios y enlaces
   producto–receta. Renombrar un plato no valida sus fotos, ingredientes o alérgenos.
2. Registrar costo/versión en cada venta y definir consumo de insumos, conversiones
   y valorización. Stock de platos terminados no sustituye ese kardex.
3. Integrar cobro real, conciliación, reembolsos y entrega física antes de operar
   comercialmente. SIMULATED no significa PAID.
4. Preparar despliegue: HTTPS, cookies/orígenes, estáticos, backups con restauración
   probada, logs y monitoreo. Propuesta: Vercel + Railway/Render + PostgreSQL/Supabase;
   no implica que ese despliegue ya esté realizado.
5. Incorporar pruebas E2E de navegador, dispositivos reales, carga y CI. Después,
   evaluar WebSockets, proveedores, compras, múltiples almacenes/locales y facturación.

La visión sigue siendo una fuente de datos que conecte autoservicio, producción,
trazabilidad, costos e indicadores. El circuito demo ya está integrado; la
rentabilidad histórica y la operación comercial son las próximas integraciones.
