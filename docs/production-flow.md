# Acceso del personal y reglas de producción

Las pantallas de Cocina, Barra y Administración son operativas para pedidos demo.
El checkout envía tickets automáticamente cuando producción está habilitada.
SIMULATED no significa PAID; el stock operativo sí se descuenta con control activo.

## Roles

| Grupo | Acceso funcional |
| --- | --- |
| ADMIN | Administración, dashboard, Cocina, Barra, catálogo, costeo y gestión de stock |
| CHEF | Cocina y gestión de stock |
| KITCHEN | Cocina y consulta de stock |
| BAR | Barra y consulta de stock |

Solo un superusuario puede aprobar o rechazar cancelaciones. El grupo ADMIN no
concede esa condición ni permite elevar privilegios. `is_staff` habilita Django
Admin, pero no sustituye los permisos funcionales. Los permisos se verifican en
cada petición; ocultar un botón no constituye autorización.

## Activación en una instalación nueva

Desde backend, con el entorno virtual activo:

```sh
python manage.py migrate
python manage.py setup_roles
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

El superusuario crea cuentas individuales y asigna grupos desde Django Admin.
No marcar superusuario para Cocina o Barra. `setup_roles` es idempotente y reemplaza
los permisos de los cuatro grupos por la matriz del código; no crea contraseñas
ni asigna grupos a usuarios existentes. El login del frontend está en `/login`.

## Sesión y seguridad

- GET `/api/v1/auth/csrf/`: prepara cookie y devuelve csrfToken.
- POST `/api/v1/auth/login/`: username/password y X-CSRFToken; rota el token.
- GET `/api/v1/auth/me/`: usuario, roles y permisos; sin sesión responde 403.
- POST `/api/v1/auth/logout/`: protegido por CSRF, invalida sesión.
- GET `/api/v1/{staff,kitchen,bar}/access/`: comprueba acceso en servidor.

El frontend mantiene la sesión en memoria sin bloquear cada navegación con una
pantalla de carga. El servidor sigue verificándola en cada petición. No se guardan
contraseñas ni tokens de sesión en localStorage. Los errores de red se distinguen
de la pérdida de autorización.

Vite sirve `/api` mediante proxy. Usar 127.0.0.1 consistentemente; configurar
CSRF_TRUSTED_ORIGINS explícitamente. DEBUG=False activa cookies Secure y requiere
HTTPS. El diseño asume frontend y API bajo el mismo origen; un despliegue distinto
necesita configurar cookies, credenciales y CORS antes de publicarse.

El login limita intentos mediante caché Django. Para varios procesos se requiere
caché compartida y controles del proxy; la caché local no es un límite global.

Ver [contrato de producción](production-api.md), [stock](stock.md) y
[configuración y pruebas](../README.md).
