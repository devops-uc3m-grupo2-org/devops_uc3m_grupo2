#!/usr/bin/env bash
# examen.sh — Proceso completo automatizado para el examen NewsRadar
# Uso: bash pfinal/examen.sh          (desde la raíz del repo, en WSL)
#      bash examen.sh                 (desde pfinal/)

cd "$(dirname "${BASH_SOURCE[0]}")"  # Siempre ejecutar desde pfinal/

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅  $*${NC}"; }
info() { echo -e "${CYAN}${BOLD}── $* ──${NC}"; }
warn() { echo -e "${YELLOW}⚠️   $*${NC}"; }
fail() { echo -e "${RED}❌  $*${NC}"; }

LOG_VERIFIER=/tmp/newsradar_verifier.log
LOG_MOCK=/tmp/newsradar_mock.log

echo ""
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}   NewsRadar — Script de examen automatizado      ${NC}"
echo -e "${CYAN}${BOLD}   Inicio: $(date '+%d/%m/%Y %H:%M')              ${NC}"
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# [1/5] Arrancar la app
# ─────────────────────────────────────────────────────────────────────────────
info "[1/5] Arrancando la app — reset BD + rebuild Docker (~2 min)"
if bash start.sh; then
    ok "App arrancada y respondiendo en http://localhost:8000"
else
    fail "start.sh falló — revisar Docker y volver a intentar"
    exit 1
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# [2/5] Verificador 281 tests en background
# ─────────────────────────────────────────────────────────────────────────────
info "[2/5] Lanzando verificador 281 tests en segundo plano (~10-12 min)"
bash run_verifier.sh --all > "$LOG_VERIFIER" 2>&1 &
VERIFIER_PID=$!
echo "   PID: $VERIFIER_PID"
echo "   Log en tiempo real: tail -f $LOG_VERIFIER"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# [3/5] Inspecciones rápidas M3 y M4 (instantáneas)
# ─────────────────────────────────────────────────────────────────────────────
info "[3/5] Inspección manual M3 (correo verificación) y M4 (expiración 24h)"

if bash m3_registro_verificacion.sh; then
    ok "M3 pasado"
else
    warn "M3 falló — verificar manualmente con Swagger POST /auth/register"
fi

if bash m4_expiracion_24h.sh; then
    ok "M4 pasado"
else
    warn "M4 falló — verificar GET /auth/verify?token=tokenfalso → HTTP 400"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# [4/5] Mock RSS en background
# ─────────────────────────────────────────────────────────────────────────────
info "[4/5] Iniciando mock RSS en background (puerto 8100)"
(cd devops_verifica-main && python mock_rss_service.py --port 8100 --host 0.0.0.0) \
    > "$LOG_MOCK" 2>&1 &
MOCK_PID=$!
echo "   PID: $MOCK_PID — esperando que levante..."
sleep 5

if curl -sf http://127.0.0.1:8100/openapi.json > /dev/null 2>&1; then
    ok "Mock RSS en marcha en http://127.0.0.1:8100"
else
    warn "Mock RSS no responde todavía — M5 podría fallar"
    warn "Log del mock: $LOG_MOCK"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# [5/5] M1 + M2 y M5 en paralelo (~10 min)
# ─────────────────────────────────────────────────────────────────────────────
info "[5/5] M1 (email notificación), M2 (formato asunto) y M5 (mock RSS) — en paralelo"
echo "   Todos esperan el ciclo del scheduler (~5 min). Tiempo máximo: ~12 min."
echo ""

# M1 → M2 en subshell (m2 solo si m1 pasa)
(
    if bash m1_email_notificacion.sh; then
        bash m2_formato_asunto.sh
    else
        fail "M1 falló — M2 omitido. Verificar manualmente con Swagger."
    fi
) &
M1M2_PID=$!

# M5 en paralelo
bash demo_m5.sh &
M5_PID=$!

# Esperar M1+M2
wait $M1M2_PID
ok "M1 + M2 finalizados"

# Esperar M5
wait $M5_PID
ok "M5 finalizado"

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Esperar verificador y mostrar resumen
# ─────────────────────────────────────────────────────────────────────────────
info "Esperando que termine el verificador..."
if wait $VERIFIER_PID; then
    ok "Verificador completado"
else
    warn "Verificador terminó con código de error — ver log abajo"
fi

echo ""
echo -e "${BOLD}── Resumen del verificador ──────────────────────${NC}"
grep -E "Total casos|OK:|NOK:|WARNING:|Resultado:" "$LOG_VERIFIER" || \
    tail -5 "$LOG_VERIFIER"

# ─────────────────────────────────────────────────────────────────────────────
# Limpiar mock RSS
# ─────────────────────────────────────────────────────────────────────────────
kill $MOCK_PID 2>/dev/null || true
wait $MOCK_PID 2>/dev/null || true

# ─────────────────────────────────────────────────────────────────────────────
# Resumen final
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}   PROCESO COMPLETO                               ${NC}"
echo -e "${GREEN}${BOLD}   Fin: $(date '+%d/%m/%Y %H:%M')                 ${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════${NC}"
echo ""
echo "   Logs:"
echo "   · Verificador: $LOG_VERIFIER"
echo "   · Mock RSS:    $LOG_MOCK"
echo ""
echo "   Si algo falló, ejecutar el script individual:"
echo "   bash pfinal/m1_email_notificacion.sh"
echo "   bash pfinal/m5_mock_rss.sh"
echo ""
