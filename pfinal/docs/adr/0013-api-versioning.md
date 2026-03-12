# ADR 013: Versionado de API y rutas

## Estado
**Aceptado**

## Contexto

Se necesita una convención mínima para versionar endpoints y permitir evolución sin romper clients.

## Decisión

Prefijar todas las rutas con `/api/v1/` para la Fase 1. Las futuras versiones incrementarán el número (`/api/v2/`) y se documentarán en el changelog.

## Justificación

- Convención simple y explícita, compatible con FastAPI y routers modularizados.

## Consecuencias

- Mantener compatibilidad hacia atrás cuando se añadan versiones.

## Fecha

2026-03-12
