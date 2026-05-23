#!/usr/bin/env bash
# verifier_shell.sh — Abre una shell interactiva con el venv del verificador activado.
# Uso: bash pfinal/verifier_shell.sh
# Para salir: exit (vuelve a la shell original)
#
# ALTERNATIVA SIN ESTE SCRIPT (desde pfinal/):
#   ./devops_verifica-main/.venv/bin/python devops_verifica-main/run_tests.py --service http://localhost:8000
#
# O desde dentro de devops_verifica-main/:
#   .venv/bin/python run_tests.py --service http://localhost:8000

# Calcula la carpeta donde está este script, sin importar desde dónde lo ejecutes.
# Así las rutas siguientes funcionan siempre, estés donde estés.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ruta al entorno virtual (virtual environment) del verificador del profe
VENV="$SCRIPT_DIR/devops_verifica-main/.venv"

# Ruta a la carpeta del verificador del profe
VERIFICA_DIR="$SCRIPT_DIR/devops_verifica-main"

# Comprueba que el .venv existe antes de continuar.
# Si no existe (porque no se ha creado todavía), avisa y para.
if [ ! -f "$VENV/bin/activate" ]; then
    echo "ERROR: .venv no existe. Créalo con:"
    echo "  bash $SCRIPT_DIR/run_verifier.sh"
    exit 1
fi

echo "Entrando en shell con venv del verificador activado..."
echo "Para salir: exit"
echo ""

# Abre una nueva terminal interactiva con el entorno virtual ya activado.
# Al escribir 'exit' vuelves a tu terminal original sin haber tocado nada.
exec bash --rcfile <(
    # Carga tu configuración habitual de terminal (aliases, colores, etc.)
    [ -f ~/.bashrc ] && cat ~/.bashrc
    # Activa el entorno virtual — a partir de aquí 'python' es el del .venv
    echo "source '$VENV/bin/activate'"
    # Entra en la carpeta del verificador — así puedes ejecutar run_tests.py directamente
    echo "cd '$VERIFICA_DIR'"
    # Añade la carpeta actual al PYTHONPATH (ruta de búsqueda de módulos de Python)
    # para que los imports del verificador funcionen correctamente
    echo "export PYTHONPATH='.'"
    # Muestra qué Python está activo y desde dónde, para confirmar que todo está bien
    echo "echo \"Venv activo: \$(python --version) | \$(which python)\""
    echo "echo \"Directorio:  \$(pwd)\""
    echo "echo \"\""
)
