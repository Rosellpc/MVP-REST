# Acceso del personal y reglas de producción

Implementado: sesiones, CSRF, grupos, permisos, pantallas de acceso y API de tickets
de demostración con liberación manual. Las pantallas aún no muestran tickets.
Los pedidos continúan siendo de demostración; SIMULATED no significa PAID.

## Reglas de la API de producción

- Administración libera explícitamente pedidos de prueba en un entorno habilitado.
- Cocina y barra solo podrán operar su estación. Administración podrá supervisar ambas.
- Tickets: PENDING → IN_PROGRESS → READY. Cancelación administrativa con motivo y auditoría.
- Un pedido estará listo cuando todas sus preparaciones requeridas estén listas.
- DELIVERY bloquea la liberación completa con 409 hasta definir quién confirma su entrega.
- Cancelación permitida solo desde PENDING o IN_PROGRESS. READY y CANCELLED son terminales.
- Una cancelación parcial produce PARTIALLY_CANCELLED; si todos se cancelan, CANCELLED.
- Cobro real, cancelaciones parciales y evento de liberación real siguen pendientes de validación.

Estas propuestas no activan operaciones reales ni descuento de inventario.

## Roles actuales

| Grupo | Permisos |
| --- | --- |
| ADMIN | Acceso administrativo, cocina, barra y gestión del catálogo |
| KITCHEN | Acceso a cocina |
| BAR | Acceso a barra |

Los permisos `accounts.access_staff`, `accounts.access_kitchen` y `accounts.access_bar`
habilitan áreas. Los permisos de producción separados controlan consulta, avance,
liberación y cancelación. ADMIN no permite gestionar usuarios ni elevar privilegios.
`is_staff` habilita Django Admin, no convierte a una persona en administrador funcional.

## Activación local

En backend, con el entorno virtual activado:

```sh
python manage.py migrate
python manage.py setup_roles
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

No se ejecutaron migraciones sobre la base remota durante la implementación.
Usa el superusuario en http://127.0.0.1:8000/admin/ para crear cuentas individuales
y asignarles un grupo. No marques superusuario ni staff para cocina/barra.
Para un responsable del catálogo, asigna ADMIN y staff; la gestión de cuentas queda
en manos del superusuario o de un responsable expresamente autorizado.

`setup_roles` es idempotente y reemplaza los permisos de esos tres grupos por la
matriz declarada; no crea contraseñas ni asigna grupos a usuarios existentes.

En frontend: `pnpm dev`. Abre http://127.0.0.1:5173/login.
El acceso termina en /staff, donde aparecen las áreas autorizadas.
/staff/admin, /kitchen y /bar son pantallas preparatorias, no dashboards operativos.
El menú sigue siendo público y NotFoundPage queda fuera de los layouts.

## Contrato y seguridad

- GET /api/v1/auth/csrf/: devuelve csrfToken y prepara la cookie.
- POST /api/v1/auth/login/: username/password, con X-CSRFToken; devuelve usuario y token rotado.
- GET /api/v1/auth/me/: usuario, roles y permisos. Sin sesión responde 403 con SessionAuthentication.
- POST /api/v1/auth/logout/: protegido con CSRF; invalida la sesión.
- GET /api/v1/{staff,kitchen,bar}/access/: verificación de permiso en servidor.

Las respuestas no se cachean. El frontend conserva el usuario en memoria y consulta
la sesión al arrancar y al recuperar foco. Un fallo de red se muestra como error,
no como cierre de sesión. El backend aplica los permisos en cada petición.
No se almacenan contraseñas ni tokens de sesión en localStorage.

El proxy Vite usa /api. Usa 127.0.0.1 consistentemente. En desarrollo DEBUG habilita
el origen http://127.0.0.1:5173 para CSRF. Se puede configurar CSRF_TRUSTED_ORIGINS
como lista separada por comas en el entorno. No utilices comodines.
En producción DEBUG=False activa cookies Secure: requiere HTTPS. Esta configuración
asume API bajo el mismo origen mediante proxy. Un despliegue entre orígenes requiere
configurar CORS, cookies y credenciales de forma explícita antes de publicar.

Login limita 10 intentos/minuto por IP mediante caché Django. Para varios procesos,
configura caché compartida y limitación en el proxy; la caché local no es un límite
global ni reemplaza protección operativa contra intentos automatizados.

## Validación

```sh
python manage.py test accounts catalog orders --settings=core.test_settings
python manage.py makemigrations --check --dry-run --settings=core.test_settings
```

En frontend: `pnpm build`, `pnpm lint`, `pnpm test`.
Prueba manual: login cocina, recarga /kitchen, intenta /bar, cierra sesión y vuelve
a /kitchen. Repite con barra y ADMIN. Verifica fallos de conexión y contraseñas inválidas.
