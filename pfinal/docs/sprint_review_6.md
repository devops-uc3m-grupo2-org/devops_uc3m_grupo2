# Sprint Review 6 – Estadísticas (Dashboard + Analytics + Wordcloud)

Este sprint introduce el módulo de **analítica y métricas** en **NewsRadar**. Su objetivo es proporcionar información agregada sobre noticias, alertas y categorías, además de generar visualizaciones tipo **wordcloud** basadas en el contenido de las noticias relacionadas con las alertas del usuario.

El sistema matching fue verficado previamente en el sprint 3.

---

# Objetivos del Sprint

- Generar métricas globales del sistema (news, sources, alerts).
- Obtener estadísticas agrupadas por categoría.
- Generar análisis de palabras más frecuentes (wordcloud).
- Filtrar datos en función de las alertas del usuario autenticado.
- Exponer endpoints de analítica para dashboard.

---

# Endpoints disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/stats` | Métricas generales del sistema |
| GET | `/api/v1/stats/by-category` | Estadísticas por categoría |
| GET | `/api/v1/stats/wordcloud` | Palabras más frecuentes (wordcloud) |

Antes de Testear los endpoints debes autenticarte mediante el endpoint (con un email ya registrado).

`POST /api/v1/auth/login`
```json
{
  "email": "tu_email_ya_registrado@newsradar.com",
  "password": "tu_password"
}
```
Importante: Tienes que tener rol de usuario, no gestor.

## Estadísticas generales

### Endpoint:
`GET /api/v1/stats`

---

### Objetivo:
Obtener métricas globales del sistema filtradas por las alertas del usuario autenticado.

---

### Métricas devueltas:

- `total_news`: noticias relacionadas con las alertas del usuario  
- `total_sources`: número total de fuentes en el sistema  
- `total_alerts`: número de alertas del usuario  

---

###  Caso de éxito

**Respuesta esperada (200 OK):**
```json id="stats1_ok"
[
  {
    "id": 1,
    "metrics": [
      {
        "name": "total_news",
        "value": 0
      },
      {
        "name": "total_sources",
        "value": 10
      },
      {
        "name": "total_alerts",
        "value": 0
      }
    ]
  }
]
```

---

###  Notas de prueba

- Si el usuario no tiene alertas → `total_news = 0`
- `total_sources` depende de la base de datos global
- `total_alerts` depende del usuario autenticado

---

##  Estadísticas por categoría

### Endpoint:
`GET /api/v1/stats/by-category`

---

### Objetivo:
Obtener distribución de noticias y alertas agrupadas por categoría.

---

### Lógica:
- Noticias agrupadas por categoría del canal RSS  
- Alertas agrupadas por categoría asignada en cada alerta del usuario  

---

### Caso de éxito



**Respuesta esperada (200 OK):**
```json id="stats2_ok"
[
  {
    "category": "Economía",
    "news_count": 10,
    "alerts_count": 2
  },
  {
    "category": "Política",
    "news_count": 5,
    "alerts_count": 1
  },
  {
    "category": "Sin categoría",
    "news_count": 3,
    "alerts_count": 1
  }
]
```

---

### Casos a validar

#### Usuario sin alertas
```json id="stats2_empty1"
[]
```

#### Usuario con alertas pero sin noticias relacionadas
```json id="stats2_empty2"
[
  {
    "category": "Economía",
    "news_count": 0,
    "alerts_count": 2
  }
]
```

---

## Wordcloud (análisis de texto)

### Endpoint:
`GET /api/v1/stats/wordcloud`

---

### Objetivo:
Generar un análisis de palabras más frecuentes a partir de:

- títulos de noticias  
- resúmenes de noticias  
- filtrado por alertas del usuario  

---

### Lógica principal:

- Eliminación de stopwords (español)
- Limpieza de HTML y URLs
- Agrupación por categoría
- Top 40 palabras más frecuentes

---

### Caso de éxito

**Respuesta esperada (200 OK):**
```json id="stats3_ok"
{
  "Economía": [
    { "word": "mercado", "count": 12 },
    { "word": "inflación", "count": 9 }
  ],
  "Política": [
    { "word": "elecciones", "count": 8 },
    { "word": "gobierno", "count": 6 }
  ]
}
```

---

### Casos especiales

#### Usuario sin alertas
```json id="stats3_empty1"
{}
```

#### Usuario con alertas pero sin noticias
```json id="stats3_empty2"
{}
```

---

# Flujo de pruebas completo (Sprint Review)

---

## Preparación

Autenticarse:
```http id="stats_flow_auth"
POST /api/v1/auth/login
```

Obtener JWT token

---

## Datos necesarios

Para validar correctamente el sprint:

- 1 usuario con alertas activas  
- 1 fuente de noticias  
- noticias asociadas a alertas (AlertNews)  
- categorías asignadas a canales RSS  


## Proceder a la Ejecución de pruebas

## Validaciones clave

- Solo se muestran datos del usuario autenticado  
- Si no hay alertas → respuestas vacías o cero  
- Las noticias se filtran por `AlertNews`  
- El análisis de texto depende del contenido real de noticias  


# Sprint 6 – Gestión de Categorías (CRUD)

Este módulo del backend de **NewsRadar** implementa la gestión completa de **categorías temáticas**, utilizadas para clasificar fuentes RSS, noticias y estadísticas del sistema.

Las categorías siguen un modelo simple pero central en el sistema de agregación de noticias.

Este funcionamiento debió haber sido implementado antes, pero por problemas técnicos se realiza la revisión en este sprint.

---

# Objetivos

- Listar todas las categorías del sistema.
- Crear nuevas categorías.
- Consultar una categoría por ID.
- Actualizar categorías existentes.
- Eliminar categorías.
- Validar existencia antes de operar.

---

# Endpoints disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/categories` | Listar todas las categorías |
| POST | `/api/v1/categories` | Crear nueva categoría |
| GET | `/api/v1/categories/{id}` | Obtener categoría por ID |
| PUT | `/api/v1/categories/{id}` | Actualizar categoría |
| DELETE | `/api/v1/categories/{id}` | Eliminar categoría |

---

# Flujo de pruebas

---

##  Listar categorías

### Endpoint:
`GET /api/v1/categories`

---

### Objetivo:
Obtener todas las categorías registradas en el sistema.

---

### Caso de éxito

**Respuesta esperada (200 OK):**
```json id="cat1_ok"
[
  {
    "name": "Política",
    "source": "IPTC",
    "id": 1
  },
  {
    "name": "Economía, negocios y finanzas",
    "source": "IPTC",
    "id": 2
  },
  {
    "name": "Ciencia y tecnología",
    "source": "IPTC",
    "id": 3
  },
  {
    "name": "Arte, cultura y espectáculos",
    "source": "IPTC",
    "id": 4
  },
  ...
]
```

---

##  Crear categoría

### Endpoint:
`POST /api/v1/categories`

---

### Objetivo
Crear una nueva categoría en el sistema.

---

### Request Body

```json id="cat2_body"
{
  "name": "Deporte",
  "source": "IPTC_prueba"
}
```

---

### Caso de éxito

```json
{
  "name": "Deporte",
  "source": "IPTC_prueba",
  "id": 18
}
```

Código: **201 Created**

---

###  Notas

- `source` identifica el origen de clasificación (ej: IPTC)
- No se valida duplicación en este endpoint
- La validación de tipos se asegura que el nombre debe pertenecer a una de las categorías principales de clasificación IPTC. Si no lo es, se recibirá el "Error 422: Unporcessable Entity".

---

## Obtener categoría por ID

### Endpoint:
`GET /api/v1/categories/{category_id}`

---

Debes poner el id de la categoría, puedes poner el id generado por la creación anterior.

###  Caso de éxito

```json
{
  "name": "Deporte",
  "source": "IPTC_prueba",
  "id": 18
}
```

---

### Caso de error

```json
{
  "detail": "Categoría no encontrada"
}
```

Código: **404**

---

## Actualizar categoría

### Endpoint:
`PUT /api/v1/categories/{category_id}`

---

### Objetivo:
Modificar nombre o fuente de una categoría existente.

---
### Request:

Se debe incluir el id de la categoría a modificar, puede ser el de la recientemente creada.
```json
{
  "name": "Deporte",
  "source": "IPTC_prueba_mod"
}
```

---

### Caso de éxito
{
  "name": "Deporte",
  "source": "IPTC_prueba_mod",
  "id": 18
}
---

### Caso de error

```json id="cat4_err"
{
  "detail": "Categoría no encontrada"
}
```

Código: **404**

---

## Eliminar categoría

### Endpoint:
`DELETE /api/v1/categories/{category_id}`

Se debe incluir el id de la categoría a modificar, puede ser el de la recientemente creada.

---

### Caso de éxito

 access-control-allow-credentials: true 
 access-control-allow-origin: * 
 date: Wed,06 May 2026 13:05:33 GMT 
 server: uvicorn 

- Código: **204 No Content**
- Sin body

---

### Caso de error

```json id="cat5_err"
{
  "detail": "Categoría no encontrada"
}
```

Código: **404**

Verificar si fue borrado con el endpoint de "list categories".

---

## Resumen — Estado al cierre de Sprint 6 (revisado mayo 2026)

Al finalizar el Sprint 6, NewsRadar incorpora el módulo completo de analítica (stats, by-category, wordcloud) y el CRUD de categorías IPTC, sobre la base de alertas y notificaciones de sprints anteriores.

> **Correcciones respecto al documento original:**
> - La nota "Tienes que tener rol de usuario, no gestor" es incorrecta: cualquier usuario autenticado (admin, gestor, user) puede acceder a los endpoints de stats.
> - Las categorías IPTC (≥ 16) están **sembradas automáticamente** al inicializar la BD; no es necesario crearlas manualmente para que el sistema funcione.
> - El formato real de `GET /api/v1/stats` es el mostrado en el documento (lista con un objeto que contiene `"metrics": [...]`); sin cambios.

### De qué consta

| Área | Detalle |
|------|---------|
| **Stats generales** | `GET /api/v1/stats` — `total_news`, `total_sources`, `total_alerts` filtrados por el usuario autenticado |
| **Stats por categoría** | `GET /api/v1/stats/by-category` — distribución de noticias y alertas por categoría |
| **Wordcloud** | `GET /api/v1/stats/wordcloud` — top 40 palabras más frecuentes en títulos/resúmenes, agrupadas por categoría |
| **Categorías — CRUD** | `GET`, `POST`, `PUT`, `DELETE /api/v1/categories` |
| **Categorías semilla** | ≥ 16 categorías IPTC cargadas automáticamente al arrancar |

### Ejemplos

**Estadísticas generales**
```bash
curl http://localhost:8000/api/v1/stats \
  -H "Authorization: Bearer <JWT>"
# [ { "id": 1, "metrics": [ {"name":"total_news","value":42}, {"name":"total_sources","value":15}, {"name":"total_alerts","value":2} ] } ]
```

**Wordcloud**
```bash
curl http://localhost:8000/api/v1/stats/wordcloud \
  -H "Authorization: Bearer <JWT>"
# { "Economía": [{"word":"mercado","count":12}, ...], "Política": [...] }
```

**Listar categorías**
```bash
curl http://localhost:8000/api/v1/categories \
  -H "Authorization: Bearer <JWT>"
# [ {"id":1,"name":"Política","source":"IPTC"}, {"id":2,"name":"Economía, negocios y finanzas","source":"IPTC"}, ... ]
```

**Crear categoría adicional**
```json
// POST /api/v1/categories
// Authorization: Bearer <JWT>
// Request
{ "name": "Deporte", "source": "IPTC_prueba" }

// Response 201
{ "id": 18, "name": "Deporte", "source": "IPTC_prueba" }
```