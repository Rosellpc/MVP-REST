# Validación del sistema de diseño

Verificación realizada el 25 de septiembre de 2026.

- Compilación TypeScript + Vite: aprobada.
- Oxlint: aprobado, sin advertencias.
- Playwright: **34 pruebas aprobadas** en Chromium escritorio y móvil emulado.
- Axe: sin infracciones detectadas en menú, galería, cocina, inventario,
  dashboard y modal de producto, para los tags WCAG A/AA configurados.
- Foco del modal, Tab/Shift+Tab, Escape y retorno al botón de origen.
- Selección de prueba, cantidades, notas, resumen y confirmación sin transacción real.
- Tabs por teclado, separación de estaciones y transiciones visuales.
- Tablas con búsqueda, filtro, orden y paginación.
- Preferencia persistente de transparencia y reducción de movimiento.
- Reflujo de menú e inventario a 320 px.
- Fallback de fotografías ante error de red.
- Carga manual en navegador: cuatro URLs externas respondieron HTTP 200.
- Revisión visual del menú con fotos y del KDS.

No hay fotografías descargadas en frontend/public. Las capturas de prueba son
artefactos locales ignorados por Git, no assets de la aplicación.

Pendiente antes del piloto: revisión con lectores de pantalla, zoom 200–400%,
Safari/iOS real, Android real, alto contraste y rendimiento en dispositivos de cocina.
Las comprobaciones realizadas no certifican conformidad WCAG 2.2 AA completa.
