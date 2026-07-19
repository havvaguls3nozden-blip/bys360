from __future__ import annotations

from datetime import timedelta
from typing import Any
from collections.abc import Mapping

from flask_login import current_user

from app.extensions import db
from app.models import MessageThread, MessageTypingState

from .repository import orm_entity, participant_for_thread
import logging
logger = logging.getLogger(__name__)

_TYPING_FALSE_VALUES = {"0", "false", "hayir", "hayır", "no", "off", ""}
_TYPING_EXPIRE_SECONDS = 12


def normalize_typing_flag(value: Any) -> bool:
    """Mesaj yaziyor bilgisini eski route davranisiyla ayni sekilde bool degerine cevirir."""

    return str(value if value is not None else "1").strip().lower() not in _TYPING_FALSE_VALUES


def update_thread_typing_state(
    thread_id: int,
    *,
    payload: Mapping[str, Any] | None,
    preview_text: str | None,
    now,
) -> tuple[dict[str, Any], int]:
    """Thread yaziyor bilgisini gunceller.

    Canli route davranisi korunur:
    - Katilimci degilse 403
    - Thread pasif/self ise 404
    - is_typing false ise mevcut typing satiri silinir
    - is_typing true ise satir olusturulur/guncellenir ve 12 sn sonrasina expire edilir
    """

    participant = participant_for_thread(thread_id)
    if not participant:
        return {"ok": False, "error": "forbidden"}, 403

    thread = db.session.get(orm_entity(MessageThread), thread_id)
    if not thread or not getattr(thread, "is_active", False) or getattr(thread, "thread_type", "") == "self":
        return {"ok": False, "error": "not_found"}, 404

    incoming = payload or {}
    is_typing = normalize_typing_flag(incoming.get("is_typing", "1"))

    try:
        existing = MessageTypingState.query.filter_by(thread_id=thread_id, user_id=current_user.id).first()
        if not is_typing:
            if existing:
                db.session.delete(existing)
                db.session.commit()
            return {"ok": True, "typing": False}, 200

        if not existing:
            existing = MessageTypingState(thread_id=thread_id, user_id=current_user.id, expires_at=now)
            db.session.add(existing)

        existing.preview_text = preview_text or None
        existing.last_activity_at = now
        existing.expires_at = now + timedelta(seconds=_TYPING_EXPIRE_SECONDS)
        db.session.commit()
        return {
            "ok": True,
            "typing": True,
            "expires_at": existing.expires_at.isoformat() if existing.expires_at else None,
        }, 200
    except Exception as exc:  # pragma: no cover - canli DB hatasi guard'i
        logger.exception("BYS360 V6C guarded exception | file=app/services/messages/typing.py | line=73")
        db.session.rollback()
        return {"ok": False, "error": str(exc)}, 500
