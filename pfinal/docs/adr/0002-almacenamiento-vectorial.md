# ADR 002: Almacenamiento de datos — PostgreSQL como motor dual

## Estado
**Aceptado — Implementado (2026-05)**

## Contexto

El enunciado exige dos sistemas gestores de datos:

> *"Un sistema gestor de datos para el almacenamiento de la información"* (noticias, matches, notificaciones)
> *"Un sistema gestor de datos para el almacenamiento de las entidades del sistema"* (usuarios, alertas, fuentes, categorías)

En Fase 1 ya está en uso PostgreSQL + SQLAlchemy como base relacional principal. Se evaluó si era necesario añadir un segundo motor independiente (base vectorial tipo Qdrant) o si PostgreSQL podía cubrir ambos requisitos del enunciado.

## Decisión

**PostgreSQL cubre ambos requisitos del enunciado** con dos roles diferenciados dentro del mismo motor:

| Rol | Tablas | Requisito cubierto |
|---|---|---|
| Gestión de entidades | `users`, `roles`, `alerts`, `information_sources`, `rss_channels`, `categories` | "almacenamiento de entidades del sistema" |
| Gestión de información procesada | `news_items`, `alert_news`, `notifications` | "almacenamiento de la información" |

El enunciado no exige que sean tecnologías distintas, solo que haya dos sistemas lógicos separados. PostgreSQL actúa como ambos de forma coherente.

La detección de noticias relevantes se hace mediante matching por palabras clave con expresiones regulares (`\bpalabra\b`, `re.UNICODE`) en `pfinal/app/services/alertLogic.py`.

## Por qué se descartó añadir Qdrant u otra base vectorial

- Añade un segundo servicio Docker sin aportar valor al caso de uso actual (matching por descriptores con regex es suficiente).
- El matching por regex es suficiente para 3–10 descriptores por alerta.
- El plazo (25 mayo 2026) no justificaba la infraestructura adicional.
- El enunciado no exige búsqueda semántica vectorial, solo monitorización por palabras clave.

## Alternativas consideradas y rechazadas

| Opción | Razón de rechazo |
|---|---|
| **Qdrant** | Añade un segundo contenedor Docker; búsqueda vectorial no requerida por el enunciado |
| **pgvector** | Extensión de PostgreSQL para embeddings; no necesaria para matching por regex |
| **Chroma** | Más simple que Qdrant pero igualmente innecesario para el caso de uso |
| **SQLite** | No soporta concurrencia de múltiples conexiones simultáneas |

## Consecuencias

- Positivas:
  - Un solo motor, un solo contenedor, configuración mínima.
  - El matching por regex en `alertLogic.py` es determinista, testeable y sin dependencias externas.
  - 281/281 casos del verificador pasando con este modelo (2026-05-22).

- Negativas / Mitigadas:
  - Si en fases futuras se requiriera búsqueda semántica real (embeddings), habría que añadir pgvector o Qdrant.

## Fecha

2026-03 — propuesta inicial con Qdrant como opción preferida
2026-05 — decisión revisada: PostgreSQL dual role + matching por regex; Qdrant descartado
