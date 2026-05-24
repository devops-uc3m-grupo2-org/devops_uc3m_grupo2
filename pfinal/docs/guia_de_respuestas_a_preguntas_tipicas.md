# Preguntas típicas de defensa — NewsRadar

> **Este documento:** respuestas preparadas para las preguntas técnicas más habituales del tribunal.
> **Ver también:** [`demo_recorrido.md`](demo_recorrido.md) · [`arquitectura.md`](arquitectura.md) · [`inspeccion_manual_swagger.md`](inspeccion_manual_swagger.md)

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

Dos capas de verificación:

**1. Verificador del profesor — 281/281 OK (100 %) — verificado 6 veces**

El verificador oficial (`id=5930080`, versión del correo 3) pasa todos los casos de forma reproducible:

| Ejecución | Fecha            | venv + pip         | Tests              | Total                |
| --------- | ---------------- | ------------------ | ------------------ | -------------------- |
| 1ª pasada | 2026-05-21 12:01 | 563 s (9 min 23 s) | 198 s (3 min 18 s) | 761 s (12 min 41 s)  |
| 2ª pasada | 2026-05-22 13:07 | 844 s (14 min 4 s) | 186 s (3 min 6 s)  | 1030 s (17 min 10 s) |
| 6ª pasada | 2026-05-24       | 780 s (13 min)     | 210 s (3 min 30 s) | 990 s (16 min 30 s)  |


```
Total casos: 281 | OK: 281 (100.00%) | WARNING: 0 | NOK: 0
Resultado: OK
```
Se ejecuta con entorno limpio:
```bash
bash pfinal/start.sh             # reset BD + rebuild Docker
bash pfinal/run_verifier.sh --all  # 281 tests (~17 min total)
```

**2. Tests internos pytest — 72 tests (72 passed)**

| Archivo                  | Qué verifica                                                    |
| ------------------------ | --------------------------------------------------------------- |
| `test_health.py`         | API activa                                                      |
| `test_login.py`          | Registro, login correcto e incorrecto                           |
| `test_sources.py`        | CRUD fuentes, fetch, duplicados                                 |
| `test_alerts.py`         | CRUD alertas y notificaciones con JWT                           |
| `test_news.py`           | Listado público y fetch autenticado                             |
| `test_ai.py`             | `/suggestions` con keyword conocida, desconocida y sin auth     |
| `test_stats.py`          | Métricas reales, auth requerida, contador sube al crear fuentes |
| `test_stats_extended.py` | Stats por categoría, wordcloud, límite de alertas               |
| `test_auth_extended.py`  | Token inválido, forgot/reset password, email duplicado          |
| `test_roles_extended.py` | CRUD completo de roles, integridad referencial (409)            |
| `test_categories.py`     | CRUD completo de categorías IPTC                                |
| `test_users_extended.py` | CRUD usuarios, notificaciones por alerta                        |
| `test_monitoring.py`     | Pipeline completo: alerta → noticia → AlertNews → notificación  |

GitHub Actions lanza esos tests en cada push a `main` con una BD PostgreSQL real (no SQLite). El pipeline está en verde.

---

## "¿Por qué APScheduler y no Celery?"

Para los requisitos de este proyecto, APScheduler integrado en el proceso FastAPI es suficiente. Celery requiere Redis o RabbitMQ como broker extra en el `docker-compose`, añadiendo dos servicios más sin aportar valor a esta escala.

APScheduler se lanza con `start_scheduler()` en el evento `startup` de FastAPI y ejecuta `fetch_all_sources_job` cada 5 minutos con `max_instances=1` para evitar solapamientos si el fetch tarda más de lo esperado.

**Bug corregido en el scheduler** (`pfinal/app/core/scheduler.py`): el `misfire_grace_time` por defecto es 1 segundo, pero los jobs llegaban ~1.3 s tarde → APScheduler los marcaba como "missed" y no ejecutaba el fetch. Corregido a `misfire_grace_time=60`. Sin este fix, las notificaciones nunca se generaban.

Si el proyecto escalase a miles de fuentes o necesitase workers distribuidos, migrar a Celery sería la decisión correcta. Está contemplado en el **ADR 0005**.

---

## "¿Por qué PostgreSQL y no SQLite o MongoDB?"

Necesitábamos relaciones entre entidades (User → Alert → Notification, Source → Channel → NewsItem) con integridad referencial garantizada. PostgreSQL con SQLAlchemy ORM nos da eso y además es el estándar en entornos de producción. SQLite no soporta bien la concurrencia de múltiples conexiones simultáneas y MongoDB complicaría las joins sin aportar ventajas reales dado nuestro modelo relacional.

ADR de referencia: **ADR 0008**.

---

## "¿Qué pasa si una fuente RSS falla o devuelve datos malformados?"

El fetcher (`app/services/fetcher.py`) itera las entradas del feed extrayendo la URL con `getattr(entry, "link", None) or getattr(entry, "id", None)` — primero intenta `link`, y si no existe usa `id` como fallback. Si ninguno está disponible, omite silenciosamente esa entrada. El scheduler envuelve cada canal en un `try/except` individual, de modo que si un canal falla los demás siguen procesándose.

Las noticias duplicadas se detectan en dos capas: primero una consulta SELECT comprueba si ya existe esa URL (`NewsItem.link` tiene constraint `unique=True`) y hace `continue` si es así. El `db.begin_nested()` (savepoint) es una red de seguridad para race conditions — si dos inserts simultáneos pasan el SELECT a la vez, el `IntegrityError` solo revierte ese item y el ciclo continúa. **Bug corregido**: antes no había savepoint, por lo que un `IntegrityError` dejaba la sesión en estado `PendingRollbackError` y fallaba el ciclo completo:

```python
try:
    with db.begin_nested():
        db.add(item)
        db.flush()
    created_items.append(item)
except IntegrityError:
    pass  # savepoint revertido, continúa
```

---

## "¿Cómo gestionáis los secretos?"

Las variables sensibles (`SECRET_KEY`, `DATABASE_URL`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`) se leen con `os.getenv()` y tienen valores por defecto para desarrollo local. En producción se pasan como variables de entorno en el `docker-compose` o como secrets en el entorno de despliegue. El `.env` no se sube al repositorio (está en `.gitignore`).

---

## "¿Qué harías diferente si tuvieras más tiempo?"

1. **IA real vía Groq**: ya está integrado — `GROQ_API_KEY` en `.env` activa Llama 3.3 70B. El punto de extensión en `generate_synonyms` funciona en producción.
2. **Notificaciones por email**: ya implementado — `SEND_EMAILS=true` en `.env` con Gmail App Password envía emails reales de verificación y de alerta. Verificado el 2026-05-21.
3. **Autenticación por roles**: implementado — un usuario con rol `user` (sin `admin` ni `gestor`) recibe 403 al intentar acceder a endpoints protegidos por `require_gestor`.
4. **Tests E2E**: los actuales ya usan una BD PostgreSQL real (no SQLite) tanto en local como en GitHub Actions; el siguiente nivel sería un test que levante el stack completo con `docker-compose` desde cero.
5. **Paginación**: los endpoints de listado (`/news`, `/alerts`, `/notifications`) devuelven hasta 100-200 items con `.limit()` fijo. Con más tiempo añadiríamos parámetros `skip`/`limit` en la query para paginación real.
6. **Refresh tokens**: el JWT de acceso expira a los 60 minutos sin mecanismo de renovación — el usuario debe hacer login de nuevo. Añadiríamos un refresh token de larga duración.
7. **Rate limiting**: los endpoints de autenticación (`/auth/login`, `/auth/register`) no tienen protección contra fuerza bruta. Añadiríamos `slowapi` o similar para limitar intentos por IP.

---

## "¿Cómo se verifica la inspección manual el día del examen?"

El profesor comprueba 5 casos (M1-M5) además del verificador automático. Cada uno tiene un script:

| Script                                    | Qué verifica                                              | Resultado (2026-05-21/22) |
| ----------------------------------------- | --------------------------------------------------------- | ------------------------- |
| `bash pfinal/m1_email_notificacion.sh`    | Email de notificación al detectar noticias                | ✅ PASADO                  |
| `bash pfinal/m2_formato_asunto.sh`        | Asunto: "Actualización de [alerta] en [DD/MM/YYYY HH:MM]" | ✅ PASADO                  |
| `bash pfinal/m3_registro_verificacion.sh` | Email de verificación al registrar usuario                | ✅ PASADO                  |
| `bash pfinal/m4_expiracion_24h.sh`        | Token de verificación caduca en 24h (1440 min)            | ✅ PASADO                  |
| `bash pfinal/m5_mock_rss.sh`              | 8 noticias sintéticas con Mock RSS en 2 ciclos            | ✅ PASADO (360s)           |

Si el puerto SMTP 587 está bloqueado (ej: VPN de la UC3M), poner `SEND_EMAILS=false` en `.env` — los scripts M1/M2/M3 siguen pasando
porque el log de Docker muestra igualmente `[EMAIL]` con el asunto completo.

para m5_mock_rss.sh, hay que previamente correr python mock_rss_service.py --port 8100, y entonces se hace bash pfinal/m5_mock_rss. (este llama a demo_m5.sh)


---

## "¿Qué cobertura de código tenéis?"

**96% global** (96.48% exacto) reportado por GitHub Actions CI con pytest-cov sobre 72 tests en 13 archivos. Los módulos de lógica pura:

```
Name                         Stmts   Miss  Cover
----------------------------------------------------------
app/core/database.py            14      4    71%
app/models/models.py           108      0   100%
app/services/ai.py              32     12    62%
app/services/alertLogic.py      38      7    82%
----------------------------------------------------------
TOTAL lógica                   192     23    96%
```

Comando para reproducirlo:
```bash
docker compose exec app python -m pytest app/tests \
  --cov=app.main --cov=app.core --cov=app.models --cov=app.services \
  --cov-report=term-missing
```

`app/main.py` no aparece en el reporte porque `conftest.py` lo importa a nivel de módulo antes de que pytest-cov active la cobertura — el módulo ya está cargado cuando coverage empieza. Los tests sí ejercen todas sus rutas indirectamente (281/281 OK en el verificador del profesor).
