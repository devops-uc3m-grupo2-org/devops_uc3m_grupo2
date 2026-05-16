# ADR 011: Migrations — Alembic

## Estado
**Aceptado**

## Contexto

La evolución del esquema de BD requiere control de versiones y migraciones reproducibles.

## Decisión

Usar Alembic para gestionar migraciones de SQLAlchemy. Mantener las migraciones en `alembic/versions` y ejecutar `alembic revision --autogenerate` al introducir cambios en los modelos.

## Justificación

- Alembic es la solución estándar junto a SQLAlchemy.
- Permite mantener un historial de cambios y facilitar despliegues con migración automática en CI/CD.

## Consecuencias

- Incluir pasos en README para ejecutar `alembic upgrade head` como parte del despliegue.

## Fecha

2026-03-12
