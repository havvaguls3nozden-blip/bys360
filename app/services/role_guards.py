"""BYS360 ortak rol ve görünürlük yardımcıları.

SP route dosyalarındaki _role_name / _is_top_or_manager tekrarını tek merkezde
azaltmak için oluşturuldu. Bu dosya veri erişim yetkisini tek başına vermez;
menü/route görünürlüğü için ortak karar yardımcısıdır.
"""
from __future__ import annotations

from typing import Any

# BYS360_CLAUDE_10E_ROLE_GUARDS

TOP_OR_MANAGER_TOKENS = (
    "admin",
    "sistem",
    "başkan",
    "baskan",
    "yardımc",
    "yardimc",
    "grup",
    "koordinat",
    "performans",
    "ik",
    "mali",
    "yönetici",
    "yonetici",
)


def role_name(user: Any) -> str:
    role = getattr(user, "role", None) or getattr(user, "role_name", None) or ""
    return str(role).strip().lower()


def is_authenticated_user(user: Any) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def is_top_or_manager(user: Any) -> bool:
    if not is_authenticated_user(user):
        return False
    role = role_name(user)
    return (
        any(token in role for token in TOP_OR_MANAGER_TOKENS)
        or bool(getattr(user, "is_admin", False))
        or bool(getattr(user, "is_superuser", False))
    )


def can_view_strategic_performance(user: Any) -> bool:
    return is_top_or_manager(user)


def can_manage_strategic_targets(user: Any) -> bool:
    return is_top_or_manager(user)
