
"""Video destekli pop-up duyuru servis katmanı.

Faz 5 kapsamı:
- Okunma/onay raporu ve kişi bazlı izleme yüzeyi üretir.
- CSV dışa aktarımı sağlar.
- Faz 4 medya güvenliğini korur.

Faz 4 kapsamı:
- YouTube / Shorts / Vimeo / Dailymotion bağlantılarını güvenli embed URL'ine çevirir.
- Kurum içi yüklenen mp4/webm videolarını kontrollü medya klasöründe saklar.
- Serbest iframe/html/script kabul etmeden runtime medya payload'u üretir.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import csv
import io
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote, urlsplit, parse_qs
from uuid import uuid4

from flask import current_app, has_request_context, url_for
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import OrganizationUnit, User
from app.models.announcement_popup_models import Announcement, AnnouncementRead

ANNOUNCEMENT_TYPES = {
    "info": "Bilgilendirme",
    "warning": "Uyarı",
    "important": "Önemli",
    "maintenance": "Bakım",
}

SHOW_RULES = {
    "every_login": "Her girişte göster",
    "once_per_day": "Günde bir kez göster",
    "once": "Sadece bir kez göster",
}

TARGET_SCOPES = {
    "all": "Tüm kullanıcılar",
    "role": "Role göre",
    "unit": "Birim bazlı",
}

MEDIA_TYPES = {
    "none": "Yok",
    "youtube": "YouTube",
    "vimeo": "Vimeo",
    "dailymotion": "Dailymotion",
    "upload_video": "Kurum videosu",
    "image": "Görsel",
    "pdf": "PDF",
}

SAFE_CTA_SCHEMES = {"http", "https"}
EXTERNAL_VIDEO_TYPES = {"youtube", "vimeo", "dailymotion"}
UPLOAD_MEDIA_TYPES = {"upload_video", "image", "pdf"}

ALLOWED_UPLOAD_EXTENSIONS = {
    "upload_video": {"mp4", "webm"},
    "image": {"jpg", "jpeg", "png", "webp"},
    "pdf": {"pdf"},
}

ALLOWED_UPLOAD_MIME_PREFIXES = {
    "upload_video": ("video/mp4", "video/webm", "application/octet-stream"),
    "image": ("image/jpeg", "image/png", "image/webp", "application/octet-stream"),
    "pdf": ("application/pdf", "application/octet-stream"),
}

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,64}$")
VIMEO_ID_RE = re.compile(r"^[0-9]{4,32}$")
DAILYMOTION_ID_RE = re.compile(r"^[A-Za-z0-9]{4,32}$")


@dataclass(frozen=True)
class AnnouncementFormOptions:
    announcement_types: dict[str, str]
    show_rules: dict[str, str]
    target_scopes: dict[str, str]
    media_types: dict[str, str]
    roles: list[str]
    units: list[OrganizationUnit]


def _clean_text(value: Any, *, limit: int | None = None) -> str:
    text = " ".join(str(value or "").replace("\r", "\n").split())
    if limit:
        return text[:limit]
    return text


def _clean_multiline(value: Any, *, limit: int = 12000) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return text[:limit]


def _parse_datetime_local(value: str | None) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _normalize_choice(value: Any, allowed: dict[str, str], default: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in allowed else default


def _safe_url(value: Any, *, allow_relative: bool = True, limit: int = 1000) -> str:
    raw = str(value or "").strip()[:limit]
    if not raw:
        return ""
    if allow_relative and raw.startswith("/") and not raw.startswith("//"):
        return raw
    parsed = urlsplit(raw)
    if parsed.scheme in SAFE_CTA_SCHEMES and parsed.netloc:
        return raw
    return ""


def _now() -> datetime:
    return datetime.now()


def get_announcement_form_options() -> AnnouncementFormOptions:
    roles = [
        (row[0] or "").strip()
        for row in db.session.query(User.role)
        .filter(User.is_active.is_(True), User.role.isnot(None), func.trim(User.role) != "")
        .group_by(User.role)
        .order_by(func.lower(func.trim(User.role)).asc())
        .all()
    ]
    units = (
        OrganizationUnit.query
        .filter(OrganizationUnit.is_active.is_(True))
        .order_by(OrganizationUnit.name.asc())
        .all()
    )
    return AnnouncementFormOptions(
        announcement_types=ANNOUNCEMENT_TYPES,
        show_rules=SHOW_RULES,
        target_scopes=TARGET_SCOPES,
        media_types=MEDIA_TYPES,
        roles=roles,
        units=units,
    )


def normalize_announcement_form(form: Any) -> dict[str, Any]:
    target_scope = _normalize_choice(form.get("target_scope"), TARGET_SCOPES, "all")
    media_type = _normalize_choice(form.get("media_type"), MEDIA_TYPES, "none")
    target_role = _clean_text(form.get("target_role"), limit=80) if target_scope == "role" else ""

    target_unit_id = None
    if target_scope == "unit":
        try:
            parsed_unit = int(str(form.get("target_unit_id") or "").strip())
            target_unit_id = parsed_unit if parsed_unit > 0 else None
        except (TypeError, ValueError):
            target_unit_id = None

    media_url = _safe_url(form.get("media_url"), allow_relative=False, limit=1000) if media_type in (EXTERNAL_VIDEO_TYPES | {"image", "pdf"}) else ""
    cta_url = _safe_url(form.get("cta_url"), allow_relative=True, limit=1000)

    return {
        "title": _clean_text(form.get("title"), limit=200),
        "body": _clean_multiline(form.get("body"), limit=12000),
        "announcement_type": _normalize_choice(form.get("announcement_type"), ANNOUNCEMENT_TYPES, "info"),
        "is_active": str(form.get("is_active") or "").lower() in {"1", "true", "on", "yes", "aktif"},
        "is_required": str(form.get("is_required") or "").lower() in {"1", "true", "on", "yes", "zorunlu"},
        "show_rule": _normalize_choice(form.get("show_rule"), SHOW_RULES, "once"),
        "target_scope": target_scope,
        "target_role": target_role or None,
        "target_unit_id": target_unit_id,
        "publish_start_at": _parse_datetime_local(form.get("publish_start_at")),
        "publish_end_at": _parse_datetime_local(form.get("publish_end_at")),
        "button_text": _clean_text(form.get("button_text") or "Okudum", limit=80) or "Okudum",
        "media_type": media_type,
        "media_url": media_url or None,
        "media_file_path": _clean_text(form.get("media_file_path"), limit=500) or None,
        "cover_image_path": _safe_url(form.get("cover_image_path"), allow_relative=True, limit=1000) or None,
        "cta_text": _clean_text(form.get("cta_text"), limit=120) or None,
        "cta_url": cta_url or None,
    }


def announcement_media_root() -> Path:
    configured = str(current_app.config.get("ANNOUNCEMENT_MEDIA_ROOT", "") or "").strip()
    if configured:
        return Path(configured)
    # app/ dizininin bir üstü proje köküdür.
    return Path(current_app.root_path).parent / "data" / "uploads" / "announcement_media"


def safe_media_subpath(value: Any) -> str:
    raw = str(value or "").replace("\\", "/").strip().lstrip("/")
    parts = [secure_filename(part) for part in raw.split("/") if secure_filename(part)]
    return "/".join(parts)


def _extension_for_upload(filename: str) -> str:
    return Path(filename or "").suffix.lower().lstrip(".")


def validate_upload_file(file_storage: FileStorage, media_type: str) -> None:
    filename = file_storage.filename or ""
    ext = _extension_for_upload(filename)
    allowed = ALLOWED_UPLOAD_EXTENSIONS.get(media_type, set())
    if ext not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"Bu medya tipi için yalnızca şu dosya uzantıları kabul edilir: {allowed_text}")

    content_type = (file_storage.mimetype or "").lower()
    allowed_mimes = ALLOWED_UPLOAD_MIME_PREFIXES.get(media_type, ())
    if content_type and allowed_mimes and content_type not in allowed_mimes:
        raise ValueError("Dosya içerik tipi seçilen medya tipiyle uyumlu değil.")


def persist_announcement_media_upload(file_storage: FileStorage | None, media_type: str) -> str | None:
    if not file_storage or not (file_storage.filename or "").strip():
        return None
    if media_type not in UPLOAD_MEDIA_TYPES:
        raise ValueError("Bu medya tipi için dosya yükleme desteklenmiyor.")

    validate_upload_file(file_storage, media_type)
    ext = _extension_for_upload(file_storage.filename or "")
    now_text = datetime.now().strftime("%Y%m")
    root = announcement_media_root()
    target_dir = root / now_text
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex}.{ext}"
    target_path = target_dir / filename
    file_storage.save(target_path)
    return f"{now_text}/{filename}"


def process_announcement_media_upload(payload: dict[str, Any], file_storage: FileStorage | None, *, existing: Announcement | None = None) -> dict[str, Any]:
    media_type = (payload.get("media_type") or "none").strip().lower()
    existing_file_path = getattr(existing, "media_file_path", None) if existing else None
    uploaded_path = persist_announcement_media_upload(file_storage, media_type) if file_storage else None

    if media_type == "none":
        payload["media_url"] = None
        payload["media_file_path"] = None
        payload["cover_image_path"] = None
        return payload

    if media_type in EXTERNAL_VIDEO_TYPES:
        payload["media_file_path"] = None
        return payload

    if media_type in UPLOAD_MEDIA_TYPES:
        if uploaded_path:
            payload["media_file_path"] = uploaded_path
            if media_type == "upload_video":
                payload["media_url"] = None
        else:
            payload["media_file_path"] = payload.get("media_file_path") or existing_file_path
    return payload


def _youtube_id_from_url(raw_url: str) -> str | None:
    parsed = urlsplit(raw_url)
    host = (parsed.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    path_parts = [part for part in parsed.path.split("/") if part]

    candidate = ""
    if host == "youtu.be" and path_parts:
        candidate = path_parts[0]
    elif host in {"youtube.com", "youtube-nocookie.com"}:
        if parsed.path == "/watch":
            candidate = (parse_qs(parsed.query).get("v") or [""])[0]
        elif path_parts and path_parts[0] in {"shorts", "embed", "live"} and len(path_parts) > 1:
            candidate = path_parts[1]
    candidate = candidate.strip()
    return candidate if VIDEO_ID_RE.match(candidate) else None


def build_safe_youtube_embed_url(raw_url: str) -> str | None:
    video_id = _youtube_id_from_url(raw_url)
    if not video_id:
        return None
    return f"https://www.youtube-nocookie.com/embed/{video_id}"


def _vimeo_id_from_url(raw_url: str) -> str | None:
    parsed = urlsplit(raw_url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    path_parts = [part for part in parsed.path.split("/") if part]
    candidate = ""
    if host == "vimeo.com" and path_parts:
        candidate = path_parts[-1]
    elif host == "player.vimeo.com" and len(path_parts) >= 2 and path_parts[0] == "video":
        candidate = path_parts[1]
    candidate = candidate.strip()
    return candidate if VIMEO_ID_RE.match(candidate) else None


def build_safe_vimeo_embed_url(raw_url: str) -> str | None:
    video_id = _vimeo_id_from_url(raw_url)
    if not video_id:
        return None
    return f"https://player.vimeo.com/video/{video_id}"


def _dailymotion_id_from_url(raw_url: str) -> str | None:
    parsed = urlsplit(raw_url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    path_parts = [part for part in parsed.path.split("/") if part]
    candidate = ""
    if host == "dai.ly" and path_parts:
        candidate = path_parts[0]
    elif host == "dailymotion.com":
        if len(path_parts) >= 2 and path_parts[0] in {"video", "embed"}:
            candidate = path_parts[-1]
    candidate = candidate.split("_")[0].strip()
    return candidate if DAILYMOTION_ID_RE.match(candidate) else None


def build_safe_dailymotion_embed_url(raw_url: str) -> str | None:
    video_id = _dailymotion_id_from_url(raw_url)
    if not video_id:
        return None
    return f"https://www.dailymotion.com/embed/video/{video_id}"


def build_external_media_embed_url(media_type: str, raw_url: str | None) -> str | None:
    if not raw_url:
        return None
    media_type = (media_type or "").strip().lower()
    if media_type == "youtube":
        return build_safe_youtube_embed_url(raw_url)
    if media_type == "vimeo":
        return build_safe_vimeo_embed_url(raw_url)
    if media_type == "dailymotion":
        return build_safe_dailymotion_embed_url(raw_url)
    return None


def _media_public_url(relative_path: str | None) -> str:
    clean_path = safe_media_subpath(relative_path)
    if not clean_path:
        return ""
    if has_request_context():
        return url_for("main.announcement_popup_media", filename=clean_path)
    return "/announcements/popup/media/" + quote(clean_path)


def build_runtime_media_payload(announcement: Announcement) -> dict[str, str]:
    media_type = (announcement.media_type or "none").strip().lower()
    raw_url = announcement.media_url or ""
    file_url = _media_public_url(announcement.media_file_path)

    payload = {
        "media_type": media_type,
        "media_label": announcement.media_label,
        "media_url": raw_url,
        "media_embed_url": "",
        "media_file_url": file_url,
        "media_kind": "none",
        "cover_image_path": announcement.cover_image_path or "",
    }

    if media_type in EXTERNAL_VIDEO_TYPES:
        embed_url = build_external_media_embed_url(media_type, raw_url)
        if embed_url:
            payload["media_embed_url"] = embed_url
            payload["media_kind"] = "embed_video"
        return payload

    if media_type == "upload_video" and file_url:
        payload["media_url"] = file_url
        payload["media_kind"] = "upload_video"
        return payload

    if media_type == "image":
        payload["media_url"] = file_url or raw_url
        payload["media_kind"] = "image" if payload["media_url"] else "none"
        return payload

    if media_type == "pdf":
        payload["media_url"] = file_url or raw_url
        payload["media_kind"] = "pdf" if payload["media_url"] else "none"
        return payload

    return payload


def validate_announcement_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    media_type = (payload.get("media_type") or "none").strip().lower()
    if not payload.get("title"):
        errors.append("Duyuru başlığı zorunludur.")
    if not payload.get("body"):
        errors.append("Duyuru metni zorunludur.")
    if payload.get("target_scope") == "role" and not payload.get("target_role"):
        errors.append("Rol bazlı duyuru için hedef rol seçilmelidir.")
    if payload.get("target_scope") == "unit" and not payload.get("target_unit_id"):
        errors.append("Birim bazlı duyuru için hedef birim seçilmelidir.")
    if payload.get("publish_start_at") and payload.get("publish_end_at"):
        if payload["publish_end_at"] < payload["publish_start_at"]:
            errors.append("Yayın bitiş tarihi başlangıç tarihinden önce olamaz.")

    if media_type in EXTERNAL_VIDEO_TYPES:
        if not payload.get("media_url"):
            errors.append("Seçilen video tipi için geçerli bir bağlantı girilmelidir.")
        elif not build_external_media_embed_url(media_type, payload.get("media_url")):
            errors.append("Video bağlantısı desteklenen ve güvenli bir YouTube/Vimeo/Dailymotion bağlantısı olmalıdır.")

    if media_type == "upload_video" and not payload.get("media_file_path"):
        errors.append("Kurum videosu için .mp4 veya .webm dosyası yüklenmelidir.")

    if media_type in {"image", "pdf"} and not (payload.get("media_url") or payload.get("media_file_path")):
        errors.append("Seçilen medya tipi için bağlantı girilmeli veya dosya yüklenmelidir.")

    return errors


def apply_payload_to_announcement(announcement: Announcement, payload: dict[str, Any], *, actor_id: int | None) -> Announcement:
    for field_name, field_value in payload.items():
        setattr(announcement, field_name, field_value)
    if not announcement.created_by:
        announcement.created_by = actor_id
    announcement.updated_by = actor_id
    return announcement


def target_user_query(announcement: Announcement | None = None, *, target_scope: str | None = None, target_role: str | None = None, target_unit_id: int | None = None):
    scope = (target_scope or getattr(announcement, "target_scope", None) or "all").strip().lower()
    role = (target_role or getattr(announcement, "target_role", None) or "").strip()
    unit_id = target_unit_id if target_unit_id is not None else getattr(announcement, "target_unit_id", None)

    query = User.query.filter(User.is_active.is_(True))
    if scope == "role" and role:
        query = query.filter(func.lower(func.trim(func.coalesce(User.role, ""))) == role.lower())
    elif scope == "unit" and unit_id:
        query = query.filter(User.organization_unit_id == int(unit_id))
    return query


def count_target_users(announcement: Announcement | None = None, **kwargs: Any) -> int:
    return int(target_user_query(announcement, **kwargs).count())


def summarize_announcement_reads(announcement: Announcement) -> dict[str, int]:
    total_reads = AnnouncementRead.query.filter_by(announcement_id=announcement.id).count()
    acknowledged = AnnouncementRead.query.filter(
        AnnouncementRead.announcement_id == announcement.id,
        AnnouncementRead.acknowledged_at.isnot(None),
    ).count()
    dismissed = AnnouncementRead.query.filter(
        AnnouncementRead.announcement_id == announcement.id,
        AnnouncementRead.dismissed_at.isnot(None),
        AnnouncementRead.acknowledged_at.is_(None),
    ).count()
    target_count = count_target_users(announcement)
    return {
        "target_count": target_count,
        "seen_count": int(total_reads),
        "acknowledged_count": int(acknowledged),
        "dismissed_count": int(dismissed),
        "pending_count": max(int(target_count) - int(acknowledged), 0),
    }


def _user_full_name(user: User) -> str:
    cached = (getattr(user, "full_name_cache", None) or "").strip()
    if cached:
        return cached
    ad = (getattr(user, "ad", None) or "").strip()
    soyad = (getattr(user, "soyad", None) or "").strip()
    combined = " ".join(part for part in (ad, soyad) if part).strip()
    return combined or (getattr(user, "email", None) or f"Kullanıcı #{getattr(user, 'id', '')}")


def _user_unit_name(user: User) -> str:
    direct = (getattr(user, "birim", None) or "").strip()
    if direct:
        return direct
    unit = getattr(user, "organization_unit", None)
    return (getattr(unit, "name", None) or "").strip()


def _read_status_for_record(record: AnnouncementRead | None) -> tuple[str, str, str, bool]:
    if not record:
        return "not_seen", "Henüz görmedi", "gray", True
    if record.acknowledged_at:
        return "acknowledged", "Okudu", "green", False
    if record.dismissed_at:
        return "dismissed", "Kapattı", "red", True
    if record.last_seen_at:
        return "seen", "Gördü", "amber", True
    return "not_seen", "Henüz görmedi", "gray", True


def list_announcement_report_rows(announcement: Announcement) -> list[dict[str, Any]]:
    """Hedef kullanıcıları okundu/geçmiş kayıtlarıyla birlikte döndürür."""

    users = target_user_query(announcement).order_by(User.id.asc()).all()
    read_records = {
        record.user_id: record
        for record in AnnouncementRead.query.filter_by(announcement_id=announcement.id).all()
    }
    rows: list[dict[str, Any]] = []
    for user in users:
        record = read_records.get(user.id)
        status_key, status_label, status_color, pending = _read_status_for_record(record)
        rows.append({
            "user_id": user.id,
            "full_name": _user_full_name(user),
            "sicil_no": getattr(user, "sicil_no", None) or "",
            "email": getattr(user, "email", None) or "",
            "role": getattr(user, "role", None) or getattr(user, "role_label", None) or "",
            "unit_name": _user_unit_name(user),
            "status_key": status_key,
            "status_label": status_label,
            "status_color": status_color,
            "is_pending": pending,
            "first_seen_at": getattr(record, "first_seen_at", None) if record else None,
            "last_seen_at": getattr(record, "last_seen_at", None) if record else None,
            "dismissed_at": getattr(record, "dismissed_at", None) if record else None,
            "acknowledged_at": getattr(record, "acknowledged_at", None) if record else None,
            "seen_count": int(getattr(record, "seen_count", 0) or 0) if record else 0,
            "ip_address": getattr(record, "ip_address", None) or "" if record else "",
            "user_agent": getattr(record, "user_agent", None) or "" if record else "",
        })
    return rows


def build_announcement_acceptance_summary(announcement: Announcement, *, rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    report_rows = rows if rows is not None else list_announcement_report_rows(announcement)
    target_count = len(report_rows)
    acknowledged_count = sum(1 for row in report_rows if row["status_key"] == "acknowledged")
    dismissed_count = sum(1 for row in report_rows if row["status_key"] == "dismissed")
    seen_only_count = sum(1 for row in report_rows if row["status_key"] == "seen")
    not_seen_count = sum(1 for row in report_rows if row["status_key"] == "not_seen")
    seen_total = target_count - not_seen_count
    pending_count = sum(1 for row in report_rows if row.get("is_pending"))
    acceptance_rate = round((acknowledged_count / target_count) * 100, 1) if target_count else 0
    seen_rate = round((seen_total / target_count) * 100, 1) if target_count else 0
    return {
        "target_count": target_count,
        "seen_count": seen_total,
        "acknowledged_count": acknowledged_count,
        "dismissed_count": dismissed_count,
        "seen_only_count": seen_only_count,
        "not_seen_count": not_seen_count,
        "pending_count": pending_count,
        "acceptance_rate": acceptance_rate,
        "seen_rate": seen_rate,
        "is_required": bool(announcement.is_required),
    }


def _format_csv_datetime(value: Any) -> str:
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def export_announcement_report_csv(announcement: Announcement) -> str:
    """Excel uyumlu UTF-8 BOM'lu okundu raporu CSV çıktısı üretir."""

    rows = list_announcement_report_rows(announcement)
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "Duyuru ID",
        "Duyuru Başlığı",
        "Kullanıcı ID",
        "Ad Soyad",
        "Sicil No",
        "E-posta",
        "Rol",
        "Birim",
        "Durum",
        "İlk Gösterim",
        "Son Gösterim",
        "Okuma Tarihi",
        "Kapatma Tarihi",
        "Gösterim Sayısı",
        "IP",
        "Tarayıcı",
    ])
    for row in rows:
        writer.writerow([
            announcement.id,
            announcement.title or "",
            row.get("user_id", ""),
            row.get("full_name", ""),
            row.get("sicil_no", ""),
            row.get("email", ""),
            row.get("role", ""),
            row.get("unit_name", ""),
            row.get("status_label", ""),
            _format_csv_datetime(row.get("first_seen_at")),
            _format_csv_datetime(row.get("last_seen_at")),
            _format_csv_datetime(row.get("acknowledged_at")),
            _format_csv_datetime(row.get("dismissed_at")),
            row.get("seen_count", 0),
            row.get("ip_address", ""),
            row.get("user_agent", ""),
        ])
    return output.getvalue()

def is_announcement_in_publish_window(announcement: Announcement, *, now: datetime | None = None) -> bool:
    moment = now or _now()
    if not announcement.is_active:
        return False
    if announcement.publish_start_at and announcement.publish_start_at > moment:
        return False
    if announcement.publish_end_at and announcement.publish_end_at < moment:
        return False
    return True


def is_user_targeted(announcement: Announcement, user: User) -> bool:
    scope = (announcement.target_scope or "all").strip().lower()
    if scope == "all":
        return True
    if scope == "role":
        expected = (announcement.target_role or "").strip().lower()
        actual = (getattr(user, "role", None) or "").strip().lower()
        return bool(expected and expected == actual)
    if scope == "unit":
        unit_id = getattr(user, "organization_unit_id", None)
        return bool(announcement.target_unit_id and unit_id and int(announcement.target_unit_id) == int(unit_id))
    return False


def get_or_create_read_record(announcement: Announcement, user: User) -> AnnouncementRead:
    record = AnnouncementRead.query.filter_by(announcement_id=announcement.id, user_id=user.id).first()
    if record:
        return record
    record = AnnouncementRead(announcement_id=announcement.id, user_id=user.id, seen_count=0)
    db.session.add(record)
    return record


def should_show_announcement(announcement: Announcement, user: User, read_record: AnnouncementRead | None, *, now: datetime | None = None) -> bool:
    moment = now or _now()
    if not is_announcement_in_publish_window(announcement, now=moment):
        return False
    if not is_user_targeted(announcement, user):
        return False

    if not read_record:
        return True

    # Zorunlu duyuru, kullanıcı "Okudum" demediyse tekrar gösterilir.
    if announcement.is_required and not read_record.acknowledged_at:
        return True

    rule = (announcement.show_rule or "once").strip().lower()
    if rule == "every_login":
        return True
    if rule == "once_per_day":
        last_seen = read_record.last_seen_at
        if not last_seen:
            return True
        return last_seen.date() < date.today()

    # once: okundu veya kapatıldı kaydı varsa tekrar gösterilmez.
    return not (read_record.acknowledged_at or read_record.dismissed_at or read_record.last_seen_at)


def find_pending_announcement_for_user(user: User) -> Announcement | None:
    candidates = (
        Announcement.query
        .filter(Announcement.is_active.is_(True))
        .order_by(Announcement.is_required.desc(), Announcement.publish_start_at.desc().nullslast(), Announcement.id.desc())
        .limit(25)
        .all()
    )
    moment = _now()
    for announcement in candidates:
        read_record = AnnouncementRead.query.filter_by(announcement_id=announcement.id, user_id=user.id).first()
        if should_show_announcement(announcement, user, read_record, now=moment):
            return announcement
    return None


def _request_ip(request_obj: Any) -> str:
    forwarded = (request_obj.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return (forwarded or request_obj.remote_addr or "")[:80]


def record_announcement_seen(announcement: Announcement, user: User, request_obj: Any) -> AnnouncementRead:
    record = get_or_create_read_record(announcement, user)
    moment = _now()
    if not record.first_seen_at:
        record.first_seen_at = moment
    record.last_seen_at = moment
    record.seen_count = int(record.seen_count or 0) + 1
    record.ip_address = _request_ip(request_obj)
    record.user_agent = (request_obj.headers.get("User-Agent") or "")[:2000]
    return record


def acknowledge_announcement(announcement: Announcement, user: User, request_obj: Any) -> AnnouncementRead:
    record = get_or_create_read_record(announcement, user)
    moment = _now()
    if not record.first_seen_at:
        record.first_seen_at = moment
    record.last_seen_at = moment
    record.acknowledged_at = moment
    record.dismissed_at = moment
    record.ip_address = _request_ip(request_obj)
    record.user_agent = (request_obj.headers.get("User-Agent") or "")[:2000]
    return record


def dismiss_announcement(announcement: Announcement, user: User, request_obj: Any) -> AnnouncementRead:
    if announcement.is_required:
        raise ValueError("Zorunlu duyuru kapatılamaz; okundu onayı verilmelidir.")
    record = get_or_create_read_record(announcement, user)
    moment = _now()
    if not record.first_seen_at:
        record.first_seen_at = moment
    record.last_seen_at = moment
    record.dismissed_at = moment
    record.ip_address = _request_ip(request_obj)
    record.user_agent = (request_obj.headers.get("User-Agent") or "")[:2000]
    return record


def serialize_runtime_announcement(announcement: Announcement) -> dict[str, Any]:
    media_payload = build_runtime_media_payload(announcement)
    return {
        "id": announcement.id,
        "title": announcement.title or "Duyuru",
        "body": announcement.body or "",
        "type": announcement.announcement_type or "info",
        "type_label": announcement.type_label,
        "is_required": bool(announcement.is_required),
        "button_text": announcement.button_text or "Okudum",
        "media_type": media_payload["media_type"],
        "media_label": media_payload["media_label"],
        "media_url": media_payload["media_url"],
        "media_embed_url": media_payload["media_embed_url"],
        "media_file_url": media_payload["media_file_url"],
        "media_kind": media_payload["media_kind"],
        "cover_image_path": media_payload["cover_image_path"],
        "cta_text": announcement.cta_text or "",
        "cta_url": announcement.cta_url or "",
    }


def commit_runtime_change() -> None:
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise
