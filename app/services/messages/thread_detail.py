from __future__ import annotations

import logging
from typing import Any

from flask_login import current_user

from app.extensions import db
from app.models import Message, MessageThread, MessageThreadParticipant

from .inbox import build_thread_counts_payload
from .repository import orm_entity, thread_for_user
from .serialization import build_reaction_map, serialize_message

logger = logging.getLogger(__name__)

"""Mesaj thread detay, activity ve live okuma servisleri.

Faz 6 kapsami yalnizca okuma/canli sayac davranisini tasir. Mesaj gonderme,
ek kaydetme, reaksiyon ve kullanici durum POST islemleri bu fazda tasinmaz.
"""


def load_thread_detail_payload(thread_id: int, now) -> tuple[dict[str, Any], int]:
    """Thread detay sayfasi icin katilimci, mesaj ve okundu bilgisini hazirlar."""

    participant = (
        MessageThreadParticipant.query.filter_by(
            thread_id=thread_id,
            user_id=current_user.id,
        )
        .filter(MessageThreadParticipant.left_at.is_(None))
        .first()
    )
    if not participant:
        return {"ok": False, "error": "forbidden", "message": "Bu konuşmayı görüntüleme yetkiniz yok."}, 403

    thread = db.session.get(orm_entity(MessageThread), thread_id)
    if not thread or not thread.is_active:
        return {"ok": False, "error": "not_found", "message": "Konuşma bulunamadı."}, 404

    participants = (
        thread.participants
        .filter(MessageThreadParticipant.left_at.is_(None))
        .all()
    )
    messages = (
        thread.messages
        .order_by(Message.sent_at.asc(), Message.id.asc())
        .all()
    )

    if messages:
        participant.last_read_message_id = messages[-1].id
        participant.last_read_at = now
        try:
            db.session.commit()
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/messages/thread_detail.py | line=58")
            db.session.rollback()

    return {
        "ok": True,
        "thread": thread,
        "participant": participant,
        "participants": participants,
        "messages": messages,
    }, 200


def build_thread_activity_payload(thread_id: int, now) -> tuple[dict[str, Any], int]:
    """Thread activity endpoint'i icin okunmamis/okundu/presence payload'u uretir."""

    thread, participant = thread_for_user(thread_id)
    if not participant:
        return {"ok": False, "error": "forbidden"}, 403
    if not thread or not thread.is_active:
        return {"ok": False, "error": "not_found"}, 404

    payload = build_thread_counts_payload(thread, participant, now)
    payload.update({"ok": True, "thread_id": thread.id})
    return payload, 200


def build_thread_live_payload(thread_id: int, *, after_id: int = 0, mark_read: bool = True, now=None) -> tuple[dict[str, Any], int]:
    """Thread live endpoint'i icin yeni mesajlari ve sayaclari uretir."""

    thread, participant = thread_for_user(thread_id)
    if not participant:
        return {"ok": False, "error": "forbidden"}, 403
    if not thread:
        return {"ok": False, "error": "not_found"}, 404

    messages = (
        thread.messages
        .filter(Message.id > (after_id or 0))
        .order_by(Message.sent_at.asc(), Message.id.asc())
        .all()
    )
    reaction_map = build_reaction_map(messages) if messages else {}
    serialized_messages = [serialize_message(message, reaction_map) for message in messages]

    latest_visible_message = None
    if mark_read and messages:
        visible_messages = [m for m in messages if not getattr(m, "is_deleted", False)]
        incoming_visible = [m for m in visible_messages if m.sender_user_id != current_user.id]
        if incoming_visible:
            latest_visible_message = incoming_visible[-1]
        elif visible_messages:
            latest_visible_message = visible_messages[-1]
        if latest_visible_message and (
            not participant.last_read_message_id
            or latest_visible_message.id > participant.last_read_message_id
        ):
            participant.last_read_message_id = latest_visible_message.id
            participant.last_read_at = now
            try:
                db.session.commit()
            except Exception:
                logger.exception("BYS360 V6C guarded exception | file=app/services/messages/thread_detail.py | line=118")
                db.session.rollback()

    payload = build_thread_counts_payload(thread, participant, now)
    payload.update({
        "ok": True,
        "messages": serialized_messages,
    })
    return payload, 200
