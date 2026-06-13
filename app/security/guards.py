"""BYS360 yükleme güvenliği koruyucuları.

Upload boyutu profillerini ve runtime güvenlik raporunu sağlar.
app.security.guards olarak import edilir.
"""
from __future__ import annotations


from dataclasses import dataclass
from typing import Any

from flask import current_app

from app.security import EXCEL_MAX_BYTES, PROFILE_PHOTO_MAX_BYTES, REPOSITORY_DOCUMENT_MAX_BYTES, REPOSITORY_MEDIA_MAX_BYTES


@dataclass(frozen=True)
class UploadGuardProfile:
    name: str
    max_bytes: int


DEFAULT_UPLOAD_PROFILES = {
    "profile_photo": UploadGuardProfile("profile_photo", PROFILE_PHOTO_MAX_BYTES),
    "excel": UploadGuardProfile("excel", EXCEL_MAX_BYTES),
    "repository_document": UploadGuardProfile("repository_document", REPOSITORY_DOCUMENT_MAX_BYTES),
    "repository_media": UploadGuardProfile("repository_media", REPOSITORY_MEDIA_MAX_BYTES),
}


def resolve_upload_guard(name: str) -> UploadGuardProfile:
    profile = DEFAULT_UPLOAD_PROFILES[name]
    override = current_app.config.get(f"UPLOAD_MAX_BYTES_{name.upper()}")
    if override in {None, ""}:
        return profile
    try:
        return UploadGuardProfile(profile.name, max(int(override), 0))
    except (TypeError, ValueError):
        return profile


def build_security_runtime_report() -> dict[str, Any]:
    return {
        "max_content_length": int(current_app.config.get("MAX_CONTENT_LENGTH") or 0),
        "csrf_time_limit": int(current_app.config.get("WTF_CSRF_TIME_LIMIT") or 0),
        "session_cookie_secure": bool(current_app.config.get("SESSION_COOKIE_SECURE")),
        "session_cookie_httponly": bool(current_app.config.get("SESSION_COOKIE_HTTPONLY", True)),
        "session_cookie_samesite": current_app.config.get("SESSION_COOKIE_SAMESITE", "Lax"),
        "upload_profiles": {name: profile.max_bytes for name, profile in DEFAULT_UPLOAD_PROFILES.items()},
    }