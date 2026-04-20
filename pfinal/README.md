# NewsRadar API

Sistema de monitorización de noticias RSS con alertas inteligentes, clasificación IPTC y sugerencias de IA.

## Sprints cubiertos

| Sprint | Contenido                                      | Estado |
| ------ | ---------------------------------------------- | ------ |
| S0–S1  | Infraestructura, auth JWT, usuarios y roles    | ✅      |
| S2     | Fuentes RSS, canales, categorías IPTC          | ✅      |
| S3     | Alertas CRUD, notificaciones, cron             | ✅      |
| S4     | IA generativa: sugerencias y sinónimos         | ✅      |
| S5     | Motor RSS + matching alertas + notificaciones  | ✅      |
| S6     | Stats/dashboard con métricas reales            | ✅      |
| S7     | Tests, CI/CD con GitHub Actions, documentación | ✅      |

## Stack técnico

- **Backend**: FastAPI + Python 3.12
- **Base de datos**: PostgreSQL + SQLAlchemy
- **Autenticación**: JWT (python-jose + passlib)
- **RSS**: feedparser
- **Scheduler**: APScheduler (polling cada 5 min)
- **IA**: Servicio propio de sinónimos con diccionario IPTC extensible
- **Contenedores**: Docker + Docker Compose
- **CI**: GitHub Actions

## Levantar el proyecto

```bash
# 1. Variables de entorno (opcional, hay valores por defecto)
cp .env.example .env

# 2. Levantar API + PostgreSQL
docker compose up --build
```

| Recurso                              | URL                                                    |
| ------------------------------------ | ------------------------------------------------------ |
| API + Swagger                        | http://localhost:8000/docs                             |
| Aplicación web (si está configurada) | http://localhost:8000                                  |
| pgAdmin                              | http://localhost:8080 (admin@newsradar.com / admin123) |

**Usuario admin por defecto**: `admin@newsradar.com` / `admin123`

## Ejecutar los tests

```bash
docker compose run --rm app python -m pytest app/tests/ -v
```

Suite actual: **26 tests** repartidos en 8 archivos:

| Archivo              | Qué cubre                                               |
| -------------------- | ------------------------------------------------------- |
| `test_health.py`     | Health check                                            |
| `test_login.py`      | Registro, login, credenciales incorrectas               |
| `test_sources.py`    | CRUD fuentes, fetch con debug, duplicados               |
| `test_alerts.py`     | CRUD alertas y notificaciones con JWT                   |
| `test_news.py`       | Listado de noticias, fetch autenticado                  |
| `test_ai.py`         | Endpoint `/suggestions`, keyword conocido y desconocido |
| `test_stats.py`      | Métricas reales, auth requerida, contador se actualiza  |
| `test_monitoring.py` | Matching alertas-noticias, pipeline completo Sprint 5   |

## Endpoints principales

### Autenticación
```
POST /api/v1/auth/register   — Registro (JSON: email, password, first_name, last_name, organization)
POST /api/v1/auth/login      — Login    (JSON: email, password) → access_token
```

### Fuentes RSS
```
GET    /api/v1/information-sources               — Listar fuentes          [JWT]
POST   /api/v1/information-sources               — Crear fuente            [JWT]
POST   /api/v1/information-sources/{id}/fetch    — Importar noticias       [JWT]
```

### Alertas y notificaciones
```
GET    /api/v1/users/{id}/alerts                              — Listar alertas       [JWT]
POST   /api/v1/users/{id}/alerts                              — Crear alerta         [JWT]
PUT    /api/v1/users/{id}/alerts/{aid}                        — Actualizar alerta    [JWT]
DELETE /api/v1/users/{id}/alerts/{aid}                        — Eliminar alerta      [JWT]
GET    /api/v1/users/{id}/alerts/{aid}/notifications          — Ver notificaciones   [JWT]
POST   /api/v1/users/{id}/alerts/{aid}/notifications          — Crear notificación   [JWT]
```

### Noticias
```
GET  /api/v1/news            — Listar noticias (público)
GET  /api/v1/news/latest     — Noticias enriquecidas con fuente y categoría (público)
POST /api/v1/news/fetch      — Importar desde todos los canales RSS [JWT]
```

### IA y estadísticas
```
GET /api/v1/suggestions?keyword=economía  — Sinónimos y términos relacionados [JWT]
GET /api/v1/stats                         — Métricas: total_news, total_sources, total_alerts [JWT]
```

## Guía rápida de demo

```bash
# 1. Login (usa el admin por defecto)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@newsradar.com","password":"admin123"}'
# → guarda el access_token como TOKEN

# 2. Crear fuente RSS
curl -X POST http://localhost:8000/api/v1/information-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"El País","rss_url":"https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"}'

# 3. Crear alerta con descriptores
curl -X POST http://localhost:8000/api/v1/users/1/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alerta Tecnología","descriptors":["tecnología","IA"],"categories":[],"cron_expression":"*/5 * * * *","is_active":true}'

# 4. Importar noticias
curl -X POST http://localhost:8000/api/v1/news/fetch \
  -H "Authorization: Bearer $TOKEN"

# 5. Sugerencias de IA
curl "http://localhost:8000/api/v1/suggestions?keyword=economía" \
  -H "Authorization: Bearer $TOKEN"

# 6. Estadísticas
curl http://localhost:8000/api/v1/stats \
  -H "Authorization: Bearer $TOKEN"
```

## Arquitectura del scheduler (Sprint 5)

El `BackgroundScheduler` (APScheduler) se lanza al arrancar la aplicación y ejecuta cada 5 minutos:

1. Consulta todos los `RSSChannel` de la BD.
2. Para cada canal llama a `fetch_feed` (feedparser) e inserta `NewsItem` nuevos.
3. Ejecuta `process_alerts_for_items`: cruza cada noticia nueva con las alertas activas.
4. Si un descriptor de la alerta aparece en el título o resumen → crea un `AlertNews`.

Los usuarios consultan sus coincidencias vía `/notifications` y pueden crear notificaciones con métricas desde su cliente.

## CI/CD

GitHub Actions ejecuta automáticamente en cada push:
- `docker compose up` con la base de datos de test
- `pytest app/tests/ -v`
- El pipeline falla si algún test no pasa
