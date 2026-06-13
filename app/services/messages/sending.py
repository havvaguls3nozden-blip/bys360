
"""Mesaj gönderme ve ek kaydetme servis köprüsü.

Faz 9 kapsamı canlı mesaj yazma davranışını route içinden servis katmanına taşır.
Route tarafında form token, AJAX/flash dili ve yönlendirme davranışı korunur; bu
servis yalnızca veritabanı yazımı, ek kaydı, okundu/sessiz/arşiv durumları ve
bildirim üretimini yönetir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from flask import url_for
from flask_login import current_user

from app.extensions import db
from app.models import Message, MessageThread, MessageThreadParticipant, MessageTypingState, User
from app.services.message_service import (
    find_or_create_direct_thread,
    notify_user,
    remove_message_attachment_file,
    save_message_attachment,
)

from .repository import orm_entity


@dataclass
class MessageSendResult:
    ok: bool
    message: str
    thread: Any | None = None
    sent_message: Any | None = None
    participant: Any | None = None
    is_self_message: bool = False
    saved_attachments: list[str | None] | None = None


def _sender_display_name() -> str:
    return str(
        getattr(current_user, "full_name", None)
        or getattr(current_user, "ad", None)
        or "Bir kullanıcı"
    )


def _message_type_for(body: str | None, attachment_files: Iterable[Any] | None) -> str:
    files = list(attachment_files or [])
    if files and body:
        return "mixed"
    if files:
        return "attachment"
    return "text"


def _cleanup_saved_attachments(saved_attachments: list[str | None]) -> None:
    for stored_filename in saved_attachments or []:
        if not stored_filename:
            continue
        try:
            remove_message_attachment_file(stored_filename)
        except Exception:
            # Ana hatayi ezmemek icin dosya temizleme hatalari yutulur.
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/messages/sending.py:65)")


def _save_attachments_for_message(attachment_files: Iterable[Any] | None, message: Message) -> list[str | None]:
    saved_attachments: list[str | None] = []
    for attachment_file in attachment_files or []:
        attachment_row = save_message_attachment(attachment_file, message, current_user.id)
        if attachment_row:
            saved_attachments.append(getattr(attachment_row, "stored_filename", None))
    return saved_attachments


def create_direct_message_with_attachments(
    *,
    recipient: User,
    body: str | None,
    attachment_files: Iterable[Any] | None,
    badge_label: str = "",
    icon_name: str = "",
    accent_color: str = "",
    now,
) -> MessageSendResult:
    """Yeni mesaj ekranından direkt/self konuşma açar ve mesajı kaydeder.

    Eski route davranışı korunur:
    - self mesajda "Kendime not kaydedildi." döner
    - alıcı muted ise bildirim gönderilmez
    - kaydetme hatasında DB rollback + yüklenen dosyaların temizliği yapılır
    """

    saved_attachments: list[str | None] = []
    try:
        is_self_message = recipient.id == current_user.id
        thread = find_or_create_direct_thread(
            current_user.id,
            recipient.id,
            badge_label=badge_label,
            icon_name=icon_name,
            accent_color=accent_color,
        )

        files = list(attachment_files or [])
        message = Message(
            thread_id=thread.id,
            sender_user_id=current_user.id,
            body=body or "[Ek]",
            message_type=_message_type_for(body, files),
            sent_at=now,
            is_deleted=False,
        )
        db.session.add(message)
        db.session.flush()

        saved_attachments = _save_attachments_for_message(files, message)
        thread.last_message_at = message.sent_at

        my_participant = (
            MessageThreadParticipant.query
            .filter_by(thread_id=thread.id, user_id=current_user.id)
            .filter(MessageThreadParticipant.left_at.is_(None))
            .first()
        )
        if my_participant:
            my_participant.last_read_message_id = message.id

        recipient_participant = my_participant if is_self_message else (
            MessageThreadParticipant.query
            .filter_by(thread_id=thread.id, user_id=recipient.id)
            .filter(MessageThreadParticipant.left_at.is_(None))
            .first()
        )
        if recipient_participant and hasattr(recipient_participant, "is_archived"):
            recipient_participant.is_archived = False

        if not is_self_message and not (recipient_participant and getattr(recipient_participant, "is_muted", False)):
            notify_user(
                recipient.id,
                title="Yeni mesajınız var",
                body=f"{_sender_display_name()} size mesaj gönderdi.",
                notification_type="new_message",
                source_type="message_thread",
                source_id=thread.id,
                link_url=url_for("main.messages_inbox", thread_id=thread.id),
                priority="normal",
            )

        db.session.commit()
        return MessageSendResult(
            ok=True,
            message="Kendime not kaydedildi." if is_self_message else "Mesaj gönderildi.",
            thread=thread,
            sent_message=message,
            participant=my_participant,
            is_self_message=is_self_message,
            saved_attachments=saved_attachments,
        )
    except Exception:
        db.session.rollback()
        _cleanup_saved_attachments(saved_attachments)
        raise


def append_thread_message_with_attachments(
    *,
    thread: MessageThread,
    participant: MessageThreadParticipant,
    body: str | None,
    attachment_files: Iterable[Any] | None,
    now,
) -> MessageSendResult:
    """Mevcut thread'e mesaj ve ekleri kaydeder.

    Token tuketimi route tarafında kalır; bu servis yalnızca yazma bloğunu yönetir.
    """

    saved_attachments: list[str | None] = []
    try:
        files = list(attachment_files or [])
        message = Message(
            thread_id=thread.id,
            sender_user_id=current_user.id,
            body=body or "[Ek]",
            message_type=_message_type_for(body, files),
            sent_at=now,
            is_deleted=False,
        )
        db.session.add(message)
        db.session.flush()

        saved_attachments = _save_attachments_for_message(files, message)

        thread.last_message_at = message.sent_at
        participant.last_read_message_id = message.id
        participant.last_read_at = now
        MessageTypingState.query.filter_by(thread_id=thread.id, user_id=current_user.id).delete()
        if hasattr(participant, "is_archived"):
            participant.is_archived = False

        recipients = (
            thread.participants
            .filter(
                MessageThreadParticipant.left_at.is_(None),
                MessageThreadParticipant.user_id != current_user.id,
            )
            .all()
        )

        for row in recipients:
            if hasattr(row, "is_archived"):
                row.is_archived = False
            if not getattr(row, "is_muted", False):
                notify_user(
                    row.user_id,
                    title="Yeni mesajınız var",
                    body=f"{_sender_display_name()} size mesaj gönderdi.",
                    notification_type="new_message",
                    source_type="message_thread",
                    source_id=thread.id,
                    link_url=url_for("main.messages_inbox", thread_id=thread.id),
                    priority="normal",
                )

        db.session.commit()
        return MessageSendResult(
            ok=True,
            message="Kendime not kaydedildi." if getattr(thread, "thread_type", "") == "self" else "Mesaj gönderildi.",
            thread=thread,
            sent_message=message,
            participant=participant,
            is_self_message=getattr(thread, "thread_type", "") == "self",
            saved_attachments=saved_attachments,
        )
    except Exception:
        db.session.rollback()
        _cleanup_saved_attachments(saved_attachments)
        raise


def resolve_thread_for_sending(thread_id: int) -> MessageThread | None:
    """Route tarafındaki mevcut thread doğrulamasına küçük servis köprüsü."""

    thread = db.session.get(orm_entity(MessageThread), thread_id)
    if not thread or not getattr(thread, "is_active", False):
        return None
    return thread
