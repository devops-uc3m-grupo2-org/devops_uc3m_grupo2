from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome
from tests.test_data_loader import TestDataLoader

_DATA_FILE = Path(__file__).resolve().parent.parent / "test_data" / "is_case_data.json"


class InformationSourceManagementScopeTests(BaseScopeTests):
    """Implements IS-* test cases for information source management."""

    VALIDATION_STATUSES = {400, 409, 422}
    NOT_FOUND_STATUSES = {400, 404, 422}

    def __init__(self, base_url: str, openapi_path: Optional[Path] = None, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._loader = TestDataLoader(_DATA_FILE)
        seed_login = self._loader.get_default("seed_login", {})
        self.seed_email = str(seed_login.get("email", "admin@newsradar.com"))
        self.seed_password = str(seed_login.get("password", "admin123"))
        self.openapi_spec = self._load_openapi(openapi_path)

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        self._cleanup_reset()
        try:
            return self._run_case_impl(case)
        finally:
            self._cleanup_run()

    def _run_case_impl(self, case: Dict[str, str]) -> TestOutcome:
        case_id = str(case.get("Caso de Prueba", "")).strip().upper()

        if case_id == "IS-001":
            return self._case_is_001_create_valid_source(case)
        if case_id == "IS-002":
            return self._case_is_002_without_name(case)
        if case_id == "IS-003":
            return self._case_is_003_without_url(case)
        if case_id == "IS-004":
            return self._case_is_004_name_empty(case)
        if case_id == "IS-005":
            return self._case_is_005_name_too_long(case)
        if case_id == "IS-006":
            return self._case_is_006_url_empty(case)
        if case_id == "IS-007":
            return self._case_is_007_url_invalid_format(case)
        if case_id == "IS-008":
            return self._case_is_008_url_too_long(case)
        if case_id == "IS-009":
            return self._case_is_009_url_not_accessible(case)
        if case_id == "IS-010":
            return self._case_is_010_domain_not_resolvable(case)
        if case_id == "IS-011":
            return self._case_is_011_duplicate_exact(case)
        if case_id == "IS-012":
            return self._case_is_012_duplicate_by_url(case)
        if case_id == "IS-013":
            return self._case_is_013_duplicate_by_name(case)
        if case_id == "IS-014":
            return self._case_is_014_duplicate_case_insensitive_url(case)
        if case_id == "IS-015":
            return self._case_is_015_duplicate_trailing_slash(case)
        if case_id == "IS-016":
            return self._case_is_016_url_normalization(case)
        if case_id == "IS-017":
            return self._case_is_017_name_with_whitespace(case)
        if case_id == "IS-018":
            return self._case_is_018_payload_extra(case)
        if case_id == "IS-019":
            return self._case_is_019_get_existing(case)
        if case_id == "IS-020":
            return self._case_is_020_get_nonexistent(case)
        if case_id == "IS-021":
            return self._case_is_021_validate_id_type(case)
        if case_id == "IS-022":
            return self._case_is_022_update_valid(case)
        if case_id == "IS-023":
            return self._case_is_023_update_invalid_url(case)
        if case_id == "IS-024":
            return self._case_is_024_update_unreachable_url(case)
        if case_id == "IS-025":
            return self._case_is_025_update_to_duplicate(case)
        if case_id == "IS-026":
            return self._case_is_026_delete_existing(case)
        if case_id == "IS-027":
            return self._case_is_027_delete_nonexistent(case)
        if case_id == "IS-028":
            return self._case_is_028_utf8_name(case)
        if case_id == "IS-029":
            return self._case_is_029_response_schema(case)

        return self.nok(case, f"Caso IS no implementado: {case_id}")

    def _case_is_001_create_valid_source(self, case: Dict[str, str]) -> TestOutcome:
        source, detail = self._create_source(self._valid_payload())
        if source is None:
            return self.nok(case, detail)
        self._cleanup_source(source.get("id"))
        return self.ok(case, detail)

    def _case_is_002_without_name(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload()
        payload.pop("name", None)
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "crear fuente sin name")

    def _case_is_003_without_url(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload()
        payload.pop("url", None)
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "crear fuente sin url")

    def _case_is_004_name_empty(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload(name="")
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name vacio")

    def _case_is_005_name_too_long(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload(name="N" * 121)
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "name longitud maxima")

    def _case_is_006_url_empty(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload(url="")
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url vacia")

    def _case_is_007_url_invalid_format(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload(url=self._default_string("invalid_url", "not-a-uri"))
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url formato inválido")

    def _case_is_008_url_too_long(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload(url=self._default_string("url_too_long_prefix", "https://example.com/") + "a" * 2100)
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url longitud maxima")

    def _case_is_009_url_not_accessible(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload(url=self._default_string("url_unreachable", "http://127.0.0.1:1/unreachable"))
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url no accesible")

    def _case_is_010_domain_not_resolvable(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload(url=self._default_string("url_invalid_domain", "https://domain-inexistente.invalid/rss"))
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "dominio no resolvible")

    def _case_is_011_duplicate_exact(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload()
        source, detail = self._create_source(payload)
        if source is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado exacto")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_012_duplicate_by_url(self, case: Dict[str, str]) -> TestOutcome:
        url = self._unique_url()
        source, detail = self._create_source(self._valid_payload(url=url))
        if source is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "POST", "/api/v1/information-sources", body=self._valid_payload(url=url)
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado por url")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_013_duplicate_by_name(self, case: Dict[str, str]) -> TestOutcome:
        name = self._unique_name()
        source, detail = self._create_source(self._valid_payload(name=name))
        if source is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "POST", "/api/v1/information-sources", body=self._valid_payload(name=name)
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado por name")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_014_duplicate_case_insensitive_url(self, case: Dict[str, str]) -> TestOutcome:
        base_url = f"https://EXAMPLE.COM/{uuid.uuid4().hex[:8]}/rss"
        source, detail = self._create_source(self._valid_payload(url=base_url))
        if source is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "POST", "/api/v1/information-sources", body=self._valid_payload(url=base_url.lower())
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado url case-insensitive")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_015_duplicate_trailing_slash(self, case: Dict[str, str]) -> TestOutcome:
        url = f"https://example.com/{uuid.uuid4().hex[:8]}/rss"
        source, detail = self._create_source(self._valid_payload(url=url))
        if source is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "POST", "/api/v1/information-sources", body=self._valid_payload(url=f"{url}/")
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado trailing slash")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_016_url_normalization(self, case: Dict[str, str]) -> TestOutcome:
        url_variant_a = f"https://EXAMPLE.COM/{uuid.uuid4().hex[:8]}/rss/"
        source, detail = self._create_source(self._valid_payload(url=url_variant_a))
        if source is None:
            return self.nok(case, detail)
        try:
            url_variant_b = url_variant_a.lower().rstrip("/")
            status_code, response_body, request_error = self._authorized_request(
                "POST", "/api/v1/information-sources", body=self._valid_payload(url=url_variant_b)
            )
            if request_error is not None:
                return self.nok(case, f"Error validando normalizacion url: {request_error}")
            if status_code in {400, 409, 422}:
                return self.ok(case, f"Normalizacion consistente: variante equivalente rechazada con {status_code}")
            if status_code == 201 and isinstance(response_body, dict):
                self._cleanup_source(response_body.get("id"))
                return self.nok(case, "Variantes equivalentes de URL fueron aceptadas como distintas")
            return self.nok(case, f"Resultado inesperado en normalizacion url: {status_code}")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_017_name_with_whitespace(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload(name=f"  {self._unique_name()}  ")
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error creando name con espacios: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Name con espacios rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                stored_name = str(response_body.get("name", ""))
                if stored_name.strip() == "":
                    return self.nok(case, "Name con solo espacios fue persistido")
                return self.ok(case, "Name con espacios aceptado y normalizado")
            finally:
                self._cleanup_source(response_body.get("id"))
        return self.nok(case, f"Status inesperado para name con espacios: {status_code}")

    def _case_is_018_payload_extra(self, case: Dict[str, str]) -> TestOutcome:
        payload = self._valid_payload()
        payload["unexpected"] = "x"
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        if request_error is not None:
            return self.nok(case, f"Error enviando payload extra: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Payload extra rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                if "unexpected" in response_body:
                    return self.nok(case, "Campo inesperado persistido en respuesta")
                return self.ok(case, "Campo extra ignorado sin romper contrato")
            finally:
                self._cleanup_source(response_body.get("id"))
        return self.nok(case, f"Status inesperado para payload extra: {status_code}")

    def _case_is_019_get_existing(self, case: Dict[str, str]) -> TestOutcome:
        source, detail = self._create_source(self._valid_payload())
        if source is None:
            return self.nok(case, detail)
        try:
            status_code, response_body, request_error = self._authorized_request(
                "GET", f"/api/v1/information-sources/{source['id']}", body=None
            )
            if request_error is not None:
                return self.nok(case, f"Error consultando fuente: {request_error}")
            if status_code != 200:
                return self.nok(case, f"GET fuente devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict) or response_body.get("id") != source["id"]:
                return self.nok(case, f"Respuesta GET invalida: {response_body!r}")
            return self.ok(case, "Consulta de fuente existente correcta")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_020_get_nonexistent(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request(
            "GET", f"/api/v1/information-sources/{self._nonexistent_id()}", body=None
        )
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "get fuente inexistente")

    def _case_is_021_validate_id_type(self, case: Dict[str, str]) -> TestOutcome:
        source, detail = self._create_source(self._valid_payload())
        if source is None:
            return self.nok(case, detail)
        try:
            source_id = source.get("id")
            if not isinstance(source_id, int):
                return self.nok(case, f"id no es entero: {source_id!r}")
            return self.ok(case, "Tipo de id validado como entero")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_022_update_valid(self, case: Dict[str, str]) -> TestOutcome:
        source, detail = self._create_source(self._valid_payload())
        if source is None:
            return self.nok(case, detail)
        try:
            update_payload = self._valid_payload(name=self._unique_name(), url=self._unique_url())
            status_code, response_body, request_error = self._authorized_request(
                "PUT", f"/api/v1/information-sources/{source['id']}", body=update_payload
            )
            if request_error is not None:
                return self.nok(case, f"Error actualizando fuente: {request_error}")
            if status_code != 200:
                return self.nok(case, f"Actualizar fuente devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict):
                return self.nok(case, f"Respuesta update invalida: {response_body!r}")
            if response_body.get("name") != update_payload["name"]:
                return self.nok(case, f"Name no actualizado: {response_body!r}")
            return self.ok(case, "Fuente actualizada correctamente")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_023_update_invalid_url(self, case: Dict[str, str]) -> TestOutcome:
        source, detail = self._create_source(self._valid_payload())
        if source is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "PUT", f"/api/v1/information-sources/{source['id']}", body={"url": "bad-url", "name": source["name"]}
            )
            return self._expect_statuses(case, status_code, request_error, {400, 422}, "update url invalida")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_024_update_unreachable_url(self, case: Dict[str, str]) -> TestOutcome:
        source, detail = self._create_source(self._valid_payload())
        if source is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "PUT",
                f"/api/v1/information-sources/{source['id']}",
                body={"url": self._default_string("url_down", "http://127.0.0.1:1/down"), "name": source["name"]},
            )
            return self._expect_statuses(case, status_code, request_error, {400, 422}, "update url no accesible")
        finally:
            self._cleanup_source(source.get("id"))

    def _case_is_025_update_to_duplicate(self, case: Dict[str, str]) -> TestOutcome:
        source_a, detail_a = self._create_source(self._valid_payload())
        if source_a is None:
            return self.nok(case, detail_a)
        source_b, detail_b = self._create_source(self._valid_payload())
        if source_b is None:
            self._cleanup_source(source_a.get("id"))
            return self.nok(case, detail_b)
        try:
            status_code, _, request_error = self._authorized_request(
                "PUT",
                f"/api/v1/information-sources/{source_b['id']}",
                body={"name": source_a["name"], "url": source_a["url"]},
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "update a duplicado")
        finally:
            self._cleanup_source(source_a.get("id"))
            self._cleanup_source(source_b.get("id"))

    def _case_is_026_delete_existing(self, case: Dict[str, str]) -> TestOutcome:
        source, detail = self._create_source(self._valid_payload())
        if source is None:
            return self.nok(case, detail)
        status_code, _, request_error = self._authorized_request(
            "DELETE", f"/api/v1/information-sources/{source['id']}", body=None
        )
        if request_error is not None:
            return self.nok(case, f"Error eliminando fuente: {request_error}")
        if status_code != 204:
            self._cleanup_source(source.get("id"))
            return self.nok(case, f"Delete fuente devolvió {status_code}, esperado 204")
        return self.ok(case, "Fuente eliminada correctamente")

    def _case_is_027_delete_nonexistent(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request(
            "DELETE", f"/api/v1/information-sources/{self._nonexistent_id()}", body=None
        )
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "delete fuente inexistente")

    def _case_is_028_utf8_name(self, case: Dict[str, str]) -> TestOutcome:
        source, detail = self._create_source(self._valid_payload(name=self._default_string("utf8_name", "Fuente Información Ñ")))
        if source is None:
            return self.nok(case, detail)
        self._cleanup_source(source.get("id"))
        return self.ok(case, detail)

    def _case_is_029_response_schema(self, case: Dict[str, str]) -> TestOutcome:
        source, detail = self._create_source(self._valid_payload())
        if source is None:
            return self.nok(case, detail)
        try:
            schema = self._get_openapi_information_source_schema()
            if not schema:
                return self.nok(case, "No se pudo resolver components.schemas.InformationSource en OpenAPI")

            properties = schema.get("properties", {})
            if not isinstance(properties, dict) or not properties:
                return self.nok(case, "Schema InformationSource sin properties validas")

            allowed_keys = set(properties.keys())
            required_keys = set(schema.get("required", [])) if isinstance(schema.get("required"), list) else set()
            actual_keys = set(source.keys())

            missing_required = sorted(required_keys - actual_keys)
            unexpected = sorted(actual_keys - allowed_keys)
            if missing_required:
                return self.nok(case, f"Faltan campos requeridos por OpenAPI: {missing_required}")
            if unexpected:
                return self.nok(case, f"Campos inesperados fuera de OpenAPI: {unexpected}")

            type_errors: List[str] = []
            for key in sorted(actual_keys & allowed_keys):
                if not self._matches_openapi_type(source.get(key), properties.get(key, {})):
                    expected_type = self._describe_openapi_type(properties.get(key, {}))
                    actual_type = type(source.get(key)).__name__
                    type_errors.append(f"{key}: esperado {expected_type}, obtenido {actual_type}")

            if type_errors:
                return self.nok(case, "Tipos incompatibles con OpenAPI: " + "; ".join(type_errors))

            return self.ok(case, "IS-029 válido: respuesta alineada al schema InformationSource de OpenAPI")
        finally:
            self._cleanup_source(source.get("id"))

    def _valid_payload(self, *, name: Optional[str] = None, url: Optional[str] = None) -> Dict[str, str]:
        defaults = self._loader.get_default("create_source_payload", {})
        name_prefix = str(defaults.get("name_prefix", "Fuente"))
        url_base = str(defaults.get("url_base", "https://example.com/feed"))
        return {
            "name": name if name is not None else self._unique_name(name_prefix),
            "url": url if url is not None else self._unique_url(url_base),
        }

    @staticmethod
    def _unique_name(prefix: str = "Fuente") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _unique_url(base_url: str = "https://example.com/feed") -> str:
        return f"{base_url}/{uuid.uuid4().hex[:10]}"

    def _default_string(self, key: str, fallback: str) -> str:
        strings = self._loader.get_default("strings", {})
        return str(strings.get(key, fallback))

    def _nonexistent_id(self) -> int:
        ids = self._loader.get_default("ids", {})
        try:
            return int(ids.get("nonexistent", 99999999))
        except Exception:
            return 99999999

    def _create_source(self, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        if request_error is not None:
            return None, f"Error creando fuente: {request_error}"
        if status_code != 201:
            return None, f"Crear fuente devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear fuente no devolvió objeto JSON: {response_body!r}"
        return response_body, f"Fuente creada correctamente con id {response_body.get('id')}"

    def _cleanup_source(self, source_id: Any) -> None:
        if source_id in (None, ""):
            return
        try:
            self._authorized_request("DELETE", f"/api/v1/information-sources/{source_id}", body=None)
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

    def _get_openapi_information_source_schema(self) -> Dict[str, Any]:
        components = self.openapi_spec.get("components", {}) if isinstance(self.openapi_spec, dict) else {}
        schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
        source_schema = schemas.get("InformationSource", {}) if isinstance(schemas, dict) else {}
        return source_schema if isinstance(source_schema, dict) else {}

    @staticmethod
    def _matches_openapi_type(value: Any, schema: Dict[str, Any]) -> bool:
        if not isinstance(schema, dict):
            return True

        if "anyOf" in schema and isinstance(schema.get("anyOf"), list):
            return any(
                InformationSourceManagementScopeTests._matches_openapi_type(value, option)
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
            and path == "/api/v1/information-sources"
            and status_code == 201
            and isinstance(response_body, dict)
        ):
            self._cleanup_register(self._cleanup_source, response_body.get("id"))
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