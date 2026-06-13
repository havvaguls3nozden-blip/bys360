from __future__ import annotations



import json
from typing import Any

from flask import request
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog


def _json_dump(payload: Any) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, ensure_ascii=False, default=str)


def write_audit_log(
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    *,
    old_data: Any = None,
    new_data: Any = None,
    summary: str = "",
) -> AuditLog:
    user_id = None
    try:
        if getattr(current_user, "is_authenticated", False):
            user_id = getattr(current_user, "id", None)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/audit_service.py:34")
        user_id = None

    audit = AuditLog(
        user_id=user_id,
        action=(action or "").strip(),
        entity_type=(entity_type or "").strip(),
        entity_id=entity_id,
        old_data_json=_json_dump(old_data),
        new_data_json=_json_dump(new_data),
        summary=(summary or "").strip() or None,
        endpoint=(request.endpoint or "").strip() or None,
        ip_address=(request.headers.get("X-Forwarded-For") or request.remote_addr or "").strip() or None,
    )
    db.session.add(audit)
    return audit
