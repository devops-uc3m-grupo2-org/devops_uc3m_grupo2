# Entorno virtual y ejecución de tests

Breve guía para preparar un `venv` y ejecutar los tests del proyecto.

Requisitos
- Python 3.10+ instalado

Crear y activar el entorno virtual
- Crear: `python -m venv .venv` (ejecutar desde la raíz del repo)
- Activar (PowerShell): `.
  .venv\Scripts\Activate.ps1`
- Activar (CMD): `.venv\Scripts\activate.bat`
- Activar (WSL / Linux / macOS): `source .venv/bin/activate`

Actualizar pip (recomendado)
- `python -m pip install --upgrade pip`

Instalar dependencias
- `pip install -r pfinal/requirements.txt`

Ejecutar tests
- Ejecutar todos los tests del subpaquete de la app:
  `python -m pytest pfinal/app/tests -q`
- Ejecutar todos los tests del repo:
  `python -m pytest -q`
- Ejecutar un test concreto:
  `python -m pytest pfinal/app/tests/test_alerts.py::test_update_alert -q`

Consejos rápidos
- Usa `python -m pip` para asegurarte de usar el pip del `venv`.
- Si falta un módulo, verifica que está en `pfinal/requirements.txt` y vuelve a instalar.
- Añade `.venv/` a tu `.gitignore` si no está ya.
- Para reproducir en CI, instala con: `python -m pip install -r pfinal/requirements.txt`.

¿Quieres que añada un script de instalación o instrucciones específicas para Windows/WSL en el README?
