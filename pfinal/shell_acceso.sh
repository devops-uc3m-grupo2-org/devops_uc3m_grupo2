#!/usr/bin/env bash
# verifier_shell.sh — Abre una shell interactiva con el venv del verificador activado.
# Uso: bash pfinal/verifier_shell.sh
# Para salir: exit (vuelve a la shell original)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/devops_verifica-main/.venv"
VERIFICA_DIR="$SCRIPT_DIR/devops_verifica-main"

if [ ! -f "$VENV/bin/activate" ]; then
    echo "ERROR: .venv no existe. Créalo con:"
    echo "  bash $SCRIPT_DIR/run_verifier.sh"
    exit 1
fi

echo "Entrando en shell con venv del verificador activado..."
echo "Para salir: exit"
echo ""

exec bash --rcfile <(
    # Carga bashrc del usuario si existe (para aliases, etc.)
    [ -f ~/.bashrc ] && cat ~/.bashrc
    echo "source '$VENV/bin/activate'"
    echo "cd '$VERIFICA_DIR'"
    echo "export PYTHONPATH='.'"
    echo "echo \"Venv activo: \$(python --version) | \$(which python)\""
    echo "echo \"Directorio:  \$(pwd)\""
    echo "echo \"\""
)
