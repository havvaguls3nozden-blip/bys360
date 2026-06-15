from __future__ import annotations

import logging
import json
from typing import Any

from sqlalchemy import inspect

from app.extensions import db
from app.models import SettingsChangeLog


def _safe_rollback() -> None:
    try:
        db.session.rollback()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/settings/change_logs.py")
def _table_exists(table_name: str) -> bool:
    try:
        return inspect(db.engine).has_table(table_name)
    except Exception:
        _safe_rollback()
        return False


def serialize_settings_state(payload: Any) -> str | None:
    """Ayar snapshot verisini deterministik JSON olarak saklar."""
    if payload is None:
        return None
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def deserialize_settings_state(payload: str | None) -> Any:
    """Log içindeki JSON snapshot verisini güvenli şekilde çözer."""
    if not payload:
        return None
    try:
        return json.loads(payload)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None


def create_settings_change_log(
    *,
    actor_user_id: int | None,
    change_scope: str,
    action_type: str,
    summary: str,
    previous_state: Any,
    new_state: Any,
    target_user_id: int | None = None,
    target_role_name: str | None = None,
    target_unit_name: str | None = None,
    reverted_from_log_id: int | None = None,
    is_rollback: bool = False,
) -> SettingsChangeLog | None:
    """Ayar değişiklik kaydı oluşturur; commit akışına müdahale etmez."""
    if not _table_exists("settings_change_logs"):
        return None

    row = SettingsChangeLog(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        target_role_name=(target_role_name or "").strip().lower() or None,
        target_unit_name=(target_unit_name or "").strip() or None,
        change_scope=change_scope,
        action_type=action_type,
        summary=summary,
        previous_state_json=serialize_settings_state(previous_state),
        new_state_json=serialize_settings_state(new_state),
        reverted_from_log_id=reverted_from_log_id,
        is_rollback=is_rollback,
    )
    db.session.add(row)
    return row


def list_recent_settings_change_logs(
    limit: int = 12,
    *,
    target_user_id: int | None = None,
) -> list[SettingsChangeLog]:
    """Ayarlar ekranı için son değişiklik kayıtlarını döndürür."""
    if not _table_exists("settings_change_logs"):
        return []

    try:
        query = SettingsChangeLog.query.order_by(
            SettingsChangeLog.created_at.desc(),
            SettingsChangeLog.id.desc(),
        )
        if target_user_id:
            query = query.filter(
                (SettingsChangeLog.target_user_id == target_user_id)
                | (
                    (SettingsChangeLog.target_user_id.is_(None))
                    & (SettingsChangeLog.change_scope.in_(["system_settings", "module_settings"]))
                )
            )
        return query.limit(limit).all()
    except Exception:
        _safe_rollback()
        return []
