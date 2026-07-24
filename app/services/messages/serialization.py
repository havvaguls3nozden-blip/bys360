from __future__ import annotations

import logging
from typing import Any

from flask import url_for
from flask_login import current_user

from app.models import MessageAttachment, MessageComment, MessageReaction
from app.services.message_service import (
    attachment_icon_class,
    attachment_is_image,
    attachment_is_video,
    format_attachment_file_size,
    message_placeholder_bodies,
)

from .constants import REACTION_OPTIONS
from .formatting import format_dt_label, message_sender_initials, message_sender_name

logger = logging.getLogger(__name__)


def build_reaction_map(messages: list[Any] | tuple[Any, ...] | None) -> dict[int, list[dict[str, Any]]]:
    """Mesajlara ait emoji tepkilerini route davranisiyla ayni sekilde gruplar."""

    message_ids = [mid for message in (messages or []) if (mid := getattr(message, "id", None))]
    if not message_ids:
        return {}
    rows = (
        MessageReaction.query
        .filter(MessageReaction.message_id.in_(message_ids))
        .order_by(MessageReaction.id.asc())
        .all()
    )
    payload: dict[int, list[dict[str, Any]]] = {message_id: [] for message_id in message_ids}
    grouped: dict[int, dict[str, dict[str, Any]]] = {}
    active_user_id = getattr(current_user, "id", None)
    for row in rows:
        message_bucket = grouped.setdefault(row.message_id, {})
        item = message_bucket.setdefault(row.reaction_value, {"emoji": row.reaction_value, "count": 0, "mine": False})
        item["count"] += 1
        if row.user_id == active_user_id:
            item["mine"] = True
    for message_id, emoji_map in grouped.items():
        payload[message_id] = list(emoji_map.values())
    return payload


def serialize_attachment(attachment: Any) -> dict[str, Any]:
    """Ek payload'unu mevcut mobil/web sozlesmesine uygun uretir."""

    is_image = attachment_is_image(attachment)
    is_video = attachment_is_video(attachment)
    stored_filename = getattr(attachment, "stored_filename", None)
    return {
        "id": getattr(attachment, "id", None),
        "original_filename": getattr(attachment, "original_filename", None),
        "stored_filename": stored_filename,
        "download_url": url_for("main.message_attachment_download", filename=stored_filename),
        "preview_url": url_for("main.message_attachment_download", filename=stored_filename),
        "file_ext": getattr(attachment, "file_ext", None),
        "mime_type": getattr(attachment, "mime_type", None),
        "file_size": getattr(attachment, "file_size", 0),
        "file_size_label": format_attachment_file_size(getattr(attachment, "file_size", 0)),
        "is_image": is_image,
        "is_video": is_video,
        "icon_class": attachment_icon_class(attachment),
    }


def _reactions_for_message(message: Any) -> list[dict[str, Any]]:
    message_bucket: dict[str, dict[str, Any]] = {}
    try:
        reaction_rows = message.reactions.order_by(MessageReaction.id.asc()).all()
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/messages/serialization.py | line=75")
        reaction_rows = []
    active_user_id = getattr(current_user, "id", None)
    for row in reaction_rows:
        item = message_bucket.setdefault(row.reaction_value, {"emoji": row.reaction_value, "count": 0, "mine": False})
        item["count"] += 1
        if row.user_id == active_user_id:
            item["mine"] = True
    return list(message_bucket.values())




def _message_comment_dt_label(value: Any) -> str:
    if not value:
        return "-"
    try:
        return value.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return "-"


def serialize_comment(comment: Any) -> dict[str, Any]:
    """Mesaj yorumu için güvenli JSON payload üretir."""

    user = getattr(comment, "user", None)
    full_name = getattr(user, "full_name", None)
    fallback_name = " ".join([
        str(getattr(user, "ad", "") or "").strip(),
        str(getattr(user, "soyad", "") or "").strip(),
    ]).strip() if user else ""

    created_at = getattr(comment, "created_at", None)
    edited_at = getattr(comment, "edited_at", None)

    return {
        "id": getattr(comment, "id", None),
        "message_id": getattr(comment, "message_id", None),
        "user_id": getattr(comment, "user_id", None),
        "user_name": full_name or fallback_name or "Kullanıcı",
        "body": getattr(comment, "body", "") or "",
        "created_at": created_at.isoformat() if created_at else None,
        "created_at_label": _message_comment_dt_label(created_at),
        "edited_at": edited_at.isoformat() if edited_at else None,
        "is_mine": getattr(comment, "user_id", None) == getattr(current_user, "id", None),
    }


def _comments_for_message(message: Any) -> list[dict[str, Any]]:
    try:
        rows = (
            message.comments
            .filter_by(is_deleted=False)
            .order_by(MessageComment.id.asc())
            .all()
        )
    except Exception:
        rows = []

    return [serialize_comment(row) for row in rows]

# BYS360_PHASE4A_MESSAGE_COMMENT_SERIALIZATION

def serialize_message(message: Any, reaction_map: dict[int, list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    """Mesaj payload'unu eski route fonksiyonu ile uyumlu bicimde uretir."""

    reactions = []
    if reaction_map is not None:
        reactions = reaction_map.get(message.id, []) or []
    elif hasattr(message, "reactions"):
        reactions = _reactions_for_message(message)

    attachments = []
    try:
        attachments = [serialize_attachment(row) for row in message.attachments.order_by(MessageAttachment.id.asc()).all()]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/messages/serialization.py | line=98")
        attachments = []

    if bool(getattr(message, "is_deleted", False)):
        attachments = []

    raw_body = getattr(message, "body", None) or ""
    hide_placeholder_body = bool(attachments) and raw_body.strip() in message_placeholder_bodies()
    sender_user_id = getattr(message, "sender_user_id", None)
    active_user_id = getattr(current_user, "id", None)
    sent_at = getattr(message, "sent_at", None)
    edited_at = getattr(message, "edited_at", None)

    return {
        "id": getattr(message, "id", None),
        "thread_id": getattr(message, "thread_id", None),
        "body": "" if hide_placeholder_body else raw_body,
        "raw_body": raw_body,
        "body_is_placeholder": hide_placeholder_body,
        "is_mine": sender_user_id == active_user_id,
        "sender_user_id": sender_user_id,
        "sender_name": message_sender_name(message),
        "sender_initials": message_sender_initials(message),
        "sent_at": sent_at.isoformat() if sent_at else None,
        "sent_at_label": format_dt_label(sent_at) or "-",
        "edited_at": edited_at.isoformat() if edited_at else None,
        "is_deleted": bool(getattr(message, "is_deleted", False)),
        "attachments": attachments,
        "reactions": reactions,
        "comments": _comments_for_message(message),
        "comment_count": len(_comments_for_message(message)),
        "reaction_options": REACTION_OPTIONS,
    }
