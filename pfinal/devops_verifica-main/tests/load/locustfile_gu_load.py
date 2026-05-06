from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

from locust import HttpUser, constant, events, task


RESULTS: Dict[str, Any] = {
    "scenario": "",
    "status_counts": {},
    "response_times_ms": [],
    "total_requests": 0,
    "auth_failed": False,
    "errors": [],
}


def _record_status(status_code: int, response_time_ms: float) -> None:
    key = str(status_code)
    RESULTS["status_counts"][key] = int(RESULTS["status_counts"].get(key, 0)) + 1
    RESULTS["response_times_ms"].append(float(response_time_ms))
    RESULTS["total_requests"] = int(RESULTS["total_requests"]) + 1


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = max(0, min(len(sorted_values) - 1, int(round((p / 100.0) * (len(sorted_values) - 1)))))
    return float(sorted_values[index])


@events.quitting.add_listener
def _on_quitting(environment, **kwargs):
    response_times = RESULTS.get("response_times_ms", [])
    avg_ms = float(sum(response_times) / len(response_times)) if response_times else 0.0
    p95_ms = _percentile(response_times, 95.0)

    payload = {
        "scenario": RESULTS.get("scenario", ""),
        "status_counts": RESULTS.get("status_counts", {}),
        "total_requests": int(RESULTS.get("total_requests", 0)),
        "avg_ms": avg_ms,
        "p95_ms": p95_ms,
        "auth_failed": bool(RESULTS.get("auth_failed", False)),
        "errors": RESULTS.get("errors", []),
    }

    result_file = os.getenv("LR_RESULT_FILE")
    if result_file:
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True)


class NewsRadarLoadUser(HttpUser):
    wait_time = constant(0)

    def on_start(self):
        self.scenario = os.getenv("LR_SCENARIO", "")
        RESULTS["scenario"] = self.scenario

        self.seed_email = os.getenv("LR_LOGIN_EMAIL", "admin@newsradar.com")
        self.seed_password = os.getenv("LR_LOGIN_PASSWORD", "admin123")
        self.fixed_email = os.getenv("LR_FIXED_EMAIL", f"load-test-{int(time.time())}@example.com")
        self.user_counter = 0
        self.token: Optional[str] = None
        self.role_id: Optional[int] = None

        login_ok = self._login()
        if not login_ok:
            RESULTS["auth_failed"] = True
            return

        self.role_id = self._get_first_role_id()
        if self.role_id is None:
            RESULTS["errors"].append("No role id found from /api/v1/roles")

    @task
    def run_selected_scenario(self):
        if RESULTS.get("auth_failed"):
            return

        if self.scenario == "GU-057":
            self._run_rate_limiting()
            return

        if self.scenario == "GU-039":
            self._run_sla_load()
            return

        if self.scenario == "GU-036":
            self._run_concurrent_same_email()
            return

        self._run_sla_load()

    def _auth_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _login(self) -> bool:
        payload = {"email": self.seed_email, "password": self.seed_password}
        with self.client.post("/api/v1/auth/login", json=payload, name="auth_login", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Login failed with {response.status_code}")
                return False
            try:
                body = response.json()
                token = body.get("access_token")
            except Exception:
                response.failure("Login did not return JSON")
                return False
            if not isinstance(token, str) or not token:
                response.failure("Login missing access_token")
                return False
            self.token = token
            response.success()
            return True

    def _get_first_role_id(self) -> Optional[int]:
        with self.client.get("/api/v1/roles", headers=self._auth_headers(), name="roles_get", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"roles_get failed with {response.status_code}")
                return None
            try:
                body = response.json()
            except Exception:
                response.failure("roles_get did not return JSON")
                return None

            if not isinstance(body, list) or not body:
                response.failure("roles_get empty list")
                return None

            first = body[0] if isinstance(body[0], dict) else {}
            role_id = first.get("id")
            if not isinstance(role_id, int):
                response.failure("roles_get first role missing integer id")
                return None

            response.success()
            return role_id

    def _run_rate_limiting(self) -> None:
        with self.client.get("/api/v1/users", headers=self._auth_headers(), name="users_get_rate_limit", catch_response=True) as response:
            _record_status(response.status_code, response.elapsed.total_seconds() * 1000.0)
            if response.status_code in {200, 429}:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    def _run_sla_load(self) -> None:
        with self.client.get("/api/v1/users", headers=self._auth_headers(), name="users_get_sla", catch_response=True) as response:
            _record_status(response.status_code, response.elapsed.total_seconds() * 1000.0)
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    def _run_concurrent_same_email(self) -> None:
        if self.role_id is None:
            return

        self.user_counter += 1
        payload = {
            "email": self.fixed_email,
            "first_name": f"Load{self.user_counter}",
            "last_name": "Parallel",
            "organization": "LoadTests",
            "password": "Valid123",
            "role_ids": [self.role_id],
        }

        with self.client.post("/api/v1/users", json=payload, headers=self._auth_headers(), name="users_post_same_email", catch_response=True) as response:
            _record_status(response.status_code, response.elapsed.total_seconds() * 1000.0)
            if response.status_code in {201, 400, 409, 422}:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
