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

