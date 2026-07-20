"""Access policy for the Corporate Information Center."""
from __future__ import annotations

from typing import Any

ADMIN_ROLES = frozenset(
    {
        "admin",
        "administrator",
        "super_admin",
        "system_admin",
        "sistem_yoneticisi",
    }
)


def can_manage(user: Any) -> bool:
    """Return whether an authenticated user may manage CIC settings."""
    if not getattr(user, "is_authenticated", False):
        return False
    role = str(getattr(user, "role", "") or "").lower()
    return role in ADMIN_ROLES
