from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome
from tests.test_data_loader import TestDataLoader

_DATA_FILE = Path(__file__).resolve().parent.parent / "test_data" / "gn_case_data.json"


class NotificationManagementScopeTests(BaseScopeTests):
    """Implements GN-* test cases for notification management."""

    VALIDATION_STATUSES: Set[int] = {400, 409, 422}
    NOT_FOUND_STATUSES: Set[int] = {400, 404, 422}

    def __init__(self, base_url: str, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.seed_email = "admin@newsradar.com"
        self.seed_password = "admin123"
        self._loader = TestDataLoader(_DATA_FILE)

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        self._cleanup_reset()
        try:
            return self._run_case_impl(case)
        finally:
            self._cleanup_run()

    def _run_case_impl(self, case: Dict[str, str]) -> TestOutcome:
        case_id = str(case.get("Caso de Prueba", "")).strip().upper()

        handlers = {
            "GN-001": self._case_gn_001_create_valid_notification,
            "GN-002": self._case_gn_002_create_without_timestamp,
            "GN-003": self._case_gn_003_create_empty_timestamp,
            "GN-004": self._case_gn_004_create_invalid_timestamp,
            "GN-005": self._case_gn_005_create_valid_iso_timestamp,
            "GN-006": self._case_gn_006_create_future_timestamp,
            "GN-007": self._case_gn_007_create_old_timestamp,
            "GN-008": self._case_gn_008_create_without_metrics,
            "GN-009": self._case_gn_009_create_empty_metrics,
            "GN-010": self._case_gn_010_create_metrics_not_array,
            "GN-011": self._case_gn_011_create_metric_without_name,
            "GN-012": self._case_gn_012_create_metric_without_value,
            "GN-013": self._case_gn_013_create_metric_empty_name,
            "GN-014": self._case_gn_014_create_metric_name_too_long,
            "GN-015": self._case_gn_015_create_metric_non_numeric_value,
            "GN-016": self._case_gn_016_create_metric_null_value,
            "GN-017": self._case_gn_017_create_metric_negative_value,
            "GN-018": self._case_gn_018_create_metric_decimal_value,
            "GN-019": self._case_gn_019_create_multiple_valid_metrics,
            "GN-020": self._case_gn_020_create_duplicate_metric_name,
            "GN-021": self._case_gn_021_create_metric_name_with_spaces,
            "GN-022": self._case_gn_022_create_metric_special_chars,
            "GN-023": self._case_gn_023_create_metric_with_extra_payload,
            "GN-024": self._case_gn_024_create_with_nonexistent_alert,
            "GN-025": self._case_gn_025_create_with_nonexistent_user,
            "GN-026": self._case_gn_026_user_alert_mismatch,
            "GN-027": self._case_gn_027_create_for_valid_alert,
            "GN-028": self._case_gn_028_list_for_valid_alert,
            "GN-029": self._case_gn_029_list_nonexistent_alert,
            "GN-030": self._case_gn_030_list_nonexistent_user,
            "GN-031": self._case_gn_031_validate_id_integer,
            "GN-032": self._case_gn_032_validate_alert_id_in_response,
            "GN-033": self._case_gn_033_validate_chronological_order,
            "GN-034": self._case_gn_034_duplicate_exact_notification,
            "GN-035": self._case_gn_035_metric_name_normalization,
            "GN-036": self._case_gn_036_utf8_metric_name,
            "GN-037": self._case_gn_037_response_schema_validation,
            "GN-038": self._case_gn_038_timezone_consistency,
            "GN-039": self._case_gn_039_metrics_empty_object,
            "GN-040": self._case_gn_040_metrics_mixed_valid_invalid,
        }

        handler = handlers.get(case_id)
        if handler is None:
            return self.nok(case, f"Caso GN no implementado: {case_id}")
        return handler(case)

    def _case_gn_001_create_valid_notification(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-001", {201}, "crear notification valida")

    def _case_gn_002_create_without_timestamp(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-002", self.VALIDATION_STATUSES, "crear notification sin timestamp", created_warning=True)

    def _case_gn_003_create_empty_timestamp(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-003", self.VALIDATION_STATUSES, "crear notification con timestamp vacio", created_warning=True)

    def _case_gn_004_create_invalid_timestamp(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-004", self.VALIDATION_STATUSES, "crear notification con timestamp inválido", created_warning=True)

    def _case_gn_005_create_valid_iso_timestamp(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-005", {201}, "crear notification con timestamp ISO8601")

    def _case_gn_006_create_future_timestamp(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-006", {201, 400, 422}, "crear notification con timestamp futuro")

    def _case_gn_007_create_old_timestamp(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-007", {201, 400, 422}, "crear notification con timestamp antiguo")

    def _case_gn_008_create_without_metrics(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-008", {201}, "crear notification sin metrics")

    def _case_gn_009_create_empty_metrics(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-009", {201}, "crear notification con metrics vacio")

    def _case_gn_010_create_metrics_not_array(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-010", self.VALIDATION_STATUSES, "crear notification con metrics no array")

    def _case_gn_011_create_metric_without_name(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-011", self.VALIDATION_STATUSES, "crear metric sin name")

    def _case_gn_012_create_metric_without_value(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-012", self.VALIDATION_STATUSES, "crear metric sin value")

    def _case_gn_013_create_metric_empty_name(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-013", self.VALIDATION_STATUSES, "crear metric con name vacio")

    def _case_gn_014_create_metric_name_too_long(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-014", self.VALIDATION_STATUSES, "crear metric con name > 100")

    def _case_gn_015_create_metric_non_numeric_value(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-015", self.VALIDATION_STATUSES, "crear metric con value no numerico")

    def _case_gn_016_create_metric_null_value(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-016", self.VALIDATION_STATUSES, "crear metric con value null")

    def _case_gn_017_create_metric_negative_value(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-017", {201, 400, 422}, "crear metric con value negativo")

    def _case_gn_018_create_metric_decimal_value(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-018", {201}, "crear metric con value decimal")

    def _case_gn_019_create_multiple_valid_metrics(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-019", {201}, "crear notification con multiples metrics")

    def _case_gn_020_create_duplicate_metric_name(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-020", {201, 409, 422}, "crear notification con metric duplicado")

    def _case_gn_021_create_metric_name_with_spaces(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-021", {201, 400, 422}, "crear notification con metric con espacios")

    def _case_gn_022_create_metric_special_chars(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-022", {201}, "crear notification con metric UTF-8")

    def _case_gn_023_create_metric_with_extra_payload(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-023", {201, 400, 422}, "crear notification con metric con payload extra")

    def _case_gn_024_create_with_nonexistent_alert(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = self._build_notification_payload("GN-024")
            status_code, _, req_error = self._authorized_request(
                "POST",
                f"/api/v1/users/{user['id']}/alerts/99999999/notifications",
                body=payload,
            )
            return self._expect_statuses(case, status_code, req_error, self.NOT_FOUND_STATUSES, "crear notification con alert inexistente")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_gn_025_create_with_nonexistent_user(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_notification_payload("GN-025")
        status_code, _, req_error = self._authorized_request(
            "POST",
            "/api/v1/users/99999999/alerts/99999999/notifications",
            body=payload,
        )
        return self._expect_statuses(case, status_code, req_error, self.NOT_FOUND_STATUSES, "crear notification con user inexistente")

    def _case_gn_026_user_alert_mismatch(self, case: Dict[str, str]) -> TestOutcome:
        user_a, detail_a = self._create_test_user()
        if user_a is None:
            return self.nok(case, detail_a)
        user_b, detail_b = self._create_test_user()
        if user_b is None:
            self._cleanup_user(user_a.get("id"))
            return self.nok(case, detail_b)

        alert_a, alert_detail = self._create_test_alert(user_a["id"])
        if alert_a is None:
            self._cleanup_user(user_a.get("id"))
            self._cleanup_user(user_b.get("id"))
            return self.nok(case, alert_detail)

        try:
            payload = self._build_notification_payload("GN-026")
            status_code, _, req_error = self._authorized_request(
                "POST",
                f"/api/v1/users/{user_b['id']}/alerts/{alert_a['id']}/notifications",
                body=payload,
            )
            return self._expect_statuses(case, status_code, req_error, self.NOT_FOUND_STATUSES | {403}, "desajuste user_id vs alert_id")
        finally:
            self._cleanup_alert(user_a["id"], alert_a.get("id"))
            self._cleanup_user(user_a.get("id"))
            self._cleanup_user(user_b.get("id"))

    def _case_gn_027_create_for_valid_alert(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-027", {201}, "crear notification para alerta valida")

    def _case_gn_028_list_for_valid_alert(self, case: Dict[str, str]) -> TestOutcome:
        user, alert, notification_ids, setup_error = self._setup_context()
        if setup_error is not None:
            return self.nok(case, setup_error)
        try:
            status_code, body, req_error = self._create_notification(
                user["id"], alert["id"], self._build_notification_payload("GN-027")
            )
            if req_error is not None or status_code != 201 or not isinstance(body, dict):
                return self.nok(case, f"No se pudo crear notification para el listado. status={status_code}, error={req_error}, body={body!r}")
            notification_ids.append(body.get("id"))

            list_status, list_body, list_error = self._list_notifications(user["id"], alert["id"])
            if list_error is not None:
                return self.nok(case, f"Error listando notifications: {list_error}")
            if list_status != 200:
                return self.nok(case, f"List notifications devolvió {list_status}, esperado 200")
            if not isinstance(list_body, list):
                return self.nok(case, f"List notifications no devolvió array: {list_body!r}")
            return self.ok(case, f"List notifications correcto con {len(list_body)} elemento(s)")
        finally:
            self._cleanup_notifications(user["id"], alert["id"], notification_ids)
            self._cleanup_alert(user["id"], alert.get("id"))
            self._cleanup_user(user.get("id"))

    def _case_gn_029_list_nonexistent_alert(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            status_code, _, req_error = self._list_notifications(user["id"], 99999999)
            return self._expect_statuses(case, status_code, req_error, self.NOT_FOUND_STATUSES, "listar notifications con alert inexistente")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_gn_030_list_nonexistent_user(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, req_error = self._list_notifications(99999999, 99999999)
        return self._expect_statuses(case, status_code, req_error, self.NOT_FOUND_STATUSES, "listar notifications con user inexistente")

    def _case_gn_031_validate_id_integer(self, case: Dict[str, str]) -> TestOutcome:
        user, alert, notification_ids, setup_error = self._setup_context()
        if setup_error is not None:
            return self.nok(case, setup_error)
        try:
            status_code, body, req_error = self._create_notification(
                user["id"], alert["id"], self._build_notification_payload("GN-027")
            )
            if req_error is not None or status_code != 201 or not isinstance(body, dict):
                return self.nok(case, f"No se pudo crear notification para validar id. status={status_code}, error={req_error}, body={body!r}")
            notification_ids.append(body.get("id"))
            if not isinstance(body.get("id"), int):
                return self.nok(case, f"id no es entero: {body.get('id')!r}")
            return self.ok(case, f"id de notification es entero: {body.get('id')}")
        finally:
            self._cleanup_notifications(user["id"], alert["id"], notification_ids)
            self._cleanup_alert(user["id"], alert.get("id"))
            self._cleanup_user(user.get("id"))

    def _case_gn_032_validate_alert_id_in_response(self, case: Dict[str, str]) -> TestOutcome:
        user, alert, notification_ids, setup_error = self._setup_context()
        if setup_error is not None:
            return self.nok(case, setup_error)
        try:
            status_code, body, req_error = self._create_notification(
                user["id"], alert["id"], self._build_notification_payload("GN-027")
            )
            if req_error is not None or status_code != 201 or not isinstance(body, dict):
                return self.nok(case, f"No se pudo crear notification para validar alert_id. status={status_code}, error={req_error}, body={body!r}")
            notification_ids.append(body.get("id"))
            if body.get("alert_id") != alert["id"]:
                return self.nok(case, f"alert_id en respuesta ({body.get('alert_id')!r}) no coincide con path ({alert['id']})")
            return self.ok(case, "alert_id en response coincide con el path")
        finally:
            self._cleanup_notifications(user["id"], alert["id"], notification_ids)
            self._cleanup_alert(user["id"], alert.get("id"))
            self._cleanup_user(user.get("id"))

    def _case_gn_033_validate_chronological_order(self, case: Dict[str, str]) -> TestOutcome:
        user, alert, notification_ids, setup_error = self._setup_context()
        if setup_error is not None:
            return self.nok(case, setup_error)
        timestamps = ["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "2026-01-03T00:00:00Z"]
        try:
            for timestamp in timestamps:
                payload = self._build_notification_payload("GN-027")
                payload["timestamp"] = timestamp
                status_code, body, req_error = self._create_notification(user["id"], alert["id"], payload)
                if req_error is not None or status_code != 201 or not isinstance(body, dict):
                    return self.nok(case, f"No se pudo crear dataset cronologico. status={status_code}, error={req_error}, body={body!r}")
                notification_ids.append(body.get("id"))

            list_status, list_body, list_error = self._list_notifications(user["id"], alert["id"])
            if list_error is not None:
                return self.nok(case, f"Error listando notifications: {list_error}")
            if list_status != 200 or not isinstance(list_body, list):
                return self.nok(case, f"List notifications inválido: status={list_status} body={list_body!r}")

            parsed: List[datetime] = []
            for item in list_body:
                if not isinstance(item, dict):
                    continue
                if item.get("id") not in notification_ids:
                    continue
                timestamp_value = self._parse_timestamp(item.get("timestamp"))
                if timestamp_value is not None:
                    parsed.append(timestamp_value)

            if len(parsed) < 2:
                return self.warning(case, "No hay suficientes timestamps parseables para validar orden cronologico")

            asc = all(parsed[index] <= parsed[index + 1] for index in range(len(parsed) - 1))
            desc = all(parsed[index] >= parsed[index + 1] for index in range(len(parsed) - 1))
            if asc or desc:
                return self.ok(case, "Orden cronologico consistente")
            return self.nok(case, "Listado no mantiene orden cronologico consistente")
        finally:
            self._cleanup_notifications(user["id"], alert["id"], notification_ids)
            self._cleanup_alert(user["id"], alert.get("id"))
            self._cleanup_user(user.get("id"))

    def _case_gn_034_duplicate_exact_notification(self, case: Dict[str, str]) -> TestOutcome:
        user, alert, notification_ids, setup_error = self._setup_context()
        if setup_error is not None:
            return self.nok(case, setup_error)
        try:
            payload = self._build_notification_payload("GN-034")
            first_status, first_body, first_error = self._create_notification(user["id"], alert["id"], payload)
            if first_error is not None or first_status != 201 or not isinstance(first_body, dict):
                return self.nok(case, f"No se pudo crear notification base. status={first_status}, error={first_error}, body={first_body!r}")
            notification_ids.append(first_body.get("id"))

            second_status, second_body, second_error = self._create_notification(user["id"], alert["id"], payload)
            if second_error is not None:
                return self.nok(case, f"Error creando notification duplicada: {second_error}")
            if second_status in {400, 409, 422}:
                return self.ok(case, f"Duplicado exacto rechazado con status {second_status}")
            if second_status == 201:
                if isinstance(second_body, dict):
                    notification_ids.append(second_body.get("id"))
                return self.warning(case, "API permite notifications duplicadas exactas")
            return self.nok(case, f"Status inesperado para duplicado exacto: {second_status}")
        finally:
            self._cleanup_notifications(user["id"], alert["id"], notification_ids)
            self._cleanup_alert(user["id"], alert.get("id"))
            self._cleanup_user(user.get("id"))

    def _case_gn_035_metric_name_normalization(self, case: Dict[str, str]) -> TestOutcome:
        user, alert, notification_ids, setup_error = self._setup_context()
        if setup_error is not None:
            return self.nok(case, setup_error)
        try:
            first_payload = {
                "timestamp": "2026-05-01T00:00:00Z",
                "metrics": [{"name": "  SCORE  ", "value": 1}],
            }
            second_payload = {
                "timestamp": "2026-05-01T00:01:00Z",
                "metrics": [{"name": "score", "value": 2}],
            }

            first_status, first_body, first_error = self._create_notification(user["id"], alert["id"], first_payload)
            if first_error is not None or first_status != 201 or not isinstance(first_body, dict):
                return self.nok(case, f"No se pudo crear primer notification. status={first_status}, error={first_error}, body={first_body!r}")
            notification_ids.append(first_body.get("id"))

            second_status, second_body, second_error = self._create_notification(user["id"], alert["id"], second_payload)
            if second_error is not None:
                return self.nok(case, f"Error creando segundo notification: {second_error}")
            if second_status in {400, 409, 422}:
                return self.ok(case, f"API aplica normalización o control de duplicado (status {second_status})")
            if second_status == 201:
                if isinstance(second_body, dict):
                    notification_ids.append(second_body.get("id"))
                return self.warning(case, "API trata metric names con distinto case/espacios como distintos")
            return self.nok(case, f"Status inesperado en normalización: {second_status}")
        finally:
            self._cleanup_notifications(user["id"], alert["id"], notification_ids)
            self._cleanup_alert(user["id"], alert.get("id"))
            self._cleanup_user(user.get("id"))

    def _case_gn_036_utf8_metric_name(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-036", {201}, "crear notification con metric UTF-8")

    def _case_gn_037_response_schema_validation(self, case: Dict[str, str]) -> TestOutcome:
        user, alert, notification_ids, setup_error = self._setup_context()
        if setup_error is not None:
            return self.nok(case, setup_error)
        try:
            status_code, body, req_error = self._create_notification(
                user["id"], alert["id"], self._build_notification_payload("GN-027")
            )
            if req_error is not None or status_code != 201 or not isinstance(body, dict):
                return self.nok(case, f"No se pudo crear notification para validar schema. status={status_code}, error={req_error}, body={body!r}")
            notification_ids.append(body.get("id"))

            required_fields = {"id", "alert_id", "timestamp"}
            missing = required_fields - set(body.keys())
            if missing:
                return self.nok(case, f"Schema inválido. Faltan campos: {missing!r}")
            if not isinstance(body.get("id"), int):
                return self.nok(case, f"id no es entero: {body.get('id')!r}")
            if not isinstance(body.get("alert_id"), int):
                return self.nok(case, f"alert_id no es entero: {body.get('alert_id')!r}")
            if not isinstance(body.get("timestamp"), str):
                return self.nok(case, f"timestamp no es string: {body.get('timestamp')!r}")
            if "metrics" in body and not isinstance(body.get("metrics"), list):
                return self.nok(case, f"metrics no es array: {body.get('metrics')!r}")
            return self.ok(case, "Schema response de notification cumple contrato")
        finally:
            self._cleanup_notifications(user["id"], alert["id"], notification_ids)
            self._cleanup_alert(user["id"], alert.get("id"))
            self._cleanup_user(user.get("id"))

    def _case_gn_038_timezone_consistency(self, case: Dict[str, str]) -> TestOutcome:
        user, alert, notification_ids, setup_error = self._setup_context()
        if setup_error is not None:
            return self.nok(case, setup_error)
        try:
            payload = self._build_notification_payload("GN-038")
            status_code, body, req_error = self._create_notification(user["id"], alert["id"], payload)
            if req_error is not None or status_code != 201 or not isinstance(body, dict):
                return self.nok(case, f"No se pudo crear notification con timezone. status={status_code}, error={req_error}, body={body!r}")
            notification_ids.append(body.get("id"))

            timestamp_value = self._parse_timestamp(body.get("timestamp"))
            if timestamp_value is None:
                return self.nok(case, f"timestamp response no parseable: {body.get('timestamp')!r}")
            return self.ok(case, "Timestamp con zona horaria aceptado y parseable")
        finally:
            self._cleanup_notifications(user["id"], alert["id"], notification_ids)
            self._cleanup_alert(user["id"], alert.get("id"))
            self._cleanup_user(user.get("id"))

    def _case_gn_039_metrics_empty_object(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-039", self.VALIDATION_STATUSES, "crear notification con metric vacio")

    def _case_gn_040_metrics_mixed_valid_invalid(self, case: Dict[str, str]) -> TestOutcome:
        return self._run_create_case(case, "GN-040", self.VALIDATION_STATUSES, "crear notification con metrics mixtos")

    def _run_create_case(
        self,
        case: Dict[str, str],
        case_id: str,
        expected_statuses: Set[int],
        context: str,
        created_warning: bool = False,
    ) -> TestOutcome:
        user, alert, notification_ids, setup_error = self._setup_context()
        if setup_error is not None:
            return self.nok(case, setup_error)

        try:
            status_code, body, req_error = self._create_notification(
                user["id"], alert["id"], self._build_notification_payload(case_id)
            )
            if req_error is not None:
                return self.nok(case, f"Error en {context}: {req_error}")
            if status_code in expected_statuses:
                if status_code == 201 and isinstance(body, dict):
                    notification_ids.append(body.get("id"))
                return self.ok(case, f"{context}: status {status_code} dentro de lo esperado")
            if created_warning and status_code == 201:
                if isinstance(body, dict):
                    notification_ids.append(body.get("id"))
                return self.warning(case, f"{context}: API permitio el payload cuando se esperaba validacion")
            return self.nok(case, f"{context}: status {status_code}, esperado uno de {sorted(expected_statuses)}")
        finally:
            self._cleanup_notifications(user["id"], alert["id"], notification_ids)
            self._cleanup_alert(user["id"], alert.get("id"))
            self._cleanup_user(user.get("id"))

    def _setup_context(self) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[Any], Optional[str]]:
        user, user_detail = self._create_test_user()
        if user is None:
            return None, None, [], user_detail
        alert, alert_detail = self._create_test_alert(user["id"])
        if alert is None:
            self._cleanup_user(user.get("id"))
            return None, None, [], alert_detail
        return user, alert, [], None

    def _create_test_user(self) -> Tuple[Optional[Dict[str, Any]], str]:
        payload = {
            "email": self._unique_email(),
            "first_name": "Notification",
            "last_name": "Tester",
            "organization": "QA",
            "password": "Valid123",
            "role_ids": [],
        }
        status_code, body, req_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if req_error is not None:
            return None, f"Error creando usuario de prueba: {req_error}"
        if status_code != 201 or not isinstance(body, dict):
            return None, f"Crear usuario devolvió {status_code}, esperado 201. Respuesta: {body!r}"
        self._cleanup_register(self._cleanup_user, body.get("id"))
        return body, f"Usuario de prueba creado con id {body.get('id')}"

    def _create_test_alert(self, user_id: int) -> Tuple[Optional[Dict[str, Any]], str]:
        payload = {
            "name": self._unique_alert_name(),
            "cron_expression": "0 9 * * 1-5",
        }
        status_code, body, req_error = self._authorized_request(
            "POST",
            f"/api/v1/users/{user_id}/alerts",
            body=payload,
        )
        if req_error is not None:
            return None, f"Error creando alerta de prueba: {req_error}"
        if status_code != 201 or not isinstance(body, dict):
            return None, f"Crear alerta devolvió {status_code}, esperado 201. Respuesta: {body!r}"
        self._cleanup_register(self._cleanup_alert, user_id, body.get("id"))
        return body, f"Alerta de prueba creada con id {body.get('id')}"

    def _create_notification(self, user_id: int, alert_id: int, payload: Dict[str, Any]) -> Tuple[int, Any, Optional[str]]:
        status_code, body, req_error = self._authorized_request(
            "POST",
            f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications",
            body=payload,
        )
        if req_error is None and status_code == 201 and isinstance(body, dict):
            self._cleanup_register(self._cleanup_notification, user_id, alert_id, body.get("id"))
        return status_code, body, req_error

    def _list_notifications(self, user_id: int, alert_id: int) -> Tuple[int, Any, Optional[str]]:
        return self._authorized_request(
            "GET",
            f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications",
            body=None,
        )

    def _cleanup_notifications(self, user_id: Any, alert_id: Any, notification_ids: List[Any]) -> None:
        if user_id in (None, "") or alert_id in (None, ""):
            return
        for notification_id in notification_ids:
            self._cleanup_notification(user_id, alert_id, notification_id)

    def _cleanup_notification(self, user_id: Any, alert_id: Any, notification_id: Any) -> None:
        if user_id in (None, "") or alert_id in (None, "") or notification_id in (None, ""):
            return
        try:
            self._authorized_request(
                "DELETE",
                f"/api/v1/users/{user_id}/alerts/{alert_id}/notifications/{notification_id}",
                body=None,
            )
        except Exception:
            return

    def _cleanup_alert(self, user_id: Any, alert_id: Any) -> None:
        if user_id in (None, "") or alert_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/users/{user_id}/alerts/{alert_id}", body=None)
        except Exception:
            return

    def _cleanup_user(self, user_id: Any) -> None:
        if user_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/users/{user_id}", body=None)
        except Exception:
            return

    def _build_notification_payload(self, case_id: str) -> Dict[str, Any]:
        default_payload = self._loader.get_default("create_notification_payload", {})
        payload = self._deep_copy(default_payload if isinstance(default_payload, dict) else {})
        case_data = self._loader.get_case_data(case_id)
        overrides = case_data.get("overrides") if isinstance(case_data, dict) else None
        if isinstance(overrides, dict):
            payload.update(self._deep_copy(overrides))
        remove_fields = case_data.get("remove_fields") if isinstance(case_data, dict) else None
        if isinstance(remove_fields, list):
            for field_name in remove_fields:
                if isinstance(field_name, str):
                    payload.pop(field_name, None)
        return payload

    def _login_seed_user(self) -> Tuple[Optional[str], Optional[str]]:
        payload = {"email": self.seed_email, "password": self.seed_password}
        status_code, body, req_error = self._request("POST", "/api/v1/auth/login", body=payload)
        if req_error is not None:
            return None, f"Error en login semilla: {req_error}"
        if status_code != 200 or not isinstance(body, dict):
            return None, f"Login semilla fallo con status {status_code}"
        token = body.get("access_token")
        if not token:
            return None, f"Login semilla no devolvió access_token válido: {body!r}"
        return str(token).strip(), None

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
        if request_error is None and method.upper() == "POST" and status_code == 201 and isinstance(response_body, dict):
            path_parts = [part for part in path.split("/") if part]
            if path == "/api/v1/users":
                self._cleanup_register(self._cleanup_user, response_body.get("id"))
            elif len(path_parts) == 5 and path_parts[:4] == ["api", "v1", "users", path_parts[3]] and path_parts[4] == "alerts":
                self._cleanup_register(self._cleanup_alert, path_parts[3], response_body.get("id"))
            elif len(path_parts) == 7 and path_parts[:3] == ["api", "v1", "users"] and path_parts[4] == "alerts" and path_parts[6] == "notifications":
                self._cleanup_register(self._cleanup_notification, path_parts[3], path_parts[5], response_body.get("id"))
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
        except Exception as exc:
            return -1, None, str(exc)

    def _expect_statuses(
        self,
        case: Dict[str, str],
        status_code: int,
        request_error: Optional[str],
        expected_statuses: Set[int],
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
        if not raw.strip():
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return raw

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
        if not isinstance(value, str) or not value:
            return None
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    @staticmethod
    def _deep_copy(value: Any) -> Any:
        return json.loads(json.dumps(value))

    @staticmethod
    def _unique_email() -> str:
        unique = uuid.uuid4().hex[:12]
        return f"gn.{unique}@example.com"

    @staticmethod
    def _unique_alert_name() -> str:
        unique = uuid.uuid4().hex[:8]
        return f"GN-Alert-{unique}"
