#!/usr/bin/env bash
# run_verifier.sh — Prepara el entorno del verificador desde cero y lanza los tests
#
# Uso:
#   bash pfinal/run_verifier.sh           # para si falla SMOKE
#   bash pfinal/run_verifier.sh --all     # continúa aunque fallen los SMOKE
#
# Requisito previo: NewsRadar corriendo → bash pfinal/start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERIFICA_DIR="$SCRIPT_DIR/devops_verifica-main"
SERVICE="http://localhost:8000"

# ── Timer en vivo ─────────────────────────────────────────────────────────────
# Arranca un proceso en segundo plano que imprime el tiempo transcurrido cada segundo.
# Se para cuando se llama a stop_timer.
_TIMER_PID=""

start_timer() {
    local label="$1"
    local start=$SECONDS
    (
        while true; do
            elapsed=$(( SECONDS - start ))
            printf "\r   %s... %ds" "$label" "$elapsed"
            sleep 1
        done
    ) &
    _TIMER_PID=$!
}

stop_timer() {
    if [ -n "$_TIMER_PID" ]; then
        kill "$_TIMER_PID" 2>/dev/null || true
        wait "$_TIMER_PID" 2>/dev/null || true
        _TIMER_PID=""
        printf "\r"  # limpia la línea del timer
    fi
}

# Asegura que el timer muere si el script se interrumpe
trap stop_timer EXIT

# ─────────────────────────────────────────────────────────────────────────────
echo "════════════════════════════════════════"
echo "  Verificador NewsRadar — setup + run"
echo "════════════════════════════════════════"
echo ""

# ── 0. Comprobar que NewsRadar está levantado ──────────────────────────────
echo "── [0/4] Comprobando que NewsRadar responde ──"
STATUS=$(curl -sf "$SERVICE/api/v1/health" 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
if [ "$STATUS" != "ok" ]; then
    echo "ERROR: NewsRadar no responde en $SERVICE"
    echo "Arráncalo con: bash $SCRIPT_DIR/start.sh"
    exit 1
fi
echo "OK — $SERVICE responde"
echo ""

# ── 1. Borrar entorno virtual anterior ────────────────────────────────────
echo "── [1/4] Borrando .venv anterior (si existe) ──"
cd "$VERIFICA_DIR"
rm -rf .venv
echo "OK — .venv eliminado"
echo ""

# ── 2. Crear entorno virtual nuevo ────────────────────────────────────────
echo "── [2/4] Creando entorno virtual limpio ──"
t_venv_start=$SECONDS
start_timer "Creando .venv"
python3 -m venv .venv
stop_timer
echo "   OK — .venv creado en $((SECONDS - t_venv_start))s"
echo ""

# ── 3. Instalar dependencias ──────────────────────────────────────────────
echo "── [3/4] Instalando dependencias ──"
t_pip_start=$SECONDS
start_timer "Instalando requirements"
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
stop_timer
t_venv_end=$SECONDS
echo "   OK — dependencias instaladas en $((t_venv_end - t_pip_start))s"
echo "   Entorno listo en $((t_venv_end - t_venv_start))s total"
echo ""

# ── 4. Lanzar el verificador ──────────────────────────────────────────────
echo "── [4/4] Ejecutando verificador ──"
echo "   Servicio: $SERVICE"
echo "   Argumentos extra: ${*:-ninguno}"
echo ""

export PYTHONPATH="."
t_tests_start=$SECONDS
start_timer "Tests en curso"
.venv/bin/python run_tests.py --service "$SERVICE" "$@"
stop_timer
t_tests_end=$SECONDS

echo ""
echo "── Tiempos ──────────────────────────────"
echo "   Entorno virtual (venv + pip): $((t_venv_end - t_venv_start))s"
echo "   Tests:                        $((t_tests_end - t_tests_start))s"
echo "   Total:                        $((t_tests_end - t_venv_start))s"
