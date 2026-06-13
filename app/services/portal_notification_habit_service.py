# -*- coding: utf-8 -*-
"""BYS360 Portal V2E bildirim alışkanlığı servis katmanı."""
from __future__ import annotations

from typing import Any, Callable

from app.models import Notification
from app.route_support import sanitize_free_text


def _safe(factory: Callable[[], Any], default: Any = None) -> Any:
    try:
        return factory()
    except Exception:
        return default


def _user_id(user: Any) -> int:
    try:
        return int(getattr(user, "id", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _label_for_type(value: Any) -> str:
    kind = sanitize_free_text(value, limit=80).lower()
    mapping = {
        "portal_post_created": "Yeni paylaşım",
        "portal_announcement_created": "Duyuru",
        "portal_recognition_created": "Teşekkür",
        "portal_success_created": "İyi uygulama",
        "portal_event_created": "Etkinlik",
        "portal_post_reaction": "Etkileşim",
        "portal_post_comment": "Yorum",
        "portal_comment_reply": "Cevap",
        "portal_comment_mention": "Etiket",
        "support_ticket_comment": "Destek",
        "support_ticket_status_changed": "Destek",
        "survey_assignment": "Anket",
        "survey_published": "Anket",
    }
    return mapping.get(kind, "Bildirim")


def _tone(row: Any) -> str:
    priority = sanitize_free_text(getattr(row, "priority", ""), limit=30).lower()
    kind = sanitize_free_text(getattr(row, "notification_type", ""), limit=80).lower()
    if priority in {"high", "critical", "kritik"}:
        return "danger"
    if kind in {"portal_announcement_created", "portal_comment_mention", "portal_comment_reply"}:
        return "warning"
    if kind.startswith("portal_"):
        return "portal"
    return "normal"


def _item(row: Any) -> dict[str, str]:
    return {
        "title": sanitize_free_text(getattr(row, "title", ""), limit=120) or "Bildirim",
        "body": sanitize_free_text(getattr(row, "body", ""), limit=170) or "Yeni bildiriminiz var.",
        "type_label": _label_for_type(getattr(row, "notification_type", "")),
        "tone": _tone(row),
        "link_url": sanitize_free_text(getattr(row, "link_url", ""), limit=500) or "/notifications",
        "is_read": bool(getattr(row, "is_read", False)),
    }


def portal_notification_habit_context(user: Any) -> dict[str, Any]:
    uid = _user_id(user)
    if uid <= 0:
        return {
            "enabled": False,
            "unread_total": 0,
            "priority_total": 0,
            "portal_total": 0,
            "latest": [],
            "message": "Giriş yaptıktan sonra bildirimleriniz burada görünür.",
        }

    unread_total = int(_safe(lambda: Notification.query.filter_by(user_id=uid, is_read=False).count(), 0) or 0)
    priority_total = int(_safe(lambda: Notification.query.filter(Notification.user_id == uid, Notification.is_read.is_(False), Notification.priority.in_(["high", "critical"])).count(), 0) or 0)
    portal_total = int(_safe(lambda: Notification.query.filter(Notification.user_id == uid, Notification.is_read.is_(False), Notification.notification_type.like("portal_%")).count(), 0) or 0)
    rows = _safe(lambda: Notification.query.filter_by(user_id=uid, is_read=False).order_by(Notification.created_at.desc(), Notification.id.desc()).limit(6).all(), []) or []
    latest = [_item(row) for row in rows]

    if priority_total:
        message = "Öncelikli bildirimleriniz var. İlk olarak bunları kontrol edin."
    elif unread_total:
        message = "Yeni bildirimleriniz var. Portal akışından hızlıca takip edebilirsiniz."
    else:
        message = "Okunmamış bildiriminiz bulunmuyor."

    return {
        "enabled": True,
        "unread_total": unread_total,
        "priority_total": priority_total,
        "portal_total": portal_total,
        "latest": latest,
        "message": message,
        "all_url": "/notifications",
        "portal_url": "/notifications?filter=portal",
    }
