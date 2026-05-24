from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome
from tests.test_data_loader import TestDataLoader

_DATA_FILE = Path(__file__).resolve().parent.parent / "test_data" / "st_case_data.json"


class StatsManagementScopeTests(BaseScopeTests):
    """Implements ST-* test cases for stats management."""

    VALIDATION_STATUSES = {400, 409, 422}
    NOT_FOUND_STATUSES = {400, 404, 422}

    def __init__(self, base_url: str, openapi_path: Optional[Path] = None, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.seed_email = "admin@newsradar.com"
        self.seed_password = "admin123"
        self.openapi_spec = self._load_openapi(openapi_path)
        self._loader = TestDataLoader(_DATA_FILE)

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        self._cleanup_reset()
        try:
            return self._run_case_impl(case)
        finally:
            self._cleanup_run()

    def _run_case_impl(self, case: Dict[str, str]) -> TestOutcome:
        case_id = str(case.get("Caso de Prueba", "")).strip().upper()

        if case_id == "ST-001":
            return self._case_st_001_create_valid(case)
        if case_id == "ST-002":
            return self._case_st_002_without_metrics(case)
        if case_id == "ST-003":
            return self._case_st_003_metrics_empty(case)
        if case_id == "ST-004":
            return self._case_st_004_metric_without_name(case)
        if case_id == "ST-005":
            return self._case_st_005_metric_without_value(case)
        if case_id == "ST-006":
            return self._case_st_006_metric_name_empty(case)
        if case_id == "ST-007":
            return self._case_st_007_metric_name_too_long(case)
        if case_id == "ST-008":
            return self._case_st_008_value_not_numeric(case)
        if case_id == "ST-009":
            return self._case_st_009_value_null(case)
        if case_id == "ST-010":
            return self._case_st_010_value_negative(case)
        if case_id == "ST-011":
            return self._case_st_011_value_decimal(case)
        if case_id == "ST-012":
            return self._case_st_012_value_extremely_large(case)
        if case_id == "ST-013":
            return self._case_st_013_multiple_metrics_valid(case)
        if case_id == "ST-014":
            return self._case_st_014_duplicate_metric_name(case)
        if case_id == "ST-015":
            return self._case_st_015_metric_name_whitespace(case)
        if case_id == "ST-016":
            return self._case_st_016_metric_name_special_chars(case)
        if case_id == "ST-017":
            return self._case_st_017_metric_payload_extra(case)
        if case_id == "ST-018":
            return self._case_st_018_metrics_not_array(case)
        if case_id == "ST-019":
            return self._case_st_019_metrics_with_empty_object(case)
        if case_id == "ST-020":
            return self._case_st_020_single_metric(case)
        if case_id == "ST-021":
            return self._case_st_021_get_existing(case)
        if case_id == "ST-022":
            return self._case_st_022_get_nonexistent(case)
        if case_id == "ST-023":
            return self._case_st_023_validate_id_type(case)
        if case_id == "ST-024":
            return self._case_st_024_update_valid(case)
        if case_id == "ST-025":
            return self._case_st_025_update_invalid_value(case)
        if case_id == "ST-026":
            return self._case_st_026_delete_existing(case)
        if case_id == "ST-027":
            return self._case_st_027_delete_nonexistent(case)
        if case_id == "ST-028":
            return self._case_st_028_utf8_name(case)
        if case_id == "ST-029":
            return self._case_st_029_response_schema(case)
        if case_id == "ST-030":
            return self._case_st_030_name_normalization(case)
        if case_id == "ST-031":
            return self._case_st_031_metrics_order_consistency(case)
        if case_id == "ST-032":
            return self._case_st_032_list_stats_consistency(case)

        return self.nok(case, f"Caso ST no implementado: {case_id}")

    def _case_st_001_create_valid(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-001"))
        if stats is None:
            return self.nok(case, detail)
        self._cleanup_stats(stats.get("id"))
        return self.ok(case, detail)

    def _case_st_002_without_metrics(self, case: Dict[str, str]) -> TestOutcome:
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/stats", body=self._valid_payload("ST-002"))
        if request_error is not None:
            return self.nok(case, f"Error creando stats sin metrics: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Sin metrics rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            self._cleanup_stats(response_body.get("id"))
            return self.ok(case, "El API permite crear stats sin metrics")
        return self.nok(case, f"Status inesperado sin metrics: {status_code}")

    def _case_st_003_metrics_empty(self, case: Dict[str, str]) -> TestOutcome:
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/stats", body=self._valid_payload("ST-003"))
        if request_error is not None:
            return self.nok(case, f"Error con metrics vacio: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"metrics vacio rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            self._cleanup_stats(response_body.get("id"))
            return self.ok(case, "El API acepta metrics vacio")
        return self.nok(case, f"Status inesperado con metrics vacio: {status_code}")

    def _case_st_004_metric_without_name(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-004")
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "metric sin name")

    def _case_st_005_metric_without_value(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-005")
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "metric sin value")

    def _case_st_006_metric_name_empty(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-006")
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name vacio en metric")

    def _case_st_007_metric_name_too_long(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-007")
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name longitud maxima")

    def _case_st_008_value_not_numeric(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-008")
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "value no numerico")

    def _case_st_009_value_null(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-009")
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "value null")

    def _case_st_010_value_negative(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-010")
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error con value negativo: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Value negativo rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            self._cleanup_stats(response_body.get("id"))
            return self.ok(case, "Value negativo aceptado por regla de negocio")
        return self.nok(case, f"Status inesperado para value negativo: {status_code}")

    def _case_st_011_value_decimal(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-011"))
        if stats is None:
            return self.nok(case, detail)
        self._cleanup_stats(stats.get("id"))
        return self.ok(case, detail)

    def _case_st_012_value_extremely_large(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-012")
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error con value muy alto: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Value muy alto rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            self._cleanup_stats(response_body.get("id"))
            return self.ok(case, "Value muy alto aceptado")
        return self.nok(case, f"Status inesperado para value muy alto: {status_code}")

    def _case_st_013_multiple_metrics_valid(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-013"))
        if stats is None:
            return self.nok(case, detail)
        self._cleanup_stats(stats.get("id"))
        return self.ok(case, detail)

    def _case_st_014_duplicate_metric_name(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-014")
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error con metric duplicado: {request_error}")
        if status_code in {400, 409, 422}:
            return self.ok(case, f"Metric duplicado rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            self._cleanup_stats(response_body.get("id"))
            return self.ok(case, "Metric duplicado aceptado/consolidado por el API")
        return self.nok(case, f"Status inesperado para metric duplicado: {status_code}")

    def _case_st_015_metric_name_whitespace(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-015")
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error con name whitespace: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Name whitespace rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                metrics = response_body.get("metrics", [])
                if isinstance(metrics, list) and metrics:
                    first_name = str(metrics[0].get("name", "")).strip() if isinstance(metrics[0], dict) else ""
                    if not first_name:
                        return self.nok(case, "Metric name con solo espacios fue persistido")
                return self.ok(case, "Name whitespace aceptado y normalizado")
            finally:
                self._cleanup_stats(response_body.get("id"))
        return self.nok(case, f"Status inesperado para name whitespace: {status_code}")

    def _case_st_016_metric_name_special_chars(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-016"))
        if stats is None:
            return self.nok(case, detail)
        self._cleanup_stats(stats.get("id"))
        return self.ok(case, detail)

    def _case_st_017_metric_payload_extra(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload("ST-017")
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error con payload extra en metric: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Payload extra rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                metrics = response_body.get("metrics", [])
                if isinstance(metrics, list) and metrics and isinstance(metrics[0], dict) and "extra" in metrics[0]:
                    return self.nok(case, "Campo extra en metric persistido")
                return self.ok(case, "Campo extra ignorado en metric")
            finally:
                self._cleanup_stats(response_body.get("id"))
        return self.nok(case, f"Status inesperado payload extra metric: {status_code}")

    def _case_st_018_metrics_not_array(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/stats", body=self._valid_payload("ST-018"))
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "metrics no array")

    def _case_st_019_metrics_with_empty_object(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/stats", body=self._valid_payload("ST-019"))
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "metrics con objeto vacio")

    def _case_st_020_single_metric(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-020"))
        if stats is None:
            return self.nok(case, detail)
        self._cleanup_stats(stats.get("id"))
        return self.ok(case, detail)

    def _case_st_021_get_existing(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-021"))
        if stats is None:
            return self.nok(case, detail)
        try:
            status_code, response_body, request_error = self._authorized_request("GET", f"/api/v1/stats/{stats['id']}", body=None)
            if request_error is not None:
                return self.nok(case, f"Error consultando stats: {request_error}")
            if status_code != 200:
                return self.nok(case, f"GET stats devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict) or response_body.get("id") != stats["id"]:
                return self.nok(case, f"Respuesta GET invalida: {response_body!r}")
            return self.ok(case, "Consulta de stats existente correcta")
        finally:
            self._cleanup_stats(stats.get("id"))

    def _case_st_022_get_nonexistent(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("GET", "/api/v1/stats/99999999", body=None)
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "get stats inexistente")

    def _case_st_023_validate_id_type(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-023"))
        if stats is None:
            return self.nok(case, detail)
        try:
            if not isinstance(stats.get("id"), int):
                return self.nok(case, f"id no es entero: {stats.get('id')!r}")
            return self.ok(case, "id entero validado")
        finally:
            self._cleanup_stats(stats.get("id"))

    def _case_st_024_update_valid(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-024"))
        if stats is None:
            return self.nok(case, detail)
        try:
            update_payload = self._case_data_payload("ST-024", "update_payload")
            status_code, response_body, request_error = self._authorized_request(
                "PUT", f"/api/v1/stats/{stats['id']}", body=update_payload
            )
            if request_error is not None:
                return self.nok(case, f"Error actualizando stats: {request_error}")
            if status_code != 200:
                return self.nok(case, f"Update stats devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict):
                return self.nok(case, f"Respuesta update invalida: {response_body!r}")
            metrics = response_body.get("metrics", [])
            if not isinstance(metrics, list) or not metrics:
                return self.nok(case, f"Metrics no devuelto tras update: {response_body!r}")
            return self.ok(case, "Stats actualizado correctamente")
        finally:
            self._cleanup_stats(stats.get("id"))

    def _case_st_025_update_invalid_value(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-025"))
        if stats is None:
            return self.nok(case, detail)
        try:
            payload = self._case_data_payload("ST-025", "update_payload")
            status_code, _, request_error = self._authorized_request("PUT", f"/api/v1/stats/{stats['id']}", body=payload)
            return self._expect_statuses(case, status_code, request_error, {400, 422}, "update value inválido")
        finally:
            self._cleanup_stats(stats.get("id"))

    def _case_st_026_delete_existing(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-026"))
        if stats is None:
            return self.nok(case, detail)
        status_code, _, request_error = self._authorized_request("DELETE", f"/api/v1/stats/{stats['id']}", body=None)
        if request_error is not None:
            return self.nok(case, f"Error eliminando stats: {request_error}")
        if status_code != 204:
            self._cleanup_stats(stats.get("id"))
            return self.nok(case, f"Delete stats devolvió {status_code}, esperado 204")
        return self.ok(case, "Stats eliminado correctamente")

    def _case_st_027_delete_nonexistent(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("DELETE", "/api/v1/stats/99999999", body=None)
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "delete stats inexistente")

    def _case_st_028_utf8_name(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-028"))
        if stats is None:
            return self.nok(case, detail)
        self._cleanup_stats(stats.get("id"))
        return self.ok(case, detail)

    def _case_st_029_response_schema(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-029"))
        if stats is None:
            return self.nok(case, detail)
        try:
            schema = self._get_openapi_stats_schema()
            if not schema:
                return self.nok(case, "No se pudo resolver components.schemas.Stats en OpenAPI")

            properties = schema.get("properties", {})
            if not isinstance(properties, dict) or not properties:
                return self.nok(case, "Schema Stats sin properties validas")

            allowed_keys = set(properties.keys())
            required_keys = set(schema.get("required", [])) if isinstance(schema.get("required"), list) else set()
            actual_keys = set(stats.keys())

            missing_required = sorted(required_keys - actual_keys)
            unexpected = sorted(actual_keys - allowed_keys)
            if missing_required:
                return self.nok(case, f"Faltan campos requeridos por OpenAPI: {missing_required}")
            if unexpected:
                return self.nok(case, f"Campos inesperados fuera de OpenAPI: {unexpected}")

            type_errors: List[str] = []
            for key in sorted(actual_keys & allowed_keys):
                if not self._matches_openapi_type(stats.get(key), properties.get(key, {})):
                    expected_type = self._describe_openapi_type(properties.get(key, {}))
                    actual_type = type(stats.get(key)).__name__
                    type_errors.append(f"{key}: esperado {expected_type}, obtenido {actual_type}")
            if type_errors:
                return self.nok(case, "Tipos incompatibles con OpenAPI: " + "; ".join(type_errors))

            return self.ok(case, "ST-029 válido: respuesta alineada al schema Stats de OpenAPI")
        finally:
            self._cleanup_stats(stats.get("id"))

    def _case_st_030_name_normalization(self, case: Dict[str, str]) -> TestOutcome:
        stats, detail = self._create_stats(self._valid_payload("ST-030"))
        if stats is None:
            return self.nok(case, detail)
        try:
            status_code, response_body, request_error = self._authorized_request("GET", f"/api/v1/stats/{stats['id']}", body=None)
            if request_error is not None:
                return self.nok(case, f"Error verificando normalizacion: {request_error}")
            if status_code != 200 or not isinstance(response_body, dict):
                return self.nok(case, f"No se pudo verificar normalizacion: {status_code} {response_body!r}")
            metrics = response_body.get("metrics", [])
            if not isinstance(metrics, list) or not metrics:
                return self.nok(case, "No hay metrics para verificar normalizacion")
            metric_name = str(metrics[0].get("name", "")).strip() if isinstance(metrics[0], dict) else ""
            if not metric_name:
                return self.nok(case, "Name de metric vacio tras almacenamiento")
            return self.ok(case, f"Normalizacion consistente, metric name='{metric_name}'")
        finally:
            self._cleanup_stats(stats.get("id"))

    def _case_st_031_metrics_order_consistency(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._case_data_payload("ST-031", "initial_payload")
        stats, detail = self._create_stats(payload)
        if stats is None:
            return self.nok(case, detail)
        try:
            reversed_payload = self._case_data_payload("ST-031", "update_payload")
            update_status, _, update_error = self._authorized_request("PUT", f"/api/v1/stats/{stats['id']}", body=reversed_payload)
            if update_error is not None:
                return self.nok(case, f"Error actualizando orden de metrics: {update_error}")
            if update_status != 200:
                return self.nok(case, f"Update orden metrics devolvió {update_status}, esperado 200")

            get_status, get_body, get_error = self._authorized_request("GET", f"/api/v1/stats/{stats['id']}", body=None)
            if get_error is not None:
                return self.nok(case, f"Error verificando orden metrics: {get_error}")
            if get_status != 200 or not isinstance(get_body, dict):
                return self.nok(case, f"GET tras update orden devolvió {get_status} {get_body!r}")
            metrics = get_body.get("metrics", [])
            if not isinstance(metrics, list):
                return self.nok(case, f"Metrics no es lista tras update: {metrics!r}")
            names = [str(m.get("name")) for m in metrics if isinstance(m, dict)]
            if set(names) != {"a", "b"}:
                return self.nok(case, f"Inconsistencia logica en metrics: names={names!r}")
            return self.ok(case, "Orden de metrics no altero la consistencia logica")
        finally:
            self._cleanup_stats(stats.get("id"))

    def _case_st_032_list_stats_consistency(self, case: Dict[str, str]) -> TestOutcome:
        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/stats", body=None)
        if request_error is not None:
            return self.nok(case, f"Error listando stats: {request_error}")
        if status_code != 200:
            return self.nok(case, f"List stats devolvió {status_code}, esperado 200")
        if not isinstance(response_body, list):
            return self.nok(case, f"List stats no devolvió lista JSON: {response_body!r}")
        for item in response_body:
            if not isinstance(item, dict):
                return self.nok(case, f"Elemento de stats no es objeto: {item!r}")
            if "id" not in item or not isinstance(item.get("id"), int):
                return self.nok(case, f"Elemento de stats sin id entero: {item!r}")
        return self.ok(case, f"Listado de stats consistente con {len(response_body)} elementos")

    def _valid_payload(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        payload = self._json_clone(self._loader.get_default("create_stats_payload", {}))
        if case_id is None:
            return payload

        case_data = self._loader.get_case_data(case_id)
        for field in case_data.get("remove_fields", []):
            payload.pop(field, None)

        overrides = case_data.get("overrides", {})
        if isinstance(overrides, dict):
            payload.update(self._json_clone(overrides))
        return payload

    def _case_data_payload(self, case_id: str, field_name: str) -> Dict[str, Any]:
        case_data = self._loader.get_case_data(case_id)
        payload = case_data.get(field_name, {})
        return self._json_clone(payload if isinstance(payload, dict) else {})

    def _create_stats(self, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/stats", body=payload)
        if request_error is not None:
            return None, f"Error creando stats: {request_error}"
        if status_code != 201:
            return None, f"Crear stats devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear stats no devolvió objeto JSON: {response_body!r}"
        self._cleanup_register(self._cleanup_stats, response_body.get("id"))
        return response_body, f"Stats creado correctamente con id {response_body.get('id')}"

    def _cleanup_stats(self, stats_id: Any) -> None:
        if stats_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/stats/{stats_id}", body=None)
        except Exception:
            return

    @staticmethod
    def _load_openapi(openapi_path: Optional[Path]) -> Dict[str, Any]:
        if openapi_path is None:
            return {}
        try:
            with openapi_path.open("r", encoding="utf-8") as file_handle:
                loaded = json.load(file_handle)
                return loaded if isinstance(loaded, dict) else {}
        except Exception:
            return {}

    def _get_openapi_stats_schema(self) -> Dict[str, Any]:
        components = self.openapi_spec.get("components", {}) if isinstance(self.openapi_spec, dict) else {}
        schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
        stats_schema = schemas.get("Stats", {}) if isinstance(schemas, dict) else {}
        return stats_schema if isinstance(stats_schema, dict) else {}

    @staticmethod
    def _matches_openapi_type(value: Any, schema: Dict[str, Any]) -> bool:
        if not isinstance(schema, dict):
            return True

        if "anyOf" in schema and isinstance(schema.get("anyOf"), list):
            return any(
                StatsManagementScopeTests._matches_openapi_type(value, option)
                for option in schema.get("anyOf", [])
                if isinstance(option, dict)
            )

        schema_type = schema.get("type")
        if schema_type is None:
            return True
        if schema_type == "string":
            return isinstance(value, str)
        if schema_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if schema_type == "number":
            return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
        if schema_type == "boolean":
            return isinstance(value, bool)
        if schema_type == "array":
            return isinstance(value, list)
        if schema_type == "object":
            return isinstance(value, dict)
        if schema_type == "null":
            return value is None
        return True

    @staticmethod
    def _describe_openapi_type(schema: Dict[str, Any]) -> str:
        if not isinstance(schema, dict):
            return "desconocido"
        if "anyOf" in schema and isinstance(schema.get("anyOf"), list):
            variants = [
                str(option.get("type", "any"))
                for option in schema.get("anyOf", [])
                if isinstance(option, dict)
            ]
            return "|".join(variants) if variants else "any"
        return str(schema.get("type", "any"))

    def _login_seed_user(self) -> Tuple[Optional[str], Optional[str]]:
        payload = {"email": self.seed_email, "password": self.seed_password}
        status_code, response_body, request_error = self._request("POST", "/api/v1/auth/login", body=payload)
        if request_error is not None:
            return None, f"Error en login con usuario semilla: {request_error}"
        if status_code != 200:
            return None, f"Login semilla devolvió {status_code}, esperado 200"
        if not isinstance(response_body, dict):
            return None, f"Login semilla no devolvió JSON objeto: {response_body!r}"
        token = response_body.get("access_token")
        if not isinstance(token, str) or not token.strip():
            return None, f"Login semilla no devolvió access_token válido: {response_body!r}"
        return token.strip(), None

    def _authorized_request(
        self,
        method: str,
        path: str,
        body: Optional[Any],
    ) -> Tuple[int, Any, Optional[str]]:
        token, login_error = self._login_seed_user()
        if login_error is not None:
            return -1, None, login_error
        status_code, response_body, request_error = self._request(
            method,
            path,
            body=body,
            extra_headers={"Authorization": f"Bearer {token}"},
        )
        if (
            request_error is None
            and method.upper() == "POST"
            and path == "/api/v1/stats"
            and status_code == 201
            and isinstance(response_body, dict)
        ):
            self._cleanup_register(self._cleanup_stats, response_body.get("id"))
        return status_code, response_body, request_error

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Any],
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any, Optional[str]]:
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if extra_headers:
            headers.update(extra_headers)

        data: Optional[bytes] = None
        if body is not None and method.upper() in {"POST", "PUT", "PATCH"}:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, method=method.upper(), data=data, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                status_code = int(response.status)
                raw = response.read().decode("utf-8", errors="replace")
                return status_code, self._parse_json(raw), None
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            return int(exc.code), self._parse_json(raw), None
        except Exception as exc:  # pragma: no cover
            return -1, None, str(exc)

    def _expect_statuses(
        self,
        case: Dict[str, str],
        status_code: int,
        request_error: Optional[str],
        expected_statuses: set,
        context: str,
    ) -> TestOutcome:
        if request_error is not None:
            return self.nok(case, f"Error en {context}: {request_error}")
        if status_code not in expected_statuses:
            expected = ", ".join(str(item) for item in sorted(expected_statuses))
            return self.nok(case, f"{context}: status {status_code}, esperado uno de {{{expected}}}")
        return self.ok(case, f"{context}: status {status_code} dentro de lo esperado")

    @staticmethod
    def _parse_json(raw: str) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    @staticmethod
    def _json_clone(value: Any) -> Any:
        return json.loads(json.dumps(value))