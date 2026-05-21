#!/usr/bin/env bash
# M5 — ¿Se indexan las noticias con el Mock de RSS?
# Redirige a demo_m5.sh — toda la lógica está ahí.
#
# Prerrequisito: arrancar el mock en otra terminal:
#   cd pfinal/devops_verifica-main && python mock_rss_service.py --port 8100

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec bash "$SCRIPT_DIR/demo_m5.sh" "$@"
