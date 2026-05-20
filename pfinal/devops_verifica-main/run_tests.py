from __future__ import annotations

import argparse
import csv
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from tests.scope_base import TestOutcome
from tests.test_gu_scope import UserManagementScopeTests
from tests.test_gr_scope import RoleManagementScopeTests
from tests.test_gc_scope import CategoryManagementScopeTests
from tests.test_is_scope import InformationSourceManagementScopeTests
from tests.test_rss_scope import RSSChannelManagementScopeTests
from tests.test_st_scope import StatsManagementScopeTests
from tests.test_api_scope import APIScopeTests
from tests.test_ga_scope import AlertManagementScopeTests
from tests.test_gn_scope import NotificationManagementScopeTests
from tests.test_smoke_scope import SystemInitializationSmokeTests


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_CASES_FILE = ROOT_DIR / "test_data" / "casos_prueba.csv"
DEFAULT_OPENAPI_FILE = ROOT_DIR / "newsradar_openapi.json"
DEFAULT_OUTPUT_FILE = ROOT_DIR / "output" / "resultado_pruebas.csv"
EXPECTED_HEADERS = ["Caso de Prueba", "Título", "Ámbito", "Comprobación", "Flujo"]


def load_test_cases(cases_file: Path) -> List[Dict[str, str]]:
    with cases_file.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = [row for row in reader if any(str(cell).strip() for cell in row)]

    if not rows:
        return []

    first_row_normalized = [str(cell).strip() for cell in rows[0]]
    has_header = len(first_row_normalized) >= len(EXPECTED_HEADERS) and all(
        first_row_normalized[idx] == EXPECTED_HEADERS[idx] for idx in range(len(EXPECTED_HEADERS))
    )

    data_rows = rows[1:] if has_header else rows

    cases: List[Dict[str, str]] = []
    for row in data_rows:
        normalized = [str(cell).strip() for cell in row]
        case_id = normalized[0] if len(normalized) > 0 else ""
        
        # Ignorar casos comentados (ID comienza con #)
        if case_id.startswith("#"):
            continue
        
        case = {
            "Caso de Prueba": case_id,
            "Título": normalized[1] if len(normalized) > 1 else "",
            "Ámbito": normalized[2] if len(normalized) > 2 else "",
            "Comprobación": normalized[3] if len(normalized) > 3 else "",
            "Flujo": normalized[4] if len(normalized) > 4 else "",
        }
        cases.append(case)
    return cases


def group_cases_by_scope(cases: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    groups: Dict[str, List[Dict[str, str]]] = {}
    for case in cases:
        scope = (case.get("Ámbito") or "").strip()
        groups.setdefault(scope, []).append(case)
    return groups


def build_report_explanation(case: Dict[str, str]) -> str:
    title = (case.get("Título") or "").strip()
    check = (case.get("Comprobación") or "").strip()
    flow = (case.get("Flujo") or "").strip()
    return " | ".join(part for part in (title, check, flow) if part)


def extract_api_code(detail: str) -> str:
    if not detail:
        return ""

    patterns = [
        r"\bstatus\s+(-?\d{1,3})\b",
        r"\bdevolvi[oó]\s+(-?\d{1,3})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, detail, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def write_results_csv(output_file: Path, outcomes: List[TestOutcome], cases: List[Dict[str, str]]) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cases_by_id = {str(case.get("Caso de Prueba", "")).strip(): case for case in cases}

    with output_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ID Caso de Prueba", "Estado", "Código API", "Explicación", "Detalle"],
        )
        writer.writeheader()
        for outcome in outcomes:
            source_case = cases_by_id.get(str(outcome.case_id).strip(), {})
            report_status = "WARNING" if outcome.detail.startswith("WARNING:") else outcome.status
            writer.writerow(
                {
                    "ID Caso de Prueba": outcome.case_id,
                    "Estado": report_status,
                    "Código API": extract_api_code(outcome.detail),
                    "Explicación": build_report_explanation(source_case),
                    "Detalle": outcome.detail,
                }
            )


def build_timestamped_output_file(base_output_file: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = base_output_file.suffix or ".csv"
    stem = base_output_file.stem
    return base_output_file.with_name(f"{stem}_{timestamp}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta la suite de pruebas de NewsRadar")
    parser.add_argument(
        "--service",
        default=None,
        help="URL base del servicio NewsRadar (sobrescribe NEWSRADAR_BASE_URL)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ejecuta todas las pruebas, incluyendo el resto aunque falle la fase SMOKE",
    )
    args = parser.parse_args()

    base_url = args.service or os.getenv("NEWSRADAR_BASE_URL", "http://localhost:8000")
    cases_file = Path(os.getenv("TEST_CASES_FILE", str(DEFAULT_CASES_FILE))).resolve()
    openapi_file = Path(os.getenv("OPENAPI_FILE", str(DEFAULT_OPENAPI_FILE))).resolve()
    configured_output_file = Path(os.getenv("TEST_OUTPUT_FILE", str(DEFAULT_OUTPUT_FILE))).resolve()
    output_file = build_timestamped_output_file(configured_output_file)

    print("=== EJECUCION DE PRUEBAS NEWSRADAR ===")
    print(f"Base URL: {base_url}")
    print(f"Casos: {cases_file}")
    print(f"OpenAPI: {openapi_file}")
    print(f"Modo ALL: {'SI' if args.all else 'NO'}")

    if not cases_file.exists():
        print(f"ERROR: no existe el fichero de casos: {cases_file}")
        return 2

    if not openapi_file.exists():
        print(f"ERROR: no existe el OpenAPI: {openapi_file}")
        return 2

    cases = load_test_cases(cases_file)

    outcomes: List[TestOutcome] = []

    api_suite = APIScopeTests(base_url=base_url, openapi_path=openapi_file)
    gu_suite = UserManagementScopeTests(base_url=base_url)
    gr_suite = RoleManagementScopeTests(base_url=base_url)
    gc_suite = CategoryManagementScopeTests(base_url=base_url, openapi_path=openapi_file)
    is_suite = InformationSourceManagementScopeTests(base_url=base_url, openapi_path=openapi_file)
    rss_suite = RSSChannelManagementScopeTests(base_url=base_url, openapi_path=openapi_file)
    st_suite = StatsManagementScopeTests(base_url=base_url, openapi_path=openapi_file)
    ga_suite = AlertManagementScopeTests(base_url=base_url)
    gn_suite = NotificationManagementScopeTests(base_url=base_url)
    smoke_suite = SystemInitializationSmokeTests(base_url=base_url)

    # Primary routing by CSV scope (ambito). Prefix fallback below keeps compatibility.
    suite_by_scope = {
        "API": api_suite,
        "Gestión de Usuarios": gu_suite,
        "Gestión de Roles": gr_suite,
        "Gestión de Categorías": gc_suite,
        "Gestión de Fuentes de Información": is_suite,
        "Gestión de RSS Channels": rss_suite,
        "Gestión de Stats": st_suite,
        "Gestión de Alertas": ga_suite,
        "Gestión Alertas": ga_suite,
        "Gestión de Notificaciones": gn_suite,
        "Inicialización del Sistema": smoke_suite,
    }

    def execute_case(case: Dict[str, str]) -> TestOutcome:
        case_id = str(case.get("Caso de Prueba", "")).strip().upper()
        scope = (case.get("Ámbito") or "").strip()

        suite = suite_by_scope.get(scope)

        if suite is None:
            if case_id.startswith("API-"):
                suite = api_suite
            elif case_id.startswith("GU-"):
                suite = gu_suite
            elif case_id.startswith("GR-"):
                suite = gr_suite
            elif case_id.startswith("GC-"):
                suite = gc_suite
            elif case_id.startswith("IS-"):
                suite = is_suite
            elif case_id.startswith("RSS-"):
                suite = rss_suite
            elif case_id.startswith("ST-"):
                suite = st_suite
            elif case_id.startswith("GA-") or case_id.startswith("RN-"):
                suite = ga_suite
            elif case_id.startswith("GN-"):
                suite = gn_suite
            elif case_id.startswith("SMOKE-"):
                suite = smoke_suite

        if suite is not None:
            try:
                return suite.run_case(case)
            except Exception as e:
                return TestOutcome(
                    case_id=case.get("Caso de Prueba", ""),
                    status="NOK",
                    explanation=case.get("Comprobación", ""),
                    detail=f"Excepción no controlada durante ejecución: {type(e).__name__}: {str(e)}",
                )

        return TestOutcome(
            case_id=case.get("Caso de Prueba", ""),
            status="NOK",
            explanation=case.get("Comprobación", ""),
            detail=f"No hay implementacion para el caso '{case_id or scope}'",
        )

    smoke_cases = [
        case for case in cases if str(case.get("Caso de Prueba", "")).strip().upper().startswith("SMOKE-")
    ]
    non_smoke_cases = [
        case for case in cases if not str(case.get("Caso de Prueba", "")).strip().upper().startswith("SMOKE-")
    ]

    print(f"\n-- Fase SMOKE ({len(smoke_cases)} casos)")
    for case in smoke_cases:
        try:
            outcome = execute_case(case)
            outcomes.append(outcome)
            print(
                f"Caso {outcome.case_id}: {outcome.status} | "
                f"Explicación: {outcome.explanation} | Detalle: {outcome.detail}"
            )
        except Exception as e:
            case_id = case.get("Caso de Prueba", "")
            print(f"Caso {case_id}: ERROR | Excepción no controlada: {type(e).__name__}: {str(e)}")
            outcome = TestOutcome(
                case_id=case_id,
                status="NOK",
                explanation=case.get("Comprobación", ""),
                detail=f"Excepción no controlada en execute_case: {type(e).__name__}: {str(e)}",
            )
            outcomes.append(outcome)

    smoke_nok = sum(
        1
        for outcome in outcomes
        if str(outcome.case_id).strip().upper().startswith("SMOKE-") and outcome.status == "NOK"
    )
    if smoke_nok > 0:
        print(
            f"\nSe detectaron {smoke_nok} fallo(s) en fase SMOKE. "
            "No se ejecutan el resto de pruebas."
        )
        if args.all:
            print("Se continua con el resto de pruebas por --all")

    if smoke_nok == 0 or args.all:
        grouped = group_cases_by_scope(non_smoke_cases)
        for scope, scope_cases in grouped.items():
            print(f"\n-- Ambito: {scope} ({len(scope_cases)} casos)")
            for case in scope_cases:
                try:
                    outcome = execute_case(case)
                    outcomes.append(outcome)
                    print(
                        f"Caso {outcome.case_id}: {outcome.status} | "
                        f"Explicación: {outcome.explanation} | Detalle: {outcome.detail}"
                    )
                except Exception as e:
                    case_id = case.get("Caso de Prueba", "")
                    print(f"Caso {case_id}: ERROR | Excepción no controlada: {type(e).__name__}: {str(e)}")
                    outcome = TestOutcome(
                        case_id=case_id,
                        status="NOK",
                        explanation=case.get("Comprobación", ""),
                        detail=f"Excepción no controlada en execute_case: {type(e).__name__}: {str(e)}",
                    )
                    outcomes.append(outcome)

    write_results_csv(output_file, outcomes, cases)

    total_warnings = sum(1 for r in outcomes if r.detail.startswith("WARNING:"))
    total_ok = sum(1 for r in outcomes if r.status == "OK" and not r.detail.startswith("WARNING:"))
    total_nok = sum(1 for r in outcomes if r.status == "NOK")
    total_cases = len(outcomes)

    ok_pct = (total_ok / total_cases * 100.0) if total_cases else 0.0
    warning_pct = (total_warnings / total_cases * 100.0) if total_cases else 0.0
    nok_pct = (total_nok / total_cases * 100.0) if total_cases else 0.0

    execution_status = "OK" if total_nok == 0 else "NOK"

    print("\n=== RESUMEN ===")
    print(f"Total casos: {total_cases}")
    print(f"OK: {total_ok} ({ok_pct:.2f}%)")
    print(f"WARNING: {total_warnings} ({warning_pct:.2f}%)")
    print(f"NOK: {total_nok} ({nok_pct:.2f}%)")
    print(f"Resultado de la ejecucion: {execution_status}")
    print(f"CSV salida: {output_file}")

    return 0 if total_nok == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
