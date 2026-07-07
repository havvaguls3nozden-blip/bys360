"""User-related effective-menu helper functions."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

RollbackHook = Callable[[], None]

from app.services.settings.effective_menu_parts.bys360_context import (
    _bys360_admin_period_reminder_is_admin_v1,
    _bys360_admin_period_reminder_norm_v1,
    _bys360_apply_general_category_visibility_fix_v1,
    _bys360_apply_performance_main_switch,
    _bys360_apply_performance_shortcut_gate_v4,
    _bys360_exec_item_matches,
    _bys360_exec_norm,
    _bys360_force_home_menu_visible_v1,
    _bys360_general_category_bool_v1,
    _bys360_general_category_state_v1,
    _bys360_is_exec_summary_menu_key,
    _bys360_perf_rm_v8_apply_aliases,
    _bys360_perf_rm_v8_apply_main_gate,
    _bys360_perf_rm_v8_norm_role,
    _bys360_perf_rm_v8_state_for_keys,
    _bys360_performance_role_state,
    _bys360_person_matrix_can_open_v1,
    _bys360_person_matrix_user_is_admin_v1,
    _bys360_portal_role_matrix_v2_12_apply,
    _bys360_press_news_role,
    _bys360_restore_general_section_v4,
    _get_unit_name_for_authority,
    _load_role_matrix_state,
    _load_unit_profile_state,
    _load_user_override_state,
    _rollback,
    _row_map_by_key,
    _safe_query_all,
    normalize_role_name,
)


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
