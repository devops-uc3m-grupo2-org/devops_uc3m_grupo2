from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome
from tests.test_data_loader import TestDataLoader

_DATA_FILE = Path(__file__).resolve().parent.parent / "test_data" / "smoke_case_data.json"


class SystemInitializationSmokeTests(BaseScopeTests):
    """Implements SMOKE-* test cases for system bootstrap checks.

    This suite is intentionally read-only against domain resources.
    The only POST allowed is the technical login call used to obtain a token.
    """

    def __init__(self, base_url: str, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._loader = TestDataLoader(_DATA_FILE)
        seed_login = self._loader.get_default("seed_login", {})
        self.seed_email = str(seed_login.get("email", "admin@newsradar.com"))
        self.seed_password = str(seed_login.get("password", "admin123"))

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        case_id = str(case.get("Caso de Prueba", "")).strip().upper()

        if case_id == "SMOKE-001":
            return self._case_smoke_001_admin_user_exists(case)
        if case_id == "SMOKE-002":
            return self._case_smoke_002_min_sources(case)
        if case_id == "SMOKE-003":
            return self._case_smoke_003_min_rss_channels(case)
        if case_id == "SMOKE-004":
            return self._case_smoke_004_at_least_one_channel_per_category(case)
        if case_id == "SMOKE-005":
            return self._case_smoke_005_all_iptc_categories_present(case)
        if case_id == "SMOKE-006":
            return self._case_smoke_006_default_gestor_role_exists(case)

        return self.nok(case, f"Caso SMOKE no implementado: {case_id}")

    def _case_smoke_001_admin_user_exists(self, case: Dict[str, str]) -> TestOutcome:
        admin_email = str(self._loader.get_default("admin_email", "admin@newsradar.com")).strip().lower()
        admin_role_names_raw = self._loader.get_default("admin_role_names", ["admin", "administrador"])
        admin_role_names = {
            str(item).strip().lower()
            for item in (admin_role_names_raw if isinstance(admin_role_names_raw, list) else ["admin", "administrador"])
            if str(item).strip()
        }

        role_status, role_body, role_error = self._authorized_request("GET", "/api/v1/roles", body=None)
        if role_error is not None:
            return self.nok(case, f"Error listando roles: {role_error}")
        if role_status != 200 or not isinstance(role_body, list):
            return self.nok(case, f"GET /api/v1/roles devolvió {role_status}, esperado 200 con lista")

        admin_role_ids: Set[int] = set()
        for role in role_body:
            if not isinstance(role, dict):
                continue
            role_id = role.get("id")
            role_name = str(role.get("name", "")).strip().lower()
            if isinstance(role_id, int) and role_name in admin_role_names:
                admin_role_ids.add(role_id)

        user_status, user_body, user_error = self._authorized_request("GET", "/api/v1/users", body=None)
        if user_error is not None:
            return self.nok(case, f"Error listando usuarios: {user_error}")
        if user_status != 200 or not isinstance(user_body, list):
            return self.nok(case, f"GET /api/v1/users devolvió {user_status}, esperado 200 con lista")

        for user in user_body:
            if not isinstance(user, dict):
                continue

            email = str(user.get("email", "")).strip().lower()
            if email == admin_email:
                return self.ok(case, f"Usuario administrador inicial encontrado por email: {admin_email}")

            role_ids = user.get("role_ids")
            if isinstance(role_ids, list) and admin_role_ids:
                if any(isinstance(role_id, int) and role_id in admin_role_ids for role_id in role_ids):
                    return self.ok(case, "Usuario administrador inicial encontrado por role_ids")

            roles = user.get("roles")
            if isinstance(roles, list):
                for role in roles:
                    if isinstance(role, dict):
                        role_name = str(role.get("name", "")).strip().lower()
                        if role_name in admin_role_names:
                            return self.ok(case, "Usuario administrador inicial encontrado por roles[].name")

        return self.nok(case, "No se encontró un usuario administrador inicial en /api/v1/users")

    def _case_smoke_002_min_sources(self, case: Dict[str, str]) -> TestOutcome:
        threshold = int(self._loader.get_default("min_information_sources", 10))

        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/information-sources", body=None)
        if request_error is not None:
            return self.nok(case, f"Error listando information-sources: {request_error}")
        if status_code != 200 or not isinstance(response_body, list):
            return self.nok(case, f"GET /api/v1/information-sources devolvió {status_code}, esperado 200 con lista")

        distinct_media: Set[str] = set()
        for source in response_body:
            if not isinstance(source, dict):
                continue
            source_id = source.get("id")
            source_name = source.get("name")
            if isinstance(source_id, int):
                distinct_media.add(f"id:{source_id}")
            elif isinstance(source_name, str) and source_name.strip():
                distinct_media.add(f"name:{source_name.strip().lower()}")

        total_sources = len(distinct_media)
        if total_sources < threshold:
            return self.nok(case, f"Medios de comunicacion insuficientes: {total_sources} < {threshold}")
        return self.ok(case, f"Medios de comunicacion verificados: {total_sources} >= {threshold}")

    def _case_smoke_003_min_rss_channels(self, case: Dict[str, str]) -> TestOutcome:
        threshold = int(self._loader.get_default("min_rss_channels", 100))

        channels, channel_error = self._fetch_all_rss_channels()
        if channel_error is not None:
            return self.nok(case, channel_error)

        unique_channel_ids: Set[int] = {
            channel.get("id")
            for channel in channels
            if isinstance(channel, dict) and isinstance(channel.get("id"), int)
        }

        total_channels = len(unique_channel_ids)
        if total_channels < threshold:
            return self.nok(case, f"Canales RSS iniciales insuficientes: {total_channels} < {threshold}")
        return self.ok(case, f"Canales RSS iniciales verificados: {total_channels} >= {threshold}")

    def _case_smoke_004_at_least_one_channel_per_category(self, case: Dict[str, str]) -> TestOutcome:
        category_status, category_body, category_error = self._authorized_request("GET", "/api/v1/categories", body=None)
        if category_error is not None:
            return self.nok(case, f"Error listando categorias: {category_error}")
        if category_status != 200 or not isinstance(category_body, list):
            return self.nok(case, f"GET /api/v1/categories devolvió {category_status}, esperado 200 con lista")

        category_items = [item for item in category_body if isinstance(item, dict)]
        if not category_items:
            return self.nok(case, "No hay categorias iniciales para validar cobertura de RSS")

        channels, channel_error = self._fetch_all_rss_channels()
        if channel_error is not None:
            return self.nok(case, channel_error)

        covered_tokens: Set[str] = set()
        for channel in channels:
            if isinstance(channel, dict):
                covered_tokens.update(self._extract_category_tokens_from_channel(channel))

        missing_categories: List[str] = []
        for category in category_items:
            category_tokens = self._extract_category_tokens_from_category(category)
            if not category_tokens:
                category_label = str(category.get("name") or category.get("label") or category.get("code") or category.get("id") or "?")
                missing_categories.append(f"sin-token:{category_label}")
                continue
            if category_tokens.isdisjoint(covered_tokens):
                category_label = str(category.get("code") or category.get("name") or category.get("label") or category.get("id"))
                missing_categories.append(category_label)

        if missing_categories:
            sample = ", ".join(missing_categories[:10])
            return self.nok(case, f"Categorias sin al menos un RSS asociado: {sample}")

        return self.ok(case, f"Cobertura RSS por categoria verificada: {len(category_items)} categorias con al menos un canal")

    def _case_smoke_005_all_iptc_categories_present(self, case: Dict[str, str]) -> TestOutcome:
        expected_pairs_raw = self._loader.get_default("iptc_categories", [])
        if not isinstance(expected_pairs_raw, list) or not expected_pairs_raw:
            return self.nok(case, "No hay configuracion de categorias IPTC esperadas en smoke_case_data.json")

        expected_pairs: Set[Tuple[str, str]] = set()
        for item in expected_pairs_raw:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            raw_code = str(item[0]).strip()
            raw_name = str(item[1]).strip().lower()
            if raw_code and raw_name:
                expected_pairs.add((str(raw_code), str(raw_name)))

        if not expected_pairs:
            return self.nok(case, "Configuracion de categorias IPTC invalida: no se pudieron construir pares id+name")

        category_status, category_body, category_error = self._authorized_request("GET", "/api/v1/categories", body=None)
        if category_error is not None:
            return self.nok(case, f"Error listando categorias: {category_error}")
        if category_status != 200 or not isinstance(category_body, list):
            return self.nok(case, f"GET /api/v1/categories devolvió {category_status}, esperado 200 con lista")

        observed_pairs: Set[Tuple[str, str]] = set()
        for category in category_body:
            if not isinstance(category, dict):
                continue
            name = str(category.get("name", "")).strip().lower()
            if not name:
                continue

            source_code = self._extract_iptc_code(category)
            if source_code is None:
                continue

            observed_pairs.add((str(source_code), str(name)))

        missing = sorted(expected_pairs - observed_pairs)
        if missing:
            sample = ", ".join(f"{item[0]}:{item[1]}" for item in missing[:10])
            return self.nok(case, f"Faltan categorias IPTC esperadas (id+name): {sample}")

        return self.ok(case, f"Categorias IPTC verificadas: {len(expected_pairs)} pares id+name presentes")

    def _case_smoke_006_default_gestor_role_exists(self, case: Dict[str, str]) -> TestOutcome:
        expected_role_name = str(self._loader.get_default("default_role_name", "gestor")).strip().lower()
        if not expected_role_name:
            expected_role_name = "gestor"

        role_status, role_body, role_error = self._authorized_request("GET", "/api/v1/roles", body=None)
        if role_error is not None:
            return self.nok(case, f"Error listando roles: {role_error}")
        if role_status != 200 or not isinstance(role_body, list):
            return self.nok(case, f"GET /api/v1/roles devolvió {role_status}, esperado 200 con lista")

        for role in role_body:
            if not isinstance(role, dict):
                continue
            role_name = str(role.get("name", "")).strip().lower()
            if role_name == expected_role_name:
                return self.ok(case, f"Rol por defecto verificado: {expected_role_name}")

        return self.nok(case, f"No se encontró el rol por defecto requerido: {expected_role_name}")

    def _fetch_all_rss_channels(self) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        source_status, source_body, source_error = self._authorized_request("GET", "/api/v1/information-sources", body=None)
        if source_error is not None:
            return [], f"Error listando information-sources: {source_error}"
        if source_status != 200 or not isinstance(source_body, list):
            return [], f"GET /api/v1/information-sources devolvió {source_status}, esperado 200 con lista"

        source_ids: List[int] = []
        for item in source_body:
            if isinstance(item, dict) and isinstance(item.get("id"), int):
                source_ids.append(item["id"])

        channels: List[Dict[str, Any]] = []
        for source_id in source_ids:
            status_code, channels_body, request_error = self._authorized_request(
                "GET", f"/api/v1/information-sources/{source_id}/rss-channels", body=None
            )
            if request_error is not None:
                return [], f"Error listando rss-channels para source_id={source_id}: {request_error}"
            if status_code != 200 or not isinstance(channels_body, list):
                return [], f"GET rss-channels para source_id={source_id} devolvió {status_code}, esperado 200 con lista"
            for channel in channels_body:
                if isinstance(channel, dict):
                    channels.append(channel)

        return channels, None

    @staticmethod
    def _extract_category_tokens_from_channel(channel: Dict[str, Any]) -> Set[str]:
        tokens: Set[str] = set()

        category_id = channel.get("category_id")
        if isinstance(category_id, int):
            tokens.add(f"id:{category_id}")
        elif isinstance(category_id, str) and category_id.strip().isdigit():
            tokens.add(f"id:{int(category_id.strip())}")

        category_code = channel.get("category_code")
        if isinstance(category_code, str) and category_code.strip():
            tokens.add(f"code:{category_code.strip().lower()}")

        category = channel.get("category")
        if isinstance(category, dict):
            tokens.update(SystemInitializationSmokeTests._extract_category_tokens_from_category(category))

        categories = channel.get("categories")
        if isinstance(categories, list):
            for item in categories:
                if isinstance(item, dict):
                    tokens.update(SystemInitializationSmokeTests._extract_category_tokens_from_category(item))

        return tokens

    @staticmethod
    def _extract_category_tokens_from_category(category: Dict[str, Any]) -> Set[str]:
        tokens: Set[str] = set()

        category_id = category.get("id")
        if isinstance(category_id, int):
            tokens.add(f"id:{category_id}")
        elif isinstance(category_id, str) and category_id.strip().isdigit():
            tokens.add(f"id:{int(category_id.strip())}")

        code = category.get("code")
        if isinstance(code, str) and code.strip():
            tokens.add(f"code:{code.strip().lower()}")

        name = category.get("name")
        if isinstance(name, str) and name.strip():
            tokens.add(f"name:{name.strip().lower()}")

        label = category.get("label")
        if isinstance(label, str) and label.strip():
            tokens.add(f"label:{label.strip().lower()}")

        return tokens

    @staticmethod
    def _extract_iptc_code(category: Dict[str, Any]) -> Optional[str]:
        category_id = category.get("id")
        if isinstance(category_id, int):
            return str(category_id).zfill(8)
        if isinstance(category_id, str):
            raw = category_id.strip()
            if raw.startswith("medtop:"):
                raw = raw.split(":", 1)[1]
            if raw.isdigit():
                return raw.zfill(8)
        return None

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
        return str(token).strip(), None

    def _authorized_request(
        self,
        method: str,
        path: str,
        body: Optional[Any],
    ) -> Tuple[int, Any, Optional[str]]:
        if method.upper() != "GET":
            return -1, None, (
                f"Operacion no permitida en suite SMOKE: {method.upper()} {path}. "
                "La suite es de solo lectura (GET)."
            )

        token, login_error = self._login_seed_user()
        if login_error is not None:
            return -1, None, login_error
        return self._request(
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

    @staticmethod
    def _parse_json(raw: str) -> Any:
        if not raw.strip():
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return raw
