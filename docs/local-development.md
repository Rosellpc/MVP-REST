# Arranque local — Windows PowerShell

Este hito comprueba React → Django con una carta de demostración. No crea pedidos
ni registra cobros o movimientos de inventario. País del piloto confirmado: Perú.
PEN y America/Lima se usan como valores locales provisionales; confirmar la moneda operativa.

## Herramientas

Entorno verificado: Git 2.48.1, Node 22.14.0, pnpm 11.20.0 y Python 3.13.6.
Dependencias exactas: `frontend/pnpm-lock.yaml` y `backend/requirements.txt`.
Se utiliza Django 5.2 LTS. Los comandos siguientes se ejecutan desde la raíz,
en dos terminales distintas. No es necesario activar el entorno virtual.

## Terminal 1: backend

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python.exe backend/setup_local.py
backend/.venv/Scripts/python.exe backend/manage.py migrate
backend/.venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000
```

`setup_local.py` crea `backend/.env` con una clave local aleatoria y no sobrescribe
un archivo existente. SQLite se usa únicamente para comprobar la instalación,
sesiones y administración predeterminada de Django. No hay modelos de negocio aún.

## Terminal 2: frontend

```powershell
cd frontend
pnpm.cmd install --frozen-lockfile
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
pnpm.cmd run dev
```

Abrir **http://127.0.0.1:5173/menu**. También se permite el origen localhost:5173.
El puerto es fijo: si está ocupado, Vite informa del conflicto en vez de cambiarlo
silenciosamente y romper CORS. Detener cada servidor con Ctrl+C.

En Git Bash se puede usar `pnpm` y `backend/.venv/Scripts/python.exe`.
Las instrucciones anteriores usan `pnpm.cmd` para evitar bloqueos de ejecución de scripts PowerShell.

## Qué comprobar

- http://127.0.0.1:8000/api/v1/health/ devuelve `{"status":"ok"}`.
- http://127.0.0.1:8000/api/v1/menu/ devuelve los cuatro productos de ejemplo.
- React muestra la carta, permite filtrar categorías y buscar por nombre o descripción.
- Si Django no está disponible, la interfaz muestra un error y permite reintentar.
- La demostración informa que sus precios son ilustrativos y no habilita pedidos.

El endpoint health verifica que el proceso atiende HTTP; no verifica PostgreSQL.
Los productos provienen de `backend/catalog/demo.py`, no de tablas persistidas.

## Comprobaciones automatizadas

Desde la raíz:

```powershell
backend/.venv/Scripts/python.exe backend/manage.py check
backend/.venv/Scripts/python.exe backend/manage.py test catalog
backend/.venv/Scripts/python.exe -m pip check
cd frontend
pnpm.cmd run build
pnpm.cmd run lint
pnpm.cmd exec playwright install chromium
pnpm.cmd run test:e2e
```

Playwright inicia sus propios servidores en 8001 y 5174 y los detiene al terminar.
Comprueba escritorio y móvil: carga real desde Django, filtros, búsqueda, recuperación
tras error, carga, carta vacía y navegación. Genera capturas en `.artifacts/playwright/`.
Requiere que la configuración local del backend se haya generado previamente.

## Próximo paso: PostgreSQL en Supabase

1. Crear o elegir un proyecto de desarrollo en Supabase.
2. Copiar su URI PostgreSQL a `DATABASE_URL` dentro de `backend/.env`.
   Mantener la contraseña fuera de Git y de variables `VITE_*`. Usar
   `sslmode=require` y elegir conexión directa o pooler según el entorno.
3. Detener el backend y ejecutar `backend/.venv/Scripts/python.exe backend/manage.py migrate`.
4. Ejecutar `backend/.venv/Scripts/python.exe backend/manage.py showmigrations`.
5. Crear el acceso del administrador de manera interactiva:
   `backend/.venv/Scripts/python.exe backend/manage.py createsuperuser`.
6. Volver a arrancar Django y abrir http://127.0.0.1:8000/admin/.

No se ha creado un proyecto remoto, un superusuario ni una conexión Supabase.
Los roles operativos y el catálogo persistente se implementarán después de cerrar
el modelo de dominio; las cuentas actuales son las predeterminadas de Django.
Cambiar DATABASE_URL no migra automáticamente datos de SQLite a PostgreSQL.

## Referencias técnicas

- [Instalación y requisitos de Vite](https://vite.dev/guide/).
- [Versiones y soporte de Django](https://www.djangoproject.com/download/).
- [Permisos de Django REST Framework](https://www.django-rest-framework.org/api-guide/permissions/).

La configuración actual está destinada a desarrollo local. El despliegue, HTTPS,
static files, backups y validación de seguridad de producción pertenecen a la fase 5.
