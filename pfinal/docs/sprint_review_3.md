# Sprint 3 – Alertas CRUD + Etiquetado + Cron básico


En este sprint se busca trabajar en el backend de **Newsradar** para agregar la lógica de las **alertas** generadas cuando llega una noticia con la información pertinente. Asimismo, se enfoca en lograr que la aplicación etiquete debidamente esta notica de acuerdo a sus palabras claves.

---

## Objetivos de Sprint 2

- Definir modelos para representar alertas
- Implementar un servicio que genere una alerta.
- Implementar un servicio que etiquete las noticias despendiendo de su contenido

- Exponer endpoints REST para:
  - Crear alerta.
  - Listar alerta.
  - Consultar etiqueta.

---

## Modelos añadidos

Archivo: `app/models/models.py`

### Alert
- **id**: int (PK)
- **name**: Nombre de la alerta.
- **keyword**: Palabra de la cuál se genera.
- **synonyms**: Sinónimos de la palabra.
- **iptc_category**: categoría temática 
- **cron_expression**: Tiempo de duración
- **is_active**: Si está activa o no
- **user_id**: Id Usuario Recipiente
- **user**: Relación SQLAlchemy con 'User'

- **Funciones de Alert**
    - **get_synonyms** : Muestra los sinónimos de la palabra
    - **ser_synonyms**: Añade sinónimos de la palabra.



---

## Servicio Alert (`alertLogic.py`)

Archivo: `app/services/alertLogic.py`

### Función Principal
- **match_alert(alert, news_item)**

### Comportamiento
- Recibe una alerta y una noticia
- Mediante loops identifica si alguna palabra de la noticia corresponde a la keyword o sinónimos de la alerta. De esta forma cumpliendo el *Objetivo 1* del enunciado que *"A partir de ese momento, el sistema comenzará a monitorizar esa alerta (y todos sus descriptores)*."

---
## Scheduler

Archivo: `app/core/scheduler.py`

### Función Principal

### Comportamiento

---

### Endpoints disponibles (Sprint 3)

| Método | Ruta                              | Descripción                      |
| ------ | --------------------------------- | -------------------------------- |
| GET    | /api/v1/alerts                    |   Listar alertas                 |
| POST   | /api/v1/alerts                    |   Crear alerta                   |
| PUT    | /api/v1/alerts/{alert_id}         |   Actualizar alerta              |
| DELETE | /api/v1/alerts/{alert_id}         |   Borrar Alerta                  |


### Flujo de Prueba

### Crear Alerta 
Endpoint: `POST /api/v1/alerts`

**Ejemplo de body:**
```json
{
  "name": "Artes",
  "keyword": "Monet",
  "iptc_category": "Artes",
  "user_id" : "Admin123" 
}
```

**Respuesta esperada:**
```json
{
  "id": 1,
  "name": "Artes",
  "keyword": "Monet",
  "synonyms": []
}
```
Puedes probar con diferentes valores.

**Ejemplo de body:**
```json
{
  "name": "Guerra",
  "keyword": "Bomba",
  "iptc_category": "Politica",
  "user_id" : "Admin123" 
}
```

**Respuesta esperada:**
```json
{
  "id": 2,
  "name": "Guerra",
  "keyword": "Bomba",
  "synonyms": []
}
```

### Mostrar Alertas
Endpoint: `GET /api/v1/alerts`

Se espera que se muestren todas las alertas que has creado, en este caso:

**Respuesta esperada:**
```json
[
  {
    "id": 1,
    "name": "Artes",
    "keyword": "Monet",
    "synonyms": [],
    "iptc_category": "Artes",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Guerra",
    "keyword": "Bomba",
    "synonyms": [],
    "iptc_category": "Politica",
    "is_active": true
  }
]
```
### Actualizar Alert
Endpoint: `PUT /api/v1/alerts/{alert_id}`

Para este endpoint debes insertar el id de una alerta y el valor que esperas modificar.

```alert_id : 1```

**Ejemplo de body:**
```json
{
  "keyword": "arma",
}
```

**Respuesta esperada:**
{
  "Alert 1": "updated"
}

Para comprobar qué la actualización se realizó correctamente, basta con volver a ejecutar el endpoint de "List Alerts" y verificar que el cambio se realizó.

### Actualizar Alert
Endpoint: `Delete /api/v1/alerts/{alert_id}`

Para este endpoint debes insertar el id de una alerta que deseas eliminar.

```alert_id : 2```

**Respuesta esperada:**
{
  "Alert 1": "deleted"
}

En este caso, puedes comprobar si se ha borrado correctamente con List Alerts.