from __future__ import annotations

import logging
from typing import Any

from flask import current_app, has_app_context
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import Notification
from app.services.mail_core import send_email

logger = logging.getLogger(__name__)

MAIL_TYPE = "system_notification_alert"
_INFO_PAYLOADS = "bys360_notification_mail_payloads_v1"
_INFO_SEEN = "bys360_notification_mail_seen_v1"
_REGISTERED = False


def _safe_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _clean(value: Any, *, limit: int = 500) -> str:
    text_value = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    while "  " in text_value:
        text_value = text_value.replace("  ", " ")
    return text_value[:limit]


def _enabled() -> bool:
    if not has_app_context():
        return False
    raw = current_app.config.get("BYS360_NOTIFICATION_EMAILS_ENABLED", True)
    return str(raw).strip().lower() not in {"0", "false", "off", "hayir", "hayır", "no"}


def _base_url() -> str:
    if not has_app_context():
        return ""
    return str(current_app.config.get("APP_BASE_URL") or current_app.config.get("BASE_URL") or "").rstrip("/")


def _absolute_link(link_url: Any) -> str:
    link = str(link_url or "").strip()
    if not link:
        return _base_url() or "/"
    if link.startswith("http://") or link.startswith("https://"):
        return link
    base = _base_url()
    if not base:
        return link if link.startswith("/") else f"/{link}"
    return f"{base}/{link.lstrip('/')}"


def _collect_notification_payloads(session: Session, flush_context: Any) -> None:  # noqa: ARG001
    """Yeni Notification kayıtlarını commit sonrası mail gönderimi için kuyruklar."""
    if not _enabled():
        return

    payloads = session.info.setdefault(_INFO_PAYLOADS, [])
    seen = session.info.setdefault(_INFO_SEEN, set())

    for obj in list(session.new):
        if not isinstance(obj, Notification):
            continue
        user_id = _safe_int(getattr(obj, "user_id", None))
        if not user_id:
            continue
        notification_id = _safe_int(getattr(obj, "id", None))
        key = notification_id or (
            user_id,
            _clean(getattr(obj, "title", ""), limit=255),
            _clean(getattr(obj, "notification_type", ""), limit=50),
            _clean(getattr(obj, "source_type", ""), limit=50),
            _safe_int(getattr(obj, "source_id", None)),
        )
        if key in seen:
            continue
        seen.add(key)
        payloads.append(
            {
                "notification_id": notification_id,
                "user_id": user_id,
                "title": _clean(getattr(obj, "title", ""), limit=255) or "BYS360 bildirimi",
                "body": _clean(getattr(obj, "body", ""), limit=700),
                "notification_type": _clean(getattr(obj, "notification_type", ""), limit=50) or "system",
                "source_type": _clean(getattr(obj, "source_type", ""), limit=50),
                "source_id": _safe_int(getattr(obj, "source_id", None)),
                "link_url": str(getattr(obj, "link_url", "") or "").strip(),
                "priority": _clean(getattr(obj, "priority", ""), limit=20) or "normal",
            }
        )


def _clear_notification_payloads(session: Session) -> None:
    session.info.pop(_INFO_PAYLOADS, None)
    session.info.pop(_INFO_SEEN, None)


def _user_mail_row(user_id: int) -> dict[str, Any] | None:
    sql = text("SELECT id, email, ad, soyad FROM users WHERE id = :user_id LIMIT 1")
    with db.engine.connect() as connection:
        row = connection.execute(sql, {"user_id": user_id}).mappings().first()
        return dict(row) if row else None


def _recipient_name(row: dict[str, Any]) -> str:
    name = " ".join(part for part in [_clean(row.get("ad"), limit=80), _clean(row.get("soyad"), limit=80)] if part).strip()
    return name or "BYS360 kullanıcısı"


def _build_mail(row: dict[str, Any], payload: dict[str, Any]) -> tuple[str, str]:
    app_name = "BYS360"
    if has_app_context():
        app_name = str(current_app.config.get("APP_NAME", "BYS360") or "BYS360").strip() or "BYS360"
    title = _clean(payload.get("title"), limit=220) or "Yeni bildirim"
    link = _absolute_link(payload.get("link_url"))
    subject = f"{app_name} | Yeni bildiriminiz var"
    body = f"""Sayın {_recipient_name(row)},

{app_name} sisteminde size ait yeni bir bildirim bulunmaktadır.

Bildirim başlığı: {title}

Detayları görüntülemek için lütfen sisteme giriş yapınız.
Sistem bağlantısı: {link}

Bu e-posta yalnızca bilgilendirme amacıyla gönderilmiştir.
İyi çalışmalar dileriz.
{app_name}
""".strip()
    return subject, body


def _insert_mail_log(
    *,
    user_id: int,
    recipient_email: str,
    subject: str,
    body: str,
    ok: bool,
    message: str,
) -> None:
    sql = text(
        """
        INSERT INTO mail_logs
            (mail_type, related_user_id, recipient_email, subject, body_preview, sent_at, is_success, error_message)
        VALUES
            (:mail_type, :related_user_id, :recipient_email, :subject, :body_preview, :sent_at, :is_success, :error_message)
        """
    )
    with db.engine.begin() as connection:
        connection.execute(
            sql,
            {
                "mail_type": MAIL_TYPE,
                "related_user_id": user_id,
                "recipient_email": recipient_email,
                "subject": subject[:255],
                "body_preview": body[:1000],
                "sent_at": utc_now(),
                "is_success": bool(ok),
                "error_message": None if ok else _clean(message, limit=900),
            },
        )


def _deliver_notification_mail(payload: dict[str, Any]) -> None:
    user_id = _safe_int(payload.get("user_id"))
    if not user_id:
        return
    row = _user_mail_row(user_id)
    if not row:
        return
    recipient = _clean(row.get("email"), limit=255)
    if not recipient or "@" not in recipient:
        logger.info("BYS360 notification mail skipped: user_id=%s has no valid email", user_id)
        return

    subject, body = _build_mail(row, payload)
    ok, message = send_email(recipient, subject, body)
    _insert_mail_log(
        user_id=user_id,
        recipient_email=recipient,
        subject=subject,
        body=body,
        ok=ok,
        message=message,
    )


def _send_after_commit(session: Session) -> None:
    payloads = list(session.info.pop(_INFO_PAYLOADS, []) or [])
    session.info.pop(_INFO_SEEN, None)
    if not payloads or not _enabled():
        return

    for payload in payloads:
        try:
            _deliver_notification_mail(payload)
        except Exception:
            logger.exception("BYS360 bildirim e-posta gönderimi başarısız oldu.")


def _clear_after_rollback(session: Session) -> None:
    _clear_notification_payloads(session)


def register_notification_mailer(app: Any | None = None) -> None:  # noqa: ARG001
    """Yeni sistem içi bildirimler için e-posta bilgilendirme dinleyicisini kurar."""
    global _REGISTERED
    if _REGISTERED:
        return
    event.listen(Session, "after_flush", _collect_notification_payloads)
    event.listen(Session, "after_commit", _send_after_commit)
    event.listen(Session, "after_rollback", _clear_after_rollback)
    _REGISTERED = True
    logger.info("BYS360 Notification Mailer V1 aktif edildi.")


__all__ = ["MAIL_TYPE", "register_notification_mailer"]
