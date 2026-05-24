#!/usr/bin/env bash
# script_correo_4.sh — Verificación de los requisitos del correo 4 del profesor
#
# El correo confirma:
#   1. Los 281 tests deben ejecutarse EN VIVO con versión "limpia descargada"
#   2. La verificación manual (M1-M5) también se hará en el momento
#   3. La entrega en AulaGlobal debe ser un zip ejecutable (git archive)
#
# Este script comprueba que todo está listo para el día del examen (25/05/2026).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE="http://localhost:8000/api/v1"
ZIP_OUTPUT="$REPO_ROOT/../newsradar_entrega.zip"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; }

echo "════════════════════════════════════════"
echo "  Correo 4 — Checklist examen 25/05/2026"
echo "════════════════════════════════════════"
echo ""

# ── 1. Comprobar que NewsRadar responde ──────────────────────────────────────
echo "── [1/5] NewsRadar responde ──"
STATUS=$(curl -sf "$BASE/health" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
if [ "$STATUS" = "ok" ]; then
    ok "http://localhost:8000 responde (status=ok)"
else
    fail "NewsRadar no responde. Ejecuta: bash pfinal/start.sh"
    exit 1
fi
echo ""

# ── 2. Comprobar scripts M1-M5 presentes ────────────────────────────────────
echo "── [2/5] Scripts de inspección manual M1-M5 ──"
ALL_OK=true
for i in 1 2 3 4 5; do
    case $i in
        1) f="m1_email_notificacion.sh" ;;
        2) f="m2_formato_asunto.sh" ;;
        3) f="m3_registro_verificacion.sh" ;;
        4) f="m4_expiracion_24h.sh" ;;
        5) f="m5_mock_rss.sh" ;;
    esac
    if [ -f "$SCRIPT_DIR/$f" ]; then
        ok "M$i → $f"
    else
        fail "M$i → $f NO ENCONTRADO"
        ALL_OK=false
    fi
done
$ALL_OK || exit 1
echo ""

# ── 3. Comprobar start.sh y run_verifier.sh ──────────────────────────────────
echo "── [3/5] Scripts de arranque y verificador ──"
for f in start.sh run_verifier.sh stop.sh; do
    if [ -f "$SCRIPT_DIR/$f" ]; then
        ok "$f presente"
    else
        fail "$f NO ENCONTRADO"
        exit 1
    fi
done
echo ""

# ── 4. Generar zip para AulaGlobal ──────────────────────────────────────────
echo "── [4/5] Generando zip para AulaGlobal ──"
cd "$REPO_ROOT"
git archive --format=zip --output="$ZIP_OUTPUT" HEAD 2>/dev/null

# Inyectar .env (excluido por .gitignore pero necesario para arrancar)
if [ -f "$SCRIPT_DIR/.env" ]; then
    python3 -c "
import zipfile, os
zip_path = '$ZIP_OUTPUT'
env_path = '$SCRIPT_DIR/.env'
with zipfile.ZipFile(zip_path, 'a') as z:
    z.write(env_path, 'pfinal/.env')
print('  .env añadido al zip')
"
else
    warn ".env no encontrado en pfinal/ — el zip no incluirá variables de entorno"
fi

ZIP_SIZE=$(du -sh "$ZIP_OUTPUT" 2>/dev/null | cut -f1)
ok "newsradar_entrega.zip generado — tamaño: $ZIP_SIZE"
echo "   Ruta: $ZIP_OUTPUT"
echo ""
echo "   Contenido (primeras 20 entradas):"
python3 -c "
import zipfile, sys
with zipfile.ZipFile('$ZIP_OUTPUT') as z:
    names = z.namelist()
    for n in names[:20]:
        print('   ', n)
    if len(names) > 20:
        print(f'   ... y {len(names)-20} archivos más ({len(names)} total)')
"
echo ""

# ── 5. Recordatorio procedimiento día del examen ────────────────────────────
echo "── [5/5] Procedimiento el 25/05/2026 (10:00) ──"
echo ""
echo "   PASO 1 — Arranque limpio (obligatorio antes de cada pasada):"
echo "     bash pfinal/start.sh"
echo ""
echo "   PASO 2 — 281 tests en vivo:"
echo "     bash pfinal/run_verifier.sh --all"
echo "     → Resultado esperado: OK: 281 (100%) en ~12 min"
echo ""
echo "   PASO 3 — Inspección manual M1-M5 (en otra terminal):"
echo "     bash pfinal/m1_email_notificacion.sh"
echo "     bash pfinal/m2_formato_asunto.sh"
echo "     bash pfinal/m3_registro_verificacion.sh"
echo "     bash pfinal/m4_expiracion_24h.sh"
echo "     bash pfinal/m5_mock_rss.sh    # requiere mock en otra terminal"
echo ""
echo "   PASO 4 — Subir zip a AulaGlobal:"
echo "     $ZIP_OUTPUT"
echo ""

ok "Todo listo para el examen"
echo ""
echo "════════════════════════════════════════"