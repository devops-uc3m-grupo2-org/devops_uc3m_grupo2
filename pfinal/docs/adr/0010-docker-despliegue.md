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
- Levantar siempre con `bash pfinal/start.sh` (hace `down -v` + rebuild + espera health) para garantizar BD limpia.

### Bug crítico corregido — `--reload` en el Dockerfile

El `CMD` original tenía `--reload`:
```dockerfile
# Antes (incorrecto):
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

Con `--reload`, uvicorn vigila cambios en el sistema de ficheros. El scheduler escribe en `__pycache__` cada vez que procesa noticias → uvicorn reinicia continuamente → conexiones cortadas → `ERR_EMPTY_RESPONSE` en el navegador y `Remote end closed connection` en el verificador.

Corrección:
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

En un contenedor con `COPY . .`, `--reload` no detecta cambios del host de todas formas (el código está copiado dentro de la imagen). Solo causa inestabilidad.

## Migración futura

- Para producción, añadir CI/CD que construya imágenes y despliegue (registry, tags), y supervisión/healthchecks.

## Fecha

2026-03-12 — propuesta inicial
2026-05 — bug `--reload` corregido; script `start.sh` creado para arranque limpio
