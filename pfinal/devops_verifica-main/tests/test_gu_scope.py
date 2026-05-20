from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome


class UserManagementScopeTests(BaseScopeTests):
    """Implements GU-* test cases for user management and related API security checks."""

    VALIDATION_ERROR_STATUSES = {400, 409, 415, 422}
    NOT_FOUND_STATUSES = {400, 404, 422}

    def __init__(self, base_url: str, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.seed_email = "admin@newsradar.com"
        self.seed_password = "admin123"
        self.locust_file = Path(__file__).resolve().parent / "load" / "locustfile_gu_load.py"

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        self._cleanup_reset()
        try:
            return self._run_case_impl(case)
        finally:
            self._cleanup_run()

    def _run_case_impl(self, case: Dict[str, str]) -> TestOutcome:
        case_id = str(case.get("Caso de Prueba", "")).strip()

        if case_id == "GU-001":
            return self._case_gu_001_create_valid_user(case)
        if case_id in {"GU-002", "GU-003", "GU-004", "GU-006"}:
            return self._case_gu_002_gu_006_missing_required_field(case_id, case)
        if case_id == "GU-005":
            return self._case_gu_005_without_role_ids_defaults_to_gestor(case)
        if case_id == "GU-007":
            return self._case_gu_007_invalid_email(case)
        if case_id == "GU-008":
            return self._case_gu_008_duplicate_email(case)
        if case_id in {"GU-009", "GU-010", "GU-011", "GU-012", "GU-013", "GU-014", "GU-015", "GU-017", "GU-018"}:
            return self._case_gu_009_gu_018_validation_variant(case_id, case)
        if case_id in {"GU-019", "GU-020", "GU-021", "GU-045", "GU-056"}:
            return self.warning(case, "Caso requiere validacion en base de datos o hashing interno no accesible por API")
        if case_id == "GU-022":
            return self._case_gu_022_optional_field_omitted(case)
        if case_id == "GU-023":
            return self._case_gu_023_special_characters(case)
        if case_id == "GU-024":
            return self._case_gu_024_sql_injection_payload(case)
        if case_id == "GU-025":
            return self._case_gu_025_xss_payload(case)
        if case_id == "GU-026":
            return self._case_gu_026_multiple_roles(case)
        if case_id == "GU-027":
            return self._case_gu_027_update_valid_user(case)
        if case_id == "GU-028":
            return self._case_gu_028_update_email_to_existing(case)
        if case_id == "GU-029":
            return self._case_gu_029_delete_existing_user(case)
        if case_id == "GU-030":
            return self._case_gu_030_delete_missing_user(case)
        if case_id == "GU-031":
            return self._case_gu_031_get_existing_user(case)
        if case_id == "GU-032":
            return self._case_gu_032_get_missing_user(case)
        if case_id == "GU-033":
            return self._case_gu_033_whitespace_strings(case)
        if case_id == "GU-034":
            return self._case_gu_034_uppercase_email(case)
        if case_id == "GU-035":
            return self._case_gu_035_case_insensitive_duplicate(case)
        if case_id == "GU-036":
            return self._case_gu_036_parallel_same_email_with_locust(case)
        if case_id == "GU-037":
            return self._case_gu_037_password_not_exposed(case)
        if case_id == "GU-038":
            return self._case_gu_038_extra_payload_field(case)
        if case_id == "GU-039":
            return self._case_gu_039_parallel_sla_load_with_locust(case)
        if case_id == "GU-040":
            return self._case_gu_040_utf8_payload(case)
        if case_id == "GU-041":
            return self._case_gu_041_users_without_token(case)
        if case_id in {"GU-042", "GU-043", "GU-044"}:
            return self.warning(case, "Caso requiere precondiciones de seguridad o infraestructura no automatizadas en esta suite")
        if case_id == "GU-046":
            return self._case_gu_046_recreate_user_after_delete(case)
        if case_id == "GU-051":
            return self._case_gu_051_payload_too_large(case)
        if case_id == "GU-057":
            return self._case_gu_057_parallel_rate_limiting_with_locust(case)
        if case_id == "GU-047":
            return self._case_gu_047_users_pagination(case)
        if case_id == "GU-048":
            return self._case_gu_048_users_filter(case)
        if case_id == "GU-049":
            return self._case_gu_049_unsupported_content_type(case)
        if case_id == "GU-050":
            return self._case_gu_050_malformed_json(case)
        if case_id == "GU-052":
            return self._case_gu_052_email_alias(case)
        if case_id == "GU-053":
            return self._case_gu_053_patch_not_supported(case)
        if case_id == "GU-054":
            return self._case_gu_054_invalid_ids(case)
        if case_id == "GU-055":
            return self._case_gu_055_nosql_injection(case)
        if case_id == "GU-058":
            return self._case_gu_058_empty_body(case)
        if case_id == "GU-059":
            return self._case_gu_059_security_headers(case)
        if case_id == "GU-060":
            return self._case_gu_060_mixed_role_ids(case)
        if case_id == "GU-061":
            return self._case_gu_061_only_gestor_role(case)
        if case_id == "GU-016":
            return self._case_gu_016_empty_role_ids_defaults_to_gestor(case)

        return self.nok(case, f"Caso GU no implementado: {case_id}")

    def _case_gu_001_create_valid_user(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload()
        created_user, detail = self._create_user_and_cleanup(payload)
        if created_user is None:
            return self.nok(case, detail)
        return self.ok(case, detail)

    def _case_gu_002_gu_006_missing_required_field(self, case_id: str, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload()
        missing_field_by_case = {
            "GU-002": "email",
            "GU-003": "first_name",
            "GU-004": "last_name",
            "GU-006": "password",
        }
        payload.pop(missing_field_by_case[case_id], None)
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "validacion por campo obligatorio")

    def _case_gu_007_invalid_email(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload(email="invalid-email")
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "email inválido")

    def _case_gu_008_duplicate_email(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload()
        user, detail = self._create_user(payload)
        if user is None:
            return self.nok(case, f"No se pudo preparar usuario duplicado: {detail}")

        try:
            status_code, _, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
            return self._expect_statuses(case, status_code, request_error, {400, 409, 422}, "email duplicado")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_gu_009_gu_018_validation_variant(self, case_id: str, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload()

        if case_id == "GU-009":
            payload["first_name"] = ""
        elif case_id == "GU-010":
            payload["first_name"] = "A" * 121
        elif case_id == "GU-011":
            payload["last_name"] = ""
        elif case_id == "GU-012":
            payload["last_name"] = "B" * 121
        elif case_id == "GU-013":
            payload["organization"] = "O" * 181
        elif case_id == "GU-014":
            payload["password"] = "12345"
        elif case_id == "GU-015":
            payload["password"] = "p" * 129
        elif case_id == "GU-017":
            payload["role_ids"] = ["admin"]
        elif case_id == "GU-018":
            payload["role_ids"] = [99999999]

        expected = {400, 404, 422} if case_id == "GU-018" else {400, 422}
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        return self._expect_statuses(case, status_code, request_error, expected, f"validacion del caso {case_id}")

    def _case_gu_022_optional_field_omitted(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload()
        payload.pop("organization", None)
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error creando usuario sin organization: {request_error}")
        if status_code == 201 and isinstance(response_body, dict):
            self._cleanup_user(response_body.get("id"))
            return self.nok(case, "El API aceptó la creación sin organization, pero es un campo obligatorio")
        if status_code in {400, 422}:
            return self.ok(case, f"El API rechazó correctamente la creación sin organization con status {status_code}")
        return self.nok(case, f"Crear usuario sin organization devolvió status inesperado {status_code}")

    def _case_gu_023_special_characters(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload(first_name="José", last_name="Peña-Núñez")
        created_user, detail = self._create_user_and_cleanup(payload)
        if created_user is None:
            return self.nok(case, detail)
        return self.ok(case, detail)

    def _case_gu_024_sql_injection_payload(self, case: Dict[str, str]) -> TestOutcome:
        return self.warning(
            case,
            "No es posible certificar por API REST la mitigacion completa de inyeccion SQL; se requiere validacion adicional de seguridad en backend/BD",
        )

    def _case_gu_025_xss_payload(self, case: Dict[str, str]) -> TestOutcome:
        xss_marker = "<script>alert('x')</script>"
        payload = self._build_valid_user_payload(first_name=xss_marker)
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error enviando payload XSS inocuo: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Payload XSS inocuo rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                returned_name = str(response_body.get("first_name", ""))
                if "<script>" in returned_name.lower():
                    return self.nok(case, "El payload XSS fue persistido sin sanitizacion")
                return self.ok(case, "El payload XSS inocuo fue aceptado pero sanitizado")
            finally:
                self._cleanup_user(response_body.get("id"))
        return self.nok(case, f"Payload XSS inocuo devolvió status inesperado {status_code}")

    def _case_gu_026_multiple_roles(self, case: Dict[str, str]) -> TestOutcome:
        gestor_role_id, gestor_detail = self._get_gestor_role_id()
        if gestor_role_id is None:
            return self.nok(case, f"No se encontró el rol gestor requerido: {gestor_detail}")
        other_role_ids, _ = self._get_non_gestor_role_ids()
        payload_role_ids: List[Any] = [gestor_role_id]
        if other_role_ids:
            payload_role_ids.append(other_role_ids[0])
        else:
            payload_role_ids.append(gestor_role_id)

        payload = self._build_valid_user_payload(role_ids=payload_role_ids)
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 409, 422}, "mas de un role_id asignado a un usuario")

    def _case_gu_027_update_valid_user(self, case: Dict[str, str]) -> TestOutcome:
        user, detail = self._create_user(self._build_valid_user_payload())
        if user is None:
            return self.nok(case, f"No se pudo preparar usuario a actualizar: {detail}")
        try:
            payload = {"first_name": "Actualizado", "organization": "QA Updated"}
            status_code, response_body, request_error = self._authorized_request(
                "PUT", f"/api/v1/users/{user['id']}", body=payload
            )
            if request_error is not None:
                return self.nok(case, f"Error actualizando usuario: {request_error}")
            if status_code != 200:
                return self.nok(case, f"Actualizar usuario devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict) or response_body.get("first_name") != "Actualizado":
                return self.nok(case, f"Respuesta de actualizacion invalida: {response_body!r}")
            return self.ok(case, "Usuario actualizado correctamente")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_gu_028_update_email_to_existing(self, case: Dict[str, str]) -> TestOutcome:
        user_a, detail_a = self._create_user(self._build_valid_user_payload())
        if user_a is None:
            return self.nok(case, f"No se pudo preparar usuario A: {detail_a}")
        user_b, detail_b = self._create_user(self._build_valid_user_payload())
        if user_b is None:
            self._cleanup_user(user_a.get("id"))
            return self.nok(case, f"No se pudo preparar usuario B: {detail_b}")
        try:
            status_code, _, request_error = self._authorized_request(
                "PUT",
                f"/api/v1/users/{user_b['id']}",
                body={"email": user_a["email"]},
            )
            return self._expect_statuses(case, status_code, request_error, {400, 409, 422}, "email duplicado en update")
        finally:
            self._cleanup_user(user_a.get("id"))
            self._cleanup_user(user_b.get("id"))

    def _case_gu_029_delete_existing_user(self, case: Dict[str, str]) -> TestOutcome:
        user, detail = self._create_user(self._build_valid_user_payload())
        if user is None:
            return self.nok(case, detail)
        status_code, _, request_error = self._authorized_request("DELETE", f"/api/v1/users/{user['id']}", body=None)
        if request_error is not None:
            return self.nok(case, f"Error eliminando usuario: {request_error}")
        if status_code != 204:
            self._cleanup_user(user.get("id"))
            return self.nok(case, f"Eliminar usuario devolvió {status_code}, esperado 204")
        return self.ok(case, "Usuario eliminado correctamente")

    def _case_gu_030_delete_missing_user(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("DELETE", "/api/v1/users/99999999", body=None)
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "delete usuario inexistente")

    def _case_gu_031_get_existing_user(self, case: Dict[str, str]) -> TestOutcome:
        user, detail = self._create_user(self._build_valid_user_payload())
        if user is None:
            return self.nok(case, detail)
        try:
            status_code, response_body, request_error = self._authorized_request("GET", f"/api/v1/users/{user['id']}", body=None)
            if request_error is not None:
                return self.nok(case, f"Error consultando usuario: {request_error}")
            if status_code != 200:
                return self.nok(case, f"GET usuario devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict) or response_body.get("id") != user["id"]:
                return self.nok(case, f"Respuesta GET usuario invalida: {response_body!r}")
            return self.ok(case, "Consulta de usuario existente correcta")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_gu_032_get_missing_user(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("GET", "/api/v1/users/99999999", body=None)
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "get usuario inexistente")

    def _case_gu_033_whitespace_strings(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload(first_name="  Juan  ", last_name="  Perez  ")
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error con payload con espacios: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Payload con espacios rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                return self.ok(case, "Payload con espacios aceptado y procesado por el API")
            finally:
                self._cleanup_user(response_body.get("id"))
        return self.nok(case, f"Payload con espacios devolvió status inesperado {status_code}")

    def _case_gu_034_uppercase_email(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload(email=self._unique_email().upper())
        created_user, detail = self._create_user_and_cleanup(payload)
        if created_user is None:
            return self.nok(case, detail)
        return self.ok(case, detail)

    def _case_gu_035_case_insensitive_duplicate(self, case: Dict[str, str]) -> TestOutcome:
        email = self._unique_email()
        user, detail = self._create_user(self._build_valid_user_payload(email=email.upper()))
        if user is None:
            return self.nok(case, f"No se pudo preparar usuario base: {detail}")
        try:
            status_code, _, request_error = self._authorized_request(
                "POST", "/api/v1/users", body=self._build_valid_user_payload(email=email.lower())
            )
            return self._expect_statuses(case, status_code, request_error, {400, 409, 422}, "email duplicado case-insensitive")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_gu_037_password_not_exposed(self, case: Dict[str, str]) -> TestOutcome:
        user, detail = self._create_user(self._build_valid_user_payload())
        if user is None:
            return self.nok(case, detail)
        try:
            if "password" in user:
                return self.nok(case, "La respuesta de creacion expone el campo password")
            return self.ok(case, "La respuesta no expone password")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_gu_038_extra_payload_field(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload()
        payload["unexpected_field"] = "surplus"
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error enviando campo extra: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Campo extra rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                if "unexpected_field" in response_body:
                    return self.nok(case, "El campo extra fue persistido o devuelto por la API")
                return self.ok(case, "El campo extra fue ignorado por la API")
            finally:
                self._cleanup_user(response_body.get("id"))
        return self.nok(case, f"Campo extra devolvió status inesperado {status_code}")

    def _case_gu_036_parallel_same_email_with_locust(self, case: Dict[str, str]) -> TestOutcome:
        ok, detail = self._run_locust_scenario(
            scenario="GU-036",
            users=25,
            spawn_rate=25,
            run_time_seconds=8,
            extra_env={"LR_FIXED_EMAIL": self._unique_email()},
        )
        if not ok:
            if detail.startswith("No existe locustfile") or detail.startswith("Locust no esta instalado") or detail.startswith("Locust no generó resultado"):
                return self.warning(case, f"No se pudo ejecutar GU-036 con Locust: {detail}")
            return self.nok(case, detail)
        return self.ok(case, detail)

    def _case_gu_039_parallel_sla_load_with_locust(self, case: Dict[str, str]) -> TestOutcome:
        ok, detail = self._run_locust_scenario(
            scenario="GU-039",
            users=20,
            spawn_rate=20,
            run_time_seconds=10,
        )
        if not ok:
            return self.nok(case, detail)
        return self.ok(case, detail)

    def _case_gu_057_parallel_rate_limiting_with_locust(self, case: Dict[str, str]) -> TestOutcome:
        ok, detail = self._run_locust_scenario(
            scenario="GU-057",
            users=120,
            spawn_rate=120,
            run_time_seconds=8,
        )
        if not ok:
            if detail.startswith("No existe locustfile") or detail.startswith("Locust no esta instalado") or detail.startswith("Locust no generó resultado"):
                return self.warning(case, f"No se pudo ejecutar GU-057 con Locust: {detail}")
            return self.nok(case, detail)
        return self.ok(case, detail)

    def _case_gu_040_utf8_payload(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload(first_name="李", last_name="García")
        created_user, detail = self._create_user_and_cleanup(payload)
        if created_user is None:
            return self.nok(case, detail)
        return self.ok(case, detail)

    def _case_gu_041_users_without_token(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._request("GET", "/api/v1/users", body=None)
        return self._expect_statuses(case, status_code, request_error, {401}, "acceso anonimo a users")

    def _case_gu_046_recreate_user_after_delete(self, case: Dict[str, str]) -> TestOutcome:
        gestor_role_id, gestor_detail = self._get_or_create_gestor_role_id()
        if gestor_role_id is None:
            return self.nok(case, f"Precondición fallida — no se pudo obtener ni crear el rol 'gestor': {gestor_detail}")

        email = self._unique_email()
        payload = self._build_valid_user_payload(email=email, role_ids=[gestor_role_id])

        first_user, first_detail = self._create_user(payload)
        if first_user is None:
            return self.nok(case, f"La primera creación no devolvió 201: {first_detail}")

        first_user_id = first_user.get("id")
        if not isinstance(first_user_id, int):
            self._cleanup_user(first_user.get("id"))
            return self.nok(case, f"La primera creación devolvió 201 pero sin id válido: {first_user!r}")

        deleted_ok = False
        recreated_user: Optional[Dict[str, Any]] = None
        try:
            status_code, _, request_error = self._authorized_request("DELETE", f"/api/v1/users/{first_user_id}", body=None)
            if request_error is not None:
                return self.nok(case, f"Error eliminando usuario tras la primera creación: {request_error}")
            if status_code != 204:
                return self.nok(case, f"La eliminación del usuario devolvió {status_code}, esperado 204")
            deleted_ok = True

            recreated_user, recreate_detail = self._create_user(payload)
            if recreated_user is None:
                return self.nok(case, f"La recreación del usuario tras borrado no devolvió 201: {recreate_detail}")

            recreated_user_id = recreated_user.get("id")
            if not isinstance(recreated_user_id, int):
                return self.nok(case, f"La recreación devolvió 201 pero sin id válido: {recreated_user!r}")

            return self.ok(
                case,
                f"Primera creación 201, borrado 204 y recreación 201 correctos para el email {email}",
            )
        finally:
            if not deleted_ok:
                self._cleanup_user(first_user_id)
            if recreated_user is not None:
                self._cleanup_user(recreated_user.get("id"))

    def _case_gu_047_users_pagination(self, case: Dict[str, str]) -> TestOutcome:
        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/users?page=1&size=10", body=None)
        if request_error is not None:
            return self.nok(case, f"Error consultando paginacion: {request_error}")
        if status_code != 200:
            return self.nok(case, f"Paginacion devolvió {status_code}, esperado 200")
        if not isinstance(response_body, list):
            return self.nok(case, f"Paginacion no devolvió lista JSON: {response_body!r}")
        return self.ok(case, "Consulta paginada respondió correctamente")

    def _case_gu_048_users_filter(self, case: Dict[str, str]) -> TestOutcome:
        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/users?first_name=Juan", body=None)
        if request_error is not None:
            return self.nok(case, f"Error consultando filtro: {request_error}")
        if status_code != 200:
            return self.nok(case, f"Filtro devolvió {status_code}, esperado 200")
        if not isinstance(response_body, list):
            return self.nok(case, f"Filtro no devolvió lista JSON: {response_body!r}")
        return self.ok(case, "Consulta con filtro respondió correctamente")

    def _case_gu_049_unsupported_content_type(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request(
            "POST",
            "/api/v1/users",
            body=None,
            raw_body="<user></user>",
            content_type="application/xml",
        )
        return self._expect_statuses(case, status_code, request_error, {400, 415, 422}, "content-type no soportado")

    def _case_gu_050_malformed_json(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request(
            "POST",
            "/api/v1/users",
            body=None,
            raw_body='{"email":"bad",}',
            content_type="application/json",
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "json mal formado")

    def _case_gu_051_payload_too_large(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload(organization="O" * (10 * 1024 * 1024))
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        return self._expect_statuses(case, status_code, request_error, {413, 422}, "payload de 10MB en organization")

    def _case_gu_052_email_alias(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload(email=self._unique_email(alias=True))
        created_user, detail = self._create_user_and_cleanup(payload)
        if created_user is None:
            return self.nok(case, detail)
        return self.ok(case, detail)

    def _case_gu_053_patch_not_supported(self, case: Dict[str, str]) -> TestOutcome:
        user, detail = self._create_user(self._build_valid_user_payload())
        if user is None:
            return self.nok(case, detail)
        try:
            status_code, response_body, request_error = self._authorized_request(
                "PATCH",
                f"/api/v1/users/{user['id']}",
                body={"organization": "Solo PATCH"},
            )
            if request_error is not None:
                return self.nok(case, f"Error invocando PATCH: {request_error}")
            if status_code == 200:
                if not isinstance(response_body, dict) or response_body.get("organization") != "Solo PATCH":
                    return self.nok(case, f"PATCH respondió 200 pero no actualizó correctamente: {response_body!r}")
                return self.ok(case, "PATCH parcial soportado y aplicado correctamente")
            if status_code in {404, 405}:
                return self.nok(case, f"PATCH no soportado por el API actual: {status_code}")
            return self.nok(case, f"PATCH devolvió status inesperado {status_code}")
        finally:
            self._cleanup_user(user.get("id"))

    def _case_gu_054_invalid_ids(self, case: Dict[str, str]) -> TestOutcome:
        failures: List[str] = []
        for candidate in ("-1", "99999999"):
            for method in ("GET", "DELETE"):
                status_code, _, request_error = self._authorized_request(method, f"/api/v1/users/{candidate}", body=None)
                if request_error is not None:
                    failures.append(f"{method} {candidate}: {request_error}")
                    continue
                if status_code not in self.NOT_FOUND_STATUSES:
                    failures.append(f"{method} {candidate}: status {status_code}")
        if failures:
            return self.nok(case, " ; ".join(failures))
        return self.ok(case, "IDs inválidos rechazados correctamente")

    def _case_gu_055_nosql_injection(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._build_valid_user_payload()
        payload["email"] = {"$ne": None}
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "inyeccion NoSQL por tipos inválidos")

    def _case_gu_058_empty_body(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/users", body=None)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "body vacio")

    def _case_gu_059_security_headers(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, headers, request_error = self._authorized_request_with_headers("GET", "/api/v1/users", body=None)
        if request_error is not None:
            return self.nok(case, f"Error obteniendo headers: {request_error}")
        if status_code != 200:
            return self.nok(case, f"Consulta users para headers devolvió {status_code}, esperado 200")
        normalized_headers = {key.lower(): value for key, value in headers.items()}
        has_cors = "access-control-allow-origin" in normalized_headers
        has_hsts = "strict-transport-security" in normalized_headers
        if not (has_cors or has_hsts):
            return self.nok(case, "No se encontraron headers CORS ni HSTS en la respuesta")
        return self.ok(case, f"Headers presentes: CORS={has_cors}, HSTS={has_hsts}")

    def _case_gu_060_mixed_role_ids(self, case: Dict[str, str]) -> TestOutcome:
        gestor_role_id, gestor_detail = self._get_gestor_role_id()
        if gestor_role_id is None:
            return self.nok(case, f"No se encontró el rol gestor requerido: {gestor_detail}")
        payload = self._build_valid_user_payload(role_ids=[gestor_role_id, "admin", 3])
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "mezcla de tipos en role_ids")

    def _case_gu_005_without_role_ids_defaults_to_gestor(self, case: Dict[str, str]) -> TestOutcome:
        # Precondition: get or create the role with name "gestor" and capture its id
        gestor_role_id, gestor_detail = self._get_or_create_gestor_role_id()
        if gestor_role_id is None:
            return self.nok(case, f"Precondición fallida — no se pudo obtener ni crear el rol 'gestor': {gestor_detail}")

        # Action: create a user without role_ids in the payload
        payload = {
            "email": self._unique_email(),
            "first_name": "Test",
            "last_name": "User",
            "organization": "QA",
            "password": "Valid123",
        }
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error creando usuario sin role_ids: {request_error}")
        if status_code != 201 or not isinstance(response_body, dict):
            return self.nok(case, f"Crear usuario sin role_ids devolvió {status_code}, esperado 201")

        # Assertion: the response must include the gestor role_id
        try:
            role_ids = response_body.get("role_ids")
            if not isinstance(role_ids, list) or gestor_role_id not in role_ids:
                return self.nok(case, f"La respuesta no contiene el role_id del rol gestor ({gestor_role_id}). role_ids recibidos: {role_ids!r}")
            return self.ok(case, f"Usuario creado sin role_ids y la respuesta contiene el role_id gestor ({gestor_role_id})")
        finally:
            self._cleanup_user(response_body.get("id"))

    def _case_gu_016_empty_role_ids_defaults_to_gestor(self, case: Dict[str, str]) -> TestOutcome:
        # Precondition: get or create the role with name "gestor" and capture its id
        gestor_role_id, gestor_detail = self._get_or_create_gestor_role_id()
        if gestor_role_id is None:
            return self.nok(case, f"Precondición fallida — no se pudo obtener ni crear el rol 'gestor': {gestor_detail}")

        # Action: create a user with role_ids=[] (empty array) in the payload
        payload = {
            "email": self._unique_email(),
            "first_name": "Test",
            "last_name": "User",
            "organization": "QA",
            "password": "Valid123",
            "role_ids": [],
        }
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error creando usuario con role_ids vacío: {request_error}")
        if status_code != 201 or not isinstance(response_body, dict):
            return self.nok(case, f"Crear usuario con role_ids vacío devolvió {status_code}, esperado 201")

        # Assertion: the response must include the gestor role_id
        try:
            role_ids = response_body.get("role_ids")
            if not isinstance(role_ids, list) or gestor_role_id not in role_ids:
                return self.nok(case, f"La respuesta no contiene el role_id del rol gestor ({gestor_role_id}). role_ids recibidos: {role_ids!r}")
            return self.ok(case, f"Usuario creado con role_ids vacío y la respuesta contiene el role_id gestor ({gestor_role_id})")
        finally:
            self._cleanup_user(response_body.get("id"))

    def _case_gu_061_only_gestor_role(self, case: Dict[str, str]) -> TestOutcome:
        gestor_role_id, gestor_detail = self._get_or_create_gestor_role_id()
        if gestor_role_id is None:
            return self.nok(case, f"Precondición fallida — no se pudo obtener ni crear el rol 'gestor': {gestor_detail}")

        payload = self._build_valid_user_payload(role_ids=[gestor_role_id])
        user, detail = self._create_user(payload)
        if user is None:
            return self.nok(case, detail)
        try:
            user_id = user.get("id")
            if not isinstance(user_id, int):
                return self.nok(case, f"La creación con role_id gestor fue aceptada pero la respuesta no incluye un id válido: {user!r}")
            returned_role_ids = user.get("role_ids")
            if not isinstance(returned_role_ids, list) or gestor_role_id not in returned_role_ids:
                return self.nok(
                    case,
                    f"La creación no confirmó el role_id gestor admitido ({gestor_role_id}). role_ids recibidos: {returned_role_ids!r}",
                )
            return self.ok(case, f"El role_id gestor {gestor_role_id} fue admitido y el usuario se creó con id {user_id}")
        finally:
            self._cleanup_user(user.get("id"))

    def _validate_user_only_gestor_role(self, user: Dict[str, Any], gestor_role_id: int) -> Tuple[bool, str]:
        user_id = user.get("id")
        if not isinstance(user_id, int):
            return False, f"Respuesta de creación sin id entero de usuario: {user!r}"

        status_code, response_body, request_error = self._authorized_request("GET", f"/api/v1/users/{user_id}", body=None)
        if request_error is not None:
            return False, f"Error consultando usuario para validar roles: {request_error}"
        if status_code != 200 or not isinstance(response_body, dict):
            return False, f"GET /users/{user_id} devolvió {status_code}, esperado 200 con objeto"

        role_ids = response_body.get("role_ids")
        if isinstance(role_ids, list):
            normalized = [item for item in role_ids if isinstance(item, int)]
            if normalized != [gestor_role_id]:
                return False, f"role_ids no es exclusivamente gestor: {role_ids!r}"
            return True, "role_ids validados"

        roles = response_body.get("roles")
        if isinstance(roles, list):
            role_names = {
                str(item.get("name", "")).strip().lower()
                for item in roles
                if isinstance(item, dict)
            }
            if role_names == {"gestor"}:
                return True, "roles[].name validados"
            return False, f"roles devueltos no son exclusivamente gestor: {sorted(role_names)!r}"

        return False, f"La respuesta del usuario no incluye role_ids ni roles para validar: {response_body!r}"

    def _build_valid_user_payload(
        self,
        *,
        email: Optional[str] = None,
        first_name: str = "Test",
        last_name: str = "User",
        organization: str = "QA",
        password: str = "Valid123",
        role_ids: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        if role_ids is None:
            gestor_role_id, _ = self._get_gestor_role_id()
            role_ids = [gestor_role_id] if gestor_role_id is not None else []
        return {
            "email": email if email is not None else self._unique_email(),
            "first_name": first_name,
            "last_name": last_name,
            "organization": organization,
            "password": password,
            "role_ids": role_ids,
        }

    def _create_user_and_cleanup(self, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        user, detail = self._create_user(payload)
        if user is None:
            return None, detail
        self._cleanup_user(user.get("id"))
        return user, detail

    def _create_user(self, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if request_error is not None:
            return None, f"Error creando usuario: {request_error}"
        if status_code != 201:
            return None, f"Crear usuario devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear usuario no devolvió JSON objeto: {response_body!r}"
        self._cleanup_register(self._cleanup_user, response_body.get("id"))
        return response_body, f"Usuario creado correctamente con id {response_body.get('id')}"

    def _cleanup_user(self, user_id: Any) -> None:
        if user_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/users/{user_id}", body=None)
        except Exception:
            return

    def _get_existing_role_ids(self) -> Tuple[List[int], str]:
        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/roles", body=None)
        if request_error is not None:
            return [], f"Error consultando roles: {request_error}"
        if status_code != 200 or not isinstance(response_body, list):
            return [], f"GET /roles devolvió {status_code} con cuerpo {response_body!r}"
        role_ids = [int(item["id"]) for item in response_body if isinstance(item, dict) and "id" in item]
        return role_ids, f"Se encontraron {len(role_ids)} roles"

    def _get_gestor_role_id(self) -> Tuple[Optional[int], str]:
        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/roles", body=None)
        if request_error is not None:
            return None, f"Error consultando roles: {request_error}"
        if status_code != 200 or not isinstance(response_body, list):
            return None, f"GET /roles devolvió {status_code} con cuerpo {response_body!r}"

        for item in response_body:
            if not isinstance(item, dict) or "id" not in item:
                continue
            role_name = str(item.get("name") or "").strip().lower()
            if role_name == "gestor":
                return int(item["id"]), f"Rol gestor encontrado con id {item['id']}"
        return None, "No existe ningun rol con name 'gestor'"

    def _get_or_create_gestor_role_id(self) -> Tuple[Optional[int], str]:
        """Return the id of the role named 'gestor', creating it if it does not exist."""
        gestor_role_id, detail = self._get_gestor_role_id()
        if gestor_role_id is not None:
            return gestor_role_id, detail

        # Role not found — create it
        status_code, response_body, request_error = self._authorized_request(
            "POST", "/api/v1/roles", body={"name": "gestor"}
        )
        if request_error is not None:
            return None, f"Error creando rol gestor: {request_error}"
        if status_code == 201 and isinstance(response_body, dict) and "id" in response_body:
            return int(response_body["id"]), f"Rol gestor creado con id {response_body['id']}"
        return None, f"No se pudo crear el rol gestor: status {status_code}, respuesta {response_body!r}"

    def _get_non_gestor_role_ids(self) -> Tuple[List[int], str]:
        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/roles", body=None)
        if request_error is not None:
            return [], f"Error consultando roles: {request_error}"
        if status_code != 200 or not isinstance(response_body, list):
            return [], f"GET /roles devolvió {status_code} con cuerpo {response_body!r}"

        role_ids: List[int] = []
        for item in response_body:
            if not isinstance(item, dict) or "id" not in item:
                continue
            role_name = str(item.get("name") or "").strip().lower()
            if role_name != "gestor":
                role_ids.append(int(item["id"]))
        return role_ids, f"Se encontraron {len(role_ids)} roles no gestor"

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
        raw_body: Optional[str] = None,
        content_type: str = "application/json",
    ) -> Tuple[int, Any, Optional[str]]:
        token, login_error = self._login_seed_user()
        if login_error is not None:
            return -1, None, login_error
        status_code, response_body, request_error = self._request(
            method,
            path,
            body=body,
            extra_headers={"Authorization": f"Bearer {token}"},
            raw_body=raw_body,
            content_type=content_type,
        )
        if (
            request_error is None
            and method.upper() == "POST"
            and path == "/api/v1/users"
            and status_code == 201
            and isinstance(response_body, dict)
        ):
            self._cleanup_register(self._cleanup_user, response_body.get("id"))
        return status_code, response_body, request_error

    def _authorized_request_with_headers(
        self,
        method: str,
        path: str,
        body: Optional[Any],
    ) -> Tuple[int, Any, Dict[str, str], Optional[str]]:
        token, login_error = self._login_seed_user()
        if login_error is not None:
            return -1, None, {}, login_error
        return self._request_with_headers(
            method,
            path,
            body=body,
            extra_headers={"Authorization": f"Bearer {token}"},
        )

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Any],
        extra_headers: Optional[Dict[str, str]] = None,
        raw_body: Optional[str] = None,
        content_type: str = "application/json",
    ) -> Tuple[int, Any, Optional[str]]:
        status_code, parsed_body, _, request_error = self._request_with_headers(
            method,
            path,
            body=body,
            extra_headers=extra_headers,
            raw_body=raw_body,
            content_type=content_type,
        )
        return status_code, parsed_body, request_error

    def _request_with_headers(
        self,
        method: str,
        path: str,
        body: Optional[Any],
        extra_headers: Optional[Dict[str, str]] = None,
        raw_body: Optional[str] = None,
        content_type: str = "application/json",
    ) -> Tuple[int, Any, Dict[str, str], Optional[str]]:
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if extra_headers:
            headers.update(extra_headers)

        data: Optional[bytes] = None
        if raw_body is not None:
            data = raw_body.encode("utf-8")
            headers["Content-Type"] = content_type
        elif body is not None and method.upper() in {"POST", "PUT", "PATCH"}:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = content_type

        req = request.Request(url=url, method=method.upper(), data=data, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                status_code = int(response.status)
                response_headers = dict(response.headers.items())
                raw = response.read().decode("utf-8", errors="replace")
                return status_code, self._parse_json(raw), response_headers, None
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            response_headers = dict(exc.headers.items()) if exc.headers else {}
            return int(exc.code), self._parse_json(raw), response_headers, None
        except Exception as exc:  # pragma: no cover
            return -1, None, {}, str(exc)

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
    def _unique_email(alias: bool = False) -> str:
        unique = uuid.uuid4().hex[:12]
        local = f"qa+{unique}" if alias else f"qa.{unique}"
        return f"{local}@example.com"

    @staticmethod
    def _parse_json(raw: str) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def _run_locust_scenario(
        self,
        *,
        scenario: str,
        users: int,
        spawn_rate: int,
        run_time_seconds: int,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, str]:
        if not self.locust_file.exists():
            return False, f"No existe locustfile para carga: {self.locust_file}"

        with tempfile.TemporaryDirectory(prefix="locust-gu-") as temp_dir:
            result_file = Path(temp_dir) / "result.json"

            env = os.environ.copy()
            env.update(
                {
                    "LR_SCENARIO": scenario,
                    "LR_LOGIN_EMAIL": self.seed_email,
                    "LR_LOGIN_PASSWORD": self.seed_password,
                    "LR_RESULT_FILE": str(result_file),
                }
            )
            if extra_env:
                env.update(extra_env)

            command = [
                "locust",
                "-f",
                str(self.locust_file),
                "--host",
                self.base_url,
                "--headless",
                "-u",
                str(users),
                "-r",
                str(spawn_rate),
                "-t",
                f"{run_time_seconds}s",
                "--only-summary",
            ]

            try:
                process = subprocess.run(command, capture_output=True, text=True, env=env)
            except FileNotFoundError:
                return False, "Locust no esta instalado. Instala con: pip install locust"

            if not result_file.exists():
                stderr_tail = process.stderr.strip().splitlines()[-1] if process.stderr.strip() else "sin detalle"
                return False, f"Locust no generó resultado para {scenario}. stderr: {stderr_tail}"

            try:
                result = json.loads(result_file.read_text(encoding="utf-8"))
            except Exception as exc:
                return False, f"No se pudo leer resultado de Locust ({scenario}): {exc}"

            if process.returncode != 0:
                return False, f"Locust finalizó con código {process.returncode} en {scenario}"

            if result.get("auth_failed"):
                return False, f"Locust {scenario}: fallo de autenticacion con usuario semilla"

            status_counts = result.get("status_counts", {})
            total_requests = int(result.get("total_requests", 0))
            p95_ms = float(result.get("p95_ms", 0.0))

            if scenario == "GU-057":
                count_429 = int(status_counts.get("429", 0))
                if count_429 <= 0:
                    return False, f"GU-057 no detectó 429 (total_requests={total_requests}, status={status_counts})"
                return True, f"Locust GU-057 detectó rate limit con {count_429} respuestas 429"

            if scenario == "GU-036":
                count_201 = int(status_counts.get("201", 0))
                duplicate_failures = sum(int(status_counts.get(code, 0)) for code in ("400", "409", "422"))
                if count_201 <= 0 or duplicate_failures <= 0:
                    return False, (
                        "GU-036 no mostró concurrencia esperada para email duplicado "
                        f"(201={count_201}, conflict={duplicate_failures}, status={status_counts})"
                    )
                return True, (
                    "Locust GU-036 válido concurrencia en email duplicado "
                    f"(201={count_201}, conflict={duplicate_failures})"
                )

            if scenario == "GU-039":
                if total_requests <= 0:
                    return False, "GU-039 no ejecuto requests"
                if p95_ms > 1000.0:
                    return False, f"GU-039 excede SLA p95={p95_ms:.2f}ms (>1000ms)"
                return True, f"Locust GU-039 cumple SLA con p95={p95_ms:.2f}ms"

            return False, f"Escenario Locust no soportado: {scenario}"