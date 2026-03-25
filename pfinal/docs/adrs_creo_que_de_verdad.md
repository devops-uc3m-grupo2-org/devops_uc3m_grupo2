# Architecture Decision Records (ADRs)

Estos ADR reflejan las decisiones arquitectónicas ya implementadas en el proyecto actual (FastAPI + JWT + PostgreSQL + Docker + RSS básico).
Cada decisión está respaldada por código y alineada con los sprints desarrollados.

---

## ADR 001 – Lenguaje de programación: Python 3.12 + FastAPI

**Estado:** Aceptado

### Decisión
Usar **Python 3.12** como lenguaje principal del backend y **FastAPI** como framework web.

### Motivación
- Ecosistema muy fuerte para IA, NLP y APIs (FastAPI, SQLAlchemy, Pydantic, feedparser, etc.).
- Curva de aprendizaje baja para el equipo y amplia documentación.
- FastAPI genera automáticamente documentación OpenAPI/Swagger (`/docs`) y acelera el desarrollo de endpoints.

### Referencias
- FastAPI docs: https://fastapi.tiangolo.com/

### Consecuencias
- Prototipado rápido y código legible.
- Rendimiento suficiente para el alcance del proyecto; si surgen cuellos de botella, se optimizarán partes concretas.

---

## ADR 002 – Base de datos: PostgreSQL + SQLAlchemy

**Estado:** Aceptado

### Decisión
Usar **PostgreSQL** como base de datos relacional y **SQLAlchemy 2.x** como ORM.

### Motivación
- PostgreSQL es robusto, bien soportado en Docker y adecuado para datos relacionales (usuarios, roles, fuentes, noticias).
- SQLAlchemy permite definir modelos (`User`, `Role`, `InformationSource`, `NewsItem`) de forma declarativa y mantener sesiones coherentes en FastAPI.
- Ya está integrado en el proyecto (Fase 1 y Sprint 2).

### Consecuencias
- Permite realizar joins, filtros por fecha/fuente/categoría y paginación fácilmente.
- En el futuro se podrán gestionar migraciones con **Alembic**.

---

## ADR 003 – Autenticación: JWT con python-jose

**Estado:** Aceptado

### Decisión
Usar **JSON Web Tokens (JWT)** firmados con **HS256** para login y acceso a endpoints protegidos.

### Motivación
- Requisito explícito del proyecto: autenticación basada en JWT.
- Implementación actual en `app.main` usando **python-jose** (`create_access_token`) y `OAuth2PasswordBearer`.
- Tokens configurables mediante variables de entorno (`SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`).

### Consecuencias
- El endpoint `POST /api/v1/auth/login` genera tokens de acceso.
- La protección de endpoints por rol/permisos puede extenderse en fases futuras (p. ej., RBAC mediante la tabla `roles`).

---

## ADR 004 – Contenedores: Docker + Docker Compose

**Estado:** Aceptado

### Decisión
Usar **Docker** y **Docker Compose** para levantar el stack local: API (`app`), base de datos (`db`) y pgAdmin (`pgadmin`).

### Motivación
- Permite al profesor o tribunal levantar el entorno con un solo comando:
  ```bash
  docker compose up --build
  ```
- Encapsula dependencias (PostgreSQL, Python, librerías del backend) sin configuración manual en la máquina host.
- El volumen `./app:/app/app` facilita el desarrollo en local reflejando los cambios en el contenedor.

### Nota demo / ejecución local
En la demo también se soporta ejecución local con `uvicorn` (por ejemplo `uvicorn app.main:app --reload --port 9000`) — el código es el mismo que se monta en Docker, por lo que las pruebas locales y en contenedor son equivalentes.

### Consecuencias
- El backend está accesible en [http://localhost:8000](http://localhost:8000) (desde Docker).
- También se puede ejecutar localmente con `uvicorn` (puerto 9000) para desarrollo.
- Ampliar el stack (cola de tareas, vector DB, etc.) es sencillo mediante `docker-compose.yml`.

---

## ADR 005 – Modelado de fuentes y noticias

**Estado:** Aceptado

### Decisión
Introducir dos modelos nuevos en la base de datos:
- `InformationSource`: representa una fuente RSS.
- `NewsItem`: representa una noticia individual.

### Motivación
- El proyecto requiere monitorizar múltiples canales RSS y almacenar noticias asociadas (título, resumen, fecha, enlace).
- Tener modelos explícitos en SQLAlchemy facilita futuras ampliaciones: clasificación IPTC, alertas o anotaciones.

### Consecuencias
- Las tablas se crean automáticamente durante el `startup` de FastAPI (`Base.metadata.create_all`).
- Los endpoints de Sprint 2 (`/api/v1/sources`, `/api/v1/news`) operan directamente sobre estos modelos.

---

## ADR 006 – Ingesta RSS: feedparser + servicio de dominio

**Estado:** Aceptado

### Decisión
Usar la librería **feedparser** para consumir feeds RSS y encapsular la lógica de ingesta en un servicio `fetch_feed(db, source_id)`.

### Motivación
- `feedparser` es una librería madura y estándar para leer RSS/Atom en Python.
- Encapsular la ingesta en `app/services/fetcher.py` permite reutilizar la lógica (desde endpoint o scheduler futuro).
- El servicio se encarga de:
  - Leer la URL RSS de `InformationSource`.
  - Parsear entradas.
  - Evitar duplicados por `link`.
  - Mapear campos (`title`, `summary`, `published`) a `NewsItem`.

### Consecuencias
- El endpoint `POST /api/v1/sources/{source_id}/fetch` llama a `fetch_feed` y devuelve el número de noticias nuevas (`new_items`).
- Cambiar de librería o añadir limpieza de HTML solo afecta a `fetcher.py`.

### Referencias
- feedparser docs: https://feedparser.readthedocs.io/

---

## ADR 007 – API pública Sprint 2: endpoints mínimos

**Estado:** Aceptado

### Decisión
Definir un conjunto de endpoints REST mínimos para cubrir Sprint 1 + Sprint 2:

#### Autenticación / usuarios
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/users`
- `GET /api/v1/health`

#### Fuentes RSS
- `POST /api/v1/sources`
- `GET /api/v1/sources`
- `POST /api/v1/sources/{source_id}/fetch`

#### Noticias
- `GET /api/v1/news`

#### Debug
- `GET /_routes` (solo desarrollo)

### Motivación
- Cumple los objetivos del sprint:
  - Registrar fuentes RSS.
  - Lanzar ingesta de noticias por fuente.
  - Consultar noticias persistidas.
- Mantiene la API simple, limpia y versionada bajo `/api/v1/`.

### Consecuencias
- **Swagger** (`/docs`) muestra todo lo necesario para demostrar el Sprint 2.
- Futuras funcionalidades (alertas, clasificación IPTC, búsqueda semántica) se podrán integrar bajo `/api/v1/...` o versiones nuevas.

---

# ADR 008 – Versionado de la API: prefijo `/api/v1/`

**Estado:** Aceptado

## Decisión
Versionar la API HTTP usando un prefijo de ruta estable `/api/v1/` para todos los endpoints públicos del backend.

## Motivación
- Facilitar la **evolución** de la API sin romper clientes existentes, permitiendo introducir cambios incompatibles en futuras versiones (`/api/v2/`, etc.). [web:183][web:184]
- Mantener una estructura clara y homogénea de rutas (`/api/v1/auth/...`, `/api/v1/sources/...`, `/api/v1/news/...`), alineada con buenas prácticas de versionado por path en APIs REST. [web:186][web:188]
- Integrarse de forma natural con FastAPI y su sistema de routers (`include_router(..., prefix="/api/v1")`), sin necesidad de librerías externas de versionado. [web:184]

## Alcance actual
En la implementación actual del proyecto:
- Todos los endpoints funcionales de Sprint 1 y Sprint 2 se exponen bajo el prefijo `/api/v1/`:
  - Autenticación / usuarios: `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/users`.
  - Salud: `/api/v1/health`.
  - Fuentes RSS: `/api/v1/sources`, `/api/v1/sources/{source_id}/fetch`.
  - Noticias: `/api/v1/news`.
- Endpoints de depuración como `GET /_routes` se mantienen fuera del espacio versionado al estar pensados solo para desarrollo.

## Consecuencias
- Los clientes (frontend, scripts, herramientas externas) deben apuntar siempre a rutas bajo `/api/v1/...`, lo que hace explícita la versión consumida.
- En el futuro se podrá:
  - Crear nuevos routers (por ejemplo `/api/v2/...`) con contratos distintos, manteniendo `/api/v1/...` operativo para compatibilidad. [web:183][web:184]
  - Separar documentación por versión si fuera necesario (p. ej. docs específicas por sub‑app montada o separación por tags en Swagger). [web:135][web:184]
- La configuración de OpenAPI/Swagger puede ajustarse para servir la especificación bajo una ruta versionada (por ejemplo `openapi_url="/api/v1/openapi.json"`), manteniendo coherencia en la estructura de URLs. [web:135]
