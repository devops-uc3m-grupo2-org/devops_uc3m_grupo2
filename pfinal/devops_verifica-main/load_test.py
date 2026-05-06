from __future__ import annotations

import os
import random
import threading
from typing import Any, Dict, Optional

from locust import HttpUser, constant_throughput, events, task


"""Simple Locust load test for race-condition pressure on user creation/deletion.

Design:
- Run with 100 users and spawn-rate 100 to target about 100 requests/second.
- Each Locust user executes about 1 task/second via constant_throughput(1).
- Tasks repeatedly create and delete the same small pool of valid users.
- A gestor role id is ensured as a precondition before user creation.
- Scenario `pool` races over a shared pool of emails.
- Scenario `fixed` races over one single email to maximize collisions.

Example:
    locust -f load_test.py --host http://localhost:8000 --users 100 --spawn-rate 100 --headless --run-time 2m
"""


USER_POOL_SIZE = int(os.getenv("LR_USER_POOL_SIZE", "20"))
LOGIN_EMAIL = os.getenv("LR_LOGIN_EMAIL", "admin@newsradar.com")
LOGIN_PASSWORD = os.getenv("LR_LOGIN_PASSWORD", "admin123")
USER_PASSWORD = os.getenv("LR_USER_PASSWORD", "Valid123")
USER_ORGANIZATION = os.getenv("LR_USER_ORGANIZATION", "LoadTests")
SCENARIO = os.getenv("LR_SCENARIO", "pool").strip().lower() or "pool"
FIXED_EMAIL = os.getenv("LR_FIXED_EMAIL", "race-user-fixed@example.com")


class _SharedState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.gestor_role_id: Optional[int] = None
        self.user_ids_by_email: Dict[str, int] = {}
        self.emails = [f"race-user-{index:02d}@example.com" for index in range(USER_POOL_SIZE)]
        self.status_counts: Dict[str, int] = {"201": 0, "204": 0, "404": 0, "409": 0}


STATE = _SharedState()


def _record_status(status_code: int) -> None:
    key = str(status_code)
    with STATE.lock:
        STATE.status_counts[key] = int(STATE.status_counts.get(key, 0)) + 1


@events.quitting.add_listener
def _print_summary(environment, **kwargs) -> None:
    del environment, kwargs
    with STATE.lock:
        summary = dict(STATE.status_counts)
    print(
        "LOAD TEST SUMMARY "
        f"scenario={SCENARIO} "
        f"201={summary.get('201', 0)} "
        f"204={summary.get('204', 0)} "
        f"404={summary.get('404', 0)} "
        f"409={summary.get('409', 0)}"
    )


class RaceConditionLoadUser(HttpUser):
    wait_time = constant_throughput(1)

    def on_start(self) -> None:
        self.token: Optional[str] = None
        if not self._login():
            return
        self._ensure_gestor_role_id()

    def _auth_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _login(self) -> bool:
        payload = {"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD}
        with self.client.post("/api/v1/auth/login", json=payload, name="auth_login", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"login failed with {response.status_code}")
                return False
            try:
                body = response.json()
            except Exception:
                response.failure("login did not return JSON")
                return False

            token = body.get("access_token")
            if not isinstance(token, str) or not token:
                response.failure("login missing access_token")
                return False

            self.token = token
            response.success()
            return True

    def _ensure_gestor_role_id(self) -> Optional[int]:
        with STATE.lock:
            if STATE.gestor_role_id is not None:
                return STATE.gestor_role_id

        role_id = self._find_gestor_role_id()
        if role_id is None:
            role_id = self._create_gestor_role_id()
        if role_id is None:
            return None

        with STATE.lock:
            STATE.gestor_role_id = role_id
        return role_id

    def _find_gestor_role_id(self) -> Optional[int]:
        with self.client.get("/api/v1/roles", headers=self._auth_headers(), name="roles_get", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"roles_get failed with {response.status_code}")
                return None
            try:
                body = response.json()
            except Exception:
                response.failure("roles_get did not return JSON")
                return None

            if not isinstance(body, list):
                response.failure("roles_get did not return an array")
                return None

            for item in body:
                if not isinstance(item, dict):
                    continue
                if str(item.get("name", "")).strip().lower() == "gestor" and isinstance(item.get("id"), int):
                    response.success()
                    return int(item["id"])

            response.success()
            return None

    def _create_gestor_role_id(self) -> Optional[int]:
        payload = {"name": "gestor"}
        with self.client.post("/api/v1/roles", json=payload, headers=self._auth_headers(), name="roles_post_gestor", catch_response=True) as response:
            if response.status_code == 201:
                try:
                    body = response.json()
                except Exception:
                    response.failure("roles_post_gestor did not return JSON")
                    return None
                role_id = body.get("id")
                if not isinstance(role_id, int):
                    response.failure("roles_post_gestor missing integer id")
                    return None
                response.success()
                return role_id

            if response.status_code in {400, 409, 422}:
                response.success()
                return self._find_gestor_role_id()

            response.failure(f"roles_post_gestor failed with {response.status_code}")
            return None

    def _pick_email(self) -> str:
        if SCENARIO == "fixed":
            return FIXED_EMAIL
        return random.choice(STATE.emails)

    @task(3)
    def create_valid_user(self) -> None:
        role_id = self._ensure_gestor_role_id()
        if role_id is None:
            return

        email = self._pick_email()
        payload = {
            "email": email,
            "first_name": "Race",
            "last_name": "Condition",
            "organization": USER_ORGANIZATION,
            "password": USER_PASSWORD,
            "role_ids": [role_id],
        }

        with self.client.post("/api/v1/users", json=payload, headers=self._auth_headers(), name="users_post_race", catch_response=True) as response:
            if response.status_code == 201:
                _record_status(response.status_code)
                try:
                    body = response.json()
                except Exception:
                    response.failure("users_post_race did not return JSON")
                    return

                user_id = body.get("id")
                if not isinstance(user_id, int):
                    response.failure("users_post_race missing integer id")
                    return

                with STATE.lock:
                    STATE.user_ids_by_email[email] = user_id
                response.success()
                return

            if response.status_code in {400, 409, 422}:
                _record_status(response.status_code)
                response.success()
                return

            response.failure(f"unexpected status {response.status_code}")

    @task(2)
    def delete_same_user(self) -> None:
        email = self._pick_email()
        with STATE.lock:
            user_id = STATE.user_ids_by_email.get(email)

        if user_id is None:
            return

        with self.client.delete(
            f"/api/v1/users/{user_id}",
            headers=self._auth_headers(),
            name="users_delete_race",
            catch_response=True,
        ) as response:
            if response.status_code == 204:
                _record_status(response.status_code)
                with STATE.lock:
                    if STATE.user_ids_by_email.get(email) == user_id:
                        STATE.user_ids_by_email.pop(email, None)
                response.success()
                return

            if response.status_code in {400, 404, 422}:
                _record_status(response.status_code)
                with STATE.lock:
                    if STATE.user_ids_by_email.get(email) == user_id:
                        STATE.user_ids_by_email.pop(email, None)
                response.success()
                return

            response.failure(f"unexpected status {response.status_code}")