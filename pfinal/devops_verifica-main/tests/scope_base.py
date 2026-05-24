from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple


@dataclass
class TestOutcome:
    case_id: str
    status: str
    explanation: str
    detail: str


class BaseScopeTests:
    """Base contract for tests grouped by scope (ambito)."""

    def _cleanup_reset(self) -> None:
        self._cleanup_actions: List[Tuple[Callable[..., None], Tuple[Any, ...]]] = []

    def _cleanup_register(self, action: Callable[..., None], *args: Any) -> None:
        if not hasattr(self, "_cleanup_actions"):
            self._cleanup_reset()
        self._cleanup_actions.append((action, args))

    def _cleanup_run(self) -> None:
        actions = list(getattr(self, "_cleanup_actions", []))
        self._cleanup_reset()
        for action, args in reversed(actions):
            try:
                action(*args)
            except Exception:
                continue

    def run_case(self, case: Dict[str, str]) -> TestOutcome:
        raise NotImplementedError("run_case must be implemented by scope classes")

    @staticmethod
    def ok(case: Dict[str, str], detail: str) -> TestOutcome:
        return TestOutcome(
            case_id=case["Caso de Prueba"],
            status="OK",
            explanation=case["Comprobación"],
            detail=detail,
        )

    @staticmethod
    def nok(case: Dict[str, str], detail: str) -> TestOutcome:
        return TestOutcome(
            case_id=case["Caso de Prueba"],
            status="NOK",
            explanation=case["Comprobación"],
            detail=detail,
        )

    @staticmethod
    def warning(case: Dict[str, str], detail: str) -> TestOutcome:
        return TestOutcome(
            case_id=case["Caso de Prueba"],
            status="OK",
            explanation=case["Comprobación"],
            detail=f"WARNING: {detail}",
        )
