#!/bin/bash
# Generates technical documentation from source code.
# Output: pfinal/docs-output/ (HTML)
# API docs also auto-generated at runtime: /docs (Swagger), /redoc (ReDoc), /openapi.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

pip install pdoc -q
pdoc app --output-dir docs-output

echo ""
echo "Documentation generated in: $SCRIPT_DIR/docs-output/"
echo "Open docs-output/app.html in a browser to view."
echo ""
echo "Live API docs (when app is running):"
echo "  Swagger:  http://localhost:8000/docs"
echo "  ReDoc:    http://localhost:8000/redoc"
echo "  OpenAPI:  http://localhost:8000/openapi.json"
