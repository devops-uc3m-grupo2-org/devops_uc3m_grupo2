from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome


class APIScopeTests(BaseScopeTests):
    """Implements API scope checks described in casos_prueba.csv."""

    def __init__(self, base_url: str, openapi_path: Path, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.openapi_path = openapi_path
        self.timeout_seconds = timeout_seconds
        self.openapi_spec = self._load_openapi()
        self.seed_email = "admin@newsradar.com"
        self.seed_password = "admin123"

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        case_id = str(case["Caso de Prueba"]).strip().upper()

        if case_id == "API-001":
            return self._case_api_001_unauthorized_crud(case)
        if case_id == "API-002":
            return self._case_api_002_health_without_auth(case)
        if case_id ==  "API-003":
            return self._case_api_003_seed_login_and_authorized_users(case)
        if case_id =="API-004":
            return self._case_api_004_invalid_login(case)

        return self.nok(case, f"Caso no implementado en APIScopeTests: {case_id}")

    def _case_api_001_unauthorized_crud(self, case: Dict[str, str]) -> TestOutcome:
        endpoints = self._get_secured_operations()
        if not endpoints:
            return self.nok(case, "No se encontraron operaciones protegidas por HTTPBearer")

        failures: List[str] = []
        for op in endpoints:
            status_code, _, request_error = self._invoke_operation_without_auth(op)
            if request_error is not None:
                failures.append(f"{op['method']} {op['path']} -> error: {request_error}")
                continue

            if status_code != 401:
                failures.append(f"{op['method']} {op['path']} -> status {status_code}, esperado 401")

        if failures:
            return self.nok(
                case,
                " ; ".join(failures[:8]) + (" ; ..." if len(failures) > 8 else ""),
            )

        return self.ok(case, f"Todas las operaciones protegidas ({len(endpoints)}) devolvieron 401 sin token")

    def _case_api_002_health_without_auth(self, case: Dict[str, str]) -> TestOutcome:
        status_code, response_body, request_error = self._raw_request("GET", "/api/v1/health", body=None)

        if request_error is not None:
            return self.nok(case, f"Error invocando health: {request_error}")

        if status_code != 200:
            return self.nok(case, f"Health devolvió {status_code}, esperado 200")

        if not isinstance(response_body, dict):
            return self.nok(case, f"Health no devolvió JSON objeto: {response_body!r}")

        status = str(response_body.get("status", "")).lower()
        if status != "ok":
            return self.nok(case, f"Health.status='{status}', esperado 'ok'")

        return self.ok(case, "Health sin autorización devolvió 200 y status='ok'")

    def _case_api_003_seed_login_and_authorized_users(self, case: Dict[str, str]) -> TestOutcome:
        token, login_error = self._login_seed_user()
        if login_error is not None:
            return self.nok(case, login_error)

        status_code, response_body, request_error = self._raw_request(
            "GET",
            "/api/v1/users",
            body=None,
            extra_headers={"Authorization": f"Bearer {token}"},
        )

        if request_error is not None:
            return self.nok(case, f"Error invocando endpoint protegido con bearer: {request_error}")

        if status_code != 200:
            return self.nok(case, f"GET /api/v1/users con bearer devolvió {status_code}, esperado 200")

        if not isinstance(response_body, list):
            return self.nok(case, f"GET /api/v1/users no devolvió una lista JSON: {response_body!r}")

        return self.ok(case, "Login semilla OK y acceso autorizado a GET /api/v1/users OK")

    def _case_api_004_invalid_login(self, case: Dict[str, str]) -> TestOutcome:
        payload = {"email": self.seed_email, "password": "bad-password"}
        status_code, response_body, request_error = self._raw_request(
            "POST",
            "/api/v1/auth/login",
            body=payload,
        )

        if request_error is not None:
            return self.nok(case, f"Error invocando login con credenciales inválidas: {request_error}")

        if status_code == 200:
            if isinstance(response_body, dict) and response_body.get("access_token"):
                return self.nok(case, "Login inválido devolvió 200 y access_token, deberia fallar")
            return self.nok(case, "Login inválido devolvió 200, deberia fallar")

        return self.ok(case, f"Login inválido fallo como se esperaba con status {status_code} y sin bearer")

    def _login_seed_user(self) -> Tuple[Optional[str], Optional[str]]:
        payload = {"email": self.seed_email, "password": self.seed_password}
        status_code, response_body, request_error = self._raw_request(
            "POST",
            "/api/v1/auth/login",
            body=payload,
        )

        if request_error is not None:
            return None, f"Error en login con usuario semilla: {request_error}"

        if status_code != 200:
            return None, f"Login semilla devolvió {status_code}, esperado 200"

        if not isinstance(response_body, dict):
            return None, f"Login no devolvió JSON objeto: {response_body!r}"

        token = response_body.get("access_token")
        if not isinstance(token, str) or not token.strip():
            return None, f"Login no devolvió access_token válido: {response_body!r}"

        return token.strip(), None

    def _load_openapi(self) -> Dict[str, Any]:
        with self.openapi_path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)

    def _get_secured_operations(self) -> List[Dict[str, Any]]:
        methods = {"get", "post", "put", "patch", "delete"}
        paths = self.openapi_spec.get("paths", {})
        global_security = self.openapi_spec.get("security", [])

        secured_operations: List[Dict[str, Any]] = []
        for path, item in paths.items():
            for method, operation in item.items():
                if method.lower() not in methods:
                    continue

                operation_security = operation.get("security", global_security)
                if not self._requires_http_bearer(operation_security):
                    continue

                secured_operations.append(
                    {
                        "path": path,
                        "method": method.upper(),
                        "parameters": operation.get("parameters", []),
                        "request_body": operation.get("requestBody"),
                    }
                )

        return secured_operations

    @staticmethod
    def _requires_http_bearer(security: Any) -> bool:
        if not isinstance(security, list):
            return False

        for requirement in security:
            if isinstance(requirement, dict) and "HTTPBearer" in requirement:
                return True

        return False

    def _invoke_operation_without_auth(self, op: Dict[str, Any]) -> Tuple[int, Any, Optional[str]]:
        path = self._materialize_path(op["path"], op.get("parameters", []))
        body = self._build_fake_body(op.get("request_body"))
        return self._raw_request(op["method"], path, body)

    def _materialize_path(self, raw_path: str, parameters: List[Dict[str, Any]]) -> str:
        path = raw_path
        for parameter in parameters:
            if parameter.get("in") != "path":
                continue

            name = parameter.get("name")
            if not name:
                continue

            schema_type = parameter.get("schema", {}).get("type")
            value = "999999" if schema_type == "integer" else "fake-value"
            path = path.replace("{" + name + "}", value)

        return path

    def _build_fake_body(self, request_body: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(request_body, dict):
            return None

        content = request_body.get("content", {})
        app_json = content.get("application/json", {})
        schema = app_json.get("schema", {})
        if not schema:
            return {"fake": "data"}

        resolved = self._resolve_schema(schema)
        if not isinstance(resolved, dict):
            return {"fake": "data"}

        properties = resolved.get("properties", {})
        required = resolved.get("required", [])

        body: Dict[str, Any] = {}
        for field in required:
            definition = properties.get(field, {})
            body[field] = self._fake_value_for_schema(definition)

        return body or {"fake": "data"}

    def _resolve_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        ref = schema.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            schema_name = ref.split("/")[-1]
            components = self.openapi_spec.get("components", {}).get("schemas", {})
            resolved = components.get(schema_name, {})
            if isinstance(resolved, dict):
                return resolved
        return schema

    def _fake_value_for_schema(self, schema: Dict[str, Any]) -> Any:
        schema = self._resolve_schema(schema)

        if "anyOf" in schema and isinstance(schema["anyOf"], list) and schema["anyOf"]:
            schema = schema["anyOf"][0]

        schema_type = schema.get("type")
        if schema_type == "string":
            fmt = schema.get("format")
            if fmt == "email":
                return "fake@example.com"
            if fmt == "date-time":
                return "2026-01-01T00:00:00Z"
            if fmt == "uri":
                return "https://example.com/resource"
            return "fake-value"

        if schema_type == "integer":
            return 1

        if schema_type == "number":
            return 1.0

        if schema_type == "array":
            item_schema = schema.get("items", {})
            return [self._fake_value_for_schema(item_schema)]

        if schema_type == "object":
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            return {name: self._fake_value_for_schema(properties.get(name, {})) for name in required}

        return "fake-value"

    def _raw_request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]],
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any, Optional[str]]:
        url = f"{self.base_url}{path}"

        data: Optional[bytes] = None
        headers = {"Accept": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        if body is not None and method.upper() in {"POST", "PUT", "PATCH"}:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, method=method.upper(), data=data, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                status_code = int(response.status)
                raw = response.read().decode("utf-8", errors="replace")
                parsed = self._parse_json(raw)
                return status_code, parsed, None
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            parsed = self._parse_json(raw)
            return int(exc.code), parsed, None
        except Exception as exc:  # pragma: no cover
            return -1, None, str(exc)

    @staticmethod
    def _parse_json(raw: str) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
