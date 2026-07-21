from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def format_dt_label(value: datetime | None) -> str | None:
    if not value:
        return None
    try:
        return value.strftime("%d.%m.%Y %H:%M")
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/messages/formatting.py | line=14")
        return None


def message_sender_name(message: Any) -> str:
    sender = getattr(message, "sender", None)
    if sender and getattr(sender, "full_name", None):
        return str(sender.full_name)
    if sender:
        return f"{getattr(sender, 'ad', '') or ''} {getattr(sender, 'soyad', '') or ''}".strip() or "Kullanıcı"
    return "Kullanıcı"


def message_sender_initials(message: Any) -> str:
    sender = getattr(message, "sender", None)
    if not sender:
        return "K"
    first = (getattr(sender, "ad", "") or "")[:1]
    last = (getattr(sender, "soyad", "") or "")[:1]
    initials = f"{first}{last}".upper().strip()
    return initials or "K"
