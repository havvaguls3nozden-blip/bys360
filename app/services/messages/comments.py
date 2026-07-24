from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import url_for
from flask_login import current_user

from app.extensions import db
from app.models import Message, MessageComment, MessageThreadParticipant
from app.services.message_service import notify_user

from .repository import orm_entity, participant_for_thread
from .serialization import serialize_comment


@dataclass
class MessageCommentResult:
    ok: bool
    message: str
    comment: Any | None = None
    message_row: Any | None = None
    comment_count: int = 0


def _comment_count(message: Message) -> int:
    try:
        return (
            MessageComment.query
            .filter_by(message_id=message.id, is_deleted=False)
            .count()
        )
    except Exception:
        return 0


def create_message_comment(message_id: int, body: str, *, now) -> tuple[dict[str, Any], int]:
    """Mesaj altına yetki kontrollü yorum ekler.

    Yorumlar, konuşma katılımcılarıyla sınırlıdır. Sayfa yenilemeden çalışan web
    arayüzü için JSON payload döner; normal CSRF koruması route katmanında kalır.
    """

    message = db.session.get(orm_entity(Message), message_id)
    if not message or getattr(message, "is_deleted", False):
        return {"ok": False, "error": "not_found", "message": "Mesaj bulunamadı."}, 404

    participant = participant_for_thread(int(getattr(message, "thread_id", 0) or 0))
    if not participant:
        return {"ok": False, "error": "forbidden", "message": "Bu mesaja yorum yapma yetkiniz bulunmamaktadır."}, 403

    cleaned_body = (body or "").strip()[:1200]
    if not cleaned_body:
        return {"ok": False, "error": "empty", "message": "Boş yorum gönderilemez."}, 400

    try:
        comment = MessageComment(
            message_id=message.id,
            user_id=current_user.id,
            body=cleaned_body,
        )
        db.session.add(comment)
        db.session.flush()

        sender_id = getattr(message, "sender_user_id", None)
        if sender_id and int(sender_id) != int(current_user.id):
            sender_participant = (
                MessageThreadParticipant.query
                .filter_by(thread_id=message.thread_id, user_id=sender_id)
                .filter(MessageThreadParticipant.left_at.is_(None))
                .first()
            )
            if sender_participant and not getattr(sender_participant, "is_muted", False):
                notify_user(
                    sender_id,
                    title="Mesajınıza yorum yapıldı",
                    body="BYS360 mesajınız için yeni bir yorum var.",
                    notification_type="message_comment",
                    source_type="message",
                    source_id=message.id,
                    link_url=url_for("main.messages_inbox", thread_id=message.thread_id),
                    priority="normal",
                )

        db.session.commit()
        return {
            "ok": True,
            "message": "Yorum eklendi.",
            "message_id": message.id,
            "comment": serialize_comment(comment),
            "comment_count": _comment_count(message),
        }, 200
    except Exception as exc:  # pragma: no cover - canlı DB guard
        db.session.rollback()
        return {"ok": False, "error": "server_error", "message": f"Yorum eklenirken hata oluştu: {exc}"}, 500

# BYS360_MESSAGE_INTERACTIONS_V1_COMMENTS_SERVICE
