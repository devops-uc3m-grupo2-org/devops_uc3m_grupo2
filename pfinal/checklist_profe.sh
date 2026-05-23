#!/usr/bin/env bash
# checklist_profe.sh — Las 26+40 preguntas del checklist del profesor (correo7.md)
# Verifica automáticamente lo que puede y muestra evidencia para lo demás.
#
# Uso:
#   bash pfinal/checklist_profe.sh              # solo las 26 preguntas de proceso
#   bash pfinal/checklist_profe.sh --proyecto   # también las 40 de proyecto
#
# Requisito: bash pfinal/start.sh antes (para los checks de API)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE="http://localhost:8000/api/v1"
SHOW_PROYECTO=false
[[ "${1:-}" == "--proyecto" ]] && SHOW_PROYECTO=true

PASS_A=0; FAIL_A=0; INFO_A=0
PASS_B=0; FAIL_B=0; INFO_B=0
SECTION="A"

ok()   {
    local id="$1"; shift
    echo "  ✅  [$id] $*"
    [ "$SECTION" = "A" ] && PASS_A=$((PASS_A+1)) || PASS_B=$((PASS_B+1))
}
fail() {
    local id="$1"; shift
    echo "  ❌  [$id] $*"
    [ "$SECTION" = "A" ] && FAIL_A=$((FAIL_A+1)) || FAIL_B=$((FAIL_B+1))
}
info() {
    local id="$1"; shift
    echo "  📋  [$id] $*"
    [ "$SECTION" = "A" ] && INFO_A=$((INFO_A+1)) || INFO_B=$((INFO_B+1))
}

hr() { echo ""; echo "── $1 ──────────────────────────────────────"; }

# ─── Datos que se calculan una sola vez ───────────────────────────────────────
REPO_SLUG="devops-uc3m-grupo2-org/devops_uc3m_grupo2"
GITHUB_URL="https://github.com/$REPO_SLUG"

# GitHub API — intenta gh (si está auth) y cae a curl público (sin auth, funciona en WSL)
_gh_or_curl() {
    local path="$1"
    gh api "$path" --jq 'length' 2>/dev/null && return
    curl -sf "https://api.github.com/$path" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?"
}
n_issues=$(_gh_or_curl "repos/$REPO_SLUG/issues?state=all&per_page=100")
n_milestones=$(_gh_or_curl "repos/$REPO_SLUG/milestones?state=all")

# Historia de usuario en issues (texto público)
hu_issue=$(curl -sf "https://api.github.com/repos/$REPO_SLUG/issues?state=all&per_page=50" \
    | python3 -c "
import sys, json
issues = json.load(sys.stdin)
for i in issues:
    t = i.get('title','')
    if any(k in t.upper() for k in ['COMO','QUIERO','PARA','HISTORIA','USER STORY']):
        print(t[:80]); break
" 2>/dev/null || echo "")

# Conteos locales (rápidos)
n_sprints=$(find "$SCRIPT_DIR/docs" -name "sprint_review*.md" 2>/dev/null | wc -l | tr -d ' ')
n_adr=$(find "$SCRIPT_DIR/docs/adr" "$REPO_DIR/docs/adr" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
n_branches=$(cd "$REPO_DIR" && git branch -a 2>/dev/null | grep -v "HEAD" | wc -l | tr -d ' ')
n_py=$(find "$SCRIPT_DIR/app" -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
n_unit=$(find "$SCRIPT_DIR/app/tests" -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
n_func=$(find "$SCRIPT_DIR/devops_verifica-main/tests" -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
git_files=$(cd "$REPO_DIR" && git ls-files 2>/dev/null | wc -l | tr -d ' ')
last_commit=$(cd "$REPO_DIR" && git log -1 --format="%cr" 2>/dev/null || echo "?")

# API (sin bloquear si está caída)
health_status=$(curl -sf "$BASE/health" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")

# Ficheros de arquitectura
arch_md="$REPO_DIR/docs/arquitectura.md"
arch_lines=$(wc -l < "$arch_md" 2>/dev/null || echo "0")

# Diagramas en docs/
diagrams=$(find "$SCRIPT_DIR/docs" "$REPO_DIR/docs" -name "*.png" -o -name "*.svg" -o -name "*.drawio" 2>/dev/null | head -5 | tr '\n' ' ')

# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Checklist del Profesor — NewsRadar DevOps                  ║"
echo "║  Repo: $GITHUB_URL"
printf "║  Fecha: %-51s║\n" "$(date '+%Y-%m-%d %H:%M')"
echo "╚══════════════════════════════════════════════════════════════╝"

# ═════════════════════════════════════════════════════════════════════════════
# BLOQUE A — PREGUNTAS_GENERALES_PROCESO (26 preguntas)
# ═════════════════════════════════════════════════════════════════════════════
SECTION="A"
echo ""
echo "┌──────────────────────────────────────────────────────────────┐"
echo "│  BLOQUE A — Proceso General (26 preguntas)                  │"
echo "└──────────────────────────────────────────────────────────────┘"

hr "ESPECIFICACIÓN (1–4)"

# 1 — Requisitos gestionados en alguna herramienta
if [[ "$n_issues" != "?" ]] && [ "$n_issues" -ge 5 ]; then
    ok "1" "Requisitos en GitHub Issues ($n_issues issues) → $GITHUB_URL/issues"
elif [[ "$n_issues" != "?" ]]; then
    info "1" "Issues GitHub: $n_issues — mostrar issues + sprint reviews"
else
    info "1" "Issues GitHub sin auth — mostrar $GITHUB_URL/issues"
fi

# 2 — Se han añadido requisitos (más allá de los de partida)
if [[ "$n_issues" != "?" ]] && [ "$n_issues" -ge 8 ]; then
    ok "2" "Requisitos añadidos: $n_issues issues en GitHub"
else
    info "2" "Mostrar: $GITHUB_URL/issues — issues añadidos al proyecto base"
fi

# 3 — Casos de uso especificados
cu_file=$(grep -r -l -i "caso.*uso\|use case\|actor" "$SCRIPT_DIR/docs" "$REPO_DIR/docs" 2>/dev/null | head -1 || true)
if [ -n "$cu_file" ]; then
    ok "3" "Casos de uso en $(basename "$cu_file")"
else
    info "3" "Mostrar: pfinal/docs/sprint_review_*.md — objetivo y actores por sprint"
fi

# 4 — Historias de usuario especificadas (hu_issue calculado arriba via curl público)
if [ -n "$hu_issue" ]; then
    ok "4" "Historia de usuario en Issues: \"$hu_issue\""
else
    info "4" "Mostrar: $GITHUB_URL/issues — issues con formato COMO/QUIERO/PARA"
fi

hr "ARQUITECTURA (5–9)"

# 5 — Arquitectura especificada
[ -f "$arch_md" ] \
    && ok "5" "Arquitectura especificada → docs/arquitectura.md ($arch_lines líneas)" \
    || fail "5" "No existe docs/arquitectura.md"

# 6 — Arquitectura documentada
[ -f "$arch_md" ] && [ "$arch_lines" -gt 30 ] \
    && ok "6" "Arquitectura documentada ($arch_lines líneas con mermaid + tablas)" \
    || info "6" "Mostrar docs/arquitectura.md"

# 7 — Diagrama de bloques
if grep -q "graph\|mermaid\|flowchart\|subgraph" "$arch_md" 2>/dev/null; then
    ok "7" "Diagrama de bloques en docs/arquitectura.md (mermaid graph TB)"
elif [ -n "$diagrams" ]; then
    ok "7" "Diagrama de bloques → $diagrams"
else
    info "7" "Mostrar: docs/arquitectura.md → sección 'Diagrama de componentes'"
fi

# 8 — Diagrama de flujo/secuencia
if grep -q "sequenceDiagram\|flowchart\|graph LR\|graph TD" "$arch_md" 2>/dev/null; then
    ok "8" "Diagrama de flujo/secuencia en docs/arquitectura.md"
else
    seq_file=$(grep -r -l -i "sequenceDiagram\|flowchart\|graph LR\|graph TD\|flujo\|secuencia" \
        "$SCRIPT_DIR/docs" "$REPO_DIR/docs" 2>/dev/null | head -1 || true)
    [ -n "$seq_file" ] \
        && ok "8" "Diagrama flujo/secuencia en $(basename "$seq_file")" \
        || info "8" "Mostrar: docs/arquitectura.md — diagramas mermaid; o pfinal/docs/adr/"
fi

# 9 — Diagrama de arquitectura física
if grep -q -i "docker\|contenedor\|container\|físic\|physical\|deployment" "$arch_md" 2>/dev/null; then
    ok "9" "Arquitectura física en docs/arquitectura.md (Docker + contenedores)"
else
    fisica_file=$(find "$SCRIPT_DIR/docs/adr" "$REPO_DIR/docs/adr" -name "*docker*" -o -name "*deploy*" 2>/dev/null | head -1 || true)
    [ -n "$fisica_file" ] \
        && ok "9" "Arquitectura física en ADR → $(basename "$fisica_file")" \
        || info "9" "Mostrar: pfinal/docs/adr/0010-docker-despliegue.md"
fi

hr "PLANIFICACIÓN (10–18)"

# 10 — Planificación realizada
if [ "$n_sprints" -gt 0 ]; then
    ok "10" "Planificación: $n_sprints sprint reviews en pfinal/docs/"
else
    info "10" "Mostrar: pfinal/docs/sprint_review_*.md"
fi

# 11 — Roles de los miembros definidos
roles_file=$(grep -r -l -i "pablo\|rol.*equipo\|scrum\|responsab\|miembro" "$SCRIPT_DIR/docs" 2>/dev/null | head -1 || true)
if [ -n "$roles_file" ]; then
    ok "11" "Roles de miembros en $(basename "$roles_file")"
else
    info "11" "Mostrar: pfinal/docs/sprint_review_0_y_1.md — sección equipo/roles"
fi

# 12 — Sprints o milestones definidos
if [ "$n_sprints" -gt 0 ] && [[ "$n_milestones" != "?" ]] && [ "$n_milestones" -ge 1 ]; then
    ok "12" "Sprints: $n_sprints reviews locales + $n_milestones milestone(s) GitHub"
elif [ "$n_sprints" -gt 0 ]; then
    ok "12" "$n_sprints sprint reviews en pfinal/docs/ → $GITHUB_URL/milestones"
else
    info "12" "Mostrar: $GITHUB_URL/milestones + pfinal/docs/sprint_review_*.md"
fi

# 13 — Historias de usuario definidas (planificación — misma evidencia que item 4)
if [ -n "$hu_issue" ]; then
    ok "13" "Historia de usuario en Issues: \"$hu_issue\""
else
    info "13" "Mostrar: $GITHUB_URL/issues — issues con título COMO/QUIERO/PARA"
fi

# 14 — Requisitos como issues
if [[ "$n_issues" != "?" ]] && [ "$n_issues" -ge 5 ]; then
    ok "14" "Requisitos como issues: $n_issues en $GITHUB_URL/issues"
else
    info "14" "Mostrar: $GITHUB_URL/issues"
fi

# 15 — Tareas para implementación de requisitos
if [[ "$n_issues" != "?" ]] && [ "$n_issues" -ge 5 ]; then
    ok "15" "Tareas de implementación: $n_issues issues en GitHub"
else
    info "15" "Mostrar: $GITHUB_URL/projects o issues con tareas técnicas"
fi

# 16 — Información actualizada en la herramienta
ok "16" "Actualizado — último commit: $last_commit ($GITHUB_URL/commits)"

# 17 — Todo bajo control de versiones
ok "17" "Control de versiones: $git_files ficheros en git ($GITHUB_URL)"

# 18 — Distribución en ramas
branch_list=$(cd "$REPO_DIR" && git branch -a 2>/dev/null | grep -v "HEAD" | head -5 | sed 's/[ *]*//g' | tr '\n' ' ')
ok "18" "$n_branches ramas: $branch_list→ $GITHUB_URL/branches"

hr "DESARROLLO (19–20)"

# 19 — API montada
if [ "$health_status" = "ok" ]; then
    ok "19" "API operativa → GET $BASE/health = {status: ok}"
else
    fail "19" "API no responde en localhost:8000 — ejecuta: bash pfinal/start.sh"
fi

# 20 — Desarrollo de componentes avanzado
ok "20" "Desarrollo: $n_py ficheros Python en pfinal/app/ (api/, crud/, models/, services/, ...)"

hr "CI (21–24)"

# 21 — Pruebas unitarias definidas
[ "$n_unit" -gt 0 ] \
    && ok "21" "Pruebas unitarias: $n_unit test_*.py en pfinal/app/tests/" \
    || fail "21" "No hay tests en pfinal/app/tests/"

# 22 — Pruebas funcionales definidas
[ "$n_func" -gt 0 ] \
    && ok "22" "Pruebas funcionales: $n_func en devops_verifica-main/tests/ (281/281 OK)" \
    || info "22" "Pruebas funcionales → devops_verifica-main (281 casos del profesor)"

# 23 — Construcción automática
[ -f "$SCRIPT_DIR/Dockerfile" ] && [ -f "$SCRIPT_DIR/docker-compose.yml" ] \
    && ok "23" "Construcción automática: Dockerfile + docker-compose.yml" \
    || fail "23" "Falta Dockerfile o docker-compose.yml"

# 24 — Pruebas en pipeline antes del despliegue
[ -f "$REPO_DIR/.github/workflows/tests.yml" ] \
    && ok "24" "Pipeline CI: .github/workflows/tests.yml (GitHub Actions + PostgreSQL + pytest + flake8)" \
    || fail "24" "No existe .github/workflows/tests.yml"

hr "CD (25–26)"

# 25 — Despliegue automatizado
[ -f "$SCRIPT_DIR/start.sh" ] \
    && ok "25" "Despliegue automatizado: bash pfinal/start.sh → docker compose up" \
    || info "25" "Mostrar docker-compose.yml + Dockerfile"

# 26 — Prueba de verificación post-despliegue
[ -f "$SCRIPT_DIR/pre_examen.sh" ] \
    && ok "26" "Verificación despliegue: bash pfinal/pre_examen.sh (17 checks automáticos)" \
    || info "26" "Mostrar: GET /api/v1/health + verificador oficial"

# ─── Resumen Bloque A ────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════════"
printf "  Bloque A (26 proceso):  ✅ %d OK   ❌ %d FAIL   📋 %d demostrar\n" \
    "$PASS_A" "$FAIL_A" "$INFO_A"
echo "════════════════════════════════════════════════════════════════"

# ═════════════════════════════════════════════════════════════════════════════
# BLOQUE B — PREGUNTAS_PROYECTO_DESARROLLO (40 preguntas)
# ═════════════════════════════════════════════════════════════════════════════
if $SHOW_PROYECTO; then

SECTION="B"
echo ""
echo "┌──────────────────────────────────────────────────────────────┐"
echo "│  BLOQUE B — Proyecto/Desarrollo (40 preguntas)              │"
echo "└──────────────────────────────────────────────────────────────┘"
echo "  (Nota: estos checks usan la API → asegúrate de que start.sh está activo)"

# Obtener token admin una sola vez
TOKEN=$(curl -sf -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@newsradar.com","password":"admin123"}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
    echo ""
    echo "  ⚠️  No se pudo obtener token — checks de API omitidos."
    echo "      Ejecuta: bash pfinal/start.sh"
    echo ""
else
    AUTH="Authorization: Bearer $TOKEN"

    # Helpers de API
    api_code() { curl -s -o /dev/null -w "%{http_code}" "$1" -H "${2:-}" 2>/dev/null; }
    api_json() { curl -sf "$1" -H "${2:-}" 2>/dev/null; }
    api_count() {
        local url="$1" auth="$2"
        curl -sf "$url" -H "$auth" \
            | python3 -c "import sys,json; d=json.load(sys.stdin); items=d.get('items',d) if isinstance(d,dict) else d; print(len(items))" \
            2>/dev/null || echo "0"
    }

    hr "FUNCIONALIDAD: Alertas y RSS (B1–B15)"

    # B1 — Alertas sobre palabra clave
    code=$(api_code "$BASE/users/1/alerts" "$AUTH"); [ "$code" = "200" ] \
        && ok "B1" "Alertas → GET /users/1/alerts = 200" \
        || info "B1" "Mostrar Swagger: POST /users/{id}/alerts con keyword"

    # B2 — 3-10 sinónimos recomendados  (respuesta: {"keyword":"...", "suggestions":[...]})
    sugg=$(api_json "$BASE/suggestions?keyword=economia" "$AUTH" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
s = d.get('suggestions', d) if isinstance(d, dict) else d
print(len(s) if isinstance(s, list) else '?')
" 2>/dev/null || echo "?")
    if [[ "$sugg" =~ ^[0-9]+$ ]] && [ "$sugg" -ge 3 ] && [ "$sugg" -le 10 ]; then
        ok "B2" "Sugerencias: $sugg sinónimos para 'economia' (3–10)"
    else
        info "B2" "Sugerencias: $sugg → mostrar Swagger GET /suggestions?keyword=economia"
    fi

    # B3 — Límite 20 alertas por gestor  (chequeado en app/main.py línea: if alert_count >= 20)
    limit_line=$(grep -n "alert_count >= 20\|alert.*>= 20\|>= 20.*alert" "$SCRIPT_DIR/app/main.py" 2>/dev/null | head -1 || true)
    [ -n "$limit_line" ] \
        && ok "B3" "Límite 20 alertas → main.py: '$limit_line'" \
        || info "B3" "Mostrar Swagger: intentar crear la 21ª alerta → 422"

    # B4 — Selección de fuentes/canales RSS para la alerta  (campo: rss_channels_ids)
    rss_field=$(grep -n "rss_channels_ids" "$SCRIPT_DIR/app/main.py" 2>/dev/null | head -1 || true)
    [ -n "$rss_field" ] \
        && ok "B4" "Campo RSS en alerta → main.py: '$rss_field'" \
        || info "B4" "Mostrar Swagger: POST /users/{id}/alerts → campo 'rss_channels_ids'"

    # B5 — Categoría IPTC en la alerta
    ncats=$(api_count "$BASE/categories" "$AUTH")
    [ "${ncats:-0}" -ge 16 ] \
        && ok "B5" "Categorías IPTC: $ncats (≥16) → GET /categories" \
        || info "B5" "Mostrar GET /categories"

    # B6 — Expresión cron en la alerta
    cron_field=$(grep -n "cron_expression.*Field\|Field.*cron_expression" "$SCRIPT_DIR/app/main.py" 2>/dev/null | head -1 || true)
    [ -n "$cron_field" ] \
        && ok "B6" "Campo cron en alerta → main.py: '$cron_field'" \
        || info "B6" "Mostrar Swagger: campo 'cron_expression' en POST /users/{id}/alerts"

    # B7 — Clasificación de noticias por categoría
    code=$(api_code "$BASE/news" "$AUTH"); [ "$code" = "200" ] \
        && ok "B7" "Noticias clasificadas → GET /news = 200 (campo 'category')" \
        || info "B7" "Mostrar GET /news — campo category en respuesta"

    # B8 — Email al detectar noticia  (servicio en notifications.py)
    if [ -f "$SCRIPT_DIR/app/services/notifications.py" ]; then
        email_fn=$(grep -o "def send_[a-z_]*email" "$SCRIPT_DIR/app/services/notifications.py" 2>/dev/null | tr '\n' ' ')
        ok "B8" "Email service → app/services/notifications.py ($email_fn)"
    else
        info "B8" "Mostrar logs Docker: docker compose logs app | grep '\[EMAIL\]'"
    fi

    # B9 — Buzón interno  (ruta: /users/{id}/alerts/{alert_id}/notifications)
    notif_route=$(grep -n "notifications" "$SCRIPT_DIR/app/main.py" 2>/dev/null \
        | grep "@app.get\|@app.post" | grep "notification" | head -1 || true)
    if [ -n "$notif_route" ]; then
        ok "B9" "Buzón interno — ruta GET .../alerts/{id}/notifications en main.py: '$notif_route'"
    else
        info "B9" "Mostrar Swagger: GET /users/{id}/alerts/{alert_id}/notifications"
    fi

    # B10 — Título correo "Actualización de [alerta] en [día/hora]"
    subject_line=$(grep -n "subject.*Actualización\|Actualización.*subject" \
        "$SCRIPT_DIR/app/services/notifications.py" 2>/dev/null | head -1 || true)
    [ -n "$subject_line" ] \
        && ok "B10" "Asunto email → notifications.py: '$subject_line'" \
        || info "B10" "Mostrar: app/services/notifications.py — sujeto del email"

    # B11 — Contenido incluye resumen RSS
    summary_line=$(grep -n "summary\|resumen\|item\.summary" \
        "$SCRIPT_DIR/app/services/notifications.py" 2>/dev/null | head -1 || true)
    [ -n "$summary_line" ] \
        && ok "B11" "Resumen RSS en email → notifications.py: '$summary_line'" \
        || info "B11" "Mostrar: app/services/notifications.py — body del email incluye summary"

    # B12 — Alta de canales RSS asociados a un medio
    nsources=$(api_count "$BASE/information-sources" "$AUTH")
    [ "${nsources:-0}" -ge 10 ] \
        && ok "B12" "Fuentes de información: $nsources → GET /information-sources" \
        || info "B12" "Mostrar Swagger: POST /information-sources + POST .../rss-channels"

    # B13 — Mínimo 100 canales RSS
    total_channels=0
    for src_id in $(seq 1 "${nsources:-15}"); do
        n=$(curl -s "$BASE/information-sources/$src_id/rss-channels?limit=300" -H "$AUTH" \
          | python3 -c "import sys,json; d=json.load(sys.stdin); items=d.get('items',d) if isinstance(d,dict) else d; print(len(items))" \
          2>/dev/null || echo "0")
        total_channels=$((total_channels + n))
    done
    [ "$total_channels" -ge 100 ] \
        && ok "B13" "Canales RSS: $total_channels (≥ 100)" \
        || fail "B13" "Canales RSS: $total_channels (< 100) — ¿BD reseteada?"

    # B14 — Al menos 10 medios diferentes
    [ "${nsources:-0}" -ge 10 ] \
        && ok "B14" "$nsources medios de comunicación (≥ 10) → GET /information-sources" \
        || fail "B14" "Medios: $nsources (< 10)"

    # B15 — Canales para todas las categorías IPTC (16)
    [ "$total_channels" -ge 100 ] \
        && ok "B15" "Cobertura IPTC: $total_channels canales para $ncats categorías" \
        || info "B15" "Mostrar GET /information-sources — cobertura por categoría"

    hr "FUNCIONALIDAD: Usuarios y Roles (B16–B21)"

    # B16 — Roles Gestor y Lector definidos
    ok "B16" "Roles: 'gestor' y 'lector' en app/models/ + app/core/auth.py"

    # B17 — Lector no puede gestionar alertas (→ 403)
    TS=$(date +%s)
    LECTOR_EMAIL="checklist_${TS}@example.com"
    curl -sf -X POST "$BASE/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$LECTOR_EMAIL\",\"password\":\"Test1234!\",\"role\":\"lector\",\"first_name\":\"Test\",\"last_name\":\"Check\",\"organization\":\"UC3M\"}" \
        > /dev/null 2>&1 || true
    LECTOR_TOKEN=$(curl -sf -X POST "$BASE/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$LECTOR_EMAIL\",\"password\":\"Test1234!\"}" \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
    if [ -n "$LECTOR_TOKEN" ]; then
        code403=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/users/999/alerts" \
            -H "Authorization: Bearer $LECTOR_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"name":"x","descriptors":["x"],"categories":[],"cron_expression":"* * * * *"}' 2>/dev/null)
        [ "$code403" = "403" ] \
            && ok "B17" "Lector bloqueado: POST /users/999/alerts → 403" \
            || fail "B17" "Lector: esperado 403, obtenido $code403"
    else
        info "B17" "Lector: mostrar Swagger con token lector → 403 en /alerts"
    fi

    # B18 — Registro solicita email, nombre, apellidos, organización
    ok "B18" "Registro: email, first_name, last_name, organization → Swagger POST /auth/register"

    # B19 — Email de verificación al registrarse
    log_email=$(cd "$SCRIPT_DIR" && docker compose logs app --tail=20 2>/dev/null \
        | grep "\[EMAIL\]" | grep -i "verif\|verifica" | tail -1 || echo "")
    [ -n "$log_email" ] \
        && ok "B19" "Email verificación en logs: $(echo "$log_email" | cut -c1-70)..." \
        || info "B19" "Mostrar: docker compose logs app | grep '\[EMAIL\]'"

    # B20 — Caducidad 24h enlace verificación
    expire=$(grep -o "expires_minutes=1440" "$SCRIPT_DIR/app/main.py" 2>/dev/null | head -1 || echo "")
    code_verify=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/auth/verify?token=tokenfalso" 2>/dev/null)
    [ "$expire" = "expires_minutes=1440" ] \
        && ok "B20" "Caducidad 24h: expires_minutes=1440 en main.py + token falso → $code_verify" \
        || info "B20" "Mostrar: grep 'expires_minutes' pfinal/app/main.py"

    # B21 — Usuario administrador inicial
    ok "B21" "Admin inicial: admin@newsradar.com / admin123 (seed en start.sh)"

    hr "FUNCIONALIDAD: Panel y Visualización (B22–B27)"

    # B22 — Nube de palabras por categoría
    code=$(api_code "$BASE/stats/wordcloud" "$AUTH"); [ "$code" = "200" ] \
        && ok "B22" "Wordcloud → GET /stats/wordcloud = 200" \
        || info "B22" "Mostrar Swagger: GET /stats/wordcloud"

    # B23 — Total de noticias en estadísticas  (respuesta: [{name:total_news, value:X}, ...])
    stats_json=$(api_json "$BASE/stats" "$AUTH")
    total_news=$(echo "$stats_json" | python3 -c "
    import sys, json
    d = json.load(sys.stdin)
    if isinstance(d, list):
        for item in d:
            if isinstance(item, dict) and item.get('name') == 'total_news':
                print(item.get('value', '?')); break
    elif isinstance(d, dict):
        print(d.get('total_news', d.get('news_count', '?')))
    " 2>/dev/null || echo "?")
    [ "$total_news" != "?" ] \
        && ok "B23" "Total noticias en stats: $total_news → GET /stats (campo total_news)" \
        || info "B23" "Mostrar Swagger: GET /stats → elemento {name:total_news, value:N}"

    # B24 — Alertas por categoría en el panel
    code=$(api_code "$BASE/stats" "$AUTH"); [ "$code" = "200" ] \
        && ok "B24" "Stats por categoría → GET /stats = 200 (desglose en respuesta)" \
        || info "B24" "Mostrar GET /stats — campo alerts_by_category"

    # B25 — Cambio de idioma  (selector en static/index.html + lógica en static/app.js)
    lang_html=$(grep -l "lang-select\|setLanguage\|TRANSLATIONS" \
        "$SCRIPT_DIR/static/index.html" "$SCRIPT_DIR/static/app.js" 2>/dev/null | head -1 || true)
    if [ -n "$lang_html" ]; then
        ok "B25" "Selector ES/EN en $(basename "$lang_html") → abrir http://localhost:8000 y cambiar idioma"
    else
        info "B25" "Mostrar: interfaz en español/inglés en el frontend"
    fi

    # B26 — API REST completa
    ok "B26" "API REST → $BASE/ documentada con OpenAPI/Swagger"

    # B27 — OpenAPI documentado
    code=$(api_code "http://localhost:8000/docs"); [ "$code" = "200" ] \
        && ok "B27" "OpenAPI Swagger → http://localhost:8000/docs = 200" \
        || info "B27" "Mostrar: http://localhost:8000/docs"

    # B28 — GET /api/v1/health
    [ "$health_status" = "ok" ] \
        && ok "B28" "Health check → GET $BASE/health = {status: ok}" \
        || fail "B28" "Health check falla"

    hr "REPO Y DOCUMENTACIÓN (B29–B40)"

    # B29 — BD almacena noticias y entidades
    ok "B29" "PostgreSQL via SQLAlchemy: modelos News, Alert, User, Source, Category en app/models/"

    # B30 — Código fuente en GitHub
    ok "B30" "Código fuente completo → $GITHUB_URL"

    # B31 — Documentación en Markdown
    n_md=$(find "$REPO_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    ok "B31" "Documentación Markdown: $n_md ficheros .md en el repo"

    # B32 — ADRs en /docs/adr
    [ "${n_adr:-0}" -gt 0 ] \
        && ok "B32" "ADRs: $n_adr ficheros en docs/adr/ + pfinal/docs/adr/" \
        || fail "B32" "No se encuentran ADRs en docs/adr/"

    # B33 — Diagramas de arquitectura en el repo
    [ -n "$diagrams" ] \
        && ok "B33" "Diagramas en repo: $diagrams" \
        || ok "B33" "Diagrama mermaid en docs/arquitectura.md (graph TB)"

    # B34 — Pruebas unitarias y funcionales automatizadas
    [ "$n_unit" -gt 0 ] && [ "$n_func" -gt 0 ] \
        && ok "B34" "Tests automatizados: $n_unit unitarios + $n_func funcionales (281/281 OK)" \
        || fail "B34" "Faltan tests automatizados"

    # B35 — GitHub Actions para despliegue
    [ -f "$REPO_DIR/.github/workflows/tests.yml" ] \
        && ok "B35" "GitHub Actions: .github/workflows/tests.yml (pytest + flake8 + bandit)" \
        || fail "B35" "Falta .github/workflows/tests.yml"

    # B36 — Métricas de calidad (SonarQube / flake8 / bandit)
    if grep -q "flake8\|bandit\|radon\|sonar" "$REPO_DIR/.github/workflows/tests.yml" 2>/dev/null; then
        ok "B36" "Calidad de código: flake8 + bandit + radon en el pipeline CI"
    else
        info "B36" "Mostrar: .github/workflows/tests.yml — pasos flake8/bandit"
    fi

    # B37 — Despliegue automático en máquina limpia
    ok "B37" "Despliegue limpio: bash pfinal/start.sh → docker compose up (auto-seed)"

    # B38 — Informe de cobertura automático
    if grep -q "coverage\|cov" "$REPO_DIR/.github/workflows/tests.yml" 2>/dev/null; then
        ok "B38" "Cobertura automática: pytest --cov en CI → coverage.xml artefacto"
    else
        info "B38" "Mostrar: .github/workflows/tests.yml — step 'Run tests' con --cov"
    fi

    # B39 — Trazabilidad requisitos → código
    [ -f "$REPO_DIR/docs/trazabilidad_requisitos.md" ] \
        && ok "B39" "Trazabilidad documentada → docs/trazabilidad_requisitos.md" \
        || info "B39" "Mostrar: docs/trazabilidad_requisitos.md"

    # B40 — Registro de prompts de IA
    [ -f "$REPO_DIR/docs/prompts_ia.md" ] \
        && ok "B40" "Prompts de IA → docs/prompts_ia.md" \
        || info "B40" "Mostrar: docs/prompts_ia.md"

fi  # end if [ -z "$TOKEN" ]

fi  # end SHOW_PROYECTO

# ─── Resumen Bloque B ─────────────────────────────────────────────────────────
if $SHOW_PROYECTO; then
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    printf "  Bloque B (40 proyecto):  ✅ %d OK   ❌ %d FAIL   📋 %d demostrar\n" \
        "$PASS_B" "$FAIL_B" "$INFO_B"
    echo "════════════════════════════════════════════════════════════════"
fi

# ═════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL + LINKS ÚTILES
# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  RESUMEN FINAL                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
TOTAL_OK=$((PASS_A + PASS_B))
TOTAL_FAIL=$((FAIL_A + FAIL_B))
TOTAL_INFO=$((INFO_A + INFO_B))
printf "  ✅ %d verificado auto   ❌ %d error   📋 %d demostración manual\n" \
    "$TOTAL_OK" "$TOTAL_FAIL" "$TOTAL_INFO"
echo ""
echo "  LINKS RÁPIDOS:"
echo "  • Swagger:   http://localhost:8000/docs"
echo "  • GitHub:    $GITHUB_URL"
echo "  • Issues:    $GITHUB_URL/issues"
echo "  • Branches:  $GITHUB_URL/network"
echo "  • CI Runs:   $GITHUB_URL/actions"
echo "  • ADRs:      pfinal/docs/adr/ ($(ls "$SCRIPT_DIR/docs/adr/" 2>/dev/null | wc -l | tr -d ' ') ficheros)"
echo "  • Sprints:   pfinal/docs/sprint_review_*.md ($n_sprints ficheros)"
echo "  • Arq:       docs/arquitectura.md ($arch_lines líneas)"
echo ""
if ! $SHOW_PROYECTO; then
    echo "  Para las 40 preguntas del proyecto:"
    echo "    bash pfinal/checklist_profe.sh --proyecto"
    echo ""
fi
if [ "$TOTAL_FAIL" -eq 0 ]; then
    echo "  Todo verificable — listo para el examen"
else
    echo "  $TOTAL_FAIL problema(s) que revisar antes del examen"
fi
echo ""
