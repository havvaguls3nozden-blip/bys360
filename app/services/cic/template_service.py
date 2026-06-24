from __future__ import annotations

from app.extensions import db

from app.models import User

# BYS360 P8 template migration imports


import logging
from typing import Any
try:
    from flask import current_app
except Exception:  # pragma: no cover - optional Flask context
    current_app = None  # type: ignore
from app.services.cic.repository import (
    get_setting, set_setting,
)
from app.services.cic.task_contract import BASE_KEY, TASK_DEFINITIONS
logger = logging.getLogger(__name__)


"""BYS360 CIC facade slice.

This module is intentionally facade-only in P5.
The legacy implementation remains in app.services.corporate_information_center.
Routes, template names, endpoint contracts and public function names are not changed.
"""



__all__ = [
    "_cic_phase6_template_quality",
    "_render_template_text",
    "get_template",
    "save_templates",
]

# BYS360 P8 migrated legacy dependency bridge
try:
    from app.services import corporate_information_center as _legacy_cic
except Exception:  # pragma: no cover
    _legacy_cic = None  # type: ignore
_P8_LEGACY_NAMES = ['_cic_phase6_item', '_cic_v40_previous_render_template_text', '_cic_v40_service_year', '_cic_v40_special_days_today', 'any']
for _p8_name in _P8_LEGACY_NAMES:
    if _p8_name not in globals() and _legacy_cic is not None and hasattr(_legacy_cic, _p8_name):
        globals()[_p8_name] = getattr(_legacy_cic, _p8_name)


# ---------------------------------------------------------------------------
# BYS360 P8 - migrated template service functions
# ---------------------------------------------------------------------------

# BYS360 P8 migrated: _render_template_text
def _render_template_text(text: str, user: User | None, task_key: str) -> str:  # type: ignore[override]
    if _cic_v40_previous_render_template_text is not None:
        rendered = _cic_v40_previous_render_template_text(text, user, task_key)
    else:
        rendered = text or ""
    special_names = ", ".join(str(d.get("name")) for d in _cic_v40_special_days_today()) or "Özel Gün"
    service_year = _cic_v40_service_year(user) if user is not None else 0
    extra = {
        "ozel_gun_adi": special_names,
        "hizmet_yili": service_year or "değerli",
        "kutlama_notu": "Yaş bilgisi gösterilmeden, KVKK uyumlu kutlama metni oluşturulmuştur.",
    }
    for key, value in extra.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered


# BYS360 P8 migrated: get_template
def get_template(task_key: str) -> dict[str, str]:
    meta = TASK_DEFINITIONS[task_key]
    return {
        "subject": get_setting(f"{BASE_KEY}.template.{task_key}.subject", meta["subject"]) or meta["subject"],
        "body": get_setting(f"{BASE_KEY}.template.{task_key}.body", meta["body"]) or meta["body"],
    }


# BYS360 P8 migrated: save_templates
def save_templates(payload: dict[str, Any], actor_user_id: int | None = None) -> None:
    for key, meta in TASK_DEFINITIONS.items():
        subject = (payload.get(f"subject_{key}") or meta["subject"]).strip()
        body = (payload.get(f"body_{key}") or meta["body"]).strip()
        set_setting(f"{BASE_KEY}.template.{key}.subject", subject, label=f"{meta['label']} konusu", actor_user_id=actor_user_id)
        set_setting(f"{BASE_KEY}.template.{key}.body", body, label=f"{meta['label']} metni", value_type="text", actor_user_id=actor_user_id)
    db.session.commit()


# BYS360 P8 migrated: _cic_phase6_template_quality
def _cic_phase6_template_quality(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    empty_subject = sum(1 for t in tasks if not (t.get("subject") or "").strip())
    short_body = sum(1 for t in tasks if len((t.get("body") or "").strip()) < 60)
    technical_terms = ["traceback", "exception", "endpoint", "csrf", "debug", "workflow", "sync", "phase"]
    technical = 0
    for t in tasks:
        body = ((t.get("subject") or "") + " " + (t.get("body") or "")).lower()
        if any(term in body for term in technical_terms):
            technical += 1
    items = [
        _cic_phase6_item("Konu kontrolü", empty_subject == 0, f"{empty_subject} görevde konu eksik.", warn=True),
        _cic_phase6_item("Metin uzunluğu", short_body == 0, f"{short_body} şablon çok kısa görünüyor.", warn=True),
        _cic_phase6_item("Teknik dil", technical == 0, f"{technical} şablonda teknik ifade riski var.", warn=True),
    ]
    problems = empty_subject + short_body + technical
    return {"status": "ok" if problems == 0 else "warn", "label": "Şablonlar hazır" if problems == 0 else "Şablonları kontrol et", "items": items, "problem_count": problems}


# Compatibility guard.
try:
    _cic_v40_previous_render_template_text
except NameError:
    _cic_v40_previous_render_template_text = globals().get("_cic_v40_previous_render_template_text")


if "_cic_v40_special_days_today" not in globals():
    def _cic_v40_special_days_today():
        return []


if "_cic_v40_service_year" not in globals():
    def _cic_v40_service_year(user) -> int:
        try:
            from datetime import date
            start = getattr(user, "start_date", None) or getattr(user, "employment_start_date", None) or getattr(user, "hire_date", None) or getattr(user, "ise_giris_tarihi", None)
            if not start:
                return 0
            today = date.today()
            return max(0, int(today.year) - int(start.year))
        except Exception:
            return 0


if "_cic_phase6_item" not in globals():
    def _cic_phase6_item(label: str, ok: bool, detail: str, warn: bool = False) -> dict:
        return {"label": label, "ok": bool(ok), "detail": detail, "warn": bool(warn)}
