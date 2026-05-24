# Buenas prácticas de Git, GitHub y versionado

> **Este documento:** guía de flujo de ramas, commits, SemVer y estrategia de branching del equipo para el proyecto NewsRadar.
> **Ver también:** [`ci_cd_documentation.md`](ci_cd_documentation.md) · [`sprint_review_0_indice_planificacion_sprints.md`](sprint_review_0_indice_planificacion_sprints.md)

Guía sencilla para usar Git, GitHub, ramas, tags y SemVer en un proyecto de desarrollo (por ejemplo, FastAPI + Docker).

---

## 1. Flujo básico de trabajo

1. Empezar from `main`:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Crear rama nueva para cada tarea:
   ```bash
   git checkout -b feat/nueva-ruta   # o bugfix/...
   ```

3. Hacer cambios y commits pequeños:
   ```bash
   git add .
   git commit -m "feat: añade nueva ruta /product/search"
   ```

4. Subir la rama a GitHub:
   ```bash
   git push origin feat/nueva-ruta
   ```

5. En GitHub:
   - Abrir **Pull Request** de `feat/nueva-ruta` → `main`.
   - Revisión de código, pruebas.
   - Si todo está OK: **Merge** → `main`.

6. Eliminar rama terminada:
   - En GitHub: borra la rama tras el merge.
   - En local (opcional):
     ```bash
     git checkout main
     git branch -d feat/nueva-ruta
     ```

---

## 2. Ramas: buenas prácticas

- **No commitear directo en `main`**.
- **Una rama por tarea** (pequeña y clara).
- Nombrar ramas con prefijos:
  - `feat/...`   → nueva funcionalidad.
  - `bugfix/...` → arregla bug.
  - `refactor/...` → reorganiza código sin cambiar comportamiento.
  - `chore/...` → cambios técnicos (CI, dependencias, etc.).
- Rama de corta duración: crear → trabajar → PR → fusionar → borrar.
- Actualizar tu rama con `main` antes de fusionar:
  ```bash
  git checkout main
  git pull origin main
  git checkout feat/tu-rama
  git rebase main
  git push origin feat/tu-rama --force-with-lease
  ```

---

## 3. Commits: buenas prácticas

- **Commits pequeños y atómicos**:
  - Cada commit hace una sola cosa.
- Usar tipo de commit al inicio del mensaje:
  - `feat: ...`       → nueva funcionalidad.
  - `fix: ...`        → corrige bug.
  - `refactor: ...`   → reorganiza código.
  - `chore: ...`      → cambios técnicos.
  - `doc: ...`        → mejora documentación.
  - `test: ...`       → añade o cambia tests.
- Formato de mensaje:
  - Línea corta: qué hiciste.
  - Si hace falta, líneas extra de cuerpo explicando por qué.
- Ejemplos:
  ```bash
  git commit -m "feat: añade /user/register"
  git commit -m "fix: corrige error 500 en login"
  git commit -m "refactor: divide auth_service.py"
  ```

---

## 4. Tags y versiones (SemVer)

### 4.1. Qué es un tag

- Un **tag** es una **etiqueta de versión** en un commit concreto.
- Ejemplo:
  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```
- Nunca se borra un tag ya subido (representa un punto fijo).

### 4.2. SemVer: `MAJOR.MINOR.PATCH`

Formato: `v1.2.5`
- `MAJOR` → 1
- `MINOR` → 2
- `PATCH` → 5

Casos:

- **PATCH**: solo arreglos de bug.
  - `v1.2.5 → v1.2.6`
- **MINOR**: añades nueva funcionalidad sin romper nada.
  - `v1.2.6 → v1.3.0`
- **MAJOR**: cambio que rompe compatibilidad.
  - `v1.3.0 → v2.0.0`

Ejemplo de flujo:

```bash
git tag v1.0.0    # primera versión estable
git tag v1.1.0    # nueva ruta /product/search
git tag v1.1.1    # arreglos de bug en login
git tag v2.0.0    # cambias toda la API v1/v2
```

Subir todos los tags:

```bash
git push origin --tags
```

---

## 5. Flujo simple aplicado a tu proyecto

Ejemplo típico FastAPI + Docker:

1. `git checkout main && git pull origin main`
2. `git checkout -b feat/user-registration`
3. Añadir ruta `/user/register`, pruebas, Docker, etc.
4. `git add .`
5. `git commit -m "feat: add user registration endpoint"`
6. `git push origin feat/user-registration`
7. En GitHub: Pull Request → `main`.
8. Tras aprobarse: merge → `main`.
9. En local:
   ```bash
   git checkout main
   git pull origin main
   git branch -d feat/user-registration
   ```
10. Cuando la versión está lista para “entrega”:
    ```bash
    git tag v1.1.0
    git push origin v1.1.0
    git push origin --tags
    ```

---

## 6. Qué NO hacer

- Hacer `git push -f` en `main` sin control.
- Combinar muchas tareas distintas en un solo commit.
- Dejar ramas viejas sin borrar después de fusionar.
- Forzar cambios de API sin cambiar de versión MAJOR.
- Usar `git checkout .` o `git restore .` sin saber qué vas a perder.







# Flujo de ramas y buenas prácticas de Git

Este documento define el flujo de ramas y las buenas prácticas de Git para el equipo de DevOps UC3M Grupo 2.

---

## 1. Estructura de ramas

Cada rama se crea desde `main` y se fusiona a `main` mediante una Pull Request.

### Backend (máximo 2 personas)

- **Backend 1**
  - Rama principal: `feat/backend-XX`
  - Ejemplo: `feat/backend-user-api`, `feat/backend-products`.

- **Backend 2**
  - Rama principal: `feat/backend-YY`
  - Ejemplo: `feat/backend-metrics`, `feat/backend-auth`.

### Frontend (1 persona fija + 1 flexible)

- **Frontend fijo**
  - Rama principal: `feat/frontend-XX`
  - Ejemplo: `feat/frontend-login`, `feat/frontend-dashboard`.

- **Frontend flexible**
  - Rama principal: `feat/frontend-flex`
  - Para cambios rápidos o pruebas de UI.

### Documentación

- Rama de documentación común:
  - `docs/team-guides`
  - Aquí se incluyen:
    - Buenas prácticas de Git y DevOps.
    - Historias de usuario.
    - READMEs y guías internas.

### Automatización y Testing

- **Automatización (CI/CD, scripts, etc.)**
  - Rama: `feat/automation`

- **Testing (pruebas unitarias, integración, etc.)**
  - Rama: `feat/testing`

### DevOps (supervisor y corrección de errores)

- **Corrección de errores y monitorización**
  - `devops/bugfix` → correcciones de incidencias en producción.
  - `devops/monitoring` → cambios de monitorización, métricas (DORA, logs, etc.).

---

## 2. Cómo crear las ramas

Ejemplos de comandos para cada rama (ejecutar desde `main` actualizado):

```bash
git checkout main
git pull origin main

# Backend 1
git checkout -b feat/backend-user-api
git push origin feat/backend-user-api

# Backend 2
git checkout -b feat/backend-metrics
git push origin feat/backend-metrics

# Frontend fijo
git checkout -b feat/frontend-login
git push origin feat/frontend-login

# Frontend flexible
git checkout -b feat/frontend-flex
git push origin feat/frontend-flex

# Documentación
git checkout -b docs/team-guides
git push origin docs/team-guides

# Automatización
git checkout -b feat/automation
git push origin feat/automation

# Testing
git checkout -b feat/testing
git push origin feat/testing

# DevOps bugfix
git checkout -b devops/bugfix
git push origin devops/bugfix

# DevOps monitoring
git checkout -b devops/monitoring
git push origin devops/monitoring
```

---

## 3. Flujo de trabajo básico

1. Cada miembro trabaja en su rama asignada.
2. Cuando la tarea está lista:
   - `git add .` y `git commit` con mensajes claros.
   - `git push origin <nombre-rama>`.
3. En GitHub:
   - Crear **Pull Request** `<nombre-rama>` → `main`.
   - Revisión de código, pruebas y aprobación.
4. Tras la aprobación:
   - Fusionar PR en `main`.
5. En local, una vez fusionado:
   ```bash
   git checkout main
   git pull origin main
   git branch -d <nombre-rama>
   ```
6. (Opcional) También borrar la rama remota:
   ```bash
   git push origin --delete <nombre-rama>
   ```

---

## 4. Relación con DevOps y automatización

- La rama `feat/automation` debe contener los scripts de CI/CD (GitHub Actions, etc.).
- La rama `devops/monitoring` guarda cambios relacionados con métricas, logs y monitorización del sistema.

Esto permite que el equipo siga las buenas prácticas de DevOps (DORA metrics, integración continua, etc.) mientras mantiene un flujo de Git limpio y organizado.

---
