from __future__ import annotations

from app.services.settings.effective_menu_parts.public_build_context import (
    apply_admin_period_reminder_public_build_wrapper,
)

ADMIN_VISIBILITY_KEYS = {
    "performance_period_management_center",
    "performance_evaluator_reminder_center",
    "performance_evaluation_live_tracking",
    "performance_module",
    "performance_management",
    "performans_yonetimi",
}


def test_public_build_wrapper_enables_admin_period_reminder_visibility() -> None:
    user = object()
    calls: dict[str, object] = {}

    def previous_build_menu_visibility_map(
        candidate,
        *args,
        **kwargs,
    ):
        calls["previous_user"] = candidate
        calls["args"] = args
        calls["kwargs"] = kwargs
        return None

    def is_admin(candidate) -> bool:
        calls["admin_user"] = candidate
        return True

    build_menu_visibility_map = (
        apply_admin_period_reminder_public_build_wrapper(
            previous_build_menu_visibility_map,
            is_admin,
        )
    )

    result = build_menu_visibility_map(
        user,
        "compact",
        source="unit-test",
    )

    assert calls == {
        "previous_user": user,
        "args": ("compact",),
        "kwargs": {
            "source": "unit-test",
        },
        "admin_user": user,
    }

    assert result == {
        key: True
        for key in ADMIN_VISIBILITY_KEYS
    }


def test_public_build_wrapper_preserves_non_admin_visibility() -> None:
    user = object()

    original_visibility = {
        "existing_menu": True,
        "another_menu": False,
    }

    calls: dict[str, object] = {}

    def previous_build_menu_visibility_map(
        candidate,
        *args,
        **kwargs,
    ):
        calls["previous_user"] = candidate
        calls["args"] = args
        calls["kwargs"] = kwargs
        return original_visibility

    def is_admin(candidate) -> bool:
        calls["admin_user"] = candidate
        return False

    build_menu_visibility_map = (
        apply_admin_period_reminder_public_build_wrapper(
            previous_build_menu_visibility_map,
            is_admin,
        )
    )

    result = build_menu_visibility_map(
        user,
        42,
        mode="readonly",
    )

    assert calls == {
        "previous_user": user,
        "args": (42,),
        "kwargs": {
            "mode": "readonly",
        },
        "admin_user": user,
    }

    assert result == original_visibility
    assert result is not original_visibility

    for key in ADMIN_VISIBILITY_KEYS:
        assert key not in result
