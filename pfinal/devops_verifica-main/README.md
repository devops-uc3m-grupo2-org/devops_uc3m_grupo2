# Verificación automática de NewsRadar

Esta aplicación ejecuta los casos definidos en test_data/casos_prueba.csv.
También utiliza newsradar_openapi.json para comprobaciones del contrato de API.

## Alcance

- Los casos se enrutan por ámbito y por prefijo de ID de caso.
- Ámbitos soportados: API, Gestión de Usuarios, Gestión de Roles, Gestión de Categorías,
  Gestión de Fuentes de Información, Gestión de RSS Channels, Gestión de Stats,
  Gestión de Alertas, Gestión de Notificaciones e Inicialización del Sistema.
- Casos RN-* se ejecutan en la suite de alertas.
- Casos comentados: filas con ID comenzando por '#' se ignoran durante la ejecución.

## Evaluación

Este apartado vale 1 punto calculado como:

* 80% pasar todos los tests automáticos (287)
* 10% pasar los tests de inspección manuales (5)
* 10% test del propio proyecto, cobertura de código por encima del 80%, etc.

Nota: si los códigos de retorno en el API no son exactos pero sí la detección del problema, el caso de prueba se dará por superado. No obstante, sería conveniente ajustar el retorno de códigos en el API.

## Configuración

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Orden de ejecucion

Por defecto:

1. Se ejecutan primero los casos SMOKE-*.
2. Si hay algun SMOKE en estado NOK, la ejecución se detiene y no se ejecuta el resto.
3. Si todos los SMOKE pasan, se ejecutan los demas ámbitos.

Con --all:

1. Se ejecutan primero los SMOKE-*.
2. Aunque fallen, se continua con el resto de pruebas.

## Requisitos

- Entorno virtual Python activo o uso del intérprete del proyecto.
- Servicio NewsRadar levantado y accesible.

Instalación de dependencias del proyecto:

```bash
./devops_verifica/.venv/bin/pip install -r ./devops_verifica/requirements.txt
```

Si el entorno virtual ya está activado, también puede ejecutarse:

```bash
pip install -r requirements.txt
```


## Ejecución

Ejemplo básico:

```bash
./devops_verifica/.venv/bin/python run_tests.py
```

Ejecutar todo aunque falle SMOKE:

```bash
./devops_verifica/.venv/bin/python run_tests.py --all
```

Indicar URL del servicio por parámetro:

```bash
./devops_verifica/.venv/bin/python run_tests.py --service http://localhost:8000
```

Combinar ambos:

```bash
./devops_verifica/.venv/bin/python run_tests.py --service http://localhost:8000 --all
```

## Parámetros CLI

- --service: URL base del servicio NewsRadar. Si se indica, sobrescribe NEWSRADAR_BASE_URL.
- --all: ejecuta todas las pruebas incluso si falla la fase SMOKE.

## Comentarios en CSV

Para desactivar temporalmente un caso de prueba sin eliminarlo del fichero,
prefije su ID con '#':

```csv
RN-001,Recomendar entre 3 y 10 sinónimos,...
#RN-002,Limitar máximo de 20 alertas,...  ← Se ignora
SMOKE-001,Existir usuario administrador,...
```

## Variables de entorno

- NEWSRADAR_BASE_URL: URL base del servicio cuando no se usa --service.
- TEST_CASES_FILE: ruta del CSV de casos. Por defecto, test_data/casos_prueba.csv.
- OPENAPI_FILE: ruta del OpenAPI. Por defecto, newsradar_openapi.json.
- TEST_OUTPUT_FILE: ruta base del CSV de salida. El runner anade un sufijo de timestamp.

Ejemplo con variables de entorno:

```bash
NEWSRADAR_BASE_URL=http://localhost:8000 \
TEST_OUTPUT_FILE=/tmp/resultado_pruebas.csv \
./devops_verifica/.venv/bin/python run_tests.py
```

## Limpieza de datos

Cada caso de prueba que crea recursos (usuarios, alertas, etc.) los elimina automáticamente
después de su ejecución, incluso si falla el caso. Esto se aplica a todas las suites
y garantiza que datos residuales no interfieren en ejecuciones posteriores.

## Salida

Se genera un CSV con columnas:

- ID Caso de Prueba
- Estado (OK, NOK o WARNING)
- Código API (código HTTP extraído del detalle de respuesta)
- Explicación (tomada de la columna Comprobación del CSV de entrada)
- Detalle (mensaje técnico completo de la ejecución)

Adicionalmente, la consola muestra el detalle técnico de cada caso y un resumen final.


## Opcional: prueba de carga con Locust

El archivo `load_test.py` permite también ejecutar una prueba de carga simple orientada a provocar condiciones de carrera en el API de usuarios.

La prueba realiza dos tipos de operaciones sobre usuarios válidos con rol `gestor`:

- altas concurrentes de usuarios
- borrados concurrentes de esos mismos usuarios

Antes de crear usuarios, la prueba comprueba que exista el rol `gestor`; si no existe, intenta crearlo automáticamente.

La carga recomendada para esta prueba es de `100` usuarios virtuales con `spawn-rate 100`, de forma que cada usuario ejecute aproximadamente `1` petición por segundo y el escenario se aproxime a `100 req/s`.

### Escenario por defecto

Este modo reparte la carga sobre un conjunto pequeño de emails compartidos para generar colisiones frecuentes entre creación y borrado.

```bash
cd ./devops_verifica
./devops_verifica/.venv/bin/locust -f load_test.py --host http://localhost:8000 --users 100 --spawn-rate 100 --headless --run-time 2m
```

Opcionalmente puede ajustarse el tamaño del conjunto compartido con `LR_USER_POOL_SIZE`. Cuanto menor sea el valor, mayor será la contención.

Ejemplo:

```bash
cd ./devops_verifica
LR_USER_POOL_SIZE=10 \
./devops_verifica/.venv/bin/locust -f load_test.py --host http://localhost:8000 --users 100 --spawn-rate 100 --headless --run-time 2m
```

### Escenario de carga 

Este modo de carga trata de que todos los usuarios virtuales compitan sobre un único email, lo que incrementa la probabilidad de detectar problemas de concurrencia.

```bash
cd ./devops_verifica
LR_SCENARIO=fixed LR_FIXED_EMAIL=race-user-fixed@example.com \
./devops_verifica/.venv/bin/locust -f load_test.py --host http://localhost:8000 --users 100 --spawn-rate 100 --headless --run-time 2m
```

### Resultado esperado

Al finalizar, `load_test.py` imprime un resumen simple con conteos de respuestas relevantes para este escenario:

- `201` para altas creadas correctamente
- `204` para borrados correctos
- `404` para borrados sobre recursos que ya no existen
- `409` para conflictos de creación, si el API los utiliza

Este resultado no sustituye un análisis funcional detallado, pero sirve como señal rápida para detectar comportamientos anómalos bajo concurrencia.

# Verificación manual de NewsRadar

Las siguientes funcionalidades se verifican manualmente:

1. (M1) ¿Se envía un correo electrónico al detectar una noticia coincidente?
2. (M2) ¿El título del correo sigue el formato "Actualización de [alerta] en [día/hora]"?
3. (M3) ¿Se envía un correo de verificación al darse de alta un usuario?
4. (M4) ¿Caduca el enlace de verificación de usuario a las 24 horas?
5. (M5) ¿Se indexan las noticias con el Mock de RSS?
  * Se debe arrancar el servicio Mock RSS
  * Se debe crear una information source
  * Se debe crear un RSS channel asociada a esa information source con la URL del servicio Mock (ver siguiente sección)
  * Se debe crear una alerta añadiendo una categoría (la que se prefiera), con este canal RSS y con un ejecución de de cada minuto desde 0: * * * * *
  * Se deben esperar 2 minutos (2 ejecuciones) y se deben haber rescatado 8 noticias

# Mock RSS con FastAPI

API mínima para generar un feed RSS con actualizaciones simuladas:

- Primera llamada a `GET /rss`: devuelve 5 noticias sintéticas.
- Segunda llamada a `GET /rss`: devuelve 3 noticias sintéticas.
- Tercera y siguientes: devuelve 0 noticias (sin items).

## Requisitos

- Python 3.10+

## Arranque

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python mock_rss_service.py --port 8100 --reload
```

La API quedará disponible en el puerto elegido:

- RSS: `http://127.0.0.1:<PUERTO>/rss`
- Swagger: `http://127.0.0.1:<PUERTO>/docs`

## Prueba rápida

Ejecuta varias veces para ver el comportamiento por llamadas:

```bash
curl -s http://127.0.0.1:8100/rss
```

Nota: el estado de llamadas se guarda en memoria del proceso. Si reinicias el servidor, vuelve a empezar en 5 -> 3 -> 0.
