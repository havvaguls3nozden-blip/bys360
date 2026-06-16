from __future__ import annotations

from typing import Any

from flask_login import current_user

from app.models import Message, MessageTypingState

from .formatting import format_dt_label


def build_thread_presence(thread: Any, participants: list[Any] | tuple[Any, ...], now) -> dict[str, Any]:
    other_participants = [
        p for p in (participants or [])
        if getattr(p, "user_id", None) != current_user.id and getattr(p, "user", None)
    ]
    typing_rows = []
    if other_participants:
        typing_rows = (
            MessageTypingState.query
            .filter(
                MessageTypingState.thread_id == thread.id,
                MessageTypingState.user_id.in_([p.user_id for p in other_participants]),
                MessageTypingState.expires_at > now,
            )
            .order_by(MessageTypingState.last_activity_at.desc(), MessageTypingState.id.desc())
            .all()
        )
    typing_map = {row.user_id: row for row in typing_rows}

    statuses = []
    for participant in other_participants:
        latest_message = (
            thread.messages
            .filter(
                Message.sender_user_id == participant.user_id,
                Message.is_deleted.is_(False),
            )
            .order_by(Message.sent_at.desc(), Message.id.desc())
            .first()
        )
        typing_row = typing_map.get(participant.user_id)
        if typing_row:
            label = "yazıyor..."
            sort_key = 0
            last_activity_at = typing_row.last_activity_at or typing_row.expires_at
        elif latest_message and latest_message.sent_at:
            label = f"son işlem {format_dt_label(latest_message.sent_at)}"
            sort_key = 1
            last_activity_at = latest_message.sent_at
        else:
            label = "yakın işlem yok"
            sort_key = 2
            last_activity_at = None
        user_obj = participant.user
        statuses.append({
            "user_id": participant.user_id,
            "name": user_obj.full_name if getattr(user_obj, "full_name", None) else f"{user_obj.ad or ''} {user_obj.soyad or ''}".strip(),
            "label": label,
            "is_typing": bool(typing_row),
            "last_activity_at": last_activity_at,
            "sort_key": sort_key,
        })

    statuses.sort(key=lambda item: (item["sort_key"], -(item["last_activity_at"].timestamp()) if item["last_activity_at"] else 0, item["name"]))

    typing_names = [item["name"] for item in statuses if item["is_typing"]]
    typing_text = None
    if typing_names:
        if len(typing_names) == 1:
            typing_text = f"{typing_names[0]} yazıyor..."
        elif len(typing_names) == 2:
            typing_text = f"{typing_names[0]} ve {typing_names[1]} yazıyor..."
        else:
            typing_text = f"{typing_names[0]} ve {len(typing_names) - 1} kişi yazıyor..."

    last_active_text = None
    if statuses:
        non_typing = next((item for item in statuses if not item["is_typing"] and item["last_activity_at"]), None)
        if non_typing:
            last_active_text = f"{non_typing['name']} · son işlem {format_dt_label(non_typing['last_activity_at'])}"

    return {
        "typing_text": typing_text,
        "last_active_text": last_active_text,
        "statuses": statuses,
    }
