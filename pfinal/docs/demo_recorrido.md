# NewsRadar — Recorrido de demo (probado en vivo)

Todos los pasos han sido ejecutados y verificados contra `http://192.168.1.172:8000`.
Para la defensa, sustituye esa IP por `localhost` si corres el proyecto en tu máquina.

---

## 0. Levantar el proyecto

```bash
docker compose up --build
```

Espera hasta ver en los logs:
```
INFO:     Application startup complete.
```

Comprueba que está vivo:

```bash
curl http://localhost:8000/api/v1/health
# → {"status":"ok","message":"NewsRadar listo con PostgreSQL + JWT"}
```

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

Respuesta esperada:
```json
{
  "keyword": "economía",
  "suggestions": ["economía", "finanzas", "bolsa", "mercado", "negocios", "inversión"]
}
```

```bash
# Keyword desconocida — devuelve fallback genérico
curl -s --get http://localhost:8000/api/v1/suggestions \
  --data-urlencode "keyword=xyzfoo" \
  -H "Authorization: Bearer $TOKEN"
```

Respuesta esperada:
```json
{
  "keyword": "xyzfoo",
  "suggestions": ["xyzfoo", "xyzfoo noticias", "xyzfoo actualidad"]
}
```

Keywords verificadas en vivo: `economía`, `tecnología`, `política`, `salud`.
Disponibles también: `deporte`, `cultura`, `medioambiente`, `educación`, `sociedad`, `ciencia`.

**Qué decir:** *"El servicio de IA usa Groq con Llama 3.3 70B en producción. El diseño está desacoplado del proveedor: la función generate_synonyms tiene la misma firma independientemente del backend. En CI no se configura GROQ_API_KEY, por lo que los tests usan el diccionario IPTC de fallback y pasan sin dependencia de red. Cambiar de proveedor es modificar solo el cuerpo de esa función."*

---

## 5. Importar noticias (monitorización RSS)

```bash
curl -s -X POST http://localhost:8000/api/v1/news/fetch \
  -H "Authorization: Bearer $TOKEN"
```

Respuesta esperada:
```json
{"new_items": 10}
```

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

Respuesta esperada tras los pasos anteriores:
```json
[
  {
    "id": 1,
    "metrics": [
      {"name": "total_news",    "value": 10},
      {"name": "total_sources", "value": 2},
      {"name": "total_alerts",  "value": 1}
    ]
  }
]
```

**Qué decir:** *"Los contadores salen directamente de PostgreSQL en cada petición, no de una caché estática. Si creamos otra fuente o alerta ahora, el número sube."*

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

Ejecución (el script está guardado en `docs/demo_recorrido.py`):
```bash
python3 docs/demo_recorrido.py
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
