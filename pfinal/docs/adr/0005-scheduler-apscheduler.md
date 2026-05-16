# ADR 005: Elección de scheduler — APScheduler (Background)

## Estado
**Aceptado (Fase 1)**

## Contexto

La aplicación necesita ejecutar tareas periódicas de monitorización de alertas (detección de noticias) en Fase 1. Las opciones consideradas incluyen correr un worker externo (Celery + broker), usar un servicio cron externo, o usar un scheduler embebido en el proceso web.

## Decisión

Para la Fase 1 se usará `APScheduler` en modo `BackgroundScheduler` ejecutándose dentro del proceso FastAPI. La integración es ligera y permite ejecutar la función `monitor_alerts` cada X segundos/minutos.

## Justificación

- Rápida de desplegar y suficiente para pruebas / fase inicial.
- Evita infra adicional (RabbitMQ/Redis) y complejidad de despliegue en Fase 1.
- Permite iterar rápidamente y validar la lógica de detección en el mismo contenedor.

## Consecuencias

- Positivas:
  - Menos infra y menos componentes a operar.
  - Inicio automático junto con la app, sencillo de debug.

- Negativas / Riesgos:
  - No tolerante a restarts del proceso: las tareas programadas se pierden si el proceso muere. Para producción es recomendable migrar a Celery/Beat o un gestor de tareas externo.
  - Aún con APScheduler, si la carga es alta podría ser necesario separar worker.

## Migración futura

- Migrar a Celery/Redis o un sistema de colas si necesitamos fiabilidad, reintentos y escalado horizontal.

## Fecha

2026-03-12
