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
```
GET /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}
```

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
```
PUT /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}
```

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
```
DELETE /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}
```

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
