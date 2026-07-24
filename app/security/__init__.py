# app/security/__init__.py
"""
Geriye dönük uyumluluk katmanı.
Eski modüller app.security içinden farklı yardımcılar/validator'lar import ediyor.
Bu dosya onları tek noktadan güvenli biçimde köprüler.
"""
import logging

logger = logging.getLogger(__name__)

import os  # noqa: E402 - deferred import (staged facade/route-registration architecture)
import secrets  # noqa: E402 - deferred import (staged facade/route-registration architecture)
import string  # noqa: E402 - deferred import (staged facade/route-registration architecture)
import uuid  # noqa: E402 - deferred import (staged facade/route-registration architecture)
from pathlib import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    Path,  # noqa: E402 - deferred import (staged facade/route-registration architecture)
)

try:
    from werkzeug.utils import secure_filename
except Exception as exc:
    logger.exception("BYS360 critical exception captured in app/security/__init__.py", exc_info=exc)
    def secure_filename(filename: str) -> str:
        return filename or "upload.bin"

try:
    from flask import current_app
except Exception as exc:
    logger.exception("BYS360 critical exception captured in app/security/__init__.py", exc_info=exc)
    current_app = None  # type: ignore[assignment]

try:
    from .upload_security import UploadValidationError, validate_upload as _core_validate_upload
except Exception as exc:
    logger.exception("BYS360 critical exception captured in app/security/__init__.py", exc_info=exc)
    _core_validate_upload = None  # type: ignore[assignment]
    UploadValidationError = ValueError  # type: ignore[misc,assignment]

try:
    from .email_policy import (
        corporate_email_error_message,
        get_allowed_email_domains,
        is_allowed_corporate_email,
        normalize_email,
    )
except Exception as exc:
    logger.exception("BYS360 critical exception captured in app/security/__init__.py", exc_info=exc)
    corporate_email_error_message = None  # type: ignore[assignment]
    get_allowed_email_domains = None  # type: ignore[assignment]
    is_allowed_corporate_email = None  # type: ignore[assignment]
    normalize_email = None  # type: ignore[assignment]


DEFAULT_MESSAGE_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx",
    "png", "jpg", "jpeg", "webp", "txt", "zip"
}

DEFAULT_REPOSITORY_DOCUMENT_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "txt", "csv", "zip", "rar", "7z"
}

DEFAULT_IMAGE_EXTENSIONS = {
    "png", "jpg", "jpeg", "webp", "gif"
}

DEFAULT_MEDIA_EXTENSIONS = DEFAULT_IMAGE_EXTENSIONS | {"mp4", "mov", "webm", "avi", "mkv"}

DEFAULT_EXCEL_EXTENSIONS = {"xls", "xlsx", "csv"}


# app.security artık bir paket olduğu için `from app.security import ...` çağrıları
# bu __init__ dosyasına düşüyor. Kökte ayrıca `app/security.py` bulunduğundan,
# paket-modül gölgelemesi sebebiyle sabitlerin burada da export edilmesi gerekiyor.
# Aksi halde security_guards import aşamasında ImportError veriyor.
PROFILE_PHOTO_MAX_BYTES = 5 * 1024 * 1024
EXCEL_MAX_BYTES = 20 * 1024 * 1024
REPOSITORY_DOCUMENT_MAX_BYTES = 25 * 1024 * 1024
REPOSITORY_MEDIA_MAX_BYTES = 15 * 1024 * 1024


def _legacy_basic_validation(file_storage, allowed_extensions=None, max_size=None):
    filename = secure_filename(getattr(file_storage, "filename", "") or "")
    if not filename:
        return None, "Dosya adı boş."

    ext = Path(filename).suffix.lower().lstrip(".")
    allowed = {str(x).lower().lstrip('.') for x in (allowed_extensions or []) if str(x).strip()}
    if allowed and ext not in allowed:
        return None, f"İzin verilmeyen dosya uzantısı: .{ext}"

    size = 0
    stream = getattr(file_storage, "stream", None)
    if stream is not None:
        pos = stream.tell()
        try:
            stream.seek(0, os.SEEK_END)
            size = int(stream.tell() or 0)
        finally:
            stream.seek(pos)

    if max_size and size > int(max_size):
        return None, "Dosya boyutu izin verilen sınırı aşıyor."

    return {
        "original_filename": filename,
        "extension": ext,
        "size": size,
        "detected_mime": getattr(file_storage, "mimetype", None) or "application/octet-stream",
    }, None


def _run_validation(file_storage, allowed_extensions=None, max_size=None):
    if _core_validate_upload is None:
        return _legacy_basic_validation(file_storage, allowed_extensions=allowed_extensions, max_size=max_size)

    try:
        meta = _core_validate_upload(
            file_storage,
            allowed_extensions=allowed_extensions,
            max_size=max_size,
        )
    except TypeError:
        try:
            meta = _core_validate_upload(
                file_storage,
                allowed_extensions=allowed_extensions,
            )
        except (UploadValidationError, ValueError) as exc:
            return None, str(exc)
    except (UploadValidationError, ValueError) as exc:
        return None, str(exc)

    if max_size and int(meta.get("size") or 0) > int(max_size):
        return None, "Dosya boyutu izin verilen sınırı aşıyor."

    return meta, None


def _ok_message_tuple(file_storage, allowed_extensions=None, max_size=None):
    meta, error = _run_validation(file_storage, allowed_extensions=allowed_extensions, max_size=max_size)
    if error:
        return False, error
    return True, "ok"


def _ok_message_name_size_tuple(file_storage, allowed_extensions=None, max_size=None):
    meta, error = _run_validation(file_storage, allowed_extensions=allowed_extensions, max_size=max_size)
    if error:
        original_name = secure_filename(getattr(file_storage, "filename", "") or "")
        size = 0
        return False, error, original_name, size
    return True, "ok", meta.get("original_filename", ""), int(meta.get("size") or 0)


def validate_upload(file_storage, allowed_extensions=None, max_size=None):
    return _run_validation(file_storage, allowed_extensions=allowed_extensions, max_size=max_size)


def validate_message_attachment(file_storage, allowed_extensions=None, max_size=None):
    return _ok_message_name_size_tuple(
        file_storage,
        allowed_extensions=allowed_extensions or DEFAULT_MESSAGE_EXTENSIONS,
        max_size=max_size,
    )


def validate_repository_document(file_storage, allowed_extensions=None, max_size=None):
    return _ok_message_name_size_tuple(
        file_storage,
        allowed_extensions=allowed_extensions or DEFAULT_REPOSITORY_DOCUMENT_EXTENSIONS,
        max_size=max_size,
    )


def validate_repository_image(file_storage, allowed_extensions=None, max_size=None):
    meta, error = _run_validation(
        file_storage,
        allowed_extensions=allowed_extensions or DEFAULT_IMAGE_EXTENSIONS,
        max_size=max_size,
    )
    if error:
        return False, [error]
    return True, []


def validate_repository_media(file_storage, allowed_extensions=None, max_size=None):
    return _ok_message_name_size_tuple(
        file_storage,
        allowed_extensions=allowed_extensions or DEFAULT_MEDIA_EXTENSIONS,
        max_size=max_size,
    )


def validate_portal_media(file_storage, allowed_extensions=None, max_size=None):
    return validate_repository_media(
        file_storage,
        allowed_extensions=allowed_extensions,
        max_size=max_size,
    )


def validate_excel_file(file_storage, allowed_extensions=None, max_size=None):
    return _ok_message_tuple(
        file_storage,
        allowed_extensions=allowed_extensions or DEFAULT_EXCEL_EXTENSIONS,
        max_size=max_size,
    )


_INSECURE_FIRST_LOGIN_PASSWORDS = {
    "123456",
    "12345678",
    "password",
    "admin",
    "changeme",
    "change-me",
    "CHANGE_ME",
}


def _configured_first_login_password() -> str:
    try:
        if current_app:
            cfg = (current_app.config.get("DEFAULT_FIRST_LOGIN_PASSWORD") or "").strip()
            if cfg:
                return cfg
    except Exception as exc:
        logger.exception("BYS360 critical exception captured in app/security/__init__.py", exc_info=exc)
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/security/__init__.py)")
    return (os.getenv("DEFAULT_FIRST_LOGIN_PASSWORD") or "").strip()


def generate_secure_first_login_password(length: int = 14) -> str:
    """Yeni kullanıcı için güvenli başlangıç şifresi üretir.

    DEFAULT_FIRST_LOGIN_PASSWORD ortam değişkeni yalnızca güvenli ve bilinçli
    biçimde verilmişse kullanılır. Aksi halde her kullanıcı için rastgele,
    tahmini zor bir şifre üretilir.
    """
    configured = _configured_first_login_password()
    if configured and configured not in _INSECURE_FIRST_LOGIN_PASSWORDS and len(configured) >= 10:
        return configured

    alphabet = string.ascii_letters + string.digits
    # En az bir küçük harf, bir büyük harf ve bir rakam içersin.
    parts = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
    ]
    parts.extend(secrets.choice(alphabet) for _ in range(max(length, 12) - len(parts)))
    secrets.SystemRandom().shuffle(parts)
    return ''.join(parts)


def get_default_first_login_password() -> str:
    """Geriye dönük uyumluluk için güvenli ilk giriş şifresi döndürür."""
    return generate_secure_first_login_password()


def save_profile_photo_to_user(file_storage, user=None, upload_folder=None, subdir="profile_photos"):
    """
    Geriye dönük uyumluluk için basit profil fotoğrafı kaydetme yardımcısı.
    Dosyayı kaydeder, mümkünse kullanıcı nesnesine photo/profile_image alanını yazar.
    """
    if not file_storage or not getattr(file_storage, "filename", None):
        return None

    ok, errors = validate_repository_image(file_storage, max_size=PROFILE_PHOTO_MAX_BYTES)
    if ok is False:
        if isinstance(errors, str):
            message = errors
        else:
            message = "; ".join(errors or ["Geçersiz profil fotoğrafı."])
        raise ValueError(message)

    # BYS360_PROFILE_PHOTO_SAVE_CANONICAL_V2_17_73
    # User modelinde asıl alan profile_photo_path olduğu için personel/profil
    # fotoğrafı yeni kayıtlarda app/static/uploads/profile_photos altında
    # saklanır ve portalda doğrudan görüntülenebilir hale gelir.
    if user is not None and hasattr(user, "profile_photo_path"):
        try:
            file_storage.stream.seek(0)
        except Exception as exc:
            logger.exception("BYS360 critical exception captured in app/security/__init__.py", exc_info=exc)
            pass
        from app.services.profile_photo_service import (
            save_profile_photo as _canonical_profile_photo_save,
        )
        return _canonical_profile_photo_save(file_storage, user)

    filename = secure_filename(file_storage.filename)
    ext = Path(filename).suffix.lower()
    final_name = f"{uuid.uuid4().hex}{ext}"

    root = upload_folder
    if not root:
        root = os.getenv("UPLOAD_FOLDER")
    if not root:
        try:
            if current_app:
                root = current_app.config.get("UPLOAD_FOLDER")
        except Exception as exc:
            logger.exception("BYS360 critical exception captured in app/security/__init__.py", exc_info=exc)
            root = None
    if not root:
        root = "uploads"

    target_dir = Path(root) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / final_name

    file_storage.save(str(target_path))

    relative_path = f"{subdir}/{final_name}".replace("\\", "/")

    if user is not None:
        for attr in ("profile_photo", "profile_image", "photo", "avatar", "image_path"):
            if hasattr(user, attr):
                try:
                    setattr(user, attr, relative_path)
                    break
                except Exception as exc:
                    logger.exception("BYS360 critical exception captured in app/security/__init__.py", exc_info=exc)
                    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/security/__init__.py)")

    return relative_path


__all__ = [
    "validate_upload",
    "validate_message_attachment",
    "validate_repository_document",
    "validate_repository_image",
    "validate_repository_media",
    "validate_portal_media",
    "validate_excel_file",
    "get_default_first_login_password",
    "generate_secure_first_login_password",
    "save_profile_photo_to_user",
    "get_allowed_email_domains",
    "normalize_email",
    "is_allowed_corporate_email",
    "corporate_email_error_message",
    "PROFILE_PHOTO_MAX_BYTES",
    "EXCEL_MAX_BYTES",
    "REPOSITORY_DOCUMENT_MAX_BYTES",
    "REPOSITORY_MEDIA_MAX_BYTES",
    # audit
    "SecurityAuditFinding",
    "collect_runtime_security_findings",
    "findings_to_dicts",
    "build_security_audit_summary",
    "log_runtime_security_posture",
    # guards
    "UploadGuardProfile",
    "DEFAULT_UPLOAD_PROFILES",
    "resolve_upload_guard",
    "build_security_runtime_report",
    # headers
    "DEFAULT_CSP",
    "build_csp_header",
    "apply_default_security_headers",
    "inject_csp_nonce_into_html",
]


# ---------------------------------------------------------------------------
# security.audit, security.guards, security.headers alt modülleri re-export
# ---------------------------------------------------------------------------
from app.security.audit import (  # noqa: F401, E402
    SecurityAuditFinding,
    build_security_audit_summary,
    collect_runtime_security_findings,
    findings_to_dicts,
    log_runtime_security_posture,
)
from app.security.guards import (  # noqa: F401, E402
    DEFAULT_UPLOAD_PROFILES,
    UploadGuardProfile,
    build_security_runtime_report,
    resolve_upload_guard,
)
from app.security.headers import (  # noqa: F401, E402
    DEFAULT_CSP,
    apply_default_security_headers,
    build_csp_header,
    inject_csp_nonce_into_html,
)
