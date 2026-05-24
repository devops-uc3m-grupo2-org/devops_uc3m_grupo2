# Inspección manual M1-M5 desde Swagger

> **Este documento:** guía paso a paso para verificar M1-M5 desde Swagger UI — verificado el 2026-05-22.
> **Ver también:** [`demo_recorrido.md`](demo_recorrido.md) · [`guia_de_respuestas_a_preguntas_tipicas.md`](guia_de_respuestas_a_preguntas_tipicas.md)

URL Swagger: `http://localhost:8000/docs`

---

## Antes de empezar — arrancar la app

```bash
bash pfinal/start.sh
```

---

## Paso 0 — Autenticarse en Swagger (obligatorio antes de todo)

**`POST /api/v1/auth/login`**
```json
{ "email": "admin@newsradar.com", "password": "admin123" }
```

Respuesta:
```json
{ "access_token": "eyJhbGci...", "token_type": "bearer" }
```

1. Copia el `access_token`.
2. Pulsa **Authorize** (arriba a la derecha en Swagger).
3. Pega el token → **Authorize** → **Close**.

> Si cierras la pestaña sin guardar el token, repite este paso. La BD no se toca.

---

## M1 — ¿Se envía correo al detectar noticia coincidente?

### 1. Comprobar que las fuentes ya existen (el seed las crea)

**`GET /api/v1/information-sources`**

Verás 15 fuentes (El País, El Mundo, ABC…). Anota `id=1` (El País).

> Si intentas crear una fuente que ya existe → 409 Conflict. Usa las del seed directamente.

### 2. Los canales ya existen — no hace falta crearlos

**`GET /api/v1/information-sources/1/rss-channels`**

Verás 10 canales (portada, economía, ciencia…). Ya están listos.

### 3. Crear alerta

**`POST /api/v1/users/1/alerts`**
```json
{
  "name": "Alerta M1",
  "descriptors": ["España", "gobierno", "política"],
  "categories": [],
  "cron_expression": "*/5 * * * *"
}
```

Respuesta:
```json
{ "id": 1, "name": "Alerta M1", "descriptors": ["España", "gobierno", "política"], ... }
```

Anota `alert_id=1`.

### 4. Esperar ~5 min y vigilar los logs en terminal

```bash
docker compose logs app -f | grep -E "FETCH|MATCH|EMAIL"
```

Verás:
```
app-1  | [FETCH] Channel 199: 3 new items
...
app-1  | [EMAIL] Enviado a admin@newsradar.com -> Actualización de Alerta M1 en 22/05/2026 17:35
```

### 5. Comprobar notificaciones en Swagger

**`GET /api/v1/users/1/alerts/1/notifications`**

Respuesta esperada:
```json
[{ "id": 1, "timestamp": "2026-05-22T17:35:35...", "alert_id": 1, "metrics": [{"name": "news_matched", "value": 1}] }]
```

**M1 ✅** — hay notificación + línea `[EMAIL]` en logs.

---

## M2 — ¿El asunto sigue el formato correcto?

No requiere pasos adicionales. Con el email de M1 ya en logs:

```bash
docker compose logs app --tail=20 | grep EMAIL
```

Resultado:
```
app-1  | [EMAIL] Enviado a admin@newsradar.com -> Actualización de Alerta M1 en 22/05/2026 17:35
```

Formato confirmado: `Actualización de [nombre alerta] en [DD/MM/YYYY HH:MM]`

**M2 ✅**

---

## M3 — ¿Se envía correo de verificación al registrar usuario?

### 1. Registrar usuario nuevo

**`POST /api/v1/auth/register`**
```json
{
  "email": "profe_test@example.com",
  "password": "Test1234!",
  "role": "lector",
  "first_name": "Profe",
  "last_name": "Test",
  "organization": "UC3M"
}
```

Respuesta:
```json
{ "id": 1206, "email": "profe_test@example.com", ... }
```

### 2. Verificar en logs

```bash
docker compose logs app --tail=5 | grep EMAIL
```

Resultado:
```
app-1  | [EMAIL] Enviado a profe_test@example.com -> NewsRadar: verifica tu cuenta (válido 24h)
```

**M3 ✅**

---

## M4 — ¿Caduca el enlace de verificación a las 24h?

**`GET /api/v1/auth/verify?token=tokenfalso`**

Respuesta esperada:
```json
{ "detail": "Token expirado o inválido" }
```

HTTP **400 Bad Request** → el sistema rechaza tokens inválidos.

**M4 ✅** — configurado a 1440 min = 24h exactas en `main.py` línea 701.

---

## M5 — ¿Se indexan noticias con el Mock RSS?

### Paso previo — arrancar el mock en otra terminal

```bash
cd pfinal/devops_verifica-main
python mock_rss_service.py --port 8100
```

Espera hasta ver:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8100 (Press CTRL+C to quit)
```

> **IMPORTANTE:** si ves líneas `GET /rss HTTP/1.1" 200 OK` antes de empezar, el contador ya está consumido. Haz Ctrl+C y reinicia el mock — vuelve a empezar en 5→3→0.

### 1. Crear fuente apuntando al mock

**`POST /api/v1/information-sources`**
```json
{
  "name": "Mock RSS Source",
  "url": "http://host.docker.internal:8100",
  "medium": "online"
}
```

Respuesta:
```json
{ "id": 16, "name": "Mock RSS Source", "url": "http://host.docker.internal:8100" }
```

Anota `source_id=16`.

### 2. Crear canal RSS del mock

**`POST /api/v1/information-sources/16/rss-channels`**
```json
{
  "url": "http://host.docker.internal:8100/rss",
  "category_id": "13000000"
}
```

Respuesta:
```json
{ "id": 202, "url": "http://host.docker.internal:8100/rss", "category_id": 13000000, ... }
```

Anota `channel_id=202`.

### 3. Crear alerta con descriptor "sintetica"

**`POST /api/v1/users/1/alerts`**
```json
{
  "name": "Alerta Mock RSS",
  "descriptors": ["sintetica", "noticia", "prueba"],
  "categories": [{"code": "13000000", "label": "Ciencia y tecnología"}],
  "cron_expression": "*/5 * * * *"
}
```

Respuesta:
```json
{ "id": 2, "name": "Alerta Mock RSS", "descriptors": ["sintetica", "noticia", "prueba"], ... }
```

Anota `alert_id=2`.

### 4. Vigilar los logs mientras esperas 2 ciclos (~10 min)

```bash
docker compose logs app -f | grep -E "FETCH|MATCH|EMAIL"
```

**Ciclo 1** (~5 min):
```
app-1  | [FETCH] Channel 202: 5 new items
app-1  | [EMAIL] Enviado a admin@newsradar.com -> Actualización de Alerta Mock RSS en 22/05/2026 17:45
```

**Ciclo 2** (~5 min después):
```
app-1  | [FETCH] Channel 202: 3 new items
app-1  | [EMAIL] Enviado a admin@newsradar.com -> Actualización de Alerta Mock RSS en 22/05/2026 17:50
```

### 5. Comprobar 8 notificaciones en Swagger

**`GET /api/v1/users/1/alerts/2/notifications`**

Deben aparecer 8 notificaciones: 5 del ciclo 1 + 3 del ciclo 2.

```json
[
  { "id": 5,  "timestamp": "2026-05-22T17:45:57...", "alert_id": 2, ... },
  { "id": 6,  "timestamp": "2026-05-22T17:45:57...", "alert_id": 2, ... },
  { "id": 7,  "timestamp": "2026-05-22T17:45:57...", "alert_id": 2, ... },
  { "id": 8,  "timestamp": "2026-05-22T17:45:57...", "alert_id": 2, ... },
  { "id": 9,  "timestamp": "2026-05-22T17:45:57...", "alert_id": 2, ... },
  { "id": 12, "timestamp": "2026-05-22T17:50:47...", "alert_id": 2, ... },
  { "id": 13, "timestamp": "2026-05-22T17:50:47...", "alert_id": 2, ... },
  { "id": 14, "timestamp": "2026-05-22T17:50:47...", "alert_id": 2, ... }
]
```

**M5 ✅ — 8/8 notificaciones en 2 ciclos.**

### 6. Bonus — nube de palabras

Abre `http://localhost:8000` → Dashboard → selecciona categoría **Ciencia y tecnología**.

Aparecen: `noticia`, `sintetica`, `resumen`, `sintetico`, `pruebas`.

---

## Resumen final

| Caso | Endpoint clave                                  | Tiempo      | Resultado UC3M     |
| ---- | ----------------------------------------------- | ----------- | ------------------ |
| M1   | `POST /users/1/alerts` + esperar scheduler      | ~5-10 min   | ✅ 17:35            |
| M2   | logs Docker                                     | instantáneo | ✅ formato correcto |
| M3   | `POST /auth/register` + logs                    | instantáneo | ✅ 17:38            |
| M4   | `GET /auth/verify?token=falso`                  | instantáneo | ✅ HTTP 400         |
| M5   | fuente + canal + alerta mock + esperar 2 ciclos | ~10-12 min  | ✅ 8/8 notif        |

> La nube de palabras **no usa IA** — es conteo de frecuencia de palabras de las noticias matcheadas.
> La IA (Groq Llama 3.3 70B) solo se usa en `GET /api/v1/suggestions?keyword=...`.
