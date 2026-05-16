# ADR 001: Elección del lenguaje de programación

## Estado
**Aceptado**

## Contexto

NEWSRADAR es un sistema que necesita:

- Procesar y analizar grandes volúmenes de texto (noticias, posts de redes sociales, RSS, etc.)
- Integrarse fácilmente con modelos de lenguaje, APIs de IA y herramientas de procesamiento de lenguaje natural (LLMs, embeddings, clasificación, NER, sentiment analysis…)
- Permitir prototipado rápido en fases iniciales
- Facilitar la incorporación de nuevos miembros al equipo con curva de aprendizaje razonable
- Tener buena disponibilidad de librerías maduras para web scraping, manejo de datos, pipelines de ML, bases de datos, APIs REST/GraphQL, etc.
- Ser compatible con el ecosistema actual de herramientas de IA (2025–2026)

Se evaluaron principalmente los siguientes lenguajes:

- Python
- JavaScript/TypeScript (Node.js)
- Go
- Rust
- Julia (para partes muy numéricas)

## Decisión

**Usaremos Python 3.11+ (preferiblemente la versión más reciente estable al momento de cada actualización importante del proyecto)**

## Justificación

| Criterio                         | Python | JavaScript/TS | Go    | Rust  | Comentario breve                                     |
| -------------------------------- | ------ | ------------- | ----- | ----- | ---------------------------------------------------- |
| Ecosistema de IA / LLMs          | ★★★★★  | ★★★☆☆         | ★★☆☆☆ | ★★☆☆☆ | LangChain, LlamaIndex, HuggingFace, OpenAI SDK, etc. |
| Librerías de procesamiento texto | ★★★★★  | ★★★☆☆         | ★★☆☆☆ | ★★☆☆☆ | spaCy, NLTK, transformers, sentence-transformers     |
| Velocidad de desarrollo          | ★★★★★  | ★★★★☆         | ★★★☆☆ | ★★☆☆☆ | Prototipado muy rápido                               |
| Curva de aprendizaje equipo      | ★★★★★  | ★★★★☆         | ★★★★☆ | ★★☆☆☆ | Muy conocida en data/IA                              |
| Mantenimiento a medio plazo      | ★★★★☆  | ★★★★☆         | ★★★★★ | ★★★★☆ | Gran comunidad                                       |
| Rendimiento en producción        | ★★★☆☆  | ★★★☆☆         | ★★★★★ | ★★★★★ | Suficiente con optimizaciones                        |
| Despliegue y contenedores        | ★★★★☆  | ★★★★★         | ★★★★★ | ★★★★☆ | Muy bueno con Docker/Poetry/uv                       |

## Consecuencias

### Positivas

- Acceso inmediato al mejor ecosistema actual de herramientas de IA y procesamiento de lenguaje natural
- Desarrollo y prototipado significativamente más rápido en las primeras fases
- Gran cantidad de tutoriales, ejemplos y código reutilizable disponible
- Facilidad para integrar scrapers, APIs, bases vectoriales (Chroma, Weaviate, Pinecone, Qdrant…), LLMs locales y en la nube
- Comunidad muy activa en data engineering, MLOps y periodismo de datos

### Negativas / Mitigadas

- Menor rendimiento bruto comparado con Go/Rust → se mitiga usando Rust/Go/Cython en bottlenecks muy concretos si aparecen (scraping masivo, cómputo intensivo)
- Mayor consumo de memoria en algunos casos → monitorear y optimizar con uv + dependencias modernas + profiling
- GIL puede limitar paralelismo CPU → usar multiprocessing, asyncio, o herramientas como Polars / Dask cuando sea necesario

## Alternativas consideradas y rechazadas

- **TypeScript/Node.js** → muy buen soporte web/full-stack, pero ecosistema IA claramente inferior en 2026
- **Go** → excelente rendimiento y simplicidad, pero librerías de NLP/IA muy limitadas
- **Rust** → máximo rendimiento y seguridad, pero curva de aprendizaje alta y ecosistema IA aún inmaduro para nuestro caso de uso
- **Mezcla de lenguajes (Python + Go/Rust)** → posible en el futuro para partes críticas, pero aumenta complejidad → descartado para la fase inicial

## Referencias

- [Python vs Go for data processing pipelines (2025 comparatives)](https://...)
- [State of AI tooling 2026 – Python dominance](https://...)
- [LangChain / LlamaIndex ecosystem overview](https://...)

<!--
   Fecha de decisión: 2026-03-XX
   Quién propuso: ...
   Quién decidió: ...
-->


# ADR 002: Almacenamiento de la información y búsqueda semántica

## Estado
**Aceptado** (Pendiente de implementación)

## Contexto

Según el documento oficial del proyecto (páginas 2-5):

- El sistema debe **monitorizar** canales RSS y detectar noticias que contengan los descriptores de una alerta (palabra clave + 3-10 sinónimos/relacionados generados por IA).
- Se requiere **clasificación** automática de cada noticia en categorías IPTC Media Topics.
- Se necesita visualizar **temas candentes** (nubes de palabras por categoría) y estadísticas globales.
- Hay que almacenar la “información” (noticias: título, resumen, fecha, fuente, texto, categoría IPTC, etc.) de forma eficiente y searchable.
- El proyecto exige **dos sistemas gestores de datos**:
  - Uno para **entidades del sistema** (usuarios, roles, alertas, fuentes RSS).
  - Otro para **almacenamiento de la información** (noticias).

Ya tenemos en Fase 1 (ver código actual):
- **PostgreSQL + SQLAlchemy** como base de datos relacional para entidades (usuarios, roles).
- FastAPI como backend.
- Uso intensivo de IA generativa obligatorio (recomendación de sinónimos, clasificación).

Se evaluaron soluciones que permitan:
- Búsqueda por palabras clave + **búsqueda semántica** (para sinónimos y relevancia).
- Filtrado por metadatos (fecha, fuente, categoría IPTC, alerta).
- Agregaciones rápidas para word clouds y estadísticas.
- Escalabilidad razonable para un proyecto universitario (deadline 25 mayo 2026).

## Decisión

**Usaremos PostgreSQL + extensión pgvector** como única base de datos.

- Tablas relacionales (ya existentes) para entidades del sistema.
- Nueva tabla `news_items` (o extensión) + **pgvector** para almacenar embeddings de las noticias + búsqueda híbrida (full-text + vectorial).
- No introduciremos segundo servicio (Qdrant, Elasticsearch, etc.).

## Justificación

| Criterio del proyecto                      | pgvector (Postgres)  | Qdrant         | Elasticsearch  | Chroma         | Comentario clave del PDF              |
| ------------------------------------------ | -------------------- | -------------- | -------------- | -------------- | ------------------------------------- |
| Dos sistemas de datos requeridos           | Sí (un solo motor)   | Sí (2 motores) | Sí (2 motores) | Sí (2 motores) | Simplifica ops                        |
| Búsqueda semántica + sinónimos IA          | ★★★★★                | ★★★★★          | ★★★★           | ★★★★           | Suficiente para volumen universitario |
| Full-text + hybrid search                  | ★★★★★ (con tsvector) | ★★★★★          | ★★★★★          | ★★★            | Alertas + word clouds                 |
| Filtrado por metadatos (categoría, fecha…) | ★★★★★                | ★★★★★          | ★★★★★          | ★★★★           | IPTC, fuentes                         |
| Agregaciones / word clouds / estadísticas  | ★★★★★ (SQL nativo)   | Media          | Excelente      | Baja           | Necesario para dashboard              |
| Complejidad operativa (estudiantes)        | Muy baja             | Media          | Alta           | Baja           | Deadline mayo 2026                    |
| Docker + docker-compose actual             | Ya existe            | Extra servicio | Extra servicio | Extra servicio | Mínimo overhead                       |
| Coste / mantenimiento                      | Gratis               | Gratis         | Medio          | Gratis         | Proyecto académico                    |
| Integración LangChain / IA                 | Excelente            | Excelente      | Buena          | Buena          | Uso intensivo IA requerido            |

**Razones principales para elegir pgvector**:
- Cumple literalmente el requisito de “dos sistemas gestores de datos” sin duplicar infraestructura (Postgres ya está en producción y en docker-compose).
- Soporte oficial de embeddings + búsqueda semántica desde 2024-2025 (HNSW + ivfflat).
- Full-text search nativo (`tsvector`) + vector similarity en la misma consulta → ideal para alertas (keyword + semántico).
- Agregaciones SQL ultra-rápidas para nubes de palabras y estadísticas del dashboard.
- Zero configuración extra en producción universitaria.
- Fácil integración con SQLAlchemy 2.0 y FastAPI (ya usado).

## Consecuencias

### Positivas
- Todo el stack en un solo contenedor → más sencillo de mantener, desplegar y depurar.
- Transacciones ACID entre metadatos y embeddings.
- Búsquedas híbridas muy rápidas incluso con miles de noticias.
- Word clouds y estadísticas se resuelven con simples queries SQL.
- Camino directo a producción con un único servicio PostgreSQL.

### Negativas / Mitigadas
- Rendimiento ligeramente inferior a Qdrant/Elasticsearch en >1M documentos → no relevante para este proyecto (volumen esperado: cientos/miles de noticias).
- Gestión de embeddings en la misma DB → se mitigará con índices dedicados y limpieza periódica.
- Si en futuro crece mucho → migración a Qdrant/Elasticsearch será sencilla (exportar embeddings).

## Alternativas consideradas y rechazadas

- **Qdrant** → Excelente, pero introduce segundo servicio (más complejidad para estudiantes).
- **Elasticsearch** → Recomendado en el PDF (pág. 5), pero overhead operativo alto y curva de aprendizaje innecesaria.
- **Chroma** → Demasiado simple, pierde en agregaciones y filtrado avanzado.
- **MongoDB** → No tiene vector search nativo tan potente como pgvector en 2026.

## Referencias
- Documento oficial del proyecto (páginas 2-5 y Anexo I).
- pgvector documentation[](https://github.com/pgvector/pgvector)
- SQLAlchemy + pgvector integration examples 2026.
- Benchmarks pgvector vs Qdrant 2025 (para proyectos de tamaño medio).

Fecha de decisión: 12 marzo 2026
Propuesto por: Equipo NEWSRADAR
Aceptado por: [nombre del líder]


# ADR 003: Estrategia de ingestión de fuentes RSS y orquestación de monitorización continua

## Estado
**Aceptado** (Pendiente de implementación)

## Contexto

Según el documento oficial del proyecto (páginas 2-5 y 3.1):

- El sistema debe **monitorizar de forma continua** canales RSS mediante un proceso descrito por una **expresión cron**.
- Para cada alerta definida (palabra clave + 3-10 sinónimos/relacionados generados por IA):
  - Detectar noticias que contengan cualquiera de los descriptores.
  - Clasificar la noticia en categoría IPTC (de la alerta o de la fuente).
  - Almacenar la noticia y generar notificaciones (email + buzón interno).
- El sistema debe incluir **mínimo 100 canales RSS** iniciales (cubriendo todas las categorías IPTC de primer nivel).
- Requisitos DevOps: automatización, Docker, pipeline, mínimo intervención manual.
- Ya tenemos en Fase 1-2:
  - FastAPI + PostgreSQL + pgvector (ADR 002).
  - Autenticación JWT y gestión básica de usuarios/alertas (por implementar).
  - Uso intensivo de IA generativa obligatorio (recomendación de sinónimos y clasificación).

Se necesita un mecanismo fiable para:
- Parsear RSS periódicamente.
- Ejecutar jobs según cron por alerta.
- Procesar en background (embeddings, clasificación, notificaciones).
- Evitar duplicados (URL o hash del contenido).
- Escalar a cientos de fuentes sin bloquear la API.

## Decisión

**Usaremos:**
- **feedparser** para parsear RSS (estándar de facto).
- **APScheduler (AsyncIOScheduler)** integrado en el startup de FastAPI para orquestación de tareas periódicas.
- **BackgroundTasks + Celery** (opcional en Fase 3) solo para tareas pesadas de IA (embedding + clasificación).
- Todo dentro del mismo contenedor Docker (sin broker externo en fase inicial).

**No usaremos** soluciones externas como Scrapy, Airflow o cron del sistema operativo.

## Justificación

| Criterio del proyecto                | APScheduler + feedparser   | Celery + Redis | Airflow | Cron + script separado | Comentario clave del PDF      |
| ------------------------------------ | -------------------------- | -------------- | ------- | ---------------------- | ----------------------------- |
| Expresión cron por alerta            | ★★★★★                      | ★★★★★          | ★★★★★   | ★★★                    | Requerido explícitamente      |
| Integración directa con FastAPI      | ★★★★★                      | ★★★★           | ★★      | ★★★                    | Startup event ya existe       |
| Zero servicios extra (Docker simple) | ★★★★★                      | ★★★            | ★       | ★★★★★                  | Proyecto académico            |
| Procesamiento background de IA       | ★★★★ (con BackgroundTasks) | ★★★★★          | ★★★★    | ★★★                    | Uso intensivo IA              |
| Manejo de duplicados y idempotencia  | ★★★★★                      | ★★★★★          | ★★★★★   | ★★★★                   | Necesario para notificaciones |
| Facilidad de pruebas y CI/CD         | ★★★★★                      | ★★★★           | ★★★     | ★★★                    | DevOps obligatorio            |
| Overhead operativo (estudiantes)     | Muy bajo                   | Medio          | Alto    | Bajo                   | Deadline mayo 2026            |

**Razones principales para elegir APScheduler + feedparser**:
- Extremadamente ligero y 100% Python → se integra en 5 líneas en `main.py` (ya tenemos `@app.on_event("startup")`).
- Soporta cron nativo por alerta (`cron='0 * * * *'` por ejemplo).
- No requiere Redis/RabbitMQ en fase inicial → cumple “desplegar con un único comando”.
- feedparser es la librería más madura y robusta para RSS (maneja errores, fechas, enclosures, etc.).
- Fácil escalar después a Celery si el volumen crece (solo cambiar el job a task).

## Consecuencias

### Positivas
- Monitorización real-time por alerta sin infraestructura extra.
- Código limpio: un `RSSIngestorService` inyectado como dependencia.
- Fácil seeding inicial de 100+ fuentes RSS (script de inicialización).
- Integración directa con pgvector: al detectar match → embed + store + notificar.
- Dashboard de estadísticas (nº noticias, fuentes) se actualiza automáticamente.

### Negativas / Mitigadas
- APScheduler corre en el mismo proceso → si hay 50 alertas muy frecuentes podría consumir CPU → mitigar con rate-limiting y jobs agrupados (una sola tarea global cada X minutos que procesa todas las alertas activas).
- Posibles rate-limits de fuentes RSS → implementar backoff y caché de última fecha procesada.
- En producción futura → migrar jobs pesados a Celery + Redis (ADR futuro si es necesario).

El detalle del scheduler y su configuración práctica se recoge en ADR 005 (APScheduler).

## Alternativas consideradas y rechazadas

- **Celery + Redis desde el principio** → Muy robusto, pero añade 2 servicios Docker y complejidad innecesaria para el volumen esperado.
- **Airflow** → Sobredimensionado para un proyecto universitario.
- **Cron del sistema + script Python separado** → Funciona, pero pierde integración con FastAPI y base de datos (más difícil logging y estado).
- **Scrapy + scheduler** → Overkill (pensado para web crawling masivo, no RSS simple).

## Referencias
- Documento oficial NEWSRADAR (págs. 2-5 y 3.1).
- APScheduler docs + FastAPI integration examples 2026.
- feedparser documentation.
- Ejemplo oficial del proyecto (newsradar_api.zip) – API REST ya usa FastAPI.

Fecha de decisión: 12 marzo 2026
Propuesto por: Equipo NEWSRADAR
Aceptado por: [tu nombre]

<!-- Próximo paso: crear app/services/rss_ingestor.py y registrar scheduler en main.py -->

# ADR 004: Elección de motor de IA generativa — Groq (Llama 3.3 70B)

## Estado
**Aceptado (revisado 2026-05-11)**

## Contexto

El enunciado del proyecto exige "hacer un uso intensivo de tecnologías de IA generativa" (Anexo I). En Fase 1 se requiere que la API sea capaz de recomendar entre 3 y 10 términos relacionados/sinónimos para una alerta.

La decisión inicial era usar Gemini (Google). Durante la implementación se identificaron problemas prácticos:

1. **Quota 0 en free tier**: el proyecto académico de Google Cloud tiene `limit: 0` para todos los modelos de Gemini, lo que impide cualquier llamada desde el entorno universitario.
2. **Restricciones regionales**: las cuentas de educación de la UC3M tienen limitaciones adicionales en Google AI Studio.

## Decisión

Usar **Groq** con el modelo `llama-3.3-70b-versatile` como proveedor de IA generativa, con fallback a un diccionario IPTC propio si la API no está disponible. La clave se configura mediante `GROQ_API_KEY` en `.env`.

## Justificación

- **Free tier real**: Groq ofrece miles de tokens gratuitos al día sin restricciones académicas.
- **Velocidad**: Groq es uno de los proveedores de inferencia más rápidos disponibles (tokens/s muy superiores a otros).
- **Llama 3.3 70B**: modelo open source de Meta con excelente calidad para tareas en español.
- **Fallback robusto**: si `GROQ_API_KEY` no está configurada o la API falla, el sistema usa el diccionario IPTC sin interrumpir el servicio.
- **CI sin dependencias externas**: en CI no se configura `GROQ_API_KEY`, por lo que los tests usan el fallback del diccionario y pasan sin red ni secretos.

## Consecuencias

- Positivas:
  - Cumple el requisito de IA generativa con LLM real en producción.
  - Sugerencias dinámicas y contextualmente relevantes para cualquier keyword.
  - Sin coste en CI; sin riesgo de romper el pipeline por rate limits.

- Negativas / Riesgos:
  - Dependencia de Groq como proveedor externo en producción.
  - La clave `GROQ_API_KEY` debe configurarse en `.env` para activar Groq; sin ella se usa el diccionario.

## Implementación

```python
# app/services/ai.py
def generate_synonyms(keyword: str) -> list[str]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return _fallback_synonyms(keyword)  # diccionario IPTC
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", ...
        )
        ...
    except Exception:
        return _fallback_synonyms(keyword)
```

## Alternativas consideradas

- **Gemini / Google AI** — Descartado por quota 0 en el proyecto académico de la UC3M.
- **OpenAI / Anthropic** — Requieren tarjeta de crédito para free tier.
- **Datamuse (thesaurus)** — Rechazado porque no es IA generativa según el enunciado.
- **Diccionario IPTC puro** — Usado como fallback; insuficiente como solución principal.

## Fecha

2026-03-12 — propuesta inicial (Gemini)
2026-04-20 — revisada como diccionario IPTC propio
2026-05-11 — implementada con Groq + fallback al diccionario

# ADR 005: Elección de scheduler — APScheduler (Background)

## Estado
**Aceptado (Fase 1)**

## Contexto

La aplicación necesita ejecutar tareas periódicas de monitorización de alertas (detección de noticias) en Fase 1. Las opciones consideradas incluyen correr un worker externo (Celery + broker), usar un servicio cron externo, o usar un scheduler embebido en el proceso web.

## Decisión

Para la Fase 1 se usará `APScheduler` en modo `BackgroundScheduler` ejecutándose dentro del proceso FastAPI. La integración es ligera y permite ejecutar la función `monitor_alerts` cada X segundos/minutos.

Este ADR complementa ADR 003 (ingestión RSS y orquestación de monitorización), que describe el flujo de ingestión y requisitos de cron por alerta.

## Justificación

- Rápida de desplegar y suficiente para pruebas / fase inicial.
- Evita infra adicional (RabbitMQ/Redis) y complejidad de despliegue en Fase 1.
- Permite iterar rápidamente y validar la lógica de detección en el mismo contenedor.

## Consecuencias

- Positivas:
  - Menos infra y menos componentes a operar.
  - Inicio automático junto con la app, sencillo de debug.

- Negativas / Riesgos:
  - No tolerante a restarts del proceso: las tareas programadas se pierden si el proceso muere. Para producción es recomendable migrar a Celery/Beat o un gestor de tareas externo.
  - Aún con APScheduler, si la carga es alta podría ser necesario separar worker.

## Migración futura

- Migrar a Celery/Redis o un sistema de colas si necesitamos fiabilidad, reintentos y escalado horizontal.

## Fecha

2026-03-12

# ADR 007: Permisos de gestores — enfoque inicial y migración a roles

## Estado
**Aceptado (Fase 1)**

## Contexto

Al principio del desarrollo se necesita una forma simple de restringir quién puede crear/listar alertas (gestores). Para acelerar la entrega, se eligió un método rápido basado en la variable de entorno `MANAGERS` que contiene una lista de emails permitidos.

## Decisión

Fase 1: usar `MANAGERS` (emails) como control de acceso para los endpoints de gestión de alertas.

Plan de migración: en Fase 2 migrar a un sistema basado en la tabla `roles` y relaciones many-to-many entre `users` y `roles`, con comprobaciones RBAC en los endpoints.

## Justificación

- Rápido de implementar y suficiente para la entrega del objetivo 1.
- Evita añadir complejidad de migraciones y lógica RBAC inmediata.

## Consecuencias

- Positivas:
  - Entrega rápida y control simple de acceso.

- Negativas:
  - No escalable ni auditable a largo plazo.
  - Requiere migración y cambios en código/DB cuando se active RBAC.

## Migración propuesta

- Añadir tabla `roles` (ya existe en DB) y tabla intermedia `user_roles`.
- Crear middleware/dependencies que verifiquen roles desde DB en lugar de `MANAGERS`.

## Fecha

2026-03-12

# ADR 008: Elección de base de datos — PostgreSQL + SQLAlchemy

## Estado
**Aceptado**

## Contexto

El proyecto necesita una base de datos relacional fiable para almacenar usuarios, alertas y noticias detectadas. Se requiere compatibilidad con migraciones (Alembic) y facilidad para consultas y relaciones.

## Decisión

Usar PostgreSQL como base de datos relacional y SQLAlchemy como ORM en el backend. Las migraciones se gestionarán con Alembic.

## Justificación

- PostgreSQL es robusto y ampliamente apoyado en entornos académicos y de producción.
- SQLAlchemy (v2) ofrece potencia y flexibilidad para modelar relaciones y usar sesiones.
- Alembic facilita versionado del esquema y despliegues reproducibles.

## Consecuencias

- Positivas:
  - Buen soporte para relaciones y consultas complejas.
  - Escalable y compatible con la mayoría de infraestructuras en la nube.

- Consideraciones:
  - Requiere administración de la instancia y backups.
  - Para índices de búsquedas semánticas o vectores se usará la extensión `pgvector` (ver ADR 002), sin añadir otro motor externo.

## Fecha

2026-03-12

# ADR 009: Autenticación y tokens — JWT

## Estado
**Aceptado**

## Contexto

La aplicación requiere autenticación para endpoints sensibles (registro, login, gestión de alertas). El sistema debe ser sencillo, interoperable y alineado con requisitos del curso (uso de JWT en Fase 1).

## Decisión

Usar JSON Web Tokens (JWT) para autenticación y autorización básica. Los tokens se firmarán con `HS256` (algoritmo configurable vía `ALGORITHM`) y una `SECRET_KEY` gestionada por variables de entorno.

## Justificación

- JWT es un estándar ampliamente utilizado y suficiente para la Fase 1.
- Fácil de integrar con `python-jose` y `fastapi`.

## Consecuencias

- Requiere proteger la `SECRET_KEY` y considerar rotación de claves en fases posteriores.
- Para permisos más finos (roles, scopes) se añadirá validación RBAC en futuros ADRs.

## Implementación

- Uso de `python-jose` para firmado y verificación.
- Dependencia en variables de entorno `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.

## Fecha

2026-03-12

# ADR 010: Docker y despliegue en contenedor

## Estado
**Aceptado**

## Contexto

El proyecto debe ser reproducible y desplegable en contenedores. Ya existe un `Dockerfile` y `docker-compose.yml` parcial; hay que documentar la estrategia mínima para Fase 1.

## Decisión

Usar Docker + Docker Compose para el despliegue local y pruebas. Cada servicio (API, DB) correrá en contenedores separados y la configuración principal se pasará por variables de entorno o `.env`.

## Justificación

- Facilita replicar el entorno del profesor y pruebas de integración.
- Permite encapsular dependencias (Postgres, app) sin modificar la máquina del evaluador.

## Consecuencias

- Mantener `Dockerfile` pequeño y la `requirements.txt` precisa.
- Documentar en README cómo levantar la aplicación con `docker-compose up --build`.

## Migración futura

- Para producción, añadir CI/CD que construya imágenes y despliegue (registry, tags), y supervisión/healthchecks.

## Fecha

2026-03-12

# ADR 011: Migrations — Alembic

## Estado
**Aceptado**

## Contexto

La evolución del esquema de BD requiere control de versiones y migraciones reproducibles.

## Decisión

Usar Alembic para gestionar migraciones de SQLAlchemy. Mantener las migraciones en `alembic/versions` y ejecutar `alembic revision --autogenerate` al introducir cambios en los modelos.

## Justificación

- Alembic es la solución estándar junto a SQLAlchemy.
- Permite mantener un historial de cambios y facilitar despliegues con migración automática en CI/CD.

## Consecuencias

- Incluir pasos en README para ejecutar `alembic upgrade head` como parte del despliegue.

## Fecha

2026-03-12

# ADR 012: Seed inicial — admin y roles

## Estado
**Aceptado**

## Contexto

Para probar la aplicación y cumplir Fase 1 se necesita un usuario administrador y roles básicos (`admin`, `user`).

## Decisión

Crear un seed inicial que inserte roles `admin` y `user` y un usuario `admin@newsradar.com` en el arranque (si no existen).

## Justificación

- Facilita pruebas y revisión por parte del profesor sin necesidad de UI.

## Consecuencias

- El seed se ejecuta en `startup` de la app y debe ser idempotente.

## Fecha

2026-03-12

# ADR 013: Versionado de API y rutas

## Estado
**Aceptado**

## Contexto

Se necesita una convención mínima para versionar endpoints y permitir evolución sin romper clients.

## Decisión

Prefijar todas las rutas con `/api/v1/` para la Fase 1. Las futuras versiones incrementarán el número (`/api/v2/`) y se documentarán en el changelog.

## Justificación

- Convención simple y explícita, compatible con FastAPI y routers modularizados.

## Consecuencias

- Mantener compatibilidad hacia atrás cuando se añadan versiones.

## Fecha

2026-03-12

# ADR 014: Logging y monitoring básicos

## Estado
**Propuesto**

## Contexto

Se requiere visibilidad de errores y métricas mínimas para depuración durante el desarrollo y entrega.

## Decisión

Usar el `logging` estándar de Python configurado en nivel `INFO` por defecto y exportar métricas básicas a la salida estándar para que el orquestador (Docker) y el profesor puedan ver logs. En paralelo, documentar la integración futura con Prometheus/Grafana.

## Justificación

- Rápido de implementar y suficiente para Fase 1.

## Consecuencias

- Logs estructurados (JSON) pueden añadirse si se requiere en entregas futuras.

## Fecha

2026-03-12
