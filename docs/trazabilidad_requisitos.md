# Trazabilidad Requisitos ↔ Código

| # | Requisito | Archivo | Función / Clase |
|---|---|---|---|
| 1 | Alertas sobre palabra clave | `app/main.py` | `AlertBase.descriptors`, `create_user_alert` |
| 2 | Sinónimos (3-10) | `app/services/ai.py` | `generate_synonyms()` |
| 3 | Límite 20 alertas por gestor | `app/main.py` | `create_user_alert` (línea con `alert_count >= 20`) |
| 4 | Seleccionar fuentes/canales en alerta | `app/main.py` | `AlertBase.rss_channels_ids`, `AlertBase.information_sources_ids` |
| 5 | Categoría IPTC en alerta | `app/models/models.py` | `IPTCCategoryEnum`, `Alert.categories` |
| 6 | Expresión cron en alerta | `app/main.py` | `AlertBase.cron_expression` |
| 7 | Clasificación noticias por categoría | `app/models/models.py` | `RSSChannel.category_id → Category` |
| 8 | Email al detectar noticia | `app/services/notifications.py` | `notify_alert()` |
| 9 | Buzón interno (Notification) | `app/models/models.py` | `Notification`, `app/main.py` → `create_alert_notification` |
| 10 | Formato título email | `app/services/notifications.py` | `notify_alert()` → `subject = f"Actualización de {alert.name} en {now}"` |
| 11 | Resumen RSS en notificación | `app/services/notifications.py` | `notify_alert()` → `item.summary[:200]` |
| 12 | Alta canales RSS por medio | `app/main.py` | `create_source_channel` |
| 13 | Mínimo 100 canales RSS iniciales | `app/services/seed_rss.py` | `seed_rss_channels()` |
| 14 | 10 medios diferentes | `app/services/seed_rss.py` | `SEED_SOURCES` (10 medios) |
| 15 | Todas las categorías IPTC (17) | `app/services/seed_rss.py` | Canales con las 17 categorías IPTC |
| 16 | Roles Gestor y Lector | `app/main.py` | `create_seed_data()` → roles `admin` y `user` |
| 17 | Lector bloqueado en gestión alertas | `app/main.py` | `require_gestor()` aplicado a POST/PUT/DELETE |
| 18 | Email, nombre, apellidos, org en registro | `app/main.py` | `UserCreate`, `register` |
| 19 | Email verificación en registro | `app/services/notifications.py` | `send_verification_email()` |
| 20 | Enlace verificación caduca en 24h | `app/main.py` | `create_access_token(..., expires_minutes=1440)` |
| 21 | Usuario admin inicial | `app/main.py` | `create_seed_data()` → `admin@newsradar.com` |
| 22 | Nube de palabras por categoría | `app/main.py` | `GET /stats/wordcloud`, `static/app.js` → `loadWordCloud()` |
| 23 | Total noticias en estadísticas | `app/main.py` | `GET /stats` |
| 24 | Alertas desglosadas por categoría | `app/main.py` | `GET /stats/by-category` |
| 25 | Cambio idioma ES/EN | `static/app.js` | `TRANSLATIONS`, `setLanguage()` |
| 26 | API REST completa | `app/main.py` | Todos los endpoints bajo `/api/v1/` |
| 27 | Documentación OpenAPI | `app/main.py` | `custom_openapi()`, Swagger en `/docs` |
| 28 | Endpoint salud | `app/main.py` | `GET /api/v1/health` |
| 29 | Almacenamiento noticias y entidades | `app/models/models.py` | `NewsItem`, `Alert`, `Notification`, `InformationSource` |
| 30 | Código en GitHub | `.github/` | Repositorio `devops_uc3m_grupo2` |
| 31 | Documentación Markdown | `README.md`, `docs/` | README principal + docs/ |
| 32 | ADRs en /docs/adr | `docs/adr/` | 13 ADRs documentados |
| 33 | Diagrama arquitectura | `docs/` | `DiagramaRelacionEntidad.drawio.png` |
| 34 | Pruebas automatizadas | `app/tests/` | 72 tests en 12 archivos |
| 35 | GitHub Actions pipeline | `.github/workflows/tests.yml` | FastAPI CI + CI |
| 36 | Informe cobertura de código | `.github/workflows/tests.yml` | `--cov-report=xml`, artifact `coverage-report` |
| 37 | Despliegue en máquina limpia | `docker-compose.yml` | `docker compose up --build` |
| 38 | Informe cobertura automático | `.github/workflows/tests.yml` | `--cov=app --cov-report=term` |
| 39 | Trazabilidad requisitos ↔ código | `docs/trazabilidad_requisitos.md` | Este documento |
| 40 | Registro de prompts IA | `docs/prompts_ia.md` | Ver documento |
