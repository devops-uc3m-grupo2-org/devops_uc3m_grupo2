from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from tests.scope_base import BaseScopeTests, TestOutcome
from tests.test_data_loader import TestDataLoader

_DATA_FILE = Path(__file__).resolve().parent.parent / "test_data" / "rss_case_data.json"


class RSSChannelManagementScopeTests(BaseScopeTests):
    """Implements RSS-* test cases for RSS channel management."""

    VALIDATION_STATUSES = {400, 409, 422}
    NOT_FOUND_STATUSES = {400, 404, 422}

    def __init__(self, base_url: str, openapi_path: Optional[Path] = None, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._loader = TestDataLoader(_DATA_FILE)
        self._cleanup_lock = threading.Lock()
        self._cleanup_rss_channels: List[Tuple[Any, Any]] = []
        self._cleanup_information_sources: List[Any] = []
        self._cleanup_categories: List[Any] = []
        seed_login = self._loader.get_default("seed_login", {})
        self.seed_email = str(seed_login.get("email", "admin@newsradar.com"))
        self.seed_password = str(seed_login.get("password", "admin123"))
        self.openapi_spec = self._load_openapi(openapi_path)

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        self._reset_case_cleanup_registry()
        try:
            return self._run_case_impl(case)
        finally:
            self._cleanup_registered_resources()

    def _run_case_impl(self, case: Dict[str, str]) -> TestOutcome:
        case_id = str(case.get("Caso de Prueba", "")).strip().upper()

        if case_id == "RSS-001":
            return self._case_rss_001_create_valid(case)
        if case_id == "RSS-002":
            return self._case_rss_002_without_url(case)
        if case_id == "RSS-003":
            return self._case_rss_003_without_category_id(case)
        if case_id == "RSS-004":
            return self._case_rss_004_without_information_source_id(case)
        if case_id == "RSS-005":
            return self._case_rss_005_url_empty(case)
        if case_id == "RSS-006":
            return self._case_rss_006_url_invalid_format(case)
        if case_id == "RSS-007":
            return self._case_rss_007_url_too_long(case)
        if case_id == "RSS-008":
            return self._case_rss_008_url_not_accessible(case)
        if case_id == "RSS-009":
            return self._case_rss_009_url_not_rss(case)
        if case_id == "RSS-010":
            return self._case_rss_010_url_not_xml(case)
        if case_id == "RSS-011":
            return self._case_rss_011_category_id_not_found(case)
        if case_id == "RSS-012":
            return self._case_rss_012_information_source_not_found(case)
        if case_id == "RSS-013":
            return self._case_rss_013_path_body_consistency(case)
        if case_id == "RSS-014":
            return self._case_rss_014_duplicate_exact(case)
        if case_id == "RSS-015":
            return self._case_rss_015_duplicate_by_url_same_source(case)
        if case_id == "RSS-016":
            return self._case_rss_016_duplicate_by_url_global(case)
        if case_id == "RSS-017":
            return self._case_rss_017_duplicate_case_insensitive_url(case)
        if case_id == "RSS-018":
            return self._case_rss_018_duplicate_trailing_slash(case)
        if case_id == "RSS-019":
            return self._case_rss_019_url_normalization(case)
        if case_id == "RSS-020":
            return self._case_rss_020_payload_extra(case)
        if case_id == "RSS-021":
            return self._case_rss_021_list_by_source(case)
        if case_id == "RSS-022":
            return self._case_rss_022_list_by_source_not_found(case)
        if case_id == "RSS-023":
            return self._case_rss_023_validate_id_type(case)
        if case_id == "RSS-024":
            return self._case_rss_024_validate_category_relation(case)
        if case_id == "RSS-025":
            return self._case_rss_025_validate_information_source_relation(case)
        if case_id == "RSS-026":
            return self._case_rss_026_create_with_category_from_other_source(case)
        if case_id == "RSS-027":
            return self._case_rss_027_update_valid(case)
        if case_id == "RSS-028":
            return self._case_rss_028_update_to_not_rss(case)
        if case_id == "RSS-029":
            return self._case_rss_029_update_invalid_category(case)
        if case_id == "RSS-030":
            return self._case_rss_030_delete_existing(case)
        if case_id == "RSS-031":
            return self._case_rss_031_delete_nonexistent(case)
        if case_id == "RSS-032":
            return self._case_rss_032_concurrent_duplicates(case)
        if case_id == "RSS-033":
            return self._case_rss_033_utf8_url(case)
        if case_id == "RSS-034":
            return self._case_rss_034_response_schema(case)
        if case_id == "RSS-035":
            return self._case_rss_035_redirect_url(case)

        return self.nok(case, f"Caso RSS no implementado: {case_id}")

    def _case_rss_001_create_valid(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        self._cleanup_rss_channel(source_id, channel.get("id"))
        return self.ok(case, detail)

    def _case_rss_002_without_url(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(category_id=category_id)
        payload.pop("url", None)
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "crear rss sin url")

    def _case_rss_003_without_category_id(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(category_id=category_id)
        payload.pop("category_id", None)
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "crear rss sin category_id")

    def _case_rss_004_without_information_source_id(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request("POST", "/api/v1/information-sources/rss-channels", body={})
        return self._expect_statuses(case, status_code, request_error, {400, 404, 405, 422}, "falta information_source_id en path")

    def _case_rss_005_url_empty(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(url="", category_id=category_id)
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url vacia")

    def _case_rss_006_url_invalid_format(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(url=self._default_string("url_invalid", "not-a-uri"), category_id=category_id)
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url formato inválido")

    def _case_rss_007_url_too_long(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(
            url=self._default_string("url_too_long_prefix", "https://example.com/") + "a" * 2100,
            category_id=category_id,
        )
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url longitud maxima")

    def _case_rss_008_url_not_accessible(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(url=self._default_string("url_unreachable", "http://127.0.0.1:1/down"), category_id=category_id)
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url no accesible")

    def _case_rss_009_url_not_rss(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(url=self._default_string("url_not_rss", "https://example.com"), category_id=category_id)
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url no es rss")

    def _case_rss_010_url_not_xml(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(url=self._default_string("url_not_xml", "https://api.github.com"), category_id=category_id)
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 422}, "url no xml")

    def _case_rss_011_category_id_not_found(self, case: Dict[str, str]) -> TestOutcome:
        source_id, _, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(category_id=self._nonexistent_id())
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 404, 422}, "category_id inexistente")

    def _case_rss_012_information_source_not_found(self, case: Dict[str, str]) -> TestOutcome:
        _, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(category_id=category_id)
        status_code, _, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{self._nonexistent_id()}/rss-channels", body=payload
        )
        return self._expect_statuses(case, status_code, request_error, {400, 404, 422}, "information_source_id inexistente")

    def _case_rss_013_path_body_consistency(self, case: Dict[str, str]) -> TestOutcome:
        source_a_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        source_b, source_b_detail = self._create_information_source(self._valid_information_source_payload())
        if source_b is None:
            return self.nok(case, source_b_detail)

        channel, channel_detail = self._create_rss_channel(source_a_id, self._valid_payload(category_id=category_id))
        if channel is None:
            self._cleanup_information_source(source_b.get("id"))
            return self.nok(case, channel_detail)

        try:
            status_code, _, request_error = self._authorized_request(
                "PUT",
                f"/api/v1/information-sources/{source_b['id']}/rss-channels/{channel['id']}",
                body={"url": self._unique_rss_url_variant(), "category_id": category_id},
            )
            return self._expect_statuses(case, status_code, request_error, {400, 404, 422}, "consistencia source_id en path")
        finally:
            self._cleanup_rss_channel(source_a_id, channel.get("id"))
            self._cleanup_information_source(source_b.get("id"))

    def _case_rss_014_duplicate_exact(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(category_id=category_id)
        channel, detail = self._create_rss_channel(source_id, payload)
        if channel is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado exacto")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_015_duplicate_by_url_same_source(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_a_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        category_b_id, category_error = self._get_or_create_another_category_id(exclude_id=category_a_id)
        if category_error is not None:
            return self.nok(case, category_error)

        url = self._unique_rss_url_variant()
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(url=url, category_id=category_a_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "POST",
                f"/api/v1/information-sources/{source_id}/rss-channels",
                body=self._valid_payload(url=url, category_id=category_b_id),
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado por url misma source")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_016_duplicate_by_url_global(self, case: Dict[str, str]) -> TestOutcome:
        source_a_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        source_b, source_b_detail = self._create_information_source(self._valid_information_source_payload())
        if source_b is None:
            return self.nok(case, source_b_detail)

        url = self._unique_rss_url_variant()
        channel_a, detail_a = self._create_rss_channel(source_a_id, self._valid_payload(url=url, category_id=category_id))
        if channel_a is None:
            self._cleanup_information_source(source_b.get("id"))
            return self.nok(case, detail_a)

        try:
            status_code, response_body, request_error = self._authorized_request(
                "POST",
                f"/api/v1/information-sources/{source_b['id']}/rss-channels",
                body=self._valid_payload(url=url, category_id=category_id),
            )
            if request_error is not None:
                return self.nok(case, f"Error en duplicado global por url: {request_error}")
            if status_code in {400, 409, 422}:
                return self.ok(case, f"Duplicado global por url bloqueado con status {status_code}")
            if status_code == 201 and isinstance(response_body, dict):
                self._cleanup_rss_channel(source_b["id"], response_body.get("id"))
                return self.ok(case, "Duplicado global por url permitido segun regla del servicio")
            return self.nok(case, f"Status inesperado en duplicado global: {status_code}")
        finally:
            self._cleanup_rss_channel(source_a_id, channel_a.get("id"))
            self._cleanup_information_source(source_b.get("id"))

    def _case_rss_017_duplicate_case_insensitive_url(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        upper_url = self._unique_rss_url_variant().replace("https://", "HTTPS://")
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(url=upper_url, category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "POST",
                f"/api/v1/information-sources/{source_id}/rss-channels",
                body=self._valid_payload(url=upper_url.lower(), category_id=category_id),
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado url case-insensitive")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_018_duplicate_trailing_slash(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        url = self._unique_rss_url_variant().rstrip("/")
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(url=url, category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "POST",
                f"/api/v1/information-sources/{source_id}/rss-channels",
                body=self._valid_payload(url=f"{url}/", category_id=category_id),
            )
            return self._expect_statuses(case, status_code, request_error, self.VALIDATION_STATUSES, "duplicado trailing slash")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_019_url_normalization(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        base_url = self._unique_rss_url_variant().rstrip("/")
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(url=base_url.upper() + "/", category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            status_code, response_body, request_error = self._authorized_request(
                "POST",
                f"/api/v1/information-sources/{source_id}/rss-channels",
                body=self._valid_payload(url=base_url.lower(), category_id=category_id),
            )
            if request_error is not None:
                return self.nok(case, f"Error validando normalizacion url: {request_error}")
            if status_code in {400, 409, 422}:
                return self.ok(case, f"Normalizacion consistente, variante equivalente rechazada con {status_code}")
            if status_code == 201 and isinstance(response_body, dict):
                self._cleanup_rss_channel(source_id, response_body.get("id"))
                return self.nok(case, "Variantes equivalentes de URL fueron aceptadas como distintas")
            return self.nok(case, f"Status inesperado en normalizacion url: {status_code}")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_020_payload_extra(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(category_id=category_id)
        payload["unexpected"] = "x"
        status_code, response_body, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        if request_error is not None:
            return self.nok(case, f"Error enviando payload extra: {request_error}")
        if status_code in {400, 422}:
            return self.ok(case, f"Payload extra rechazado con status {status_code}")
        if status_code == 201 and isinstance(response_body, dict):
            try:
                if "unexpected" in response_body:
                    return self.nok(case, "Campo inesperado devuelto en respuesta")
                return self.ok(case, "Campo extra ignorado por el API")
            finally:
                self._cleanup_rss_channel(source_id, response_body.get("id"))
        return self.nok(case, f"Status inesperado en payload extra: {status_code}")

    def _case_rss_021_list_by_source(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, channel_detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, channel_detail)
        try:
            status_code, response_body, request_error = self._authorized_request(
                "GET", f"/api/v1/information-sources/{source_id}/rss-channels", body=None
            )
            if request_error is not None:
                return self.nok(case, f"Error listando rss por source: {request_error}")
            if status_code != 200:
                return self.nok(case, f"List rss por source devolvió {status_code}, esperado 200")
            if not isinstance(response_body, list):
                return self.nok(case, f"List rss no devolvió lista JSON: {response_body!r}")
            mismatched = [
                item for item in response_body
                if isinstance(item, dict) and int(item.get("information_source_id", -1)) != int(source_id)
            ]
            if mismatched:
                return self.nok(case, f"Items con information_source_id incorrecto: {mismatched!r}")
            return self.ok(case, f"Listado de RSS por source correcto ({len(response_body)} items)")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_022_list_by_source_not_found(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request(
            "GET", f"/api/v1/information-sources/{self._nonexistent_id()}/rss-channels", body=None
        )
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "listar rss con source inexistente")

    def _case_rss_023_validate_id_type(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            channel_id = channel.get("id")
            if not isinstance(channel_id, int):
                return self.nok(case, f"id de rss no es entero: {channel_id!r}")
            return self.ok(case, "Tipo de id de RSS validado")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_024_validate_category_relation(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            if int(channel.get("category_id", -1)) != int(category_id):
                return self.nok(case, f"category_id inconsistente en respuesta: {channel!r}")
            return self.ok(case, "Relacion category_id correcta")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_025_validate_information_source_relation(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            if int(channel.get("information_source_id", -1)) != int(source_id):
                return self.nok(case, f"information_source_id inconsistente: {channel!r}")
            return self.ok(case, "Relacion information_source_id correcta")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_026_create_with_category_from_other_source(self, case: Dict[str, str]) -> TestOutcome:
        source_a_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        source_b, source_b_detail = self._create_information_source(self._valid_information_source_payload())
        if source_b is None:
            return self.nok(case, source_b_detail)
        channel, detail = self._create_rss_channel(source_b["id"], self._valid_payload(category_id=category_id))
        if channel is None:
            self._cleanup_information_source(source_b.get("id"))
            return self.nok(case, detail)
        self._cleanup_rss_channel(source_b["id"], channel.get("id"))
        self._cleanup_information_source(source_b.get("id"))
        return self.ok(case, "RSS creado con category valida y source distinto")

    def _case_rss_027_update_valid(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            update_payload = {"url": self._unique_rss_url_variant(), "category_id": category_id}
            status_code, response_body, request_error = self._authorized_request(
                "PUT",
                f"/api/v1/information-sources/{source_id}/rss-channels/{channel['id']}",
                body=update_payload,
            )
            if request_error is not None:
                return self.nok(case, f"Error actualizando rss: {request_error}")
            if status_code != 200:
                return self.nok(case, f"Update rss devolvió {status_code}, esperado 200")
            if not isinstance(response_body, dict) or response_body.get("url") != update_payload["url"]:
                return self.nok(case, f"Respuesta update invalida: {response_body!r}")
            return self.ok(case, "RSS actualizado correctamente")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_028_update_to_not_rss(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "PUT",
                f"/api/v1/information-sources/{source_id}/rss-channels/{channel['id']}",
                body={"url": self._default_string("url_not_rss", "https://example.com"), "category_id": category_id},
            )
            return self._expect_statuses(case, status_code, request_error, {400, 422}, "update url no rss")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_029_update_invalid_category(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            status_code, _, request_error = self._authorized_request(
                "PUT",
                f"/api/v1/information-sources/{source_id}/rss-channels/{channel['id']}",
                body={"url": self._unique_rss_url_variant(), "category_id": self._nonexistent_id()},
            )
            return self._expect_statuses(case, status_code, request_error, {400, 404, 422}, "update category_id inválido")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_030_delete_existing(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, detail)

        status_code, _, request_error = self._authorized_request(
            "DELETE", f"/api/v1/information-sources/{source_id}/rss-channels/{channel['id']}", body=None
        )
        if request_error is not None:
            return self.nok(case, f"Error eliminando rss: {request_error}")
        if status_code != 204:
            self._cleanup_rss_channel(source_id, channel.get("id"))
            return self.nok(case, f"Delete rss devolvió {status_code}, esperado 204")
        return self.ok(case, "RSS eliminado correctamente")

    def _case_rss_031_delete_nonexistent(self, case: Dict[str, str]) -> TestOutcome:
        status_code, _, request_error = self._authorized_request(
            "DELETE", f"/api/v1/information-sources/{self._nonexistent_id()}/rss-channels/{self._nonexistent_id()}", body=None
        )
        return self._expect_statuses(case, status_code, request_error, self.NOT_FOUND_STATUSES, "delete rss inexistente")

    def _case_rss_032_concurrent_duplicates(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)

        payload = self._valid_payload(url=self._unique_rss_url_variant(), category_id=category_id)
        results: List[Tuple[int, Any, Optional[str]]] = []
        created_ids: List[Any] = []

        def worker() -> None:
            status_code, response_body, request_error = self._authorized_request(
                "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
            )
            results.append((status_code, response_body, request_error))

        thread_a = threading.Thread(target=worker)
        thread_b = threading.Thread(target=worker)
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        for status_code, response_body, request_error in results:
            if request_error is not None:
                return self.nok(case, f"Error en concurrencia de duplicados: {request_error}")
            if status_code == 201 and isinstance(response_body, dict):
                created_ids.append(response_body.get("id"))

        statuses = [item[0] for item in results]
        success_count = statuses.count(201)
        conflict_count = sum(1 for s in statuses if s in {400, 409, 422})

        for channel_id in created_ids:
            self._cleanup_rss_channel(source_id, channel_id)

        if success_count >= 1 and conflict_count >= 1:
            return self.ok(case, f"Concurrencia correcta: statuses={statuses}")
        return self.nok(case, f"Concurrencia no genero 1 exito + 1 fallo: statuses={statuses}")

    def _case_rss_033_utf8_url(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)

        payload = self._valid_payload(url=self._default_string("url_utf8", "https://example.com/rss/%C3%B1"), category_id=category_id)
        status_code, response_body, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        if request_error is not None:
            return self.nok(case, f"Error creando rss UTF-8: {request_error}")
        if status_code == 201 and isinstance(response_body, dict):
            self._cleanup_rss_channel(source_id, response_body.get("id"))
            return self.ok(case, "URL UTF-8 aceptada")
        if status_code in {400, 422}:
            return self.ok(case, f"URL UTF-8 rechazada con validacion controlada ({status_code})")
        return self.nok(case, f"Status inesperado para URL UTF-8: {status_code}")

    def _case_rss_034_response_schema(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        channel, detail = self._create_rss_channel(source_id, self._valid_payload(category_id=category_id))
        if channel is None:
            return self.nok(case, detail)
        try:
            schema = self._get_openapi_rss_schema()
            if not schema:
                return self.nok(case, "No se pudo resolver components.schemas.RSSChannel en OpenAPI")

            properties = schema.get("properties", {})
            if not isinstance(properties, dict) or not properties:
                return self.nok(case, "Schema RSSChannel sin properties validas")

            allowed_keys = set(properties.keys())
            required_keys = set(schema.get("required", [])) if isinstance(schema.get("required"), list) else set()
            actual_keys = set(channel.keys())

            missing_required = sorted(required_keys - actual_keys)
            unexpected = sorted(actual_keys - allowed_keys)
            if missing_required:
                return self.nok(case, f"Faltan campos requeridos por OpenAPI: {missing_required}")
            if unexpected:
                return self.nok(case, f"Campos inesperados fuera de OpenAPI: {unexpected}")

            type_errors: List[str] = []
            for key in sorted(actual_keys & allowed_keys):
                if not self._matches_openapi_type(channel.get(key), properties.get(key, {})):
                    expected_type = self._describe_openapi_type(properties.get(key, {}))
                    actual_type = type(channel.get(key)).__name__
                    type_errors.append(f"{key}: esperado {expected_type}, obtenido {actual_type}")
            if type_errors:
                return self.nok(case, "Tipos incompatibles con OpenAPI: " + "; ".join(type_errors))

            return self.ok(case, "RSS-034 válido: respuesta alineada al schema RSSChannel de OpenAPI")
        finally:
            self._cleanup_rss_channel(source_id, channel.get("id"))

    def _case_rss_035_redirect_url(self, case: Dict[str, str]) -> TestOutcome:
        source_id, category_id, setup_error = self._prepare_source_and_category()
        if setup_error is not None:
            return self.nok(case, setup_error)
        payload = self._valid_payload(url=self._default_string("url_redirect", "http://feeds.bbci.co.uk/news/rss.xml"), category_id=category_id)
        status_code, response_body, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        if request_error is not None:
            return self.nok(case, f"Error probando URL con redirect: {request_error}")
        if status_code == 201 and isinstance(response_body, dict):
            self._cleanup_rss_channel(source_id, response_body.get("id"))
            return self.ok(case, "URL con redirect aceptada")
        if status_code in {400, 422}:
            return self.ok(case, f"URL con redirect rechazada por validacion ({status_code})")
        return self.nok(case, f"Status inesperado para URL con redirect: {status_code}")

    def _prepare_source_and_category(self) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        source, source_detail = self._create_information_source(self._valid_information_source_payload())
        if source is None:
            return None, None, source_detail
        category_id, category_error = self._get_or_create_category_id()
        if category_error is not None:
            self._cleanup_information_source(source.get("id"))
            return None, None, category_error
        return int(source["id"]), int(category_id), None

    def _valid_payload(self, *, url: Optional[str] = None, category_id: int) -> Dict[str, Any]:
        return {
            "url": url if url is not None else self._unique_rss_url_variant(),
            "category_id": category_id,
        }

    def _valid_information_source_payload(self) -> Dict[str, str]:
        defaults = self._loader.get_default("information_source_payload", {})
        name_prefix = str(defaults.get("name_prefix", "RSS Source"))
        url_base = str(defaults.get("url_base", "https://example.com/source"))
        unique = uuid.uuid4().hex[:10]
        return {
            "name": f"{name_prefix} {unique}",
            "url": f"{url_base}/{unique}",
        }

    def _default_category_payload(self) -> Dict[str, str]:
        defaults = self._loader.get_default("category_payload", {})
        return {
            "name": str(defaults.get("name", "Sociedad")),
            "source": str(defaults.get("source", "medtop:14000000")),
        }

    def _unique_rss_url_variant(self) -> str:
        defaults = self._loader.get_default("rss_payload", {})
        url_base = str(defaults.get("url_base", "https://hnrss.org/frontpage"))
        unique = uuid.uuid4().hex[:8]
        separator = "&" if "?" in url_base else "?"
        return f"{url_base}{separator}uid={unique}"

    def _default_string(self, key: str, fallback: str) -> str:
        strings = self._loader.get_default("strings", {})
        return str(strings.get(key, fallback))

    def _nonexistent_id(self) -> int:
        ids = self._loader.get_default("ids", {})
        try:
            return int(ids.get("nonexistent", 99999999))
        except Exception:
            return 99999999

    def _create_information_source(self, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, request_error = self._authorized_request("POST", "/api/v1/information-sources", body=payload)
        if request_error is not None:
            return None, f"Error creando information source: {request_error}"
        if status_code != 201:
            return None, f"Crear information source devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear information source no devolvió objeto JSON: {response_body!r}"
        self._register_information_source_for_cleanup(response_body.get("id"))
        return response_body, f"Information source creada con id {response_body.get('id')}"

    def _get_or_create_category_id(self) -> Tuple[Optional[int], Optional[str]]:
        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/categories", body=None)
        if request_error is None and status_code == 200 and isinstance(response_body, list):
            for item in response_body:
                if isinstance(item, dict) and isinstance(item.get("id"), int):
                    return int(item["id"]), None

        create_status, create_body, create_error = self._authorized_request(
            "POST", "/api/v1/categories", body=self._default_category_payload()
        )
        if create_error is not None:
            return None, f"Error creando categoria para RSS: {create_error}"
        if create_status == 201 and isinstance(create_body, dict) and isinstance(create_body.get("id"), int):
            self._register_category_for_cleanup(create_body.get("id"))
            return int(create_body["id"]), None

        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/categories", body=None)
        if request_error is None and status_code == 200 and isinstance(response_body, list):
            for item in response_body:
                if isinstance(item, dict) and isinstance(item.get("id"), int):
                    return int(item["id"]), None

        return None, f"No se pudo obtener category_id válido para RSS (create_status={create_status}, create_body={create_body!r})"

    def _get_or_create_another_category_id(self, exclude_id: int) -> Tuple[Optional[int], Optional[str]]:
        status_code, response_body, request_error = self._authorized_request("GET", "/api/v1/categories", body=None)
        if request_error is None and status_code == 200 and isinstance(response_body, list):
            for item in response_body:
                if isinstance(item, dict) and isinstance(item.get("id"), int) and int(item["id"]) != int(exclude_id):
                    return int(item["id"]), None
        return int(exclude_id), None

    def _create_rss_channel(self, source_id: int, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        status_code, response_body, request_error = self._authorized_request(
            "POST", f"/api/v1/information-sources/{source_id}/rss-channels", body=payload
        )
        if request_error is not None:
            return None, f"Error creando rss channel: {request_error}"
        if status_code != 201:
            return None, f"Crear rss channel devolvió {status_code}, esperado 201. Respuesta: {response_body!r}"
        if not isinstance(response_body, dict):
            return None, f"Crear rss channel no devolvió objeto JSON: {response_body!r}"
        self._register_rss_channel_for_cleanup(source_id, response_body.get("id"))
        return response_body, f"RSS channel creado con id {response_body.get('id')}"

    def _cleanup_rss_channel(self, source_id: Any, channel_id: Any) -> None:
        if source_id in (None, "") or channel_id in (None, ""):
            return
        try:
            status_code, _, request_error = self._authorized_request(
                "DELETE",
                f"/api/v1/information-sources/{source_id}/rss-channels/{channel_id}",
                body=None,
            )
            if request_error is None and status_code in {200, 202, 204, 404}:
                self._unregister_rss_channel_cleanup(source_id, channel_id)
        except Exception:
            return

    def _cleanup_information_source(self, source_id: Any) -> None:
        if source_id in (None, ""):
            return
        try:
            status_code, _, request_error = self._authorized_request(
                "DELETE",
                f"/api/v1/information-sources/{source_id}",
                body=None,
            )
            if request_error is None and status_code in {200, 202, 204, 404}:
                self._unregister_information_source_cleanup(source_id)
        except Exception:
            return

    def _cleanup_category(self, category_id: Any) -> None:
        if category_id in (None, ""):
            return
        try:
            status_code, _, request_error = self._authorized_request(
                "DELETE",
                f"/api/v1/categories/{category_id}",
                body=None,
            )
            if request_error is None and status_code in {200, 202, 204, 404}:
                self._unregister_category_cleanup(category_id)
        except Exception:
            return

    def _reset_case_cleanup_registry(self) -> None:
        with self._cleanup_lock:
            self._cleanup_rss_channels = []
            self._cleanup_information_sources = []
            self._cleanup_categories = []

    def _register_rss_channel_for_cleanup(self, source_id: Any, channel_id: Any) -> None:
        if source_id in (None, "") or channel_id in (None, ""):
            return
        item = (source_id, channel_id)
        with self._cleanup_lock:
            self._cleanup_rss_channels.append(item)

    def _register_information_source_for_cleanup(self, source_id: Any) -> None:
        if source_id in (None, ""):
            return
        with self._cleanup_lock:
            self._cleanup_information_sources.append(source_id)

    def _register_category_for_cleanup(self, category_id: Any) -> None:
        if category_id in (None, ""):
            return
        with self._cleanup_lock:
            self._cleanup_categories.append(category_id)

    def _unregister_rss_channel_cleanup(self, source_id: Any, channel_id: Any) -> None:
        item = (source_id, channel_id)
        with self._cleanup_lock:
            self._cleanup_rss_channels = [existing for existing in self._cleanup_rss_channels if existing != item]

    def _unregister_information_source_cleanup(self, source_id: Any) -> None:
        with self._cleanup_lock:
            self._cleanup_information_sources = [existing for existing in self._cleanup_information_sources if existing != source_id]

    def _unregister_category_cleanup(self, category_id: Any) -> None:
        with self._cleanup_lock:
            self._cleanup_categories = [existing for existing in self._cleanup_categories if existing != category_id]

    def _cleanup_registered_resources(self) -> None:
        with self._cleanup_lock:
            channels = list(self._cleanup_rss_channels)
            sources = list(self._cleanup_information_sources)
            categories = list(self._cleanup_categories)

        for source_id, channel_id in reversed(channels):
            self._cleanup_rss_channel(source_id, channel_id)
        for source_id in reversed(sources):
            self._cleanup_information_source(source_id)
        for category_id in reversed(categories):
            self._cleanup_category(category_id)

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

    def _get_openapi_rss_schema(self) -> Dict[str, Any]:
        components = self.openapi_spec.get("components", {}) if isinstance(self.openapi_spec, dict) else {}
        schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
        rss_schema = schemas.get("RSSChannel", {}) if isinstance(schemas, dict) else {}
        return rss_schema if isinstance(rss_schema, dict) else {}

    @staticmethod
    def _matches_openapi_type(value: Any, schema: Dict[str, Any]) -> bool:
        if not isinstance(schema, dict):
            return True

        if "anyOf" in schema and isinstance(schema.get("anyOf"), list):
            return any(
                RSSChannelManagementScopeTests._matches_openapi_type(value, option)
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
        if request_error is None and method.upper() == "POST" and status_code == 201 and isinstance(response_body, dict):
            path_parts = [part for part in path.split("/") if part]
            if path == "/api/v1/information-sources":
                self._register_information_source_for_cleanup(response_body.get("id"))
            elif path == "/api/v1/categories":
                self._register_category_for_cleanup(response_body.get("id"))
            elif len(path_parts) == 6 and path_parts[:3] == ["api", "v1", "information-sources"] and path_parts[5] == "rss-channels":
                self._register_rss_channel_for_cleanup(path_parts[3], response_body.get("id"))
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