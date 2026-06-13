
"""BYS360 CIC facade slice.

This module is intentionally facade-only in P5.
The legacy implementation remains in app.services.corporate_information_center.
Routes, template names, endpoint contracts and public function names are not changed.
"""
from __future__ import annotations

from typing import Any

from app.services import corporate_information_center as _legacy

__all__ = [
    "_cic_v40_anniversary_users",
    "_cic_v40_birthday_users",
    "_cic_v40_run_weekend_celebrations",
    "_cic_v40_service_year",
    "celebration_context",
    "ensure_celebration_schema",
    "import_celebration_dates_from_excel",
    "save_celebration_settings",
]

def _cic_v40_anniversary_users(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_anniversary_users``."""
    return _legacy._cic_v40_anniversary_users(*args, **kwargs)

def _cic_v40_birthday_users(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_birthday_users``."""
    return _legacy._cic_v40_birthday_users(*args, **kwargs)

def _cic_v40_run_weekend_celebrations(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_run_weekend_celebrations``."""
    return _legacy._cic_v40_run_weekend_celebrations(*args, **kwargs)

def _cic_v40_service_year(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_service_year``."""
    return _legacy._cic_v40_service_year(*args, **kwargs)

def celebration_context(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``celebration_context``."""
    return _legacy.celebration_context(*args, **kwargs)

def ensure_celebration_schema(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``ensure_celebration_schema``."""
    return _legacy.ensure_celebration_schema(*args, **kwargs)

def import_celebration_dates_from_excel(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``import_celebration_dates_from_excel``."""
    return _legacy.import_celebration_dates_from_excel(*args, **kwargs)

def save_celebration_settings(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``save_celebration_settings``."""
    return _legacy.save_celebration_settings(*args, **kwargs)
