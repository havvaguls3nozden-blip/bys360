from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

SETTINGS_FILE_NAME = "ai_governance_settings.json"
DEFAULT_SETTINGS: dict[str, Any] = {
    "module_quality_floor": 65,
    "prompt_quality_floor": 60,
    "backlog_limit": 8,
    "negative_feedback_limit": 3,
    "default_lookback_days": 30,
    "weekly_summary": {
        "lookback_days": 7,
        "top_limit": 5,
        "show_prompt_breakdown": True,
        "show_module_breakdown": True,
        "include_actions": True,
    },
}


def _settings_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / SETTINGS_FILE_NAME


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result.get(key) or {}, value)
        else:
            result[key] = value
    return result


def get_ai_governance_settings() -> dict[str, Any]:
    path = _settings_path()
    if not path.exists():
        return deepcopy(DEFAULT_SETTINGS)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return deepcopy(DEFAULT_SETTINGS)
    if not isinstance(payload, dict):
        return deepcopy(DEFAULT_SETTINGS)
    return _merge_dict(DEFAULT_SETTINGS, payload)


def save_ai_governance_settings(payload: dict[str, Any]) -> dict[str, Any]:
    settings = _merge_dict(DEFAULT_SETTINGS, payload or {})
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    return settings


def get_governance_thresholds() -> dict[str, int]:
    settings = get_ai_governance_settings()
    return {
        "module_quality_floor": int(settings.get("module_quality_floor") or 65),
        "prompt_quality_floor": int(settings.get("prompt_quality_floor") or 60),
        "backlog_limit": int(settings.get("backlog_limit") or 8),
        "negative_feedback_limit": int(settings.get("negative_feedback_limit") or 3),
        "default_lookback_days": int(settings.get("default_lookback_days") or 30),
    }


def get_weekly_summary_settings() -> dict[str, Any]:
    settings = get_ai_governance_settings()
    summary = settings.get("weekly_summary") if isinstance(settings.get("weekly_summary"), dict) else {}
    return _merge_dict(DEFAULT_SETTINGS["weekly_summary"], summary)