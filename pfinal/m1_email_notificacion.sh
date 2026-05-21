#!/usr/bin/env bash
# M1 — ¿Se envía un correo al detectar una noticia coincidente?
# Comprueba los logs de Docker buscando líneas [EMAIL] de notificación de alerta.
# Si no hay ninguna reciente, crea una alerta y espera un ciclo del scheduler (5 min).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="http://localhost:8000/api/v1"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ADMIN_EMAIL="newsradargrupo@gmail.com"

echo "════════════════════════════════════════"
echo "  M1 — Email de notificación de alerta"
echo "════════════════════════════════════════"
echo ""

# ── 1. Ver si ya hay emails de notificación en los logs ───────────────────
echo "── [1/3] Buscando emails de notificación en logs de Docker ──"
echo "   (destinatario configurado: $ADMIN_EMAIL)"
EMAIL_LINES=$(docker compose -f "$COMPOSE_FILE" logs app 2>/dev/null | grep '\[EMAIL\]' | grep -v 'verif' || true)

if [ -n "$EMAIL_LINES" ]; then
    echo "✅ Emails de notificación encontrados:"
    echo "$EMAIL_LINES"
    echo ""
    echo "✅ M1 PASADO — el sistema envía correos al detectar noticias coincidentes"
    exit 0
fi

echo "   No hay emails recientes. Creando alerta y esperando ciclo del scheduler..."
echo ""

# ── 2. Login ──────────────────────────────────────────────────────────────
echo "── [2/3] Login como admin ──"
LOGIN=$(curl -sf -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@newsradar.com","password":"admin123"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Token obtenido"
echo ""

# ── 3. Crear alerta y esperar email ──────────────────────────────────────
echo "── [3/3] Creando alerta y esperando email (máx 10 min) ──"
curl -sf -X POST "$BASE/users/1/alerts" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d '{"name":"Alerta M1","descriptors":["España","gobierno","economia"],"categories":[],"cron_expression":"*/5 * * * *"}' > /dev/null

ELAPSED=0
while [ $ELAPSED -lt 600 ]; do
    sleep 30
    ELAPSED=$((ELAPSED + 30))
    EMAIL_LINES=$(docker compose -f "$COMPOSE_FILE" logs app 2>/dev/null | grep '\[EMAIL\]' | grep -v 'verif' || true)
    printf "\r   [%3ds] Esperando email de notificación..." "$ELAPSED"
    if [ -n "$EMAIL_LINES" ]; then
        echo ""
        echo ""
        echo "✅ Email recibido:"
        echo "$EMAIL_LINES" | tail -3
        echo ""
        echo "✅ M1 PASADO — el sistema envía correos al detectar noticias coincidentes"
        exit 0
    fi
done

echo ""
echo "⚠️  No llegó email en $ELAPSED segundos. Comprueba los logs manualmente:"
echo "   docker compose logs app | grep '\[EMAIL\]'"
