from __future__ import annotations

import logging
from typing import Any

from flask_login import current_user

from app.extensions import db
from app.models import Message, MessageReaction

from .constants import REACTION_OPTIONS
from .repository import orm_entity, participant_for_thread
from .serialization import build_reaction_map

logger = logging.getLogger(__name__)


def normalize_reaction_value(value: Any) -> str:
    """Emoji tepki degerini route ile uyumlu bicimde temizler."""

    return (value or "").strip()


def toggle_message_reaction(message_id: int, reaction_value: str) -> tuple[dict[str, Any], int]:
    """Mesaj emoji tepkisini ekler, degistirir veya ayni emojiye tekrar basildiysa kaldirir."""

    message = db.session.get(orm_entity(Message), message_id)
    if not message or getattr(message, "is_deleted", False):
        return {"ok": False, "error": "not_found"}, 404

    participant = participant_for_thread(int(getattr(message, "thread_id", 0) or 0))
    if not participant:
        return {"ok": False, "error": "forbidden"}, 403

    normalized_reaction = normalize_reaction_value(reaction_value)
    if normalized_reaction not in REACTION_OPTIONS:
        return {"ok": False, "error": "invalid_reaction"}, 400

    try:
        existing = MessageReaction.query.filter_by(message_id=message.id, user_id=current_user.id).first()
        removed = False
        if existing and existing.reaction_value == normalized_reaction:
            db.session.delete(existing)
            removed = True
        else:
            if not existing:
                existing = MessageReaction(
                    message_id=message.id,
                    user_id=current_user.id,
                    reaction_value=normalized_reaction,
                )
                db.session.add(existing)
            else:
                existing.reaction_value = normalized_reaction

        db.session.commit()
        reactions = build_reaction_map([message]).get(message.id, [])
        return {
            "ok": True,
            "message_id": message.id,
            "removed": removed,
            "reactions": reactions,
        }, 200
    except Exception as exc:  # pragma: no cover - canli DB hatasi guard'i
        logger.exception("BYS360 V6C guarded exception | file=app/services/messages/reactions.py | line=63")
        db.session.rollback()
        return {"ok": False, "error": str(exc)}, 500
