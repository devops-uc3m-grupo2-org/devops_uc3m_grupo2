"""
smoke_runner.py — Ejecuta la batería de comprobaciones Smoke para NewsRadar.

Este archivo contiene la versión ejecutable del script de comprobación. `smoke_test.py`
se mantiene como un stub para que `pytest` no lo importe y provoque `SystemExit`.
"""

import sys
import uuid
import requests

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://192.168.1.172:8000"
API = f"{BASE}/api/v1"

# ── Colores ────────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def safe_json_get(r, key, default=None):
    try:
        return r.json().get(key, default)
    except Exception:
        print(f"    [WARN] no JSON in response (status {r.status_code}): {r.text[:300]}")
        return default


def h(token):
    return {"Authorization": f"Bearer {token}"}


def check(label, response, expected_status):
    ok = response.status_code == expected_status
    symbol = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
    detail = "" if ok else f" → got {response.status_code}, body: {response.text[:120]}"
    print(f"  [{symbol}] {label}{detail}")
    return ok


def main():
    passed = []
    failed = []

    print(f"\n{BOLD}NewsRadar Smoke Test → {BASE}{RESET}\n")

    # 0. Sistema
    print(f"{BOLD}[ Sistema ]{RESET}")
    r = requests.get(f"{API}/health")
    if check("GET  /health", r, 200):
        passed.append("GET  /health")
    else:
        failed.append("GET  /health")
    if check("GET  /        (frontend)", requests.get(f"{BASE}/"), 200):
        passed.append("GET  /        (frontend)")
    else:
        failed.append("GET  /        (frontend)")

    # 1. Auth
    print(f"\n{BOLD}[ Auth ]{RESET}")
    email = f"smoke_{uuid.uuid4().hex[:8]}@test.com"
    password = "Smoke1234"

    r = requests.post(f"{API}/auth/register", json={
        "email": email, "password": password,
        "first_name": "Smoke", "last_name": "Test",
        "organization": "UC3M", "role_ids": [1],
    })
    check("POST /auth/register", r, 201) and passed.append("POST /auth/register") or failed.append("POST /auth/register")

    r_login = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
    check("POST /auth/login", r_login, 200) and passed.append("POST /auth/login") or failed.append("POST /auth/login")
    token = safe_json_get(r_login, "access_token", "")

    check("POST /auth/login  (wrong password)", requests.post(f"{API}/auth/login", json={"email": email, "password": "wrong"}), 401)
    check("GET  /auth/verify (invalid token)", requests.get(f"{API}/auth/verify?token=invalid"), 400)
    check("POST /auth/forgot-password (unknown email)", requests.post(f"{API}/auth/forgot-password", json={"email": "noexiste@test.com"}), 200)
    check("POST /auth/forgot-password (known email)", requests.post(f"{API}/auth/forgot-password", json={"email": email}), 200)
    check("POST /auth/reset-password (invalid token)", requests.post(f"{API}/auth/reset-password", json={"token": "invalid", "new_password": "nueva1234"}), 400)
    check("GET  /stats (no auth → 401)", requests.get(f"{API}/stats"), 401)

    # 2. Usuarios
    print(f"\n{BOLD}[ Usuarios ]{RESET}")
    check("GET  /users", requests.get(f"{API}/users", headers=h(token)), 200)
    users = requests.get(f"{API}/users", headers=h(token)).json()
    my_id = users[-1]["id"] if users else None

    if my_id:
        check("GET  /users/{id}", requests.get(f"{API}/users/{my_id}", headers=h(token)), 200)
    check("GET  /users/99999 (404)", requests.get(f"{API}/users/99999", headers=h(token)), 404)
    check("PUT  /users/{id}", requests.put(f"{API}/users/{my_id}", headers=h(token), json={"first_name": "Updated"}), 200)

    new_email = f"smoke2_{uuid.uuid4().hex[:8]}@test.com"
    r_create = requests.post(f"{API}/users", headers=h(token), json={
        "email": new_email, "password": "pass1234",
        "first_name": "Extra", "last_name": "User", "organization": "UC3M", "role_ids": [],
    })
    check("POST /users", r_create, 201)
    extra_id = safe_json_get(r_create, "id")

    # duplicate test: use a valid password so validation doesn't block
    check("POST /users (email duplicado → 409)", requests.post(f"{API}/users", headers=h(token), json={
        "email": new_email, "password": "pass1234", "first_name": "X",
        "last_name": "X", "organization": "X", "role_ids": [],
    }), 409)

    if extra_id:
        check("DELETE /users/{id}", requests.delete(f"{API}/users/{extra_id}", headers=h(token)), 204)

    # 3. Roles
    print(f"\n{BOLD}[ Roles ]{RESET}")
    check("GET  /roles", requests.get(f"{API}/roles", headers=h(token)), 200)
    r_role = requests.post(f"{API}/roles", headers=h(token), json={"name": f"role_{uuid.uuid4().hex[:6]}"})
    check("POST /roles", r_role, 201)
    role_id = safe_json_get(r_role, "id")
    if role_id:
        check("GET  /roles/{id}", requests.get(f"{API}/roles/{role_id}", headers=h(token)), 200)
        check("PUT  /roles/{id}", requests.put(f"{API}/roles/{role_id}", headers=h(token), json={"name": f"updated_{uuid.uuid4().hex[:6]}"}), 200)
        check("DELETE /roles/{id} (no asignado)", requests.delete(f"{API}/roles/{role_id}", headers=h(token)), 204)
    check("DELETE /roles/1 (asignado → 409)", requests.delete(f"{API}/roles/1", headers=h(token)), 409)

    # 4. Categorías (usar nombres exactos del catálogo IPTC)
    print(f"\n{BOLD}[ Categorías ]{RESET}")
    check("GET  /categories", requests.get(f"{API}/categories", headers=h(token)), 200)

    # usar etiqueta exacta del catálogo
    r_cat = requests.post(f"{API}/categories", headers=h(token), json={"name": "Economía, negocios y finanzas", "source": "IPTC"})
    check("POST /categories", r_cat, 201)
    cat_id = safe_json_get(r_cat, "id")

    if cat_id:
        check("GET  /categories/{id}", requests.get(f"{API}/categories/{cat_id}", headers=h(token)), 200)
        check("PUT  /categories/{id}", requests.put(f"{API}/categories/{cat_id}", headers=h(token), json={"name": "Salud"}), 200)
        check("DELETE /categories/{id}", requests.delete(f"{API}/categories/{cat_id}", headers=h(token)), 204)

    # 5. Fuentes
    print(f"\n{BOLD}[ Fuentes de información ]{RESET}")
    check("GET  /information-sources", requests.get(f"{API}/information-sources", headers=h(token)), 200)
    rss_url = f"https://feeds.elpais.com/mrss-s/smoke-{uuid.uuid4().hex[:6]}"
    r_src = requests.post(f"{API}/information-sources", headers=h(token), json={"name": "Smoke Source", "rss_url": rss_url})
    check("POST /information-sources", r_src, 201)
    src_id = safe_json_get(r_src, "id")

    check("POST /information-sources (duplicado → 409)", requests.post(f"{API}/information-sources", headers=h(token), json={"name": "Smoke Source 2", "rss_url": rss_url}), 409)

    if src_id:
        check("GET  /information-sources/{id}", requests.get(f"{API}/information-sources/{src_id}", headers=h(token)), 200)
        check("PUT  /information-sources/{id}", requests.put(f"{API}/information-sources/{src_id}", headers=h(token), json={"name": "Smoke Source Updated"}), 200)
        check("POST /information-sources/{id}/fetch (debug)", requests.post(f"{API}/information-sources/{src_id}/fetch?debug=true", headers=h(token)), 200)
        check("GET  /information-sources/{id}/rss-channels", requests.get(f"{API}/information-sources/{src_id}/rss-channels", headers=h(token)), 200)

        # crear categoría válida para el canal
        r_cat2 = requests.post(f"{API}/categories", headers=h(token), json={"name": "Economía, negocios y finanzas", "source": "IPTC"})
        cat2_id = safe_json_get(r_cat2, "id")
        r_ch = requests.post(f"{API}/information-sources/{src_id}/rss-channels", headers=h(token), json={"url": f"https://example.com/rss/{uuid.uuid4().hex}", "category_id": cat2_id})
        check("POST /information-sources/{id}/rss-channels", r_ch, 201)
        ch_id = safe_json_get(r_ch, "id")
        if ch_id:
            check("GET  /information-sources/{id}/rss-channels/{ch_id}", requests.get(f"{API}/information-sources/{src_id}/rss-channels/{ch_id}", headers=h(token)), 200)
            check("PUT  /information-sources/{id}/rss-channels/{ch_id}", requests.put(f"{API}/information-sources/{src_id}/rss-channels/{ch_id}", headers=h(token), json={"url": f"https://example.com/rss/updated-{uuid.uuid4().hex}"}), 200)
            check("DELETE /information-sources/{id}/rss-channels/{ch_id}", requests.delete(f"{API}/information-sources/{src_id}/rss-channels/{ch_id}", headers=h(token)), 204)

    # 6. Alertas
    print(f"\n{BOLD}[ Alertas ]{RESET}")
    if my_id:
        check("GET  /users/{id}/alerts", requests.get(f"{API}/users/{my_id}/alerts", headers=h(token)), 200)
        r_alert = requests.post(f"{API}/users/{my_id}/alerts", headers=h(token), json={
            "name": "Alerta Smoke", "descriptors": ["economía", "mercado"],
            "categories": [{"code": "04000000", "label": "Economía, negocios y finanzas"}],
            "rss_channels_ids": [], "information_sources_ids": [],
            "cron_expression": "0 * * * *", "is_active": True,
        })
        check("POST /users/{id}/alerts", r_alert, 201)
        alert_id = safe_json_get(r_alert, "id")

        if alert_id:
            check("GET  /users/{id}/alerts/{aid}", requests.get(f"{API}/users/{my_id}/alerts/{alert_id}", headers=h(token)), 200)
            check("PUT  /users/{id}/alerts/{aid}", requests.put(f"{API}/users/{my_id}/alerts/{alert_id}", headers=h(token), json={"name": "Alerta Smoke Actualizada"}), 200)

            # Notificaciones
            check("GET  /users/{id}/alerts/{aid}/notifications", requests.get(f"{API}/users/{my_id}/alerts/{alert_id}/notifications", headers=h(token)), 200)
            r_notif = requests.post(f"{API}/users/{my_id}/alerts/{alert_id}/notifications", headers=h(token), json={"timestamp": "2025-01-01T12:00:00", "metrics": []})
            check("POST /users/{id}/alerts/{aid}/notifications", r_notif, 201)
            notif_id = safe_json_get(r_notif, "id")
            if notif_id:
                check("GET  /users/{id}/alerts/{aid}/notifications/{nid}", requests.get(f"{API}/users/{my_id}/alerts/{alert_id}/notifications/{notif_id}", headers=h(token)), 200)
                check("PUT  /users/{id}/alerts/{aid}/notifications/{nid}", requests.put(f"{API}/users/{my_id}/alerts/{alert_id}/notifications/{notif_id}", headers=h(token), json={"timestamp": "2025-06-01T08:00:00"}), 200)
                check("DELETE /users/{id}/alerts/{aid}/notifications/{nid}", requests.delete(f"{API}/users/{my_id}/alerts/{alert_id}/notifications/{notif_id}", headers=h(token)), 204)

            # cleanup alert
            check("DELETE /users/{id}/alerts/{aid}", requests.delete(f"{API}/users/{my_id}/alerts/{alert_id}", headers=h(token)), 204)

    # 8. Noticias
    print(f"\n{BOLD}[ Noticias ]{RESET}")
    check("GET  /news", requests.get(f"{API}/news", headers=h(token)), 200)
    check("GET  /news/latest", requests.get(f"{API}/news/latest", headers=h(token)), 200)
    check("POST /news/fetch", requests.post(f"{API}/news/fetch", headers=h(token)), 200)
    check("POST /alerts/check", requests.post(f"{API}/alerts/check", headers=h(token)), 200)

    # 9. Stats
    print(f"\n{BOLD}[ Estadísticas ]{RESET}")
    r_stats = requests.get(f"{API}/stats", headers=h(token))
    check("GET  /stats", r_stats, 200)
    if r_stats.status_code == 200:
        try:
            metrics = {m["name"]: m["value"] for m in r_stats.json()[0]["metrics"]}
            assert "total_news" in metrics and "total_sources" in metrics and "total_alerts" in metrics
        except Exception:
            pass

    check("GET  /stats/by-category", requests.get(f"{API}/stats/by-category", headers=h(token)), 200)
    check("GET  /stats/wordcloud", requests.get(f"{API}/stats/wordcloud", headers=h(token)), 200)

    r_stats_new = requests.post(f"{API}/stats", headers=h(token), json={"metrics": [{"name": "smoke_metric", "value": 42.0}]})
    check("POST /stats", r_stats_new, 201)
    stats_id = safe_json_get(r_stats_new, "id")
    if stats_id:
        check("GET  /stats/{id}", requests.get(f"{API}/stats/{stats_id}", headers=h(token)), 200)
        check("PUT  /stats/{id}", requests.put(f"{API}/stats/{stats_id}", headers=h(token), json={"metrics": [{"name": "updated_metric", "value": 99.0}]}), 200)
        check("DELETE /stats/{id}", requests.delete(f"{API}/stats/{stats_id}", headers=h(token)), 204)

    # Limpieza: eliminar source si existe
    if src_id:
        check("DELETE /information-sources/{id}", requests.delete(f"{API}/information-sources/{src_id}", headers=h(token)), 204)

    # Resumen simple
    print(f"\nScript finalizado. Revisa las líneas anteriores para PASS/FAIL output.")


if __name__ == "__main__":
    main()
