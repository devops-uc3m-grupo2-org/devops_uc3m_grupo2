#!/usr/bin/env bash
# M2 — ¿El asunto del correo sigue el formato "Actualización de [alerta] en [DD/MM/YYYY HH:MM]"?
# Lee los logs de Docker. Si no hay emails aún, espera un ciclo del scheduler (igual que M1).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="http://localhost:8000/api/v1"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

echo "════════════════════════════════════════"
echo "  M2 — Formato del asunto del correo"
echo "════════════════════════════════════════"
echo ""
echo "Formato esperado: «Actualización de [nombre alerta] en [DD/MM/YYYY HH:MM]»"
echo ""

# ── 1. Ver si ya hay emails en los logs ──────────────────────────────────────
echo "── [1/2] Buscando emails de notificación en logs de Docker ──"
EMAIL_LINES=$(docker compose -f "$COMPOSE_FILE" logs app 2>/dev/null | grep '\[EMAIL\]' | grep -v 'verif' || true)

if [ -z "$EMAIL_LINES" ]; then
    echo "   No hay emails en logs. Creando alerta y esperando ciclo del scheduler..."
    echo ""

    # Login
    LOGIN=$(curl -sf -X POST "$BASE/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@newsradar.com","password":"admin123"}')
    TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

    # Crear alerta (idempotente: si ya existe, ignorar el error)
    curl -s -X POST "$BASE/users/1/alerts" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json; charset=utf-8" \
        -d '{"name":"Alerta M2","descriptors":["España","gobierno","economia"],"categories":[],"cron_expression":"*/5 * * * *"}' > /dev/null || true

    echo "── [2/2] Esperando email (máx 10 min) ──"
    ELAPSED=0
    while [ $ELAPSED -lt 600 ]; do
        sleep 30
        ELAPSED=$((ELAPSED + 30))
        EMAIL_LINES=$(docker compose -f "$COMPOSE_FILE" logs app 2>/dev/null | grep '\[EMAIL\]' | grep -v 'verif' || true)
        printf "\r   [%3ds] Esperando email de notificación..." "$ELAPSED"
        if [ -n "$EMAIL_LINES" ]; then
            echo ""
            break
        fi
    done

    if [ -z "$EMAIL_LINES" ]; then
        echo ""
        echo "⚠️  No llegó email en $ELAPSED segundos. Comprueba los logs manualmente:"
        echo "   docker compose logs app | grep '[EMAIL]'"
        exit 1
    fi
else
    echo "── [2/2] Verificando formato ──"
fi

echo ""
echo "Emails encontrados:"
echo "$EMAIL_LINES"
echo ""

# ── 2. Verificar formato ─────────────────────────────────────────────────────
if echo "$EMAIL_LINES" | grep -q "Actualización de .* en "; then
    echo "✅ M2 PASADO — el asunto sigue el formato «Actualización de [alerta] en [día/hora]»"
else
    echo "❌ El asunto no coincide con el formato esperado"
    exit 1
fi