from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome
from tests.test_data_loader import TestDataLoader

_DATA_FILE = Path(__file__).resolve().parent.parent / "test_data" / "gr_case_data.json"


class RoleManagementScopeTests(BaseScopeTests):
    """Implements GR-* test cases for role management and user-role integrity checks."""

    VALIDATION_STATUSES = {400, 409, 422}
    NOT_FOUND_STATUSES = {400, 404, 422}

    def __init__(self, base_url: str, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._loader = TestDataLoader(_DATA_FILE)
        seed_login = self._loader.get_default("seed_login", {})
        self.seed_email = str(seed_login.get("email", "admin@newsradar.com"))
        self.seed_password = str(seed_login.get("password", "admin123"))

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        self._cleanup_reset()
        try:
            return self._run_case_impl(case)
        finally:
            self._cleanup_run()

    def _run_case_impl(self, case: Dict[str, str]) -> TestOutcome:
        case_id = str(case.get("Caso de Prueba", "")).strip().upper()

        if case_id == "GR-001":
            return self._case_gr_001_create_valid_role(case)
        if case_id == "GR-002":
            return self._case_gr_002_create_role_without_name(case)
        if case_id == "GR-003":
            return self._case_gr_003_name_empty(case)
        if case_id == "GR-004":
            return self._case_gr_004_name_min_length_invalid(case)
        if case_id == "GR-005":
            return self._case_gr_005_name_max_length_exceeded(case)
        if case_id == "GR-006":
            return self._case_gr_006_name_whitespace(case)
        if case_id == "GR-007":
            return self._case_gr_007_name_special_chars_valid(case)
        if case_id == "GR-008":
            return self._case_gr_008_name_invalid_chars(case)
        if case_id == "GR-009":
            return self._case_gr_009_duplicate_exact_name(case)
        if case_id == "GR-010":
            return self._case_gr_010_duplicate_case_insensitive(case)
        if case_id == "GR-011":
            return self._case_gr_011_trim_duplicate(case)
        if case_id == "GR-012":
            return self._case_gr_012_update_valid_role(case)
        if case_id == "GR-013":
            return self._case_gr_013_update_to_existing_name(case)
        if case_id == "GR-014":
            return self._case_gr_014_delete_role_without_dependencies(case)
        if case_id == "GR-015":
            return self._case_gr_015_delete_role_with_users(case)
        if case_id == "GR-016":
            return self._case_gr_016_delete_nonexistent_role(case)
        if case_id == "GR-017":
            return self._case_gr_017_get_existing_role(case)
        if case_id == "GR-018":
            return self._case_gr_018_get_nonexistent_role(case)
        if case_id == "GR-019":
            return self._case_gr_019_utf8_name(case)
        if case_id == "GR-020":
            return self._case_gr_020_name_normalization(case)
        if case_id == "GR-021":
            return self._case_gr_021_response_schema(case)
        if case_id == "GR-022":
            return self._case_gr_022_assign_existing_role_to_user(case)
        if case_id == "GR-023":
            return self._case_gr_023_assign_nonexistent_role_to_user(case)
        if case_id == "GR-024":
            return self._case_gr_024_update_user_with_nonexistent_role(case)
        if case_id == "GR-025":
            return self._case_gr_025_delete_referenced_role_consistency(case)
        if case_id == "GR-026":
            return self._case_gr_026_delete_user_then_free_role(case)
        if case_id == "GR-027":
            return self._case_gr_027_get_user_and_verify_roles(case)
        if case_id == "GR-028":
            return self._case_gr_028_create_user_with_one_invalid_role(case)
        if case_id == "GR-029":
            return self._case_gr_029_transaction_consistency(case)

        return self.nok(case, f"Caso GR no implementado: {case_id}")

    def _case_gr_001_create_valid_role(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        self._cleanup_role(role.get("id"))
        return self.ok(case, detail)

    def _case_gr_002_create_role_without_name(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/roles", body={})
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "crear rol sin name")

    def _case_gr_003_name_empty(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/roles", body={"name": ""})
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name vacio")

    def _case_gr_004_name_min_length_invalid(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/roles", body={"name": ""})
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name longitud minima")

    def _case_gr_005_name_max_length_exceeded(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request(
            "POST",
            "/api/v1/roles",
            body={"name": self._default_string("name_too_long", "R" * 101)},
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name longitud maxima")

    def _case_gr_006_name_whitespace(self, case: Dict[str, str]) -> TestOutcome:
        status_code, response_body, request_error = self._authorized_request(
            "POST",
            "/api/v1/roles",
            body={"name": self._default_string("whitespace_role_name", "   ")},
        )
        if request_error is not None:
            return self.nok(case, f"Error creando rol con whitespace: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Whitespace rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                role_name = str(response_body.get("name", ""))
                if role_name.strip() == "":
                    return self.nok(case, "Name con solo espacios fue persistido")
                return self.ok(case, "Name con espacios fue normalizado por el API")
            finally:
                self._cleanup_role(response_body.get("id"))
        return self.nok(case, f"Status inesperado para whitespace: {status_code}")

    def _case_gr_007_name_special_chars_valid(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._default_string("utf8_role_name_primary", "Rol Ánalisis-Ñ"))
        if role is None:
            return self.nok(case, detail)
        self._cleanup_role(role.get("id"))
        return self.ok(case, detail)

    def _case_gr_008_name_invalid_chars(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request(
            "POST",
            "/api/v1/roles",
            body={"name": self._default_string("invalid_role_name", "role\nname")},
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name con caracteres inválidos")

    def _case_gr_009_duplicate_exact_name(self, case: Dict[str, str]) -> TestOutcome:
        name = self._unique_role_name()
        role, detail = self._create_role(name)
        if role is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request("POST", "/api/v1/roles", body={"name": name})
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "name duplicado exacto")
        finally:
            self._cleanup_role(role.get("id"))

    def _case_gr_010_duplicate_case_insensitive(self, case: Dict[str, str]) -> TestOutcome:
        base_name = self._unique_role_name(prefix="RoleCase")
        role, detail = self._create_role(base_name.upper())
        if role is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request("POST", "/api/v1/roles", body={"name": base_name.lower()})
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado case-insensitive")
        finally:
            self._cleanup_role(role.get("id"))

    def _case_gr_011_trim_duplicate(self, case: Dict[str, str]) -> TestOutcome:
        name = self._unique_role_name(prefix="RoleTrim")
        role, detail = self._create_role(name)
        if role is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request("POST", "/api/v1/roles", body={"name": f" {name} "})
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado por trim")
        finally:
            self._cleanup_role(role.get("id"))

    def _case_gr_012_update_valid_role(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        try:
            new_name = self._unique_role_name(prefix="UpdatedRole")
            status_code, response_body, request_error = self._authorized_request(
                "PUT", f"/api/v1/roles/{role['id']}", body={"name": new_name}
            )
            if request_error is not None:
                return self.nok(case, f"Error actualizando rol: {request_error}")
            if status_code != 200:
                return self.nok(case, f"Actualizar rol devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict) or response_body.get("name") != new_name:
                return self.nok(case, f"Respuesta de update inválida: {response_body!r}")
            return self.ok(case, "Rol actualizado correctamente")
        finally:
            self._cleanup_role(role.get("id"))

    def _case_gr_013_update_to_existing_name(self, case: Dict[str, str]) -> TestOutcome:
        role_a, detail_a = self._create_role(self._unique_role_name(prefix="RoleA"))
        if role_a is None:
            return self.nok(case, detail_a)
        role_b, detail_b = self._create_role(self._unique_role_name(prefix="RoleB"))
        if role_b is None:
            self._cleanup_role(role_a.get("id"))
            return self.nok(case, detail_b)
        try:
            status_code, _, request_error = self._authorized_request(
                "PUT", f"/api/v1/roles/{role_b['id']}", body={"name": role_a["name"]}
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "update a nombre existente")
        finally:
            self._cleanup_role(role_a.get("id"))
            self._cleanup_role(role_b.get("id"))

    def _case_gr_014_delete_role_without_dependencies(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        status_code, _, request_error = self._authorized_request("DELETE", f"/api/v1/roles/{role['id']}", body=None)
        if request_error is not None:
            return self.nok(case, f"Error borrando rol: {request_error}")
        if status_code != 204:
            self._cleanup_role(role.get("id"))
            return self.nok(case, f"Delete de rol devolvió {status_code}, esperado 204")
        return self.ok(case, "Rol eliminado correctamente")

    def _case_gr_015_delete_role_with_users(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        user, user_detail = self._create_user_with_roles([int(role["id"])])
        if user is None:
            self._cleanup_role(role.get("id"))
            return self.nok(case, f"No se pudo preparar usuario con rol: {user_detail}")
        try:
            status_code, _, request_error = self._authorized_request("DELETE", f"/api/v1/roles/{role['id']}", body=None)
            return self._expect_statuses(case, status_code, request_error, {400, 409, 422}, "delete rol en uso")
        finally:
            self._cleanup_user(user.get("id"))
            self._cleanup_role(role.get("id"))

    def _case_gr_016_delete_nonexistent_role(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request(
            "DELETE", f"/api/v1/roles/{self._nonexistent_id()}", body=None
        )
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "delete rol inexistente")

    def _case_gr_017_get_existing_role(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        try:
            status_code, response_body, request_error = self._authorized_request("GET", f"/api/v1/roles/{role['id']}", body=None)
            if request_error is not None:
                return self.nok(case, f"Error consultando rol: {request_error}")
            if status_code != 200:
                return self.nok(case, f"GET rol devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict) or response_body.get("id") != role["id"]:
                return self.nok(case, f"Respuesta GET rol inválida: {response_body!r}")
            return self.ok(case, "Consulta de rol existente correcta")
        finally:
            self._cleanup_role(role.get("id"))

    def _case_gr_018_get_nonexistent_role(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("GET", f"/api/v1/roles/{self._nonexistent_id()}", body=None)
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "get rol inexistente")

    def _case_gr_019_utf8_name(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._default_string("utf8_role_name_secondary", "Rol Gestión Ñ"))
        if role is None:
            return self.nok(case, detail)
        self._cleanup_role(role.get("id"))
        return self.ok(case, detail)

    def _case_gr_020_name_normalization(self, case: Dict[str, str]) -> TestOutcome:
        name = self._unique_role_name(prefix="NormRole")
        role, detail = self._create_role(name.upper())
        if role is None:
            return self.nok(case, detail)
        try:
            status_code, response_body, request_error = self._authorized_request("GET", f"/api/v1/roles/{role['id']}", body=None)
            if request_error is not None:
                return self.nok(case, f"Error verificando normalización: {request_error}")
            if status_code != 200 or not isinstance(response_body, dict):
                return self.nok(case, f"No se pudo verificar normalización: {status_code} {response_body!r}")
            stored_name = str(response_body.get("name", "")).strip()
            if not stored_name:
                return self.nok(case, "Name almacenado vacio tras normalización")
            return self.ok(case, f"normalización consistente, name almacenado='{stored_name}'")
        finally:
            self._cleanup_role(role.get("id"))

    def _case_gr_021_response_schema(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        try:
            expected_keys = {"id", "name"}
            actual_keys = set(role.keys())
            if not expected_keys.issubset(actual_keys):
                return self.nok(case, f"Response schema incompleto: keys={sorted(actual_keys)}")
            return self.ok(case, "Contrato de respuesta para Role es correcto")
        finally:
            self._cleanup_role(role.get("id"))

    def _case_gr_022_assign_existing_role_to_user(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        user, user_detail = self._create_user_with_roles([int(role["id"])])
        if user is None:
            self._cleanup_role(role.get("id"))
            return self.nok(case, user_detail)
        try:
            role_ids = user.get("role_ids", []) if isinstance(user, dict) else []
            if int(role["id"]) not in [int(x) for x in role_ids if isinstance(x, int)]:
                return self.nok(case, f"Usuario creado sin rol esperado. role_ids={role_ids!r}")
            return self.ok(case, "Relacion usuario-rol creada correctamente")
        finally:
            self._cleanup_user(user.get("id"))
            self._cleanup_role(role.get("id"))

    def _case_gr_023_assign_nonexistent_role_to_user(self, case: Dict[str, str]) -> TestOutcome:
        case_data = self._loader.get_case_data("GR-023")
        invalid_role_ids = case_data.get("invalid_role_ids", [self._nonexistent_id()])
        status_code, _, request_error = self._authorized_request(
            "POST", "/api/v1/users", body=self._build_user_payload(role_ids=invalid_role_ids)
        )
        return self._expect_statuses(case, status_code, request_error, {400, 404, 422}, "asignar rol inexistente")

    def _case_gr_024_update_user_with_nonexistent_role(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        user, user_detail = self._create_user_with_roles([int(role["id"])])
        if user is None:
            self._cleanup_role(role.get("id"))
            return self.nok(case, user_detail)
        try:
            case_data = self._loader.get_case_data("GR-024")
            invalid_role_ids = case_data.get("invalid_role_ids", [self._nonexistent_id()])
            status_code, _, request_error = self._authorized_request(
                "PUT", f"/api/v1/users/{user['id']}", body={"role_ids": invalid_role_ids}
            )
            return self._expect_statuses(case, status_code, request_error, {400, 404, 422}, "update con rol inexistente")
        finally:
            self._cleanup_user(user.get("id"))
            self._cleanup_role(role.get("id"))

    def _case_gr_025_delete_referenced_role_consistency(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        user, user_detail = self._create_user_with_roles([int(role["id"])])
        if user is None:
            self._cleanup_role(role.get("id"))
            return self.nok(case, user_detail)
        try:
            status_code, _, request_error = self._authorized_request("DELETE", f"/api/v1/roles/{role['id']}", body=None)
            if request_error is not None:
                return self.nok(case, f"Error borrando rol referenciado: {request_error}")

            get_status, get_user_body, get_error = self._authorized_request("GET", f"/api/v1/users/{user['id']}", body=None)
            if get_error is not None:
                return self.nok(case, f"Error verificando consistencia de usuario: {get_error}")

            if status_code in {400, 409, 422} and get_status == 200:
                return self.ok(case, "Integridad protegida: rol no se borra si esta referenciado")
            if status_code == 204 and get_status == 200 and isinstance(get_user_body, dict):
                role_ids = get_user_body.get("role_ids", [])
                if int(role["id"]) in [x for x in role_ids if isinstance(x, int)]:
                    return self.nok(case, "Rol borrado pero referencia sigue en usuario")
                return self.ok(case, "Consistencia mantenida tras borrado controlado")

            return self.nok(case, f"Comportamiento inesperado delete={status_code}, get_user={get_status}")
        finally:
            self._cleanup_user(user.get("id"))
            self._cleanup_role(role.get("id"))

    def _case_gr_026_delete_user_then_free_role(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        user, user_detail = self._create_user_with_roles([int(role["id"])])
        if user is None:
            self._cleanup_role(role.get("id"))
            return self.nok(case, user_detail)

        delete_user_status, _, delete_user_error = self._authorized_request("DELETE", f"/api/v1/users/{user['id']}", body=None)
        if delete_user_error is not None or delete_user_status != 204:
            self._cleanup_user(user.get("id"))
            self._cleanup_role(role.get("id"))
            return self.nok(case, f"No se pudo borrar usuario previo ({delete_user_status}): {delete_user_error}")

        delete_role_status, _, delete_role_error = self._authorized_request("DELETE", f"/api/v1/roles/{role['id']}", body=None)
        if delete_role_error is not None:
            self._cleanup_role(role.get("id"))
            return self.nok(case, f"Error borrando rol tras borrar usuario: {delete_role_error}")
        if delete_role_status != 204:
            self._cleanup_role(role.get("id"))
            return self.nok(case, f"Delete rol tras borrar usuario devolvió {delete_role_status}, esperado 204")
        return self.ok(case, "Rol liberado correctamente tras borrar usuario")

    def _case_gr_027_get_user_and_verify_roles(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        user, user_detail = self._create_user_with_roles([int(role["id"])])
        if user is None:
            self._cleanup_role(role.get("id"))
            return self.nok(case, user_detail)
        try:
            status_code, response_body, request_error = self._authorized_request("GET", f"/api/v1/users/{user['id']}", body=None)
            if request_error is not None:
                return self.nok(case, f"Error consultando usuario: {request_error}")
            if status_code != 200 or not isinstance(response_body, dict):
                return self.nok(case, f"GET usuario devolvió {status_code} con body {response_body!r}")
            role_ids = response_body.get("role_ids", [])
            if int(role["id"]) not in [int(x) for x in role_ids if isinstance(x, int)]:
                return self.nok(case, f"Rol esperado no encontrado en usuario: {role_ids!r}")
            return self.ok(case, "Usuario devuelve los roles asociados correctamente")
        finally:
            self._cleanup_user(user.get("id"))
            self._cleanup_role(role.get("id"))

    def _case_gr_028_create_user_with_one_invalid_role(self, case: Dict[str, str]) -> TestOutcome:
        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        try:
            case_data = self._loader.get_case_data("GR-028")
            invalid_role_id = int(case_data.get("invalid_role_id", self._nonexistent_id()))
            status_code, _, request_error = self._authorized_request(
                "POST", "/api/v1/users", body=self._build_user_payload(role_ids=[int(role["id"]), invalid_role_id])
            )
            return self._expect_statuses(case, status_code, request_error, {400, 404, 422}, "mezcla de role_ids válidos e inválidos")
        finally:
            self._cleanup_role(role.get("id"))

    def _case_gr_029_transaction_consistency(self, case: Dict[str, str]) -> TestOutcome:
        email = self._unique_email()
        case_data = self._loader.get_case_data("GR-029")
        invalid_role_ids = case_data.get("invalid_role_ids", [self._nonexistent_id()])
        invalid_payload = self._build_user_payload(email=email, role_ids=invalid_role_ids)
        invalid_status, _, invalid_error = self._authorized_request("POST", "/api/v1/users", body=invalid_payload)
        if invalid_error is not None:
            return self.nok(case, f"Error en create inválido para rollback: {invalid_error}")
        if invalid_status not in {400, 404, 422}:
            return self.nok(case, f"Create inválido devolvió {invalid_status}, esperado error de integridad")

        role, detail = self._create_role(self._unique_role_name())
        if role is None:
            return self.nok(case, detail)
        valid_payload = self._build_user_payload(email=email, role_ids=[int(role["id"])])
        valid_user, valid_detail = self._create_user(valid_payload)
        if valid_user is None:
            self._cleanup_role(role.get("id"))
            return self.nok(case, f"No hubo rollback consistente (create válido fallo): {valid_detail}")

        self._cleanup_user(valid_user.get("id"))
        self._cleanup_role(role.get("id"))
        return self.ok(case, "Rollback consistente: intento inválido no dejo estado parcial")

    def _create_role(self, name: str) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/roles", body={"name": name})
        if request_error is not None:
            return None, f"Error creando rol: {request_error}"
        if status_code != 201:
            return None, f"Crear rol devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear rol no devolvió objeto JSON: {response_body!r}"
        self._cleanup_register(self._cleanup_role, response_body.get("id"))
        return response_body, f"Rol creado correctamente con id {response_body.get('id')}"

    def _create_user_with_roles(self, role_ids: List[int]) -> Tuple[Optional[Dict[str, Any]], str]:
        return self._create_user(self._build_user_payload(role_ids=role_ids))

    def _create_user(self, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/users", body=payload)
        if request_error is not None:
            return None, f"Error creando usuario: {request_error}"
        if status_code != 201:
            return None, f"Crear usuario devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear usuario no devolvió objeto JSON: {response_body!r}"
        self._cleanup_register(self._cleanup_user, response_body.get("id"))
        return response_body, f"Usuario creado correctamente con id {response_body.get('id')}"

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

    def _build_user_payload(
        self,
        *,
        email: Optional[str] = None,
        role_ids: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        defaults = self._loader.get_default("create_user_payload", {})
        return {
            "email": email or self._unique_email(),
            "first_name": defaults.get("first_name", "Role"),
            "last_name": defaults.get("last_name", "Tester"),
            "organization": defaults.get("organization", "QA"),
            "password": defaults.get("password", "Valid123"),
            "role_ids": list(role_ids) if role_ids is not None else list(defaults.get("role_ids", [])),
        }

    def _default_string(self, key: str, fallback: str) -> str:
        strings = self._loader.get_default("strings", {})
        return str(strings.get(key, fallback))

    def _nonexistent_id(self) -> int:
        ids = self._loader.get_default("ids", {})
        try:
            return int(ids.get("nonexistent", 99999999))
        except Exception:
            return 99999999

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
        if request_error is None and method.upper() == "POST" and status_code == 201 and isinstance(response_body, dict):
            if path == "/api/v1/roles":
                self._cleanup_register(self._cleanup_role, response_body.get("id"))
            elif path == "/api/v1/users":
                self._cleanup_register(self._cleanup_user, response_body.get("id"))
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
    def _unique_email() -> str:
        unique = uuid.uuid4().hex[:12]
        return f"gr.{unique}@example.com"

    @staticmethod
    def _unique_role_name(prefix: str = "Role") -> str:
        unique = uuid.uuid4().hex[:8]
        return f"{prefix}_{unique}"

    @staticmethod
    def _parse_json(raw: str) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
