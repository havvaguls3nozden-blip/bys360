from __future__ import annotations



import json
from pathlib import Path
from typing import Any, Dict, Optional

from flask import current_app


class HierarchyPositionRegistryService:
    def __init__(self, config_relative_path: str = "config/hierarchy_position_registry_v1.json"):
        root = Path(current_app.root_path).parent if current_app else Path.cwd()
        self.config_path = root / config_relative_path

    def load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {"version": 1, "unit_overrides": []}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def save(self, payload: Dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def find_unit_override(self, birim: str, ust_birim: str) -> Optional[Dict[str, Any]]:
        b = (birim or "").strip().upper()
        u = (ust_birim or "").strip().upper()
        for row in self.load().get("unit_overrides", []):
            if (row.get("birim") or "").strip().upper() == b and (row.get("ust_birim") or "").strip().upper() == u:
                return row
        return None