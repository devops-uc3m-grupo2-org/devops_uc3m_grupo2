# ADR 009: Autenticación y tokens — JWT

## Estado
**Aceptado**

## Contexto

La aplicación requiere autenticación para endpoints sensibles (registro, login, gestión de alertas). El sistema debe ser sencillo, interoperable y alineado con requisitos del curso (uso de JWT en Fase 1).

## Decisión

Usar JSON Web Tokens (JWT) para autenticación y autorización básica. Los tokens se firmarán con `HS256` (algoritmo configurable vía `ALGORITHM`) y una `SECRET_KEY` gestionada por variables de entorno.

## Justificación

- JWT es un estándar ampliamente utilizado y suficiente para la Fase 1.
- Fácil de integrar con `python-jose` y `fastapi`.

## Consecuencias

- Requiere proteger la `SECRET_KEY` y considerar rotación de claves en fases posteriores.
- Para permisos más finos (roles, scopes) se añadirá validación RBAC en futuros ADRs.

## Implementación

- Uso de `python-jose` para firmado y verificación.
- Dependencia en variables de entorno `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.

## Fecha

2026-03-12
