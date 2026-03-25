## Plan: Sprint 2 mínimo

TL;DR - Implementar modelo de fuente y noticias, endpoints para crear/listar fuentes, un servicio que lea 1–3 RSS reales y persista noticias en BD; dejar verificaciones manuales (Swagger/curl).

**Steps**
1. Consolidar modelos: mover/añadir `InformationSource` y `NewsItem` al paquete `app.models` (archivo `app/models/models.py`) y asegurar imports. *depende de revisar `app/models/models.py`*.
2. Corregir imports en [app/main.py](app/main.py): importar `InformationSource`, `NewsItem` desde `app.models.models`.
3. Añadir endpoints en [app/main.py](app/main.py):
   - `POST /api/v1/sources` (crear fuente) — ya existe, validar import.
   - `GET /api/v1/sources` (listar) — ya existe, validar import.
   - `POST /api/v1/sources/{source_id}/fetch` (trigger fetch) — nuevo endpoint que llama al servicio.
   - `GET /api/v1/news` (listar noticias) — simple, paginado opcional.
4. Servicio fetcher: crear `app/services/fetcher.py` con función `fetch_feed(db: Session, source_id: int)` que use `feedparser` para parsear feed, cree `NewsItem` evitando duplicados por `link` y convierta `published_parsed` a `datetime`.
5. Añadir dependencia `feedparser` a `requirements.txt` si no está presente.
6. Esquemas Pydantic mínimos: `app/schemas/source.py` y `app/schemas/news.py` para validación/serialización de requests y responses.
7. Verificación manual y pruebas:
   - Levantar la app: `uvicorn app.main:app --reload` o `docker-compose up --build`.
   - Usar Swagger `/docs` para crear una fuente (ejemplo RTVE), luego `POST /api/v1/sources/{id}/fetch` y `GET /api/v1/news` para ver las noticias.

**Relevant files**
- [app/main.py](app/main.py)
- [app/models/models.py](app/models/models.py)
- [models.py](models.py)
- [app/core/database.py](app/core/database.py)
- [requirements.txt](requirements.txt)
- `app/services/fetcher.py` (nuevo)
- `app/schemas/` (nuevo)

**Verification**
1. Crear fuente via Swagger `POST /api/v1/sources` con payload: {"name":"RTVE","medium":"RTVE","rss_url":"https://www.rtve.es/rss/","iptc_category":"politics"}.
2. `GET /api/v1/sources` → la fuente aparece.
3. `POST /api/v1/sources/{id}/fetch` → devuelve `new_items` > 0.
4. `GET /api/v1/news` → ver noticias almacenadas (campos `title`, `link`, `summary`, `published`, `source_id`).

**Decisions / Assumptions**
- Usaremos la creación automática de tablas `Base.metadata.create_all(bind=engine)` en startup.
- Duplicados se detectan por `NewsItem.link`.
- Limitar a los primeros 10 entries por fetch para evitar sobrecarga.
- Guardar `published` si `published_parsed` está presente (convertir a `datetime`).

**Further Considerations**
1. ¿Prefieres que mueva las clases desde `models.py` (root) a `app/models/models.py`, o que simplemente importe `models.py` desde `app.main`? Recomiendo mover para mantener el paquete `app` coherente.
2. ¿Quieres que proteja los endpoints de creación/fetch con autenticación ahora, o lo dejamos público para pruebas rápidas? Recomiendo dejar público para el MVP y añadir protección en Sprint 3.



### Siguientes pasos para probar localmente

1. Instalar dependencias / configurar entorno
   - Asegúrate de tener las variables en `.env` (por ejemplo `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`).

2. Levantar la aplicación
   - Usando Docker:
     - Ejecuta: `docker compose up --build`
     - Una vez arrancado, la API estará disponible en `http://localhost:8000`.
   - O en local (sin Docker, opcional):
     - Crear y activar entorno virtual.
     - Instalar dependencias: `pip install -r requirements.txt`.
     - Ejecutar: `uvicorn app.main:app --reload`.

3. Probar API en Swagger (`http://localhost:8000/docs`)

   - `POST /api/v1/sources` con un ejemplo de fuente RSS:
     ```json
     {
       "name": "RTVE",
       "medium": "RTVE",
       "rss_url": "https://www.rtve.es/rss/portada.xml",
       "iptc_category": "politics"
     }
     ```
   - `POST /api/v1/sources/{id}/fetch`
     - Usa el `id` devuelto al crear la fuente.
     - Respuesta esperada: objeto JSON con `new_items` indicando cuántas noticias nuevas se han guardado.

   - `GET /api/v1/news`
     - Devuelve la lista de noticias guardadas en la base de datos (título, link, resumen, fecha de publicación, id de la fuente).
