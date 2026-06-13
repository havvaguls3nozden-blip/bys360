from __future__ import annotations



import json
from pathlib import Path
from typing import Any, Dict

from flask import current_app


class HierarchySettingsService:
    def __init__(self, config_relative_path: str = "config/hierarchy_templates_v1.json"):
        root = Path(current_app.root_path).parent if current_app else Path.cwd()
        self.config_path = root / config_relative_path

    def load(self) -> Dict[str, Any]:
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def save(self, payload: Dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")