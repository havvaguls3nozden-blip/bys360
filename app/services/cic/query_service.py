
"""BYS360 CIC facade slice.

This module is intentionally facade-only in P5.
The legacy implementation remains in app.services.corporate_information_center.
Routes, template names, endpoint contracts and public function names are not changed.
"""
from __future__ import annotations

from typing import Any

from app.services import corporate_information_center as _legacy

__all__ = [
    "_active_staff_users",
    "_cic_v40_active_staff_candidates",
    "_cic_v40_special_day_users",
    "_cic_v40_upcoming_users",
    "_users_by_ids",
    "list_users",
]

def _active_staff_users(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_active_staff_users``."""
    return _legacy._active_staff_users(*args, **kwargs)

def _cic_v40_active_staff_candidates(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_active_staff_candidates``."""
    return _legacy._cic_v40_active_staff_candidates(*args, **kwargs)

def _cic_v40_special_day_users(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_special_day_users``."""
    return _legacy._cic_v40_special_day_users(*args, **kwargs)

def _cic_v40_upcoming_users(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_upcoming_users``."""
    return _legacy._cic_v40_upcoming_users(*args, **kwargs)

def _users_by_ids(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_users_by_ids``."""
    return _legacy._users_by_ids(*args, **kwargs)

def list_users(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``list_users``."""
    return _legacy.list_users(*args, **kwargs)
