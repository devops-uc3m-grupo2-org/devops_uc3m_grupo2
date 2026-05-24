# Registro de Prompts de IA utilizados

---

## Sprint 1 — Arquitectura y arranque (febrero 2026)

### 1. Elección de stack tecnológico

**Herramienta**: Gemini (Google)

**Prompt**:
> "Tengo que construir un sistema de monitorización de noticias RSS con alertas, notificaciones por email y panel de estadísticas. Compara FastAPI + PostgreSQL vs Django + MySQL para este caso de uso. Necesito API REST, scheduler de tareas y fácil dockerización."

**Uso**: Decisión de stack documentada en ADR-0001 y ADR-0008. Elegido FastAPI + PostgreSQL + SQLAlchemy.

---

### 2. Diseño del modelo de datos

**Herramienta**: Gemini (Google)

**Prompt**:
> "Diseña un modelo de datos en SQLAlchemy para un sistema de monitorización de noticias RSS con alertas, categorías IPTC, usuarios con roles y notificaciones."

**Uso**: Generación del esquema inicial de `models.py` con las entidades `User`, `Alert`, `NewsItem`, `RSSChannel`, `Category`, `Notification`.

---

### 3. Estructura inicial del proyecto FastAPI

**Herramienta**: Gemini (Google)

**Prompt**:
> "Genera la estructura de carpetas y el fichero main.py base para un proyecto FastAPI con: autenticación JWT, SQLAlchemy con PostgreSQL, Docker Compose con servicio app + db, y prefijo de API /api/v1. Incluye el endpoint GET /api/v1/health."

**Uso**: Estructura inicial de `pfinal/app/`, `Dockerfile`, `docker-compose.yml` y `app/main.py`.

---

### 4. Configuración Docker Compose

**Herramienta**: ChatGPT (OpenAI)
**Prompt**:
> "Crea un docker-compose.yml con tres servicios: FastAPI app (build desde Dockerfile), PostgreSQL 15 con volumen persistente, y pgAdmin. La app debe esperar a que postgres esté listo con healthcheck. Añade la variable DATABASE_URL."

**Uso**: Base de `docker-compose.yml`. Añadido posteriormente `extra_hosts: host.docker.internal:host-gateway` para compatibilidad Linux/WSL.

---

## Sprint 2 — Autenticación y usuarios (febrero–marzo 2026)

### 5. Sistema de autenticación JWT

**Herramienta**: Gemini (Google)

**Prompt**:
> "Implementa autenticación JWT en FastAPI con python-jose y passlib. Necesito: registro de usuario con hash de contraseña, login que devuelva access_token, middleware get_current_user, y tokens de verificación de cuenta con expiración configurable en minutos."

**Uso**: Funciones `create_access_token()`, `get_current_user()`, endpoints `POST /auth/register` y `POST /auth/login` en `main.py`.

---

### 6. Sistema de roles y permisos

**Herramienta**: Gemini (Google)

**Prompt**:
> "En SQLAlchemy, implementa una relación many-to-many entre User y Role usando una tabla intermedia user_roles. Añade una función require_gestor() que lance HTTP 403 si el usuario no tiene el rol 'gestor' o 'admin'."

**Uso**: Tabla `user_roles`, modelo `Role`, función `require_gestor()` en `main.py`.

---

### 7. Emails de verificación y recuperación

**Herramienta**: Gemini (Google)

**Prompt**:
> "Implementa un módulo Python para envío de emails con SMTP Gmail usando smtplib. Necesito funciones para: email de verificación de cuenta (enlace JWT 24h), notificación de alerta disparada con resumen de noticias coincidentes, y recuperación de contraseña (enlace JWT 1h)."

**Uso**: Generación de `app/services/notifications.py`.

---

## Sprint 3 — Fuentes RSS e ingesta (marzo 2026)

### 8. Generación del seed de canales RSS

**Herramienta**: Gemini (Google)

**Prompt**:
> "Genera un script Python que inserte 15 fuentes de medios de comunicación españoles con canales RSS cubriendo las 17 categorías IPTC de primer nivel. Usa SQLAlchemy. Medios: El País, El Mundo, ABC, RTVE, Expansión, Marca, La Vanguardia, El Confidencial, 20 Minutos, elDiario.es, BBC Mundo, El Español, Mundo Deportivo, Cinco Días, Sport España."

**Uso**: Generación de `app/services/seed_rss.py` con `SEED_SOURCES` y `seed_rss_channels()`. 15 medios, 218 canales.

---

### 9. Fetcher RSS con deduplicación

**Herramienta**: Gemini (Google)

**Prompt**:
> "Implementa en Python una función fetch_feed(db, channel_id) que use feedparser para descargar un canal RSS, itere sus entradas y las inserte en la tabla news_items. Debe deduplicar por URL usando un savepoint de SQLAlchemy para manejar IntegrityError sin abortar la transacción completa."

**Uso**: Función `fetch_feed()` en `app/services/fetcher.py`.

---

### 10. Scheduler con APScheduler

**Herramienta**: ChatGPT (OpenAI)
**Prompt**:
> "Configura APScheduler en FastAPI para ejecutar una función cada 5 minutos usando cron ('*/5 * * * *'). El scheduler debe arrancar en el evento startup de FastAPI y tener misfire_grace_time=60 para evitar ejecuciones perdidas."

**Uso**: `app/core/scheduler.py` con `start_scheduler()`. Documentado en ADR-0005.

---

### 11. Validación de URLs RSS

**Herramienta**: Gemini (Google)

**Prompt**:
> "Implementa una función Python _reject_bad_url(value, rss=False) que normalice una URL, rechace localhost/127.0.0.1 con HTTP 422, y si rss=True verifique que la URL parece un feed RSS comprobando si contiene tokens como 'rss', 'feed', 'xml' o dominios conocidos como 'hnrss.org'."

**Uso**: Función `_reject_bad_url()` en `main.py`, línea 120.

---

## Sprint 4 — Motor de alertas (marzo–abril 2026)

### 12. Lógica de matching de alertas

**Herramienta**: Gemini (Google)

**Prompt**:
> "Implementa en Python una función que cruce una lista de noticias (título + resumen) contra los descriptores de una alerta usando expresiones regulares con límites de palabra. Lógica OR: si cualquier descriptor hace match, la noticia es relevante."

**Uso**: Funciones `match_alert()` y `process_alerts_for_items()` en `app/services/alertLogic.py`.

---

### 13. Categorías IPTC Media Topics

**Herramienta**: Gemini (Google)

**Prompt**:
> "Dame el listado completo de las 17 categorías de primer nivel de IPTC Media Topics con sus códigos numéricos (01000000–17000000) y nombres en español. Formateado como diccionario Python."

**Uso**: Constante `IPTC_CATALOG` en `main.py` con los 17 códigos y nombres oficiales.

---

### 14. Sinónimos con diccionario IPTC

**Herramienta**: Gemini (Google)

**Prompt**:
> "Crea un diccionario Python con las principales categorías periodísticas (economía, política, tecnología, salud, deporte, etc.) y entre 5 y 8 sinónimos o términos relacionados para cada una. Expón una función generate_synonyms(keyword) que devuelva entre 3 y 10 términos."

**Uso**: Generación de `app/services/ai.py`.

---

## Sprint 5 — Frontend y visualización (abril 2026)

### 15. Panel de mando HTML/JS vanilla

**Herramienta**: Gemini (Google)

**Prompt**:
> "Genera un panel de mando HTML + CSS + JavaScript vanilla (sin frameworks) para un sistema de noticias. Debe incluir: navegación lateral, secciones para alertas, fuentes RSS, noticias, estadísticas y perfil de usuario. Sistema de internacionalización ES/EN con un objeto TRANSLATIONS."

**Uso**: Estructura base de `app/static/index.html` y `app/static/app.js`.

---

### 16. Nube de palabras sin dependencias

**Herramienta**: Gemini (Google)

**Prompt**:
> "Implementa en JavaScript vanilla una nube de palabras sin dependencias externas. Las palabras deben tener tamaño de fuente proporcional a su frecuencia (entre 13px y 54px) y colores alternados. Incluye un selector de categoría."

**Uso**: Funciones `loadWordCloud()` y `renderWordCloudForCategory()` en `static/app.js`.

---

### 17. Endpoint de estadísticas y wordcloud

**Herramienta**: Gemini (Google)

**Prompt**:
> "Crea un endpoint FastAPI GET /api/v1/stats/wordcloud que analice los títulos y resúmenes de noticias agrupadas por categoría IPTC, limpie HTML y entidades HTML, elimine stop words en español y devuelva las 40 palabras más frecuentes por categoría."

**Uso**: Endpoint `GET /api/v1/stats/wordcloud` en `main.py`.

---

## Sprint 6 — CI/CD y calidad (abril–mayo 2026)

### 18. Pipeline GitHub Actions

**Herramienta**: ChatGPT (OpenAI)
**Prompt**:
> "Genera un workflow de GitHub Actions para un proyecto FastAPI que ejecute en cada push: flake8 para estilo, bandit para seguridad, radon para complejidad ciclomática, pytest con cobertura mínima del 80% y suba coverage.xml como artefacto. Usa PostgreSQL como servicio en el job."

**Uso**: `.github/workflows/tests.yml`. Cobertura actual: 96.48%.

---

### 19. Tests automatizados con pytest

**Herramienta**: Gemini (Google)

**Prompt**:
> "Genera tests con pytest y FastAPI TestClient para: CRUD de alertas con JWT, pipeline completo de matching alertas-noticias, CRUD de fuentes RSS, estadísticas, y sugerencias IA. Usa una base de datos PostgreSQL de test con transacciones que se revierten entre tests."

**Uso**: 13 archivos de test en `app/tests/`.

---

### 20. Corrección de cobertura insuficiente

**Herramienta**: Gemini (Google)

**Prompt**:
> "Mi pipeline de CI falla porque la cobertura de tests es del 74%, por debajo del umbral del 80%. Analiza qué ramas de código en main.py no están cubiertas y genera tests adicionales para los endpoints de roles, recuperación de contraseña y el endpoint /stats/by-category."

**Uso**: Tests adicionales que subieron la cobertura del 74% al 96%.

---

## Sprint 7 — Estabilización y examen (mayo 2026)

### 21. Script de arranque automatizado

**Herramienta**: Gemini (Google)

**Prompt**:
> "Crea un script bash start.sh que: pare y elimine contenedores previos con docker compose down -v, reconstruya la imagen con --build, espere a que el healthcheck de la app pase (máximo 90 segundos comprobando cada 2s), e imprima el resultado final."

**Uso**: `pfinal/start.sh`. Usado para reset completo de la BD antes de cada demostración.

---

### 22. Diagnóstico de conectividad mock RSS

**Herramienta**: Gemini (Google)

**Prompt**:
> "Escribe un script bash de diagnóstico para verificar que un mock RSS corriendo en el host es accesible desde dentro de un contenedor Docker. Comprueba: que el mock responde HTTP 200, que docker-compose.yml tiene extra_hosts configurado, que host.docker.internal resuelve dentro del contenedor, y que el mock es accesible HTTP desde dentro."

**Uso**: `pfinal/debug_m5.sh` con 7 checks de diagnóstico.

---

### 23. Generación del diagrama entidad-relación

**Herramienta**: Gemini (Google)

**Prompt**:
> "A partir de este modelo SQLAlchemy con las tablas users, roles, user_roles, categories, information_sources, rss_channels, news_items, alerts, alert_news y notifications, genera el código DBML para importar en dbdiagram.io y obtener el diagrama entidad-relación con todas las claves foráneas correctas."

**Uso**: `pfinal/docs/DiagramaRelacionEntidad/code_generar_dbdiagram_io.sql`. Exportado a PNG, SVG y PDF.

---

### 24. Trazabilidad requisitos–código

**Herramienta**: Gemini (Google)

**Prompt**:
> "Dado el enunciado del proyecto NewsRadar con 40 requisitos funcionales y este código FastAPI, genera una tabla Markdown de trazabilidad que mapee cada requisito con el archivo y función que lo implementa."

**Uso**: `pfinal/docs/trazabilidad_requisitos.md` con las 40 filas de trazabilidad.
