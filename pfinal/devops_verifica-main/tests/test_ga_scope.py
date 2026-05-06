from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome
from tests.test_data_loader import TestDataLoader

_DATA_FILE = Path(__file__).resolve().parent.parent / "test_data" / "ga_case_data.json"


class AlertManagementScopeTests(BaseScopeTests):
    """Implements GA-* test cases for alert management."""

    VALIDATION_STATUSES = {400, 409, 422}
    NOT_FOUND_STATUSES = {400, 404, 422}

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

        if case_id == "GA-001":
            return self._case_ga_001_create_valid_alert_complete(case)
        if case_id == "GA-002":
            return self._case_ga_002_create_alert_without_name(case)
        if case_id == "GA-003":
            return self._case_ga_003_create_alert_without_cron(case)
        if case_id == "GA-004":
            return self._case_ga_004_create_alert_empty_name(case)
        if case_id == "GA-005":
            return self._case_ga_005_create_alert_name_too_long(case)
        if case_id == "GA-006":
            return self._case_ga_006_create_alert_empty_cron(case)
        if case_id == "GA-007":
            return self._case_ga_007_create_alert_invalid_cron(case)
        if case_id == "GA-008":
            return self._case_ga_008_create_alert_valid_cron(case)
        if case_id == "GA-009":
            return self._case_ga_009_create_alert_without_descriptors(case)
        if case_id == "GA-010":
            return self._case_ga_010_create_alert_empty_descriptor(case)
        if case_id == "GA-011":
            return self._case_ga_011_create_alert_duplicate_descriptor(case)
        if case_id == "GA-012":
            return self._case_ga_012_create_alert_special_chars_descriptor(case)
        if case_id == "GA-013":
            return self._case_ga_013_create_alert_without_categories(case)
        if case_id == "GA-014":
            return self._case_ga_014_create_alert_invalid_category(case)
        if case_id == "GA-015":
            return self._case_ga_015_create_alert_inconsistent_category(case)
        if case_id == "GA-016":
            return self._case_ga_016_create_alert_multiple_categories(case)
        if case_id == "GA-017":
            return self._case_ga_017_create_alert_duplicate_category(case)
        if case_id == "GA-018":
            return self._case_ga_018_create_alert_without_rss_channels(case)
        if case_id == "GA-019":
            return self._case_ga_019_create_alert_without_information_sources(case)
        if case_id == "GA-020":
            return self._case_ga_020_create_alert_invalid_rss_channel(case)
        if case_id == "GA-021":
            return self._case_ga_021_create_alert_invalid_information_source(case)
        if case_id == "GA-022":
            return self._case_ga_022_create_alert_no_sources_no_rss(case)
        if case_id == "GA-023":
            return self._case_ga_023_create_alert_with_valid_sources(case)
        if case_id == "GA-024":
            return self._case_ga_024_create_alert_duplicate_rss_channel(case)
        if case_id == "GA-025":
            return self._case_ga_025_create_alert_duplicate_information_source(case)
        if case_id == "GA-026":
            return self._case_ga_026_mismatched_user_id(case)
        if case_id == "GA-027":
            return self._case_ga_027_create_alert_nonexistent_user(case)
        if case_id == "GA-028":
            return self._case_ga_028_create_duplicate_alert_same_user(case)
        if case_id == "GA-029":
            return self._case_ga_029_same_name_different_user(case)
        if case_id == "GA-030":
            return self._case_ga_030_name_normalization(case)
        if case_id == "GA-031":
            return self._case_ga_031_extra_fields_in_payload(case)
        if case_id == "GA-032":
            return self._case_ga_032_get_existing_alert(case)
        if case_id == "GA-033":
            return self._case_ga_033_get_nonexistent_alert(case)
        if case_id == "GA-034":
            return self._case_ga_034_validate_id_integer(case)
        if case_id == "GA-035":
            return self._case_ga_035_validate_user_id_in_response(case)
        if case_id == "GA-036":
            return self._case_ga_036_update_alert_valid(case)
        if case_id == "GA-037":
            return self._case_ga_037_update_alert_invalid_cron(case)
        if case_id == "GA-038":
            return self._case_ga_038_update_alert_invalid_categories(case)
        if case_id == "GA-039":
            return self._case_ga_039_delete_existing_alert(case)
        if case_id == "GA-040":
            return self._case_ga_040_delete_nonexistent_alert(case)
        if case_id == "GA-041":
            return self._case_ga_041_cron_execution_consistency(case)
        if case_id == "GA-042":
            return self._case_ga_042_utf8_encoding(case)
        if case_id == "GA-043":
            return self._case_ga_043_response_schema_validation(case)
        if case_id == "RN-001":
            return self._case_rn_001_synonyms_recommendation(case)
        if case_id == "RN-002":
            return self._case_rn_002_limit_20_alerts_for_gestor(case)

        return self.nok(case, f"Caso GA no implementado: {case_id}")

    # -------------------------------------------------------------------------
    # GA-001 to GA-013: Basic creation cases
    # -------------------------------------------------------------------------

    def _case_ga_001_create_valid_alert_complete(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = self._build_alert_payload()
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, detail)
            self._cleanup_alert(user["id"], alert.get("id"))
            return self.ok(case, detail)
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_002_create_alert_without_name(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"cron_expression": "0 9 * * 1-5"}
            status_code, _, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            return self._expect_statuses(case, status_code, req_error, self.VALIDATION_STATUSES, "crear alerta sin name")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_003_create_alert_without_cron(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": "Alert Without Cron"}
            status_code, _, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            return self._expect_statuses(case, status_code, req_error, self.VALIDATION_STATUSES, "crear alerta sin cron_expression")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_004_create_alert_empty_name(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": "", "cron_expression": "0 9 * * 1-5"}
            status_code, _, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            return self._expect_statuses(case, status_code, req_error, self.VALIDATION_STATUSES, "crear alerta con name vacío")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_005_create_alert_name_too_long(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": "A" * 201, "cron_expression": "0 9 * * 1-5"}
            status_code, _, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            return self._expect_statuses(case, status_code, req_error, self.VALIDATION_STATUSES, "crear alerta con name >200 chars")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_006_create_alert_empty_cron(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": "Alert Empty Cron", "cron_expression": ""}
            status_code, _, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            return self._expect_statuses(case, status_code, req_error, self.VALIDATION_STATUSES, "crear alerta con cron_expression vacío")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_007_create_alert_invalid_cron(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": "Alert Invalid Cron", "cron_expression": "not-a-cron-expression"}
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando cron inválido: {req_error}")
            if status_code in self.VALIDATION_STATUSES:
                return self.ok(case, f"Cron inválido rechazado con status {status_code}")
            if status_code == 201:
                self._cleanup_alert(user["id"], response_body.get("id") if isinstance(response_body, dict) else None)
                return self.nok(case, "API aceptó cron_expression inválida 'not-a-cron-expression'")
            return self.nok(case, f"Status inesperado para cron inválido: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_008_create_alert_valid_cron(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = self._build_alert_payload(cron_expression="0 9 * * 1-5")
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, detail)
            self._cleanup_alert(user["id"], alert.get("id"))
            return self.ok(case, detail)
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_009_create_alert_without_descriptors(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": self._unique_alert_name(), "cron_expression": "0 9 * * 1-5"}
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error creando alerta sin descriptors: {req_error}")
            if status_code != 201 or not isinstance(response_body, dict):
                return self.nok(case, f"Crear alerta sin descriptors devolvió {status_code}, esperado 201")
            self._cleanup_alert(user["id"], response_body.get("id"))
            descriptor_error = self._validate_alert_descriptors(response_body)
            if descriptor_error is not None:
                return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
            descriptors = response_body.get("descriptors", [])
            return self.ok(case, f"Alerta creada sin descriptors; server devolvió {len(descriptors)} descriptors")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_010_create_alert_empty_descriptor(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "descriptors": [],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando descriptors vacío: {req_error}")
            if status_code != 201 or not isinstance(response_body, dict):
                return self.nok(case, f"Crear alerta con descriptors vacío devolvió {status_code}, esperado 201")
            self._cleanup_alert(user["id"], response_body.get("id"))
            descriptor_error = self._validate_alert_descriptors(response_body)
            if descriptor_error is not None:
                return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
            descriptors = response_body.get("descriptors", [])
            return self.ok(case, f"Alerta creada con descriptors vacío; server devolvió {len(descriptors)} descriptors")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_011_create_alert_duplicate_descriptor(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "descriptors": ["keyword", "keyword"],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando descriptor duplicado: {req_error}")
            if status_code in self.VALIDATION_STATUSES:
                return self.ok(case, f"Descriptor duplicado rechazado con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                    saved_descriptors = response_body.get("descriptors", [])
                    self._cleanup_alert(user["id"], response_body.get("id"))
                    if isinstance(saved_descriptors, list) and len(saved_descriptors) == 1:
                        return self.ok(case, "Descriptores duplicados deduplicados correctamente")
                    return self.warning(case, f"Descriptores duplicados aceptados: {saved_descriptors!r}")
                return self.warning(case, "Descriptor duplicado aceptado sin respuesta parseable")
            return self.nok(case, f"Status inesperado: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_012_create_alert_special_chars_descriptor(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "descriptors": ["tech & science", "AI/ML", "Ñoño"],
            }
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, detail)
            self._cleanup_alert(user["id"], alert.get("id"))
            return self.ok(case, "Descriptores con caracteres especiales aceptados")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_013_create_alert_without_categories(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": self._unique_alert_name(), "cron_expression": "0 9 * * 1-5"}
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, detail)
            self._cleanup_alert(user["id"], alert.get("id"))
            return self.ok(case, "Alerta creada correctamente sin campo categories")
        finally:
            self._cleanup_user(user.get("id"))

    # -------------------------------------------------------------------------
    # GA-014 to GA-017: Categories validation
    # -------------------------------------------------------------------------

    def _case_ga_014_create_alert_invalid_category(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "categories": [{"code": "INVALID_CODE_99999", "label": "Non-existent category"}],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando category inválida: {req_error}")
            if status_code in self.VALIDATION_STATUSES:
                return self.ok(case, f"Category inválida rechazada con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                self._cleanup_alert(user["id"], response_body.get("id") if isinstance(response_body, dict) else None)
                return self.nok(case, "API aceptó category con code inexistente sin validación de catálogo")
            return self.nok(case, f"Status inesperado para category inválida: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_015_create_alert_inconsistent_category(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "categories": [{"code": "01000000", "label": "this label does not match code 01000000"}],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando category inconsistente: {req_error}")
            if status_code in self.VALIDATION_STATUSES:
                return self.ok(case, f"Category code-label inconsistente rechazada con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                self._cleanup_alert(user["id"], response_body.get("id") if isinstance(response_body, dict) else None)
                return self.nok(case, "API aceptó category con code/label inconsistentes sin validación")
            return self.nok(case, f"Status inesperado para category inconsistente: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_016_create_alert_multiple_categories(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "categories": [
                    {"code": "01000000", "label": "arts, culture, entertainment and media"},
                    {"code": "02000000", "label": "crime, law and justice"},
                ],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando múltiples categories: {req_error}")
            if status_code in self.VALIDATION_STATUSES:
                return self.ok(case, f"Múltiples categories rechazadas con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                self._cleanup_alert(user["id"], response_body.get("id") if isinstance(response_body, dict) else None)
                return self.nok(case, "API aceptó array con más de una category (regla de negocio no aplicada)")
            return self.nok(case, f"Status inesperado: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_017_create_alert_duplicate_category(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            category = {"code": "01000000", "label": "arts, culture, entertainment and media"}
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "categories": [category, category],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando category duplicada: {req_error}")
            if status_code in self.VALIDATION_STATUSES:
                return self.ok(case, f"Category duplicada rechazada con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                    saved = response_body.get("categories", [])
                    self._cleanup_alert(user["id"], response_body.get("id"))
                    if isinstance(saved, list) and len(saved) == 1:
                        return self.nok(case, "API aceptó categories duplicadas y las deduplicó en vez de rechazarlas")
                    return self.nok(case, f"Category duplicada aceptada: {saved!r}")
                return self.nok(case, "Category duplicada aceptada sin respuesta parseable")
            return self.nok(case, f"Status inesperado: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    # -------------------------------------------------------------------------
    # GA-018 to GA-025: RSS channels / information sources fields
    # (not in OpenAPI AlertCreate schema — tested as best-effort)
    # -------------------------------------------------------------------------

    def _case_ga_018_create_alert_without_rss_channels(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": self._unique_alert_name(), "cron_expression": "0 9 * * 1-5"}
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, detail)
            self._cleanup_alert(user["id"], alert.get("id"))
            return self.ok(case, "Alerta creada sin rss_channels_ids (campo no requerido)")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_019_create_alert_without_information_sources(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": self._unique_alert_name(), "cron_expression": "0 9 * * 1-5"}
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, detail)
            self._cleanup_alert(user["id"], alert.get("id"))
            return self.ok(case, "Alerta creada sin information_sources_ids (campo no requerido)")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_020_create_alert_invalid_rss_channel(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "rss_channels_ids": [99999999],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando rss_channel inexistente: {req_error}")
            if status_code in self.VALIDATION_STATUSES | {404}:
                return self.ok(case, f"rss_channel inexistente rechazado con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                self._cleanup_alert(user["id"], response_body.get("id") if isinstance(response_body, dict) else None)
                return self.warning(case, "API aceptó rss_channels_ids con id inexistente (campo ignorado o no validado)")
            return self.nok(case, f"Status inesperado: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_021_create_alert_invalid_information_source(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "information_sources_ids": [99999999],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando information_source inexistente: {req_error}")
            if status_code in self.VALIDATION_STATUSES | {404}:
                return self.ok(case, f"information_source inexistente rechazado con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                self._cleanup_alert(user["id"], response_body.get("id") if isinstance(response_body, dict) else None)
                return self.warning(case, "API aceptó information_sources_ids con id inexistente (campo ignorado o no validado)")
            return self.nok(case, f"Status inesperado: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_022_create_alert_no_sources_no_rss(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {"name": self._unique_alert_name(), "cron_expression": "0 9 * * 1-5"}
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, detail)
            self._cleanup_alert(user["id"], alert.get("id"))
            return self.ok(case, "Alerta creada sin fuentes ni canales RSS")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_023_create_alert_with_valid_sources(self, case: Dict[str, str]) -> TestOutcome:
        case_data = self._loader.get_case_data("GA-023")

        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            source, channel, setup_detail = self._prepare_valid_alert_sources(case_id="GA-023")
            if source is None or channel is None:
                return self.nok(case, setup_detail)

            payload = {
                "name": str(case_data.get("name", self._unique_alert_name("GA-023 Alert"))),
                "cron_expression": str(case_data.get("cron_expression", "0 9 * * 1-5")),
                "descriptors": list(case_data.get("descriptors", ["economia", "mercado", "finanzas"])),
                "rss_channels_ids": [str(channel["id"])],
                "information_sources_ids": [str(source["id"])],
            }
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, f"No se pudo crear alerta con ids válidos ({setup_detail}): {detail}")

            self._cleanup_alert(user["id"], alert.get("id"))
            return self.ok(
                case,
                "Alerta creada con fuente y canal RSS válidos "
                f"(source_id={source['id']}, source_name={source.get('name')!r}, rss_channel_id={channel['id']}, rss_url={channel.get('url')!r})",
            )
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_024_create_alert_duplicate_rss_channel(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "rss_channels_ids": [99999999, 99999999],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando rss_channel duplicado: {req_error}")
            if status_code in self.VALIDATION_STATUSES | {404}:
                return self.ok(case, f"rss_channel duplicado rechazado con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                self._cleanup_alert(user["id"], response_body.get("id") if isinstance(response_body, dict) else None)
                return self.warning(case, "API aceptó rss_channels_ids con ids duplicados (campo ignorado o deduplicado)")
            return self.nok(case, f"Status inesperado: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_025_create_alert_duplicate_information_source(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "information_sources_ids": [99999999, 99999999],
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando information_source duplicado: {req_error}")
            if status_code in self.VALIDATION_STATUSES | {404}:
                return self.ok(case, f"information_source duplicado rechazado con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                self._cleanup_alert(user["id"], response_body.get("id") if isinstance(response_body, dict) else None)
                return self.warning(case, "API aceptó information_sources_ids duplicados (campo ignorado o deduplicado)")
            return self.nok(case, f"Status inesperado: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    # -------------------------------------------------------------------------
    # GA-026 to GA-031: User scoping and business rules
    # -------------------------------------------------------------------------

    def _case_ga_026_mismatched_user_id(self, case: Dict[str, str]) -> TestOutcome:
        return self.warning(
            case,
            "user_id solo se indica en el path de la URL — el schema AlertCreate no tiene campo user_id "
            "en el body, por lo que no existe desajuste path/body que validar",
        )

    def _case_ga_027_create_alert_nonexistent_user(self, case: Dict[str, str]) -> TestOutcome:
        nonexistent_user_id = 99999999
        payload = self._build_alert_payload()
        status_code, _, req_error = self._authorized_request(
            "POST", f"/api/v1/users/{nonexistent_user_id}/alerts", body=payload
        )
        return self._expect_statuses(case, status_code, req_error, self.NOT_FOUND_STATUSES, "crear alerta en usuario inexistente")

    def _case_ga_028_create_duplicate_alert_same_user(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            alert_name = self._unique_alert_name()
            payload = {"name": alert_name, "cron_expression": "0 9 * * 1-5"}
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, detail)
            try:
                status_code, _, req_error = self._authorized_request(
                    "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
                )
                return self._expect_statuses(case, status_code, req_error, self.VALIDATION_STATUSES, "crear alerta duplicada mismo usuario")
            finally:
                self._cleanup_alert(user["id"], alert.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_029_same_name_different_user(self, case: Dict[str, str]) -> TestOutcome:
        user_a, detail_a = self._create_test_user()
        if user_a is None:
            return self.nok(case, detail_a)
        user_b, detail_b = self._create_test_user()
        if user_b is None:
            self._cleanup_user(user_a.get("id"))
            return self.nok(case, detail_b)
        try:
            alert_name = self._unique_alert_name()
            payload = {"name": alert_name, "cron_expression": "0 9 * * 1-5"}
            alert_a, detail_create_a = self._create_alert(user_a["id"], payload)
            if alert_a is None:
                return self.nok(case, detail_create_a)
            try:
                alert_b, detail_create_b = self._create_alert(user_b["id"], payload)
                if alert_b is None:
                    return self.nok(case, f"Segunda alerta en distinto usuario fallo: {detail_create_b}")
                self._cleanup_alert(user_b["id"], alert_b.get("id"))
                return self.ok(case, "Mismo nombre de alerta aceptado en distinto usuario")
            finally:
                self._cleanup_alert(user_a["id"], alert_a.get("id"))
        finally:
            self._cleanup_user(user_a.get("id"))
            self._cleanup_user(user_b.get("id"))

    def _case_ga_030_name_normalization(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload_1 = {"name": "  Alert Normalization Test  ", "cron_expression": "0 9 * * 1-5"}
            payload_2 = {"name": "ALERT NORMALIZATION TEST", "cron_expression": "0 9 * * 1-5"}
            alert_1, detail_1 = self._create_alert(user["id"], payload_1)
            if alert_1 is None:
                return self.nok(case, detail_1)
            try:
                status_code, response_body, req_error = self._authorized_request(
                    "POST", f"/api/v1/users/{user['id']}/alerts", body=payload_2
                )
                if status_code in self.VALIDATION_STATUSES:
                    return self.ok(case, "API aplica normalización: variantes del mismo name tratadas como duplicados")
                if status_code == 201:
                    if isinstance(response_body, dict):
                        descriptor_error = self._validate_alert_descriptors(response_body)
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        if descriptor_error is not None:
                            return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                    return self.nok(case, "API no normaliza name: variantes con distinto case/espacios tratadas como nombres distintos")
                return self.nok(case, f"Status inesperado: {status_code}")
            finally:
                self._cleanup_alert(user["id"], alert_1.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_031_extra_fields_in_payload(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": self._unique_alert_name(),
                "cron_expression": "0 9 * * 1-5",
                "extra_field": "unexpected_value",
                "another_extra": 42,
            }
            status_code, response_body, req_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
            )
            if req_error is not None:
                return self.nok(case, f"Error enviando payload con campos extra: {req_error}")
            if status_code in self.VALIDATION_STATUSES:
                return self.ok(case, f"Payload con campos extra rechazado con status {status_code}")
            if status_code == 201:
                if isinstance(response_body, dict):
                    descriptor_error = self._validate_alert_descriptors(response_body)
                    if descriptor_error is not None:
                        self._cleanup_alert(user["id"], response_body.get("id"))
                        return self.nok(case, f"Respuesta de alerta inválida: {descriptor_error}")
                    self._cleanup_alert(user["id"], response_body.get("id"))
                    has_extra = "extra_field" in response_body or "another_extra" in response_body
                    if has_extra:
                        return self.nok(case, "Campos extra fueron persistidos en la respuesta")
                    return self.ok(case, "Campos extra ignorados correctamente")
                return self.warning(case, "Campos extra aceptados pero respuesta no parseable")
            return self.nok(case, f"Status inesperado: {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    # -------------------------------------------------------------------------
    # GA-032 to GA-035: Read operations
    # -------------------------------------------------------------------------

    def _case_ga_032_get_existing_alert(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            alert, detail = self._create_alert(user["id"], self._build_alert_payload())
            if alert is None:
                return self.nok(case, detail)
            try:
                status_code, response_body, req_error = self._authorized_request(
                    "GET", f"/api/v1/users/{user['id']}/alerts/{alert['id']}", body=None
                )
                if req_error is not None:
                    return self.nok(case, f"Error en GET alerta existente: {req_error}")
                if status_code != 200:
                    return self.nok(case, f"GET alerta devolvió {status_code}, esperado 200")
                if not isinstance(response_body, dict):
                    return self.nok(case, "GET alerta no devolvió objeto JSON")
                descriptor_error = self._validate_alert_descriptors(response_body)
                if descriptor_error is not None:
                    return self.nok(case, f"GET alerta devolvió descriptors inválidos: {descriptor_error}")
                return self.ok(case, f"Alerta consultada correctamente con id {alert['id']}")
            finally:
                self._cleanup_alert(user["id"], alert.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_033_get_nonexistent_alert(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            status_code, _, req_error = self._authorized_request(
                "GET", f"/api/v1/users/{user['id']}/alerts/99999999", body=None
            )
            return self._expect_statuses(case, status_code, req_error, self.NOT_FOUND_STATUSES, "GET alerta inexistente")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_034_validate_id_integer(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            alert, detail = self._create_alert(user["id"], self._build_alert_payload())
            if alert is None:
                return self.nok(case, detail)
            try:
                alert_id = alert.get("id")
                if not isinstance(alert_id, int):
                    return self.nok(case, f"id en respuesta no es entero: {alert_id!r} ({type(alert_id).__name__})")
                return self.ok(case, f"id de alerta es entero correcto: {alert_id}")
            finally:
                self._cleanup_alert(user["id"], alert.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_035_validate_user_id_in_response(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            alert, detail = self._create_alert(user["id"], self._build_alert_payload())
            if alert is None:
                return self.nok(case, detail)
            try:
                response_user_id = alert.get("user_id")
                expected_user_id = user["id"]
                if response_user_id != expected_user_id:
                    return self.nok(case, f"user_id en respuesta ({response_user_id!r}) no coincide con path ({expected_user_id})")
                return self.ok(case, f"user_id en respuesta es consistente con el path: {response_user_id}")
            finally:
                self._cleanup_alert(user["id"], alert.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    # -------------------------------------------------------------------------
    # GA-036 to GA-038: Update operations
    # -------------------------------------------------------------------------

    def _case_ga_036_update_alert_valid(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            alert, detail = self._create_alert(user["id"], self._build_alert_payload())
            if alert is None:
                return self.nok(case, detail)
            try:
                update_payload = {"name": self._unique_alert_name(), "cron_expression": "0 12 * * *"}
                status_code, response_body, req_error = self._authorized_request(
                    "PUT", f"/api/v1/users/{user['id']}/alerts/{alert['id']}", body=update_payload
                )
                if req_error is not None:
                    return self.nok(case, f"Error actualizando alerta: {req_error}")
                if status_code != 200:
                    return self.nok(case, f"PUT alerta devolvió {status_code}, esperado 200")
                if not isinstance(response_body, dict):
                    return self.nok(case, "PUT alerta no devolvió objeto JSON")
                descriptor_error = self._validate_alert_descriptors(response_body)
                if descriptor_error is not None:
                    return self.nok(case, f"PUT alerta devolvió descriptors inválidos: {descriptor_error}")
                if response_body.get("cron_expression") != "0 12 * * *":
                    return self.nok(case, f"cron_expression no actualizado correctamente: {response_body.get('cron_expression')!r}")
                return self.ok(case, "Alerta actualizada correctamente")
            finally:
                self._cleanup_alert(user["id"], alert.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_037_update_alert_invalid_cron(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            alert, detail = self._create_alert(user["id"], self._build_alert_payload())
            if alert is None:
                return self.nok(case, detail)
            try:
                update_payload = {"cron_expression": "bad cron!!"}
                status_code, response_body, req_error = self._authorized_request(
                    "PUT", f"/api/v1/users/{user['id']}/alerts/{alert['id']}", body=update_payload
                )
                if req_error is not None:
                    return self.nok(case, f"Error actualizando cron inválido: {req_error}")
                if status_code in self.VALIDATION_STATUSES:
                    return self.ok(case, f"cron_expression inválido en update rechazado con status {status_code}")
                if status_code == 200:
                    if isinstance(response_body, dict):
                        descriptor_error = self._validate_alert_descriptors(response_body)
                        if descriptor_error is not None:
                            return self.nok(case, f"PUT alerta devolvió descriptors inválidos: {descriptor_error}")
                    return self.nok(case, "API aceptó cron_expression inválida en update (sin validación de formato)")
                return self.nok(case, f"Status inesperado: {status_code}")
            finally:
                self._cleanup_alert(user["id"], alert.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_038_update_alert_invalid_categories(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            alert, detail = self._create_alert(user["id"], self._build_alert_payload())
            if alert is None:
                return self.nok(case, detail)
            try:
                update_payload = {"categories": [{"code": "INVALID_XXXX", "label": "bad label"}]}
                status_code, response_body, req_error = self._authorized_request(
                    "PUT", f"/api/v1/users/{user['id']}/alerts/{alert['id']}", body=update_payload
                )
                if req_error is not None:
                    return self.nok(case, f"Error actualizando categories inválidas: {req_error}")
                if status_code in self.VALIDATION_STATUSES:
                    return self.ok(case, f"Categories inválidas en update rechazadas con status {status_code}")
                if status_code == 200:
                    if isinstance(response_body, dict):
                        descriptor_error = self._validate_alert_descriptors(response_body)
                        if descriptor_error is not None:
                            return self.nok(case, f"PUT alerta devolvió descriptors inválidos: {descriptor_error}")
                    return self.nok(case, "API aceptó categories con code inválido en update (sin validación de catálogo)")
                return self.nok(case, f"Status inesperado: {status_code}")
            finally:
                self._cleanup_alert(user["id"], alert.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    # -------------------------------------------------------------------------
    # GA-039 to GA-040: Delete operations
    # -------------------------------------------------------------------------

    def _case_ga_039_delete_existing_alert(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            alert, detail = self._create_alert(user["id"], self._build_alert_payload())
            if alert is None:
                return self.nok(case, detail)
            status_code, _, req_error = self._authorized_request(
                "DELETE", f"/api/v1/users/{user['id']}/alerts/{alert['id']}", body=None
            )
            if req_error is not None:
                return self.nok(case, f"Error borrando alerta: {req_error}")
            if status_code != 204:
                self._cleanup_alert(user["id"], alert.get("id"))
                return self.nok(case, f"DELETE alerta devolvió {status_code}, esperado 204")
            return self.ok(case, f"Alerta eliminada correctamente con id {alert['id']}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_040_delete_nonexistent_alert(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            status_code, _, req_error = self._authorized_request(
                "DELETE", f"/api/v1/users/{user['id']}/alerts/99999999", body=None
            )
            return self._expect_statuses(case, status_code, req_error, self.NOT_FOUND_STATUSES, "DELETE alerta inexistente")
        finally:
            self._cleanup_user(user.get("id"))

    # -------------------------------------------------------------------------
    # GA-041 to GA-043: Edge cases and schema
    # -------------------------------------------------------------------------

    def _case_ga_041_cron_execution_consistency(self, case: Dict[str, str]) -> TestOutcome:
        return self.warning(
            case,
            "validación de interpretación/ejecución de cron requiere acceso al scheduler backend "
            "— no es automatizable via API REST",
        )

    def _case_ga_042_utf8_encoding(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            payload = {
                "name": "Alerta Ñoña 李 García",
                "cron_expression": "0 9 * * 1-5",
                "descriptors": ["描述符", "indicador-ñ"],
            }
            alert, detail = self._create_alert(user["id"], payload)
            if alert is None:
                return self.nok(case, detail)
            try:
                if alert.get("name") != "Alerta Ñoña 李 García":
                    return self.nok(case, f"name no devuelto correctamente: {alert.get('name')!r}")
                return self.ok(case, "Encoding UTF-8 correcto en name y descriptors")
            finally:
                self._cleanup_alert(user["id"], alert.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    def _case_ga_043_response_schema_validation(self, case: Dict[str, str]) -> TestOutcome:
        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)
        try:
            alert, detail = self._create_alert(user["id"], self._build_alert_payload())
            if alert is None:
                return self.nok(case, detail)
            try:
                required_fields = {"id", "name", "cron_expression", "user_id"}
                missing = required_fields - set(alert.keys())
                if missing:
                    return self.nok(case, f"Campos requeridos ausentes en respuesta: {missing!r}")
                if not isinstance(alert.get("id"), int):
                    return self.nok(case, f"id no es entero: {alert.get('id')!r}")
                if not isinstance(alert.get("user_id"), int):
                    return self.nok(case, f"user_id no es entero: {alert.get('user_id')!r}")
                if not isinstance(alert.get("name"), str):
                    return self.nok(case, f"name no es string: {alert.get('name')!r}")
                if not isinstance(alert.get("cron_expression"), str):
                    return self.nok(case, f"cron_expression no es string: {alert.get('cron_expression')!r}")
                return self.ok(case, "Schema de respuesta cumple contrato OpenAPI")
            finally:
                self._cleanup_alert(user["id"], alert.get("id"))
        finally:
            self._cleanup_user(user.get("id"))

    def _case_rn_001_synonyms_recommendation(self, case: Dict[str, str]) -> TestOutcome:
        case_data = self._loader.get_case_data("RN-001")
        keyword = str(case_data.get("keyword", "economia")).strip() or "economia"
        min_suggestions = int(case_data.get("min_suggestions", 3))
        max_suggestions = int(case_data.get("max_suggestions", 10))

        user, user_detail = self._create_test_user()
        if user is None:
            return self.nok(case, user_detail)

        created_alert_id: Optional[Any] = None
        try:
            creation_attempts: List[Tuple[str, Dict[str, Any]]] = [
                (
                    "keyword",
                    {
                        "name": self._unique_alert_name("RN1"),
                        "cron_expression": "0 9 * * 1-5",
                        "keyword": keyword,
                    },
                ),
                (
                    "descriptors_seed",
                    {
                        "name": self._unique_alert_name("RN1"),
                        "cron_expression": "0 9 * * 1-5",
                        "descriptors": [keyword],
                    },
                ),
            ]

            last_error = ""
            response_body: Any = None
            for attempt_name, payload in creation_attempts:
                status_code, response_body, req_error = self._authorized_request(
                    "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
                )
                if req_error is not None:
                    return self.nok(case, f"Error creando alerta RN-001 ({attempt_name}): {req_error}")
                if status_code == 201 and isinstance(response_body, dict):
                    created_alert_id = response_body.get("id")
                    break
                last_error = f"Intento {attempt_name} devolvió {status_code} con respuesta {response_body!r}"
            else:
                return self.nok(case, f"No se pudo crear alerta para RN-001. {last_error}")

            descriptors = response_body.get("descriptors") if isinstance(response_body, dict) else None
            if not isinstance(descriptors, list):
                return self.nok(case, f"Campo descriptors ausente o no es lista: {descriptors!r}")

            invalid_items = [item for item in descriptors if not isinstance(item, str)]
            if invalid_items:
                return self.nok(case, f"Campo descriptors contiene elementos no string: {invalid_items!r}")

            descriptor_count = len(descriptors)
            if descriptor_count < min_suggestions or descriptor_count > max_suggestions:
                return self.nok(
                    case,
                    f"Campo descriptors fuera de rango [{min_suggestions}, {max_suggestions}]: {descriptor_count}",
                )

            return self.ok(
                case,
                f"Alerta creada y descriptors devuelve {descriptor_count} strings (rango esperado {min_suggestions}-{max_suggestions})",
            )
        finally:
            self._cleanup_alert(user["id"], created_alert_id)
            self._cleanup_user(user.get("id"))

    def _case_rn_002_limit_20_alerts_for_gestor(self, case: Dict[str, str]) -> TestOutcome:
        case_data = self._loader.get_case_data("RN-002")
        manager_role_name = str(case_data.get("manager_role_name", "gestor")).strip() or "gestor"
        max_alerts = int(case_data.get("max_alerts_per_manager", 20))

        gestor_role_id, role_was_created, role_error = self._get_or_create_role(manager_role_name)
        if role_error is not None:
            return self.nok(case, role_error)

        user, user_detail = self._create_test_user(role_ids=[gestor_role_id])
        if user is None:
            if role_was_created:
                self._cleanup_role(gestor_role_id)
            return self.nok(case, user_detail)

        created_alert_ids: List[Any] = []
        try:
            for _ in range(max_alerts):
                payload = self._build_alert_payload(name=self._unique_alert_name("RN2"))
                status_code, response_body, req_error = self._authorized_request(
                    "POST", f"/api/v1/users/{user['id']}/alerts", body=payload
                )
                if req_error is not None:
                    return self.nok(case, f"Error creando alerta en limite RN-002: {req_error}")
                if status_code != 201 or not isinstance(response_body, dict):
                    return self.nok(
                        case,
                        f"No se pudo completar la carga de {max_alerts} alertas: status={status_code}, body={response_body!r}",
                    )
                created_alert_ids.append(response_body.get("id"))

            overflow_payload = self._build_alert_payload(name=self._unique_alert_name("RN2"))
            overflow_status, overflow_body, overflow_error = self._authorized_request(
                "POST", f"/api/v1/users/{user['id']}/alerts", body=overflow_payload
            )

            if overflow_error is not None:
                return self.nok(case, f"Error creando alerta {max_alerts + 1} en RN-002: {overflow_error}")
            if overflow_status in {400, 403, 409, 422}:
                return self.ok(case, f"Límite de {max_alerts} alertas aplicado correctamente (status {overflow_status})")
            if overflow_status == 201:
                if isinstance(overflow_body, dict):
                    created_alert_ids.append(overflow_body.get("id"))
                return self.nok(
                    case,
                    f"La alerta número {max_alerts + 1} fue aceptada (status 201); el límite de {max_alerts} alertas no está aplicado",
                )
            return self.nok(case, f"Status inesperado al crear alerta {max_alerts + 1}: {overflow_status}")
        finally:
            for alert_id in created_alert_ids:
                self._cleanup_alert(user["id"], alert_id)
            self._cleanup_user(user.get("id"))
            if role_was_created:
                self._cleanup_role(gestor_role_id)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _build_alert_payload(
        self,
        *,
        name: Optional[str] = None,
        cron_expression: str = "0 9 * * 1-5",
        descriptors: Optional[List[str]] = None,
        categories: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": name or self._unique_alert_name(),
            "cron_expression": cron_expression,
        }
        if descriptors is not None:
            payload["descriptors"] = descriptors
        if categories is not None:
            payload["categories"] = categories
        return payload

    def _prepare_valid_alert_sources(
        self, *, case_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], str]:
        source_payload = self._build_information_source_payload(case_id=case_id)
        source, source_detail = self._create_information_source(source_payload)
        if source is None:
            return None, None, source_detail

        category_id, category_detail = self._get_or_create_alert_category_id()
        if category_id is None:
            return None, None, category_detail

        channel_payload = {
            "url": self._build_rss_channel_url(case_id=case_id),
            "category_id": category_id,
        }
        channel, channel_detail = self._create_rss_channel(int(source["id"]), channel_payload)
        if channel is None:
            return None, None, f"{source_detail}; {channel_detail}"

        return source, channel, f"{source_detail}; {channel_detail}"

    def _build_information_source_payload(self, *, case_id: str) -> Dict[str, str]:
        unique = uuid.uuid4().hex[:8]
        source_name = f"{case_id} Information Source {unique}"
        return {
            "name": source_name,
            "url": f"https://example.com/{case_id.lower()}/source/{unique}",
        }

    def _build_rss_channel_url(self, *, case_id: str) -> str:
        unique = uuid.uuid4().hex[:8]
        return f"https://hnrss.org/frontpage?case={case_id.lower()}&uid={unique}"

    def _get_or_create_alert_category_id(self) -> Tuple[Optional[int], str]:
        status_code, response_body, req_error = self._authorized_request("GET", "/api/v1/categories", body=None)
        if req_error is None and status_code == 200 and isinstance(response_body, list):
            for item in response_body:
                if isinstance(item, dict) and isinstance(item.get("id"), int):
                    return int(item["id"]), f"Categoría reutilizada con id {item['id']}"

        payload = {"name": "Sociedad", "source": "IPTC"}
        status_code, response_body, req_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        if req_error is not None:
            return None, f"Error creando categoría para canal RSS: {req_error}"
        if status_code == 201 and isinstance(response_body, dict) and isinstance(response_body.get("id"), int):
            self._cleanup_register(self._cleanup_category, response_body.get("id"))
            return int(response_body["id"]), f"Categoría creada con id {response_body['id']}"

        status_code, response_body, req_error = self._authorized_request("GET", "/api/v1/categories", body=None)
        if req_error is None and status_code == 200 and isinstance(response_body, list):
            for item in response_body:
                if isinstance(item, dict) and isinstance(item.get("id"), int):
                    return int(item["id"]), f"Categoría reutilizada tras fallback con id {item['id']}"

        return None, f"No se pudo obtener categoría válida para RSS: status={status_code}, body={response_body!r}"

    def _create_information_source(self, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, req_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        if req_error is not None:
            return None, f"Error creando information source: {req_error}"
        if status_code != 201:
            return None, f"Crear information source devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear information source no devolvió objeto JSON: {response_body!r}"
        self._cleanup_register(self._cleanup_information_source, response_body.get("id"))
        return response_body, f"Information source creada con id {response_body.get('id')}"

    def _create_rss_channel(self, source_id: int, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, req_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        if req_error is not None:
            return None, f"Error creando rss channel: {req_error}"
        if status_code != 201:
            return None, f"Crear rss channel devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear rss channel no devolvió objeto JSON: {response_body!r}"
        self._cleanup_register(self._cleanup_rss_channel, source_id, response_body.get("id"))
        return response_body, f"RSS channel creado con id {response_body.get('id')}"

    @staticmethod
    def _validate_alert_descriptors(alert: Any) -> Optional[str]:
        if not isinstance(alert, dict):
            return "respuesta no es objeto JSON"

        descriptors = alert.get("descriptors")
        if not isinstance(descriptors, list):
            return f"campo descriptors ausente o no es lista: {descriptors!r}"

        invalid_items = [item for item in descriptors if not isinstance(item, str)]
        if invalid_items:
            return f"campo descriptors contiene elementos no string: {invalid_items!r}"

        descriptor_count = len(descriptors)
        if descriptor_count < 3 or descriptor_count > 10:
            return f"campo descriptors fuera de rango [3, 10]: {descriptor_count}"

        return None

    def _create_alert(
        self, user_id: int, payload: Dict[str, Any]
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, req_error = self._authorized_request(
            "POST", f"/api/v1/users/{user_id}/alerts", body=payload
        )
        if req_error is not None:
            return None, f"Error creando alerta: {req_error}"
        if status_code != 201:
            return None, f"Crear alerta devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear alerta no devolvió objeto JSON: {response_body!r}"
        descriptor_error = self._validate_alert_descriptors(response_body)
        if descriptor_error is not None:
            return None, f"Crear alerta devolvió descriptors inválidos: {descriptor_error}. Respuesta: {response_body!r}"
        self._cleanup_register(self._cleanup_alert, user_id, response_body.get("id"))
        return response_body, f"Alerta creada correctamente con id {response_body.get('id')}"

    def _cleanup_alert(self, user_id: Any, alert_id: Any) -> None:
        if user_id in (None, "") or alert_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/users/{user_id}/alerts/{alert_id}", body=None)
        except Exception:
            return

    def _cleanup_rss_channel(self, source_id: Any, channel_id: Any) -> None:
        if source_id in (None, "") or channel_id in (None, ""):
            return
        try:
            self._authorized_request(
                "DELETE", f"/api/v1/information-sources/{source_id}/rss-channels/{channel_id}", body=None
            )
        except Exception:
            return

    def _cleanup_information_source(self, source_id: Any) -> None:
        if source_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/information-sources/{source_id}", body=None)
        except Exception:
            return

    def _cleanup_category(self, category_id: Any) -> None:
        if category_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/categories/{category_id}", body=None)
        except Exception:
            return

    def _create_test_user(self, role_ids: Optional[List[int]] = None) -> Tuple[Optional[Dict[str, Any]], str]:
        payload = {
            "email": self._unique_email(),
            "first_name": "Alert",
            "last_name": "Tester",
            "organization": "QA",
            "password": "Valid123",
            "role_ids": role_ids if role_ids is not None else [],
        }
        status_code, response_body, req_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if req_error is not None:
            return None, f"Error creando usuario de prueba: {req_error}"
        if status_code != 201:
            return None, f"Crear usuario devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear usuario no devolvió objeto JSON: {response_body!r}"
        self._cleanup_register(self._cleanup_user, response_body.get("id"))
        return response_body, f"Usuario de prueba creado con id {response_body.get('id')}"

    def _get_or_create_role(self, role_name: str) -> Tuple[Optional[int], bool, Optional[str]]:
        """Busca el rol por nombre; si no existe, lo crea. Devuelve (role_id, fue_creado, error)."""
        status_code, response_body, req_error = self._authorized_request("GET", "/api/v1/roles", body=None)
        if req_error is not None:
            return None, False, f"Error consultando roles: {req_error}"
        if status_code != 200 or not isinstance(response_body, list):
            return None, False, f"GET /api/v1/roles devolvió {status_code}, esperado 200 con array"

        target = role_name.strip().lower()
        for role in response_body:
            if not isinstance(role, dict):
                continue
            if str(role.get("name", "")).strip().lower() == target and isinstance(role.get("id"), int):
                return role["id"], False, None

        # Rol no existe — crearlo como dato de prueba
        create_status, create_body, create_error = self._authorized_request(
            "POST", "/api/v1/roles", body={"name": role_name}
        )
        if create_error is not None:
            return None, False, f"Error creando rol '{role_name}': {create_error}"
        if create_status not in {200, 201} or not isinstance(create_body, dict):
            return None, False, f"Crear rol '{role_name}' devolvió {create_status}. Respuesta: {create_body!r}"
        role_id = create_body.get("id")
        if not isinstance(role_id, int):
            return None, False, f"Crear rol no devolvió id entero: {create_body!r}"
        return role_id, True, None

    def _cleanup_role(self, role_id: Any) -> None:
        if role_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/roles/{role_id}", body=None)
        except Exception:
            return

    def _cleanup_user(self, user_id: Any) -> None:
        if user_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/users/{user_id}", body=None)
        except Exception:
            return

    def _login_seed_user(self) -> Tuple[Optional[str], Optional[str]]:
        payload = {"email": self.seed_email, "password": self.seed_password}
        status_code, response_body, req_error = self._request("POST", "/api/v1/auth/login", body=payload)
        if req_error is not None:
            return None, f"Error en login semilla: {req_error}"
        if status_code != 200 or not isinstance(response_body, dict):
            return None, f"Login semilla fallo con status {status_code}"
        token = response_body.get("access_token")
        if not token:
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
        if request_error is None and method.upper() == "POST" and status_code == 201 and isinstance(response_body, dict):
            if path == "/api/v1/users":
                self._cleanup_register(self._cleanup_user, response_body.get("id"))
            elif path.startswith("/api/v1/users/") and path.endswith("/alerts"):
                user_id = path.split("/")[4] if len(path.split("/")) > 4 else None
                self._cleanup_register(self._cleanup_alert, user_id, response_body.get("id"))
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
        expected_statuses: set,
        context: str,
    ) -> TestOutcome:
        if request_error is not None:
            return self.nok(case, f"Error en {context}: {request_error}")
        if status_code not in expected_statuses:
            expected = ", ".join(str(s) for s in sorted(expected_statuses))
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
    def _unique_email() -> str:
        unique = uuid.uuid4().hex[:12]
        return f"ga.{unique}@example.com"

    @staticmethod
    def _unique_alert_name(prefix: str = "Alert") -> str:
        unique = uuid.uuid4().hex[:8]
        return f"{prefix}-{unique}"
