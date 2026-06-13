
"""Mesaj yazma ekranı ve alıcı seçimi servisleri.

Faz 5 kapsamı bilinçli olarak okuma/compose hazırlık alanıyla sınırlıdır.
Mesaj gönderme, ek kaydetme, bildirim üretme ve thread katılımcı yazımı bu
fazda taşınmaz; canlı yazma akışı route içinde kalır.
"""
from __future__ import annotations
from app import db

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from flask_login import current_user

from app.models import Message, MessageThread, MessageThreadParticipant, MessageTypingState, User

from .constants import COMPOSE_USER_SOFT_LIMIT
from .formatting import format_dt_label


@dataclass(frozen=True)
class ComposeUserCard:
    user_id: int
    display_name: str
    subtitle: str | None = None
    initials: str = "K"
    is_active: bool = True


def user_display_name(user: Any) -> str:
    if getattr(user, "full_name", None):
        return str(user.full_name)
    return f"{getattr(user, 'ad', '') or ''} {getattr(user, 'soyad', '') or ''}".strip() or "Kullanıcı"


def user_initials(user: Any) -> str:
    first = (getattr(user, "ad", "") or "")[:1]
    last = (getattr(user, "soyad", "") or "")[:1]
    value = f"{first}{last}".upper().strip()
    if value:
        return value
    display_name = user_display_name(user)
    return ((display_name[:1] if display_name else "K") + (display_name[1:2] if len(display_name) > 1 else "")).upper() or "K"


def build_compose_user_card(user: Any, subtitle: str | None = None) -> ComposeUserCard:
    return ComposeUserCard(
        user_id=int(getattr(user, "id")),
        display_name=user_display_name(user),
        subtitle=subtitle,
        initials=user_initials(user),
        is_active=bool(getattr(user, "is_active", True)),
    )


def sort_compose_users(users: list[Any] | tuple[Any, ...]) -> list[Any]:
    """Alıcı listesini eski route sıralamasıyla aynı düzene getirir."""

    return sorted(
        list(users or []),
        key=lambda user: (
            0 if getattr(user, "id", None) == current_user.id else 1,
            (getattr(user, "ad", "") or "").lower(),
            (getattr(user, "soyad", "") or "").lower(),
            getattr(user, "id", None) or 0,
        ),
    )


def load_active_compose_users(limit: int = COMPOSE_USER_SOFT_LIMIT) -> list[Any]:
    """Yeni mesaj/compose picker için aktif kullanıcıları okur.

    Bu fonksiyon veri yazmaz. Mevcut canlı davranıştaki sıralama korunur.
    """

    users = (
        User.query
        .filter(User.is_active.is_(True))
        .order_by(User.id.asc())
        .limit(limit)
        .all()
    )
    return sort_compose_users(users)


def load_all_active_compose_users() -> list[Any]:
    """Klasik /messages/new ekranındaki tam aktif kullanıcı listesini okur."""

    users = (
        User.query
        .filter(User.is_active.is_(True))
        .order_by(User.id.asc())
        .all()
    )
    return sort_compose_users(users)


def resolve_active_recipient(recipient_user_id: int | None) -> Any | None:
    """GET ekranında seçili alıcıyı güvenli şekilde doğrular."""

    if not recipient_user_id:
        return None
    recipient = db.session.get(User, recipient_user_id)
    if not recipient or not getattr(recipient, "is_active", True):
        return None
    return recipient


def build_recent_message_users_for_compose(users: list[Any] | tuple[Any, ...], limit: int = 8) -> list[Any]:
    """Son konuşulan kullanıcıları, eski route mantığıyla aynı sırada üretir."""

    user_map = {getattr(user, "id", None): user for user in users or []}
    ordered_ids: list[int] = []

    participant_rows = (
        MessageThreadParticipant.query
        .filter_by(user_id=current_user.id)
        .filter(MessageThreadParticipant.left_at.is_(None))
        .all()
    )
    thread_ids = [row.thread_id for row in participant_rows if getattr(row, "thread_id", None)]
    if thread_ids:
        threads = (
            MessageThread.query
            .filter(
                MessageThread.id.in_(thread_ids),
                MessageThread.thread_type.in_(["direct", "self"]),
                MessageThread.is_active.is_(True),
            )
            .order_by(MessageThread.last_message_at.desc().nullslast(), MessageThread.id.desc())
            .all()
        )
        for thread in threads:
            candidate_id = None
            if (getattr(thread, "thread_type", "") or "").strip().lower() == "self":
                candidate_id = current_user.id
            else:
                other_participant = (
                    thread.participants
                    .filter(
                        MessageThreadParticipant.left_at.is_(None),
                        MessageThreadParticipant.user_id != current_user.id,
                    )
                    .first()
                )
                if other_participant:
                    candidate_id = other_participant.user_id
            if candidate_id and candidate_id in user_map and candidate_id not in ordered_ids:
                ordered_ids.append(candidate_id)
            if len(ordered_ids) >= limit:
                break

    if current_user.id in user_map and current_user.id not in ordered_ids:
        ordered_ids.insert(0, current_user.id)

    for user in users or []:
        user_id = getattr(user, "id", None)
        if user_id and user_id not in ordered_ids:
            ordered_ids.append(user_id)
        if len(ordered_ids) >= limit:
            break

    return [user_map[user_id] for user_id in ordered_ids if user_id in user_map]


def _thread_payloads_for_compose(users: list[Any], now) -> dict[int, dict[str, Any]]:
    user_map = {getattr(user, "id", None): user for user in users if getattr(user, "id", None)}
    participant_rows = (
        MessageThreadParticipant.query
        .filter_by(user_id=current_user.id)
        .filter(MessageThreadParticipant.left_at.is_(None))
        .all()
    )
    thread_ids = [row.thread_id for row in participant_rows if getattr(row, "thread_id", None)]
    thread_map: dict[int, dict[str, Any]] = {}
    if not thread_ids:
        return thread_map

    threads = (
        MessageThread.query
        .filter(
            MessageThread.id.in_(thread_ids),
            MessageThread.thread_type.in_(["direct", "self"]),
            MessageThread.is_active.is_(True),
        )
        .order_by(MessageThread.last_message_at.desc().nullslast(), MessageThread.id.desc())
        .all()
    )
    typing_rows = (
        MessageTypingState.query
        .filter(
            MessageTypingState.thread_id.in_(thread_ids),
            MessageTypingState.expires_at > now,
        )
        .order_by(MessageTypingState.last_activity_at.desc(), MessageTypingState.id.desc())
        .all()
    )
    typing_map = {(row.thread_id, row.user_id): row for row in typing_rows}

    for thread in threads:
        if (getattr(thread, "thread_type", "") or "").strip().lower() == "self":
            candidate_id = current_user.id
        else:
            other_participant = (
                thread.participants
                .filter(
                    MessageThreadParticipant.left_at.is_(None),
                    MessageThreadParticipant.user_id != current_user.id,
                )
                .first()
            )
            candidate_id = getattr(other_participant, "user_id", None)
        if not candidate_id or candidate_id not in user_map:
            continue

        last_message = (
            thread.messages
            .filter(Message.is_deleted.is_(False))
            .order_by(Message.sent_at.desc(), Message.id.desc())
            .first()
        )
        my_participant = next((row for row in participant_rows if row.thread_id == thread.id), None)
        last_read_message_id = getattr(my_participant, "last_read_message_id", None)
        if last_read_message_id:
            unread_count = thread.messages.filter(
                Message.id > last_read_message_id,
                Message.sender_user_id != current_user.id,
                Message.is_deleted.is_(False),
            ).count()
        else:
            unread_count = thread.messages.filter(
                Message.sender_user_id != current_user.id,
                Message.is_deleted.is_(False),
            ).count()

        typing_row = None if candidate_id == current_user.id else typing_map.get((thread.id, candidate_id))
        last_activity = None
        if typing_row:
            last_activity = typing_row.last_activity_at or typing_row.expires_at
        elif last_message is not None:
            last_activity = last_message.sent_at
        is_online = bool(last_activity and (now - last_activity) <= timedelta(minutes=5))
        thread_map[candidate_id] = {
            "thread": thread,
            "last_message": last_message,
            "unread_count": unread_count,
            "is_typing": bool(typing_row),
            "is_online": is_online,
            "last_activity_at": last_activity,
        }
    return thread_map


def build_compose_user_cards(users: list[Any] | tuple[Any, ...], now) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compose kullanıcı kartlarını ve son kullanıcı kartlarını üretir."""

    users = list(users or [])
    thread_map = _thread_payloads_for_compose(users, now)

    cards: list[dict[str, Any]] = []
    for user in users:
        user_id = getattr(user, "id", None)
        if not user_id:
            continue
        display_name = user_display_name(user)
        initials = ((display_name[:1] if display_name else "K") + (display_name[1:2] if len(display_name) > 1 else "")).upper()
        thread_payload = thread_map.get(user_id) or {}
        last_message = thread_payload.get("last_message")
        is_self = user_id == current_user.id
        if is_self:
            status_text = "Kişisel not alanın"
        elif thread_payload.get("is_typing"):
            status_text = "şu anda yazıyor..."
        elif thread_payload.get("is_online"):
            status_text = "yakın zamanda aktif"
        elif last_message is not None and getattr(last_message, "sent_at", None):
            status_text = f"son konuşma {format_dt_label(last_message.sent_at) or ''}".strip()
        else:
            status_text = "henüz konuşma yok"
        cards.append({
            "user": user,
            "user_id": user_id,
            "display_name": "Kendime Notlar" if is_self else display_name,
            "initials": initials,
            "is_self": is_self,
            "thread": thread_payload.get("thread"),
            "has_thread": bool(thread_payload.get("thread")),
            "last_message": last_message,
            "status_text": status_text,
            "is_typing": bool(thread_payload.get("is_typing")),
            "is_online": bool(thread_payload.get("is_online")),
            "unread_count": int(thread_payload.get("unread_count") or 0),
            "search_blob": f"{display_name} {getattr(user, 'birim', '') or ''} {getattr(user, 'unvan', '') or ''} {getattr(user, 'email', '') or ''}".lower(),
        })

    recent_ids = [getattr(user, "id", None) for user in build_recent_message_users_for_compose(users)]
    recent_cards = [card for user_id in recent_ids for card in cards if card["user_id"] == user_id]
    return cards, recent_cards
