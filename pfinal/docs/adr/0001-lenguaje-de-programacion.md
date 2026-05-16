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
