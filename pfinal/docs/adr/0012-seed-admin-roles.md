# ADR 012: Seed inicial — admin y roles

## Estado
**Aceptado**

## Contexto

Para probar la aplicación y cumplir Fase 1 se necesita un usuario administrador y roles básicos (`admin`, `user`).

## Decisión

Crear un seed inicial que inserte roles `admin`, `user` y `gestor`, y un usuario `admin@newsradar.com` con rol `admin`, en el arranque (si no existen).

## Justificación

- Facilita pruebas y revisión por parte del profesor sin necesidad de UI.

## Consecuencias

- El seed se ejecuta en `startup` de la app y debe ser idempotente.

## Fecha

2026-03-12
