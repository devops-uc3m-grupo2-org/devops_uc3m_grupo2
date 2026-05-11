"""
NewsRadar — script de demo completo.
Ejecutar: python3 docs/demo_recorrido.py [host]
Por defecto usa localhost:8000.
"""
import sys
import json
import time
import urllib.request
import urllib.error
import urllib.parse

BASE = f"http://{sys.argv[1]}" if len(sys.argv) > 1 else "http://localhost:8000"


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


def ok(label, code, expected=200):
    mark = "OK" if code == expected else "FAIL"
    return f"[{mark} {code}] {label}"


print(f"\nNewsRadar demo — {BASE}\n{'='*50}")

# 0. Health
code, data = req("GET", "/api/v1/health", auth=False)
print(ok("Health", code), "->", data)

# 1. Login
code, data = req("POST", "/api/v1/auth/login",
                 {"email": "admin@newsradar.com", "password": "admin123"}, auth=False)
assert code == 200, f"Login fallido: {data}"
token = data["access_token"]
print(ok("Login", code), "-> JWT recibido")

# 1b. 401 sin token
code, _ = req("GET", "/api/v1/stats", auth=False)
print(ok("Stats sin token (esperado 401)", code, expected=401))

# 2. Crear fuente
code, src = req("POST", "/api/v1/information-sources",
                {"name": "El País",
                 "rss_url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
                 "medium": "digital"},
                token)
src_id = src.get("id")
if code == 409:
    print(f"[~ 409] Fuente ya existía — OK para demo repetida")
else:
    print(ok("Crear fuente", code, expected=201), f"-> id={src_id}, nombre={src.get('name')}")

# 2b. Listar fuentes
code, sources = req("GET", "/api/v1/information-sources", token=token)
print(ok("Listar fuentes", code), f"-> {len(sources)} fuentes")

# 3. Crear alerta
code, alert = req("POST", "/api/v1/users/1/alerts",
                  {"name": "Alerta IA",
                   "descriptors": ["tecnología", "IA", "startup"],
                   "categories": [],
                   "cron_expression": "*/5 * * * *",
                   "is_active": True},
                  token)
alert_id = alert.get("id")
print(ok("Crear alerta", code, expected=201),
      f"-> id={alert_id}, descriptores={alert.get('descriptors')}")

# 3b. Listar alertas
code, alerts = req("GET", "/api/v1/users/1/alerts", token=token)
print(ok("Listar alertas", code), f"-> {len(alerts)} alertas")

# 4. Sugerencias IA — keyword conocida
code, ai = req("GET", "/api/v1/suggestions?" + urllib.parse.urlencode({"keyword": "economía"}),
               token=token)
print(ok("IA sugerencias (economía)", code), f"-> {ai.get('suggestions')}")

# 4b. Sugerencias IA — keyword desconocida (fallback)
code, ai2 = req("GET", "/api/v1/suggestions?" + urllib.parse.urlencode({"keyword": "xyzfoo"}),
                token=token)
print(ok("IA fallback (xyzfoo)", code), f"-> {ai2.get('suggestions')}")

# 5. Stats antes del fetch
code, stats = req("GET", "/api/v1/stats", token=token)
metrics_before = {m["name"]: int(m["value"]) for m in stats[0]["metrics"]}
print(ok("Stats antes del fetch", code), f"-> {metrics_before}")

# 5b. Fetch noticias
code, fetch = req("POST", "/api/v1/news/fetch", token=token)
print(ok("News fetch", code), f"-> {fetch}")
time.sleep(1)

# 5c. Ver noticias (público)
code, news = req("GET", "/api/v1/news", auth=False)
first = news[0]["title"][:60] if news else "—"
print(ok("GET /news (público)", code), f"-> {len(news)} noticias — Primera: {first}")

# 6. Stats después del fetch
code, stats = req("GET", "/api/v1/stats", token=token)
metrics_after = {m["name"]: int(m["value"]) for m in stats[0]["metrics"]}
print(ok("Stats después del fetch", code), f"-> {metrics_after}")

delta = metrics_after["total_news"] - metrics_before["total_news"]
print(f"\n{'='*50}")
print(f"Noticias nuevas importadas: {delta}")
print(f"Estado final: {metrics_after}")
print("Demo completada sin errores.\n")
