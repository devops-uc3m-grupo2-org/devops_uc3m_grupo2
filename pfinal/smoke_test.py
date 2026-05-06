"""
smoke_test.py — Verifica todos los endpoints de NewsRadar contra la app en ejecución.

Uso:
    python smoke_test.py                        # apunta a http://localhost:8000
    python smoke_test.py http://mi-servidor:8000

Requiere: pip install requests
"""

import sys
import uuid
import requests

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://192.168.1.172:8000"
API = f"{BASE}/api/v1"

# ── Colores ────────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"
RESET = "\033[0m"
BOLD  = "\033[1m"

passed = []
failed = []


def check(label, response, expected_status):
    ok = response.status_code == expected_status
    symbol = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
    detail = "" if ok else f" → got {response.status_code}, body: {response.text[:120]}"
    print(f"  [{symbol}] {label}{detail}")
    (passed if ok else failed).append(label)
    return ok


def auth(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
    return r.json().get("access_token", "")


def h(token):
    return {"Authorization": f"Bearer {token}"}


# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{BOLD}NewsRadar Smoke Test → {BASE}{RESET}\n")

# ── 0. Sin auth ────────────────────────────────────────────────────────────────
print(f"{BOLD}[ Sistema ]{RESET}")
check("GET  /health", requests.get(f"{API}/health"), 200)
check("GET  /        (frontend)", requests.get(f"{BASE}/"), 200)

# ── 1. Auth ────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Auth ]{RESET}")
email = f"smoke_{uuid.uuid4().hex[:8]}@test.com"
password = "Smoke1234"

check("POST /auth/register",
      requests.post(f"{API}/auth/register", json={
          "email": email, "password": password,
          "first_name": "Smoke", "last_name": "Test",
          "organization": "UC3M", "role_ids": [1],
      }), 201)

r_login = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
check("POST /auth/login", r_login, 200)
token = r_login.json().get("access_token", "")

check("POST /auth/login  (wrong password)",
      requests.post(f"{API}/auth/login", json={"email": email, "password": "wrong"}), 401)

check("GET  /auth/verify (invalid token)",
      requests.get(f"{API}/auth/verify?token=invalid"), 400)

check("POST /auth/forgot-password (unknown email)",
      requests.post(f"{API}/auth/forgot-password", json={"email": "noexiste@test.com"}), 200)

check("POST /auth/forgot-password (known email)",
      requests.post(f"{API}/auth/forgot-password", json={"email": email}), 200)

check("POST /auth/reset-password (invalid token)",
      requests.post(f"{API}/auth/reset-password",
                    json={"token": "invalid", "new_password": "nueva1234"}), 400)

check("GET  /stats (no auth → 401)",
      requests.get(f"{API}/stats"), 401)

# ── 2. Usuarios ────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Usuarios ]{RESET}")
check("GET  /users", requests.get(f"{API}/users", headers=h(token)), 200)

users = requests.get(f"{API}/users", headers=h(token)).json()
my_id = users[-1]["id"]

check("GET  /users/{id}", requests.get(f"{API}/users/{my_id}", headers=h(token)), 200)
check("GET  /users/99999 (404)", requests.get(f"{API}/users/99999", headers=h(token)), 404)
check("PUT  /users/{id}", requests.put(f"{API}/users/{my_id}", headers=h(token),
      json={"first_name": "Updated"}), 200)

new_email = f"smoke2_{uuid.uuid4().hex[:8]}@test.com"
r_create = requests.post(f"{API}/users", headers=h(token), json={
    "email": new_email, "password": "pass1234",
    "first_name": "Extra", "last_name": "User", "organization": "UC3M", "role_ids": [],
})
check("POST /users", r_create, 201)
extra_id = r_create.json().get("id")

check("POST /users (email duplicado → 409)",
      requests.post(f"{API}/users", headers=h(token), json={
          "email": new_email, "password": "x", "first_name": "X",
          "last_name": "X", "organization": "X", "role_ids": [],
      }), 409)

if extra_id:
    check("DELETE /users/{id}", requests.delete(f"{API}/users/{extra_id}", headers=h(token)), 204)

# ── 3. Roles ───────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Roles ]{RESET}")
check("GET  /roles", requests.get(f"{API}/roles", headers=h(token)), 200)

r_role = requests.post(f"{API}/roles", headers=h(token), json={"name": f"role_{uuid.uuid4().hex[:6]}"})
check("POST /roles", r_role, 201)
role_id = r_role.json().get("id")

check("GET  /roles/{id}", requests.get(f"{API}/roles/{role_id}", headers=h(token)), 200)
check("GET  /roles/99999 (404)", requests.get(f"{API}/roles/99999", headers=h(token)), 404)
check("PUT  /roles/{id}", requests.put(f"{API}/roles/{role_id}", headers=h(token),
      json={"name": f"updated_{uuid.uuid4().hex[:6]}"}), 200)
check("DELETE /roles/{id} (no asignado)", requests.delete(f"{API}/roles/{role_id}", headers=h(token)), 204)
check("DELETE /roles/1 (asignado → 409)", requests.delete(f"{API}/roles/1", headers=h(token)), 409)

# ── 4. Categorías ─────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Categorías ]{RESET}")
check("GET  /categories", requests.get(f"{API}/categories", headers=h(token)), 200)

r_cat = requests.post(f"{API}/categories", headers=h(token),
                      json={"name": "Política", "source": "IPTC"})
check("POST /categories", r_cat, 201)
cat_id = r_cat.json().get("id")

check("GET  /categories/{id}", requests.get(f"{API}/categories/{cat_id}", headers=h(token)), 200)
check("GET  /categories/99999 (404)", requests.get(f"{API}/categories/99999", headers=h(token)), 404)
check("PUT  /categories/{id}", requests.put(f"{API}/categories/{cat_id}", headers=h(token),
      json={"name": "Salud"}), 200)
check("DELETE /categories/{id}", requests.delete(f"{API}/categories/{cat_id}", headers=h(token)), 204)

# ── 5. Fuentes ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Fuentes de información ]{RESET}")
check("GET  /information-sources", requests.get(f"{API}/information-sources", headers=h(token)), 200)

rss_url = f"https://feeds.elpais.com/mrss-s/smoke-{uuid.uuid4().hex[:6]}"
r_src = requests.post(f"{API}/information-sources", headers=h(token),
                      json={"name": "Smoke Source", "rss_url": rss_url})
check("POST /information-sources", r_src, 201)
src_id = r_src.json().get("id")

check("POST /information-sources (duplicado → 409)",
      requests.post(f"{API}/information-sources", headers=h(token),
                    json={"name": "Smoke Source 2", "rss_url": rss_url}), 409)

if src_id:
    check("GET  /information-sources/{id}",
          requests.get(f"{API}/information-sources/{src_id}", headers=h(token)), 200)
    check("GET  /information-sources/99999 (404)",
          requests.get(f"{API}/information-sources/99999", headers=h(token)), 404)
    check("PUT  /information-sources/{id}",
          requests.put(f"{API}/information-sources/{src_id}", headers=h(token),
                       json={"name": "Smoke Source Updated"}), 200)

check("POST /information-sources/{id}/fetch (debug)",
      requests.post(f"{API}/information-sources/{src_id}/fetch?debug=true", headers=h(token)), 200)

check("GET  /information-sources/{id}/rss-channels",
      requests.get(f"{API}/information-sources/{src_id}/rss-channels", headers=h(token)), 200)

# Canal RSS (necesita una categoría válida)
r_cat2 = requests.post(f"{API}/categories", headers=h(token),
                       json={"name": "Economía, negocios y finanzas", "source": "IPTC"})
cat2_id = r_cat2.json().get("id")
r_ch = requests.post(f"{API}/information-sources/{src_id}/rss-channels", headers=h(token),
                     json={"url": f"https://example.com/rss/{uuid.uuid4().hex}", "category_id": cat2_id})
check("POST /information-sources/{id}/rss-channels", r_ch, 201)
ch_id = r_ch.json().get("id")

if ch_id:
    check("GET  /information-sources/{id}/rss-channels/{ch_id}",
          requests.get(f"{API}/information-sources/{src_id}/rss-channels/{ch_id}", headers=h(token)), 200)
    check("PUT  /information-sources/{id}/rss-channels/{ch_id}",
          requests.put(f"{API}/information-sources/{src_id}/rss-channels/{ch_id}", headers=h(token),
                       json={"url": f"https://example.com/rss/updated-{uuid.uuid4().hex}"}), 200)
    check("DELETE /information-sources/{id}/rss-channels/{ch_id}",
          requests.delete(f"{API}/information-sources/{src_id}/rss-channels/{ch_id}", headers=h(token)), 204)

# ── 6. Alertas ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Alertas ]{RESET}")
check("GET  /users/{id}/alerts", requests.get(f"{API}/users/{my_id}/alerts", headers=h(token)), 200)

r_alert = requests.post(f"{API}/users/{my_id}/alerts", headers=h(token), json={
    "name": "Alerta Smoke", "descriptors": ["economía", "mercado"],
    "categories": [{"code": "04", "label": "Economía"}],
    "rss_channels_ids": [], "information_sources_ids": [],
    "cron_expression": "0 * * * *", "is_active": True,
})
check("POST /users/{id}/alerts", r_alert, 201)
alert_id = r_alert.json().get("id")

check("GET  /users/{id}/alerts/{aid}",
      requests.get(f"{API}/users/{my_id}/alerts/{alert_id}", headers=h(token)), 200)
check("PUT  /users/{id}/alerts/{aid}",
      requests.put(f"{API}/users/{my_id}/alerts/{alert_id}", headers=h(token),
                   json={"name": "Alerta Smoke Actualizada"}), 200)

# ── 7. Notificaciones ──────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Notificaciones ]{RESET}")
check("GET  /users/{id}/alerts/{aid}/notifications",
      requests.get(f"{API}/users/{my_id}/alerts/{alert_id}/notifications", headers=h(token)), 200)

r_notif = requests.post(f"{API}/users/{my_id}/alerts/{alert_id}/notifications", headers=h(token),
                        json={"timestamp": "2025-01-01T12:00:00", "metrics": []})
check("POST /users/{id}/alerts/{aid}/notifications", r_notif, 201)
notif_id = r_notif.json().get("id")

check("GET  /users/{id}/alerts/{aid}/notifications/{nid}",
      requests.get(f"{API}/users/{my_id}/alerts/{alert_id}/notifications/{notif_id}", headers=h(token)), 200)
check("PUT  /users/{id}/alerts/{aid}/notifications/{nid}",
      requests.put(f"{API}/users/{my_id}/alerts/{alert_id}/notifications/{notif_id}", headers=h(token),
                   json={"timestamp": "2025-06-01T08:00:00"}), 200)
check("DELETE /users/{id}/alerts/{aid}/notifications/{nid}",
      requests.delete(f"{API}/users/{my_id}/alerts/{alert_id}/notifications/{notif_id}", headers=h(token)), 204)

# ── 8. Noticias ────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Noticias ]{RESET}")
check("GET  /news", requests.get(f"{API}/news", headers=h(token)), 200)
check("GET  /news/latest", requests.get(f"{API}/news/latest", headers=h(token)), 200)
check("POST /news/fetch", requests.post(f"{API}/news/fetch", headers=h(token)), 200)
check("POST /alerts/check", requests.post(f"{API}/alerts/check", headers=h(token)), 200)

# ── 9. Stats ───────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Estadísticas ]{RESET}")
r_stats = requests.get(f"{API}/stats", headers=h(token))
check("GET  /stats", r_stats, 200)
if r_stats.status_code == 200:
    metrics = {m["name"]: m["value"] for m in r_stats.json()[0]["metrics"]}
    assert "total_news" in metrics and "total_sources" in metrics and "total_alerts" in metrics, \
        "Faltan métricas en /stats"

check("GET  /stats/by-category", requests.get(f"{API}/stats/by-category", headers=h(token)), 200)
check("GET  /stats/wordcloud", requests.get(f"{API}/stats/wordcloud", headers=h(token)), 200)

r_stats_new = requests.post(f"{API}/stats", headers=h(token),
                             json={"metrics": [{"name": "smoke_metric", "value": 42.0}]})
check("POST /stats", r_stats_new, 201)
stats_id = r_stats_new.json().get("id")

if stats_id:
    check("GET  /stats/{id}",
          requests.get(f"{API}/stats/{stats_id}", headers=h(token)), 200)
    check("GET  /stats/99999 (404)",
          requests.get(f"{API}/stats/99999", headers=h(token)), 404)
    check("PUT  /stats/{id}",
          requests.put(f"{API}/stats/{stats_id}", headers=h(token),
                       json={"metrics": [{"name": "updated_metric", "value": 99.0}]}), 200)
    check("DELETE /stats/{id}",
          requests.delete(f"{API}/stats/{stats_id}", headers=h(token)), 204)

# ── 10. IA ─────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ IA / Sugerencias ]{RESET}")
check("GET  /suggestions?keyword=economía",
      requests.get(f"{API}/suggestions?keyword=economía", headers=h(token)), 200)
check("GET  /suggestions?keyword=desconocida",
      requests.get(f"{API}/suggestions?keyword=desconocida", headers=h(token)), 200)

# ── 11. Limpieza ───────────────────────────────────────────────────────────────
print(f"\n{BOLD}[ Limpieza ]{RESET}")
check("DELETE /users/{id}/alerts/{aid}",
      requests.delete(f"{API}/users/{my_id}/alerts/{alert_id}", headers=h(token)), 204)
if src_id:
    check("DELETE /information-sources/{id}",
          requests.delete(f"{API}/information-sources/{src_id}", headers=h(token)), 204)

# ── Resumen ────────────────────────────────────────────────────────────────────
total = len(passed) + len(failed)
print(f"\n{'═'*60}")
print(f"{BOLD}Resultado: {GREEN}{len(passed)} PASS{RESET} / {RED}{len(failed)} FAIL{RESET} / {total} total{RESET}")
if failed:
    print(f"\n{RED}Tests fallidos:{RESET}")
    for f in failed:
        print(f"  ✗ {f}")
else:
    print(f"\n{GREEN}Todos los endpoints responden correctamente.{RESET}")
print(f"{'═'*60}\n")

sys.exit(0 if not failed else 1)
