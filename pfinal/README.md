# NewsRadar - Fase 1

## Cómo ejecutar

Copiar el ejemplo de variables:

```bash
cp .env.example .env
```

Arrancar con Docker Compose:

```bash
docker compose up --build
```

Accede a:

- API: http://localhost:8000/docs
- pgAdmin: http://localhost:8080 (admin@newsradar.com / admin123)

Usuario admin por defecto:

- admin@newsradar.com / admin123

Prueba los endpoints `/api/v1/health` y `/api/v1/auth/login`.


