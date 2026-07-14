from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import app.services.settings.snapshots as snapshots


def test_build_complete_visibility_map_handles_none_blank_and_membership() -> None:
    assert snapshots.build_complete_visibility_map(
        None,
        None,
    ) == {}

    result = snapshots.build_complete_visibility_map(
        [
            None,
            "",
            " dashboard ",
            "reports",
            "dashboard",
            "   ",
        ],
        [
            None,
            "",
            " dashboard ",
            "missing",
            "dashboard",
        ],
    )

    assert result == {
        "dashboard": True,
        "reports": False,
    }


def test_snapshot_system_rows_uses_rows_defaults_and_value_types() -> None:
    calls: list[tuple[Any, str]] = []

    def to_storage(
        value: Any,
        value_type: str,
    ) -> str:
        calls.append(
            (
                value,
                value_type,
            )
        )

        return f"{value_type}:{value!r}"

    assert snapshots.snapshot_system_rows(
        {},
        None,
        value_to_storage=to_storage,
    ) == {}

    rows = {
        "title": SimpleNamespace(
            value_text="stored",
        ),
        "zero": SimpleNamespace(
            value_text=0,
        ),
        "missing_attr": SimpleNamespace(),
    }

    definitions = [
        {
            "setting_key": "",
            "default": "ignored",
        },
        {
            "setting_key": " title ",
            "value_type": "string",
            "default": "fallback",
        },
        {
            "setting_key": "enabled",
            "value_type": "bool",
            "default": True,
        },
        {
            "setting_key": "zero",
            "value_type": "int",
            "default": 9,
        },
        {
            "setting_key": "missing_attr",
        },
    ]

    result = snapshots.snapshot_system_rows(
        rows,
        definitions,
        value_to_storage=to_storage,
    )

    assert result == {
        "title": "string:'stored'",
        "enabled": "bool:True",
        "zero": "int:0",
        "missing_attr": "string:None",
    }

    assert calls == [
        (
            "stored",
            "string",
        ),
        (
            True,
            "bool",
        ),
        (
            0,
            "int",
        ),
        (
            None,
            "string",
        ),
    ]


def test_snapshot_module_rows_handles_invalid_existing_and_default_rows() -> None:
    calls: list[tuple[Any, str]] = []

    def to_storage(
        value: Any,
        value_type: str,
    ) -> str:
        calls.append(
            (
                value,
                value_type,
            )
        )

        return f"{value_type}:{value!r}"

    assert snapshots.snapshot_module_rows(
        {},
        None,
        value_to_storage=to_storage,
    ) == {}

    rows = {
        (
            "performance",
            "enabled",
        ): SimpleNamespace(
            value_text="true",
        ),
        (
            "portal",
            "empty",
        ): SimpleNamespace(),
    }

    definitions = [
        {
            "module_key": "",
            "setting_key": "orphan",
        },
        {
            "module_key": "performance",
            "setting_key": "",
        },
        {
            "module_key": "performance",
            "setting_key": "enabled",
            "value_type": "bool",
            "default": "false",
        },
        {
            "module_key": "performance",
            "setting_key": "limit",
            "value_type": "int",
            "default": 5,
        },
        {
            "module_key": "portal",
            "setting_key": "empty",
        },
    ]

    result = snapshots.snapshot_module_rows(
        rows,
        definitions,
        value_to_storage=to_storage,
    )

    assert result == {
        "performance": {
            "enabled": "bool:'true'",
            "limit": "int:5",
        },
        "portal": {
            "empty": "string:None",
        },
    }

    assert calls == [
        (
            "true",
            "bool",
        ),
        (
            5,
            "int",
        ),
        (
            None,
            "string",
        ),
    ]


def test_snapshot_user_override_rows_skips_blank_and_overwrites_duplicates() -> None:
    assert snapshots.snapshot_user_override_rows(
        None
    ) == {}

    rows = [
        SimpleNamespace(),
        SimpleNamespace(
            menu_key="   ",
            is_visible=True,
        ),
        SimpleNamespace(
            menu_key=" dashboard ",
            is_visible=True,
        ),
        SimpleNamespace(
            menu_key="reports",
            is_visible=False,
        ),
        SimpleNamespace(
            menu_key="dashboard",
            is_visible=False,
        ),
    ]

    assert snapshots.snapshot_user_override_rows(
        rows
    ) == {
        "dashboard": False,
        "reports": False,
    }


def test_build_role_default_snapshot_rows_normalizes_roles_and_ratios() -> None:
    called_roles: list[str] = []

    def visible_keys(
        role_name: str,
    ) -> list[str] | None:
        called_roles.append(role_name)

        if role_name == "admin":
            return [
                "dashboard",
                "dashboard",
                "reports",
            ]

        return None

    assert snapshots.build_role_default_snapshot_rows(
        None,
        get_visible_keys=visible_keys,
        all_menu_count=0,
    ) == []

    result = snapshots.build_role_default_snapshot_rows(
        [
            None,
            "",
            " Admin ",
            "admin",
            " USER ",
        ],
        get_visible_keys=visible_keys,
        all_menu_count=4,
    )

    assert result == [
        {
            "role_name": "admin",
            "visible_count": 2,
            "total_count": 4,
            "coverage_ratio": 50.0,
        },
        {
            "role_name": "user",
            "visible_count": 0,
            "total_count": 4,
            "coverage_ratio": 0.0,
        },
    ]

    assert called_roles == [
        "admin",
        "user",
    ]


def test_build_unit_profile_snapshot_rows_groups_and_counts_visibility() -> None:
    assert snapshots.build_unit_profile_snapshot_rows(
        None,
        all_menu_count=0,
    ) == []

    rows = [
        SimpleNamespace(
            unit_name=" Unit A ",
            is_visible=True,
        ),
        SimpleNamespace(
            unit_name="Unit A",
            is_visible=False,
        ),
        SimpleNamespace(
            unit_name="Unit B",
            is_visible=True,
        ),
        SimpleNamespace(
            is_visible=True,
        ),
        SimpleNamespace(
            unit_name="Unit B",
        ),
    ]

    result = snapshots.build_unit_profile_snapshot_rows(
        rows,
        all_menu_count=4,
    )

    assert result == [
        {
            "unit_name": "Unit A",
            "configured_count": 2,
            "visible_count": 1,
            "coverage_ratio": 25.0,
        },
        {
            "unit_name": "Unit B",
            "configured_count": 2,
            "visible_count": 1,
            "coverage_ratio": 25.0,
        },
        {
            "unit_name": "",
            "configured_count": 1,
            "visible_count": 1,
            "coverage_ratio": 25.0,
        },
    ]


def test_build_setting_groups_preserves_group_order_and_current_values() -> None:
    conversion_calls: list[tuple[Any, str]] = []
    key_calls: list[str] = []

    def to_python(
        value: Any,
        value_type: str,
    ) -> dict[str, Any]:
        conversion_calls.append(
            (
                value,
                value_type,
            )
        )

        return {
            "value": value,
            "type": value_type,
        }

    def row_key(
        definition: dict[str, Any],
    ) -> str:
        key = str(
            definition.get("setting_key") or ""
        )

        key_calls.append(key)
        return key

    assert snapshots.build_setting_groups(
        None,
        {},
        value_to_python=to_python,
        group_key_field="group_key",
        group_label_field="group_label",
        group_description_field="group_description",
        row_key_builder=row_key,
        output_group_key="key",
        output_group_label="label",
        output_group_description="description",
    ) == []

    rows = {
        "site_name": SimpleNamespace(
            value_text="BYS360",
        ),
        "enabled": SimpleNamespace(
            value_text=False,
        ),
    }

    definitions = [
        {
            "group_key": "",
            "setting_key": "ignored",
            "default": "ignored",
        },
        {
            "group_key": " general ",
            "group_label": "General",
            "group_description": "General settings",
            "setting_key": "site_name",
            "value_type": "string",
            "default": "fallback",
        },
        {
            "group_key": "general",
            "group_label": "Ignored label",
            "group_description": "Ignored description",
            "setting_key": "limit",
            "value_type": "int",
            "default": 5,
        },
        {
            "group_key": "security",
            "group_label": "Security",
            "setting_key": "enabled",
            "value_type": "bool",
            "default": True,
        },
        {
            "group_key": "security",
            "group_label": "Security",
            "setting_key": "title",
            "default": "Secure",
        },
    ]

    result = snapshots.build_setting_groups(
        definitions,
        rows,
        value_to_python=to_python,
        group_key_field="group_key",
        group_label_field="group_label",
        group_description_field="group_description",
        row_key_builder=row_key,
        output_group_key="key",
        output_group_label="label",
        output_group_description="description",
    )

    assert len(result) == 2

    assert result[0]["key"] == "general"
    assert result[0]["label"] == "General"
    assert result[0]["description"] == (
        "General settings"
    )

    assert [
        row["setting_key"]
        for row in result[0]["rows"]
    ] == [
        "site_name",
        "limit",
    ]

    assert result[0]["rows"][0]["current_value"] == {
        "value": "BYS360",
        "type": "string",
    }

    assert result[0]["rows"][1]["current_value"] == {
        "value": 5,
        "type": "int",
    }

    assert result[1]["key"] == "security"
    assert result[1]["label"] == "Security"
    assert result[1]["description"] == ""

    assert [
        row["setting_key"]
        for row in result[1]["rows"]
    ] == [
        "enabled",
        "title",
    ]

    assert result[1]["rows"][0]["current_value"] == {
        "value": False,
        "type": "bool",
    }

    assert result[1]["rows"][1]["current_value"] == {
        "value": "Secure",
        "type": "string",
    }

    assert key_calls == [
        "site_name",
        "limit",
        "enabled",
        "title",
    ]

    assert conversion_calls == [
        (
            "BYS360",
            "string",
        ),
        (
            5,
            "int",
        ),
        (
            False,
            "bool",
        ),
        (
            "Secure",
            "string",
        ),
    ]
