# Sprint 3 – Alertas CRUD + Etiquetado + Cron básico


En este sprint se busca trabajar en el backend de **Newsradar** para agregar la lógica de las **alertas** generadas cuando llega una noticia con la información pertinente. Asimismo, se enfoca en lograr que la aplicación etiquete debidamente esta noticia de acuerdo a sus palabras claves y la almacene a falta de ser categorizada. Asimismo, se busca desarrollar una primera versión del scheduling, que permita hacer periodicamente identificación de noticias.

---

## Objetivos de Sprint 3

- Definir modelos para representar alerta
- Implementar un servicio que genere una alerta.
- Implementar servicio que permita modificar, actualizar y ver las alertas.
- Implementar un servicio que asigne noticia a alerta despendiendo de su contenido.
- Implementar servicio de Scheduling

- Exponer endpoints REST para:
  - Crear alerta.
  - Listar alerta.
  - Modificar alerta.
  - Borrar alerta.
  - Verificar si una noticia pertenece a alerta.
  - Probar el scheduling

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
Las alertas y las noticias tienen una multiplicidad de muchos a muchos, por lo que es útil emplear una tabla intermedia para modelar la relación. Esta tabla permite directamente asociar una noticia a varias alertas, y una alerta a varias noticias, evitando la redundancia de información. Por ejemplo, si una noticia coincide con 100 alertas, sin esta tablas, tendríamos que duplicar la noticia 100 veces, con la tabla, solo realizamos 100 relaciones pequeñas. Asimismo, evita la utilización de una lista dentro de un campo, de caso contrario necesitaríamos dentro de un campo como "related_news", meter los IDs de todas las noticias (en forma de lista). Finalmente, ayuda a la escalabilidad, ya que evita tener que hacer parsing por strings (si tenemos lista dentro de campo) y permite queries en ambas direcciones.

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

En este archivo definimos el scheduler que se encargará de cada 5 minutos revisar realizar las tareas. Este inlcuye realizar un fetch para nueva noticias, identificar si las noticias corresponden a una alerta, almacenarlas en tal caso, y llamar a la función que realizará las notificaciones. Estas tareas se incluyeron en este archivo ya que se deben realizar periódicamente sin falta. 

### Función Principal

```def fetch_all_sources_job()```

#### Comportamiento

Se encarga de llamar a fetch_feed para cada source en la base de datos.

Procede a guardar las noticias y después corre la función ```def process_alerts_for_items(db, items)```
que para cada noticia identifica si pertenece a una alerta con ```match_alert(alert, item)```.

Finalmente corre ```notify_user(alert)``` que enviará la notificación (a desarrollar más adelante).

Asimismo tenemos una función start_scheduler que inicia este proceso y con ayuda de un cron, se específica que lo debe realizar cada 5 minutos.


---

### Endpoints disponibles (Sprint 3)

| Método | Ruta                              | Descripción                      |
| ------ | --------------------------------- | -------------------------------- |
| GET    | /api/v1/alerts                    |        Listar alertas            |
| POST   | /api/v1/alerts                    |        Crear alerta              |
| PUT    | /api/v1/alerts/{alert_id}         |        Actualizar alerta         |
| DELETE | /api/v1/alerts/{alert_id}         |        Borrar Alerta             |
| POST   | /api/v1/run-matching              | Prueba el almacenamiento de todas las <br> noticias por alerta  |
| GET    | /api/v1/matchAlert/{alert_id}     | Permite ver las noticias guardada en una <br> alerta específica |
| POST   | /api/v1/run-scheduler             | Identifica si el scheduler lanza algún error |


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
Se puede probar con diferentes valores.

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
```json
{
  "Alert 1": "updated"
}
```

Para comprobar que la actualización se realizó correctamente, basta con volver a ejecutar el endpoint de "List Alerts" y verificar que el cambio se realizó.

### Borrar Alerta
Endpoint: `Delete /api/v1/alerts/{alert_id}`

Para este endpoint debes insertar el id de una alerta que deseas eliminar.

```alert_id : 1```

**Respuesta esperada:**
```json
{
  "Alert 1": "deleted"
}
```

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

### Verificar funcionamiento de scheduler (**Importante**)
Endpoint: `POST /api/v1/run-scheduler`

Este endpoint es un poco largo ya que identifica el correcto funcionamiento de todo el programa de alertas. Específicamente se encarga de correr el scheduler de forma manual para verificar si realiza todo lo que debe. Para verificarlo, podemos crear una nueva alerta con una keyword frecuentes (como indicado anteriormente).

Para asegurarnos que hayan noticias nuevas, podemos agregar un nuevo source con el endpoint `POST /api/v1/sources` de esta forma:

**Ejemplo de Body**
```json
{
  "name": "ABCAtleticoM",
  "medium": "ABC",
  "rss_url": "https://www.abc.es/rss/2.0/deportes/atletico-madrid/",
  "iptc_category": "Deportes"
}
```

**Respuesta Esperada**
```json
{
  "id": 4,
  "name": "ABCAtleticoM",
  "rss_url": "https://www.abc.es/rss/2.0/deportes/atletico-madrid/"
}
```

Posteriormente creamos una alert, con una keyword relacionada con el RSS (por ejemplo, RSS:ABCAtlecticoM -> Madrid).

**Ejemplo de body:**
```json
{
  "name": "AM",
  "keyword": "madrid",
  "iptc_category": "Deportes",
  "user_id" : "Admin123" 
}
```
Debemos observar cuál es su "id" para verificar el correcto funcionamiento más adelante (por ejemplo, id=1).

Ahora para verificar el estado inicial de la tabla AlertNews, probamos `POST /api/v1/matchAlert/{alert_id}` con "alert_id = 1" y identificamos que no está en la misma, ya que no hemos empleado match_alert todavía:

```json
{
  "detail": "Alert News not found"
}
```

Finalmente, presionanos el "*Try it Once*" del endpoint `POST /api/v1/run-scheduler`. El scheduler se ejecuta de forma manual y este ejecuta de nuevo el ```match_alert()``` sobre todas las noticias nuevas. En caso de encontrar una alerta que coincida esta noticia debería introducirse en la tabla de AlertNews.

**Respuesta Esperada**

```json
{
   "status": "scheduler executed manually"
}
```
Para verificar, probamos el endpoint the `POST /api/v1/matchAlert/{alert_id}` con "alert_id=1" de nuevo, y verificamos si aparecen las nuevas noticias coincidentes con la alerta, en caso tal, el scheduler está funcionando correctamente.

**Respuesta Esperada**
```json
{
  "alert_id": 1,
  "news_ids": [
    8,12,14
  ]
}
```
O en su defecto, si no aparece ninguna, miramos la terminal y debería aparecer esto:
"""app-1      | [FETCH] Source 1: 0 new items
app-1      | [FETCH] Source 2: 0 new items
app-1      | [MATCH] Alert 1 No matched news
app-1      | [MATCH] Alert 2 No matched news
app-1      | [MATCH] Alert 3 No matched news
app-1      | [FETCH] Source 3: 1 new items
app-1      | [FETCH] Source 4: 0 new items
app-1      | [FETCH] Source 5: 0 new items
"
Esto significa que ha ejecutado el match_alert pero no ha encontrado ninguna que coincida (Scheduler también correcto).

**Nuevo Commit:** 
El Scheduling funciona a excepción de las notificaciones, estas todavía presentan una imperfección, al correr el endpoint se recibirá un mensaje de error, pero al mirar la terminal se podrá identificar que realizá las tareas correctamente hasta los matchs 
terminal```
app-1  | [FETCH] Source 1: 0 new items
app-1  | [FETCH] Source 2: 0 new items
app-1  | [FETCH] Source 3: 10 new items
app-1  | [MATCH] Alert 1 matched News 11
app-1  | [MATCH] Alert 1 matched News 12
app-1  | [MATCH] Alert 1 matched News 13
app-1  | [MATCH] Alert 1 matched News 14
app-1  | [MATCH] Alert 1 matched News 15
app-1  | [MATCH] Alert 1 matched News 16
app-1  | [MATCH] Alert 1 matched News 17
app-1  | [MATCH] Alert 1 matched News 18
app-1  | [MATCH] Alert 1 matched News 19
app-1  | [MATCH] Alert 1 matched News 20
```