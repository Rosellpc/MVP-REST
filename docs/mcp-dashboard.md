# Consultas privadas de RestaurantOS desde ChatGPT

El MCP conserva las tres herramientas públicas y añade:

- `consultar_dashboard(start?, end?)`: los mismos datos y permisos de `/dashboard`: métricas, comparación anterior, tendencia, productos principales, canales, cocina/barra, stock, alertas y costeo.
- `resumen_ventas(start?, end?)`: importe, pedidos válidos, ticket promedio, cancelaciones y unidades.

Ambas son de solo lectura. Las fechas son inclusivas, en `America/Lima`, con un máximo de 366 días y sin fechas futuras. Sin fechas se consultan los últimos siete días. Los importes actuales corresponden a pedidos de demostración con pagos simulados; no son cobros reales. Los indicadores operativos actuales de stock, cocina y costeo mantienen la interpretación del dashboard y no son históricos del intervalo.

## Publicar

1. Publica estos cambios en GitHub y despliega primero el backend Django, después el servicio MCP. El frontend no requiere cambios.
2. El backend necesita `django-oauth-toolkit==3.4.1`. El build de `render.yaml` instala las dependencias y ejecuta `migrate`; si configuraste el servicio manualmente, conserva también `python manage.py migrate --noinput` en su build. Esto crea las tablas OAuth en la base existente, sin cambiar los pedidos.
3. Comprueba las siguientes variables en los dos servicios. Estos valores son los predeterminados del código y no contienen secretos:

| Servicio | Variable | Valor |
| --- | --- | --- |
| Django | `MCP_RESOURCE_URL` | `https://restos-mcp.onrender.com/mcp` |
| Django | `MCP_AUTH_ISSUER` | `https://mvp-rest.onrender.com` |
| MCP | `MCP_RESOURCE_URL` | `https://restos-mcp.onrender.com/mcp` |
| MCP | `MCP_AUTH_ISSUER` | `https://mvp-rest.onrender.com` |
| MCP | `API_BASE_URL` | `https://mvp-rest.onrender.com` |

Si cambiaste el dominio del MCP, actualiza `MCP_RESOURCE_URL` en ambos servicios: debe ser exactamente la misma URL HTTPS terminada en `/mcp`. `API_BASE_URL` es el origen de Django, sin `/api`. Mantén `DJANGO_ALLOWED_HOSTS`, HTTPS y la configuración de CSRF de producción existente.

## Conectar ChatGPT

1. En ChatGPT, actualiza o vuelve a crear tu conexión MCP con URL `https://restos-mcp.onrender.com/mcp` y autenticación **OAuth**.
2. Se publican los metadatos de autorización en `https://mvp-rest.onrender.com/.well-known/oauth-authorization-server` y del recurso en `https://restos-mcp.onrender.com/.well-known/oauth-protected-resource`.
3. ChatGPT puede registrarse mediante su documento de cliente (CIMD). El backend permite únicamente documentos alojados en `chatgpt.com`. No necesitas crear una contraseña compartida para el MCP ni cambiar el inicio de sesión del frontend.

   El adaptador `accounts/mcp_oauth_client.py` selecciona el método público `none` únicamente cuando el documento de ChatGPT lo anuncia explícitamente en `token_endpoint_auth_methods_supported`. Esto evita que la preferencia antigua `private_key_jwt` impida el registro en Django OAuth Toolkit. PKCE sigue siendo obligatorio y se conservan las comprobaciones de seguridad de la descarga del documento.
4. Abre la conexión y accede con tu usuario de RestaurantOS en la pantalla de Django. Autoriza los permisos de lectura solicitados. La cuenta debe tener `accounts.access_staff` (por ejemplo, pertenecer al grupo ADMIN); iniciar sesión en otra pestaña de Vercel no autoriza automáticamente a ChatGPT.
5. Si tu interfaz exige un cliente predefinido, crea una Application en Django Admin → Django OAuth Toolkit → Applications: nombre `ChatGPT RestaurantOS`, tipo `Confidential`, grant `Authorization code`, y la **URL de redirección exacta** que muestra ChatGPT. Conserva la pantalla de consentimiento y copia el Client ID y el Client secret a la configuración OAuth de ChatGPT. No compartas esos valores en el chat ni en Git.
6. Actualiza las herramientas de la conexión: deben aparecer cinco.

Prompts:

> Usa consultar_dashboard para explicar los indicadores del 1 al 31 de octubre de 2026. Señala qué datos corresponden al período y cuáles reflejan la operación actual.

> Usa resumen_ventas para el mes pasado. Presenta importe, pedidos válidos, cancelados y ticket promedio, indicando que son pagos simulados.

## Autorización y revocación

Django valida el token opaco en su propia base en cada consulta: caducidad, recurso exacto del MCP, usuario activo, alcance OAuth y permiso de personal. Las rutas `/api/v1/mcp/dashboard/` y `/api/v1/mcp/sales/summary/` aceptan exclusivamente Bearer OAuth; no aceptan cookies del navegador. Un token de otro recurso no sirve. El MCP reenvía el token solo a esas dos rutas fijas y no permite elegir URLs o ejecutar SQL.

Los tokens duran una hora; la renovación rota los refresh tokens. Para retirar acceso inmediatamente, revoca el token en Django Admin, retira el permiso de personal o desactiva la cuenta. Para una renovación limpia, desconecta y vuelve a conectar la aplicación en ChatGPT.

401 indica conexión ausente, vencida o con recurso incorrecto. 403 indica falta de alcance o de permiso del usuario. 400 indica fechas inválidas. Si Render Free estuvo inactivo, espera a que despierten ambos servicios y reintenta.

## Pruebas locales aisladas

Desde `backend`, con las dependencias instaladas:

```bash
python manage.py test analytics --settings=core.test_settings
```

Estas pruebas usan SQLite en memoria, sin cargar `.env` ni conectar con Supabase. Cubren autorización con código y PKCE, caducidad, audiencia, revocación, permisos, coincidencia con el dashboard y respuestas sin datos de clientes.

Referencias: [autenticación MCP en OpenAI](https://developers.openai.com/plugins/build/auth), [Django OAuth Toolkit](https://django-oauth-toolkit.readthedocs.io/en/latest/).
