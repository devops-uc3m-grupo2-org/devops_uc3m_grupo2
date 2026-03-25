# Architecture Decision Records (## ADRs)

Estos ADR reflejan las decisiones arquitectónicas ya implementadas en el proyecto actual (FastAPI + JWT + PostgreSQL + Docker + RSS básico).
Cada decisión está respaldada por código y alineada con los sprints desarrollados.

---

## ## ADR 1: Elección del Framework Backend (Python 3.12 + FastAPI)
**Estado:** Aceptado


### Contexto 
Para el desarrollo de NewsRadar, se necesitaba un framework que permitiera procesar datos (RSS, texto) de forma eficiente, con validación estricta y documentación automática para agilizar los Sprints. Las alternativas eran Flask o Django, pero se buscaba algo nativo para el paradigma asíncrono.


### Decisión 
Utilizar Python 3.12 junto con FastAPI y Pydantic V2.

### Consecuencias

Positivas: Generación automática de Swagger UI (/docs), lo que facilitó las pruebas del endpoint de salud y usuarios en el Sprint 1. Validación automática de esquemas mediante Pydantic.


Negativas/Riesgos: Requiere manejar el flujo asíncrono (async/await) para no bloquear el Event Loop durante la ingesta de noticias.

---

## ## ADR 2: Persistencia y Migraciones (PostgreSQL + Alembic)
Estado: Aceptado

### Contexto
El sistema debe gestionar usuarios, fuentes RSS y noticias persistidas. Al usar FastAPI asíncrono, las consultas no pueden bloquear el hilo principal.

### Decisión 
Utilizar PostgreSQL 16-alpine como motor y SQLAlchemy 2.0 como ORM, gestionando los cambios de esquema con Alembic.

### Consecuencias

Positivas: PostgreSQL ofrece robustez para relaciones complejas entre fuentes y noticias. El uso de la versión alpine optimiza el peso de los contenedores Docker.


Negativas/Riesgos: La configuración inicial de Alembic y la gestión de sesiones asíncronas (AsyncSession) añade complejidad al código frente a una base de datos embebida como SQLite.

---

## ADR 3: Estrategia de Autenticación (JWT Stateless)
Estado: Aceptado


### Contexto 
Se requiere un sistema de acceso seguro para roles de administrador y usuarios registrados sin sobrecargar la base de datos con consultas de sesión constantes.


### Decisión
Implementar autenticación basada en JSON Web Tokens (JWT) firmados con HS256.

### Consecuencias


Positivas: El backend es stateless; el servidor no necesita guardar información de sesión en memoria, facilitando la escalabilidad futura.


Negativas/Riesgos: Una vez emitido un token, no se puede revocar fácilmente hasta que caduque, por lo que se deben configurar tiempos de expiración controlados.

## ADR 4: Despliegue y Orquestación (Docker Compose)
Estado: Aceptado

### Contexto 
Era fundamental garantizar que el entorno de desarrollo fuera idéntico para todo el equipo y para la demo final, encapsulando la API, la BD y herramientas como pgAdmin.

### Decisión 
Utilizar Docker Compose para orquestar los servicios app, db y pgadmin.

### Consecuencias

Positivas: Despliegue reproducible con docker compose up --build. Persistencia garantizada mediante volúmenes (postgres_data).

Negativas/Riesgos: La "dockerización" de la aplicación durante el desarrollo puede ralentizar ligeramente el ciclo de cambios si no se configuran correctamente los volúmenes de código.

---

## ADR 5: Estrategia de Ingesta (feedparser + Servicio de Dominio)
Estado: Aceptado


### Contexto
NewsRadar necesita consumir múltiples canales RSS de forma estructurada para luego procesarlos.

### Decisión 
Utilizar la librería feedparser encapsulada en un servicio de dominio (fetcher.py) para procesar las fuentes.

### Consecuencias

Positivas: Permite normalizar distintos formatos de RSS/Atom. El servicio evita la duplicidad de noticias basándose en el campo link.

Negativas/Riesgos: La ingesta masiva puede ser lenta si se hace de forma secuencial; en el futuro podría requerir tareas en segundo plano (BackgroundTasks) para no bloquear la API.