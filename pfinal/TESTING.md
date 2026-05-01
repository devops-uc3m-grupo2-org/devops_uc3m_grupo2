# Guía de tests — NewsRadar

Suite: **72 tests** en 12 archivos. Se pueden correr de tres formas: localmente con SQLite (sin Docker), localmente con PostgreSQL o con Docker.

---

## Opción 1 — Local con SQLite (más rápido, sin Docker)

La forma más sencilla. No requiere ninguna base de datos externa.

### 1. Instalar dependencias

```bash
cd pfinal
pip install -r requirements.txt
pip install pytest pytest-cov httpx
```

### 2. Correr todos los tests

```bash
DATABASE_URL="sqlite:///./test_local.db" \
PYTHONPATH="$(pwd)" \
SEND_EMAILS="false" \
pytest app/tests/ -v
```

**En Windows (cmd):**
```cmd
set DATABASE_URL=sqlite:///./test_local.db
set PYTHONPATH=%cd%
set SEND_EMAILS=false
py -3.12 -m pytest app/tests/ -v
```

**En Windows (PowerShell):**
```powershell
$env:DATABASE_URL = "sqlite:///./test_local.db"
$env:PYTHONPATH   = (Get-Location).Path
$env:SEND_EMAILS  = "false"
py -3.12 -m pytest app/tests/ -v
```

### 3. Con informe de cobertura

```bash
DATABASE_URL="sqlite:///./test_local.db" \
PYTHONPATH="$(pwd)" \
SEND_EMAILS="false" \
pytest app/tests/ -v --cov=app --cov-report=term
```

---

## Opción 2 — Local con PostgreSQL

Equivalente al entorno de CI. Requiere PostgreSQL corriendo.

### 1. Crear la base de datos de test

```bash
psql -U postgres -c "CREATE USER test WITH PASSWORD 'test';"
psql -U postgres -c "CREATE DATABASE test_db OWNER test;"
```

### 2. Correr los tests

```bash
DATABASE_URL="postgresql://test:test@localhost:5432/test_db" \
PYTHONPATH="$(pwd)" \
SEND_EMAILS="false" \
pytest app/tests/ -v --cov=app --cov-report=term
```

---

## Opción 3 — Con Docker (igual que CI)

```bash
# Desde la raíz del proyecto
docker compose run --rm app \
  pytest app/tests/ -v --cov=app --cov-report=term
```

O levantando solo la base de datos con Docker y corriendo pytest en local:

```bash
docker compose up -d db       # solo PostgreSQL
DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/newsradar" \
PYTHONPATH="pfinal" SEND_EMAILS="false" \
pytest pfinal/app/tests/ -v
```

---

## Opciones útiles de pytest

| Comando | Efecto |
|---|---|
| `pytest app/tests/ -v` | Todos los tests, verbose |
| `pytest app/tests/test_auth_extended.py -v` | Solo un archivo |
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
| `test_users_extended.py` | 19 | CRUD usuarios, CRUD completo de notificaciones |

---

## Variables de entorno requeridas

| Variable | Valor para tests | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./test_local.db` o PostgreSQL | Base de datos de test |
| `PYTHONPATH` | Ruta a `pfinal/` | Para que los imports de `app.*` funcionen |
| `SEND_EMAILS` | `false` | Deshabilita el envío real de emails |

> `SEND_EMAILS=false` es obligatorio para que los tests no intenten conectarse al servidor SMTP y fallen por credenciales.

---

## CI — GitHub Actions

Los tests se ejecutan automáticamente en cada `push` y `pull_request` desde [`.github/workflows/tests.yml`](../.github/workflows/tests.yml):

1. Levanta PostgreSQL 15 como servicio.
2. Instala dependencias (`requirements.txt` + pytest, flake8, bandit).
3. Ejecuta análisis de calidad: **Flake8** (Python) y **ESLint** (JavaScript).
4. Ejecuta análisis de seguridad: **Bandit**.
5. Corre `pytest` con cobertura y sube el artefacto `coverage.xml`.

Para ver el resultado de la última ejecución:

```bash
gh run list --limit 5
gh run view <RUN_ID>
```
