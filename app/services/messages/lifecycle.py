
"""Mesaj düzenleme, silme ve ek indirme servisleri.

Faz 10 kapsamı mesajlaşma canlı modülünün son yazma/okuma kenarlarını route
katmanından ayırır. Route tarafında AJAX/flash/yönlendirme dili korunur; bu
servis yalnızca yetki, durum doğrulama, DB yazımı ve ek indirme çözümlemesini
üstlenir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.extensions import db
from app.models import Message
from app.services.communication_service import (
    CommunicationServiceError,
    resolve_message_attachment_download,
)

from .attachments import get_message_attachment_for_user
from .repository import orm_entity
from .serialization import serialize_message


@dataclass(frozen=True)
class MessageMutationResult:
    ok: bool
    message: str
    status_code: int = 200
    error: str | None = None
    payload: dict[str, Any] | None = None
    flash_level: str = "success"


@dataclass(frozen=True)
class MessageAttachmentDownloadResult:
    ok: bool
    message: str | None = None
    status_code: int = 200
    upload_dir: str | None = None
    safe_name: str | None = None
    download_name: str | None = None
    error: str | None = None


def _blocked(message: str, *, error: str, status_code: int, flash_level: str = "danger", **payload: Any) -> MessageMutationResult:
    return MessageMutationResult(
        ok=False,
        message=message,
        status_code=status_code,
        error=error,
        payload=payload or None,
        flash_level=flash_level,
    )


def _ok(message: str, *, flash_level: str = "success", **payload: Any) -> MessageMutationResult:
    return MessageMutationResult(
        ok=True,
        message=message,
        status_code=200,
        payload=payload or None,
        flash_level=flash_level,
    )


def _message_payload(message: Message) -> dict[str, Any]:
    return {
        "message_id": message.id,
        "thread_id": message.thread_id,
        "body": message.body or "",
        "edited_at": message.edited_at.isoformat() if getattr(message, "edited_at", None) else None,
    }


def edit_message_for_user(message_id: int, *, user_id: int, new_body: str, now) -> MessageMutationResult:
    """Kullanıcının kendi mesajını düzenler.

    Eski route davranışı korunur:
    - bulunamayan mesaj 404 döner
    - başkasının mesajı 403 döner
    - silinmiş/boş mesaj 400 döner
    - değişiklik yoksa başarılı ama info seviyesinde döner
    - DB hatasında rollback yapılıp hata route katmanına yeniden fırlatılır
    """

    message = db.session.get(orm_entity(Message), message_id)
    if not message:
        return _blocked("Mesaj bulunamadı.", error="not_found", status_code=404)

    if message.sender_user_id != user_id:
        return _blocked(
            "Sadece kendi mesajınızı düzenleyebilirsiniz.",
            error="forbidden",
            status_code=403,
            thread_id=message.thread_id,
        )

    if bool(getattr(message, "is_deleted", False)):
        return _blocked(
            "Silinmiş mesaj düzenlenemez.",
            error="deleted",
            status_code=400,
            flash_level="warning",
            thread_id=message.thread_id,
        )

    if not new_body:
        return _blocked(
            "Mesaj içeriği boş bırakılamaz.",
            error="empty",
            status_code=400,
            flash_level="warning",
            thread_id=message.thread_id,
        )

    if new_body == (message.body or ""):
        return _ok(
            "Mesajda değişiklik yapılmadı.",
            flash_level="info",
            **_message_payload(message),
        )

    try:
        message.body = new_body
        message.edited_at = now
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return _ok("Mesaj güncellendi.", **_message_payload(message))


def delete_message_for_user(message_id: int, *, user_id: int, now) -> MessageMutationResult:
    """Mesajı yumuşak silme ile siler.

    Eski canlı davranış korunur: kayıt fiziksel silinmez, ``is_deleted`` true
    yapılır, gövde ``[silindi]`` değerine çekilir ve AJAX için serialize edilmiş
    silinen mesaj payload'u döner.
    """

    message = db.session.get(orm_entity(Message), message_id)
    if not message:
        return _blocked("Mesaj bulunamadı.", error="not_found", status_code=404)

    if message.sender_user_id != user_id:
        return _blocked(
            "Sadece kendi mesajınızı silebilirsiniz.",
            error="forbidden",
            status_code=403,
            thread_id=message.thread_id,
        )

    if bool(getattr(message, "is_deleted", False)):
        return _ok(
            "Mesaj zaten silinmiş.",
            flash_level="warning",
            message_id=message.id,
            thread_id=message.thread_id,
            deleted=True,
        )

    try:
        message.is_deleted = True
        message.edited_at = now
        if not (message.body or "").startswith("[silindi]"):
            message.body = "[silindi]"
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return _ok(
        "Mesaj silindi.",
        message_id=message.id,
        thread_id=message.thread_id,
        deleted=True,
        body=message.body or "[silindi]",
        edited_at=message.edited_at.isoformat() if getattr(message, "edited_at", None) else None,
        deleted_message=serialize_message(message),
    )


def resolve_message_attachment_download_for_user(filename: str, *, user_id: int) -> MessageAttachmentDownloadResult:
    """Ek indirme/görüntüleme için dosya yolunu güvenli şekilde çözer."""

    attachment = get_message_attachment_for_user(filename, user_id)
    if not attachment:
        return MessageAttachmentDownloadResult(
            ok=False,
            message="Bu dosyayı görüntüleme yetkiniz yok ya da dosya bulunamadı.",
            status_code=404,
            error="not_found",
        )

    try:
        upload_dir, safe_name = resolve_message_attachment_download(attachment)
    except CommunicationServiceError as exc:
        return MessageAttachmentDownloadResult(
            ok=False,
            message=str(exc),
            status_code=400,
            error="download_error",
        )

    return MessageAttachmentDownloadResult(
        ok=True,
        upload_dir=str(upload_dir),
        safe_name=safe_name,
        download_name=getattr(attachment, "original_filename", None),
    )
