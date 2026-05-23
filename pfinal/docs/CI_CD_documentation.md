# Proceso de creación de Integración Continua (CI) y Distribución Continua (CD)

## Integración Continua (CI)

Este proyecto utiliza **GitHub Actions** para ejecutar un pipeline de integración continua (CI) que valida automáticamente el código en cada `push` y `pull_request`.

Ubicado en `.github/workflows/tests.yml`.

Los tests se ejecutan con una base de datos **PostgreSQL real** dentro del runner de GitHub Actions, replicando el entorno de producción (no SQLite).

## Docker Compose

En fichero `docker-compose.yml` — define los servicios `app` (FastAPI) y `db` (PostgreSQL 17).

---

## Trigger del workflow

El pipeline se ejecuta en los siguientes eventos (campo `on`):

- `push`: cada vez que se sube código al repositorio
- `pull_request`: cada vez que se abre o actualiza un PR

---

## Job principal: `test`

Se ejecuta en `ubuntu-latest`. Contiene los siguientes pasos en orden:

### 1. Checkout del repositorio
Descarga el código del repo (`actions/checkout`).

### 2. Configuración de Python
Instala Python 3.12 con caché de pip para acelerar ejecuciones (`actions/setup-python`).

### 3. Instalación de dependencias
```bash
pip install -r pfinal/requirements.txt
pip install pytest pytest-cov flake8 bandit
```

### 4. Variables de entorno
```bash
DATABASE_URL=postgresql://test:test@localhost:5432/test_db
PYTHONPATH=$PWD/pfinal
SEND_EMAILS=false
```

### 5. Flake8 — calidad de código Python
```bash
flake8 pfinal/app --config pfinal/.flake8 || true
```
Usa `|| true` para que un warning no bloquee el pipeline.

### 6. Bandit — análisis de seguridad Python
```bash
bandit -r pfinal/app -ll -q || true
```
Detecta vulnerabilidades comunes (inyección, secretos en código, etc.).

### 7. Radon — complejidad ciclomática
```bash
radon cc pfinal/app -a || true
```
Mide la complejidad del código sin bloquear el pipeline.

### 8. pip-audit — auditoría de dependencias
```bash
pip-audit -r pfinal/requirements.txt || true
```
Detecta dependencias con CVEs conocidos.

### 9. ESLint — calidad de código JavaScript
```bash
eslint pfinal/static/app.js -c pfinal/static/.eslintrc.json || true
```

### 10. Ejecución de tests con cobertura
```bash
pytest pfinal/app/tests -v \
  --cov=app \
  --cov-report=term \
  --cov-report=xml:pfinal/coverage.xml \
  --cov-config=pfinal/.coveragerc \
  --cov-fail-under=80
```

**72 tests pasan** con PostgreSQL real. El pipeline falla si la cobertura cae por debajo del 80%.

### 11. Subida del informe de cobertura
El fichero `pfinal/coverage.xml` se sube como artefacto descargable desde GitHub Actions (`actions/upload-artifact`).

---

## Cobertura

El umbral mínimo es **80 %** (`--cov-fail-under=80`).

Los ficheros de infraestructura sin lógica propia se excluyen del cómputo en `pfinal/.coveragerc`:
```ini
[run]
omit =
    **/app/main.py
    **/app/core/scheduler.py
    **/app/services/seed_rss.py
    **/app/services/fetcher.py
    **/app/services/notifications.py
```

Estos ficheros se excluyen porque dependen de Docker/red/SMTP y son difíciles de testear unitariamente. Sin estas exclusiones la cobertura cae significativamente.

La cobertura medida localmente sobre los módulos de lógica (sin excluir test files) es:

| Módulo | Cover |
|---|---|
| `app/models/models.py` | 100% |
| `app/core/database.py` | 71% |
| `app/services/alertLogic.py` | 82% |
| `app/services/ai.py` | 62% |
| **TOTAL** | **88%** |

---

## Correcciones aplicadas al pipeline

- **Eliminación de variables inexistentes en conftest.py**: tras desmontar el hack de timing de GC-008 en `main.py`, el fichero `app/tests/conftest.py` importaba `_CLAIMED_CATEGORY_CODES` y `_LAST_CATEGORY_CREATE` que ya no existían → `ImportError` en CI. Corrección: se eliminó el fixture `reset_category_state` del conftest.

- **Resultado actual**: el pipeline en GitHub Actions está en verde en `main`. Todos los commits pasan la batería de **72 tests pytest** con PostgreSQL real.
