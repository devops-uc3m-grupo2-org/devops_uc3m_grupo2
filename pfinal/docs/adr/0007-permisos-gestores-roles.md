# ADR 007: Permisos de gestores — enfoque inicial y migración a roles

## Estado
**Aceptado — RBAC implementado (2026-05)**

## Contexto

Al principio del desarrollo se usó una variable de entorno `MANAGERS` con emails permitidos para control de acceso rápido. En Fase 2 se migró a un sistema de roles completo.

## Decisión final

RBAC basado en la tabla `roles` y relaciones many-to-many con `users`. Los endpoints comprueban el rol del usuario autenticado vía JWT + `Depends(get_current_user)`.

## Roles implementados

| Rol | Puede gestionar alertas (require_gestor) | Verificado |
|---|---|---|
| `admin` | ✅ | ✅ |
| `gestor` | ✅ | ✅ |
| `user` | ❌ → HTTP 403 | ✅ |

**Verificado el 2026-05-22** (inspección manual M del examen): un usuario con rol `user` (sin `admin` ni `gestor`) recibe `403 Forbidden` al intentar acceder a endpoints protegidos por `require_gestor`.

## Consecuencias

- Sistema de roles completamente funcional en BD y endpoints.
- El seed inicial crea roles `admin`, `user` y `gestor` y el usuario `admin@newsradar.com` con rol `admin`.

## Fecha

2026-03-12 — propuesta inicial con MANAGERS
2026-05 — RBAC completo implementado y verificado
