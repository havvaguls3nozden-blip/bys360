
"""Mesaj gelen kutusu okuma ve thread listeleme servisleri.

Faz 4 kapsaminda mesaj yazma/gonderme, ek yukleme, reaksiyon ve thread durum
POST akislari tasinmaz. Bu dosya yalnizca gelen kutusu listeleme, kart
hesaplama ve secili thread okuma mantigini route dosyasindan ayirir.
"""
from __future__ import annotations

from typing import Any

from flask_login import current_user

from sqlalchemy import case, exists, func, or_
from sqlalchemy.orm import aliased

from app.extensions import db
from app.models import Message, MessageThread, MessageThreadParticipant, User

from .constants import INBOX_THREAD_FETCH_LIMIT, INBOX_THREAD_FETCH_LIMIT_SEARCH, THREAD_MESSAGE_SOFT_LIMIT
from .presence import build_thread_presence
from .repository import orm_entity
from .serialization import build_reaction_map

_VALID_FILTERS = {"active", "unread", "pinned", "muted", "archived", "all"}
_VALID_SCOPES = {"all", "self"}


def normalize_inbox_filter(value: str | None) -> str:
    current_filter = (value or "active").strip().lower()
    return current_filter if current_filter in _VALID_FILTERS else "active"


def normalize_inbox_scope(value: str | None) -> str:
    current_scope = (value or "all").strip().lower()
    return current_scope if current_scope in _VALID_SCOPES else "all"


def _active_thread_participant_query(current_scope: str = "all"):
    """Kullanıcının erişebildiği aktif thread omurgasını SQL tarafında kurar."""

    query = (
        db.session.query(MessageThreadParticipant, MessageThread)
        .join(MessageThread, MessageThread.id == MessageThreadParticipant.thread_id)
        .filter(
            MessageThreadParticipant.user_id == current_user.id,
            MessageThreadParticipant.left_at.is_(None),
            MessageThread.is_active.is_(True),
        )
    )
    if current_scope == "self":
        query = query.filter(MessageThread.thread_type == "self")
    return query


def _apply_thread_search_prefilter(query, search_query: str | None):
    """Arama yükünü kart üretiminden önce SQL WHERE/EXISTS tarafına indirir."""

    if not search_query:
        return query
    like = f"%{search_query}%"
    participant_alias = aliased(MessageThreadParticipant)
    user_alias = aliased(User)
    return query.filter(
        or_(
            MessageThread.subject.ilike(like),
            MessageThread.badge_label.ilike(like),
            exists().where(
                Message.thread_id == MessageThread.id,
                Message.is_deleted.is_(False),
                Message.body.ilike(like),
            ),
            exists().where(
                participant_alias.thread_id == MessageThread.id,
                participant_alias.left_at.is_(None),
                participant_alias.user_id != current_user.id,
                participant_alias.user_id == user_alias.id,
                or_(
                    user_alias.ad.ilike(like),
                    user_alias.soyad.ilike(like),
                    user_alias.full_name_cache.ilike(like),
                    user_alias.email.ilike(like),
                    user_alias.birim.ilike(like),
                    user_alias.unvan.ilike(like),
                ),
            ),
        )
    )


def _thread_filter_counts_sql(current_scope: str, pinned_ids: set[int] | frozenset[int]) -> dict[str, int]:
    """Gelen kutusu rozet sayılarını Python liste taraması yerine SQL aggregate ile üretir."""

    base = _active_thread_participant_query(current_scope)
    unread_exists = exists().where(
        Message.thread_id == MessageThread.id,
        Message.sender_user_id != current_user.id,
        Message.is_deleted.is_(False),
        or_(
            MessageThreadParticipant.last_read_message_id.is_(None),
            Message.id > MessageThreadParticipant.last_read_message_id,
        ),
    )
    pinned_condition = MessageThread.id.in_(list(pinned_ids or {-1}))
    row = base.with_entities(
        func.count(MessageThread.id).label("all_count"),
        func.coalesce(func.sum(case((MessageThreadParticipant.is_archived.is_(False), 1), else_=0)), 0).label("active_count"),
        func.coalesce(func.sum(case((MessageThreadParticipant.is_archived.is_(True), 1), else_=0)), 0).label("archived_count"),
        func.coalesce(func.sum(case((MessageThreadParticipant.is_muted.is_(True), 1), else_=0)), 0).label("muted_count"),
        func.coalesce(func.sum(case((pinned_condition, 1), else_=0)), 0).label("pinned_count"),
        func.coalesce(func.sum(case((unread_exists, 1), else_=0)), 0).label("unread_count"),
    ).one()
    return {
        "active": int(row.active_count or 0),
        "unread": int(row.unread_count or 0),
        "pinned": int(row.pinned_count or 0),
        "muted": int(row.muted_count or 0),
        "archived": int(row.archived_count or 0),
        "all": int(row.all_count or 0),
    }


def build_thread_counts_payload(thread: Any, participant: Any, now) -> dict[str, Any]:
    """Thread canlı sayaç payload'unu route davranışıyla uyumlu üretir."""

    last_message = (
        thread.messages
        .filter(Message.is_deleted.is_(False))
        .order_by(Message.sent_at.desc(), Message.id.desc())
        .first()
    )

    if getattr(participant, "last_read_message_id", None):
        unread_count = thread.messages.filter(
            Message.id > participant.last_read_message_id,
            Message.sender_user_id != current_user.id,
            Message.is_deleted.is_(False),
        ).count()
    else:
        unread_count = thread.messages.filter(
            Message.sender_user_id != current_user.id,
            Message.is_deleted.is_(False),
        ).count()

    recipient_participants = (
        thread.participants
        .filter(MessageThreadParticipant.left_at.is_(None), MessageThreadParticipant.user_id != current_user.id)
        .all()
    )
    read_count = 0
    pending_count = len(recipient_participants)
    if last_message:
        read_count = len([
            p for p in recipient_participants
            if p.last_read_message_id and p.last_read_message_id >= last_message.id
        ])
        pending_count = max(len(recipient_participants) - read_count, 0)

    presence_payload = build_thread_presence(
        thread,
        thread.participants.filter(MessageThreadParticipant.left_at.is_(None)).all(),
        now,
    )
    return {
        "thread_id": thread.id,
        "last_message_id": last_message.id if last_message else None,
        "last_message_at": last_message.sent_at.isoformat() if last_message and last_message.sent_at else None,
        "unread_count": unread_count,
        "is_muted": bool(getattr(participant, "is_muted", False)),
        "read_count": read_count,
        "pending_count": pending_count,
        "typing_text": presence_payload.get("typing_text"),
        "last_active_text": presence_payload.get("last_active_text"),
        "participant_statuses": [
            {
                "user_id": row.get("user_id"),
                "name": row.get("name"),
                "label": row.get("label"),
                "is_typing": row.get("is_typing"),
            }
            for row in (presence_payload.get("statuses") or [])
        ],
    }


def _user_name(user: Any) -> str:
    if getattr(user, "full_name", None):
        return str(user.full_name)
    return f"{getattr(user, 'ad', '') or ''} {getattr(user, 'soyad', '') or ''}".strip()


def _thread_display_title(thread: Any, other_users: list[Any]) -> str:
    if thread.thread_type == "self":
        return thread.subject or "Kendime Notlar"
    if thread.thread_type == "direct":
        return ", ".join([_user_name(user) for user in other_users]) or "Doğrudan Mesaj"
    return thread.subject or "Toplu Mesaj"


def _thread_unread_count(thread: Any, participant: Any) -> int:
    last_read_message_id = participant.last_read_message_id if participant else None
    if last_read_message_id:
        return thread.messages.filter(
            Message.id > last_read_message_id,
            Message.sender_user_id != current_user.id,
            Message.is_deleted.is_(False),
        ).count()
    return thread.messages.filter(
        Message.sender_user_id != current_user.id,
        Message.is_deleted.is_(False),
    ).count()


def _read_pending_counts(last_message: Any, participants: list[Any]) -> tuple[int, int, int]:
    recipient_participants = [p for p in participants if p.user_id != current_user.id]
    read_count = 0
    pending_count = len(recipient_participants)
    if last_message:
        read_count = len([
            p for p in recipient_participants
            if p.last_read_message_id and p.last_read_message_id >= last_message.id
        ])
        pending_count = max(len(recipient_participants) - read_count, 0)
    return len(recipient_participants), read_count, pending_count


def build_thread_card(thread: Any, my_participant: Any, pinned_ids: set[int] | frozenset[int]) -> dict[str, Any]:
    participants = thread.participants.filter(MessageThreadParticipant.left_at.is_(None)).all()
    other_users = [p.user for p in participants if p.user_id != current_user.id and p.user]
    last_message = (
        thread.messages
        .filter(Message.is_deleted.is_(False))
        .order_by(Message.sent_at.desc(), Message.id.desc())
        .first()
    )
    recipient_count, read_count, pending_count = _read_pending_counts(last_message, participants)
    return {
        "thread": thread,
        "display_title": _thread_display_title(thread, other_users),
        "participants": other_users,
        "last_message": last_message,
        "unread_count": _thread_unread_count(thread, my_participant),
        "is_muted": bool(my_participant.is_muted) if my_participant else False,
        "is_archived": bool(my_participant.is_archived) if my_participant else False,
        "is_pinned": thread.id in pinned_ids,
        "recipient_count": recipient_count,
        "read_count": read_count,
        "pending_count": pending_count,
    }


def _card_matches_filter(card: dict[str, Any], *, current_filter: str, current_scope: str, search_query: str | None) -> bool:
    haystack = " ".join(
        [
            str(card.get("display_title") or ""),
            str(card.get("last_message").body if card.get("last_message") else ""),
            " ".join(
                _user_name(user)
                for user in (card.get("participants") or [])
            ),
        ]
    ).lower()

    if search_query and search_query.lower() not in haystack:
        return False

    if current_scope == "self" and card["thread"].thread_type != "self":
        return False

    if current_filter == "all":
        return True
    if current_filter == "active":
        return not card["is_archived"]
    if current_filter == "unread":
        return card["unread_count"] > 0 and not card["is_archived"]
    if current_filter == "pinned":
        return card["is_pinned"] and not card["is_archived"]
    if current_filter == "muted":
        return card["is_muted"] and not card["is_archived"]
    if current_filter == "archived":
        return card["is_archived"]
    return True


def _sort_thread_cards(cards: list[dict[str, Any]]) -> None:
    cards.sort(
        key=lambda item: (
            0 if item["is_pinned"] else 1,
            0 if item["unread_count"] > 0 else 1,
            0 if not item["is_muted"] else 1,
            -(item["last_message"].id if item["last_message"] else 0),
            -(item["thread"].id or 0),
        )
    )


def _filter_counts(scope_thread_cards: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "active": sum(1 for item in scope_thread_cards if not item["is_archived"]),
        "unread": sum(1 for item in scope_thread_cards if item["unread_count"] > 0 and not item["is_archived"]),
        "pinned": sum(1 for item in scope_thread_cards if item["is_pinned"] and not item["is_archived"]),
        "muted": sum(1 for item in scope_thread_cards if item["is_muted"] and not item["is_archived"]),
        "archived": sum(1 for item in scope_thread_cards if item["is_archived"]),
        "all": len(scope_thread_cards),
    }


def build_inbox_thread_collection(
    *,
    selected_thread_id: int | None,
    current_filter: str,
    current_scope: str,
    search_query: str | None,
    pinned_ids: set[int] | frozenset[int],
) -> dict[str, Any]:
    """Gelen kutusu thread kartlari ve filtre sayaçlarini üretir."""

    thread_fetch_limit = INBOX_THREAD_FETCH_LIMIT_SEARCH if search_query else INBOX_THREAD_FETCH_LIMIT
    participant_query = (
        MessageThreadParticipant.query
        .join(MessageThread, MessageThread.id == MessageThreadParticipant.thread_id)
        .filter(
            MessageThreadParticipant.user_id == current_user.id,
            MessageThreadParticipant.left_at.is_(None),
            MessageThread.is_active.is_(True),
        )
    )
    if current_scope == "self":
        participant_query = participant_query.filter(MessageThread.thread_type == "self")
    participant_query = _apply_thread_search_prefilter(participant_query, search_query)
    participant_rows = (
        participant_query
        .order_by(MessageThread.last_message_at.desc().nullslast(), MessageThread.id.desc())
        .limit(thread_fetch_limit)
        .all()
    )

    if selected_thread_id and selected_thread_id not in {row.thread_id for row in participant_rows}:
        selected_participant = (
            MessageThreadParticipant.query
            .join(MessageThread, MessageThread.id == MessageThreadParticipant.thread_id)
            .filter(
                MessageThreadParticipant.thread_id == selected_thread_id,
                MessageThreadParticipant.user_id == current_user.id,
                MessageThreadParticipant.left_at.is_(None),
                MessageThread.is_active.is_(True),
            )
            .first()
        )
        if selected_participant is not None:
            participant_rows.append(selected_participant)

    participant_map = {p.thread_id: p for p in participant_rows}
    thread_ids = [p.thread_id for p in participant_rows]
    threads = []
    if thread_ids:
        threads = (
            MessageThread.query
            .filter(MessageThread.id.in_(thread_ids))
            .order_by(MessageThread.last_message_at.desc().nullslast(), MessageThread.id.desc())
            .limit(thread_fetch_limit)
            .all()
        )
        if selected_thread_id and selected_thread_id not in {row.id for row in threads}:
            selected_thread = (
                MessageThread.query
                .filter(MessageThread.id == selected_thread_id, MessageThread.id.in_(thread_ids))
                .first()
            )
            if selected_thread is not None:
                threads.append(selected_thread)

    all_thread_cards = [build_thread_card(thread, participant_map.get(thread.id), pinned_ids) for thread in threads]
    _sort_thread_cards(all_thread_cards)

    thread_cards = [
        item for item in all_thread_cards
        if _card_matches_filter(
            item,
            current_filter=current_filter,
            current_scope=current_scope,
            search_query=search_query,
        )
    ]
    scope_thread_cards = [
        item for item in all_thread_cards
        if current_scope != "self" or item["thread"].thread_type == "self"
    ]
    return {
        "all_thread_cards": all_thread_cards,
        "thread_cards": thread_cards,
        "scope_thread_cards": scope_thread_cards,
        "filter_counts": _thread_filter_counts_sql(current_scope, pinned_ids),
        "participant_map": participant_map,
    }


def resolve_selected_inbox_thread(
    *,
    selected_thread_id: int | None,
    current_scope: str,
    thread_cards: list[dict[str, Any]],
    all_thread_cards: list[dict[str, Any]],
    now,
) -> dict[str, Any]:
    """Secili thread icin mesajlari, katilimcilari ve presence payload'unu okur."""

    selected_thread = None
    selected_messages: list[Any] = []
    selected_participants: list[Any] = []
    selected_thread_card = None
    selected_reaction_map: dict[int, list[dict[str, Any]]] = {}
    selected_thread_presence = {"typing_text": None, "last_active_text": None, "statuses": []}

    if not selected_thread_id and current_scope == "self":
        self_thread_card = next((item for item in thread_cards if item["thread"].thread_type == "self"), None)
        if self_thread_card:
            selected_thread_id = self_thread_card["thread"].id

    if selected_thread_id:
        participant = (
            MessageThreadParticipant.query
            .filter_by(thread_id=selected_thread_id, user_id=current_user.id)
            .filter(MessageThreadParticipant.left_at.is_(None))
            .first()
        )

        if participant:
            selected_thread = db.session.get(orm_entity(MessageThread), selected_thread_id)
            selected_thread_card = next((item for item in all_thread_cards if item["thread"].id == selected_thread_id), None)

            if selected_thread and selected_thread.is_active:
                selected_messages = list(reversed(
                    selected_thread.messages
                    .order_by(Message.sent_at.desc(), Message.id.desc())
                    .limit(THREAD_MESSAGE_SOFT_LIMIT)
                    .all()
                ))
                selected_participants = (
                    selected_thread.participants
                    .filter(MessageThreadParticipant.left_at.is_(None))
                    .all()
                )
                if selected_messages:
                    participant.last_read_message_id = selected_messages[-1].id
                    db.session.commit()
                    if selected_thread_card:
                        selected_thread_card["unread_count"] = 0
                selected_reaction_map = build_reaction_map(selected_messages)
                selected_thread_presence = build_thread_presence(selected_thread, selected_participants, now)

    return {
        "selected_thread_id": selected_thread_id,
        "selected_thread": selected_thread,
        "selected_messages": selected_messages,
        "selected_participants": selected_participants,
        "selected_thread_card": selected_thread_card,
        "selected_reaction_map": selected_reaction_map,
        "selected_thread_presence": selected_thread_presence,
    }
