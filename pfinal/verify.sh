#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERIFIER_DIR="$SCRIPT_DIR/devops_verifica-main"
SERVICE="http://localhost:8000"

echo "=== Comprobando que la app responde ==="
if ! curl -sf "$SERVICE/api/v1/health" > /dev/null 2>&1; then
    echo "ERROR: la app no responde en $SERVICE — ejecuta './start.sh' primero"
    exit 1
fi
echo "App OK"

echo "=== Ejecutando verificador (281 casos) ==="
cd "$VERIFIER_DIR"
PYTHONPATH="." python run_tests.py --service "$SERVICE" --all
