# Preguntas típicas de defensa — NewsRadar

## "¿Cómo protegéis la API?"

Todos los endpoints salvo `/health`, `/auth/register`, `/auth/login` y la lectura pública de noticias exigen un JWT en la cabecera `Authorization: Bearer <token>`.

El token se genera en login con **python-jose** (algoritmo HS256, 60 min de expiración) y se valida en cada petición mediante `Depends(get_current_user)` en FastAPI. Si el token es inválido o ha expirado, la API devuelve 401 automáticamente.

Tenemos tests explícitos que verifican ese 401:
- `test_suggestions_requires_auth`
- `test_stats_requires_auth`
- `test_fetch_news_requires_auth`

ADR de referencia: **ADR 0009** (JWT), **ADR 0007** (roles).

---

## "¿Dónde entra la IA en este proyecto?"

El endpoint `GET /api/v1/suggestions?keyword=economía` devuelve términos relacionados que el usuario puede añadir como descriptores a sus alertas.

Implementamos el servicio en `app/services/ai.py` con una arquitectura **desacoplada del proveedor**: la función `generate_synonyms(keyword)` llama a **Groq (Llama 3.3 70B)** en producción y cae a un diccionario IPTC de fallback si la API no está disponible. Cambiar de proveedor implica solo modificar el cuerpo de esa función sin tocar el endpoint ni los tests.

Decidimos usar un **diccionario IPTC propio** en lugar de una API externa por tres razones (ADR 0004):
1. Elimina la dependencia de red en CI — los tests son deterministas y pasan sin claves.
2. Evita gestionar secretos en GitHub Actions.
3. Cero riesgo de bloqueo por rate limits durante la demo.

Para una fase 2, basta con sustituir el cuerpo de `generate_synonyms` por la llamada al SDK elegido.

---

## "¿Cómo sabéis que no habéis roto nada?"

Tenemos **26 tests en pytest** organizados en 8 archivos que cubren todos los sprints:

| Archivo | Qué verifica |
|---|---|
| `test_health.py` | API activa |
| `test_login.py` | Registro, login correcto e incorrecto |
| `test_sources.py` | CRUD fuentes, fetch, duplicados |
| `test_alerts.py` | CRUD alertas y notificaciones con JWT |
| `test_news.py` | Listado público y fetch autenticado |
| `test_ai.py` | `/suggestions` con keyword conocida, desconocida y sin auth |
| `test_stats.py` | Métricas reales, auth requerida, contador sube al crear fuentes |
| `test_monitoring.py` | Pipeline completo: alerta → noticia → AlertNews → notificación |

Se ejecutan en Docker:
```bash
docker compose run --rm app python -m pytest app/tests/ -v
```

GitHub Actions lanza esos tests en cada push a `main`. Los dos workflows (`CI` y `FastAPI CI`) están en verde en el último commit. Si algo se rompe, el pipeline falla antes de que llegue a `main`.

---

## "¿Por qué APScheduler y no Celery?"

Para los requisitos de este proyecto, APScheduler integrado en el proceso FastAPI es suficiente. Celery requiere Redis o RabbitMQ como broker extra en el `docker-compose`, añadiendo dos servicios más sin aportar valor a esta escala.

APScheduler se lanza con `start_scheduler()` en el evento `startup` de FastAPI y ejecuta `fetch_all_sources_job` cada 5 minutos con `max_instances=1` para evitar solapamientos si el fetch tarda más de lo esperado.

Si el proyecto escalase a miles de fuentes o necesitase workers distribuidos, migrar a Celery sería la decisión correcta. Está contemplado en el **ADR 0005**.

---

## "¿Por qué PostgreSQL y no SQLite o MongoDB?"

Necesitábamos relaciones entre entidades (User → Alert → Notification, Source → Channel → NewsItem) con integridad referencial garantizada. PostgreSQL con SQLAlchemy ORM nos da eso y además es el estándar en entornos de producción. SQLite no soporta bien la concurrencia de múltiples conexiones simultáneas y MongoDB complicaría las joins sin aportar ventajas reales dado nuestro modelo relacional.

ADR de referencia: **ADR 0008**.

---

## "¿Qué pasa si una fuente RSS falla o devuelve datos malformados?"

El fetcher (`app/services/fetcher.py`) itera las entradas del feed con `getattr(entry, "link", None)` y omite silenciosamente cualquier entrada sin URL. El scheduler envuelve cada canal en un `try/except` individual, de modo que si un canal falla los demás siguen procesándose. Las noticias duplicadas se detectan por URL única (`NewsItem.link` tiene constraint `unique=True`) y se omiten sin error.

---

## "¿Cómo gestionáis los secretos?"

Las variables sensibles (`SECRET_KEY`, `DATABASE_URL`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`) se leen con `os.getenv()` y tienen valores por defecto para desarrollo local. En producción se pasan como variables de entorno en el `docker-compose` o como secrets en el entorno de despliegue. El `.env` no se sube al repositorio (está en `.gitignore`).

---

## "¿Qué harías diferente si tuvieras más tiempo?"

1. **IA real**: integrar un LLM vía API (Groq es gratuito y rápido) — el punto de extensión ya está preparado en `generate_synonyms`.
2. **Notificaciones push**: el `notify_user` actual solo hace `print`; conectarlo a email o webhook sería el siguiente paso natural.
3. **Autenticación por roles**: el modelo de roles existe en BD pero los endpoints no comprueban si el usuario es `admin` vs `user`; añadir esa capa de autorización completaría el ADR 0007.
4. **Tests de integración E2E**: los actuales usan una BD de test en memoria; añadir un test que levante el stack completo con `docker-compose` y haga peticiones HTTP reales.
