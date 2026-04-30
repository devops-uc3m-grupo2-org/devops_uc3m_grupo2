# Registro de Prompts de IA utilizados

Documento que recoge los prompts utilizados durante el desarrollo del proyecto NewsRadar para tareas asistidas por IA generativa.

---

## 1. Diseño del modelo de datos

**Herramienta**: Claude (Anthropic)  
**Prompt**:
> "Diseña un modelo de datos en SQLAlchemy para un sistema de monitorización de noticias RSS con alertas, categorías IPTC, usuarios con roles y notificaciones."

**Uso**: Generación del esquema inicial de `models.py` con las entidades `User`, `Alert`, `NewsItem`, `RSSChannel`, `Category`, `Notification`.

---

## 2. Generación del seed de 100 canales RSS

**Herramienta**: Claude (Anthropic)  
**Prompt**:
> "Genera un script Python que inserte 10 fuentes de medios de comunicación españoles con 10 canales RSS cada uno, cubriendo las 17 categorías IPTC de primer nivel. Usa SQLAlchemy."

**Uso**: Generación de `app/services/seed_rss.py` con `SEED_SOURCES` y `seed_rss_channels()`.

---

## 3. Lógica de matching de alertas

**Herramienta**: Claude (Anthropic)  
**Prompt**:
> "Implementa en Python una función que cruce una lista de noticias (título + resumen) contra los descriptores de una alerta usando expresiones regulares con límites de palabra."

**Uso**: Generación de `match_alert()` en `app/services/alertLogic.py`.

---

## 4. Endpoint de nube de palabras

**Herramienta**: Claude (Anthropic)  
**Prompt**:
> "Crea un endpoint FastAPI que analice los títulos y resúmenes de noticias agrupadas por categoría IPTC, limpie HTML y entidades HTML, elimine stop words en español y devuelva las 40 palabras más frecuentes por categoría."

**Uso**: Generación de `GET /api/v1/stats/wordcloud` en `app/main.py`.

---

## 5. Sistema de notificaciones por email

**Herramienta**: Claude (Anthropic)  
**Prompt**:
> "Implementa un módulo Python para envío de emails con SMTP Gmail usando smtplib. Necesito funciones para: email de verificación de cuenta (enlace JWT 24h), notificación de alerta disparada con resumen de noticias coincidentes, y recuperación de contraseña (enlace JWT 1h)."

**Uso**: Generación de `app/services/notifications.py`.

---

## 6. Sinónimos con diccionario IPTC

**Herramienta**: Claude (Anthropic)  
**Prompt**:
> "Crea un diccionario Python con las principales categorías periodísticas (economía, política, tecnología, salud, deporte, etc.) y entre 5 y 8 sinónimos o términos relacionados para cada una. Expón una función generate_synonyms(keyword) que devuelva entre 3 y 10 términos."

**Uso**: Generación de `app/services/ai.py`.

---

## 7. Tests automatizados

**Herramienta**: Claude (Anthropic)  
**Prompt**:
> "Genera tests con pytest y FastAPI TestClient para: CRUD de alertas con JWT, pipeline completo de matching alertas-noticias, CRUD de fuentes RSS, estadísticas, y sugerencias IA. Usa una base de datos PostgreSQL de test con transacciones que se revierten entre tests."

**Uso**: Generación de los 8 archivos de test en `app/tests/`.

---

## 8. Componente de visualización frontend

**Herramienta**: Claude (Anthropic)  
**Prompt**:
> "Implementa en JavaScript vanilla una nube de palabras sin dependencias externas. Las palabras deben tener tamaño de fuente proporcional a su frecuencia (entre 13px y 54px) y colores alternados. Incluye un selector de categoría."

**Uso**: Funciones `loadWordCloud()` y `renderWordCloudForCategory()` en `static/app.js`.
