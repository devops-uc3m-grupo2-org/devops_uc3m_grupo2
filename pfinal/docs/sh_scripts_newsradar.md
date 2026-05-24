# Scripts de NewsRadar — guía rápida

> **Este documento:** guía de todos los scripts `.sh` del proyecto y el orden de ejecución el día del examen.
> **Ver también:** [`../README.md`](../README.md) · [`demo_recorrido.md`](demo_recorrido.md)

Todos los scripts se ejecutan desde la raíz de `pfinal/`. Requieren Docker en ejecución salvo donde se indique.

---

## Orden de ejecución en el día del examen

```
1. bash check_conexion.sh      # (opcional) red OK antes de empezar
2. bash start.sh               # levanta app + BD desde cero
3. bash pre_examen.sh          # check rápido de todo (~30 s)
4. bash run_verifier.sh        # 281 casos del verificador (~17 min)
5. bash m1_email_notificacion.sh  # inspecciones manuales M1–M5 según lo pida el profe
   bash m2_formato_asunto.sh
   bash m3_registro_verificacion.sh
   bash m4_expiracion_24h.sh
   bash m5_mock_rss.sh
6. bash stop.sh                # al terminar
```

---

## Ciclo de vida

| Script | Qué hace |
|---|---|
| `start.sh` | `docker compose down -v` + `docker compose up --build -d`. Espera hasta 90 s a que la app responda en `:8000`. |
| `stop.sh` | `docker compose down` (conserva volúmenes — los datos no se pierden). |

---

## Pre-examen y diagnóstico

| Script | Qué hace |
|---|---|
| `check_conexion.sh` | Comprueba red, Docker y acceso a Docker Hub **antes** de `start.sh`. Útil en redes universitarias con proxy. |
| `pre_examen.sh` | Check rápido (~30 s): contenedores up, login admin, seed OK (fuentes ≥15, canales ≥100, categorías ≥16), JWT 401, M4 token inválido, M3 email en logs, rol user → 403, endpoints principales 200. Muestra `✅ / ❌ / ⚠️` por cada comprobación. |
| `check_rss_urls.sh` | Comprueba qué URLs RSS del seed responden con HTTP 200. Diagnóstico de fuentes caídas. |

---

## Verificador del profesor (281 casos)

| Script | Qué hace |
|---|---|
| `run_verifier.sh` | Borra el `.venv` del verificador, lo recrea, instala deps y lanza `run_tests.py`. Muestra timer en vivo y tiempos al final. **Usar este para el examen.** |
| `verify.sh` | Versión simplificada: lanza el verificador directamente con `--all` asumiendo que el `.venv` ya existe. |
| `shell_acceso.sh` | Abre una shell interactiva con el `.venv` del verificador activado y el directorio correcto. Para ejecutar comandos del verificador a mano. |

---

## Inspecciones manuales M1–M5

Cada script comprueba un criterio de inspección manual del examen. Si ya hay evidencia en los logs de Docker, la muestra directamente. Si no, crea los datos necesarios y espera.

| Script | Qué verifica |
|---|---|
| `m1_email_notificacion.sh` | M1: que el sistema envía `[EMAIL]` de notificación al detectar una noticia coincidente. Espera hasta 10 min si no hay logs previos. |
| `m2_formato_asunto.sh` | M2: que el asunto del email sigue el formato `Actualización de [alerta] en [DD/MM/YYYY HH:MM]`. |
| `m3_registro_verificacion.sh` | M3: que el registro de un nuevo usuario dispara un `[EMAIL]` de verificación en los logs. |
| `m4_expiracion_24h.sh` | M4: que un token de verificación inválido devuelve HTTP 400, y que `expires_minutes=1440` está en el código. |
| `m5_mock_rss.sh` | M5: alias de `demo_m5.sh`. Requiere el mock RSS corriendo en `:8100` en otra terminal. |
| `demo_m5.sh` | Lógica completa de M5: crea alerta apuntando al mock RSS, espera hasta 15 min a que el scheduler indexe 8 noticias mock, verifica el match. |

**Para M5**, arrancar el mock primero (en otra terminal, dentro de `devops_verifica-main/`):
```bash
python mock_rss_service.py --port 8100 --host 0.0.0.0
```
`--host 0.0.0.0` es obligatorio — sin él el mock solo escucha en loopback y el contenedor Docker no puede alcanzarlo.

Para verificar que el contenedor alcanza el mock (el contenedor no tiene `curl`, usar python3):
```bash
docker compose exec app python3 -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:8100/openapi.json').read()[:60])"
```
Respuesta esperada: `b'{"openapi":"3.1.0","info":{"title":"Mock RSS News API"...'`

---

## Checklist y entrega

| Script | Qué hace |
|---|---|
| `checklist_profe.sh` | Verifica automáticamente las 26 preguntas de proceso del checklist del profesor. Con `--proyecto` también las 40 de proyecto. |
| `zippear.sh` | Genera el zip entregable para AulaGlobal (incluye .env), comprueba scripts M1-M5 y muestra el procedimiento del día del examen. |

---

## Documentación técnica

| Script | Qué hace |
|---|---|
| `generate_docs.sh` | Genera documentación HTML de los módulos Python en `docs-output/` usando pdoc. También disponible en runtime: `/docs` (Swagger) y `/redoc` (ReDoc). |
