from __future__ import annotations

from collections.abc import Iterable
from types import SimpleNamespace
from typing import Any, cast

from app.services.settings.contracts import MenuPermissionRule
from app.services.settings.menu_rules import (
    _safe_int,
    build_menu_rule,
    enabled_menu_keys,
    filter_live_menu_keys,
    filter_live_menu_rows,
    normalize_menu_rules,
)


class _BrokenInteger:
    def __int__(self) -> int:
        raise ValueError("invalid integer")


def test_build_menu_rule_returns_existing_rule_identity() -> None:
    existing = MenuPermissionRule(
        menu_key="portal",
        enabled=False,
        scope="role",
        target_id=7,
        reason="existing",
    )

    assert build_menu_rule(existing) is existing


def test_build_menu_rule_normalizes_mapping_fields() -> None:
    rule = build_menu_rule(
        {
            "key": "  Performance Center  ",
            "enabled": "off",
            "scope": "  role  ",
            "target_id": "42",
            "reason": "  organization rule  ",
        }
    )

    assert rule == MenuPermissionRule(
        menu_key="performance_center",
        enabled=False,
        scope="role",
        target_id=42,
        reason="organization rule",
    )


def test_safe_int_handles_empty_numeric_and_invalid_values() -> None:
    assert _safe_int(None) is None
    assert _safe_int("") is None
    assert _safe_int("11") == 11
    assert _safe_int(_BrokenInteger()) is None


def test_build_menu_rule_uses_safe_defaults() -> None:
    rule = build_menu_rule(
        {
            "menu_key": "  Internal Portal ",
            "enabled": None,
            "scope": "   ",
            "target_id": _BrokenInteger(),
            "reason": None,
        }
    )

    assert rule.menu_key == "internal_portal"
    assert rule.enabled is True
    assert rule.scope == "user"
    assert rule.target_id is None
    assert rule.reason == ""


def test_normalize_menu_rules_skips_empty_deduplicates_and_sorts() -> None:
    rules = normalize_menu_rules(
        [
            {
                "key": "B Menu",
                "scope": "role",
                "target_id": 2,
                "enabled": True,
                "reason": "first",
            },
            {
                "key": "A Menu",
                "scope": "user",
                "enabled": True,
            },
            {
                "key": " ",
                "scope": "user",
                "enabled": True,
            },
            {
                "key": "B Menu",
                "scope": "role",
                "target_id": 2,
                "enabled": False,
                "reason": "last",
            },
        ]
    )

    assert [
        (rule.scope, rule.menu_key, rule.target_id)
        for rule in rules
    ] == [
        ("role", "b_menu", 2),
        ("user", "a_menu", None),
    ]

    assert rules[0].enabled is False
    assert rules[0].reason == "last"


def test_enabled_menu_keys_returns_only_enabled_normalized_rules() -> None:
    keys = enabled_menu_keys(
        [
            {
                "key": "Portal",
                "enabled": "yes",
            },
            {
                "key": "Strategy",
                "enabled": "no",
            },
            MenuPermissionRule(
                menu_key="personnel",
                enabled=True,
            ),
        ]
    )

    assert keys == ["personnel", "portal"]


def test_filter_live_menu_keys_handles_empty_and_removed_values() -> None:
    assert filter_live_menu_keys(cast(Iterable[Any], None)) == []
    assert filter_live_menu_keys(["  portal  "]) == ["portal"]

    result = filter_live_menu_keys(
        [
            None,
            "",
            "   ",
            " portal ",
            "strategy",
            "personnel",
            0,
        ],
        is_removed_checker=lambda key: key == "strategy",
    )

    assert result == [
        "portal",
        "personnel",
    ]


def test_filter_live_menu_rows_supports_passthrough_and_filtering() -> None:
    portal = SimpleNamespace(menu_key="portal")
    removed = SimpleNamespace(menu_key="education")
    no_key = SimpleNamespace()

    assert filter_live_menu_rows(cast(Iterable[Any], None)) == []

    original = [portal, removed, no_key]

    passthrough = filter_live_menu_rows(original)

    assert passthrough == original
    assert passthrough is not original

    filtered = filter_live_menu_rows(
        original,
        is_removed_checker=lambda key: key in {
            "education",
            "",
        },
    )

    assert filtered == [portal]
