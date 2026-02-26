# Ticket Manager API

Esqueleto de una API CRUD para Users y Tickets siguiendo principios de Clean Architecture.

Resumen rápido
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async) + SQLite (aiosqlite)
- Migraciones con Alembic
- Tests con pytest + httpx

Requisitos
- Python 3.11 recomendado (funciona con 3.10 en entorno local)

Instalación (desde la raíz del repo)

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Linux / macOS (bash):

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Aplicar migraciones

```bash
alembic upgrade head
```

Arrancar servidor

```bash
uvicorn app.main:app --reload --port 8000
```

OpenAPI / Swagger: http://127.0.0.1:8000/docs

Endpoints principales
- Users: `GET /users/`, `GET /users/{id}`, `POST /users/`, `PUT /users/{id}`, `DELETE /users/{id}`
- Tickets: `GET /tickets/`, `GET /tickets/{id}`, `POST /tickets/`, `PATCH /tickets/{id}`, `DELETE /tickets/{id}`

Comandos útiles (con servidor en marcha)

- Crear user (ejemplo):

```bash
curl -s -X POST http://127.0.0.1:8000/users/ \
	-H "Content-Type: application/json" \
	-d '{"name":"Alice","email":"alice@example.com"}' -w "\n%{http_code}\n"
```

- Crear ticket (usar user_id existente):

```bash
curl -s -X POST http://127.0.0.1:8000/tickets/ \
	-H "Content-Type: application/json" \
	-d '{"user_id":1,"title":"Bug","description":"Something is broken","tags":["bug","urgent"]}' -w "\n%{http_code}\n"
```

- PATCH parcial (actualiza sólo `title`):

```bash
curl -s -X PATCH http://127.0.0.1:8000/tickets/1 \
	-H "Content-Type: application/json" \
	-d '{"title":"Bug crítico"}' -w "\n%{http_code}\n"
```

- Crear ticket con user inexistente (esperado 404):

```bash
curl -s -X POST http://127.0.0.1:8000/tickets/ \
	-H "Content-Type: application/json" \
	-d '{"user_id":9999,"title":"X","description":"Y","tags":[]}' -w "\n%{http_code}\n"
```

Ejecutar tests

```bash
pytest -q
```

Notas y puntos importantes
- Pydantic v2 requiere que los campos opcionales para updates tengan un valor por defecto (por ejemplo `title: Optional[str] = None`) para permitir patches parciales. Este proyecto ya incluye ese ajuste en `app/schemas/ticket.py`.
- Alembic está configurado para usar `sqlite:///./app.db` (driver sync) mientras la app usa `sqlite+aiosqlite://` en tiempo de ejecución.
- Si `pytest` da errores de importación, asegúrate de ejecutar `pytest` desde la raíz o usa `PYTHONPATH=. pytest -q`.

Evidencias recomendadas para entrega
- Captura de `http://127.0.0.1:8000/docs` mostrando endpoints.
- Salida de `pytest -q` (por ejemplo `1 passed`).
- Capturas de `POST /users` (201), `POST /tickets` (201) y `POST /tickets` con user inválido (404).

Extras
- Si quieres, puedo añadir un script `scripts/demo_requests.sh` con los curl anteriores para generar la demo automáticamente.

Contacto
- Si necesitas que prepare el script de demo o añada una regla de negocio simple y sus tests, dímelo y lo implemento.
