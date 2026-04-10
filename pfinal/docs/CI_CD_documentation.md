# Proceso de creación de Integración Continua (CI) y Distribución Continua (CD)

## Integración Continua (CI)
Este proyecto utiliza **GitHub Actions** para ejecutar un pipeline de integración continua (CI) que valida automáticamente el código en cada `push` y `pull_request`.

Ubicado en fichero .github\workflows\tests.yml

Asimismo, es importante resaltar que los estos tests se ejecutan con una base de datos **PostgreSQL** como en el entorno de producción.

## Docker Compose
En fichero docker-compose.yml

---

## Trigger del workflow

El pipeline se ejecuta en los siguientes eventos especificado con "On":

- `push`: cada vez que se sube código al repositorio
- `pull_request`: cada vez que se abre o actualiza un PR

---

## Job principal: `test`

El workflow contiene un único job llamado `test` que se ejecuta en un entorno. Más adelante se podría dividir en varios jobs, aunque este también permite debugging:

## Puntos importantes
Aquí se describirán los puntos principales, para más detalles, se puede observar los comentarios del fichero yml.

- Utiliza Ubuntu.
- Se encarga de configurar python. 
- Descarga todo las librerías de requirements.
- Levanta una base de datos PostgreSQL real dentro del runner de GitHub Actions
- Descarga herramienta para ver qué tanto del código cubren los tests
- Ejecuta los tests, especificando el directorio de origen (para los imports).
