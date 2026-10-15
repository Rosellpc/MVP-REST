# Demo: Vercel + Render + Supabase

Arquitectura: Vercel → proxy `/api/*` → Django en Render → PostgreSQL en Supabase.
El navegador usa el mismo origen para la API y la interfaz. No necesita secretos
VITE, CORS abierto ni cookies entre sitios. Esta guía prepara una demo sin cobros.

## 1. Datos

Usa preferentemente un proyecto Supabase separado para la demo. Una base vacía
necesita importar catálogo, recetas y stock; las migraciones solo crean tablas.
Si usas la base actual, la aplicación local y la pública modificarán los mismos
datos. Haz un respaldo antes de desplegar. No expongas stock de trabajo a una demo.
Rota los secretos que fueron compartidos en capturas. No publiques `.env`.
Las imágenes de `frontend/public` se despliegan con Vercel; revisa que las URLs de
productos no apunten a localhost o a Windows. Los Excel originales no se publican.

## 2. Render

Sube los cambios a tu repositorio y crea un Blueprint desde `render.yaml`.
La plantilla utiliza **Free**. No crea otra base de datos. Usa Gunicorn y WhiteNoise;
ejecuta migraciones y `setup_roles` al final del build, porque Free no tiene
pre-deploy. Este último sincroniza permisos de grupos existentes. Las migraciones
modifican la base antes de activar la versión nueva: utiliza cambios compatibles
con la versión anterior y respalda la base; un rollback de código no revierte datos.

Render Free suspende el servicio tras 15 minutos sin tráfico; reactivarlo puede
tardar aproximadamente un minuto. La primera consulta del frontend puede vencer:
espera a que `/api/health/` responda y reintenta. Es adecuado para mostrar una demo,
no para operar el restaurante de forma continua. No dispone de consola Shell/SSH.
Los datos persistentes permanecen en Supabase, no en el disco temporal de Render.

Completa en Render:

| Variable | Valor |
| --- | --- |
| DJANGO_ALLOWED_HOSTS | Host real de Render, sin https:// |
| CSRF_TRUSTED_ORIGINS | URL HTTPS exacta de Vercel; varios orígenes separados por coma |
| DB_HOST, DB_USER, DB_PASSWORD | Datos del Session pooler de Supabase para la demo |
| DB_NAME, DB_PORT | postgres, 5432 (comprueba los datos de tu proyecto) |

Conserva el usuario completo del pooler. Usa la contraseña literal, no codificada
como URL. SSL ya está requerido. El Blueprint genera DJANGO_SECRET_KEY y establece
DJANGO_SETTINGS_MODULE=core.production_settings. Necesita una clave de al menos
50 caracteres; si fuera necesario genera una con `secrets.token_urlsafe(64)` en tu
terminal privada. La clave nueva invalida las sesiones anteriores.

Reserva el nombre del proyecto de Vercel para conocer su URL y autorizarla en CSRF.
Añade el dominio definitivo cuando exista. No uses comodines para previews.

Comprueba `https://TU-BACKEND.onrender.com/api/health/`: debe devolver
`{"status":"ok"}`. Si la base es nueva, configura localmente la conexión a ESA
base y ejecuta `python manage.py createsuperuser` desde backend con el entorno
virtual activo, después del primer build. Free no tiene consola remota. Si usas
la base actual, los usuarios existentes se conservan. No publiques contraseñas.
Django Admin se encuentra
en `https://TU-BACKEND.onrender.com/admin/`, con sus estáticos servidos por WhiteNoise.

## 3. Vercel

Desde `frontend`, configura la URL real antes de publicar:

```bash
node scripts/configure-deploy.mjs https://TU-BACKEND.onrender.com
pnpm run build
```

Guarda `frontend/vercel.json` actualizado en Git. Mientras contenga el marcador
`.invalid`, el build en Vercel fallará explícitamente para evitar una demo rota.
La dirección del backend no es un secreto.

Importa el repositorio y configura:

| Opción | Valor |
| --- | --- |
| Root Directory | frontend |
| Framework | Vite |
| Node | 22.x, versión 22.12 o superior |
| Install Command | pnpm install --frozen-lockfile |
| Build Command | pnpm run build |
| Output Directory | dist |

El proxy de API precede al fallback de React Router. Los errores de API no deben
convertirse en HTML. Las respuestas de API se marcan privadas y sin caché.
No pongas claves Django, de base de datos o de Culqi en Vercel.

## 4. Verificación pública

1. `/api/health/` desde Vercel devuelve JSON.
2. Menú e imágenes cargan; abrir `/menu/ID` directamente y recargar funciona.
3. Login establece la cookie y `/api/v1/auth/me/` reconoce al usuario.
4. Verifica una acción autenticada para comprobar CSRF, no solo GET.
5. Revisa permisos de Cocina, Barra y Administración con cuentas distintas.
6. Con turno abierto y stock de prueba, confirma un pedido simulado y verifica
   descuento, tickets, seguimiento y finalización. Reintentar no debe duplicarlo.
7. Verifica Costeo, Dashboard, logout y móvil.

403 CSRF: revisa el origen exacto en Render. 502: revisa salud del backend.
404 en una ruta React al recargar: revisa Root Directory y rewrites.
No desactives CSRF ni uses ALLOWED_HOSTS=* para ocultar errores.

## 5. Operación y pagos

Los flujos actuales no envían correos. Antes de habilitar notificaciones o recuperación
por email, configura SMTP_HOST, SMTP_PORT, SMTP_USER y SMTP_PASSWORD en Render y
verifica la entrega. No se considera configurado el servicio de correo por defecto.
HSTS está habilitado por una hora sin incluir subdominios ni precarga; el chequeo
de despliegue avisa de esas dos opciones, que requieren revisar el dominio definitivo.

`production_settings` fuerza Culqi desactivado. Los flags de demo permiten el
flujo simulado; no se presenta como un despliegue de cobros reales.
Antes de activar pagos: validar proveedor, retirar explícitamente este bloqueo,
configurar webhook HTTPS y programar cada minuto `python manage.py reconcile_payments`
sin ejecuciones superpuestas. También libera reservas vencidas sin cargo.
No se instala cron en esta demo. Si compartes datos con intentos Culqi antiguos,
concílialos primero: no borres pagos ni liberes reservas de resultado incierto.
Consulta `docs/payments.md`.

Los límites actuales usan caché por proceso; Gunicorn usa un worker. Antes de
abrir acciones a tráfico no controlado, prepara caché compartida y controles de
abuso. Usa cuentas con permisos mínimos y datos descartables.

## Validación local

```bash
cd backend
python manage.py test --settings=core.test_settings
cd ../frontend
pnpm run build
pnpm run lint
pnpm test
```

Fuentes: [Render Django](https://render.com/docs/deploy-django),
[Vercel Vite](https://vercel.com/docs/frameworks/frontend/vite),
[Rewrites](https://vercel.com/docs/routing/rewrites).
