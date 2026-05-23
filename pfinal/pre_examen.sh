#!/usr/bin/env bash
# pre_examen.sh — Comprobación rápida antes del examen (~30 segundos)
# No espera al scheduler — comprueba todo lo que es instantáneo.
#
# Uso: bash pfinal/pre_examen.sh
# Requisito: bash pfinal/start.sh ejecutado antes

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="http://localhost:8000/api/v1"
PASS=0
FAIL=0
WARN=0

ok()   { echo "  ✅  $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌  $1"; FAIL=$((FAIL+1)); }
warn() { echo "  ⚠️   $1"; WARN=$((WARN+1)); }

echo ""
echo "════════════════════════════════════════"
echo "  Pre-examen NewsRadar — check rápido"
echo "════════════════════════════════════════"
echo ""

# ── Docker ───────────────────────────────────────────────────────────────────
echo "── Docker ──"

app_up=$(cd "$SCRIPT_DIR" && docker compose ps 2>/dev/null | grep "app" | grep -i "up\|running" || echo "")
db_up=$(cd "$SCRIPT_DIR" && docker compose ps 2>/dev/null | grep "db\|postgres" | grep -i "up\|running" || echo "")
[ -n "$app_up" ] && ok "Contenedor app: Up" || fail "Contenedor app no está corriendo — ejecuta: bash pfinal/start.sh"
[ -n "$db_up" ]  && ok "Contenedor db: Up"  || fail "Contenedor db no está corriendo — ejecuta: bash pfinal/start.sh"

send_emails=$(grep "^SEND_EMAILS=" "$SCRIPT_DIR/.env" 2>/dev/null | cut -d= -f2 | tr -d ' \r' || echo "no encontrado")
if [ "$send_emails" = "true" ]; then
    ok "SEND_EMAILS=true — emails reales via Gmail SMTP"
else
    warn "SEND_EMAILS=$send_emails — emails simulados (solo log). M1/M2/M3 pasan igualmente"
fi

# ── App ───────────────────────────────────────────────────────────────────────
echo ""
echo "── App ──"

status=$(curl -sf "$BASE/health" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
if [ "$status" != "ok" ]; then
    fail "App no responde en localhost:8000 — ejecuta: bash pfinal/start.sh"
    echo ""
    echo "  Sin app no se puede comprobar nada más. Abortando."
    exit 1
fi
ok "App corriendo en localhost:8000"

TOKEN=$(curl -sf -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@newsradar.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
if [ -z "$TOKEN" ]; then
    fail "Login admin falló — BD en mal estado, ejecuta start.sh"
    exit 1
fi
ok "Login admin OK"
AUTH="Authorization: Bearer $TOKEN"

# ── Seed (datos iniciales) ────────────────────────────────────────────────────
echo ""
echo "── Datos iniciales ──"

nsources=$(curl -sf "$BASE/information-sources" -H "$AUTH" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); items=d.get('items',d) if isinstance(d,dict) else d; print(len(items))" 2>/dev/null || echo "0")
[ "${nsources:-0}" -ge 15 ] \
  && ok "Fuentes de información: $nsources (≥ 15)" \
  || fail "Pocas fuentes: $nsources — ¿ejecutaste start.sh?"

ncats=$(curl -sf "$BASE/categories" -H "$AUTH" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else d.get('total',0))" 2>/dev/null || echo "0")
[ "${ncats:-0}" -ge 16 ] \
  && ok "Categorías IPTC: $ncats (≥ 16)" \
  || fail "Pocas categorías: $ncats — ¿BD reseteada?"

total_channels=0
for id in $(seq 1 "${nsources:-15}"); do
    n=$(curl -s "$BASE/information-sources/$id/rss-channels?limit=300" -H "$AUTH" \
      | python3 -c "import sys,json; d=json.load(sys.stdin); items=d.get('items',d) if isinstance(d,dict) else d; print(len(items))" 2>/dev/null || echo "0")
    total_channels=$((total_channels + n))
done
[ "$total_channels" -ge 100 ] \
  && ok "Canales RSS: $total_channels (≥ 100)" \
  || fail "Canales RSS insuficientes: $total_channels — ¿BD reseteada?"

# ── Seguridad JWT ─────────────────────────────────────────────────────────────
echo ""
echo "── Seguridad y roles ──"

code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/suggestions?keyword=test" 2>/dev/null)
[ "$code" = "401" ] \
  && ok "JWT: endpoint protegido → 401 sin token" \
  || fail "JWT: esperado 401, obtenido $code"

# ── M4: token inválido → 400 ──────────────────────────────────────────────────
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/auth/verify?token=tokenfalso" 2>/dev/null)
[ "$code" = "400" ] \
  && ok "M4: token inválido → HTTP 400" \
  || fail "M4: esperado 400, obtenido $code"

expire=$(grep -o "expires_minutes=1440" "$SCRIPT_DIR/app/main.py" 2>/dev/null | head -1 || echo "")
[ "$expire" = "expires_minutes=1440" ] \
  && ok "M4: expiración = 1440 min (24h) en main.py" \
  || fail "M4: no se encuentra expires_minutes=1440 en main.py"

# ── M3: registro → email en logs ─────────────────────────────────────────────
TS=$(date +%s)
LECTOR_EMAIL="preexamen_${TS}@example.com"
curl -sf -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$LECTOR_EMAIL\",\"password\":\"Test1234!\",\"role\":\"lector\",\"first_name\":\"Pre\",\"last_name\":\"Examen\",\"organization\":\"UC3M\"}" \
  > /dev/null 2>&1 || true
sleep 1

email_log=$(cd "$SCRIPT_DIR" && docker compose logs app --tail=10 2>/dev/null \
  | grep "\[EMAIL\]" | grep -i "verif" | tail -1 || echo "")
[ -n "$email_log" ] \
  && ok "M3: email de verificación aparece en logs" \
  || fail "M3: no aparece [EMAIL]...verifica en logs"

# ── Rol lector → 403 ─────────────────────────────────────────────────────────
LECTOR_TOKEN=$(curl -sf -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$LECTOR_EMAIL\",\"password\":\"Test1234!\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

if [ -n "$LECTOR_TOKEN" ]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/users/999/alerts" \
      -H "Authorization: Bearer $LECTOR_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name":"x","descriptors":["x"],"categories":[],"cron_expression":"* * * * *"}' 2>/dev/null)
    [ "$code" = "403" ] \
      && ok "Rol lector: → 403 al intentar crear alerta" \
      || fail "Rol lector: esperado 403, obtenido $code"
else
    fail "Lector: login falló"
fi

# ── Endpoints funcionales ─────────────────────────────────────────────────────
echo ""
echo "── Endpoints ──"

suggestions=$(curl -s "$BASE/suggestions?keyword=economia" -H "$AUTH" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)" 2>/dev/null || echo "0")
[ "${suggestions:-0}" -gt 0 ] \
  && ok "Sugerencias: $suggestions términos para 'economia'" \
  || warn "Sugerencias vacías — fallback IPTC debería devolver algo"

code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/stats" -H "$AUTH" 2>/dev/null)
[ "$code" = "200" ] && ok "Stats: 200 OK" || fail "Stats: $code"

code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/stats/wordcloud" -H "$AUTH" 2>/dev/null)
[ "$code" = "200" ] && ok "Wordcloud: 200 OK" || fail "Wordcloud: $code"

code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/news" -H "$AUTH" 2>/dev/null)
[ "$code" = "200" ] && ok "News: 200 OK" || fail "News: $code"

# ── Mock RSS ──────────────────────────────────────────────────────────────────
echo ""
echo "── Mock RSS (para M5) ──"

mock=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8100/openapi.json" 2>/dev/null)
[ "$mock" = "200" ] \
  && ok "Mock RSS corriendo en 8100 — listo para M5" \
  || warn "Mock RSS no arrancado (normal si no es M5 aún) — lánzalo con: python pfinal/devops_verifica-main/mock_rss_service.py --port 8100"

# ── Resumen ───────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════"
printf "  ✅  %d OK    ❌  %d FAIL    ⚠️   %d WARN\n" "$PASS" "$FAIL" "$WARN"
echo "════════════════════════════════════════"
if [ "$FAIL" -eq 0 ]; then
    echo "  Todo en orden — listo para el examen"
else
    echo "  $FAIL problema(s) que revisar antes del examen"
fi
echo ""
