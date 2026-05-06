# Sprint Review 6 – Estadísticas (Dashboard + Analytics + Wordcloud)

Este sprint introduce el módulo de **analítica y métricas** en **NewsRadar**. Su objetivo es proporcionar información agregada sobre noticias, alertas y categorías, además de generar visualizaciones tipo **wordcloud** basadas en el contenido de las noticias relacionadas con las alertas del usuario.

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
