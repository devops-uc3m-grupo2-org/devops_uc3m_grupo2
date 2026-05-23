# Documentación Tests Automáticos

---

#  Formato de los ficheros de tests

Todos los ficheros de tests deben seguir el formato:

```
test_*.py
```
o
```
*_test.py
```

Esto permite que sean detectados automáticamente por **pytest** y ejecutados dentro del **CI (Continuous Integration)**.

✔ Esto garantiza:
- Ejecución automática de nuevos tests
- Sin configuración adicional
- Integración directa con CI/CD

---

# Entorno de ejecución de tests

El proyecto utiliza principalmente **PostgreSQL en Docker** para ejecutar los tests, replicando el entorno real de producción.

Anteriormente se usaba:
- SQLite en memoria
- o archivo local (`sqlite:///./newsradar.db`)

Pero se migró a PostgreSQL para asegurar coherencia con producción.

---

##  Ejecutar tests localmente

> **Importante:** los tests deben ejecutarse **dentro del contenedor Docker** para que el hostname `db` resuelva correctamente. No ejecutar con pytest directo desde Windows/WSL.

### Todos los tests de golpe

```bash
docker compose exec app python -m pytest app/tests -v
```

Resultado esperado: **72 tests passed** en ~72 segundos (72 tests en total).

---

### Un archivo concreto

```bash
docker compose exec app python -m pytest app/tests/test_health.py -v
docker compose exec app python -m pytest app/tests/test_ai.py -v
docker compose exec app python -m pytest app/tests/test_alerts.py -v
```

---

### Un test concreto por nombre

```bash
docker compose exec app python -m pytest app/tests/test_stats.py::test_stats_returns_metrics -v
```

---

### Configurar base de datos

La `DATABASE_URL` está ya configurada en el contenedor:

```env
DATABASE_URL=postgresql://postgres:postgres123@db:5432/newsradar
```

---

# Ubicación de los tests

Todos los tests están organizados en:

```
app/tests/
```

---

## Estructura por dominio

- auth  
- users  
- roles  
- alerts  
- notifications  
- news  
- categories  
- stats  
- ai (suggestions)  
- integration (monitoring pipeline)  
- unit tests (lógica interna)  

---

# Fichero de configuración: `conftest.py`

Este archivo define las **fixtures de pytest** que preparan el entorno de tests con FastAPI.

# Arquitectura del sistema de testing

El sistema de tests se basa en **3 capas principales** que garantizan consistencia, aislamiento y reproducibilidad en todo el backend de **NewsRadar**.

---

# 1. Base de datos de test (PostgreSQL)

La base de datos de tests se gestiona automáticamente.

### Ciclo de vida

- Se crea automáticamente con `setup_database`
- Se destruye al finalizar el test suite
- Se ejecuta una migración inicial (`create_all`)

---

### Seed inicial

Durante la inicialización se insertan datos base:

- roles:
  - `admin`
  - `user`
- usuario admin del sistema

---

### Objetivo

Garantizar un estado inicial **siempre consistente y reproducible**.

---

# Aislamiento por transacciones

Cada test se ejecuta dentro de una transacción aislada.

---

### Funcionamiento

- Se usa una conexión real a PostgreSQL
- Cada test abre una transacción
- Al finalizar el test → se ejecuta `rollback`

---

### Resultado

✔ No hay datos residuales  
✔ No hay contaminación entre tests  
✔ Cada test es independiente  

---

# 3. Cliente FastAPI con override de dependencias

El fixture `client()` es el núcleo de los tests de API.

---

### Funcionalidad

El cliente:

- Sobrescribe `get_db`
- Usa la sesión de test
- Reemplaza dependencias reales por mocks controlados

---

### Objetivo

Permitir ejecutar requests HTTP reales como si fuera un usuario externo.

---

### Beneficio clave

Permite testear:

- autenticación
- permisos
- roles
- endpoints reales

---

# Fixtures principales

---

##  setup_database (scope=session)

Se ejecuta una sola vez al inicio del test suite.

---

### Responsabilidades

- Eliminar tablas anteriores
- Crear esquema de base de datos
- Insertar datos base:
  - roles
  - usuario admin

---

### Objetivo

Asegurar un entorno inicial limpio y consistente.

---

## session()

Proporciona una sesión de base de datos aislada.

---

### Características

- Conexión manual a PostgreSQL
- Cada test tiene su propia transacción
- Se aplica rollback al finalizar
- Evita contaminación entre tests

---

## client()

Proporciona un cliente HTTP de FastAPI.

---

### Permite:

- Testear endpoints reales
- Simular requests autenticados
- Usar dependencias overrideadas

---

 Es la base de todos los tests de API.

---

## create_news()

Helper para crear noticias en base de datos.

---

### Motivo

Las noticias reales dependen de scrapers externos, por lo que:

- no son deterministas
- no son fiables en tests

---

### Uso en tests

Permite validar:

- alert matching
- estadísticas
- pipelines de procesamiento

---

## create_user()

Helper para crear usuarios rápidamente.

---

### Motivo

Muchos endpoints dependen de `user_id`, por lo que:

- se evita el flujo completo de registro
- se garantizan relaciones válidas

---

### Uso en tests

- tests de integración
- tests de permisos
- tests de alertas y notificaciones

---

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

### test_news.py

| Test | Descripción |
|------|------------|
| test_list_news(client) | Verifica que el endpoint devuelve una lista de noticias correctamente |
| test_fetch_news_requires_auth(client) | Comprueba que el endpoint de fetch de noticias requiere autenticación (401 si no hay token) |
| test_fetch_news_authenticated(client) | Verifica que un usuario autenticado puede ejecutar el fetch de noticias y que la respuesta contiene el número de items (`new_items`) |


### test_alerts.py
| Test | Descripción |
|------|------------|
| test_alert_crud_for_user(client) | Test completo CRUD de alertas: crea, lista, obtiene detalle, actualiza y elimina una alerta de usuario |
| test_notification_crud_for_alert(client) | Test CRUD completo de notificaciones asociadas a una alerta (crear, listar, obtener, actualizar y eliminar) |


## test_auth_extended.py 

| Test | Descripción |
|------|------------|
| test_verify_invalid_token(client) | Verifica que un token inválido en verify devuelve error 400 |
| test_verify_wrong_purpose(client) | Comprueba que un token con propósito incorrecto falla en verify |
| test_forgot_password_unknown_email(client) | Verifica que forgot-password con email inexistente responde correctamente (sin exponer información sensible) |
| test_forgot_password_known_email(client) | Verifica que forgot-password funciona con email válido |
| test_reset_password_invalid_token(client) | Comprueba que reset-password falla con token inválido |
| test_reset_password_short_password(client) | Verifica validación de contraseña demasiado corta en reset-password |
| test_register_duplicate_email(client) | Comprueba que no se permite registrar usuarios con email duplicado (409 Conflict) |


## test_ai.py

| Test | Descripción |
|------|------------|
| test_suggestions_known_keyword(client) | Verifica que para una keyword conocida se generan sugerencias relevantes |
| test_suggestions_unknown_keyword(client) | Comprueba que el sistema genera sugerencias incluso para keywords desconocidas |
| test_suggestions_requires_auth(client) | Verifica que el endpoint requiere autenticación (401 sin token) |


## test_roles_extended.py

| Test | Descripción |
|------|------------|
| test_list_roles_requires_auth(client) | Verifica que el listado de roles requiere autenticación |
| test_list_roles(client) | Comprueba que se pueden listar roles existentes (admin/user seed incluidos) |
| test_create_role(client) | Verifica creación de un rol nuevo correctamente |
| test_get_role_by_id(client) | Comprueba obtención de un rol por ID |
| test_get_role_not_found(client) | Verifica error 404 al consultar un rol inexistente |
| test_update_role(client) | Verifica actualización de nombre de rol |
| test_update_role_not_found(client) | Verifica error 404 al actualizar un rol inexistente |
| test_delete_role_unassigned(client) | Comprueba eliminación de un rol no asignado a usuarios |
| test_delete_role_not_found(client) | Verifica error 404 al eliminar un rol inexistente |
| test_delete_assigned_role_returns_409(client) | Verifica que no se puede eliminar un rol asignado a usuarios (409 Conflict) |

## test_stats.py (Dashboard básico)

| Test | Descripción |
|------|------------|
| test_stats_returns_metrics(client) | Verifica que el endpoint `/stats` devuelve métricas del dashboard (news, sources, alerts) |
| test_stats_requires_auth(client) | Comprueba que el endpoint de estadísticas requiere autenticación (401 sin token) |
| test_stats_reflect_new_source(client) | Verifica que al crear una nueva fuente, la métrica `total_sources` se incrementa correctamente |


## test_stats_extended.py (Análisis por categoría)

| Test | Descripción |
|------|------------|
| test_stats_by_category_requires_auth(client) | Verifica que el endpoint de estadísticas por categoría requiere autenticación |
| test_stats_by_category_empty(client) | Comprueba que el endpoint responde correctamente cuando no hay datos (lista vacía o sin categorías) |
| test_wordcloud_requires_auth(client) | Verifica que el endpoint de wordcloud requiere autenticación |
| test_wordcloud_empty_no_alerts(client) | Comprueba que el wordcloud devuelve `{}` cuando no existen alertas |
| test_stats_by_category_with_alert(client) | Verifica que al crear una alerta, el endpoint de stats por categoría devuelve estructura válida con conteos |
| test_alert_limit_enforced(client) | Comprueba que existe un límite de creación de alertas por usuario (máximo 20) |
| test_alerts_check_endpoint(client) | Verifica que el endpoint `/alerts/check` responde correctamente |

## test_categories.py

| Test | Descripción |
|------|------------|
| test_list_categories_requires_auth(client) | Verifica que el endpoint de listado de categorías requiere autenticación (401 si no hay token) |
| test_create_category(client) | Comprueba que se puede crear una categoría correctamente con nombre y fuente (IPTC) |
| test_list_categories(client) | Verifica que las categorías creadas aparecen correctamente en el listado |
| test_get_category_by_id(client) | Comprueba que se puede obtener una categoría por su ID |
| test_get_category_not_found(client) | Verifica que consultar una categoría inexistente devuelve 404 |
| test_update_category(client) | Comprueba que se puede actualizar el nombre de una categoría correctamente |
| test_update_category_not_found(client) | Verifica error 404 al intentar actualizar una categoría inexistente |
| test_delete_category(client) | Verifica que se puede eliminar una categoría y que deja de existir |
| test_delete_category_not_found(client) | Comprueba que eliminar una categoría inexistente devuelve 404 |

### test_users_extended.py
| Test | Descripción |
|------|------------|
| test_get_user_by_id(client) | Verifica que se puede obtener un usuario por ID |
| test_get_user_not_found(client) | Comprueba que obtener un usuario inexistente devuelve 404 |
| test_update_user(client) | Verifica que se puede actualizar un usuario correctamente |
| test_update_user_duplicate_email(client) | Comprueba que no se puede actualizar un usuario con email duplicado (409) |
| test_create_user_direct_endpoint(client) | Verifica creación de usuario vía endpoint directo |
| test_create_user_duplicate_email(client) | Comprueba que no se pueden crear usuarios con email duplicado |
| test_delete_user(client) | Verifica que se puede eliminar un usuario correctamente |
| test_list_notifications(client) | Verifica que se pueden listar notificaciones de una alerta |
| test_create_notification(client) | Comprueba que se puede crear una notificación correctamente |
| test_get_notification_by_id(client) | Verifica que se puede obtener una notificación por ID |
| test_get_notification_not_found(client) | Comprueba que una notificación inexistente devuelve 404 |
| test_update_notification(client) | Verifica que se puede actualizar una notificación |
| test_delete_notification(client) | Comprueba que se puede eliminar una notificación correctamente |


---

## test_monitoring.py (lógica + pipeline de alertas)

### Tests unitarios de matching (alertLogic)

| Test | Descripción |
|------|------------|
| test_match_alert_descriptor_in_title() | Verifica que el sistema detecta un descriptor de alerta dentro del título de la noticia |
| test_match_alert_descriptor_in_summary() | Verifica que el sistema detecta un descriptor dentro del resumen de la noticia |
| test_match_alert_no_match() | Comprueba que no hay match cuando la noticia no contiene los descriptores |
| test_match_alert_case_insensitive() | Verifica que el matching no es sensible a mayúsculas/minúsculas |
| test_match_alert_empty_descriptors() | Comprueba que una alerta sin descriptores no genera matches |

---

### Test de integración (pipeline completo alert → news → AlertNews)

| Test | Descripción |
|------|------------|
| test_monitoring_pipeline(client, session) | Test de integración completo que verifica el flujo: registro de usuario → creación de alerta → inserción de news → ejecución del scheduler (`process_alerts_for_items`) → creación de relación AlertNews → validación de endpoints de notificaciones |

#### Flujo validado en este test:

1. Registro y autenticación de usuario
2. Creación de alerta con descriptor
3. Inserción manual en base de datos de:
   - InformationSource
   - Category
   - RSSChannel
   - NewsItem
4. Ejecución del motor de matching del scheduler
5. Verificación de relación `AlertNews`
6. Validación de endpoints de notificaciones
7. Creación de notificación simulada

---