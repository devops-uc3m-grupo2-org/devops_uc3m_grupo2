# ADR 006: Modelo de dominio — `Alert` y `DetectedNews`

## Estado
**Aceptado**

## Contexto

Fase 1 requiere almacenar reglas/alertas definidas por gestores y las noticias detectadas asociadas a esas alertas. Se necesita un diseño sencillo y suficiente para el objetivo inicial.

## Decisión (modelo implementado)

El modelo real difiere del diseño inicial. Las tablas implementadas en `pfinal/app/models/models.py`:

- `alerts` — alerta creada por un usuario. Campos: `id`, `name`, `descriptors` (lista JSON), `categories` (JSON), `cron_expression`, `is_active`, `user_id`.
- `news_items` — noticias capturadas de feeds RSS. Campos: `id`, `title`, `link` (unique), `summary`, `published`, `channel_id`.
- `alert_news` — tabla intermedia many-to-many entre alertas y noticias. Campos: `alert_id`, `news_item_id`.
- `notifications` — notificaciones generadas por el scheduler al encontrar matches. Campos: `id`, `timestamp`, `alert_id`, `metrics` (JSON).

Relaciones reales:
- `User` 1:N `Alert`
- `Alert` N:M `NewsItem` via `AlertNews`
- `Alert` 1:N `Notification`
- `InformationSource` 1:N `RSSChannel` 1:N `NewsItem`

> La tabla `detected_news` del diseño original fue renombrada y reestructurada como `alert_news` (join table) + `notifications` (eventos generados).

## Justificación

- La relación N:M entre alertas y noticias es más correcta: una noticia puede matchear múltiples alertas, y una alerta puede tener múltiples noticias.
- Las notificaciones son entidades separadas del match (permiten almacenar métricas y timestamp del envío).

## Consecuencias

- 281/281 casos del verificador pasando con este modelo (2026-05-21).
- Las categorías IPTC se normalizaron en tabla `categories` separada (id=código numérico IPTC).

## Fecha

2026-03-12 — diseño inicial
2026-05 — modelo real implementado con `AlertNews` + `Notification`
