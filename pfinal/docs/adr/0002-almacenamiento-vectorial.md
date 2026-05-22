# ADR 002: Elección del almacenamiento vectorial (Vector Database)

## Estado
**Aceptado — Implementado con PostgreSQL como motor dual (2026-05)**

## Contexto

El enunciado (§4) exige **dos sistemas gestores de datos**:

> *"Un sistema gestor de datos para el almacenamiento de la información"* (noticias, matches, notificaciones)
> *"Un sistema gestor de datos para el almacenamiento de las entidades del sistema"* (usuarios, alertas, fuentes, categorías)

En Fase 1 ya se usa:

- **PostgreSQL** como base de datos relacional principal (SQLAlchemy 2.0 + psycopg2)
- **FastAPI** como framework web
- Autenticación JWT básica y modelo de usuario/rol mínimo

## Decisión final

**PostgreSQL cubre ambos requisitos del enunciado** con dos roles diferenciados dentro del mismo motor:

| Rol | Tablas | Requisito cubierto |
|---|---|---|
| Gestión de entidades | `users`, `roles`, `alerts`, `information_sources`, `rss_channels`, `categories` | "almacenamiento de entidades del sistema" |
| Gestión de información procesada | `news_items`, `alert_news`, `notifications` | "almacenamiento de la información" |

El enunciado no exige que sean tecnologías distintas, solo que haya dos sistemas lógicos separados. PostgreSQL actúa como ambos de forma coherente: las entidades de configuración (alertas, fuentes) son distintas conceptualmente de la información procesada (noticias indexadas, notificaciones generadas).

La detección de noticias relevantes se hace mediante matching por palabras clave con expresiones regulares (`\bpalabra\b`, `re.UNICODE`) en `pfinal/app/services/alertLogic.py`.

### Por qué se descartó Qdrant/vector store separado

- Añade un segundo servicio Docker (complejidad operativa) sin aportar valor al caso de uso actual.
- El matching por regex es suficiente para los descriptores de alertas (3–10 palabras por alerta).
- El plazo (25 mayo 2026) no justificaba la infraestructura adicional.

## Propuesta original de Qdrant (archivada para referencia)

## Justificación

Se evaluaron las opciones más relevantes en 2026 para aplicaciones de news/RAG:

| Criterio                           | Qdrant                | Chroma                         | Weaviate  | pgvector (PostgreSQL) | Pinecone (managed) | Milvus    | Comentario breve                             |
| ---------------------------------- | --------------------- | ------------------------------ | --------- | --------------------- | ------------------ | --------- | -------------------------------------------- |
| Open-source / self-hosted          | Sí (Apache 2.0, Rust) | Sí (fácil Python)              | Sí        | Sí (ext. Postgres)    | No                 | Sí        | Preferimos evitar vendor lock-in inicial     |
| Rendimiento (HNSW)                 | ★★★★★                 | ★★★★☆                          | ★★★★☆     | ★★★☆☆                 | ★★★★★              | ★★★★★     | Qdrant destaca en benchmarks recientes       |
| Filtrado por payload/metadata      | ★★★★★ (muy potente)   | ★★★★☆                          | ★★★★★     | ★★★★☆                 | ★★★★★              | ★★★★☆     | Crucial para filtrar por fecha/fuente/idioma |
| Hybrid search (vector + keyword)   | Sí (BM25 + vector)    | Limitado                       | Excelente | Con extensión extra   | Sí                 | Sí        | Útil para noticias                           |
| Integración LangChain / LlamaIndex | Excelente             | Muy buena                      | Excelente | Buena                 | Excelente          | Buena     | Ecosistema IA 2026                           |
| Complejidad operativa inicial      | Media (Docker)        | Baja (in-memory o persistente) | Media     | Muy baja (misma DB)   | Muy baja           | Alta      | Fase inicial → simplicidad                   |
| Escalabilidad horizontal           | Muy buena             | Media                          | Buena     | Depende de Postgres   | Automática         | Excelente | Crecimiento futuro                           |
| Costo inicial                      | Gratis                | Gratis                         | Gratis    | Gratis                | $ (tras free tier) | Gratis    | —                                            |

**Razones principales para elegir Qdrant en NEWSRADAR:**

- Excelente balance entre rendimiento, facilidad de uso y capacidades de filtrado (payload filtering) → ideal para noticias con muchos metadatos (fecha, fuente, idioma, país, relevancia…)
- Implementado en Rust → bajo consumo de memoria y alta velocidad en búsquedas aproximadas (HNSW)
- Soporte nativo para hybrid search (vector + keyword/BM25) → muy útil cuando el usuario busca por palabras clave + semántica
- Buena documentación y clientes oficiales (Python, async support)
- Fácil de correr localmente con Docker y en producción (Kubernetes si crece)
- Comunidad activa y adopción creciente en aplicaciones RAG 2025–2026

## Consecuencias

### Positivas

- Búsquedas semánticas rápidas y precisas desde el inicio
- Posibilidad de filtrar resultados por fecha, fuente, idioma, organización, etc. sin perder rendimiento
- Integración sencilla con FastAPI vía cliente Python oficial o LangChain
- Posibilidad de empezar con despliegue simple (Docker en docker-compose) junto a PostgreSQL
- Camino claro hacia producción: Qdrant Cloud si se necesita zero-ops más adelante

### Negativas / Mitigadas

- Introduce un segundo datastore (PostgreSQL + Qdrant) → mitigar con buena abstracción (repositorio o servicio dedicado) y documentación
- Requiere gestionar embeddings consistentes (misma dimensión, mismo modelo) → definir modelo de embedding fijo desde el principio (ej. sentence-transformers/multilingual-e5-large-instruct)
- Consumo adicional de RAM/CPU en scraping + indexing masivo → monitorear y optimizar batching
- No es 100% integrado en PostgreSQL (a diferencia de pgvector) → aceptable en Fase 2 ya que la separación trae ventajas en escalabilidad independiente

## Alternativas consideradas y rechazadas

- **Chroma** → Muy simple para prototipos, pero menor rendimiento y filtrado comparado con Qdrant en cargas medias-altas
- **pgvector** → Tentador por unificar en PostgreSQL, pero en 2026 aún pierde en rendimiento puro y filtrado avanzado frente a bases dedicadas (especialmente hybrid search)
- **Weaviate** → Excelente en hybrid y graph-like features, pero mayor overhead operativo y curva inicial más alta
- **Pinecone** → Ideal para producción zero-ops, pero introduce costo y vendor lock-in desde temprano → descartado para fases iniciales

## Referencias

- Benchmarks y comparativas 2026: Qdrant vs Weaviate vs pgvector vs Chroma
- Documentación oficial Qdrant[](https://qdrant.tech/)
- Guías de integración FastAPI + Qdrant / LangChain 2026

Fecha de propuesta: 2026-03
Propuesto por: [tu nombre / equipo]
Pendiente de decisión: [fecha revisión]
