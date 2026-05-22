# ADR 003: Estrategia de ingestión de fuentes RSS y orquestación de monitorización continua

## Estado
**Aceptado — Implementado y verificado (2026-05-21)**

## Contexto

Según el documento oficial del proyecto (páginas 2-5 y 3.1):

- El sistema debe **monitorizar de forma continua** canales RSS mediante un proceso descrito por una **expresión cron**.
- Para cada alerta definida (palabra clave + 3-10 sinónimos/relacionados generados por IA):
  - Detectar noticias que contengan cualquiera de los descriptores.
  - Clasificar la noticia en categoría IPTC (de la alerta o de la fuente).
  - Almacenar la noticia y generar notificaciones (email + buzón interno).
- El sistema debe incluir **mínimo 100 canales RSS** iniciales (cubriendo todas las categorías IPTC de primer nivel).
- Requisitos DevOps: automatización, Docker, pipeline, mínimo intervención manual.
- Ya tenemos en Fase 1-2:
  - FastAPI + PostgreSQL + pgvector (ADR 002).
  - Autenticación JWT y gestión básica de usuarios/alertas (por implementar).
  - Uso intensivo de IA generativa obligatorio (recomendación de sinónimos y clasificación).

Se necesita un mecanismo fiable para:
- Parsear RSS periódicamente.
- Ejecutar jobs según cron por alerta.
- Procesar en background (embeddings, clasificación, notificaciones).
- Evitar duplicados (URL o hash del contenido).
- Escalar a cientos de fuentes sin bloquear la API.

## Decisión

**Usaremos:**
- **feedparser** para parsear RSS (estándar de facto).
- **APScheduler (AsyncIOScheduler)** integrado en el startup de FastAPI para orquestación de tareas periódicas.
- **BackgroundTasks + Celery** (opcional en Fase 3) solo para tareas pesadas de IA (embedding + clasificación).
- Todo dentro del mismo contenedor Docker (sin broker externo en fase inicial).

**No usaremos** soluciones externas como Scrapy, Airflow o cron del sistema operativo.

## Justificación

| Criterio del proyecto                | APScheduler + feedparser   | Celery + Redis | Airflow | Cron + script separado | Comentario clave del PDF      |
| ------------------------------------ | -------------------------- | -------------- | ------- | ---------------------- | ----------------------------- |
| Expresión cron por alerta            | ★★★★★                      | ★★★★★          | ★★★★★   | ★★★                    | Requerido explícitamente      |
| Integración directa con FastAPI      | ★★★★★                      | ★★★★           | ★★      | ★★★                    | Startup event ya existe       |
| Zero servicios extra (Docker simple) | ★★★★★                      | ★★★            | ★       | ★★★★★                  | Proyecto académico            |
| Procesamiento background de IA       | ★★★★ (con BackgroundTasks) | ★★★★★          | ★★★★    | ★★★                    | Uso intensivo IA              |
| Manejo de duplicados y idempotencia  | ★★★★★                      | ★★★★★          | ★★★★★   | ★★★★                   | Necesario para notificaciones |
| Facilidad de pruebas y CI/CD         | ★★★★★                      | ★★★★           | ★★★     | ★★★                    | DevOps obligatorio            |
| Overhead operativo (estudiantes)     | Muy bajo                   | Medio          | Alto    | Bajo                   | Deadline mayo 2026            |

**Razones principales para elegir APScheduler + feedparser**:
- Extremadamente ligero y 100% Python → se integra en 5 líneas en `main.py` (ya tenemos `@app.on_event("startup")`).
- Soporta cron nativo por alerta (`cron='0 * * * *'` por ejemplo).
- No requiere Redis/RabbitMQ en fase inicial → cumple “desplegar con un único comando”.
- feedparser es la librería más madura y robusta para RSS (maneja errores, fechas, enclosures, etc.).
- Fácil escalar después a Celery si el volumen crece (solo cambiar el job a task).

## Consecuencias

### Positivas
- Monitorización real-time por alerta sin infraestructura extra.
- Código limpio: un `RSSIngestorService` inyectado como dependencia.
- Fácil seeding inicial de 100+ fuentes RSS (script de inicialización).
- Al detectar match → almacenar en `AlertNews` + generar `Notification` + enviar email via SMTP.
- Dashboard de estadísticas (nº noticias, fuentes) se actualiza automáticamente.

### Negativas / Mitigadas
- APScheduler corre en el mismo proceso → si hay 50 alertas muy frecuentes podría consumir CPU → mitigar con rate-limiting y jobs agrupados (una sola tarea global cada X minutos que procesa todas las alertas activas).
- Posibles rate-limits de fuentes RSS → implementar backoff y caché de última fecha procesada.
- En producción futura → migrar jobs pesados a Celery + Redis (ADR futuro si es necesario).

## Alternativas consideradas y rechazadas

- **Celery + Redis desde el principio** → Muy robusto, pero añade 2 servicios Docker y complejidad innecesaria para el volumen esperado.
- **Airflow** → Sobredimensionado para un proyecto universitario.
- **Cron del sistema + script Python separado** → Funciona, pero pierde integración con FastAPI y base de datos (más difícil logging y estado).
- **Scrapy + scheduler** → Overkill (pensado para web crawling masivo, no RSS simple).

## Referencias
- Documento oficial NEWSRADAR (págs. 2-5 y 3.1).
- APScheduler docs + FastAPI integration examples 2026.
- feedparser documentation.
- Ejemplo oficial del proyecto (newsradar_api.zip) – API REST ya usa FastAPI.

## Estado de implementación (2026-05-22)

- **200 canales RSS verificados** en `pfinal/app/services/seed_rss.py` — todas las 17 categorías IPTC cubiertas (SMOKE-003 ≥ 100 ✅, SMOKE-004 ✅).
- Proceso de verificación: script `pfinal/check_rss_urls.sh` — resultado `OK: 200 / 200 — FAIL: 0 / 200`.
- Fuentes incluidas: El País, El Mundo, ABC, La Vanguardia, Marca, Mundo Deportivo, Euronews España, Cinco Días, 20 Minutos, RTVE (eliminado, sustituido), y más de 20 medios.

### Bug crítico corregido — `UniqueViolation` en el fetcher

Al insertar noticias, un `IntegrityError` por URL duplicada dejaba la sesión SQLAlchemy en estado `PendingRollbackError` y el ciclo completo fallaba. Corregido con savepoints (`db.begin_nested()`) por cada item:

```python
try:
    with db.begin_nested():
        db.add(item)
        db.flush()
    created_items.append(item)
except IntegrityError:
    pass  # savepoint revertido; el resto del ciclo continúa
```

Fecha de decisión: 12 marzo 2026
Propuesto por: Equipo NEWSRADAR
Implementado: mayo 2026
