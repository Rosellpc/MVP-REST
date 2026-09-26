# ADR 0001 — Base local y límite de la demostración

Estado: adoptado para el primer hito técnico.

## Contexto

Solo existía el README. La sección 14 permite SQLite para verificar instalación
y endpoints básicos, y pide conectar PostgreSQL antes de crear modelos de negocio.
El usuario ha confirmado Perú como país del piloto.

## Decisión

- Mantener el repositorio actual como monorepo: frontend, backend y docs.
- React + TypeScript + React Router + TanStack Query; estilos CSS simples en esta etapa.
- Django 5.2 LTS + DRF; Supabase se utilizará exclusivamente como PostgreSQL.
- SQLite solo para la instalación y las migraciones predeterminadas de Django.
- Servir una carta de ejemplo desde Django, con `demo: true`, identificadores
  prefijados con `demo-` y precios decimales serializados como texto.
- Activar esos datos solo con DEBUG y DEMO_MENU_ENABLED, ambos verdaderos.
- PEN y America/Lima son valores de demostración configurables, no decisiones
  comerciales confirmadas. No se calculan impuestos ni se acepta dinero.
- Autenticación de sesión del admin de Django para la base inicial. La estrategia
  de autenticación de las futuras áreas React del personal queda pendiente.

## Consecuencias

La interfaz y la API pueden probarse sin credenciales remotas. No se crean modelos
de pedidos, recetas o inventario sobre supuestos todavía no aceptados. La carta
se sustituirá por consultas PostgreSQL antes del primer piloto operativo.
No se declara terminada la fase 0 ni la fase 1 del README.
