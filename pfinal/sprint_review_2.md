# Sprint 2 – Fuentes RSS y noticias (NewsRadar)

Este sprint añade al backend de **NewsRadar** la gestión de **fuentes de información (RSS)** y la **ingesta básica de noticias** en la base de datos, manteniendo la autenticación JWT y PostgreSQL del Sprint 1.

---

## Objetivos de Sprint 2

- Definir modelos para representar fuentes de información y noticias.
- Implementar un servicio que consuma feeds RSS reales usando `feedparser`.
- Exponer endpoints REST para:
  - Crear y listar fuentes.
  - Lanzar la ingesta de noticias desde una fuente concreta.
  - Consultar las noticias almacenadas.

---

## Modelos añadidos

Archivo: `app/models/models.py`

### InformationSource
- **id**: int (PK)
- **name**: nombre de la fuente (ej. "RTVE")
- **medium**: medio o grupo (ej. "RTVE")
- **rss_url**: URL del feed RSS (única)
- **iptc_category**: categoría temática (texto libre por ahora)

### NewsItem
- **id**: int (PK)
- **title**: título de la noticia
- **link**: URL de la noticia (única)
- **summary**: resumen breve (texto)
- **published**: fecha/hora de publicación (nullable)
- **source_id**: FK a `InformationSource`
- **source**: relación SQLAlchemy con `InformationSource`

---

## Servicio RSS (`fetcher.py`)

Archivo: `app/services/fetcher.py`

### Función principal

```python
def fetch_feed(db: Session, source_id: int, limit: int = 10) -> int:
    ...
```

### Comportamiento

1. Recupera la fuente `InformationSource` por `id`.
2. Descarga y parsea el feed RSS con `feedparser.parse(src.rss_url)`.
3. Recorre las entradas (limitadas por `limit`) y, por cada una:
   - Deriva el `link` (prefiriendo `entry.link`, o `entry.id` como fallback).
   - Evita duplicados comprobando si ya existe un `NewsItem` con ese `link`.
   - Intenta convertir `published_parsed` a `datetime`; si falla, deja `published = None`.
   - Inserta un nuevo `NewsItem` con `title`, `link`, `summary`, `published`, y `source_id`.
4. Hace `db.commit()` y devuelve el número de noticias nuevas creadas.

---

## Endpoints disponibles (Sprint 2)

Todos los endpoints están documentados vía **OpenAPI** en **Swagger** (`/docs`).

| Método | Ruta                              | Descripción                      |
| ------ | --------------------------------- | -------------------------------- |
| POST   | /api/v1/auth/register             | Registro de usuario básico       |
| POST   | /api/v1/auth/login                | Login (JWT)                      |
| GET    | /api/v1/health                    | Health check                     |
| GET    | /api/v1/users                     | Listado de usuarios              |
| POST   | /api/v1/sources                   | Crear una fuente RSS             |
| GET    | /api/v1/sources                   | Listar fuentes registradas       |
| POST   | /api/v1/sources/{source_id}/fetch | Ingerir noticias desde la fuente |
| GET    | /api/v1/news                      | Listar noticias almacenadas      |
| GET    | /_routes                          | Endpoint de debug (rutas)        |

---

## Cómo ejecutar y probar localmente (modo desarrollo, SQLite)

### 1. Configurar variables de entorno

Archivo `.env` en la raíz del proyecto (`pfinal`):

```text
# Para desarrollo local sin Docker
DATABASE_URL=sqlite:///./newsradar.db

SECRET_KEY=supersecretlocal
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> Esto hace que SQLAlchemy use un fichero SQLite local (`newsradar.db`) en lugar del host `db` de Docker.

---

### 2. Levantar la API en local

Desde la carpeta `pfinal` (en shell Linux o WSL):

```bash
# Crear entorno virtual (opcional)
python3 -m venv .venv || true
source .venv/bin/activate 2>/dev/null || true

# Instalar dependencias
pip install -r requirements.txt

# Lanzar FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

- **Swagger UI:** [http://localhost:9000/docs](http://localhost:9000/docs)
- **OpenAPI JSON:** [http://localhost:9000/openapi.json](http://localhost:9000/openapi.json)

---

### 3. Flujo de prueba del Sprint 2

#### Crear una fuente RSS
Endpoint: `POST /api/v1/sources`

**Ejemplo de body:**
```json
{
  "name": "RTVE",
  "medium": "RTVE",
  "rss_url": "https://www.rtve.es/rss/portada.xml",
  "iptc_category": "politics"
}
```

**Respuesta esperada:**
```json
{
  "id": 1,
  "name": "RTVE",
  "rss_url": "https://www.rtve.es/rss/portada.xml"
}
```

---

#### Listar fuentes
Endpoint: `GET /api/v1/sources`

Debe devolver al menos la fuente creada anteriormente.

---

#### Lanzar la ingesta RSS
Endpoint: `POST /api/v1/sources/{source_id}/fetch`

En Swagger:
- Pulsa **"Try it out"**
- Introduce en `source_id` el valor `1`
- Ejecuta la petición

**Respuesta esperada:**
```json
{
  "source_id": 1,
  "new_items": 0
}
```

> `new_items` indica cuántas noticias nuevas se han insertado. Puede ser `0` si no hay novedades o si el feed ya estaba registrado.

---

#### Listar noticias almacenadas
Endpoint: `GET /api/v1/news`

**Ejemplo de respuesta:**
```json
[
  {
    "id": 1,
    "title": "...",
    "link": "https://...",
    "summary": "...",
    "published": "2026-03-25T19:30:00",
    "source_id": 1
  }
]
```

> Si el array está vacío `[]` y `new_items` fue `0`, significa que el feed no ha aportado entradas nuevas.

---

## Notas sobre Docker (estado actual)

Hay configuración Docker (`Dockerfile`, `docker-compose.yml`) para levantar:

- **app:** backend FastAPI con Uvicorn.
- **db:** PostgreSQL 16.
- **pgadmin:** interfaz web para la base de datos.

Durante el desarrollo de Sprint 2 se ha priorizado la ejecución local con **SQLite** para validación rápida.
La integración completa con PostgreSQL en Docker (del Sprint 1) se mantiene compatible y puede activarse cambiando la variable `DATABASE_URL`.

---

## Resumen de lo entregado en Sprint 2

- Nuevos modelos: `InformationSource` y `NewsItem`.
- Servicio `fetch_feed` basado en `feedparser` para ingerir noticias desde feeds RSS.
- Endpoints REST:
  - CRUD mínimo de fuentes (`POST` / `GET /api/v1/sources`).
  - Ingesta de una fuente (`POST /api/v1/sources/{source_id}/fetch`).
  - Consulta de noticias (`GET /api/v1/news`).
- Pruebas verificadas vía Swagger (`http://localhost:9000/docs`) con fuente real (RTVE).

---

## Seguimientos

*(Espacio para observaciones, mejoras e hitos futuros del proyecto.)*
