#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE="http://localhost:8000"

echo "=== Bajando contenedores y borrando volúmenes ==="
cd "$SCRIPT_DIR"
docker compose down -v

echo "=== Levantando contenedores con rebuild ==="
DOCKER_BUILDKIT=0 docker compose up --build -d

echo "=== Esperando a que la app responda (máx. 90s) ==="
for i in $(seq 1 45); do
    if curl -sf "$SERVICE/api/v1/health" > /dev/null 2>&1; then
        echo "App lista tras $((i * 2))s"
        break
    fi
    if [ "$i" -eq 45 ]; then
        echo "ERROR: la app no respondió en 90s"
        docker compose logs app --tail=20
        exit 1
    fi
    echo "Intento $i/45..."
    sleep 2
done

echo ""
echo "App corriendo en $SERVICE"
echo "Ejecuta './verify.sh' para pasar los 281 casos."
