# ADR 005: Elección de scheduler — APScheduler (Background)

## Estado
**Aceptado — Implementado y verificado (2026-05-21)**

## Contexto

La aplicación necesita ejecutar tareas periódicas de monitorización de alertas (detección de noticias). Las opciones consideradas incluyen correr un worker externo (Celery + broker), usar un servicio cron externo, o usar un scheduler embebido en el proceso web.

## Decisión

Se usa `APScheduler` en modo `BackgroundScheduler` ejecutándose dentro del proceso FastAPI. Ejecuta la función `fetch_all_sources_job` cada 5 minutos.

## Implementación real (`pfinal/app/core/scheduler.py`)

```python
scheduler.add_job(
    fetch_all_sources_job,
    trigger="cron",
    minute="*/5",
    max_instances=1,
    misfire_grace_time=60,
)
```

`max_instances=1` evita solapamientos si el fetch tarda más de lo esperado.

### Bug crítico corregido — `misfire_grace_time`

El `misfire_grace_time` por defecto de APScheduler es **1 segundo**. Los jobs llegaban ~1.3 s tarde (overhead del contenedor) → se marcaban como "missed" y no ejecutaban el fetch. Síntoma en logs:

```
Run time of job "fetch_all_sources_job" was missed by 0:00:01.305160
```

Corrección: `misfire_grace_time=60` — permite hasta 60 s de retraso antes de saltar el job. Sin este fix, las notificaciones nunca se generaban.

## Justificación

- Rápida de desplegar y suficiente para el proyecto.
- Evita infra adicional (RabbitMQ/Redis) y complejidad de despliegue.
- Verificado el 2026-05-21: el scheduler genera notificaciones y envía emails correctamente (M1/M2/M3 pasados). 8 noticias del Mock RSS en 2 ciclos (M5 en 360 s).

## Consecuencias

- Positivas:
  - Menos infra y menos componentes a operar.
  - Inicio automático junto con la app, sencillo de debug.

- Negativas / Riesgos:
  - No tolerante a restarts del proceso: las tareas programadas se pierden si el proceso muere. Para producción es recomendable migrar a Celery/Beat.

## Migración futura

- Migrar a Celery/Redis si se necesita fiabilidad, reintentos y escalado horizontal.

## Fecha

2026-03-12 — propuesta inicial
2026-05-21 — bug `misfire_grace_time` corregido, verificado en producción
