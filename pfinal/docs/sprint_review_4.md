# Sprint 4 – Endpoint de Sugerencias IA (Synonyms / Keywords)

> **Este documento:** Sprint 4 — sugerencias IA (Groq/fallback IPTC), CRUD de roles, integridad referencial.
> **Anterior:** [`sprint_review_3.md`](sprint_review_3.md) · **Siguiente:** [`sprint_review_5.md`](sprint_review_5.md)

En este apartado se implementa un endpoint basado en IA que permite generar **sugerencias de palabras clave y sinónimos** a partir de un término introducido por el usuario.

------------------------------------------------------------------------

## Objetivo del Endpoint

-   Generar sinónimos o términos relacionados a partir de una keyword.
-   Mejorar la capacidad del sistema para detectar noticias relevantes.
-   Asistir al usuario en la creación de alertas más completas.
-   Proveer una capa básica de IA aplicada al filtrado de información.

------------------------------------------------------------------------

## Endpoint

### GET `/api/v1/suggestions`

------------------------------------------------------------------------

## Autenticación

Este endpoint requiere autenticación mediante JWT:

-   Debe presionarse el boton de autenticar con el token recibido después de autenticarse (parte superior derecha):

``` http
Authorization: Bearer <token>
```

### Ejemplo de petición

`GET /api/v1/suggestions?keyword=economía`

### Lógica interna

El endpoint utiliza la función:

generate_synonyms(keyword)

Recibe una palabra clave. Genera una lista de sinónimos o términos relacionados. Devuelve una estructura JSON con la keyword original y sus sugerencias.

### Respuesta esperada

Código: 200 OK { "keyword": "economía", "suggestions": \[ "finanzas", "mercado", "comercio", "economía global", "macroeconomía" \] }

### Casos de prueba

#### Caso 1: Keyword válida

##### Input:

economía

##### Esperado:

Lista de sinónimos no vacía Código 200

#### Caso 2: Keyword desconocida

##### Input:

asdfghjkl

##### Esperado:

Lista vacía o sugerencias genéricas Código 200

#### Caso 3: Sin autenticación

##### Input: sin token

##### Resultado esperado:

{ "detail": "Not authenticated" }

Código: 401 Unauthorized

# Sprint 4 – Gestión de Roles (CRUD)

Pese a que originalmente estaba previsto para un sprint anterior, debido a problemas técnicos se ha agregado en este sprit la gestión de Roles. En este sprint se implementa la gestión completa de **roles de usuario** dentro de **NewsRadar**, permitiendo su creación, consulta, actualización y eliminación, asegurando además la integridad del sistema evitando eliminar roles asignados.

------------------------------------------------------------------------

## Objetivos del Sprint

-   Definir modelo de datos para roles
-   Implementar lógica CRUD para roles
-   Garantizar integridad referencial (roles asignados no se eliminan)
-   Exponer endpoints REST protegidos mediante autenticación

------------------------------------------------------------------------

## Modelo de Datos

Archivo: `app/models/models.py`

### Role

Representa los roles disponibles dentro del sistema.

-   **id**: int (PK)
-   **name**: Nombre del rol

------------------------------------------------------------------------

## Endpoints disponibles

| Método | Ruta                    | Descripción               |
| ------ | ----------------------- | ------------------------- |
| GET    | /api/v1/roles           | Listar todos los roles    |
| POST   | /api/v1/roles           | Crear un nuevo rol        |
| GET    | /api/v1/roles/{role_id} | Obtener un rol específico |
| PUT    | /api/v1/roles/{role_id} | Actualizar un rol         |
| DELETE | /api/v1/roles/{role_id} | Eliminar un rol           |

------------------------------------------------------------------------

# Flujo de Prueba – Gestión de Roles

Este flujo describe paso a paso cómo probar manualmente los endpoints de **roles** utilizando Swagger o cualquier cliente HTTP.

------------------------------------------------------------------------

### Autenticación

Antes de probar cualquier endpoint, es necesario autenticarse.

#### Endpoint

`POST /api/v1/auth/login`

#### Body

``` json
{
  "email": "usuario@test.com",
  "password": "password123"
}
```

#### Respuesta esperada

``` json
{
  "access_token": "TOKEN_JWT"
}
```

Copia el access_token, y en el botón "Authorize" (arriba a la derecha), pega el token.

### Listar Roles Iniciales

#### Endpoint

`GET /api/v1/roles`

#### Objetivo

Ver los roles existentes antes de realizar cambios.

#### Resultado esperado:

Código: 200 OK

Lista de roles (puede estar vacía o contener roles por defecto)

### Crear un Nuevo Rol

#### Endpoint

`POST /api/v1/roles`

#### Headers

Authorization: Bearer TOKEN_JWT

``` json
Body:
{
  "name": "tester"
}
```

#### Objetivo

Crear un nuevo rol en el sistema.

#### Resultado esperado

Código: 201 Created Devuelve el rol creado con su id

``` json
{
  "id": 3,
  "name": "tester"
}
```

Guarda el id del rol (role_id) para los siguientes pasos.

### Obtener Rol por ID

#### Endpoint

`GET /api/v1/roles/{role_id}`

#### Ejemplo

GET /api/v1/roles/3

#### Objetivo

Verificar que el rol fue creado correctamente.

#### Resultado esperado

Código: 200 OK Datos del rol

### Actualizar el Rol

#### Endpoint:

`PUT /api/v1/roles/{role_id}`

``` json
Body:
{
  "name": "tester_updated"
}
```

#### Objetivo

Modificar el nombre del rol.

#### Resultado esperado

Código: 200 OK Rol actualizado

### Verificar Actualización

#### Endpoint

`GET /api/v1/roles/{role_id}`

#### Objetivo

Confirmar que los cambios se aplicaron correctamente.

#### Resultado esperado

El campo name debe ser "tester_updated"

### Intentar Obtener Rol Inexistente

#### Endpoint:

`GET /api/v1/roles/99999` \#### Objetivo:

Verificar manejo de errores.

#### Resultado esperado

Código: 404 Not Found

### Eliminar Rol

#### Endpoint:

`DELETE /api/v1/roles/{role_id}`

#### Ejemplo

DELETE /api/v1/roles/3

#### Headers

Authorization: Bearer TOKEN_JWT Objetivo:

Eliminar el rol creado.

#### Resultado esperado

Código: 204 No Content

### Verificar Eliminación

#### Endpoint:

`GET /api/v1/roles/3`

#### Objetivo

Confirmar que el rol fue eliminado.

#### Resultado esperado

Código: 404 Not Found

### Caso Especial: Rol Asignado

#### Endpoint:

`DELETE /api/v1/roles/1`

#### Objetivo

Intentar eliminar un rol que está asignado a usuarios.

#### Resultado esperado

Código: 409 Conflict Mensaje de error:

``` json
{
  "detail": "No se puede eliminar un rol asignado a usuarios"
}
```

------------------------------------------------------------------------

## Resumen — Estado al cierre de Sprint 4 (revisado mayo 2026)

Al finalizar el Sprint 4, NewsRadar incorpora sugerencias de keywords asistidas por IA y la gestión completa de roles, sobre la base de alertas y scheduler del Sprint 3.

> **Correcciones respecto al documento original:** - Las sugerencias utilizan **Groq AI** como motor principal; si no hay API key configurada, caen en un fallback basado en categorías IPTC. El resultado sigue siendo `{"keyword": "...", "suggestions": [...]}`. - Los roles `admin`, `user` y `gestor` están **sembrados automáticamente** al arrancar; no es necesario crearlos manualmente. - Eliminar un rol asignado a usuarios devuelve `409 Conflict` (comportamiento correcto, sin cambios).

### De qué consta

| Área                       | Detalle                                                                                                        |
| -------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Sugerencias IA**         | `GET /api/v1/suggestions?keyword=...` — genera términos relacionados vía Groq AI o fallback IPTC; requiere JWT |
| **Modelo `Role`**          | `id`, `name` — roles disponibles en el sistema                                                                 |
| **CRUD roles**             | `GET`, `POST`, `PUT`, `DELETE /api/v1/roles` — protegidos con JWT                                              |
| **Roles semilla**          | `admin`, `user` y `gestor` creados automáticamente al inicializar la BD                                        |
| **Integridad referencial** | Eliminar un rol asignado a usuarios → `409 Conflict`                                                           |

### Ejemplos

**Sugerencias de keywords**

``` bash
curl "http://localhost:8000/api/v1/suggestions?keyword=economia" \
  -H "Authorization: Bearer <JWT>"
# { "keyword": "economia", "suggestions": ["finanzas", "mercado", "comercio", ...] }
```

**Listar roles existentes**

``` bash
curl http://localhost:8000/api/v1/roles \
  -H "Authorization: Bearer <JWT>"
# [ { "id": 1, "name": "admin" }, { "id": 2, "name": "user" }, { "id": 3, "name": "gestor" } ]
```

**Crear un rol adicional**

``` json
// POST /api/v1/roles
// Authorization: Bearer <JWT>
// Request
{ "name": "tester" }

// Response 201
{ "id": 4, "name": "tester" }
```

**Intentar eliminar rol asignado**

``` bash
curl -X DELETE http://localhost:8000/api/v1/roles/1 \
  -H "Authorization: Bearer <JWT>"
# 409 Conflict — { "detail": "No se puede eliminar un rol asignado a usuarios" }
```
