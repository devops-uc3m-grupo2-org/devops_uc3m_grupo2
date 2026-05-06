# Sprint 4 – IA Generativa (Sinónimos y Clasificación)


En este sprint buscamos utilizar la Inteligencia Artificial Generativa para encontrar sinónimos de la palabra clave que el usuario ha elegido. En este caso, utilizamos Gemini (modelos generativos de Google) para completar la tarea.

---

## Objetivos de Sprint 4

- Utilizar la Inteligencia Artifical para generar sinónimos de la palabra.

- Exponer endpoints REST para:
  - Crear Sinonimos

---

Se ha coniderado el enfoque de llamadas HTTP al endpoint adecuado de Gemini o al API de Google Cloud (según el plan y la cuenta), configurando `GEMINI_API_URL` y `GEMINI_API_KEY` o las credenciales necesarias.

Sin embargo, ha dado problemas el uso de las credenciales, por este motivo también se ha considerado una opción utilizar la librería google.generativeai. 

*función ia sigue en proceso de desarrollo*


# Sprint X – Gestión de Roles (CRUD)

Pese a que originalmente estaba previsto para un sprint anterior, debido a problemas técnicos se ha agregado en este sprit la gestión de Roles. En este sprint se implementa la gestión completa de **roles de usuario** dentro de **NewsRadar**, permitiendo su creación, consulta, actualización y eliminación, asegurando además la integridad del sistema evitando eliminar roles asignados.

---

## Objetivos del Sprint

- Definir modelo de datos para roles
- Implementar lógica CRUD para roles
- Garantizar integridad referencial (roles asignados no se eliminan)
- Exponer endpoints REST protegidos mediante autenticación

---

## Modelo de Datos

Archivo: `app/models/models.py`

### Role

Representa los roles disponibles dentro del sistema.

- **id**: int (PK)
- **name**: Nombre del rol

---

## Endpoints disponibles

| Método | Ruta                         | Descripción                          |
|--------|------------------------------|--------------------------------------|
| GET    | /api/v1/roles                | Listar todos los roles               |
| POST   | /api/v1/roles                | Crear un nuevo rol                   |
| GET    | /api/v1/roles/{role_id}      | Obtener un rol específico            |
| PUT    | /api/v1/roles/{role_id}      | Actualizar un rol                    |
| DELETE | /api/v1/roles/{role_id}      | Eliminar un rol                      |

---


#  Flujo de Prueba – Gestión de Roles

Este flujo describe paso a paso cómo probar manualmente los endpoints de **roles** utilizando Swagger o cualquier cliente HTTP.

---

### Autenticación

Antes de probar cualquier endpoint, es necesario autenticarse.

#### Endpoint:
`POST /api/v1/auth/login`

#### Body:
```json
{
  "email": "usuario@test.com",
  "password": "password123"
}
```

#### Respuesta esperada:
```json
{
  "access_token": "TOKEN_JWT"
}
```


Copia el access_token. En Swagger: botón Authorize → pega el token.

### Listar Roles Iniciales
#### Endpoint:

`GET /api/v1/roles`


#### Objetivo:

Ver los roles existentes antes de realizar cambios.

#### Resultado esperado:

Código: 200 OK

Lista de roles (puede estar vacía o contener roles por defecto)

### Crear un Nuevo Rol

#### Endpoint:

`POST /api/v1/roles`

#### Headers:
Authorization: Bearer TOKEN_JWT
```json
Body:
{
  "name": "tester"
}
```

#### Objetivo:

Crear un nuevo rol en el sistema.

#### Resultado esperado:
Código: 201 Created
Devuelve el rol creado con su id

```json
{
  "id": 3,
  "name": "tester"
}
```

Guarda el id del rol (role_id) para los siguientes pasos.

### Obtener Rol por ID

#### Endpoint:

`GET /api/v1/roles/{role_id}`

#### Ejemplo:

GET /api/v1/roles/3

#### Objetivo:

Verificar que el rol fue creado correctamente.

#### Resultado esperado:
Código: 200 OK
Datos del rol

### Actualizar el Rol
#### Endpoint:

`PUT /api/v1/roles/{role_id}`

```json
Body:
{
  "name": "tester_updated"
}
```

#### Objetivo:

Modificar el nombre del rol.

#### Resultado esperado:
Código: 200 OK
Rol actualizado


### Verificar Actualización
#### Endpoint:

`GET /api/v1/roles/{role_id}`

#### Objetivo:

Confirmar que los cambios se aplicaron correctamente.

#### Resultado esperado:
El campo name debe ser "tester_updated"

### Intentar Obtener Rol Inexistente
#### Endpoint:
`GET /api/v1/roles/99999`
#### Objetivo:

Verificar manejo de errores.

#### Resultado esperado:
Código: 404 Not Found

### Eliminar Rol
#### Endpoint:

`DELETE /api/v1/roles/{role_id}`

#### Ejemplo:
DELETE /api/v1/roles/3

#### Headers:
Authorization: Bearer TOKEN_JWT
Objetivo:

Eliminar el rol creado.

#### Resultado esperado:
Código: 204 No Content

### Verificar Eliminación
#### Endpoint:
`GET /api/v1/roles/3`

#### Objetivo:

Confirmar que el rol fue eliminado.

#### Resultado esperado:
Código: 404 Not Found

### Caso Especial: Rol Asignado
#### Endpoint:
`DELETE /api/v1/roles/1`

#### Objetivo:

Intentar eliminar un rol que está asignado a usuarios.

#### Resultado esperado:
Código: 409 Conflict
Mensaje de error:
```json
{
  "detail": "No se puede eliminar un rol asignado a usuarios"
}
```