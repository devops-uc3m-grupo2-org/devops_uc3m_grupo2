# Buenas prácticas de Git, GitHub y versionado

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
