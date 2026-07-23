"""User-related effective-menu helper functions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.services.settings.effective_menu_parts.bys360_context import (
    _rollback,
)

RollbackHook = Callable[[], None]


def _user_has_any_assigned_survey(user: Any, *, rollback: RollbackHook | None = None) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    try:
        from app.models import Survey
        from app.services.message_service import user_matches_assignment

        surveys = (
            Survey.query
            .filter(Survey.status == "published")
            .order_by(Survey.id.desc())
            .limit(10000)
            .all()
        )
        for survey in surveys:
            assignments = getattr(survey, "assignments", None)
            if assignments is None:
                continue
            try:
                rows = assignments.all()
            except Exception:
                logger = __import__("logging").getLogger(__name__)
                logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=249")
                rows = []
            if any(user_matches_assignment(row, user) for row in rows):
                return True
    except Exception:
        _rollback(rollback)
        return False
    return False


__all__ = [
    "_user_has_any_assigned_survey",
]
