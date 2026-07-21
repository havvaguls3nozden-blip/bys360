from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any

from app.extensions import db
from app.models import Message, MessageThread, MessageThreadParticipant
from app.route_support import ensure_boolean_toggle


@dataclass(frozen=True)
class MessageStateChangeResult:
    ok: bool
    message: str | None = None
    payload: dict | None = None


def ok_state(message: str | None = None, **payload) -> MessageStateChangeResult:
    return MessageStateChangeResult(True, message=message, payload=payload or None)


def blocked_state(message: str, **payload) -> MessageStateChangeResult:
    return MessageStateChangeResult(False, message=message, payload=payload or None)


def _participant_for_user_thread(thread_id: int, user_id: int):
    return (
        MessageThreadParticipant.query
        .filter_by(thread_id=thread_id, user_id=user_id)
        .filter(MessageThreadParticipant.left_at.is_(None))
        .first()
    )


def mark_thread_read_for_user(thread_id: int, user_id: int) -> MessageStateChangeResult:
    """Konusmayi mevcut kullanici icin okundu isaretler.

    Bu fonksiyon eski route davranisini korur: son mesaj varsa last_read_message_id
    guncellenir ve commit edilir; mesaj yoksa basarili durum doner ama gereksiz DB
    yazimi yapmaz.
    """
    participant = _participant_for_user_thread(thread_id, user_id)
    if not participant:
        return blocked_state("Konuşma bulunamadı.", error="not_found", thread_id=thread_id)

    thread = db.session.get(MessageThread, thread_id)
    if not thread:
        return blocked_state("Konuşma bulunamadı.", error="not_found", thread_id=thread_id)

    last_message = (
        thread.messages
        .filter(Message.is_deleted.is_(False))
        .order_by(Message.sent_at.desc(), Message.id.desc())
        .first()
    )
    if last_message:
        participant.last_read_message_id = last_message.id
        db.session.commit()

    return ok_state(
        "Konuşma okundu olarak işaretlendi.",
        thread_id=thread_id,
        participant_id=getattr(participant, "id", None),
        last_read_message_id=getattr(last_message, "id", None) if last_message else None,
    )


def toggle_thread_mute_for_user(thread_id: int, user_id: int, requested_state: Any | None = None) -> MessageStateChangeResult:
    participant = _participant_for_user_thread(thread_id, user_id)
    if not participant:
        return blocked_state("Konuşma bulunamadı.", error="not_found", thread_id=thread_id)

    participant.is_muted = ensure_boolean_toggle(
        current_value=getattr(participant, "is_muted", False),
        entity_label="Sohbet sessiz durumu",
        requested_state=requested_state,
    )
    db.session.commit()
    return ok_state(
        "Sohbet sessize alındı." if participant.is_muted else "Sohbet sessizden çıkarıldı.",
        thread_id=thread_id,
        participant_id=getattr(participant, "id", None),
        is_muted=bool(participant.is_muted),
    )


def toggle_thread_archive_for_user(thread_id: int, user_id: int, requested_state: Any | None = None) -> MessageStateChangeResult:
    participant = _participant_for_user_thread(thread_id, user_id)
    if not participant:
        return blocked_state("Konuşma bulunamadı.", error="not_found", thread_id=thread_id)

    participant.is_archived = ensure_boolean_toggle(
        current_value=getattr(participant, "is_archived", False),
        entity_label="Sohbet arşiv durumu",
        requested_state=requested_state,
    )
    db.session.commit()
    return ok_state(
        "Sohbet arşive alındı." if participant.is_archived else "Sohbet arşivden çıkarıldı.",
        thread_id=thread_id,
        participant_id=getattr(participant, "id", None),
        is_archived=bool(participant.is_archived),
    )


def toggle_thread_pin_for_user(
    thread_id: int,
    user_id: int,
    session_obj: MutableMapping[str, Any],
    requested_state: Any | None = None,
    *,
    max_pins: int = 25,
) -> MessageStateChangeResult:
    """Thread sabitleme durumunu session icinde yonetir.

    Eski davranis korunur: pin listesi kullanici bazli session anahtarinda tutulur,
    explicit target_state varsa ona uyulur, yoksa toggle edilir.
    """
    participant = _participant_for_user_thread(thread_id, user_id)
    if not participant:
        return blocked_state("Konuşma bulunamadı.", error="not_found", thread_id=thread_id)

    pin_key = f"message_pins_{user_id}"
    raw_pins = session_obj.get(pin_key, []) or []
    pinned = [int(x) for x in raw_pins if str(x).isdigit()]
    target_state = (str(requested_state or "")).strip().lower()

    if target_state in {"1", "true", "on", "yes", "pin"}:
        if thread_id in pinned:
            message = "Sohbet zaten sabitli."
            level = "warning"
        else:
            pinned.insert(0, thread_id)
            message = "Sohbet sabitlendi."
            level = "success"
    elif target_state in {"0", "false", "off", "no", "unpin"}:
        if thread_id not in pinned:
            message = "Sohbet zaten sabit değil."
            level = "warning"
        else:
            pinned = [x for x in pinned if x != thread_id]
            message = "Sohbet sabitlemeden çıkarıldı."
            level = "success"
    elif thread_id in pinned:
        pinned = [x for x in pinned if x != thread_id]
        message = "Sohbet sabitlemeden çıkarıldı."
        level = "success"
    else:
        pinned.insert(0, thread_id)
        message = "Sohbet sabitlendi."
        level = "success"

    session_obj[pin_key] = pinned[:max_pins]
    try:
        session_obj.modified = True
    except Exception:
        # Testlerde dict benzeri basit nesneler kullanilabilir; Flask session disinda
        # modified alani olmayabilir.
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/messages/state.py:159)")

    return ok_state(
        message,
        thread_id=thread_id,
        participant_id=getattr(participant, "id", None),
        is_pinned=thread_id in session_obj.get(pin_key, []),
        flash_level=level,
        pin_count=len(session_obj.get(pin_key, [])),
    )
