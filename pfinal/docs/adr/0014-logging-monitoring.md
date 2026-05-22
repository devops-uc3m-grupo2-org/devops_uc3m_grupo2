# ADR 014: Logging y monitoring básicos

## Estado
**Aceptado — Implementado (2026-05)**

## Contexto

Se requiere visibilidad de errores y métricas mínimas para depuración durante el desarrollo y entrega.

## Decisión

Usar prefijos de log estandarizados en `stdout` para que `docker compose logs app` muestre el estado de cada operación. Las métricas básicas se exponen via `GET /api/v1/stats`.

## Implementación real

Los logs de Docker siguen este esquema de prefijos:

| Prefijo | Qué indica |
|---|---|
| `[FETCH] Source N: X new items` | Resultado de cada fetch RSS |
| `[MATCH] Alert N: X matched news` | Noticias matcheadas por alerta |
| `[EMAIL] Enviado a {email} -> {asunto}` | Email de notificación enviado |
| `[EMAIL] Envío deshabilitado (SEND_EMAILS=false), se omite: {asunto}` | Email omitido (fallback) |

Estos prefijos son la base de la inspección manual M1/M2/M3 del examen — los scripts grepen `[EMAIL]` en los logs de Docker para verificar que el sistema envía notificaciones.

## Cobertura de tests (CI)

Cobertura: **96,48 %** (umbral: 80 %). Ficheros de infraestructura excluidos en `.coveragerc` (`main.py`, `scheduler.py`, `fetcher.py`, `notifications.py`, `seed_rss.py`).

## Consecuencias

- Logs estructurados (JSON) pueden añadirse si se requiere en fases futuras.
- Prometheus/Grafana: no implementado (fuera del alcance del proyecto académico).

## Fecha

2026-03-12 — propuesta inicial
2026-05 — implementado con prefijos `[FETCH]`, `[MATCH]`, `[EMAIL]`; cobertura CI al 96,48 %
