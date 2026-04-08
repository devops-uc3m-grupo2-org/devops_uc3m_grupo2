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
Es una tabla con todas las alertas creadas por los usuarios.

- **id**: int (PK)
- **name**: Nombre de la alerta.
- **keyword**: Palabra de la cuál se genera.
- **synonyms**: Sinónimos de la palabra.
- **iptc_category**: categoría temática ("*de etiquetar la alerta en una categoría siguiendo el primer nivel de IPTC Media Topic*")
- **cron_expression**: Tiempo de duración
- **is_active**: Si está activa o no
- **user_id**: Id Usuario Recipiente
- **user**: Relación SQLAlchemy con 'User'

Con relación a "iptc_category" más adelante se tendrá que implementar que solo acepte cómo valores el primer nivel de IPTC Media Topic

### AlertNews
Las alertas y las noticias tienen una multiplicidad de muchos a muchos, por lo que es útil emplear una tabla intermedia para modelar la relación. Esta tabla permite directamente asociar una noticia a varias alertas, y una alerta a varias noticias, evitando la redundancia de información. Por ejemplo, si una noticia coincide con 100 alertas, sin esta tablas, tendríamos que duplicar la noticia 100 veces, con la tabla, solo realizamos 100 relaciones pequeñas. Asimismo, evita la utilización de una lista dentro de un campo, de caso contrario necesitaríamos en un campo como "related_news", meter los IDs de todas las noticias. Finalmente, ayuda a la escalabilidad, ya que ayuda  a evitar tener que hacer parsing por stings (si tenemos lista dentro de campo) y permite queries en ambas direcciones.

- **id**: int (PK)
- **alert_id**: Id de la alerta.
- **news_item_id**: Id de la noticia.


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
| GET    | /api/v1/alerts                    |        Listar alertas            |
| POST   | /api/v1/alerts                    |        Crear alerta              |
| PUT    | /api/v1/alerts/{alert_id}         |        Actualizar alerta         |
| DELETE | /api/v1/alerts/{alert_id}         |        Borrar Alerta             |
| POST   | /api/v1/run-matching              | Prueba el almacenmiento de todas las <br> noticias por alerta  |
| GET    | /api/v1/matchAlert/{alert_id}     | Permite ver las noticias guardada en una <br> alerta específica |


### Flujo de Prueba

### Crear Alertas
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
  "name": "Guerra Alerta",
  "keyword": "guerra",
  "iptc_category": "Politica",
  "user_id" : "Admin123" 
}
```

**Respuesta esperada:**
```json
{
  "id": 2,
  "name": "Guerra Alerta",
  "keyword": "guerra",
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
    "name": "Guerra Alerta",
    "keyword": "guerra",
    "synonyms": [],
    "iptc_category": "Politica",
    "is_active": true
  }
]
```
### Actualizar Alerta
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

### Borrar Alerta
Endpoint: `Delete /api/v1/alerts/{alert_id}`

Para este endpoint debes insertar el id de una alerta que deseas eliminar.

```alert_id : 1```

**Respuesta esperada:**
{
  "Alert 1": "deleted"
}

En este caso, puedes comprobar si se ha borrado correctamente con List Alerts.


### Correr MatchAlert
Endpoint: `POST /api/v1/run-matching`

Este endpoint ejecutará una ronda de MatchAlert y incluirá en la tabla de AlertNews todas las relaciones de noticia-alarma que existan. Para probarlo, debes asegurarte que ya existan noticias en la base de datos (sprint 2) y que hayan alertas creadas que contengan esas palabras.

**Respuesta esperada:**

```json
{
  "status": "matching executed"
}
```

### Verificar funcionamiento de matchAlert
Endpoint: `POST /api/v1/matchAlert/{alert_id}`

Para verificar si el matchAlert está funcionando correctamente utilizamos este endpoint. Previamente en el flujo hemos creado una alerta con la keyword "guerra" (id:2). Asimismo, desde el sprint 2 se agregaron noticias desde una RSS y algunas contienen esta palabra. Para verificar que el match está funcionando debes introducir el id de la alerta:

```alert_id : 2```

Se espera que devuelva los IDs de las noticas que contienen la palabra, esto es verificable utilizando el endpoint: 
`GET /api/v1/news`
y verificando que los IDs recibidos corresponden a noticias que contienen la palabra "guerra".

**Respuesta esperada:**
```json
{
  "alert_id": 3,
  "news_ids": [
    2,
    7
  ]
}
```