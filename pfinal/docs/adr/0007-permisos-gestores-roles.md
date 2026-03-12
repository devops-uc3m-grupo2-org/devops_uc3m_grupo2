# ADR 007: Permisos de gestores — enfoque inicial y migración a roles

## Estado
**Aceptado (Fase 1)**

## Contexto

Al principio del desarrollo se necesita una forma simple de restringir quién puede crear/listar alertas (gestores). Para acelerar la entrega, se eligió un método rápido basado en la variable de entorno `MANAGERS` que contiene una lista de emails permitidos.

## Decisión

Fase 1: usar `MANAGERS` (emails) como control de acceso para los endpoints de gestión de alertas.

Plan de migración: en Fase 2 migrar a un sistema basado en la tabla `roles` y relaciones many-to-many entre `users` y `roles`, con comprobaciones RBAC en los endpoints.

## Justificación

- Rápido de implementar y suficiente para la entrega del objetivo 1.
- Evita añadir complejidad de migraciones y lógica RBAC inmediata.

## Consecuencias

- Positivas:
  - Entrega rápida y control simple de acceso.

- Negativas:
  - No escalable ni auditable a largo plazo.
  - Requiere migración y cambios en código/DB cuando se active RBAC.

## Migración propuesta

- Añadir tabla `roles` (ya existe en DB) y tabla intermedia `user_roles`.
- Crear middleware/dependencies que verifiquen roles desde DB en lugar de `MANAGERS`.

## Fecha

2026-03-12
