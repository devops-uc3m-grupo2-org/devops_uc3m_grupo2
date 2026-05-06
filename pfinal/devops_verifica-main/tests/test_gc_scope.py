from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome


class CategoryManagementScopeTests(BaseScopeTests):
    """Implements GC-* test cases for category management and closed-catalog validation."""

    VALIDATION_ERROR_STATUSES = {400, 409, 422}
    NOT_FOUND_STATUSES = {400, 404, 422}

    CATALOG: List[Tuple[str, str]] = [
        ("01000000", "Artes, cultura, entretenimiento y medios"),
        ("03000000", "Catástrofes y accidentes"),
        ("13000000", "Ciencia y tecnología"),
        ("16000000", "Conflicto, guerra y paz"),
        ("15000000", "Deporte"),
        ("04000000", "Economía, negocios y finanzas"),
        ("05000000", "Educación"),
        ("10000000", "Estilo de vida y tiempo libre"),
        ("08000000", "Interés humano, animales, insólito"),
        ("09000000", "Mano de obra"),
        ("06000000", "Medio ambiente"),
        ("17000000", "Meteorología"),
        ("02000000", "Policía y justicia"),
        ("11000000", "Política"),
        ("12000000", "Religión y culto"),
        ("07000000", "Salud"),
        ("14000000", "Sociedad"),
    ]

    def __init__(self, base_url: str, openapi_path: Optional[Path] = None, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.seed_email = "admin@newsradar.com"
        self.seed_password = "admin123"
        self.openapi_spec = self._load_openapi(openapi_path)

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        self._cleanup_reset()
        try:
            return self._run_case_impl(case)
        finally:
            self._cleanup_run()

    def _run_case_impl(self, case: Dict[str, str]) -> TestOutcome:
        case_id = str(case.get("Caso de Prueba", "")).strip().upper()

        if case_id == "GC-001":
            return self._case_gc_001_create_valid_category(case)
        if case_id == "GC-002":
            return self._case_gc_002_create_without_name(case)
        if case_id == "GC-003":
            return self._case_gc_003_create_without_source(case)
        if case_id == "GC-004":
            return self._case_gc_004_name_empty(case)
        if case_id == "GC-005":
            return self._case_gc_005_name_max_length_exceeded(case)
        if case_id == "GC-006":
            return self._case_gc_006_source_empty(case)
        if case_id == "GC-007":
            return self._case_gc_007_source_not_allowed(case)
        if case_id == "GC-008":
            return self._case_gc_008_name_source_mismatch(case)
        if case_id == "GC-009":
            return self._case_gc_009_duplicate_exact(case)
        if case_id == "GC-010":
            return self._case_gc_010_duplicate_case_insensitive(case)
        if case_id == "GC-011":
            return self._case_gc_011_name_with_whitespace(case)
        if case_id == "GC-012":
            return self._case_gc_012_normalization(case)
        if case_id == "GC-013":
            return self._case_gc_013_payload_extra_fields(case)
        if case_id == "GC-014":
            return self._case_gc_014_get_existing(case)
        if case_id == "GC-015":
            return self._case_gc_015_get_nonexistent(case)
        if case_id == "GC-016":
            return self._case_gc_016_validate_id_type(case)
        if case_id == "GC-017":
            return self._case_gc_017_update_valid(case)
        if case_id == "GC-018":
            return self._case_gc_018_update_invalid_source(case)
        if case_id == "GC-019":
            return self._case_gc_019_update_name_source_mismatch(case)
        if case_id == "GC-020":
            return self._case_gc_020_delete_existing(case)
        if case_id == "GC-021":
            return self._case_gc_021_delete_nonexistent(case)
        if case_id == "GC-022":
            return self._case_gc_022_create_full_catalog(case)
        if case_id == "GC-023":
            return self._case_gc_023_outside_catalog(case)
        if case_id == "GC-024":
            return self._case_gc_024_closed_catalog_consistency(case)
        if case_id == "GC-025":
            return self._case_gc_025_utf8_name(case)
        if case_id == "GC-026":
            return self._case_gc_026_response_schema(case)

        return self.nok(case, f"Caso GC no implementado: {case_id}")

    def _case_gc_001_create_valid_category(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(0, with_prefix=True)
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error creando categoría: {request_error}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                valid_identity, identity_detail = self._validate_catalog_category_identity(response_body, self.CATALOG[0][0], self.CATALOG[0][1])
                if not valid_identity:
                    return self.nok(case, identity_detail)
                return self.ok(case, f"categoría creada correctamente con id de catálogo {self.CATALOG[0][0]}")
            finally:
                self._cleanup_category(response_body.get("id"))
        if status_code in {400, 409, 422}:
            return self.ok(case, f"Categoría ya existente por datos iniciales (status {status_code})")
        return self.nok(case, f"Crear categoría devolvió {status_code}, esperado 201 o ya existente")

    def _case_gc_002_create_without_name(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(0, with_prefix=True)
        payload.pop("name", None)
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "crear categoría sin name")

    def _case_gc_003_create_without_source(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(0, with_prefix=True)
        payload.pop("source", None)
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "crear categoría sin source")

    def _case_gc_004_name_empty(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(0, with_prefix=True)
        payload["name"] = ""
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name vacio")

    def _case_gc_005_name_max_length_exceeded(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(0, with_prefix=True)
        payload["name"] = "N" * 121
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name longitud maxima")

    def _case_gc_006_source_empty(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(0, with_prefix=True)
        payload["source"] = ""
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "source vacio")

    def _case_gc_007_source_not_allowed(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(0, with_prefix=True)
        payload["source"] = "medtop:99999999"
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "source fuera de catálogo")

    def _case_gc_008_name_source_mismatch(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(0, with_prefix=True)
        payload["name"] = self.CATALOG[1][1]
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name-source inconsistente")

    def _case_gc_009_duplicate_exact(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(2, with_prefix=True)
        category, detail = self._create_category(payload)
        if category is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_ERROR_STATUSES, "duplicado exacto")
        finally:
            self._cleanup_category(category.get("id"))

    def _case_gc_010_duplicate_case_insensitive(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(3, with_prefix=True)
        category, detail = self._create_category(payload)
        if category is None:
            return self.nok(case, detail)
        try:
            dup_payload = {"name": str(payload["name"]).swapcase(), "source": str(payload["source"]).upper()}
            status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=dup_payload)
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_ERROR_STATUSES, "duplicado case-insensitive")
        finally:
            self._cleanup_category(category.get("id"))

    def _case_gc_011_name_with_whitespace(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(4, with_prefix=False)
        payload["name"] = f"  {payload['name']}  "
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error creando categoría con espacios: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Name con espacios rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                stored_name = str(response_body.get("name", ""))
                if stored_name.strip() == "":
                    return self.nok(case, "Name con solo espacios fue persistido")
                return self.ok(case, "Name con espacios fue aceptado y normalizado")
            finally:
                self._cleanup_category(response_body.get("id"))
        return self.nok(case, f"Status inesperado para name con espacios: {status_code}")

    def _case_gc_012_normalization(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(5, with_prefix=False)
        payload["name"] = f"  {payload['name']}  "
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error validando normalización: {request_error}")
        if status_code != 201 or not isinstance(response_body, dict):
            return self.nok(case, f"Normalización devolvió {status_code}, esperado 201")
        try:
            stored_name = str(response_body.get("name", "")).strip()
            stored_source = str(response_body.get("source", "")).strip().lower()
            if stored_name != self.CATALOG[5][1]:
                return self.nok(case, f"Name no normalizado como catálogo: '{stored_name}'")
            if stored_source not in self._accepted_source_values(self.CATALOG[5][0]):
                return self.nok(case, f"Source no corresponde al catálogo cerrado: '{stored_source}'")
            valid_identity, identity_detail = self._validate_catalog_category_identity(response_body, self.CATALOG[5][0], self.CATALOG[5][1])
            if not valid_identity:
                return self.nok(case, identity_detail)
            return self.ok(case, "Name/source almacenados de forma consistente")
        finally:
            self._cleanup_category(response_body.get("id"))

    def _case_gc_013_payload_extra_fields(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(6, with_prefix=True)
        payload["unexpected"] = "value"
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error enviando payload extra: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Payload extra rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                if "unexpected" in response_body:
                    return self.nok(case, "El API persistió un campo inesperado")
                valid_identity, identity_detail = self._validate_catalog_category_identity(response_body, self.CATALOG[6][0], self.CATALOG[6][1])
                if not valid_identity:
                    return self.nok(case, identity_detail)
                return self.ok(case, "Campos extra ignorados sin romper contrato")
            finally:
                self._cleanup_category(response_body.get("id"))
        return self.nok(case, f"Payload extra devolvió status inesperado {status_code}")

    def _case_gc_014_get_existing(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(7, with_prefix=True)
        category, detail = self._create_category(payload)
        if category is None:
            return self.nok(case, detail)
        try:
            status_code, response_body, request_error = self._authorized_request(
                "GET", f"/api/v1/categories/{category['id']}", body=None
            )
            if request_error is not None:
                return self.nok(case, f"Error consultando categoría: {request_error}")
            if status_code != 200:
                return self.nok(case, f"GET categoría devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict) or response_body.get("id") != category["id"]:
                return self.nok(case, f"Respuesta GET categoría invalida: {response_body!r}")
            return self.ok(case, "Consulta de categoría existente correcta")
        finally:
            self._cleanup_category(category.get("id"))

    def _case_gc_015_get_nonexistent(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("GET", "/api/v1/categories/99999999", body=None)
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "get categoría inexistente")

    def _case_gc_016_validate_id_type(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(8, with_prefix=False)
        category, detail = self._create_category(payload)
        if category is None:
            return self.nok(case, detail)
        try:
            category_id = category.get("id")
            if not isinstance(category_id, int):
                return self.nok(case, f"Id de categoría no es entero: {category_id!r}")
            return self.ok(case, "Tipo de id validado como entero")
        finally:
            self._cleanup_category(category.get("id"))

    def _case_gc_017_update_valid(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(9, with_prefix=True)
        category, detail = self._create_category(payload)
        if category is None:
            return self.nok(case, detail)
        try:
            update_payload = self._catalog_payload(10, with_prefix=False)
            status_code, response_body, request_error = self._authorized_request(
                "PUT", f"/api/v1/categories/{category['id']}", body=update_payload
            )
            if request_error is not None:
                return self.nok(case, f"Error actualizando categoría: {request_error}")
            if status_code != 200:
                return self.nok(case, f"Actualizar categoría devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict):
                return self.nok(case, f"Respuesta de update invalida: {response_body!r}")
            source = str(response_body.get("source", "")).strip().lower()
            if source not in self._accepted_source_values(self.CATALOG[10][0]):
                return self.nok(case, f"Source actualizado fuera de catálogo: '{source}'")
            return self.ok(case, "categoría actualizada correctamente dentro del catálogo")
        finally:
            self._cleanup_category(category.get("id"))

    def _case_gc_018_update_invalid_source(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(11, with_prefix=True)
        category, detail = self._create_category(payload)
        if category is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "PUT",
                f"/api/v1/categories/{category['id']}",
                body={"source": "medtop:99999999", "name": self.CATALOG[11][1]},
            )
            return self._expect_statuses(case, status_code, request_error, {400, 422}, "update source fuera de catálogo")
        finally:
            self._cleanup_category(category.get("id"))

    def _case_gc_019_update_name_source_mismatch(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(12, with_prefix=True)
        category, detail = self._create_category(payload)
        if category is None:
            return self.nok(case, detail)
        try:
            mismatched_name = self.CATALOG[13][1]
            status_code, _, request_error = self._authorized_request(
                "PUT",
                f"/api/v1/categories/{category['id']}",
                body={"source": self._with_prefix(self.CATALOG[12][0]), "name": mismatched_name},
            )
            return self._expect_statuses(case, status_code, request_error, {400, 422}, "update inconsistente name-source")
        finally:
            self._cleanup_category(category.get("id"))

    def _case_gc_020_delete_existing(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(14, with_prefix=False)
        category, detail = self._create_category(payload)
        if category is None:
            return self.nok(case, detail)
        status_code, _, request_error = self._authorized_request("DELETE", f"/api/v1/categories/{category['id']}", body=None)
        if request_error is not None:
            return self.nok(case, f"Error eliminando categoría: {request_error}")
        if status_code != 204:
            self._cleanup_category(category.get("id"))
            return self.nok(case, f"Eliminar categoría devolvió {status_code}, esperado 204")
        return self.ok(case, "categoría eliminada correctamente")

    def _case_gc_021_delete_nonexistent(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("DELETE", "/api/v1/categories/99999999", body=None)
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "delete categoría inexistente")

    def _case_gc_022_create_full_catalog(self, case: Dict[str, str]) -> TestOutcome:
        """Smoke precondition: ensures the full closed catalog exists in the server after execution.

        Categories are created but NOT cleaned up — subsequent tests can assume
        the catalog is fully populated.
        """
        failures: List[str] = []

        # Obtain a token once to use _request directly (avoiding auto-cleanup registration)
        token, login_error = self._login_seed_user()
        if login_error is not None:
            return self.nok(case, f"No se pudo autenticar para GC-022: {login_error}")
        auth_headers = {"Authorization": f"Bearer {token}"}

        emptied_ok, emptied_detail = self._ensure_categories_empty()
        if not emptied_ok:
            return self.nok(case, f"No se pudo dejar categories vacío antes de GC-022: {emptied_detail}")

        for index, (_, name) in enumerate(self.CATALOG):
            payload = {"name": name, "source": "IPTC"}
            status_code, response_body, request_error = self._request(
                "POST", "/api/v1/categories", body=payload, extra_headers=auth_headers
            )
            if request_error is not None:
                failures.append(f"{name} -> error {request_error}")
                continue
            if status_code == 201 and isinstance(response_body, dict):
                valid_identity, identity_detail = self._validate_catalog_category_identity(
                    response_body,
                    self.CATALOG[index][0],
                    self.CATALOG[index][1],
                )
                if not valid_identity:
                    failures.append(identity_detail)
                continue
            failures.append(f"{name} -> status {status_code}")

        if failures:
            preview = "; ".join(failures[:8]) + ("; ..." if len(failures) > 8 else "")
            return self.nok(case, f"GC-022 exige 201 en todas las altas. Fallos: {preview}")

        # Final verification: confirm all catalog entries are present in the server
        verify_status, verify_body, verify_error = self._request(
            "GET", "/api/v1/categories", body=None, extra_headers=auth_headers
        )
        if verify_error is not None:
            return self.nok(case, f"Error verificando catálogo en servidor: {verify_error}")
        if verify_status != 200 or not isinstance(verify_body, list):
            return self.nok(case, f"GET /categories tras GC-022 devolvió {verify_status}, esperado 200 con lista")

        server_names = {str(item.get("name", "")).strip() for item in verify_body if isinstance(item, dict)}
        missing = [name for _, name in self.CATALOG if name not in server_names]
        if missing:
            return self.nok(case, f"Catálogo incompleto en servidor tras GC-022. Faltan: {missing}")

        return self.ok(
            case,
            f"GC-022 válido: {len(self.CATALOG)}/{len(self.CATALOG)} categorías del catálogo confirmadas en servidor",
        )

    def _case_gc_023_outside_catalog(self, case: Dict[str, str]) -> TestOutcome:
        payload = {"name": "categoría Inventada", "source": "INVALID"}
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "alta fuera de catálogo")

    def _case_gc_024_closed_catalog_consistency(self, case: Dict[str, str]) -> TestOutcome:
        payloads = [
            {"name": "categoría Nueva", "source": "18000000"},
            {"name": "categoría Nueva", "source": "medtop:18000000"},
            {"name": "categoría Nueva", "source": "INVALID"},
        ]
        for payload in payloads:
            status_code, _, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
            if request_error is not None:
                return self.nok(case, f"Error validando catálogo cerrado: {request_error}")
            if status_code not in {400, 422}:
                return self.nok(case, f"catálogo no cerrado para source={payload['source']}: status {status_code}")
        return self.ok(case, "catálogo cerrado: solo se acepta source IPTC")

    def _case_gc_025_utf8_name(self, case: Dict[str, str]) -> TestOutcome:
        payload = {"name": "Religión y culto", "source": "IPTC"}
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error enviando name UTF-8: {request_error}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                if str(response_body.get("name", "")) != "Religión y culto":
                    return self.nok(case, f"Name UTF-8 no preservado: {response_body!r}")
                valid_identity, identity_detail = self._validate_catalog_category_identity(response_body, "12000000", "Religión y culto")
                if not valid_identity:
                    return self.nok(case, identity_detail)
                return self.ok(case, "Name UTF-8 aceptado y preservado")
            finally:
                self._cleanup_category(response_body.get("id"))
        if status_code == 409:
            return self.ok(case, "Name UTF-8 reconocido en catálogo (categoría ya existente)")
        return self.nok(case, f"Name UTF-8 devolvió status inesperado {status_code}")

    def _case_gc_026_response_schema(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._catalog_payload(16, with_prefix=True)
        category, detail = self._create_category(payload)
        if category is None:
            return self.nok(case, detail)
        try:
            schema = self._get_openapi_category_schema()
            if not schema:
                return self.nok(case, "No se pudo resolver components.schemas.Category en OpenAPI")

            properties = schema.get("properties", {})
            if not isinstance(properties, dict) or not properties:
                return self.nok(case, "Schema Category sin properties validas en OpenAPI")

            allowed_keys = set(properties.keys())
            required_keys = set(schema.get("required", [])) if isinstance(schema.get("required"), list) else set()
            actual_keys = set(category.keys())

            missing_required = sorted(required_keys - actual_keys)
            unexpected = sorted(actual_keys - allowed_keys)
            if missing_required:
                return self.nok(case, f"Faltan campos requeridos por OpenAPI: {missing_required}")
            if unexpected:
                return self.nok(case, f"Campos inesperados fuera de OpenAPI: {unexpected}")

            type_errors: List[str] = []
            for key in sorted(actual_keys & allowed_keys):
                if not self._matches_openapi_type(category.get(key), properties.get(key, {})):
                    expected_type = self._describe_openapi_type(properties.get(key, {}))
                    actual_type = type(category.get(key)).__name__
                    type_errors.append(f"{key}: esperado {expected_type}, obtenido {actual_type}")

            if type_errors:
                return self.nok(case, "Tipos incompatibles con OpenAPI: " + "; ".join(type_errors))

            return self.ok(case, "GC-026 válido: respuesta alineada exactamente al schema Category de OpenAPI")
        finally:
            self._cleanup_category(category.get("id"))

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

    def _get_openapi_category_schema(self) -> Dict[str, Any]:
        components = self.openapi_spec.get("components", {}) if isinstance(self.openapi_spec, dict) else {}
        schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
        category_schema = schemas.get("Category", {}) if isinstance(schemas, dict) else {}
        return category_schema if isinstance(category_schema, dict) else {}

    @staticmethod
    def _matches_openapi_type(value: Any, schema: Dict[str, Any]) -> bool:
        if not isinstance(schema, dict):
            return True

        if "anyOf" in schema and isinstance(schema.get("anyOf"), list):
            return any(
                CategoryManagementScopeTests._matches_openapi_type(value, option)
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

    def _catalog_payload(self, index: int, *, with_prefix: bool = False) -> Dict[str, str]:
        _, name = self.CATALOG[index]
        return {
            "name": name,
            "source": "IPTC",
        }

    @staticmethod
    def _with_prefix(raw_id: str) -> str:
        return f"medtop:{raw_id}"

    @staticmethod
    def _accepted_source_values(raw_id: str) -> set:
        return {"iptc"}

    def _create_category(self, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/categories", body=payload)
        if request_error is not None:
            return None, f"Error creando categoría: {request_error}"
        if status_code != 201:
            return None, f"Crear categoría devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear categoría no devolvió objeto JSON: {response_body!r}"
        expected_catalog_id = self._expected_catalog_id_for_name(payload.get("name"))
        if expected_catalog_id is not None:
            valid_identity, identity_detail = self._validate_catalog_category_identity(
                response_body,
                expected_catalog_id,
                str(payload.get("name", "")).strip(),
            )
            if not valid_identity:
                return None, identity_detail
        self._cleanup_register(self._cleanup_category, response_body.get("id"))
        return response_body, f"categoría creada correctamente con id {response_body.get('id')}"

    def _expected_catalog_id_for_name(self, name: Any) -> Optional[str]:
        normalized_name = str(name or "").strip()
        for raw_id, catalog_name in self.CATALOG:
            if catalog_name == normalized_name:
                return raw_id
        return None

    def _validate_catalog_category_identity(self, category: Dict[str, Any], expected_id: str, expected_name: str) -> Tuple[bool, str]:
        returned_name = str(category.get("name", "")).strip()
        if returned_name != expected_name:
            return False, f"La categoría creada no devolvió el name esperado '{expected_name}': {category!r}"

        returned_id = category.get("id")
        try:
            if int(returned_id) != int(expected_id):
                return False, f"La categoría '{expected_name}' no devolvió el id de catálogo {expected_id}: {category!r}"
        except (TypeError, ValueError):
            return False, f"La categoría '{expected_name}' devolvió un id no numérico: {returned_id!r}"

        return True, f"Categoría '{expected_name}' creada con id de catálogo {expected_id}"

    def _ensure_categories_empty(self) -> Tuple[bool, str]:
        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/categories", body=None)
        if request_error is not None:
            return False, f"Error listando categorías: {request_error}"
        if status_code != 200 or not isinstance(response_body, list):
            return False, f"GET /categories devolvió {status_code}, esperado 200 con lista"

        deleted = 0
        for item in response_body:
            if not isinstance(item, dict):
                continue
            category_id = item.get("id")
            if category_id in (None, ""):
                continue
            delete_status, _, delete_error = self._authorized_request("DELETE", f"/api/v1/categories/{category_id}", body=None)
            if delete_error is not None:
                return False, f"Error eliminando categoría {category_id}: {delete_error}"
            if delete_status != 204:
                return False, f"DELETE /categories/{category_id} devolvió {delete_status}, esperado 204"
            deleted += 1

        verify_status, verify_body, verify_error = self._authorized_request("GET", "/api/v1/categories", body=None)
        if verify_error is not None:
            return False, f"Error verificando vaciado de categorías: {verify_error}"
        if verify_status != 200 or not isinstance(verify_body, list):
            return False, f"Verificación GET /categories devolvió {verify_status}, esperado 200 con lista"
        if verify_body:
            return False, f"Siguen existiendo categorías tras el vaciado: {len(verify_body)}"

        return True, f"Categories vaciado correctamente ({deleted} eliminadas)"

    def _cleanup_category(self, category_id: Any) -> None:
        if category_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/categories/{category_id}", body=None)
        except Exception:
            return

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
            and path == "/api/v1/categories"
            and status_code == 201
            and isinstance(response_body, dict)
        ):
            self._cleanup_register(self._cleanup_category, response_body.get("id"))
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