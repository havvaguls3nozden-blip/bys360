"""Public build_menu_visibility_map wrapper helpers for effective_menu."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def apply_admin_period_reminder_public_build_wrapper(
    previous_build_menu_visibility_map: Callable[..., dict[str, Any]],
    admin_period_reminder_is_admin: Callable[[Any], bool],
) -> Callable[..., dict[str, Any]]:
    """Return public build_menu_visibility_map wrapper with admin reminder visibility."""
    def build_menu_visibility_map(user, *args, **kwargs):
        visibility = dict(previous_build_menu_visibility_map(user, *args, **kwargs) or {})
        if admin_period_reminder_is_admin(user):
            for key in (
                "performance_period_management_center",
                "performance_evaluator_reminder_center",
                "performance_evaluation_live_tracking",
            ):
                visibility[key] = True
            for parent in ("performance_module", "performance_management", "performans_yonetimi"):
                visibility[parent] = True
        return visibility

    return build_menu_visibility_map


__all__ = [
    "apply_admin_period_reminder_public_build_wrapper",
]
