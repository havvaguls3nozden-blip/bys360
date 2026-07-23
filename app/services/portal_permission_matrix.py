from __future__ import annotations

# BYS360_PORTAL_ROLE_MATRIX_DEEP_AUDIT_FIX_V2_12_3
import logging
from typing import Any

from app.models import RoleMenuDefault, UnitMenuProfile, UserMenuPermission

logger = logging.getLogger(__name__)

"""Kurumsal Portal rol matrisi ve etkileşim yetki çözümleyicisi.

V2.12.3 amacı:
- Portalda beğeni/yorum/kaydetme gibi temel etkileşimler yalnızca tek role değil,
  bütün canlı roller için rol matrisi üzerinden tutarlı çözülür.
- Kişi bazlı kapatma en güçlü kural olarak korunur.
- Birim profili eksik/yanlış false ise, rol matrisi açık olan temel etkileşimi
  yanlışlıkla kapatamaz. Böylece Grup Başkanı, Koordinatör, Personel vb.
  kullanıcılar paylaşımı görüp beğeni/yorum yapamama sorununa düşmez.
"""

try:
    from app.config import is_removed_menu_key
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6B guarded exception | file=app/services/portal_permission_matrix.py | line=21")
    def is_removed_menu_key(_key: str) -> bool:
        return False

PORTAL_MATRIX_KEYS = {
    "portal_feed",
    "portal_people",
    "portal_profiles",
    "portal_post_create",
    "portal_wall_post",
    "portal_post_interact",
    "portal_post_like",
    "portal_post_comment",
    "portal_comment_reply",
    "portal_comment_mention",
    "portal_post_report",
    "portal_post_delete",
    "portal_groups",
    "portal_group_create",
    "portal_moderation",
}

INTERACTION_KEYS = {
    "portal_post_interact",
    "portal_post_like",
    "portal_post_comment",
    "portal_comment_reply",
    "portal_comment_mention",
}

BASE_PORTAL_KEYS = {
    "portal_feed",
    "portal_people",
    "portal_profiles",
    "portal_post_interact",
    "portal_post_like",
    "portal_post_comment",
    "portal_comment_reply",
    "portal_comment_mention",
    "portal_post_report",
    "portal_groups",
}

PORTAL_DEFAULTS = {
    "admin": set(PORTAL_MATRIX_KEYS),
    "sistem_yoneticisi": set(PORTAL_MATRIX_KEYS),
    "sistem_yoneticisi_": set(PORTAL_MATRIX_KEYS),
    "baskan": set(PORTAL_MATRIX_KEYS),
    "baskan_yardimcisi": set(PORTAL_MATRIX_KEYS),
    "grup_baskani": set(PORTAL_MATRIX_KEYS),
    "mali_musavir": set(PORTAL_MATRIX_KEYS),
    "koordinator": set(PORTAL_MATRIX_KEYS) - {"portal_moderation"},
    "birim_sorumlusu": set(PORTAL_MATRIX_KEYS) - {"portal_moderation"},
    "ik": set(PORTAL_MATRIX_KEYS) - {"portal_moderation"},
    "insan_kaynaklari": set(PORTAL_MATRIX_KEYS) - {"portal_moderation"},
    "performans_yetkilisi": set(PORTAL_MATRIX_KEYS) - {"portal_moderation"},
    "portal_yoneticisi": set(PORTAL_MATRIX_KEYS),
    "personel": set(BASE_PORTAL_KEYS),
}

# Rol matrisi açık olan her canlı rolde temel portal etkileşimi önce role göre çözülür.
# Kişi bazlı kapatma bu kuralın üstündedir.
PORTAL_ROLE_FIRST_KEYS = set(INTERACTION_KEYS)


def _norm(value: Any) -> str:
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return str(value or "").strip().lower().translate(tr_map).replace(" ", "_").replace("-", "_")


def _query_bool(model, **filters) -> bool | None:
    try:
        row = model.query.filter_by(**filters).first()
        if row is None:
            return None
        return bool(getattr(row, "is_visible", False))
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/portal_permission_matrix.py | line=99")
        try:
            from app.extensions import db
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 V6B guarded exception | file=app/services/portal_permission_matrix.py | line=103")
            pass
        return None


def _role_default_allowed(role_name: str, key: str) -> bool:
    return key in PORTAL_DEFAULTS.get(role_name, set())


def _role_allows_from_db_or_default(role_name: str, key: str) -> bool | None:
    if not role_name:
        return None
    role_value = _query_bool(RoleMenuDefault, role_name=role_name, menu_key=key)
    if role_value is not None:
        return role_value
    if role_name in PORTAL_DEFAULTS:
        return _role_default_allowed(role_name, key)
    return None


def portal_permission_allowed(user: Any, key: str) -> bool:
    key = str(key or "").strip()
    if key not in PORTAL_MATRIX_KEYS or is_removed_menu_key(key):
        return False
    if not getattr(user, "is_authenticated", False):
        return False

    role_name = _norm(getattr(user, "role", ""))
    user_id = getattr(user, "id", None)

    # 1) Kişi bazlı izin en güçlü kuraldır. Kullanıcıya özel kapatma varsa
    # rol/birim izinleri bunu geçersiz kılamaz.
    if user_id:
        user_value = _query_bool(UserMenuPermission, user_id=user_id, menu_key=key)
        if user_value is not None:
            return user_value

    # 2) Beğeni/yorum/cevap/etiketleme gibi temel etkileşimlerde rol önceliklidir.
    # Birim profili false kalmışsa rolü açık olan kullanıcı yanlışlıkla engellenmez.
    if key in PORTAL_ROLE_FIRST_KEYS:
        role_allowed = _role_allows_from_db_or_default(role_name, key)
        if role_allowed is not None:
            return role_allowed

    # 3) Birim profili normal görünürlük ve özel kapsam kontrollerinde çalışır.
    unit_name = str(getattr(user, "birim", "") or "").strip()
    if unit_name:
        unit_value = _query_bool(UnitMenuProfile, unit_name=unit_name, menu_key=key)
        if unit_value is not None:
            return unit_value

    # 4) Rol matrisi.
    role_allowed = _role_allows_from_db_or_default(role_name, key)
    if role_allowed is not None:
        return role_allowed

    # 5) Bilinmeyen roller güvenli varsayılanla kapalıdır.
    return False


def require_portal_permission(user: Any, key: str):
    if portal_permission_allowed(user, key):
        return None
    from app.route_support import render_access_denied
    return render_access_denied()
