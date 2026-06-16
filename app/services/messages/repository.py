from __future__ import annotations

from typing import Any

from flask_login import current_user

from app.extensions import db
from app.models import MessageThread, MessageThreadParticipant


def orm_entity(entity: Any) -> Any:
    """Eski route yardimcisiyla uyumlu ORM entity passthrough."""

    return entity


def participant_for_thread(thread_id: int, user_id: int | None = None):
    active_user_id = user_id if user_id is not None else current_user.id
    return (
        MessageThreadParticipant.query
        .filter_by(thread_id=thread_id, user_id=active_user_id)
        .filter(MessageThreadParticipant.left_at.is_(None))
        .first()
    )


def thread_for_user(thread_id: int, user_id: int | None = None):
    participant = participant_for_thread(thread_id, user_id=user_id)
    if not participant:
        return None, None
    thread = db.session.get(orm_entity(MessageThread), thread_id)
    if not thread or not getattr(thread, "is_active", False):
        return None, None
    return thread, participant
