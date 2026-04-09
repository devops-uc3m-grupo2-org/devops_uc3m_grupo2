# 📋 GUÍA COMPLETA DE PRUEBAS - NewsRadar Frontend

## 📦 Requisitos Previos

- Docker y Docker Compose instalados
- Git (para clonar el repositorio)
- Un navegador web moderno (Chrome, Firefox, Edge, Safari)
- Terminal/PowerShell para ejecutar comandos

---

## 🚀 PASO 1: PREPARAR EL ENTORNO

### 1.1 Verificar que Docker está instalado

```bash
docker --version
docker compose --version
```

**Esperado:** Debe mostrar las versiones de Docker y Docker Compose (v2.x+)

### 1.2 Navegar al directorio del proyecto

```bash
cd c:\Users\brain\Downloads\devops_uc3m_grupo2\pfinal
```

### 1.3 Crear el archivo .env

Si no existe `.env`, copia el ejemplo:

```bash
cp .env.example .env
```

**Si `.env.example` no existe, crea `.env` con este contenido:**

```env
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql://postgres:postgres123@db:5432/newsradar

# AI (Opcional - solo si tienes clave de Google)
GOOGLE_API_KEY=your-key-here
```

---

## 🐳 PASO 2: EJECUTAR CON DOCKER COMPOSE

### 2.1 Iniciar todos los servicios

```bash
docker compose up --build
```

**Esperado en la consola:**

```
db       | PostgreSQL is starting...
pgadmin  | pgAdmin 4 is ready...
app      | Uvicorn running on http://0.0.0.0:8000
```

### 2.2 Esperar a que todo esté listo

El proceso puede tardar 1-2 minutos. Busca estos mensajes:

✅ `PostgreSQL is ready`  
✅ `pgAdmin 4 is ready`  
✅ `Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)`

### 2.3 En caso de error: Limpiar contenedores

Si algo sale mal, ejecuta en otra terminal:

```bash
docker compose down -v
docker system prune -f
docker compose up --build
```

---

## ✅ PASO 3: VERIFICAR QUE TODO FUNCIONA

### 3.1 Prueba 1: Health Check API

```bash
curl http://localhost:8000/api/v1/health
```

**Esperado:**
```json
{"status": "ok", "message": "NewsRadar listo con PostgreSQL + JWT"}
```

### 3.2 Prueba 2: Acceder a la API (Swagger)

Abre en el navegador:
```
http://localhost:8000/docs
```

Deberías ver:
- ✅ Página con documentación interactiva Swagger
- ✅ Todos los endpoints listados (Auth, Sources, News, Alerts)
- ✅ Sistema de prueba "Try it out" para cada endpoint

### 3.3 Prueba 3: Acceder al Frontend

Abre en el navegador:
```
http://localhost:8000/
```

Deberías ver:
- ✅ Pantalla de login con logo de NewsRadar
- ✅ Campo de email y contraseña
- ✅ Mensaje: "Credenciales por defecto: admin@newsradar.com / admin123"

---

## 🔐 PASO 4: PRUEBAS DE AUTENTICACIÓN

### 4.1 Login en la interfaz web

1. Ve a `http://localhost:8000/`
2. Ingresa:
   - **Email:** `admin@newsradar.com`
   - **Contraseña:** `admin123`
3. Haz clic en **"Iniciar Sesión"**

**Esperado:**
- ✅ Desaparece la pantalla de login
- ✅ Aparece el Dashboard
- ✅ Token se guarda en localStorage (verifica en DevTools → Application → Local Storage)

### 4.2 Verificar que el Dashboard carga

Deberías ver:
- ✅ **📡 Fuentes RSS:** 0 (o el número de fuentes existentes)
- ✅ **🔔 Alertas Activas:** 0
- ✅ **📰 Noticias Recientes:** 0
- ✅ **✅ Estado API:** OK

---

## 📡 PASO 5: PRUEBAS DE FUENTES RSS

### 5.1 Navegar a la sección Fuentes

1. En la navbar, haz clic en **"Fuentes"**
2. Haz clic en **"+ Nueva Fuente"**

### 5.2 Agregar una fuente RSS

Completa el formulario con datos reales:

```
Nombre: BBC News
Medio: Agencia de noticias
URL RSS: https://feeds.bbc.co.uk/news/rss.xml
Categoría: news
```

Haz clic en **"Crear Fuente"**

**Esperado:**
- ✅ Mensaje toast verde: "Fuente creada exitosamente"
- ✅ La fuente aparece en la lista
- ✅ Se muestra la tarjeta con los datos

### 5.3 Sincronizar noticias

En la tarjeta de la fuente, haz clic en **"📥 Sincronizar"**

**Esperado:**
- ✅ Toast: "✅ N nuevas noticias sincronizadas"
- ✅ El dashboard actualiza el contador de noticias

### 5.4 Agregar más fuentes (Opcional)

```
Nombre: Reuters
URL: https://www.reuters.com/rssFeed/worldNews
Categoría: world

Nombre: TechCrunch  
URL: https://feeds.techcrunch.com/
Categoría: technology
```

---

## 🔔 PASO 6: PRUEBAS DE ALERTAS

### 6.1 Navegar a Alertas

1. Haz clic en **"Alertas"** en la navbar
2. Haz clic en **"+ Nueva Alerta"**

### 6.2 Crear una alerta

Completa el formulario:

```
Nombre: Noticias de Tecnología
Palabra Clave: tecnología
Categoría: technology
Usuario ID: 1
```

Antes de crear, prueba **"Sugerencias IA"**:

**Esperado:**
- ✅ Se rellenan automáticamente sinónimos sugeridos por IA
- ✅ Por ejemplo: "tech, innovation, digital, AI"

Haz clic en **"Crear Alerta"**

**Esperado:**
- ✅ Toast: "Alerta creada exitosamente"
- ✅ Aparece en la lista con estado "🟢 Activa"

### 6.3 Crear otra alerta para pruebas

```
Nombre: Noticias de Política
Palabra Clave: política
Sinónimos: gobierno, elecciones, legislación
Categoría: politics
```

---

## 📰 PASO 7: PRUEBAS DE NOTICIAS

### 7.1 Ver todas las noticias

1. Haz clic en **"Noticias"** en la navbar

**Esperado:**
- ✅ Se muestran las noticias sincronizadas
- ✅ Cada noticia muestra:
  - Título (enlace clickeable)
  - Fecha de publicación
  - ID de fuente
  - Resumen

### 7.2 Filtro de noticias (opcional)

Haz clic en **"🔄 Actualizar"** para refrescar la lista

---

## ⚡ PASO 8: PRUEBAS DE ACCIONES AVANZADAS

### 8.1 Ejecutar Matching

1. Ve al **Dashboard**
2. Haz clic en **"⚡ Ejecutar Matching"**

**Esperado:**
- ✅ Toast: "✅ Matching ejecutado correctamente"
- ✅ El sistema asocia noticias con alertas según palabras clave

### 8.2 Ejecutar Scheduler

1. Haz clic en **"🔄 Ejecutar Scheduler"**

**Esperado:**
- ✅ Toast: "✅ Scheduler ejecutado correctamente"
- ✅ Se traen nuevas noticias de todas las fuentes

---

## 🔌 PASO 9: PRUEBAS CON SWAGGER (API Directa)

### 9.1 Acceder a Swagger

Ve a: `http://localhost:8000/docs`

### 9.2 Login por API

1. Expande **Auth** → **POST /api/v1/auth/login**
2. Haz clic en **"Try it out"**
3. En el body, ingresa:

```json
{
  "username": "admin@newsradar.com",
  "password": "admin123"
}
```

4. Haz clic en **"Execute"**

**Esperado:**
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```

### 9.3 Copiar token y usarlo

1. Copia el `access_token`
2. En la esquina superior derecha, haz clic en **"Authorize"**
3. Pega el token: `Bearer eyJ0eXAi...`
4. Haz clic en **"Authorize"**

**Esperado:**
- ✅ Todos los endpoints ahora requieren autenticación exitosa

### 9.4 Probar otros endpoints

- **GET /api/v1/health** → Debe responder con status "ok"
- **GET /api/v1/users** → Lista de usuarios
- **GET /api/v1/sources** → Lista de fuentes RSS
- **GET /api/v1/alerts** → Lista de alertas
- **GET /api/v1/news** → Últimas 200 noticias

---

## 🗄️ PASO 10: PRUEBAS DE BASE DE DATOS (pgAdmin)

### 10.1 Acceder a pgAdmin

Abre: `http://localhost:8080`

**Credenciales:**
```
Email: admin@newsradar.com
Contraseña: admin123
```

### 10.2 Conectar a la base de datos

1. En la panel de la izquierda, haz clic en **"Add New Server"**
2. En la pestaña **"General"**, ingresa:
   - **Name:** newsradar

3. En la pestaña **"Connection"**, ingresa:
   - **Host name/address:** db
   - **Port:** 5432
   - **Username:** postgres
   - **Password:** postgres123
   - **Database:** newsradar

4. Haz clic en **"Save"**

**Esperado:**
- ✅ Conexión exitosa
- ✅ Puedes ver las tablas: users, roles, information_sources, news_items, alerts, etc.

### 10.3 Verificar datos

1. Expande **newsradar** → **Schemas** → **public** → **Tables**
2. Haz clic derecho en **users** → **View/Edit Data** → **All Rows**

**Esperado:**
- ✅ Ves el usuario admin@newsradar.com

3. Repite para **information_sources**, **alerts**, **news_items**

---

## 🛑 PASO 11: PRUEBAS DE ERRORES Y VALIDACIONES

### 11.1 Intentar crear fuente con URL inválida

1. Ve a **Fuentes** → **+ Nueva Fuente**
2. Ingresa URL inválida: `no-es-una-url`
3. Haz clic en **"Crear Fuente"**

**Esperado:**
- ✅ Error de validación HTML5
- ✅ Campo resaltado en rojo

### 11.2 Intentar duplicar fuente

1. Intenta crear una fuente con la misma URL de una existente
2. Haz clic en **"Crear Fuente"**

**Esperado:**
- ✅ Toast error: "La fuente ya existe"

### 11.3 Logout y intentar acceder sin token

1. Haz clic en **"Salir"**

**Esperado:**
- ✅ Vuelves a la pantalla de login
- ✅ localStorage se limpia

2. Abre la consola (F12) y ejecuta:

```javascript
// Intenta acceder sin token
fetch('http://localhost:8000/api/v1/sources').then(r => r.json()).then(console.log)
```

**Esperado:**
- ✅ Error 401 o similar (no autorizado)

---

## 📊 PASO 12: MONITOREO Y DEBUG

### 12.1 Ver logs en tiempo real

En la terminal donde ejecutaste `docker compose up`, puedes ver:

```
app   | INFO:     127.0.0.1:49234 - "POST /api/v1/auth/login" → 200 OK
app   | INFO:     127.0.0.1:49235 - "GET /api/v1/sources" → 200 OK
```

### 12.2 Debug de fuentes RSS

En la tarjeta de fuente, haz clic en **"🔍 Debug"**

Recibirás información sobre:
```
Feed Status: 200
Total entries: 25
First entry: {...}
```

### 12.3 DevTools del Navegador

Presiona **F12** para abrir DevTools:

1. **Network tab:** Mira todas las peticiones HTTP
   - Debe haber llamadas a `/api/v1/...`
   
2. **Application tab:**
   - **Local Storage:** Verifica que guardó el token
   
3. **Console tab:**
   - Busca errores de JavaScript
   
**Esperado:**
- ✅ No debe haber errores rojos

---

## 🔧 PASO 13: SOLUCIÓN DE PROBLEMAS

### Problema: No se conecta a `http://localhost:8000`

```bash
# Verificar que los contenedores están corriendo
docker compose ps

# Debe mostrar: app, db, pgadmin todos en estado "Up"
```

Si alguno está en "Exit", ve los logs:

```bash
docker compose logs app
docker compose logs db
```

### Problema: Error "Cannot GET /"

El frontend no se sirvió correctamente. Verifica que:

1. Carpeta `/static` existe en `pfinal/`
2. Archivos están presentes: `index.html`, `styles.css`, `app.js`

```bash
ls -la pfinal/static/
```

### Problema: CORS error en consola

El frontend no se comunica con la API. Verifica que:

1. La API tiene CORS habilitado (`main.py` debe tener `CORSMiddleware`)
2. API_URL en `app.js` es correcto: `http://localhost:8000/api/v1`

### Problema: Noticias no se sincronizan

1. Verifica que la URL RSS es válida (test en navegador)
2. Ejecuta el debug: haz clic en **"🔍 Debug"** en la fuente
3. Verifica logs: `docker compose logs app`

---

## ✨ PASO 14: CASOS DE USO FINALES

### Flujo Completo de Usuario:

1. ✅ Login: admin@newsradar.com / admin123
2. ✅ Dashboard: Ver estado del sistema
3. ✅ Fuentes: Agregar 2-3 fuentes RSS
4. ✅ Sincronizar: Traer noticias de cada fuente
5. ✅ Alertas: Crear alertas con palabras clave
6. ✅ Matching: Ejecutar matching para asociar noticias
7. ✅ Noticias: Ver noticias que coinciden con alertas
8. ✅ Salir: Logout seguro

**Tiempo esperado:** 5-10 minutos

---

## 🎉 VALIDACIÓN FINAL

Si completaste todos los pasos y:

- ✅ Backend corre en Docker sin errores
- ✅ Frontend se sirve en `http://localhost:8000`
- ✅ Login funciona
- ✅ Puedes crear fuentes y alertas
- ✅ Noticias se sincronizan
- ✅ API responde correctamente

**¡FELICIDADES! Tu NewsRadar está funcionando perfectamente.**

---

## 📝 Notas Finales

- **Credenciales por defecto:** admin@newsradar.com / admin123
- **API URL:** http://localhost:8000/api/v1
- **Frontend URL:** http://localhost:8000/
- **Swagger Docs:** http://localhost:8000/docs
- **pgAdmin:** http://localhost:8080

---

## 🆘 Soporte

Si encuentras problemas:

1. **Revisa los logs:** `docker compose logs -f app`
2. **Limpia todo:** `docker compose down -v && docker compose up --build`
3. **Verifica URLs:** Asegúrate de que los RSS feeds son válidos
4. **Console JS:** F12 en el navegador para errores JavaScript

¡Listo para producción! 🚀
