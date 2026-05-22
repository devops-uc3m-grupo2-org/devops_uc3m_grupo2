#!/usr/bin/env bash
# check_conexion.sh — Simulacro de conexión en la universidad
# Ejecutar ANTES de start.sh para detectar problemas de red.

set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; }

echo "════════════════════════════════════════"
echo "  Simulacro de conexión — Universidad"
echo "════════════════════════════════════════"
echo ""

# ── 1. IP actual de la máquina ───────────────────────────────────────────────
echo "── [1/5] IP de esta máquina ──"
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ip route get 1 2>/dev/null | awk '{print $7; exit}' || echo "desconocida")
echo "   IP local: $IP"
echo "   El verificador usa http://localhost:8000 (sin importar la IP)"
echo ""

# ── 2. Docker Desktop corriendo ──────────────────────────────────────────────
echo "── [2/5] Docker Desktop ──"
if docker info > /dev/null 2>&1; then
    ok "Docker está corriendo"
else
    fail "Docker no responde — abre Docker Desktop primero"
    exit 1
fi
echo ""

# ── 3. NewsRadar responde ────────────────────────────────────────────────────
echo "── [3/5] NewsRadar en localhost:8000 ──"
STATUS=$(curl -sf "http://localhost:8000/api/v1/health" 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
if [ "$STATUS" = "ok" ]; then
    ok "NewsRadar responde (status=ok)"
else
    warn "NewsRadar no está levantado — ejecuta: bash pfinal/start.sh"
fi
echo ""

# ── 4. Acceso a internet (para RSS y SMTP) ───────────────────────────────────
echo "── [4/5] Acceso a internet ──"
if curl -sf --max-time 5 "https://www.google.com" > /dev/null 2>&1; then
    ok "Internet OK"
else
    fail "Sin acceso a internet — los feeds RSS y el email no funcionarán"
fi
echo ""

# ── 5. Puerto SMTP 587 accesible (Gmail para M1/M2/M3) ──────────────────────
echo "── [5/5] Puerto SMTP 587 (Gmail) ──"
if timeout 5 bash -c "echo > /dev/tcp/smtp.gmail.com/587" 2>/dev/null; then
    ok "Puerto 587 accesible — los emails funcionarán (M1/M2/M3)"
else
    warn "Puerto 587 bloqueado por la red de la universidad"
    echo "   Impacto: M1/M2/M3 no enviarán emails reales, pero los logs de"
    echo "   Docker SÍ muestran las líneas [EMAIL] — el professor puede verlas."
    echo "   SEND_EMAILS=false en .env si falla el arranque por SMTP."
fi
echo ""

echo "════════════════════════════════════════"
echo "  Orden de ejecución el día del examen:"
echo ""
echo "  1. bash pfinal/start.sh"
echo "  2. bash pfinal/run_verifier.sh --all"
echo "  3. bash pfinal/m1_email_notificacion.sh   (otra terminal)"
echo "  4. bash pfinal/m2_formato_asunto.sh"
echo "  5. bash pfinal/m3_registro_verificacion.sh"
echo "  6. bash pfinal/m4_expiracion_24h.sh"
echo "  7. python mock_rss_service.py --port 8100  (otra terminal)"
echo "     bash pfinal/m5_mock_rss.sh"
echo "════════════════════════════════════════"
