from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class TestDataLoader:
    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file
        with self.data_file.open("r", encoding="utf-8") as file_handle:
            self.data = json.load(file_handle)

    def get_default(self, name: str, fallback: Any = None) -> Any:
        defaults = self.data.get("defaults", {})
        return defaults.get(name, fallback)

    def get_case_data(self, case_id: str) -> Dict[str, Any]:
        cases = self.data.get("cases", {})
        case_data = cases.get(case_id, {})
        if not isinstance(case_data, dict):
            return {}
        return case_data