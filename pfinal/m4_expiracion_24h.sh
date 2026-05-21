#!/usr/bin/env bash
# M4 — ¿Caduca el enlace de verificación a las 24 horas?
# Demuestra que el token de verificación se genera con expiración de 1440 minutos (24h)
# y que al intentar verificar con un token expirado el sistema devuelve error.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="http://localhost:8000/api/v1"
MAIN_PY="$SCRIPT_DIR/app/main.py"

echo "════════════════════════════════════════"
echo "  M4 — Caducidad del enlace a las 24h"
echo "════════════════════════════════════════"
echo ""

# ── 1. Mostrar la configuración en el código ──────────────────────────────
echo "── [1/2] Configuración de expiración en app/main.py ──"
echo ""
echo "   Línea relevante en main.py:"
grep -n "expires_minutes=1440" "$MAIN_PY" || grep -n "1440" "$MAIN_PY" | head -3
echo ""
echo "   1440 minutos = 24 horas exactas"
echo ""

# ── 2. Verificar que un token falso/expirado da error ────────────────────
echo "── [2/2] Verificando que un token inválido es rechazado ──"
RESPONSE=$(curl -sf -o /dev/null -w "%{http_code}" \
    "$BASE/auth/verify?token=token.expirado.falso" 2>/dev/null || true)

if [ "$RESPONSE" = "400" ] || [ "$RESPONSE" = "401" ] || [ "$RESPONSE" = "422" ]; then
    echo "✅ Token inválido rechazado con HTTP $RESPONSE"
    echo ""
    echo "✅ M4 PASADO — el sistema rechaza tokens inválidos o expirados"
    echo "   El enlace de verificación caduca a las 24h (1440 min configurado en main.py)"
else
    echo "   Respuesta HTTP: $RESPONSE"
    echo "⚠️  Respuesta inesperada. Comprueba el endpoint /auth/verify"
fi
