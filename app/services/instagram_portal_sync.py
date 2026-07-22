
"""BYS360 Portal Instagram media/story synchronisation.

This service is safe-by-default: it does nothing until the required environment
variables are present. It imports Instagram posts and active stories into the
existing PortalPost structure so the normal portal feed can render them without
new database tables.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, UTC
from typing import Any

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import PortalActivityLog, PortalPost, PortalPostAttachment, User
from app.route_support import sanitize_free_text

GRAPH_BASE = "https://graph.facebook.com"
MARKER_MIME = "text/x-instagram-external-id"
KIND_MIME = "text/x-instagram-kind"
MEDIA_URL_MIME = "text/x-instagram-media-url"
THUMBNAIL_URL_MIME = "text/x-instagram-thumbnail-url"
PERMALINK_MIME = "text/x-instagram-permalink"
ACCOUNT_MIME = "text/x-instagram-account"
MEDIA_TYPE_MIME = "text/x-instagram-media-type"
SYNC_VERSION = "BYS360_PORTAL_INSTAGRAM_FEED_V2_11_2_PORTAL_STORY"


def _env_bool(name: str, default: bool = False) -> bool:
    value = str(os.getenv(name, "")).strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on", "aktif", "evet"}


def _clean(value: Any, *, limit: int = 500) -> str:
    return sanitize_free_text(str(value or ""), limit=limit)


def _api_version() -> str:
    return _clean(os.getenv("BYS360_INSTAGRAM_API_VERSION") or "v25.0", limit=20) or "v25.0"


def _access_token() -> str:
    return _clean(os.getenv("BYS360_INSTAGRAM_ACCESS_TOKEN"), limit=1000)


def _parse_instagram_timestamp(value: str) -> datetime:
    raw = _clean(value, limit=80)
    if not raw:
        return utc_now()
    try:
        # Instagram timestamps are ISO-8601, usually ending with +0000 or Z.
        normalized = raw.replace("Z", "+00:00")
        if normalized.endswith("+0000"):
            normalized = normalized[:-5] + "+00:00"
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(UTC).replace(tzinfo=None)
        return parsed
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/instagram_portal_sync.py:66")
        return utc_now()


def _parse_accounts() -> list[dict[str, str]]:
    accounts: list[dict[str, str]] = []
    raw = _clean(os.getenv("BYS360_INSTAGRAM_ACCOUNTS"), limit=3000)
    for part in [p.strip() for p in raw.split(",") if p.strip()]:
        if ":" not in part:
            continue
        username, ig_user_id = [x.strip() for x in part.split(":", 1)]
        if username and ig_user_id:
            accounts.append({"username": username.lstrip("@"), "ig_user_id": ig_user_id})

    fallbacks = [
        ("tarihialanbaskanligi", os.getenv("BYS360_INSTAGRAM_TARIHIALAN_ID")),
        ("casamer_tarihialan", os.getenv("BYS360_INSTAGRAM_CASAMER_ID")),
    ]
    existing = {row["ig_user_id"] for row in accounts}
    for username, ig_user_id in fallbacks:
        ig_user_id = _clean(ig_user_id, limit=120)
        if ig_user_id and ig_user_id not in existing:
            accounts.append({"username": username, "ig_user_id": ig_user_id})
            existing.add(ig_user_id)
    return accounts


def _fetch_graph_json(path: str, *, fields: str, limit: int, access_token: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"fields": fields, "limit": int(limit), "access_token": access_token})
    url = f"{GRAPH_BASE}/{_api_version()}/{path.lstrip('/')}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "BYS360-Instagram-Sync/2.11.2"})
    with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310 - official Meta Graph API URL
        payload = response.read().decode("utf-8", errors="replace")
    return json.loads(payload or "{}")


def fetch_account_media(ig_user_id: str, *, limit: int, access_token: str) -> list[dict[str, Any]]:
    fields = "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username"
    payload = _fetch_graph_json(f"{ig_user_id}/media", fields=fields, limit=limit, access_token=access_token)
    rows = payload.get("data") if isinstance(payload, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def fetch_account_stories(ig_user_id: str, *, limit: int, access_token: str) -> list[dict[str, Any]]:
    fields = "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username"
    payload = _fetch_graph_json(f"{ig_user_id}/stories", fields=fields, limit=limit, access_token=access_token)
    rows = payload.get("data") if isinstance(payload, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def _find_author_user_id() -> int | None:
    raw_id = _clean(os.getenv("BYS360_INSTAGRAM_PORTAL_AUTHOR_USER_ID"), limit=30)
    if raw_id.isdigit():
        user = db.session.get(User, int(raw_id))
        if user:
            return int(user.id)
    email = _clean(os.getenv("BYS360_INSTAGRAM_PORTAL_AUTHOR_EMAIL"), limit=180)
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            return int(user.id)
    return None


def _already_imported(media_id: str, *, kind: str | None = None) -> bool:
    marker = PortalPostAttachment.query.filter_by(mime_type=MARKER_MIME, stored_path=str(media_id)).first()
    if not marker:
        return False
    if not kind:
        return True
    kind_marker = PortalPostAttachment.query.filter_by(post_id=marker.post_id, mime_type=KIND_MIME, stored_path=kind).first()
    return bool(kind_marker)


def _add_marker(post: PortalPost, *, mime_type: str, value: str, filename: str) -> None:
    if not value:
        return
    db.session.add(PortalPostAttachment(
        post_id=post.id,
        filename=_clean(filename, limit=255),
        stored_path=_clean(value, limit=700),
        mime_type=mime_type,
        size_bytes=0,
        uploaded_by_user_id=None,
    ))


def _profile_url(account_label: str) -> str:
    account = _clean(account_label, limit=120).lstrip("@")
    return f"https://www.instagram.com/{account}/" if account else "https://www.instagram.com/"


def import_item_to_portal(media: dict[str, Any], *, account_username: str, author_user_id: int | None, kind: str) -> bool:
    media_id = _clean(media.get("id"), limit=120)
    if not media_id or _already_imported(media_id, kind=kind):
        return False

    api_username = _clean(media.get("username"), limit=120) or account_username
    account_label = api_username.lstrip("@") or account_username
    media_type = _clean(media.get("media_type"), limit=40).upper() or "IMAGE"
    permalink = _clean(media.get("permalink"), limit=700) or _profile_url(account_label)
    media_url = _clean(media.get("media_url"), limit=700)
    thumbnail_url = _clean(media.get("thumbnail_url"), limit=700)
    caption = _clean(media.get("caption"), limit=3500)
    timestamp = _parse_instagram_timestamp(_clean(media.get("timestamp"), limit=80))

    if kind == "story":
        title = f"Instagram Story • @{account_label}"
        body = caption or f"@{account_label} Instagram hesabından güncel story paylaşıldı."
        post_type = "instagram_story"
    else:
        title = f"Instagram • @{account_label}"
        body = caption or f"@{account_label} Instagram hesabından yeni kurumsal paylaşım."
        post_type = "instagram"

    post = PortalPost(
        author_user_id=author_user_id,
        title=title,
        body=body,
        post_type=post_type,
        visibility_scope="public",
        status="published",
        comments_enabled=False,
        is_pinned=False,
        is_featured_home=_env_bool("BYS360_INSTAGRAM_FEATURE_HOME", True),
        published_at=timestamp,
    )
    db.session.add(post)
    db.session.flush()

    _add_marker(post, mime_type=MARKER_MIME, value=media_id, filename="instagram_external_id")
    _add_marker(post, mime_type=KIND_MIME, value=kind, filename="instagram_kind")
    _add_marker(post, mime_type=MEDIA_URL_MIME, value=media_url, filename="instagram_media_url")
    _add_marker(post, mime_type=THUMBNAIL_URL_MIME, value=thumbnail_url, filename="instagram_thumbnail_url")
    _add_marker(post, mime_type=PERMALINK_MIME, value=permalink, filename="instagram_permalink")
    _add_marker(post, mime_type=ACCOUNT_MIME, value=account_label, filename="instagram_account")
    _add_marker(post, mime_type=MEDIA_TYPE_MIME, value=media_type, filename="instagram_media_type")
    return True


def expire_old_story_posts() -> int:
    cutoff = utc_now() - timedelta(hours=int(os.getenv("BYS360_INSTAGRAM_STORY_TTL_HOURS") or 30))
    rows = (
        PortalPost.query.filter(PortalPost.post_type == "instagram_story")
        .filter(PortalPost.status == "published")
        .filter(PortalPost.published_at < cutoff)
        .limit(200)
        .all()
    )
    for post in rows:
        post.status = "archived"
        post.hidden_at = utc_now()
        post.hidden_reason = "Instagram story süresi dolduğu için otomatik arşivlendi."
    return len(rows)


def sync_instagram_to_portal(*, actor_user: Any | None = None, limit: int | None = None) -> dict[str, Any]:
    """Import configured Instagram media and stories into the BYS360 portal feed."""
    if not _env_bool("BYS360_INSTAGRAM_SYNC_ENABLED", False):
        return {"ok": True, "enabled": False, "created": 0, "stories": 0, "message": "Instagram akışı henüz aktif değil."}

    token = _access_token()
    accounts = _parse_accounts()
    if not token:
        return {"ok": False, "enabled": True, "created": 0, "stories": 0, "message": "Instagram access token tanımlı değil."}
    if not accounts:
        return {"ok": False, "enabled": True, "created": 0, "stories": 0, "message": "Instagram hesap ID bilgisi tanımlı değil."}

    per_account_limit = int(limit or os.getenv("BYS360_INSTAGRAM_SYNC_LIMIT") or 8)
    per_account_limit = max(1, min(per_account_limit, 25))
    story_limit = int(os.getenv("BYS360_INSTAGRAM_STORY_LIMIT") or per_account_limit)
    story_limit = max(1, min(story_limit, 25))
    sync_stories = _env_bool("BYS360_INSTAGRAM_STORIES_ENABLED", True)
    author_user_id = _find_author_user_id()

    created = 0
    stories_created = 0
    skipped = 0
    archived_stories = 0
    errors: list[str] = []

    try:
        archived_stories = expire_old_story_posts()
        if archived_stories:
            db.session.commit()
    except Exception:
        db.session.rollback()

    for account in accounts:
        username = account["username"]
        ig_user_id = account["ig_user_id"]
        try:
            rows = fetch_account_media(ig_user_id, limit=per_account_limit, access_token=token)
            for row in rows:
                try:
                    if import_item_to_portal(row, account_username=username, author_user_id=author_user_id, kind="media"):
                        created += 1
                    else:
                        skipped += 1
                except Exception as exc:  # keep one bad post from stopping all accounts
                    db.session.rollback()
                    errors.append(f"@{username}: medya aktarılamadı ({type(exc).__name__})")
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            errors.append(f"@{username}: Instagram gönderi verisi alınamadı ({type(exc).__name__})")

        if sync_stories:
            try:
                story_rows = fetch_account_stories(ig_user_id, limit=story_limit, access_token=token)
                for row in story_rows:
                    try:
                        if import_item_to_portal(row, account_username=username, author_user_id=author_user_id, kind="story"):
                            stories_created += 1
                        else:
                            skipped += 1
                    except Exception as exc:
                        db.session.rollback()
                        errors.append(f"@{username}: story aktarılamadı ({type(exc).__name__})")
                db.session.commit()
            except Exception as exc:
                db.session.rollback()
                errors.append(f"@{username}: Instagram story verisi alınamadı ({type(exc).__name__})")

    try:
        db.session.add(PortalActivityLog(
            actor_user_id=getattr(actor_user, "id", None),
            entity_type="instagram_sync",
            entity_id=None,
            action_type="sync",
            summary=f"Instagram portal senkronu: gönderi={created}, story={stories_created}, arşiv={archived_stories}, atlanan={skipped}, hata={len(errors)}",
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()

    return {
        "ok": not errors,
        "enabled": True,
        "created": created,
        "stories": stories_created,
        "archived_stories": archived_stories,
        "skipped": skipped,
        "errors": errors,
        "message": f"Instagram akışı güncellendi. Gönderi: {created}, story: {stories_created}, arşivlenen story: {archived_stories}, hata: {len(errors)}.",
    }
