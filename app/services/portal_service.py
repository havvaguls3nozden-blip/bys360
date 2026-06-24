from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import (
    PortalActivityLog,
    PortalGroup,
    PortalGroupMember,
    PortalPost,
    PortalPostAudience,
    PortalPostComment,
    PortalPostReaction,
    PortalCommentMention,
    PortalProfile,
    PortalSavedPost,
    User,
)
from app.route_support import normalize_role_name, sanitize_free_text, user_has_any_role

PORTAL_ALL_ROLES = {
    "admin",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "koordinator",
    "birim_sorumlusu",
    "personel",
}

PORTAL_MANAGE_ROLES = {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"}
PORTAL_ANNOUNCEMENT_ROLES = PORTAL_MANAGE_ROLES | {"koordinator", "birim_sorumlusu"}

REACTION_OPTIONS = [
    {"key": "like", "label": "Beğendim", "icon": "fa-regular fa-thumbs-up"},
    {"key": "congrats", "label": "Tebrik ederim", "icon": "fa-solid fa-hands-clapping"},
    {"key": "appreciate", "label": "Takdir ettim", "icon": "fa-solid fa-award"},
    {"key": "informative", "label": "Bilgilendirici", "icon": "fa-solid fa-circle-info"},
    {"key": "support", "label": "Destekliyorum", "icon": "fa-solid fa-hand-holding-heart"},
    {"key": "sad", "label": "Üzüldüm", "icon": "fa-regular fa-face-frown"},
    {"key": "agree", "label": "Katılıyorum", "icon": "fa-regular fa-circle-check"},
]
REACTION_MAP = {item["key"]: item for item in REACTION_OPTIONS}

POST_TYPE_OPTIONS = [
    ("normal", "Normal Paylaşım"),
    ("corporate_announcement", "Kurumsal Duyuru"),
    ("event", "Etkinlik"),
    ("training", "Eğitim / Toplantı"),
    ("success", "Tebrik / Başarı"),
    ("thanks", "Teşekkür / Takdir"),
    ("best_practice", "İyi Uygulama"),
    ("daily_note", "Günlük Not"),
    ("commemoration", "Anma / Taziye / Geçmiş Olsun"),
    ("survey", "Anket Bağlantılı Paylaşım"),
    ("instagram", "Instagram"),
]
POST_TYPE_LABELS = dict(POST_TYPE_OPTIONS)

VISIBILITY_OPTIONS = [
    ("public", "Herkese Açık"),
    ("self", "Sadece Ben"),
    ("unit", "Kendi Birimim"),
    ("upper_unit", "Kendi Üst Birimim"),
    ("selected_users", "Belirli Kişiler"),
    ("group", "Belirli Grup"),
    ("role", "Belirli Rol"),
]
VISIBILITY_LABELS = dict(VISIBILITY_OPTIONS)


def display_user_name(user: Any) -> str:
    if not user:
        return "BYS360 Kullanıcısı"
    full_name = sanitize_free_text(getattr(user, "full_name", ""), limit=180)
    if full_name:
        return full_name
    first = sanitize_free_text(getattr(user, "ad", ""), limit=90)
    last = sanitize_free_text(getattr(user, "soyad", ""), limit=90)
    return (first + " " + last).strip() or sanitize_free_text(getattr(user, "email", ""), limit=180) or "BYS360 Kullanıcısı"


def user_unit_name(user: Any) -> str:
    return sanitize_free_text(getattr(user, "birim", ""), limit=180)


def user_upper_unit_name(user: Any) -> str:
    return sanitize_free_text(getattr(user, "ust_birim", ""), limit=180)


def can_manage_portal(user: Any) -> bool:
    return user_has_any_role(user, PORTAL_MANAGE_ROLES)


def can_publish_announcement(user: Any) -> bool:
    return user_has_any_role(user, PORTAL_ANNOUNCEMENT_ROLES)


def get_or_create_profile(user: Any) -> PortalProfile | None:
    if not user or not getattr(user, "id", None):
        return None
    profile = PortalProfile.query.filter_by(user_id=int(user.id)).first()
    if profile:
        return profile
    profile = PortalProfile(
        user_id=int(user.id),
        headline=sanitize_free_text(getattr(user, "unvan", ""), limit=180),
        about_text="",
        default_post_visibility="public",
    )
    db.session.add(profile)
    db.session.flush()
    return profile

# BYS360_PORTAL_PROFILE_WALL_V2_8_CAN_POST_TO_WALL
def can_user_post_to_wall(actor: Any, wall_owner: Any, profile: PortalProfile | None = None) -> bool:
    # Profil duvarına paylaşım bırakma iznini güvenli şekilde kontrol eder.
    if not actor or not getattr(actor, "is_authenticated", False):
        return False
    if not wall_owner or not getattr(wall_owner, "id", None):
        return False
    actor_id = int(getattr(actor, "id", 0) or 0)
    owner_id = int(getattr(wall_owner, "id", 0) or 0)
    if actor_id <= 0 or owner_id <= 0:
        return False
    if can_manage_portal(actor):
        return True
    if actor_id == owner_id:
        return True
    if profile is None:
        profile = PortalProfile.query.filter_by(user_id=owner_id).first()
    if profile is not None and getattr(profile, "is_wall_enabled", True) is False:
        return False
    # Kurumsal portal V2.8: varsayılan davranış, aktif kullanıcıların açık profil duvarına paylaşım bırakabilmesidir.
    return True

# BYS360_PORTAL_PROFILE_WALL_V2_9_WALL_PERMISSIONS
def can_user_post_to_wall(actor: Any, wall_owner: Any, profile: PortalProfile | None = None) -> bool:
    """Kullanıcının bir profil duvarına paylaşım bırakıp bırakamayacağını kontrol eder."""
    if not actor or not getattr(actor, "is_authenticated", False):
        return False
    if not wall_owner or not getattr(wall_owner, "id", None):
        return False
    actor_id = int(getattr(actor, "id", 0) or 0)
    owner_id = int(getattr(wall_owner, "id", 0) or 0)
    if actor_id <= 0 or owner_id <= 0:
        return False
    if can_manage_portal(actor):
        return True
    if actor_id == owner_id:
        return True
    if profile is None:
        profile = PortalProfile.query.filter_by(user_id=owner_id).first()
    if profile is not None and getattr(profile, "is_wall_enabled", True) is False:
        return False
    return True

# BYS360_PORTAL_PEOPLE_PREMIUM_V2_10_REMOVED_HELPER
def is_portal_post_removed(post: PortalPost) -> bool:
    status = (getattr(post, "status", "") or "").strip().lower()
    if status in {"deleted", "removed", "hidden", "archived"}:
        return True
    if getattr(post, "hidden_at", None):
        return True
    return False

def can_user_delete_post(actor: Any, post: PortalPost) -> bool:
    """Paylaşımı silme/yayından kaldırma yetkisini belirler."""
    if not actor or not getattr(actor, "is_authenticated", False) or not post:
        return False
    actor_id = int(getattr(actor, "id", 0) or 0)
    if actor_id <= 0:
        return False
    if can_manage_portal(actor):
        return True
    if getattr(post, "author_user_id", None) and int(post.author_user_id) == actor_id:
        return True
    if getattr(post, "wall_owner_user_id", None) and int(post.wall_owner_user_id) == actor_id:
        return True
    return False

def list_active_groups_for_user(user: Any, *, include_all_for_manager: bool = False) -> list[PortalGroup]:
    query = PortalGroup.query.filter_by(is_active=True)
    if include_all_for_manager and can_manage_portal(user):
        return query.order_by(PortalGroup.name.asc()).all()
    memberships = PortalGroupMember.query.filter_by(user_id=getattr(user, "id", 0), status="active").all()
    ids = [m.group_id for m in memberships]
    if not ids:
        return []
    return query.filter(PortalGroup.id.in_(ids)).order_by(PortalGroup.name.asc()).all()


def normalize_visibility(value: Any) -> str:
    normalized = str(value or "public").strip().lower()
    allowed = {key for key, _label in VISIBILITY_OPTIONS}
    return normalized if normalized in allowed else "public"


def normalize_post_type(value: Any, user: Any | None = None) -> str:
    normalized = str(value or "normal").strip().lower()
    allowed = set(POST_TYPE_LABELS)
    if normalized not in allowed:
        return "normal"
    if normalized == "corporate_announcement" and user is not None and not can_publish_announcement(user):
        return "normal"
    return normalized


def _audience_values(post: PortalPost, audience_type: str) -> set[str]:
    return {str(a.audience_value) for a in post.audiences.filter_by(audience_type=audience_type).all()}


def is_group_member(user: Any, group_id: int | None) -> bool:
    if not user or not group_id:
        return False
    return bool(
        PortalGroupMember.query.filter_by(
            group_id=group_id,
            user_id=getattr(user, "id", 0),
            status="active",
        ).first()
    )


def can_user_view_post(user: Any, post: PortalPost) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if post.status != "published" and not can_manage_portal(user):
        return False
    user_id = int(getattr(user, "id", 0) or 0)
    if post.author_user_id and int(post.author_user_id) == user_id:
        return True
    # BYS360_PORTAL_PROFILE_WALL_V2_9_VIEW_WALL_OWNER
    if getattr(post, "wall_owner_user_id", None) and int(post.wall_owner_user_id) == user_id:
        return True
    # BYS360_PORTAL_PROFILE_WALL_V2_8_WALL_OWNER_VIEW
    if getattr(post, "wall_owner_user_id", None) and int(post.wall_owner_user_id) == user_id:
        return True
    if can_manage_portal(user):
        return True
    scope = normalize_visibility(post.visibility_scope)
    if scope == "public":
        return True
    if scope == "self":
        return False
    if scope == "unit":
        target = post.target_unit_name or user_unit_name(post.author)
        return bool(target and target == user_unit_name(user))
    if scope == "upper_unit":
        target = post.target_upper_unit_name or user_upper_unit_name(post.author)
        return bool(target and target == user_upper_unit_name(user))
    if scope == "role":
        role = post.target_role_name or next(iter(_audience_values(post, "role")), "")
        return bool(role and normalize_role_name(getattr(user, "role", "")) == normalize_role_name(role))
    if scope == "group":
        group_ids = _audience_values(post, "group")
        if post.group_id:
            group_ids.add(str(post.group_id))
        return any(is_group_member(user, int(gid)) for gid in group_ids if str(gid).isdigit())
    if scope == "selected_users":
        return str(user_id) in _audience_values(post, "user")
    return False


def visible_posts_for_user(user: Any, *, limit: int = 50, author_id: int | None = None, group_id: int | None = None, wall_owner_id: int | None = None) -> list[PortalPost]:
    # BYS360_PORTAL_PEOPLE_PREMIUM_V2_10_VISIBLE_STATUS_FILTER
    query = PortalPost.query.filter(PortalPost.status == 'published').order_by(PortalPost.is_pinned.desc(), PortalPost.published_at.desc(), PortalPost.id.desc())
    if author_id is not None:
        query = query.filter_by(author_user_id=author_id)
    if group_id is not None:
        query = query.filter_by(group_id=group_id)
    # BYS360_PORTAL_PROFILE_WALL_V2_9_VISIBLE_WALL_FILTER
    if wall_owner_id is not None:
        query = query.filter(PortalPost.wall_owner_user_id == wall_owner_id)
    # BYS360_PORTAL_PROFILE_WALL_V2_8_WALL_FILTER
    if wall_owner_id is not None:
        query = query.filter(PortalPost.wall_owner_user_id == wall_owner_id)
    candidates = query.limit(max(limit * 4, 120)).all()
    visible: list[PortalPost] = []
    for post in candidates:
        if can_user_view_post(user, post):
            visible.append(post)
            if len(visible) >= limit:
                break
    return visible


def reaction_counts(post: PortalPost) -> dict[str, int]:
    rows = PortalPostReaction.query.filter_by(post_id=post.id).all()
    return dict(Counter(row.reaction_type for row in rows))


def user_reaction_for_post(post: PortalPost, user: Any) -> str | None:
    if not user or not getattr(user, "id", None):
        return None
    row = PortalPostReaction.query.filter_by(post_id=post.id, user_id=int(user.id)).first()
    return row.reaction_type if row else None


def is_saved_by_user(post: PortalPost, user: Any) -> bool:
    if not user or not getattr(user, "id", None):
        return False
    return bool(PortalSavedPost.query.filter_by(post_id=post.id, user_id=int(user.id)).first())


# BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_SERVICE
def recent_comments(post: PortalPost, *, limit: int = 3) -> list[PortalPostComment]:
    return (
        PortalPostComment.query.filter_by(post_id=post.id, status="published", parent_comment_id=None)
        .order_by(PortalPostComment.created_at.desc(), PortalPostComment.id.desc())
        .limit(limit)
        .all()
    )


def recent_replies(comment: PortalPostComment, *, limit: int = 3) -> list[PortalPostComment]:
    return (
        PortalPostComment.query.filter_by(parent_comment_id=comment.id, status="published")
        .order_by(PortalPostComment.created_at.asc(), PortalPostComment.id.asc())
        .limit(limit)
        .all()
    )


def comment_mentions(comment: PortalPostComment) -> list[PortalCommentMention]:
    return (
        PortalCommentMention.query.filter_by(comment_id=comment.id)
        .order_by(PortalCommentMention.id.asc())
        .all()
    )


def enrich_posts(posts: list[PortalPost], user: Any) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for post in posts:
        # BYS360_PORTAL_PEOPLE_PREMIUM_V2_10_ENRICH_SKIP_REMOVED
        if is_portal_post_removed(post):
            continue
        counts = reaction_counts(post)
        total_reactions = sum(counts.values())
        comments_count = PortalPostComment.query.filter_by(post_id=post.id, status="published").count()
        wall_owner = getattr(post, "wall_owner", None)
        wall_owner_label = display_user_name(wall_owner) if wall_owner and getattr(post, "wall_owner_user_id", None) != getattr(post, "author_user_id", None) else ""
        wall_owner = getattr(post, "wall_owner", None)
        wall_owner_label = display_user_name(wall_owner) if wall_owner and getattr(post, "wall_owner_user_id", None) != getattr(post, "author_user_id", None) else ""
        enriched.append({
            "post": post,
            "wall_owner_label": wall_owner_label,
            "can_delete": can_user_delete_post(user, post),
            "wall_owner_label": wall_owner_label,
            "reaction_counts": counts,
            "total_reactions": total_reactions,
            "user_reaction": user_reaction_for_post(post, user),
            "comments_count": comments_count,
            "recent_comments": list(reversed(recent_comments(post, limit=3))),
            "recent_replies": {comment.id: recent_replies(comment, limit=3) for comment in recent_comments(post, limit=3)},
            "saved": is_saved_by_user(post, user),
            "can_manage": can_manage_portal(user) or (post.author_user_id and post.author_user_id == getattr(user, "id", None)),
            "post_type_label": POST_TYPE_LABELS.get(post.post_type, "Paylaşım"),
            "visibility_label": VISIBILITY_LABELS.get(post.visibility_scope, "Herkese Açık"),
        })
    return enriched


def add_audience_entries(post: PortalPost, *, selected_user_ids: list[int] | None = None, group_id: int | None = None, role_name: str | None = None) -> None:
    for uid in selected_user_ids or []:
        db.session.add(PortalPostAudience(post_id=post.id, audience_type="user", audience_value=str(uid)))
    if group_id:
        db.session.add(PortalPostAudience(post_id=post.id, audience_type="group", audience_value=str(group_id)))
    if role_name:
        db.session.add(PortalPostAudience(post_id=post.id, audience_type="role", audience_value=normalize_role_name(role_name)))


def toggle_reaction(post: PortalPost, user: Any, reaction_type: str) -> str:
    reaction_type = str(reaction_type or "like").strip().lower()
    if reaction_type not in REACTION_MAP:
        reaction_type = "like"
    row = PortalPostReaction.query.filter_by(post_id=post.id, user_id=int(user.id)).first()
    if row and row.reaction_type == reaction_type:
        db.session.delete(row)
        return "removed"
    if row:
        row.reaction_type = reaction_type
        return "updated"
    db.session.add(PortalPostReaction(post_id=post.id, user_id=int(user.id), reaction_type=reaction_type))
    return "added"


def toggle_save(post: PortalPost, user: Any) -> str:
    row = PortalSavedPost.query.filter_by(post_id=post.id, user_id=int(user.id)).first()
    if row:
        db.session.delete(row)
        return "removed"
    db.session.add(PortalSavedPost(post_id=post.id, user_id=int(user.id)))
    return "added"


def record_activity(actor: Any, entity_type: str, entity_id: int | None, action_type: str, summary: str = "") -> None:
    try:
        db.session.add(PortalActivityLog(
            actor_user_id=getattr(actor, "id", None),
            entity_type=entity_type,
            entity_id=entity_id,
            action_type=action_type,
            summary=sanitize_free_text(summary, limit=500),
        ))
    except SQLAlchemyError:
        db.session.rollback()

# BYS360_PORTAL_INSTAGRAM_FEED_V2_11_2_PORTAL_STORY_STORY_HELPER_BEGIN
def portal_instagram_story_items(user: Any, *, limit: int = 8) -> list[dict[str, Any]]:
    """Instagram story kartları geçici olarak portal ve ana sayfada gizlenir."""
    # BYS360_PORTAL_LIGHT_HOME_V2_8_81_HIDE_INSTAGRAM_STORIES_SERVICE
    return []
# BYS360_PORTAL_INSTAGRAM_FEED_V2_11_2_PORTAL_STORY_STORY_HELPER_END

def _bys360_home_normalize_text_v4(value: Any) -> str:
    """Ana sayfa filtreleri için Türkçe karakter duyarlı sadeleştirme."""
    text = str(value or "").strip().lower()
    table = str.maketrans({
        "ı": "i", "İ": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c",
        "Â": "a", "â": "a", "Î": "i", "î": "i", "Û": "u", "û": "u",
    })
    return text.translate(table)


def _is_press_news_home_excluded_v4(post: Any) -> bool:
    """Basında Tarihi Alan kaynaklı kayıtlar ana sayfa hero/vitrin/akışına karışmasın."""
    title = _bys360_home_normalize_text_v4(getattr(post, "title", ""))
    body = _bys360_home_normalize_text_v4(getattr(post, "body", ""))
    post_type = _bys360_home_normalize_text_v4(getattr(post, "post_type", ""))
    if title in {"basinda tarihi alan", "basinda tarihi alan haberi"}:
        return True
    if title.startswith("basinda tarihi alan"):
        return True
    if post_type == "corporate_announcement" and "baskanligimiz hakkinda basinda yer alan haber" in body:
        return True
    if "kaynak:" in body and "baglanti:" in body and "haber:" in body and "basinda" in body:
        return True
    return False

# Compatibility guard.
def portal_home_context(user: Any) -> dict[str, Any]:
    """Ana sayfa için Kurumsal Portal V2.5 bağlamı.

    Tasarım amaçlı zenginleştirme yapar; herhangi bir hata oluşursa anasayfayı düşürmez.
    """
    try:
        raw_posts = [p for p in visible_posts_for_user(user, limit=30) if getattr(p, "post_type", "") not in ("instagram", "instagram_story")]
        posts = [p for p in raw_posts if not _is_press_news_home_excluded_v4(p)][:10]
        # BYS360_PORTAL_LIGHT_HOME_V2_8_81_HIDE_INSTAGRAM_HOME_POSTS
        enriched = enrich_posts(posts, user)
        portal_home_instagram_stories = []
        # BYS360_PORTAL_INSTAGRAM_FEED_V2_11_2_PORTAL_STORY_HOME_STORIES

        visible_posts_count = len(enriched)
        reactions_count = sum(int(item.get("total_reactions") or 0) for item in enriched)
        comments_count = sum(int(item.get("comments_count") or 0) for item in enriched)
        media_count = 0
        featured: list[dict[str, Any]] = []

        for item in enriched:
            post = item.get("post")
            has_media = False
            try:
                attachments = post.attachments.all() if post is not None and hasattr(post, "attachments") else []
                for attachment in attachments:
                    mime_type = str(getattr(attachment, "mime_type", "") or "")
                    if mime_type.startswith("image/") or mime_type == "text/x-portal-video":
                        has_media = True
                        media_count += 1
            except Exception:
                has_media = False
            if getattr(post, "is_pinned", False) or getattr(post, "is_featured_home", False) or has_media:
                featured.append(item)

        if not featured:
            featured = enriched[:3]
        else:
            seen: set[int] = set()
            unique_featured: list[dict[str, Any]] = []
            for item in featured + enriched:
                post = item.get("post")
                post_id = int(getattr(post, "id", 0) or 0)
                if post_id and post_id not in seen:
                    seen.add(post_id)
                    unique_featured.append(item)
                if len(unique_featured) >= 3:
                    break
            featured = unique_featured

        groups_info: list[dict[str, Any]] = []
        try:
            groups = list_active_groups_for_user(user, include_all_for_manager=True)[:5]
            for group in groups:
                try:
                    member_count = PortalGroupMember.query.filter_by(group_id=group.id, status="active").count()
                except Exception:
                    member_count = 0
                visibility = VISIBILITY_LABELS.get(getattr(group, "visibility_scope", ""), "Grup")
                groups_info.append({
                    "id": group.id,
                    "name": sanitize_free_text(getattr(group, "name", "Grup"), limit=120),
                    "member_count": member_count,
                    "visibility_label": visibility,
                })
        except Exception:
            groups_info = []

        recent_interactions: list[dict[str, str]] = []
        for item in enriched[:4]:
            post = item.get("post")
            title = sanitize_free_text(getattr(post, "title", "") or getattr(post, "body", ""), limit=58) or "Portal paylaşımı"
            if int(item.get("comments_count") or 0):
                recent_interactions.append({"icon": "fa-comment-dots", "text": f"{title} paylaşımına yorum eklendi."})
            elif int(item.get("total_reactions") or 0):
                recent_interactions.append({"icon": "fa-heart", "text": f"{title} paylaşımı tepki aldı."})

        return {
            "portal_home_enabled": True,
            "portal_home_posts": enriched,
            "portal_home_featured": featured,
            "portal_home_groups": groups_info,
            "portal_home_instagram_stories": portal_home_instagram_stories,
            "portal_recent_interactions": recent_interactions,
            "portal_home_stats": {
                "visible_posts": visible_posts_count,
                "reactions": reactions_count,
                "comments": comments_count,
                "media": media_count,
            },
            "portal_reaction_options": REACTION_OPTIONS,
        }
    except Exception:
        return {
            "portal_home_enabled": True,
            "portal_home_posts": [],
            "portal_home_featured": [],
            "portal_home_groups": [],
            "portal_home_instagram_stories": [],
            "portal_recent_interactions": [],
            "portal_home_stats": {"visible_posts": 0, "reactions": 0, "comments": 0, "media": 0},
            "portal_reaction_options": REACTION_OPTIONS,
        }
# BYS360_HOME_FESTIVAL_PORTAL_V2_5_CONTEXT
