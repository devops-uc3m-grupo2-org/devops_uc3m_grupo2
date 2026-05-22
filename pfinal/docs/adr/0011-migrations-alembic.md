# ADR 011: Migrations — Alembic

## Estado
**Aceptado — Decisión revisada: se usa `create_all()` en lugar de Alembic (2026-05)**

## Contexto

La evolución del esquema de BD requiere control de versiones y migraciones reproducibles en un entorno de CI/CD con contenedores Docker.

## Decisión final (implementación real)

**No se usa Alembic.** El esquema se crea automáticamente en cada arranque con `Base.metadata.create_all(bind=engine)` dentro del evento `startup` de FastAPI.

```python
# pfinal/app/main.py — al arrancar
Base.metadata.create_all(bind=engine)
seed_categories(db)
seed_rss_channels(db)
```

El comando de despliegue limpio es `bash pfinal/start.sh`, que hace `docker compose down -v` (borra el volumen) + rebuild. Esto garantiza un esquema siempre fresco y consistente con los modelos actuales.

## Por qué se descartó Alembic

- Con `docker compose down -v` + rebuild como estrategia de despliegue, no hay estado previo que migrar — el esquema se crea desde cero en cada arranque limpio.
- Alembic aporta valor cuando hay datos en producción que no se pueden borrar. En el contexto del proyecto (examen, BD de prueba), el enfoque `create_all` es suficiente y más simple.
- El enunciado no exige versionado de migraciones, solo un despliegue automatizado en entorno limpio — que `start.sh` cubre.

## Consecuencias

- El despliegue es siempre desde cero (`start.sh`): no hay migraciones incrementales.
- Si en el futuro hubiera datos persistentes que preservar, se debería migrar a Alembic.

## Fecha

2026-03-12 — propuesta inicial con Alembic
2026-05 — decisión revisada: `create_all()` + `start.sh` como estrategia de despliegue
