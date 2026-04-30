# Arquitectura del sistema NewsRadar

## Diagrama de componentes

```mermaid
graph TB
    subgraph Cliente
        Browser["🌐 Navegador\n(HTML + CSS + JS)"]
        Swagger["📄 Swagger UI\n/docs"]
    end

    subgraph API["Backend — FastAPI (Python 3.12)"]
        Auth["Auth\n/api/v1/auth/*\nJWT · registro · login\nverificación · reset pwd"]
        Alerts["Alertas\n/api/v1/users/{id}/alerts\nCRUD · límite 20\ncontrol de roles"]
        Sources["Fuentes RSS\n/api/v1/information-sources\nCRUD · 100 canales IPTC"]
        News["Noticias\n/api/v1/news\nlistado · fetch · latest"]
        Stats["Estadísticas\n/api/v1/stats\nglobal · by-category\nwordcloud"]
        AI["IA\n/api/v1/suggestions\nsinónimos IPTC"]
    end

    subgraph Servicios["Servicios internos"]
        Scheduler["⏰ APScheduler\ncada 5 min\nfetch RSS + matching"]
        Fetcher["feedparser\nfetch_feed()"]
        AlertLogic["Motor de alertas\nprocess_alerts_for_items()\nmatch_alert()"]
        Notifier["Notificaciones\nnotify_alert()\nsend_email()"]
        Seed["Seed RSS\nseed_rss_channels()\n10 medios · 100 canales"]
    end

    subgraph Datos["Persistencia"]
        DB[("🗄️ PostgreSQL\nSQLAlchemy ORM")]
        SQLite[("🗄️ SQLite\n(desarrollo local)")]
    end

    subgraph Email["Email externo"]
        SMTP["📧 Gmail SMTP\nnewsradargrupo@gmail.com"]
    end

    subgraph RSS["Fuentes externas"]
        Feeds["📡 Feeds RSS\nEl País · El Mundo · ABC\nRTVE · Expansión · Marca\n+ 4 más"]
    end

    subgraph CI["CI/CD — GitHub Actions"]
        Pipeline["FastAPI CI\npytest 26 tests\ncoverage XML\nartifact upload"]
    end

    Browser -->|HTTP/REST| Auth
    Browser -->|HTTP/REST| Alerts
    Browser -->|HTTP/REST| Sources
    Browser -->|HTTP/REST| News
    Browser -->|HTTP/REST| Stats
    Swagger -->|HTTP/REST| Auth

    Auth --> DB
    Alerts --> DB
    Sources --> DB
    News --> DB
    Stats --> DB
    AI --> AI

    Scheduler -->|cada 5 min| Fetcher
    Fetcher -->|feedparser| Feeds
    Fetcher --> DB
    Scheduler --> AlertLogic
    AlertLogic --> DB
    AlertLogic --> Notifier
    Notifier -->|smtplib| SMTP

    DB --> SQLite
```

---

## Diagrama de flujo — Motor de alertas (Sprint 5)

```mermaid
sequenceDiagram
    participant S as APScheduler
    participant F as fetch_feed()
    participant RSS as Feed RSS externo
    participant DB as PostgreSQL
    participant AL as process_alerts_for_items()
    participant N as notify_alert()
    participant SMTP as Gmail SMTP

    S->>F: Ejecuta cada 5 min
    F->>RSS: feedparser.parse(url)
    RSS-->>F: Entradas nuevas
    F->>DB: INSERT NewsItem (si no existe)
    F-->>AL: news_items nuevos
    AL->>DB: SELECT Alert WHERE is_active=true
    loop Para cada noticia × alerta
        AL->>AL: match_alert() — re.search descriptors
        alt Coincidencia
            AL->>DB: INSERT AlertNews
            AL->>DB: INSERT Notification
        end
    end
    AL->>N: notify_alert(alert, matched_news)
    N->>SMTP: send_email() con resumen
```

---

## Diagrama de flujo — Registro y verificación de usuario

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant SMTP as Gmail SMTP

    U->>FE: Rellena formulario (email, nombre, apellidos, org, pwd)
    FE->>API: POST /api/v1/auth/register
    API->>DB: INSERT User (hashed_password)
    API->>SMTP: send_verification_email() — token JWT 24h
    SMTP-->>U: Email con enlace de verificación
    U->>API: GET /api/v1/auth/verify?token=...
    API-->>U: {"message": "Cuenta verificada correctamente"}
```

---

## Diagrama de flujo — Recuperación de contraseña

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant SMTP as Gmail SMTP

    U->>FE: Introduce email en "¿Olvidaste tu contraseña?"
    FE->>API: POST /api/v1/auth/forgot-password
    API->>DB: SELECT User WHERE email=...
    API->>SMTP: send_reset_email() — token JWT 1h
    SMTP-->>U: Email con enlace de reset
    U->>FE: Abre enlace (?reset_token=...)
    FE->>FE: Detecta token en URL, muestra formulario
    U->>FE: Introduce nueva contraseña
    FE->>API: POST /api/v1/auth/reset-password
    API->>DB: UPDATE User SET hashed_password=...
    API-->>U: {"message": "Contraseña actualizada correctamente"}
```

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | FastAPI + Python 3.12 |
| ORM | SQLAlchemy |
| Base de datos (prod) | PostgreSQL 15 |
| Base de datos (dev) | SQLite |
| Autenticación | JWT (python-jose + passlib) |
| RSS | feedparser |
| Scheduler | APScheduler |
| Email | smtplib + Gmail SMTP |
| Contenedores | Docker + Docker Compose |
| Frontend | HTML + CSS + JavaScript (vanilla) |
| CI/CD | GitHub Actions |
| Tests | pytest + pytest-cov (26 tests) |
