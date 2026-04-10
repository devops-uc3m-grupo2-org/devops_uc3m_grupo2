# Documentación Tests Automáticos

## Formato de los ficheros de los tests
Importante, todos los ficheros de los tests deben seguir este formato `*_test.py` o `test_*.py` para que sea identificado por pytest y se ejecuten con el Continuous Integration (CI).

## Ubicación de los tests
Todos los tests se encuentran divididos en ficheros en `app/tests`.

## Fichero de configuración de los tests "/Conftest"
Este archivo define fixtures de pytest que preparan el entorno de pruebas con FastAPI. Su objetivo es facilitar tests reproducibles, aislados y consistentes. Es importante comentar que las fixtures se crean cuando un test los necesita (incluido si es un parámetro) y se destruyen al terminar su proceso interno.

### Funciones principales
Se explicará el funcionamiento general, la explicación detallada de qué hace cada parte de la función, se puede ver a través de los comentarios de la misma.

### def setup_database / @pytest.fixture(scope="session", autouse=True)
Prepara la base de datos antes de ejecutar cualquier test y la limpia al final. Con los parámetros plantemoas que se ejecuta una sola vez en los tests, y que lo hace automáticamente (sin tener que llamarla).

### def session()
Proporciona una sesión de base de datos aislada para tests que interactúan directamente con **SQLAlchemy**. Cada test recibe una sesión de base de datos independiente. Es importante resaltar que hace rollback al final, para asegurarse que cada test este aislado.

### def client()
Proporciona un cliente HTTP para probar la API como si fuera un usuario externo. Se encarga también de cambiar las dependencias para que los tests utilicen una base de datos local en vez a la real (que no se guarden las alertas y soruces que creemos). Permite testear los endpoints sin tocar la base de datos de producción.

### def create_news()
Este es un helper para crear una noticia al instante. En el proyecto las noticias se crean con el fetcher, pero los tests no pueden depender de datos externos (¿hay noticias nuevas?¿En tal caso, alguna coincide con la alerta?). Por este motivo se creó esta función que permite simular una noticia en la base de datos, y en los test utilizamos esta noticia para probar endpoints como el MatchAlert.

## Tests

### test_health.py
|               Test            |           Descripción                     |      
| ------------------------------| ----------------------------------------- |
| test_health_endpoint(client)  | Testea si el programa se monta correctamente| 

### test_login.py
|               Test            |           Descripción                     |      
| ------------------------------| ----------------------------------------- |
|  test_login_success(client)  | Testea que sea exitoso un login con datos correctos| 
|  test_login_fail(client) | Testea que lance error un login con datos erronéos |
|  test_register_user(client) | Verifica si un registro se realizó correctamente| 

### test_sources.py
|               Test            |           Descripción                     |      
| ------------------------------| ----------------------------------------- |
|  test_create_source_ok(client)  | Verifica si un source se crea si se le <br> dan los datos correctos| 
|  test_create_source_duplicate(client) | Testea que lance error cuando se <br> crean dos sources con mismo url  |
|  test_list_sources(client) | Se crea un spurce y se verifica si aparece con list|
|  test_fetch_source_not_found(client) | Prueba un fetch de un source inexistente|
|  test_fetch_source_debug(client) |Crea un source y verifica si hace un <br>fetch correctamente|


