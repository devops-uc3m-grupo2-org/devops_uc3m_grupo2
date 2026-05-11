# ADR 006: Modelo de dominio — `Alert` y `DetectedNews`

## Estado
**Aceptado**

## Contexto

Fase 1 requiere almacenar reglas/alertas definidas por gestores y las noticias detectadas asociadas a esas alertas. Se necesita un diseño sencillo y suficiente para el objetivo inicial.

## Decisión

Crear dos tablas principales:

- `alerts` — representa una alerta creada por un gestor. Campos mínimos: `id`, `title`, `description`, `user_id` (owner), `iptc_category`, `created_at`.
- `detected_news` — noticias detectadas asociadas a una alerta. Campos mínimos: `id`, `title`, `url`, `alert_id`, `detected_at`.

Relaciones: `Alert` 1:N `DetectedNews`; `User` 1:N `Alert`.

## Justificación

- Modelo simple que cubre el objetivo 1 sin sobre-diseño.
- Permite consultas directas: listar alertas, listar detecciones por alerta, y almacenar metadatos mínimos para auditoría.

## Consecuencias

- Positivas:
  - Implementación rápida y claridad conceptual.
  - Fácil de indexar y consultar en PostgreSQL.

- Futuras ampliaciones:
  - Añadir score, matching metadata, fuente (RSS/API), y deduplicación.
  - Normalizar categorías IPTC en una tabla separada si es necesario.

## Fecha

2026-03-12
