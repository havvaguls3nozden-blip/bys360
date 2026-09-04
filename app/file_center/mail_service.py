"""BYS360 Dosya Merkezi e-posta gönderim servisi.

V1F kapsamı:
- Gerçek SMTP gönderimi
- FileCenterMailLog kayıtları
- Manuel istek maili ve hatırlatma maili gövdesi
- Local otomatik hatırlatma scriptiyle ortak kullanılabilir yapı
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from flask import current_app

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models.file_center_models import FileCenterMailLog, FileRequest


def _env_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        value = str(current_app.config.get(key, ""))
    if value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "evet", "on", "açık", "acik"}


def file_center_mail_enabled() -> bool:
    return _env_bool("FILE_CENTER_MAIL_ENABLED", False)


def _smtp_port() -> int:
    return int(os.getenv("FILE_CENTER_SMTP_PORT") or current_app.config.get("FILE_CENTER_SMTP_PORT") or 587)


def _smtp_host() -> str:
    return str(os.getenv("FILE_CENTER_SMTP_HOST") or current_app.config.get("FILE_CENTER_SMTP_HOST") or "").strip()


def _smtp_user() -> str:
    return str(os.getenv("FILE_CENTER_SMTP_USER") or current_app.config.get("FILE_CENTER_SMTP_USER") or "").strip()


def _smtp_password() -> str:
    return str(os.getenv("FILE_CENTER_SMTP_PASSWORD") or current_app.config.get("FILE_CENTER_SMTP_PASSWORD") or "").strip()


def _from_email() -> str:
    return str(os.getenv("FILE_CENTER_MAIL_FROM") or current_app.config.get("FILE_CENTER_MAIL_FROM") or _smtp_user()).strip()


def _from_name() -> str:
    return str(os.getenv("FILE_CENTER_MAIL_FROM_NAME") or current_app.config.get("FILE_CENTER_MAIL_FROM_NAME") or "BYS360 Dosya Merkezi").strip()


def mail_status_label(status: str | None) -> str:
    mapping = {
        "sent": "Gönderildi",
        "failed": "Başarısız",
        "skipped": "Atlandı",
        "pending": "Bekliyor",
    }
    return mapping.get(str(status or "").lower(), "Bilinmiyor")


def mail_purpose_label(purpose: str | None) -> str:
    mapping = {
        "request_invitation": "Dosya isteği maili",
        "manual_reminder": "Manuel hatırlatma",
        "auto_reminder": "Otomatik hatırlatma",
    }
    return mapping.get(str(purpose or "").lower(), "E-posta")


def build_file_request_email(row: FileRequest, upload_url: str, *, reminder: bool = False) -> tuple[str, str]:
    recipient = row.recipient_name or "İlgili kişi"
    deadline = row.expires_at.strftime("%d.%m.%Y %H:%M") if row.expires_at else "Belirtilmedi"
    allowed = row.allowed_extensions or "Güvenlik nedeniyle engellenen dosya türleri dışındaki dosyalar"
    description = (row.description or "").strip()

    if reminder:
        subject = f"Hatırlatma: {row.title} dosya yükleme talebi"
        intro = "BYS360 Dosya Merkezi üzerinden daha önce iletilen dosya yükleme talebi için hatırlatma yapılmaktadır."
    else:
        subject = f"BYS360 Dosya Yükleme Talebi: {row.title}"
        intro = "BYS360 Dosya Merkezi üzerinden tarafınızdan dosya yüklemeniz istenmektedir."

    lines = [
        f"Sayın {recipient},",
        "",
        intro,
        "",
        f"Talep başlığı: {row.title}",
    ]
    if description:
        lines.extend(["", f"Açıklama: {description}"])
    lines.extend([
        "",
        f"Yükleme bağlantısı: {upload_url}",
        f"Son yükleme tarihi: {deadline}",
        f"Kabul edilen dosya türleri: {allowed}",
        "",
        "Lütfen yükleme şifresini bu bağlantıdan ayrı olarak size iletilen kanaldan kullanınız.",
        "Bağlantı süreli ve kayıtlıdır; yüklenen dosya BYS360 Dosya Merkezi’ne güvenli şekilde alınacaktır.",
        "",
        "İyi çalışmalar.",
        "BYS360 Dosya Merkezi",
    ])
    return subject, "\n".join(lines)


def send_file_center_email(
    *,
    recipient_email: str,
    subject: str,
    body: str,
    purpose: str,
    request_id: int | None = None,
    actor_user_id: int | None = None,
) -> FileCenterMailLog:
    host = _smtp_host()
    log = FileCenterMailLog(
        request_id=request_id,
        actor_user_id=actor_user_id,
        recipient_email=(recipient_email or "").strip(),
        subject=subject,
        body=body,
        purpose=purpose,
        status="pending",
        smtp_host=host or None,
    )
    db.session.add(log)
    db.session.flush()

    if not log.recipient_email:
        log.status = "skipped"
        log.error_message = "Alıcı e-posta adresi bulunmadığı için gönderim yapılmadı."
        return log

    if not file_center_mail_enabled():
        log.status = "skipped"
        log.error_message = "FILE_CENTER_MAIL_ENABLED aktif olmadığı için gerçek e-posta gönderimi yapılmadı."
        return log

    from_email = _from_email()
    if not host or not from_email:
        log.status = "failed"
        log.error_message = "SMTP host veya gönderici e-posta bilgisi eksik."
        return log

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = formataddr((_from_name(), from_email))
        msg["To"] = log.recipient_email
        msg.set_content(body, subtype="plain", charset="utf-8")

        with smtplib.SMTP(host, _smtp_port(), timeout=30) as smtp:
            if _env_bool("FILE_CENTER_SMTP_USE_TLS", True):
                smtp.starttls()
            user = _smtp_user()
            password = _smtp_password()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)

        log.status = "sent"
        log.sent_at = utc_now()
        return log
    except Exception:  # local mail logu için kullanıcıya gösterilecek kontrollü hata
        current_app.logger.exception("BYS360 Dosya Merkezi e-posta gönderimi başarısız oldu.")
        log.status = "failed"
        log.error_message = "E-posta gönderilemedi. Sunucu logları kontrol edilmelidir."
        return log


def send_file_request_email(
    row: FileRequest,
    *,
    upload_url: str,
    purpose: str,
    actor_user_id: int | None = None,
) -> FileCenterMailLog:
    reminder = purpose in {"manual_reminder", "auto_reminder"}
    subject, body = build_file_request_email(row, upload_url, reminder=reminder)
    return send_file_center_email(
        recipient_email=row.recipient_email or "",
        subject=subject,
        body=body,
        purpose=purpose,
        request_id=row.id,
        actor_user_id=actor_user_id,
    )
