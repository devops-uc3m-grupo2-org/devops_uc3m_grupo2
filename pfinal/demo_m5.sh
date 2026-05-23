#!/usr/bin/env bash
# demo_m5.sh — Verificación manual M5: indexación de noticias con Mock RSS
#
# Uso:
#   1. Arranca NewsRadar:          bash pfinal/start.sh
#   2. Arranca el mock (otra terminal, dentro de devops_verifica-main/):
#        python mock_rss_service.py --port 8100 --host 0.0.0.0
#        (--host 0.0.0.0 es obligatorio para que el contenedor Docker lo alcance)
#   3. Ejecuta este script:        bash pfinal/demo_m5.sh
#
# Nota sobre el scheduler: el README pide cron "* * * * *" y esperar 2 min.
# Nuestro scheduler interno corre cada 5 min fijos (minute="*/5").
# Este script espera hasta 15 min para asegurar 2 ciclos completos (8 noticias).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="http://localhost:8000/api/v1"
MOCK_LOCAL="http://127.0.0.1:8100/rss"
MOCK_DOCKER="http://host.docker.internal:8100/rss"

# ── Colores ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; exit 1; }

# ── Helper JSON ───────────────────────────────────────────────────────────────
json_field() { echo "$1" | python3 -c "import sys,json; print(json.load(sys.stdin)['$2'])"; }

# ─────────────────────────────────────────────────────────────────────────────
echo "════════════════════════════════════════"
echo "  M5 — Demo Mock RSS NewsRadar"
echo "════════════════════════════════════════"
echo ""

# 0. Comprobar que el mock está corriendo
# IMPORTANTE: usar /openapi.json, NO /rss — llamar a /rss consume una de las 3 llamadas útiles
echo "── [0/5] Comprobando mock RSS en http://127.0.0.1:8100 ──"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8100/openapi.json" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "200" ]; then
    fail "El mock RSS no está corriendo. Arráncalo con:
    cd $SCRIPT_DIR/devops_verifica-main
    python mock_rss_service.py --port 8100"
fi
ok "Mock RSS accesible (contador /rss intacto)"
echo ""

# 0b. Comprobar que NewsRadar está levantado
echo "── [0/5] Comprobando NewsRadar en $BASE/health ──"
HEALTH=$(curl -sf "$BASE/health" 2>/dev/null || echo '{}')
STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || true)
if [ "$STATUS" != "ok" ]; then
    fail "NewsRadar no responde. Arráncalo con: bash $SCRIPT_DIR/start.sh"
fi
ok "NewsRadar OK"
echo ""

# 1. Login
echo "── [1/5] Login como admin ──"
LOGIN=$(curl -sf -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@newsradar.com","password":"admin123"}')
TOKEN=$(json_field "$LOGIN" "access_token")
ok "Token obtenido: ${TOKEN:0:20}..."
echo ""

AUTH_H="Authorization: Bearer $TOKEN"

# 2. Crear fuente de información (si ya existe, reutilizarla)
echo "── [2/5] Creando information source ──"
SOURCE=$(curl -s -X POST "$BASE/information-sources" \
    -H "$AUTH_H" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d '{"name":"Mock RSS Source M5","url":"http://host.docker.internal:8100","medium":"online"}')
SOURCE_ID=$(echo "$SOURCE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id') or d.get('detail',''))" 2>/dev/null || true)
if ! echo "$SOURCE_ID" | grep -qE '^[0-9]+$'; then
    # Ya existe — buscarla por URL en la lista
    SOURCE_ID=$(curl -sf "$BASE/information-sources" -H "$AUTH_H" | \
        python3 -c "import sys,json; sources=json.load(sys.stdin); print(next((s['id'] for s in sources if 'host.docker.internal:8100' in str(s.get('url',''))), ''))")
fi
[ -z "$SOURCE_ID" ] && fail "No se pudo crear ni encontrar la fuente de información"
ok "Fuente — id=$SOURCE_ID"
echo ""

# 3. Crear canal RSS (si ya existe, reutilizarlo)
echo "── [3/5] Creando canal RSS → $MOCK_DOCKER ──"
CHANNEL=$(curl -s -X POST "$BASE/information-sources/$SOURCE_ID/rss-channels" \
    -H "$AUTH_H" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "{\"url\":\"$MOCK_DOCKER\",\"category_id\":13000000}")
CHANNEL_ID=$(echo "$CHANNEL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id') or '')" 2>/dev/null || true)
if ! echo "$CHANNEL_ID" | grep -qE '^[0-9]+$'; then
    CHANNEL_ID=$(curl -sf "$BASE/information-sources/$SOURCE_ID/rss-channels" -H "$AUTH_H" | \
        python3 -c "import sys,json; chs=json.load(sys.stdin); print(next((c['id'] for c in chs if '8100' in str(c.get('url',''))), ''))")
fi
[ -z "$CHANNEL_ID" ] && fail "No se pudo crear ni encontrar el canal RSS"
ok "Canal — id=$CHANNEL_ID"
echo ""

# 4. Crear alerta con descriptor "sintetica"
echo "── [4/5] Creando alerta con descriptor 'sintetica' ──"
# categories espera [{code, label}], no enteros
ALERT=$(curl -s -X POST "$BASE/users/1/alerts" \
    -H "$AUTH_H" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "{
      \"name\": \"Alerta Mock RSS M5\",
      \"descriptors\": [\"sintetica\"],
      \"categories\": [{\"code\": \"13000000\", \"label\": \"Ciencia y tecnología\"}],
      \"rss_channels_ids\": [],
      \"information_sources_ids\": [],
      \"cron_expression\": \"* * * * *\"
    }")
ALERT_ID=$(echo "$ALERT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id') or '')" 2>/dev/null || true)
if ! echo "$ALERT_ID" | grep -qE '^[0-9]+$'; then
    # Ya existe — buscarla por nombre
    ALERT_ID=$(curl -sf "$BASE/users/1/alerts" -H "$AUTH_H" | \
        python3 -c "import sys,json; alerts=json.load(sys.stdin); print(next((a['id'] for a in alerts if a.get('name')=='Alerta Mock RSS M5'), ''))")
fi
[ -z "$ALERT_ID" ] && fail "No se pudo crear ni encontrar la alerta"
ok "Alerta — id=$ALERT_ID"
echo ""

# 5. Esperar 2 ciclos del scheduler y verificar 8 noticias
echo "── [5/5] Esperando 2 ciclos del scheduler para indexar 8 noticias ──"
echo "   El mock devuelve 5 noticias en ciclo 1, 3 en ciclo 2 → total 8"
echo "   El scheduler corre cada 5 min (puede tardar hasta ~12 min)"
echo ""

MAX_WAIT=900   # 15 minutos
ELAPSED=0
NOTIF_COUNT=0

while [ "$NOTIF_COUNT" -lt 8 ] && [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
    sleep 30
    ELAPSED=$((ELAPSED + 30))

    NOTIF_RESP=$(curl -sf "$BASE/users/1/alerts/$ALERT_ID/notifications" \
        -H "$AUTH_H" 2>/dev/null || echo '[]')
    NOTIF_COUNT=$(echo "$NOTIF_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(len(data) if isinstance(data, list) else 0)
" 2>/dev/null || echo 0)

    printf "\r   [%3ds] Notificaciones recibidas: %d/8   " "$ELAPSED" "$NOTIF_COUNT"
done

echo ""
echo ""

if [ "$NOTIF_COUNT" -ge 8 ]; then
    ok "M5 PASADO — $NOTIF_COUNT notificaciones en $ELAPSED segundos"
else
    warn "Solo $NOTIF_COUNT/8 notificaciones tras $ELAPSED segundos"
fi

echo ""
echo "── Detalle de notificaciones ──"
curl -sf "$BASE/users/1/alerts/$ALERT_ID/notifications" \
    -H "$AUTH_H" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if isinstance(data, list):
    for n in data:
        print(f'  id={n[\"id\"]}  timestamp={n[\"timestamp\"]}  alert_id={n[\"alert_id\"]}')
else:
    print(data)
"

echo ""
echo "── Noticias en BD del canal $CHANNEL_ID ──"
curl -sf "$BASE/news" -H "$AUTH_H" | python3 -c "
import sys, json
channel_id = int('$CHANNEL_ID')
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('items', [])
mock = [i for i in items if i.get('channel_id') == channel_id]
print(f'  Noticias del mock: {len(mock)}')
for i in mock[:10]:
    print(f'  id={i[\"id\"]}  title={i[\"title\"]}')
"

echo ""
echo "════════════════════════════════════════"
echo "  Fin demo M5"
echo "════════════════════════════════════════"
