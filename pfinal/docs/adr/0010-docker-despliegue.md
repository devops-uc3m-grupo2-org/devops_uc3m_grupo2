# ADR 010: Docker y despliegue en contenedor

## Estado
**Aceptado**

## Contexto

El proyecto debe ser reproducible y desplegable en contenedores. Ya existe un `Dockerfile` y `docker-compose.yml` parcial; hay que documentar la estrategia mínima para Fase 1.

## Decisión

Usar Docker + Docker Compose para el despliegue local y pruebas. Cada servicio (API, DB) correrá en contenedores separados y la configuración principal se pasará por variables de entorno o `.env`.

## Justificación

- Facilita replicar el entorno del profesor y pruebas de integración.
- Permite encapsular dependencias (Postgres, app) sin modificar la máquina del evaluador.

## Consecuencias

- Mantener `Dockerfile` pequeño y la `requirements.txt` precisa.
- Documentar en README cómo levantar la aplicación con `docker-compose up --build`.

## Migración futura

- Para producción, añadir CI/CD que construya imágenes y despliegue (registry, tags), y supervisión/healthchecks.

## Fecha

2026-03-12
