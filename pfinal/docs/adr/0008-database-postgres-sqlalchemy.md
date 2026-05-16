# ADR 008: Elección de base de datos — PostgreSQL + SQLAlchemy

## Estado
**Aceptado**

## Contexto

El proyecto necesita una base de datos relacional fiable para almacenar usuarios, alertas y noticias detectadas. Se requiere compatibilidad con migraciones (Alembic) y facilidad para consultas y relaciones.

## Decisión

Usar PostgreSQL como base de datos relacional y SQLAlchemy como ORM en el backend. Las migraciones se gestionarán con Alembic.

## Justificación

- PostgreSQL es robusto y ampliamente apoyado en entornos académicos y de producción.
- SQLAlchemy (v2) ofrece potencia y flexibilidad para modelar relaciones y usar sesiones.
- Alembic facilita versionado del esquema y despliegues reproducibles.

## Consecuencias

- Positivas:
  - Buen soporte para relaciones y consultas complejas.
  - Escalable y compatible con la mayoría de infraestructuras en la nube.

- Consideraciones:
  - Requiere administración de la instancia y backups.
  - Para índices de búsquedas semánticas o vectores se debería integrar una capa vectorial especializada.

## Fecha

2026-03-12
