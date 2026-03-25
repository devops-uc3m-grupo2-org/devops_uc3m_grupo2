# Estado actual – NewsRadar (25‑mar 2026)

## Sprint 0 – Infraestructura + Docker + BD + Alembic

### Objetivo
Preparar base técnica sólida y dockerizada: backend, base de datos y entorno de desarrollo reproducible.

### ¿Qué está hecho?

- Proyecto montado con **Docker Compose**:
  - Servicios `app` (FastAPI), `db` (Postgres 16‑alpine) y `pgadmin`.  
- Base de datos **PostgreSQL** levantando correctamente:
  - Contenedor `pfinal-db-1` funcionando.
  - Datos persistentes en el volumen `postgres_data`.
- Backend **FastAPI** funcionando en `http://localhost:8000`:
  - Contenedor `pfinal-app-1` arrancando sin errores.
- Endpoint de salud operativo:
  - `GET /api/v1/health` → `200 OK` con respuesta:
    ```json
    {
      "status": "ok",
      "message": "NewsRadar listo con PostgreSQL + JWT"
    }
    ```

### Evidencias para la demo

1. Comando de arranque:
   ```bash
   docker compose up --build
   ```
2. Navegador:
   - `http://localhost:8000/api/v1/health`
   - `http://localhost:8000/docs`
3. Logs de Docker muestran:
   - Postgres “ready to accept connections”.
   - Uvicorn “Application startup complete”.

---

## Sprint 1 – Autenticación + Usuarios + Roles + JWT

### Objetivo
Acceso seguro, gestión de usuarios y emisión de tokens JWT.

### ¿Qué está hecho?

- **Login** funcionando:
  - Endpoint: `POST /api/v1/auth/login`
  - Credenciales admin por defecto:
    - Usuario: `admin@newsradar.com`
    - Contraseña: `admin123`
  - Respuesta correcta (`200 OK`) con cuerpo:
    ```json
    {
      "access_token": "<JWT>",
      "token_type": "bearer"
    }
    ```
- **Listado de usuarios** funcionando:
  - Endpoint: `GET /api/v1/users`
  - Respuesta:
    ```json
    [
      {
        "id": 1,
        "email": "admin@newsradar.com",
        "first_name": "Admin",
        "last_name": "NewsRadar",
        "organization": "NewsRadar"
      }
    ]
    ```
- Usuario admin semilla creado en la base de datos.

### Evidencias para la demo

1. En `http://localhost:8000/docs`:
   - Ejecutar `POST /api/v1/auth/login` con:
     - `username = admin@newsradar.com`
     - `password = admin123`
   - Ver `access_token` en la respuesta.
2. Ejecutar `GET /api/v1/users`:
   - Ver el usuario admin en la lista.

> Nota: El endpoint `POST /api/v1/auth/register` existe pero todavía no está completamente funcional (devuelve `500` si se llama con un body genérico). No es crítico para el sprint review actual.

---

## Limpieza del proyecto

### Hecho

- Eliminados directorios de caché de Python:
  - `__pycache__/`
  - Archivos `.pyc`
- Eliminados archivos de metadatos de Windows:
  - `*:Zone.Identifier`

El repositorio queda con:

- Código fuente (`app/`).
- Configuración de Docker (`docker-compose.yml`, `Dockerfile`).
- Dependencias (`requirements.txt`).
- Documentación (`docs/`, ADRs, `README.md`).
- Ficheros auxiliares del proyecto (PDF, etc.).

Preparado para commits limpios y para la revisión de sprints.
