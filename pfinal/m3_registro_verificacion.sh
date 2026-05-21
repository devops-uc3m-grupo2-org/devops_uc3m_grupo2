#!/usr/bin/env bash
# M3 — ¿Se envía un correo de verificación al registrar un usuario?
# Registra un usuario de prueba y comprueba en los logs que se envió el email.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="http://localhost:8000/api/v1"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
TIMESTAMP=$(date +%s)
TEST_EMAIL="m3_prueba_${TIMESTAMP}@example.com"

echo "════════════════════════════════════════"
echo "  M3 — Correo de verificación al registrar"
echo "════════════════════════════════════════"
echo ""

# ── 1. Login como admin para poder registrar ──────────────────────────────
echo "── [1/3] Login como admin ──"
LOGIN=$(curl -sf -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@newsradar.com","password":"admin123"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Token obtenido"
echo ""

# ── 2. Registrar usuario de prueba ────────────────────────────────────────
echo "── [2/3] Registrando usuario de prueba: $TEST_EMAIL ──"
REGISTER=$(curl -sf -X POST "$BASE/auth/register" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test1234!\",\"role\":\"gestor\",\"first_name\":\"Profe\",\"last_name\":\"Test\",\"organization\":\"UC3M\"}")
USER_ID=$(echo "$REGISTER" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "✅ Usuario creado — id=$USER_ID email=$TEST_EMAIL"
echo ""

# ── 3. Comprobar email en logs ────────────────────────────────────────────
echo "── [3/3] Comprobando email de verificación en logs ──"
sleep 3
EMAIL_VERIF=$(docker compose -f "$COMPOSE_FILE" logs app 2>/dev/null | grep '\[EMAIL\]' | grep -i 'verif' || true)

if [ -n "$EMAIL_VERIF" ]; then
    echo "$EMAIL_VERIF" | tail -5
    echo ""
    echo "✅ M3 PASADO — se envía correo de verificación al registrar un usuario"
else
    echo "⚠️  No se encontró línea de email de verificación en los logs."
    echo "   Comprueba que SEND_EMAILS=true en .env"
    echo ""
    echo "   Todos los emails en logs:"
    docker compose -f "$COMPOSE_FILE" logs app 2>/dev/null | grep '\[EMAIL\]' | tail -5 || echo "   (ninguno)"
fi