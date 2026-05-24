# NewsRadar

Sistema de monitorización de noticias RSS con alertas inteligentes, clasificación IPTC y sugerencias de IA.

> **Este documento:** punto de entrada del proyecto — arranque, endpoints, tests, CI/CD y tabla de documentación.
> **Documentos clave:** [`docs/demo_recorrido.md`](docs/demo_recorrido.md) · [`docs/arquitectura.md`](docs/arquitectura.md) · [`docs/inspeccion_manual_swagger.md`](docs/inspeccion_manual_swagger.md) · [`docs/guia_de_respuestas_a_preguntas_tipicas.md`](docs/guia_de_respuestas_a_preguntas_tipicas.md)

> **Verificador:** 281/281 OK (100 %) — última ejecución 2026-05-24

## Stack técnico

- **Backend**: FastAPI + Python 3.12
- **Base de datos**: PostgreSQL 16 + SQLAlchemy ORM
- **Autenticación**: JWT HS256 (60 min) + verificación por email (24h)
- **RSS**: feedparser + APScheduler (polling cada 5 min)
- **IA**: Groq (Llama 3.3 70B) con fallback a diccionario IPTC local
- **Frontend**: HTML + CSS + Vanilla JS (sin dependencias externas)
- **Contenedores**: Docker + Docker Compose
- **CI/CD**: GitHub Actions (tests, cobertura, Flake8, Bandit, Radon, pip-audit, ESLint, docker build)

## Levantar el proyecto

```bash
# Arrancar desde cero (borra volúmenes y reconstruye)
bash start.sh

# O manualmente:
cp .env.example .env        # ajustar credenciales SMTP y GROQ_API_KEY
docker compose up --build
```

| Recurso      | URL                                                      |
|---|---|
| API Swagger  | http://localhost:8000/docs                               |
| ReDoc        | http://localhost:8000/redoc                              |
| Frontend web | http://localhost:8000                                    |
| pgAdmin      | http://localhost:8080 (admin@newsradar.com / admin123)   |

Al arrancar se crean automáticamente:
- Roles: `admin`, `gestor`, `user`
- Usuario admin: `admin@newsradar.com` / `admin123`
- 15 fuentes RSS + 200 canales IPTC (15 medios, 16 categorías activas)

> El catálogo IPTC define 17 categorías y todas están en el enum del modelo (`IPTCCategoryEnum`). En BD se activan 16 porque ninguna fuente del seed genera noticias de Religión y culto de forma consistente — la categoría existe en el modelo pero no tiene canales activos.

## Ejecutar los tests

```bash
# Dentro del contenedor
docker compose exec app python -m pytest app/tests/ -v

# Con cobertura
docker compose exec app python -m pytest app/tests \
  --cov=app.main --cov=app.core --cov=app.models --cov=app.services \
  --cov-report=term-missing
```

72 tests en 13 archivos — cobertura real: **96%** en módulos de lógica.

| Archivo | Qué cubre |
|---|---|
| `test_health.py` | Health check |
| `test_login.py` | Registro, login, credenciales incorrectas |
| `test_auth_extended.py` | Verificación de cuenta, forgot/reset password, duplicados |
| `test_sources.py` | CRUD fuentes, fetch con debug, duplicados |
| `test_alerts.py` | CRUD alertas y notificaciones con JWT |
| `test_news.py` | Listado de noticias, fetch autenticado |
| `test_ai.py` | Endpoint `/suggestions`, keyword conocido y desconocido |
| `test_stats.py` | Métricas reales, auth requerida, contador se actualiza |
| `test_stats_extended.py` | Wordcloud, stats por categoría, límite 20 alertas |
| `test_categories.py` | CRUD completo categorías IPTC + 404s |
| `test_roles_extended.py` | CRUD completo roles + 409 al borrar rol asignado |
| `test_users_extended.py` | CRUD usuarios y CRUD completo de notificaciones |
| `test_monitoring.py` | Matching alertas-noticias, pipeline completo |

## Endpoints principales

### Autenticación
```
POST /api/v1/auth/register       — Registro (email, password, first_name, last_name, organization)
POST /api/v1/auth/login          — Login → access_token JWT
GET  /api/v1/auth/verify?token=  — Verificar cuenta por email
```

### Fuentes RSS
```
GET    /api/v1/information-sources                  — Listar fuentes          [JWT]
POST   /api/v1/information-sources                  — Crear fuente            [JWT gestor]
POST   /api/v1/information-sources/{id}/rss-channels — Añadir canal RSS       [JWT gestor]
POST   /api/v1/news/fetch                           — Importar todos los RSS  [JWT gestor]
```

### Alertas y notificaciones
```
GET    /api/v1/users/{id}/alerts                         — Listar alertas       [JWT]
POST   /api/v1/users/{id}/alerts                         — Crear alerta         [JWT gestor]
PUT    /api/v1/users/{id}/alerts/{aid}                   — Actualizar alerta    [JWT gestor]
DELETE /api/v1/users/{id}/alerts/{aid}                   — Eliminar alerta      [JWT gestor]
GET    /api/v1/users/{id}/alerts/{aid}/notifications     — Ver notificaciones   [JWT]
```

### IA y estadísticas
```
GET /api/v1/suggestions?keyword=X   — Sinónimos (Groq o fallback IPTC)  [JWT]
GET /api/v1/stats                   — Métricas globales                  [JWT]
GET /api/v1/stats/by-category       — Alertas por categoría IPTC         [JWT]
GET /api/v1/stats/wordcloud         — Nube de palabras                   [JWT]
```

## Arquitectura del scheduler

`APScheduler` arranca con la app y ejecuta cada 5 minutos:

1. Consulta todos los `RSSChannel` activos en BD.
2. Para cada canal llama a `fetch_feed` (feedparser) e inserta `NewsItem` nuevos (deduplicación por URL/link).
3. Ejecuta `process_alerts_for_items`: cruza cada noticia nueva con las alertas activas mediante regex (`\bpalabra\b`).
4. Por cada match: crea `AlertNews` + `Notification` y envía email (`[EMAIL]` en logs).

El matching es automático — no hay endpoint manual para dispararlo.

## CI/CD

GitHub Actions en `.github/workflows/fastapi-ci.yml` ejecuta en cada push:

| Paso | Herramienta | Qué hace |
|---|---|---|
| 1 | pytest + pytest-cov | 96.48% cobertura · 13 archivos, umbral ≥ 80% |
| 2 | coverage XML | Artifact `coverage-report` descargable |
| 3 | Flake8 | Estilo PEP8 |
| 4 | Bandit | Análisis de seguridad |
| 5 | Radon | Complejidad ciclomática |
| 6 | pip-audit | Vulnerabilidades en dependencias |
| 7 | ESLint | Calidad del JS del frontend |
| 8 | pdoc | Documentación técnica HTML (artifact `technical-docs`) |
| 9 | docker build | Empaquetado de la imagen |

## Scripts de operación

Ver [docs/sh_scripts_newsradar.md](docs/sh_scripts_newsradar.md) para la guía completa de todos los scripts `.sh` y el orden de ejecución en el examen.

## Configuración email (SMTP Gmail)

```env
SMTP_USER=newsradargrupo@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # App Password de 16 caracteres
EMAIL_FROM=newsradargrupo@gmail.com
SEND_EMAILS=true                    # false → solo log, no envía
```

Con `SEND_EMAILS=false` los emails aparecen en `docker compose logs app` con prefijo `[EMAIL]` — M1/M2/M3 pasan igualmente.

## Documentación

| Documento | Ruta |
|---|---|
| Arquitectura del sistema | `docs/arquitectura.md` |
| Diagrama entidad-relación | `docs/DiagramaRelacionEntidad/DiagramaRelacionEntidad.png` |
| Trazabilidad requisitos ↔ código | `docs/trazabilidad_requisitos.md` |
| Registro de prompts IA | `docs/prompts_ia.md` |
| ADRs (decisiones arquitectónicas) | `docs/adr/` — 14 ficheros (0001–0014) |
| Sprint reviews | `docs/sprint_review_0_y_1.md` … `docs/sprint_review_7.md` |
| Demo paso a paso (curl + explicaciones) | `docs/demo_recorrido.md` |
| Script Python de demo automatizada | `docs/demo_recorrido.py` |
| Guía de inspección manual (Swagger) | `docs/inspeccion_manual_swagger.md` |
| Preguntas típicas de defensa | `docs/guia_de_respuestas_a_preguntas_tipicas.md` |
| Guía de tests | `docs/testing.md` |
| CI/CD | `docs/ci_cd_documentation.md` |

---

## Sprints

| Sprint | Contenido | Estado |
|---|---|---|
| S0–S1 | Infraestructura, auth JWT, usuarios y roles | ✅ |
| S2 | Fuentes RSS, canales, categorías IPTC | ✅ |
| S3 | Alertas CRUD, notificaciones, cron | ✅ |
| S4 | IA generativa: sugerencias y sinónimos (Groq) | ✅ |
| S5 | Motor RSS + matching alertas + notificaciones email | ✅ |
| S6 | Stats/dashboard con métricas reales | ✅ |
| S7 | Tests (72 · 13 archivos · 96%), CI/CD GitHub Actions, documentación | ✅ |
