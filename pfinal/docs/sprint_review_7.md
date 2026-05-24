# Sprint Review 7 – Tests, CI/CD y Documentación

Este sprint consolida la calidad del proyecto mediante una suite de tests completa, un pipeline de integración y entrega continua en GitHub Actions, y documentación técnica actualizada.

---

## Objetivos del Sprint

- Alcanzar cobertura de tests ≥ 80% en módulos de lógica.
- Automatizar verificación de calidad en cada push (CI).
- Automatizar empaquetado Docker (CD).
- Completar documentación técnica: ADRs, guías, diagramas.

---

## Tests

Tests en 13 archivos bajo `app/tests/`:

| Módulo           | Cobertura |
| ---------------- | --------- |
| `models.py`      | 100%      |
| `alertLogic.py`  | 82%       |
| `database.py`    | 71%       |
| `ai.py`          | 62%       |
| **TOTAL lógica** | **96%**   |

Ejecutar:
```bash
docker compose exec app python -m pytest app/tests/ -v
```

Los ficheros de infraestructura (`main.py`, `scheduler.py`, `fetcher.py`, `notifications.py`, `seed_rss.py`) están excluidos del umbral de cobertura en `.coveragerc` — se verifican mediante los 281 casos del verificador del enunciado.

---

## Pipeline CI/CD — GitHub Actions

Fichero: `.github/workflows/fastapi-ci.yml` — se ejecuta en cada push.

| Paso | Herramienta         | Resultado                                      |
| ---- | ------------------- | ---------------------------------------------- |
| 1    | pytest + pytest-cov | 96.48% cobertura · 13 archivos, umbral ≥ 80%   |
| 2    | Upload coverage XML | Artifact `coverage-report`                     |
| 3    | Flake8              | Estilo PEP8                                    |
| 4    | Bandit              | Análisis de seguridad estático                 |
| 5    | Radon               | Complejidad ciclomática                        |
| 6    | pip-audit           | Vulnerabilidades en dependencias               |
| 7    | ESLint              | Calidad del JavaScript del frontend            |
| 8    | pdoc                | Documentación HTML → artifact `technical-docs` |
| 9    | docker build        | Empaquetado de la imagen `newsradar:latest`    |

---

## Documentación generada

- **14 ADRs** en `docs/adr/` — decisiones arquitectónicas numeradas 0001–0014.
- **Swagger / ReDoc** — generados automáticamente por FastAPI en `/docs` y `/redoc`.
- **pdoc** — documentación HTML de módulos Python generada por `generate_docs.sh` y como artifact de CI.
- **Sprint reviews** — `docs/sprint_review_0_y_1.md` a `docs/sprint_review_7.md`.
- **CI/CD** — `docs/ci_cd_documentation.md`.
- **Tests** — `docs/tests_documentation.md`.

---

## Estado final del verificador

281/281 casos OK — verificado el 2026-05-22.
