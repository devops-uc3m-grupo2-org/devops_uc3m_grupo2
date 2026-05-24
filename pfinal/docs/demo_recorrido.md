# NewsRadar — Recorrido de demo (probado en vivo)

> **Este documento:** guía paso a paso de la demo para el examen — arranque, endpoints clave, script Python y flujo M1-M5.
> **Ver también:** [`../README.md`](../README.md) · [`inspeccion_manual_swagger.md`](inspeccion_manual_swagger.md) · [`guia_de_respuestas_a_preguntas_tipicas.md`](guia_de_respuestas_a_preguntas_tipicas.md)

Todos los pasos han sido ejecutados y verificados contra `http://192.168.1.172:8000`.
Para la defensa, sustituye esa IP por `localhost` si corres el proyecto en tu máquina.

---

## 0. Levantar el proyecto

```bash
bash pfinal/start.sh
```

Esto hace `docker compose down -v` + rebuild + espera hasta que `/api/v1/health` responda (~2 min). Es el comando correcto para el examen — garantiza BD limpia.

Alternativamente de forma manual:
```bash
docker compose up --build
```

Comprueba que está vivo:

```bash
curl http://localhost:8000/api/v1/health
# → {"status":"ok","message":"NewsRadar listo con PostgreSQL + JWT"}
```

> ⚠️ **Importante:** no usar `--reload` en el Dockerfile (ya eliminado). Con `--reload`, uvicorn reinicia el servidor cada vez que el scheduler escribe en `__pycache__` → conexiones cortadas. Sin él, el servidor es estable.

> ⚠️ **Si `docker compose up --build` falla con** `bind source path does not exist: /run/desktop/mnt/host/wsl/...`: es un builder de buildkit con bind mount de sesión WSL obsoleto. Solución:
> ```bash
> docker buildx ls                  # busca el builder con driver "docker-container"
> docker buildx rm <nombre>         # ejemplo: docker buildx rm eager_ptolemy
> docker compose up --build         # ahora funciona
> ```
> `bash pfinal/start.sh` no tiene este problema porque usa el builder por defecto.

---

## 1. Login — obtener el JWT

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@newsradar.com","password":"admin123"}'
```

Respuesta esperada:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

Guarda el token para usarlo en el resto de pasos:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@newsradar.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### Verificar que sin token devuelve 401

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/stats
# → 401
```

**Qué decir:** *"Todos los endpoints salvo /health y la lectura pública de noticias exigen este JWT. FastAPI valida la firma y la expiración en cada petición."*

---

## 2. Crear una fuente RSS

```bash
curl -s -X POST http://localhost:8000/api/v1/information-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "El País",
    "rss_url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "medium": "digital"
  }'
```

Respuesta esperada (HTTP 201):
```json
{
  "id": 1,
  "name": "El País",
  "rss_url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
  "medium": "digital",
  "iptc_category": null
}
```

También puedes crear una fuente con categoría IPTC:

```bash
curl -s -X POST http://localhost:8000/api/v1/information-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marca",
    "rss_url": "https://e00-marca.uecdn.es/rss/portada.xml",
    "iptc_category": "Deporte"
  }'
```

### Listar fuentes guardadas

```bash
curl -s http://localhost:8000/api/v1/information-sources \
  -H "Authorization: Bearer $TOKEN"
```

**Qué decir:** *"Cada fuente puede tener una categoría IPTC. Cuando se proporciona, el sistema crea automáticamente el canal RSS y la categoría en base de datos."*

---

## 3. Crear una alerta con descriptores

```bash
curl -s -X POST http://localhost:8000/api/v1/users/1/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alerta Tecnología",
    "descriptors": ["tecnología", "IA", "startup"],
    "categories": [],
    "cron_expression": "*/5 * * * *",
    "is_active": true
  }'
```

Respuesta esperada (HTTP 201):
```json
{
  "id": 1,
  "name": "Alerta Tecnología",
  "descriptors": ["tecnología", "IA", "startup"],
  "cron_expression": "*/5 * * * *",
  "user_id": 1,
  "is_active": true
}
```

### Ver alertas del usuario

```bash
curl -s http://localhost:8000/api/v1/users/1/alerts \
  -H "Authorization: Bearer $TOKEN"
```

**Qué decir:** *"Los descriptores son las palabras clave que el motor de matching busca en el título y resumen de cada noticia. Si quiere, puede añadir otro descriptor aquí y veremos cómo afecta al número de coincidencias."*

---

## 4. Sugerencias de IA

```bash
# Keyword conocida — devuelve sinónimos del diccionario IPTC
curl -s --get http://localhost:8000/api/v1/suggestions \
  --data-urlencode "keyword=economía" \
  -H "Authorization: Bearer $TOKEN"
```

Respuesta real con GROQ_API_KEY activa (Llama 3.3 70B, verificado en demo):
```json
{
  "keyword": "economía",
  "suggestions": ["economía", "finanzas", "mercados", "comercio", "industria", "inversión", "crecimiento", "desarrollo", "negocio", "sector"]
}
```

```bash
# Keyword desconocida — Groq genera sugerencias aunque no estén en el diccionario
curl -s --get http://localhost:8000/api/v1/suggestions \
  --data-urlencode "keyword=xyzfoo" \
  -H "Authorization: Bearer $TOKEN"
```

Respuesta real con Groq activo:
```json
{
  "keyword": "xyzfoo",
  "suggestions": ["xyzfoo", "no hay información disponible", "término desconocido", "palabra no reconocida"]
}
```

> **Nota:** si `GROQ_API_KEY` no está en `.env`, cae al fallback Python — `xyzfoo` devolvería `["xyzfoo", "xyzfoo noticias", "xyzfoo actualidad"]`. En CI no se configura la clave, por lo que los tests usan ese fallback y pasan sin dependencia de red.

Keywords verificadas en vivo con Groq: `economía`, `tecnología`, `política`, `salud`, `deporte`, `cultura`, `medioambiente`, `educación`, `sociedad`, `ciencia`.

**Qué decir:** *"El servicio de IA usa Groq con Llama 3.3 70B en producción. El diseño está desacoplado del proveedor: la función generate_synonyms tiene la misma firma independientemente del backend. En CI no se configura GROQ_API_KEY, por lo que los tests usan el diccionario IPTC de fallback y pasan sin dependencia de red. Cambiar de proveedor es modificar solo el cuerpo de esa función."*

---

## 5. Importar noticias (monitorización RSS)

```bash
curl -s -X POST http://localhost:8000/api/v1/news/fetch \
  -H "Authorization: Bearer $TOKEN"
```

Respuesta (varía según cuántos canales haya y cuántas noticias sean nuevas):
```json
{"new_items": 1573}
```

> **Nota:** el fetch itera todos los canales RSS en BD (200+ tras el seed) con límite de 10 noticias por canal. En una BD recién limpiada se importan ~1573 items (verificado en demo real).

### Ver noticias importadas (público, sin auth)

```bash
curl -s http://localhost:8000/api/v1/news | python3 -c "
import sys, json
news = json.load(sys.stdin)
print(f'Total noticias: {len(news)}')
for n in news[:3]:
    print(f'  - {n[\"title\"][:70]}')
"
```

**Qué decir:** *"Este endpoint lo lanzamos a mano, pero en producción APScheduler lo ejecuta automáticamente cada 5 minutos. El scheduler arranca con la aplicación y usa max_instances=1 para evitar solapamientos si el fetch tarda más de lo esperado."*

---

## 6. Ver estadísticas en tiempo real

```bash
curl -s http://localhost:8000/api/v1/stats \
  -H "Authorization: Bearer $TOKEN"
```

Respuesta (los valores dependen del estado de la BD):
```json
[
  {
    "id": 1,
    "metrics": [
      {"name": "total_news",    "value": 33},
      {"name": "total_sources", "value": 15},
      {"name": "total_alerts",  "value": 1}
    ]
  }
]
```

> **Nota:**  incluye las 15 fuentes precargadas por el seed en startup + las que crees en la demo.  es el número de noticias que han hecho **match con las alertas del usuario** (via AlertNews), no el total en BD.

**Qué decir:** *"Los contadores salen directamente de PostgreSQL en cada petición, no de una caché estática. total_news muestra las noticias que han coincidido con mis alertas, no el total importado. Si creamos otra alerta o fuente ahora, el número sube."*

---

## 7. Script Python completo (recorrido de una sola vez)

Para ejecutar todo el flujo sin copiar y pegar paso a paso:

```python
import urllib.request, json, urllib.parse, time

BASE = "http://localhost:8000"

def req(method, path, body=None, token=None, auth=True):
    headers = {"Content-Type": "application/json"}
    if auth and token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body else (b"" if method == "POST" else None),
        headers=headers,
        method=method,
    )
    try:
        res = urllib.request.urlopen(r)
        return res.status, json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

# 0. Health
code, data = req("GET", "/api/v1/health", auth=False)
print(f"[{code}] Health: {data}")

# 1. Login
code, data = req("POST", "/api/v1/auth/login", {"email": "admin@newsradar.com", "password": "admin123"}, auth=False)
token = data["access_token"]
print(f"[{code}] Login OK, token recibido")

# 1b. 401 sin token
code, _ = req("GET", "/api/v1/stats", auth=False)
print(f"[{code}] Stats sin token (esperado 401)")

# 2. Crear fuente
code, src = req("POST", "/api/v1/information-sources",
    {"name": "El País", "rss_url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"},
    token)
print(f"[{code}] Fuente creada: {src.get('name')} (id={src.get('id')})")

# 3. Crear alerta
code, alert = req("POST", "/api/v1/users/1/alerts",
    {"name": "Alerta IA", "descriptors": ["tecnología", "IA"], "categories": [],
     "cron_expression": "*/5 * * * *", "is_active": True},
    token)
print(f"[{code}] Alerta creada: {alert.get('name')} (id={alert.get('id')})")

# 4. Sugerencias IA
code, ai = req("GET", "/api/v1/suggestions?" + urllib.parse.urlencode({"keyword": "economía"}), token=token)
print(f"[{code}] Sugerencias para 'economía': {ai.get('suggestions')}")

# 5. Fetch noticias
code, fetch = req("POST", "/api/v1/news/fetch", token=token)
print(f"[{code}] News fetch: {fetch}")

time.sleep(1)

# 5b. Ver noticias (público)
code, news = req("GET", "/api/v1/news", auth=False)
print(f"[{code}] Noticias importadas: {len(news)}")
if news:
    print(f"       Primera: {news[0]['title'][:60]}")

# 6. Stats
code, stats = req("GET", "/api/v1/stats", token=token)
metrics = {m["name"]: int(m["value"]) for m in stats[0]["metrics"]}
print(f"[{code}] Stats: {metrics}")
```

Ejecución (el script está guardado en `pfinal/docs/demo_recorrido.py`):
```bash
python3 pfinal/docs/demo_recorrido.py
```

---

## Resumen de endpoints de la demo

| Paso | Método | Endpoint | Auth |
|------|--------|----------|------|
| Health | GET | `/api/v1/health` | No |
| Login | POST | `/api/v1/auth/login` | No |
| Crear fuente | POST | `/api/v1/information-sources` | JWT |
| Listar fuentes | GET | `/api/v1/information-sources` | JWT |
| Crear alerta | POST | `/api/v1/users/{id}/alerts` | JWT |
| Ver alertas | GET | `/api/v1/users/{id}/alerts` | JWT |
| Sugerencias IA | GET | `/api/v1/suggestions?keyword=X` | JWT |
| Fetch noticias | POST | `/api/v1/news/fetch` | JWT |
| Ver noticias | GET | `/api/v1/news` | No |
| Estadísticas | GET | `/api/v1/stats` | JWT |

Swagger interactivo: `http://localhost:8000/docs`

---

## 8. Demo M5 — Mock RSS (inspección manual del examen)

El Mock RSS es un servidor Python del verificador que genera noticias sintéticas de forma controlada: 5 en el primer ciclo, 3 en el segundo, 0 en adelante. Permite demostrar el flujo completo sin depender de feeds reales.

**Requisito previo:** arrancar el mock en una terminal aparte (desde `pfinal/devops_verifica-main/`):
```bash
python mock_rss_service.py --port 8100
```

**Ejecutar la demo automatizada:**
```bash
bash pfinal/demo_m5.sh
```

El script crea la fuente, el canal RSS apuntando a `host.docker.internal:8100`, la alerta con descriptor `sintetica` y espera hasta 15 min hasta acumular 8 notificaciones (5 ciclo 1 + 3 ciclo 2).

**Resultado real obtenido (2026-05-21, 360s):**
```
✅ M5 PASADO — 8 notificaciones en 360 segundos
  Canal id=202, 8 noticias en BD (Noticia sintetica 1–8)
```

> ⚠️ Reiniciar el mock (`Ctrl+C` + relanzar) antes de cada repetición para resetear el contador 5→3→0. También hacer `bash pfinal/start.sh` para limpiar la BD.

---

## Orden completo el día del examen (25/05/2026)

```bash
# Terminal 1
bash pfinal/start.sh                    # reset BD + rebuild (~2 min)
bash pfinal/run_verifier.sh --all       # 281 tests (~17 min total: venv + tests)

# Terminal 2 — inspección manual M1-M4
bash pfinal/m1_email_notificacion.sh
bash pfinal/m2_formato_asunto.sh
bash pfinal/m3_registro_verificacion.sh
bash pfinal/m4_expiracion_24h.sh

# Terminal 3 — mock para M5
cd pfinal/devops_verifica-main && python mock_rss_service.py --port 8100

# Terminal 2 — M5
bash pfinal/demo_m5.sh
```
