# Sprint 5 – Gestión de Notificaciones (Alerts Notifications CRUD)

En este módulo se implementa la gestión completa de **notificaciones asociadas a alertas de usuario** dentro del sistema *NewsRadar*. Estas notificaciones representan eventos generados cuando una alerta detecta coincidencias con noticias o métricas relevantes.

---

# Objetivo del módulo

- Permitir listar notificaciones asociadas a una alerta.
- Crear notificaciones manualmente o desde el sistema de alertas.
- Consultar una notificación específica.
- Actualizar notificaciones existentes.
- Eliminar notificaciones.
- Garantizar que las notificaciones estén siempre asociadas a un usuario y una alerta válida.

---

# Autenticación

Todos los endpoints requieren autenticación con permisos de admin, debe ejecutarse la autenticación de usuario e incluir el token en el botón de "authorize" superior derecho.

Se debe ejecutar este Endpoint:

`POST /api/v1/auth/login`
```json
{
  "email": "admin@newsradar.com",
  "password": "admin123"
}
```

Se recibirá el Token:

Authorization: Bearer <token>

En el botón superior derecho "Authorize" se debe introducir este token.

# Endpoints disponibles


Previo a esto se debe crear un alerta para el usuario y guardar su id.

En Endpoint: 
`POST /api/v1/users/{user_id}/alerts`
Crea alerta de esta forma:

```json
{
  "name": "Guerra Alerta",
  "descriptors": ["guerra", "conflicto"],
  "categories": [
    {
      "code": "POL",
      "label": "Política"
    }
  ],
  "rss_channels_ids": [],
  "information_sources_ids": [],
  "cron_expression": "*/5 * * * *",
  "is_active": true
}
```
## Crear notificación

### Endpoint
```
POST /api/v1/users/{user_id}/alerts/{alert_id}/notifications
```

### Descripción
Crea una nueva notificación asociada a una alerta, para esto debes saber el id de la alerta creada y el id de su usuario.

### Body de la petición
```json
{
  "timestamp": "2026-05-06T10:00:00",
  "metrics": [
    {
      "name": "relevancia",
      "value": 0.85
    }
  ]
}
```

### Lógica interna:
- Valida la alerta del usuario  
- Crea objeto NotificationModel  
- Guarda métricas como estructura serializada  
- Persiste en base de datos  

### Respuesta esperada:
```json
{
  "id": 2,
  "timestamp": "2026-05-06T10:00:00",
  "alert_id": 2,
  "metrics": [
    {
      "name": "relevancia",
      "value": 0.85
    }
  ]
}
```

### Código de respuesta:
- **201 Created**

## Listar notificaciones de una alerta

### Endpoint
`GET /api/v1/users/{user_id}/alerts/{alert_id}/notifications`

### Descripción
Devuelve todas las notificaciones asociadas a una alerta específica de un usuario.

### Flujo interno
- Verifica que la alerta pertenece al usuario (get_alert_for_user)
- Consulta todas las notificaciones relacionadas con `alert_id`

### Respuesta esperada
```json
[
  {
    "id": 1,
    "timestamp": "2026-05-06T11:56:32.403000",
    "alert_id": 2,
    "metrics": [
      {
        "name": "string",
        "value": 0
      }
    ]
  },
  {
    "id": 2,
    "timestamp": "2026-05-06T10:00:00",
    "alert_id": 2,
    "metrics": [
      {
        "name": "relevancia",
        "value": 0.85
      }
    ]
  }
]
```

### Casos de prueba
- Usuario con alertas → 200 OK  
- Usuario sin acceso a la alerta → 403/404  
- Token inválido → 401  

---


---

## Obtener notificación específica

### Endpoint:
`GET /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}`

### Descripción:
Devuelve una notificación concreta dentro de una alerta, para esto necesitas el id de la notificación, alerta y usuario.

### Flujo interno:
- Verifica acceso a la alerta  
- Busca notificación por `alert_id + notification_id`  

### Respuesta esperada:
```json
 {
  "id": 2,
  "timestamp": "2026-05-06T10:00:00",
  "alert_id": 2,
  "metrics": [
    {
      "name": "relevancia",
      "value": 0.85
    }
  ]
}
```

### Casos de prueba:
-  Existe → 200 OK  
- No existe → 404 Not Found  

---

## Actualizar notificación

### Endpoint:
`PUT /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}`

### Descripción:
Permite modificar los campos de una notificación existente.

### Body opcional:
```json
{
  "timestamp": "2026-05-06T12:00:00",
  "metrics": [
    {
      "name": "impacto",
      "value": 0.92
    }
  ]
}
```

### Lógica interna:
- Busca la notificación  
- Actualiza solo los campos enviados (`exclude_unset=True`)  
- Guarda cambios en DB  

### Respuesta esperada:
```json
{
  "id": 1,
  "timestamp": "2026-05-06T12:00:00",
  "alert_id": 2,
  "metrics": [
    {
      "name": "impacto",
      "value": 0.92
    }
  ]
}
```

### Casos de prueba:
-  Update correcto → 200 OK  
-  Notificación inexistente → 404  

---

## Eliminar notificación

### Endpoint:
`DELETE /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}`

### Descripción:
Elimina una notificación específica de una alerta.

### Lógica interna:
- Verifica que la alerta pertenece al usuario  
- Verifica existencia de la notificación  
- Elimina registro de la base de datos  

### Respuesta esperada:
 ```http
 access-control-allow-credentials: true 
 access-control-allow-origin: * 
 date: Wed,06 May 2026 11:59:26 GMT 
 server: uvicorn 
 ```

### Casos de prueba:
- Eliminación correcta → 204  
- Notificación inexistente → 404  
- Sin permisos → 403  

Verificar si fue borrado correctamente con List Notifications
---


# Sprint 5 – RSS Channels (CRUD dentro de Information Sources)

Este módulo del backend de **NewsRadar** implementa la gestión de **canales RSS** asociados a una fuente de información. Permite consultar, actualizar y eliminar canales dentro de una fuente concreta, manteniendo la integridad de la relación entre fuentes y canales.

---

# Objetivos

- Obtener un canal RSS asociado a una fuente de información.
- Actualizar la configuración de un canal RSS.
- Eliminar un canal RSS de una fuente.
- Validar existencia de fuente y canal antes de operar.
- Restringir modificaciones y eliminaciones a usuarios con permisos de gestor.

---

# Endpoints disponibles

| Método | Ruta |
|--------|------|
| GET | `/api/v1/information-sources/{source_id}/rss-channels` |
| GET | `/api/v1/information-sources/{source_id}/rss-channels/{channel_id}` |
| PUT | `/api/v1/information-sources/{source_id}/rss-channels/{channel_id}` |
| DELETE | `/api/v1/information-sources/{source_id}/rss-channels/{channel_id}` |

---

## Obtener Lista de RSS

### Endpoint:
`GET /api/v1/information-sources/{source_id}/rss-channels/{channel_id}` 

Debes introducir el id de un canal RSS

### Objetivo:
Validar que se puede recuperar los canales RSS de una fuente.


### Caso de éxito

**Respuesta esperada (200 OK):**
```json 
[
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "category_id": 1,
    "id": 1,
    "information_source_id": 1
  },
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada",
    "category_id": 2,
    "id": 2,
    "information_source_id": 1
  },
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/ciencia/portada",
    "category_id": 3,
    "id": 3,
    "information_source_id": 1
  },
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/cultura/portada",
    "category_id": 4,
    "id": 4,
    "information_source_id": 1
  },
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/deportes/portada",
    "category_id": 5,
    "id": 5,
    "information_source_id": 1
  },
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/sociedad/portada",
    "category_id": 6,
    "id": 6,
    "information_source_id": 1
  },
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/salud/portada",
    "category_id": 7,
    "id": 7,
    "information_source_id": 1
  },
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/clima-y-medio-ambiente/portada",
    "category_id": 8,
    "id": 8,
    "information_source_id": 1
  },
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    "category_id": 9,
    "id": 9,
    "information_source_id": 1
  },
  {
    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/educacion/portada",
    "category_id": 10,
    "id": 10,
    "information_source_id": 1
  }
]
```

##  Crear canal Fuente

### Endpoint:
`POST /api/v1/information-sources/{source_id}/rss-channels`


### Objetivo:
Crear una fuente de RSS

---

### Requisitos:
- Usuario con rol **gestor** (asumimos que ya autenticado de prueba de notificaciones)
- Source ID de una fuente de la base de datos previamente creada.

---

### Body de ejemplo:
```json id="rss2_body"
{
  "url": "https://updated-source.com/rss",
  "category_id": 2
}
```

---

### Caso de éxito

**Respuesta esperada (200 OK):**
```json
{
  "url": "https://updated-source.com/rss",
  "category_id": 2,
  "id": 101,
  "information_source_id": 1
}
```

## Obtener canal RSS

### Endpoint:

`GET /api/v1/information-sources/{source_id}/rss-channels/{channel_id}`

Debes introducir el id de un canal RSS

### Objetivo:
Validar que se puede recuperar un canal RSS existente asociado a una fuente, puedes utilizar el canal previamente creado (verifica su id con el endpoint de "List")


### Caso de éxito

**Respuesta esperada (200 OK):**
```json
{
  "url": "https://updated-source.com/rss",
  "category_id": 2,
  "id": 101,
  "information_source_id": 1
}
```

---

### Casos de error

#### Fuente no existe
```json
{
  "detail": "Fuente de información no encontrada"
}
```
Código: 404

---

#### Canal no existe para la fuente
```json
{
  "detail": "Canal RSS no encontrado para la fuente"
}
```
Código: 404

---

## Actualizar canal RSS

### Endpoint:

`PUT /api/v1/information-sources/{source_id}/rss-channels/{channel_id}`

---

### Objetivo:
Modificar la URL o categoría de un canal RSS.

---

### Body de ejemplo:
```json
{
  "url": "https://updated2-source.com/rss",
  "category_id": 2
}
```

---

### Caso de éxito

**Respuesta esperada (200 OK):**
```json
{
  "url": "https://updated2-source.com/rss",
  "category_id": 2,
  "id": 101,
  "information_source_id": 1
}
```

---

### Casos de error

#### Fuente no encontrada
```json
{
  "detail": "Fuente de información no encontrada"
}
```
Código: 404

---

#### Canal no encontrado
```json id="rss2_err2"
{
  "detail": "Canal RSS no encontrado para la fuente"
}
```
Código: 404

---

#### Categoría no válida
```json id="rss2_err3"
{
  "detail": "Categoría no encontrada"
}
```
Código: 404

---

#### Sin permisos
Código: **403 Forbidden**

---

## Eliminar canal RSS

### Endpoint:
`DELETE /api/v1/information-sources/{source_id}/rss-channels/{channel_id}`


### Objetivo:
Eliminar un canal RSS asociado a una fuente.

---

### Caso de éxito

**Respuesta esperada:**
- Código: **204 No Content**
 access-control-allow-credentials: true 
 access-control-allow-origin: * 
 date: Wed,06 May 2026 12:21:21 GMT 
 server: uvicorn 

Verifica con el endpoint de List RSS si aparece aún.

---

### Casos de error

#### Fuente no encontrada
```json
{
  "detail": "Fuente de información no encontrada"
}
```
Código: 404

---

#### Canal no encontrado
```json
{
  "detail": "Canal RSS no encontrado para la fuente"
}
```
Código: 404

---

#### Sin permisos
Código: **403 Forbidden**

---

## Resumen — Estado al cierre de Sprint 5 (revisado mayo 2026)

Al finalizar el Sprint 5, NewsRadar incorpora el CRUD de notificaciones por alerta y la gestión de canales RSS dentro de cada fuente de información.

> **Correcciones respecto al documento original:**
> - El campo `information_sources_ids` en el body de alertas no existe en el estado final; el campo correcto es `rss_channels_ids`.
> - Las notificaciones se crean **automáticamente** por el scheduler al detectar coincidencias; el `POST` manual existe para pruebas pero no es el flujo habitual.
> - El rol requerido para PUT/DELETE en canales RSS es **gestor** (no admin); admin también puede operar.
> - La respuesta de `POST /rss-channels` devuelve `201 Created` (no `200 OK` como indica el documento).

### De qué consta

| Área | Detalle |
|------|---------|
| **Notificaciones — listar** | `GET /api/v1/users/{user_id}/alerts/{alert_id}/notifications` — devuelve buzón de la alerta |
| **Notificaciones — detalle** | `GET .../notifications/{notification_id}` |
| **Notificaciones — crear** | `POST .../notifications` — creación manual o automática por scheduler |
| **Notificaciones — actualizar** | `PUT .../notifications/{notification_id}` |
| **Notificaciones — eliminar** | `DELETE .../notifications/{notification_id}` → 204 |
| **Canales RSS — listar** | `GET /api/v1/information-sources/{source_id}/rss-channels` |
| **Canales RSS — detalle** | `GET .../rss-channels/{channel_id}` |
| **Canales RSS — crear** | `POST .../rss-channels` — requiere rol gestor |
| **Canales RSS — actualizar** | `PUT .../rss-channels/{channel_id}` — requiere rol gestor |
| **Canales RSS — eliminar** | `DELETE .../rss-channels/{channel_id}` — requiere rol gestor → 204 |

### Ejemplos

**Listar notificaciones de una alerta**
```bash
curl http://localhost:8000/api/v1/users/1/alerts/1/notifications \
  -H "Authorization: Bearer <JWT>"
# [ { "id": 1, "timestamp": "...", "alert_id": 1, "metrics": [...] } ]
```

**Listar canales RSS de una fuente**
```bash
curl http://localhost:8000/api/v1/information-sources/1/rss-channels \
  -H "Authorization: Bearer <JWT>"
# [ { "id": 1, "url": "https://...", "category_id": 1, "information_source_id": 1 }, ... ]
```

**Crear canal RSS (requiere gestor)**
```json
// POST /api/v1/information-sources/1/rss-channels
// Authorization: Bearer <JWT de gestor>
// Request
{ "url": "https://example.com/rss", "category_id": 2 }

// Response 201
{ "id": 101, "url": "https://example.com/rss", "category_id": 2, "information_source_id": 1 }
```

**Eliminar canal RSS**
```bash
curl -X DELETE http://localhost:8000/api/v1/information-sources/1/rss-channels/101 \
  -H "Authorization: Bearer <JWT de gestor>"
# 204 No Content
```
