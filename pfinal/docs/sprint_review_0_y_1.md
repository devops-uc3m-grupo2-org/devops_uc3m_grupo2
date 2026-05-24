# Estado actual – NewsRadar (25‑mar 2026)

> **Este documento:** Sprint 0–1 — infraestructura inicial, Docker, autenticación JWT, usuarios y roles.
> **Siguiente:** [`sprint_review_2.md`](sprint_review_2.md)

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

### Registro de usuarios (completado)

Además, el endpoint de registro está operativo:

- Endpoint: `POST /api/v1/auth/register`
- Ejemplo de petición válida:
  ```json
  {
    "email": "user1@newsradar.com",
    "password": "test1234",
    "first_name": "User",
    "last_name": "Uno",
    "organization": "NewsRadar"
  }
  ```
- Respuesta (`201 Created`):
  ```json
  {
    "id": 3,
    "email": "user1@newsradar.com",
    "first_name": "User",
    "last_name": "Uno",
    "organization": "NewsRadar",
    "role_ids": []
  }
  ```

Comportamiento esperado:

- Si el email no existe → crea el usuario y devuelve `201` con sus datos.
- Si el email ya está registrado → devuelve `409` con mensaje `"El email ya está registrado"`.

En la demo se puede enseñar:

1. `POST /api/v1/auth/register` creando un usuario nuevo.
2. `POST /api/v1/auth/login` con ese usuario nuevo para obtener un JWT.
3. `GET /api/v1/users` mostrando el admin y el nuevo usuario registrado.

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

---

## Resumen — Estado al cierre de Sprint 1

Al finalizar los sprints 0 y 1, NewsRadar presenta:

- Infraestructura dockerizada lista (`docker compose up --build`).
- Base de datos PostgreSQL con persistencia de datos y usuario admin semilla.
- Endpoint de salud operativo.
- Sistema de autenticación completo: registro, login y emisión de JWT.
- Listado de usuarios protegido con JWT.

### De qué consta

| Área | Detalle |
|------|---------|
| **Docker Compose** | Servicios `app` (FastAPI + Uvicorn) y `db` (PostgreSQL 16-alpine) |
| **Base de datos** | PostgreSQL con volumen persistente `postgres_data`; migraciones con Alembic |
| **Health check** | `GET /api/v1/health` → `{"status":"ok"}` |
| **Registro** | `POST /api/v1/auth/register` → crea usuario, devuelve `201` con sus datos |
| **Login / JWT** | `POST /api/v1/auth/login` → devuelve `access_token` Bearer |
| **Usuarios** | `GET /api/v1/users` (requiere JWT) → lista usuarios registrados |

### Ejemplos

**Health check**
```bash
curl http://localhost:8000/api/v1/health
# { "status": "ok", "message": "NewsRadar listo con PostgreSQL + JWT" }
```

**Login**
```json
// POST /api/v1/auth/login
// Request
{ "email": "admin@newsradar.com", "password": "admin123" }

// Response 200
{ "access_token": "<JWT>", "token_type": "bearer" }
```

**Registro**
```json
// POST /api/v1/auth/register
// Request
{
  "email": "user1@newsradar.com",
  "password": "test1234",
  "first_name": "User",
  "last_name": "Uno",
  "organization": "NewsRadar"
}

// Response 201
{
  "id": 2,
  "email": "user1@newsradar.com",
  "first_name": "User",
  "last_name": "Uno",
  "organization": "NewsRadar",
  "role_ids": []
}
```

**Listado de usuarios**
```bash
curl http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <JWT>"
# [ { "id": 1, "email": "admin@newsradar.com", ... }, { "id": 2, ... } ]
```
