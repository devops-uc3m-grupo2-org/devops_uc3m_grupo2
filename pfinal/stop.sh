#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Parando contenedores ==="
cd "$SCRIPT_DIR"
docker compose down

echo ""
echo "Contenedores parados. Los datos se conservan (volúmenes intactos)."
echo "Para arrancar de nuevo: bash start.sh"
