#!/usr/bin/env bash
# debug_m5.sh — Diagnóstico completo del mock RSS para M5
#
# Comprueba cada capa del problema descrito en el WhatsApp:
#   1. ¿El mock está corriendo en el host?
#   2. ¿docker-compose.yml tiene extra_hosts?
#   3. ¿host.docker.internal resuelve dentro del contenedor?
#   4. ¿El mock es accesible HTTP desde dentro del contenedor?
#   5. ¿El contador del mock está intacto (no consumido)?
#   6. ¿Hay canales RSS apuntando al mock en la BD?
#   7. ¿El matching de alertas funciona con "sintetica"?
#
# Uso: bash pfinal/debug_m5.sh
# Requisitos: NewsRadar corriendo (bash pfinal/start.sh), mock corriendo en puerto 8100

cd "$(dirname "${BASH_SOURCE[0]}")"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✅  $*${NC}"; }
fail() { echo -e "  ${RED}❌  $*${NC}"; GLOBAL_FAIL=1; }
warn() { echo -e "  ${YELLOW}⚠️   $*${NC}"; }
info() { echo -e "${CYAN}${BOLD}[CHECK] $*${NC}"; }

GLOBAL_FAIL=0
BASE="http://localhost:8000/api/v1"

echo ""
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}   debug_m5.sh — Diagnóstico Mock RSS             ${NC}"
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1 — Mock corriendo en el host (puerto 8100)
# ─────────────────────────────────────────────────────────────────────────────
info "1/7 — Mock RSS accesible desde el host (127.0.0.1:8100)"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8100/openapi.json 2>/dev/null || echo "000")
if [ "$HTTP" = "200" ]; then
    ok "Mock responde en http://127.0.0.1:8100 (HTTP $HTTP)"
else
    fail "Mock NO responde en 127.0.0.1:8100 (HTTP $HTTP)"
    echo ""
    echo "  Arrancar el mock con:"
    echo "    cd pfinal/devops_verifica-main"
    echo "    python mock_rss_service.py --port 8100 --host 0.0.0.0"
    echo ""
    echo "  IMPORTANTE: usar --host 0.0.0.0, NO el default 127.0.0.1"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2 — docker-compose.yml tiene extra_hosts
# ─────────────────────────────────────────────────────────────────────────────
info "2/7 — docker-compose.yml tiene 'extra_hosts: host.docker.internal:host-gateway'"
if grep -q "host.docker.internal:host-gateway" docker-compose.yml 2>/dev/null; then
    ok "extra_hosts encontrado en docker-compose.yml"
    grep -A1 "extra_hosts" docker-compose.yml | sed 's/^/     /'
else
    fail "extra_hosts NO está en docker-compose.yml"
    echo ""
    echo "  Añadir bajo el servicio 'app':"
    echo "    extra_hosts:"
    echo "      - \"host.docker.internal:host-gateway\""
    echo ""
    echo "  Sin esto, host.docker.internal no resuelve en Linux/WSL."
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3 — NewsRadar está levantado
# ─────────────────────────────────────────────────────────────────────────────
info "3/7 — NewsRadar responde en localhost:8000"
HEALTH=$(curl -sf "$BASE/health" 2>/dev/null || echo '{}')
STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
if [ "$STATUS" = "ok" ]; then
    ok "NewsRadar OK — $HEALTH"
else
    fail "NewsRadar NO responde. Ejecutar: bash start.sh"
    echo ""
    GLOBAL_FAIL=1
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4 — DNS: host.docker.internal resuelve DENTRO del contenedor
# ─────────────────────────────────────────────────────────────────────────────
info "4/7 — DNS: host.docker.internal resuelve dentro del contenedor Docker"
DNS_RESULT=$(docker compose exec -T app python3 -c "
import socket
try:
    ip = socket.gethostbyname('host.docker.internal')
    print(f'OK:{ip}')
except Exception as e:
    print(f'FAIL:{e}')
" 2>/dev/null || echo "FAIL:docker exec failed")

if echo "$DNS_RESULT" | grep -q "^OK:"; then
    IP=$(echo "$DNS_RESULT" | cut -d: -f2)
    ok "host.docker.internal → $IP (resuelve correctamente desde el contenedor)"
else
    ERROR=$(echo "$DNS_RESULT" | cut -d: -f2-)
    fail "host.docker.internal NO resuelve desde el contenedor: $ERROR"
    echo ""
    echo "  Causa: falta extra_hosts en docker-compose.yml (ver check 2)"
    echo "  O el contenedor está desactualizado — hacer rebuild: bash start.sh"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5 — HTTP: mock accesible desde DENTRO del contenedor
# ─────────────────────────────────────────────────────────────────────────────
info "5/7 — HTTP: mock accesible desde dentro del contenedor (sin consumir el contador)"
HTTP_DOCKER=$(docker compose exec -T app python3 -c "
import urllib.request, urllib.error
try:
    resp = urllib.request.urlopen('http://host.docker.internal:8100/openapi.json', timeout=5)
    data = resp.read(60).decode()
    print(f'OK:{resp.getcode()}:{data[:40]}')
except urllib.error.URLError as e:
    print(f'FAIL:URLError:{e.reason}')
except Exception as e:
    print(f'FAIL:Exception:{e}')
" 2>/dev/null || echo "FAIL:docker exec failed")

if echo "$HTTP_DOCKER" | grep -q "^OK:"; then
    CODE=$(echo "$HTTP_DOCKER" | cut -d: -f2)
    PREVIEW=$(echo "$HTTP_DOCKER" | cut -d: -f3-)
    ok "Mock accesible desde Docker — HTTP $CODE — $PREVIEW..."
else
    ERROR=$(echo "$HTTP_DOCKER" | cut -d: -f2-)
    fail "Mock NO accesible desde Docker: $ERROR"
    echo ""
    echo "  El contenedor no puede llegar a http://host.docker.internal:8100"
    echo "  Causas posibles:"
    echo "    a) El mock no está corriendo con --host 0.0.0.0"
    echo "    b) host.docker.internal no resuelve (ver check 4)"
    echo "    c) Firewall bloqueando el puerto 8100"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6 — Contador del mock: ¿cuántas llamadas quedan?
# ─────────────────────────────────────────────────────────────────────────────
info "6/7 — Estado del contador del mock (llamadas /rss restantes)"
# Leer el estado sin consumir el contador (usando /openapi.json)
# El mock expone info en sus logs — la única forma de saber el contador
# es leer la respuesta /rss (lo consumiría) o revisar el log del proceso
echo ""
echo "  El mock devuelve: 5 noticias (llamada 1) → 3 (llamada 2) → 0 (resto)"
echo ""
echo "  Estado actual — petición de prueba al endpoint /rss:"
echo "  (esto CONSUME una llamada del contador — solo ejecutar en debug)"
echo ""
read -r -p "  ¿Hacer la petición de prueba a /rss? [s/N]: " CONFIRM_RSS
if [[ "$CONFIRM_RSS" =~ ^[sS]$ ]]; then
    RSS_RESP=$(curl -sf http://127.0.0.1:8100/rss 2>/dev/null || echo "ERROR")
    ITEMS=$(echo "$RSS_RESP" | python3 -c "
import sys
data = sys.stdin.read()
count = data.count('<item>')
print(count)
" 2>/dev/null || echo "?")
    if [ "$ITEMS" = "0" ]; then
        warn "El mock devolvió 0 items — el contador está agotado"
        echo "  Reiniciar el mock: Ctrl+C + python mock_rss_service.py --port 8100 --host 0.0.0.0"
        echo "  Y hacer: bash start.sh (reset BD para evitar deduplicación)"
    elif [ "$ITEMS" = "?" ]; then
        warn "No se pudo parsear la respuesta del mock"
    else
        ok "El mock devolvió $ITEMS items RSS (contador activo)"
    fi
else
    warn "Saltado — el contador NO fue consumido"
    echo "  Para ver el contador actual relanza el mock (Ctrl+C + relanzo) y ejecuta este check"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7 — Canales RSS en BD apuntando al mock
# ─────────────────────────────────────────────────────────────────────────────
info "7/7 — Canales RSS en BD que apuntan al mock (:8100)"

# Login para hacer las peticiones API
TOKEN=$(curl -sf -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@newsradar.com","password":"admin123"}' \
    2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || true)

if [ -z "$TOKEN" ]; then
    fail "No se pudo obtener token de admin — NewsRadar no responde o credenciales incorrectas"
else
    ok "Token admin obtenido"

    # Buscar fuentes con URL del mock
    SOURCES=$(curl -sf "$BASE/information-sources" \
        -H "Authorization: Bearer $TOKEN" 2>/dev/null || echo '[]')
    MOCK_SOURCES=$(echo "$SOURCES" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('items', data)
mocks = [s for s in items if '8100' in str(s.get('url', ''))]
print(len(mocks))
for s in mocks:
    print(f'  Fuente id={s[\"id\"]} url={s.get(\"url\")} name={s.get(\"name\")}')
" 2>/dev/null || echo "0")

    COUNT=$(echo "$MOCK_SOURCES" | head -1)
    if [ "$COUNT" = "0" ]; then
        warn "Ninguna fuente de información apunta a :8100 en la BD"
        echo "  Ejecutar demo_m5.sh para crearla, o crearla manualmente:"
        echo "    POST /api/v1/information-sources"
        echo "    {\"name\":\"Mock RSS Source M5\",\"url\":\"http://host.docker.internal:8100\",\"medium\":\"online\"}"
    else
        ok "Encontrada(s) $COUNT fuente(s) apuntando al mock:"
        echo "$MOCK_SOURCES" | tail -n +2 | sed 's/^/  /'
    fi
    echo ""

    # Buscar canales RSS con URL del mock
    echo "  Canales RSS con URL :8100 en la BD:"
    CHANNELS_RAW=$(curl -sf "$BASE/information-sources" \
        -H "Authorization: Bearer $TOKEN" 2>/dev/null | \
        python3 -c "
import sys, json, urllib.request
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('items', data)
for s in items:
    print(s['id'])
" 2>/dev/null || true)

    FOUND_CHANNEL=0
    while IFS= read -r SID; do
        [ -z "$SID" ] && continue
        CHS=$(curl -sf "$BASE/information-sources/$SID/rss-channels" \
            -H "Authorization: Bearer $TOKEN" 2>/dev/null || echo '[]')
        MOCK_CHS=$(echo "$CHS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('items', data)
mocks = [c for c in items if '8100' in str(c.get('url', ''))]
for c in mocks:
    print(f'  Canal id={c[\"id\"]} url={c.get(\"url\")} category={c.get(\"category_id\")}')
    print(f'  FOUND')
" 2>/dev/null || true)
        if echo "$MOCK_CHS" | grep -q "FOUND"; then
            echo "$MOCK_CHS" | grep -v "^FOUND" | sed 's/^/  /'
            FOUND_CHANNEL=1
        fi
    done <<< "$CHANNELS_RAW"

    if [ "$FOUND_CHANNEL" = "0" ]; then
        warn "Ningún canal RSS con URL :8100 encontrado"
        echo "  El canal debe usar: http://host.docker.internal:8100/rss"
        echo "  (NO usar 127.0.0.1:8100 — esa URL es inaccesible desde Docker)"
    fi
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Bonus — Test de matching de alertLogic con "sintetica"
# ─────────────────────────────────────────────────────────────────────────────
info "Bonus — Test matching alertLogic con descriptor 'sintetica'"
MATCH=$(python3 -c "
import re
descriptor = 'sintetica'
titles = [
    'Noticia sintetica 1',
    'Noticia sintetica 2',
    'Otro titular sin relacion',
    'economia politica gobierno',
]
pattern = re.escape(descriptor.strip().lower())
for title in titles:
    text = title.lower()
    match = bool(re.search(rf'\b{pattern}\b', text, flags=re.UNICODE))
    symbol = '✅' if match else '❌'
    print(f'  {symbol}  \"{title}\" → match={match}')
" 2>/dev/null)

echo "$MATCH"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Resumen
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════${NC}"
if [ "$GLOBAL_FAIL" = "0" ]; then
    echo -e "${GREEN}${BOLD}   DIAGNÓSTICO: TODO OK — M5 debería funcionar    ${NC}"
else
    echo -e "${RED}${BOLD}   DIAGNÓSTICO: HAY PROBLEMAS — revisar los ❌     ${NC}"
    echo ""
    echo "  Checklist de fixes comunes:"
    echo "  1) Arrancar mock con --host 0.0.0.0 (no el default 127.0.0.1)"
    echo "  2) Añadir extra_hosts en docker-compose.yml (para Linux/WSL)"
    echo "  3) Usar http://host.docker.internal:8100/rss en la URL del canal"
    echo "  4) Hacer bash start.sh para resetear la BD (evita deduplicación)"
fi
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════${NC}"
echo ""
