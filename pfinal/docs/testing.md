# Guía de tests — NewsRadar

> **Este documento:** cómo ejecutar los tests — comandos, venv, opciones pytest, CI.
> **Para qué hace cada test:** ver [`tests_documentation.md`](tests_documentation.md).

Suite: **72 tests en 13 archivos · 96% cobertura**. Se pueden correr de tres formas: localmente con SQLite (sin Docker), localmente con PostgreSQL o con Docker.

---

## Requisitos previos

- Python 3.12 instalado
- Docker y Docker Compose (solo para las opciones 2 y 3)

Verifica las versiones:

```bash
python --version          # Python 3.12.x
docker --version          # Docker 24.x+
docker compose --version  # v2.x+
```

---

## Preparar el entorno virtual (recomendado para opción local)

```bash
# Desde pfinal/
python -m venv .venv
```

Activar el venv:

| Sistema | Comando |
|---|---|
| PowerShell | `.\.venv\Scripts\Activate.ps1` |
| CMD | `.venv\Scripts\activate.bat` |
| Linux / macOS / WSL | `source .venv/bin/activate` |

Instalar dependencias:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-cov httpx
```

---

## Opción 1 — Local con SQLite (más rápido, sin Docker)

La forma más sencilla. No requiere ninguna base de datos externa.

**Linux / macOS / WSL:**
```bash
DATABASE_URL="sqlite:///./test_local.db" \
PYTHONPATH="$(pwd)" \
SEND_EMAILS="false" \
pytest app/tests/ -v
```

**Windows (PowerShell):**
```powershell
$env:DATABASE_URL = "sqlite:///./test_local.db"
$env:PYTHONPATH   = (Get-Location).Path
$env:SEND_EMAILS  = "false"
py -3.12 -m pytest app/tests/ -v
```

**Windows (CMD):**
```cmd
set DATABASE_URL=sqlite:///./test_local.db
set PYTHONPATH=%cd%
set SEND_EMAILS=false
py -3.12 -m pytest app/tests/ -v
```

---

## Opción 2 — Local con PostgreSQL (equivalente a CI)

Requiere PostgreSQL corriendo localmente.

### Crear la base de datos de test

```bash
psql -U postgres -c "CREATE USER test WITH PASSWORD 'test';"
psql -U postgres -c "CREATE DATABASE test_db OWNER test;"
```

### Correr los tests

```bash
DATABASE_URL="postgresql://test:test@localhost:5432/test_db" \
PYTHONPATH="$(pwd)" \
SEND_EMAILS="false" \
pytest app/tests/ -v --cov=app --cov-report=term
```

---

## Opción 3 — Con Docker (idéntico a CI)

```bash
# Desde la raíz del proyecto
docker compose run --rm app \
  pytest app/tests/ -v --cov=app --cov-report=term
```

O levantando solo la base de datos con Docker y pytest en local:

```bash
docker compose up -d db
DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/newsradar" \
PYTHONPATH="pfinal" SEND_EMAILS="false" \
pytest pfinal/app/tests/ -v
```

---

## Opciones útiles de pytest

| Comando | Efecto |
|---|---|
| `pytest app/tests/ -v` | Todos los tests, verbose |
| `pytest app/tests/test_categories.py -v` | Solo un archivo |
| `pytest app/tests/ -k "category"` | Tests cuyo nombre contiene "category" |
| `pytest app/tests/ -v --tb=short` | Tracebacks cortos en fallos |
| `pytest app/tests/ --cov=app --cov-report=term` | Cobertura en terminal |
| `pytest app/tests/ --cov=app --cov-report=html` | Cobertura en HTML (`htmlcov/index.html`) |
| `pytest app/tests/ --cov=app --cov-report=xml:coverage.xml` | Cobertura en XML (para CI) |

---

## Archivos de test

| Archivo | Tests | Qué cubre |
|---|---|---|
| `test_health.py` | 1 | Health check `/health` |
| `test_login.py` | 3 | Registro, login, credenciales incorrectas |
| `test_auth_extended.py` | 7 | Verificación de cuenta, forgot/reset password, email duplicado |
| `test_sources.py` | 5 | CRUD fuentes RSS, duplicados, fetch debug |
| `test_alerts.py` | 2 | CRUD alertas y notificaciones con JWT |
| `test_news.py` | 3 | Listado de noticias, fetch autenticado |
| `test_ai.py` | 3 | Endpoint `/suggestions`, keyword conocido y desconocido |
| `test_stats.py` | 3 | Métricas reales, auth requerida, contador se actualiza |
| `test_stats_extended.py` | 7 | Wordcloud, stats por categoría, límite de 20 alertas, `/alerts/check` |
| `test_categories.py` | 9 | CRUD completo de categorías IPTC + 404s |
| `test_roles_extended.py` | 10 | CRUD completo de roles + 409 al borrar rol asignado |
| `test_users_extended.py` | 13 | CRUD usuarios, CRUD completo de notificaciones |
| `test_monitoring.py` | 6 | Matching alertas-noticias, pipeline completo |

---

## Variables de entorno requeridas

| Variable | Valor para tests | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./test_local.db` o PostgreSQL URL | Base de datos de test |
| `PYTHONPATH` | Ruta a `pfinal/` | Para que los imports de `app.*` funcionen |
| `SEND_EMAILS` | `false` | Deshabilita el envío real de emails (ya forzado en `conftest.py`) |

> `SEND_EMAILS=false` se establece automáticamente en `conftest.py`, por lo que no hace falta pasarlo a mano.

### Demostrar que el envío de emails funciona

Si necesitas probar que los emails llegan de verdad (por ejemplo en una revisión), sobrescribe la variable antes de correr los tests:

**PowerShell:**
```powershell
$env:SEND_EMAILS = "true"
py -3.12 -m pytest app/tests/test_login.py -v   # registra usuarios reales → llegan emails
$env:SEND_EMAILS = "false"                        # vuelve a desactivar cuando termines
```

**Linux / macOS:**
```bash
SEND_EMAILS=true pytest app/tests/test_login.py -v
```

> Usa un email real en el test o regístrate manualmente desde `http://localhost:8000` con Docker levantado — es la forma más limpia de demostrarlo sin tocar los tests.

---

## Verificación manual de la API (Swagger)

Con la aplicación corriendo (`docker compose up --build` o `uvicorn app.main:app`):

1. Abre `http://localhost:8000/docs`
2. Expande **Auth → POST /api/v1/auth/login** → **Try it out**
3. Ejecuta con:
   ```json
   { "email": "admin@newsradar.com", "password": "admin123" }
   ```
4. Copia el `access_token` y pulsa **Authorize** (esquina superior derecha)
5. A partir de ahí todos los endpoints autenticados funcionan desde el navegador

Endpoints clave para verificar manualmente:

```
GET  /api/v1/health                 → { "status": "ok" }
GET  /api/v1/users                  → lista de usuarios
GET  /api/v1/stats                  → métricas del sistema
GET  /api/v1/stats/wordcloud        → nube de palabras por categoría
GET  /api/v1/stats/by-category      → conteo por categoría IPTC
POST /api/v1/news/fetch             → importar noticias RSS
POST /api/v1/news/fetch             → importar + matching automático vía scheduler
```

---

## Solución de problemas

**Los tests no encuentran el módulo `app`**
```bash
# Asegúrate de estar en pfinal/ y de que PYTHONPATH apunta ahí
cd pfinal
export PYTHONPATH=$(pwd)   # Linux/macOS
$env:PYTHONPATH = (Get-Location).Path  # PowerShell
```

**Error de conexión a la base de datos**
```bash
# Verifica que los contenedores estén corriendo
docker compose ps
# Ver logs del contenedor de la app
docker compose logs app
# Ver logs de la base de datos
docker compose logs db
```

**Un test falla de forma inesperada**
```bash
# Ejecuta solo ese test con traceback completo
pytest app/tests/test_X.py::nombre_del_test -v --tb=long
```

**El venv tiene módulos de otro entorno**
```bash
pip install -r requirements.txt --force-reinstall
```

---

## CI — GitHub Actions

Los tests se ejecutan automáticamente en cada `push` y `pull_request` desde [`.github/workflows/fastapi-ci.yml`](../.github/workflows/fastapi-ci.yml):

1. Levanta PostgreSQL 16 como servicio del runner.
2. Instala dependencias (`requirements.txt` + pytest, pytest-cov, flake8, bandit).
3. Ejecuta análisis de calidad: **Flake8** (Python) y **ESLint** (JavaScript).
4. Ejecuta análisis de seguridad: **Bandit**.
5. Corre `pytest` con cobertura y sube el artefacto `coverage.xml`.

Ver resultado de la última ejecución:

```bash
gh run list --limit 5
gh run view <RUN_ID>
```

Descargar el informe de cobertura:

```bash
gh run download <RUN_ID> --name coverage-report
```
