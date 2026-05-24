# Modelo de datos NewsRadar

> **Este documento:** instrucciones para regenerar el diagrama entidad-relación y descripción de las tablas.
> **Ver también:** [`../arquitectura.md`](../arquitectura.md) · [`../trazabilidad_requisitos.md`](../trazabilidad_requisitos.md)

## Cómo regenerar el diagrama

El diagrama se genera con **[dbdiagram.io](https://dbdiagram.io)**:

1. Abre [dbdiagram.io](https://dbdiagram.io)
2. Borra el ejemplo por defecto
3. Pega el contenido de `code_generar_dbdiagram_io.sql` (DBML)
4. El diagrama se genera automáticamente
5. Exporta al formato deseado:
   - **Export → PNG** → `DiagramaRelacionEntidad.png`
   - **Export → PDF** → `DiagramaRelacionEntidad.pdf`
   - **Export → SVG** → `DiagramaRelacionEntidad.svg`
   - **Export → PostgreSQL** → `DiagramaRelacionEntidad.sql`

---

## Entidades y atributos

### User
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| email | string | unique, not null |
| first_name | string | not null |
| last_name | string | not null |
| organization | string | not null |
| hashed_password | string | not null |

### Role
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| name | string | unique, not null |

### user_roles *(tabla intermedia)*
| Campo | Tipo | Restricción |
|---|---|---|
| user_id | int | PK, FK → User.id |
| role_id | int | PK, FK → Role.id |

### Category
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| name | enum (17 IPTC) | not null |
| source | string | default "IPTC" |

### InformationSource
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| name | string | not null |
| medium | string | nullable |
| rss_url | string | not null |
| iptc_category | string | nullable |

### RSSChannel
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| url | string | unique, not null |
| information_source_id | int | FK → InformationSource.id |
| category_id | int | FK → Category.id |

### NewsItem
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| title | string | not null |
| link | string | unique, not null |
| summary | text | nullable |
| published | datetime | nullable |
| channel_id | int | FK → RSSChannel.id |

### Alert
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| name | string | not null |
| descriptors | JSON | lista de palabras clave |
| categories | JSON | categorías IPTC seleccionadas |
| cron_expression | string | default "*/5 * * * *" |
| is_active | boolean | not null |
| user_id | int | FK → User.id |

### AlertNews *(tabla intermedia)*
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| alert_id | int | FK → Alert.id |
| news_item_id | int | FK → NewsItem.id |

### Notification
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| timestamp | datetime | default now() |
| metrics | JSON | |
| alert_id | int | FK → Alert.id |

### Stats
| Campo | Tipo | Restricción |
|---|---|---|
| id | int | PK |
| metrics | JSON | |

---

## Relaciones

| Desde | Cardinalidad | Hasta | Via |
|---|---|---|---|
| User | 1 — * | Role | user_roles (many-to-many) |
| User | 1 — * | Alert | Alert.user_id |
| Alert | 1 — * | Notification | Notification.alert_id |
| Alert | 1 — * | AlertNews | AlertNews.alert_id |
| NewsItem | 1 — * | AlertNews | AlertNews.news_item_id |
| RSSChannel | 1 — * | NewsItem | NewsItem.channel_id |
| InformationSource | 1 — * | RSSChannel | RSSChannel.information_source_id |
| Category | 1 — * | RSSChannel | RSSChannel.category_id |

---

## Diagrama texto (para referencia visual)

```
Role ←——(user_roles)——→ User ——→ Alert ——→ Notification
                                  |
                                  └——→ AlertNews ←—— NewsItem ←—— RSSChannel ←—— InformationSource
                                                                       |
                                                                   Category
```
