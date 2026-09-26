# Avance del MVP

## Completado — instalación y primer flujo de lectura

- Repositorio Git local y estructura frontend/backend/docs.
- Exclusión de secretos, entornos, dependencias y archivos generados.
- Dependencias instaladas y fijadas mediante requirements.txt y pnpm-lock.yaml.
- Django, DRF, CORS y configuración por entorno.
- Migraciones predeterminadas de Django aplicadas en SQLite local.
- GET /api/v1/health/ y GET /api/v1/menu/ con datos de demostración.
- React /menu conectado a Django, búsqueda, filtros y estados de interfaz.
- Pruebas de API y navegación en escritorio y móvil.
- Guía de arranque y borrador de dominio.

## Siguiente hito — cerrar fase 0 y completar base persistente

1. Identificar el restaurante piloto y confirmar canal, moneda, modalidad y cobro.
2. Resolver consumo de inventario, faltantes, cancelaciones y valorización.
3. Convertir el borrador de dominio en reglas aprobadas y criterios verificables.
4. Configurar PostgreSQL de desarrollo en Supabase.
5. Crear modelos de catálogo y acceso de personal; sembrar datos persistentes.
6. Sustituir la carta de demostración por la API del catálogo.

Después: pedido completo → producción cocina/barra → recetas e inventario →
dashboard → despliegue de prueba, siguiendo las fases 2–5 del README.

## Historias iniciales

| Historia | Criterio de aceptación | Estado |
|---|---|---|
| Como cliente, exploro la carta | React muestra categorías, precios y descripciones obtenidos de Django | Demostración lista |
| Como cliente, encuentro un producto | Puedo filtrar y buscar; si no hay resultados se informa | Demostración lista |
| Como cliente, creo un pedido | El servidor valida importes y evita duplicados; devuelve código seguro | Pendiente |
| Como cocina/barra, preparo mis tickets | Solo accedo a mi estación; READY del pedido espera a todas | Pendiente |
| Como inventario, registro entradas y consumos | Cada movimiento conserva referencia, cantidades y responsable | Pendiente |
| Como gerente, consulto resultados | Los indicadores usan transacciones persistidas y periodo explícito | Pendiente |
