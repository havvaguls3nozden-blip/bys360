from __future__ import annotations

import app.services.settings.validation_defaults as validation


def test_clean_text_and_input_type_fallbacks() -> None:
    assert validation._clean_text(
        None,
        "fallback",
    ) == "fallback"

    assert validation._clean_text(
        "   ",
        "fallback",
    ) == "fallback"

    assert validation._clean_text(
        " value ",
        "fallback",
    ) == "value"

    assert validation._clean_text(
        0,
        "fallback",
    ) == "0"

    assert validation._input_type_for(
        "string",
        "email",
    ) == "email"

    assert validation._input_type_for(
        "bool",
    ) == "bool"

    assert validation._input_type_for(
        "int",
    ) == "number"

    assert validation._input_type_for(
        "string",
    ) == "text"


def test_normalize_system_definitions_cover_all_default_types() -> None:
    bool_source = {
        "setting_key": " enabled ",
        "value_type": "bool",
    }

    bool_item = (
        validation.normalize_system_setting_definition(
            bool_source
        )
    )

    assert bool_item == {
        "setting_key": "enabled",
        "value_type": "bool",
        "group_key": "general",
        "group_label": "general",
        "group_description": "",
        "label": "enabled",
        "description": "",
        "input_type": "bool",
        "default": "false",
    }

    assert bool_source == {
        "setting_key": " enabled ",
        "value_type": "bool",
    }

    int_item = (
        validation.normalize_system_setting_definition(
            {
                "setting_key": "limit",
                "value_type": "int",
            }
        )
    )

    assert int_item["input_type"] == "number"
    assert int_item["default"] == "0"

    string_item = (
        validation.normalize_system_setting_definition(
            {
                "setting_key": "title",
            }
        )
    )

    assert string_item["value_type"] == "string"
    assert string_item["input_type"] == "text"
    assert string_item["default"] == ""

    invalid_item = (
        validation.normalize_system_setting_definition(
            {
                "setting_key": " name ",
                "group_key": " display ",
                "group_label": " Display ",
                "group_description": " Description ",
                "label": " Name ",
                "description": " Note ",
                "value_type": "float",
                "input_type": "textarea",
                "default": "kept",
                "extra": 7,
            }
        )
    )

    assert invalid_item == {
        "setting_key": "name",
        "group_key": "display",
        "group_label": "Display",
        "group_description": "Description",
        "label": "Name",
        "description": "Note",
        "value_type": "string",
        "input_type": "textarea",
        "default": "kept",
        "extra": 7,
    }


def test_normalize_module_definition_adds_module_fields() -> None:
    source = {
        "module_key": " performance ",
        "setting_key": " reminder_enabled ",
        "value_type": "bool",
        "module_label": "   ",
        "module_description": " Reminder module ",
    }

    result = (
        validation.normalize_module_setting_definition(
            source
        )
    )

    assert result["module_key"] == "performance"
    assert result["module_label"] == "performance"
    assert result["module_description"] == (
        "Reminder module"
    )
    assert result["setting_key"] == (
        "reminder_enabled"
    )
    assert result["default"] == "false"

    assert source["module_key"] == " performance "


def test_normalize_system_catalog_preserves_order_and_deduplicates() -> None:
    result = (
        validation.normalize_system_setting_definitions(
            [
                {
                    "setting_key": "",
                },
                {
                    "setting_key": " alpha ",
                    "default": "first",
                },
                {
                    "setting_key": "alpha",
                    "default": "duplicate",
                },
                {
                    "setting_key": "beta",
                    "value_type": "int",
                },
            ]
        )
    )

    assert [
        item["setting_key"]
        for item in result
    ] == [
        "alpha",
        "beta",
    ]

    assert result[0]["default"] == "first"
    assert result[1]["default"] == "0"


def test_normalize_module_catalog_rejects_incomplete_and_duplicate_pairs() -> None:
    result = (
        validation.normalize_module_setting_definitions(
            [
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
                    "default": "first",
                },
                {
                    "module_key": "performance",
                    "setting_key": "enabled",
                    "default": "duplicate",
                },
                {
                    "module_key": "portal",
                    "setting_key": "enabled",
                },
            ]
        )
    )

    assert [
        (
            item["module_key"],
            item["setting_key"],
        )
        for item in result
    ] == [
        (
            "performance",
            "enabled",
        ),
        (
            "portal",
            "enabled",
        ),
    ]

    assert result[0]["default"] == "first"
    assert result[1]["default"] == ""


def test_validate_catalog_contract_accepts_valid_items() -> None:
    system_items = [
        {
            "setting_key": "site_name",
            "group_key": "general",
            "group_label": "General",
            "label": "Site name",
            "value_type": "string",
            "input_type": "text",
            "default": "BYS360",
        },
        {
            "setting_key": "enabled",
            "group_key": "general",
            "group_label": "General",
            "label": "Enabled",
            "value_type": "bool",
            "input_type": "bool",
        },
    ]

    module_items = [
        {
            "module_key": "performance",
            "setting_key": "enabled",
            "module_label": "Performance",
            "label": "Enabled",
            "value_type": "bool",
            "input_type": "bool",
            "default": "true",
        },
        {
            "module_key": "portal",
            "setting_key": "title",
            "module_label": "Portal",
            "label": "Title",
            "value_type": "string",
            "input_type": "text",
        },
    ]

    result = (
        validation.validate_settings_catalog_contract(
            system_items,
            module_items,
        )
    )

    assert result == {
        "ok": True,
        "errors": [],
        "warnings": [],
        "system_total": 2,
        "module_total": 2,
        "system_default_total": 1,
        "module_default_total": 1,
    }


def test_validate_catalog_contract_reports_all_error_and_warning_paths() -> None:
    system_items = [
        {},
        {
            "setting_key": "duplicate",
            "group_key": "general",
            "group_label": "General",
            "label": "Duplicate",
            "value_type": "string",
            "input_type": "text",
        },
        {
            "setting_key": "duplicate",
            "group_key": "",
            "group_label": "",
            "label": "",
            "value_type": "float",
            "input_type": "slider",
        },
    ]

    module_items = [
        {
            "module_key": "",
            "setting_key": "item",
        },
        {
            "module_key": "performance",
            "setting_key": "",
        },
        {
            "module_key": "performance",
            "setting_key": "enabled",
            "module_label": "Performance",
            "label": "Enabled",
            "value_type": "bool",
            "input_type": "bool",
        },
        {
            "module_key": "performance",
            "setting_key": "enabled",
            "module_label": "",
            "label": "",
            "value_type": "float",
            "input_type": "slider",
        },
    ]

    result = (
        validation.validate_settings_catalog_contract(
            system_items,
            module_items,
        )
    )

    assert result["ok"] is False
    assert result["system_total"] == 3
    assert result["module_total"] == 4
    assert result["system_default_total"] == 0
    assert result["module_default_total"] == 0

    assert "system.setting_key bos" in result["errors"]
    assert (
        "system.duplicate | duplicate"
        in result["errors"]
    )
    assert (
        "system.duplicate.group_key bos"
        in result["errors"]
    )
    assert (
        "system.duplicate.group_label bos"
        in result["errors"]
    )
    assert (
        "system.duplicate.label bos"
        in result["errors"]
    )
    assert (
        "system.duplicate.value_type gecersiz: float"
        in result["errors"]
    )

    assert (
        result["errors"].count(
            "module.module_key/setting_key bos"
        )
        == 2
    )

    assert (
        "module.duplicate | performance.enabled"
        in result["errors"]
    )
    assert (
        "module.performance.enabled.module_label bos"
        in result["errors"]
    )
    assert (
        "module.performance.enabled.label bos"
        in result["errors"]
    )
    assert (
        "module.performance.enabled.value_type gecersiz: float"
        in result["errors"]
    )

    assert (
        "system.duplicate.input_type alisilmadik: slider"
        in result["warnings"]
    )
    assert (
        "module.performance.enabled.input_type alisilmadik: slider"
        in result["warnings"]
    )


def test_build_defaults_snapshot_handles_empty_invalid_and_grouped_items() -> None:
    empty = validation.build_settings_defaults_snapshot(
        [],
        [],
    )

    assert empty == {
        "system_defaults": {},
        "module_defaults": {},
        "stats": {
            "system_total": 0,
            "module_total": 0,
            "module_group_total": 0,
        },
    }

    result = validation.build_settings_defaults_snapshot(
        [
            {
                "setting_key": "",
                "default": "ignored",
            },
            {
                "setting_key": " alpha ",
                "default": 1,
            },
            {
                "setting_key": "alpha",
                "default": 2,
            },
        ],
        [
            {
                "module_key": "",
                "setting_key": "ignored",
                "default": 0,
            },
            {
                "module_key": "performance",
                "setting_key": "",
                "default": 0,
            },
            {
                "module_key": "performance",
                "setting_key": "enabled",
                "default": True,
            },
            {
                "module_key": "performance",
                "setting_key": "title",
            },
            {
                "module_key": "portal",
                "setting_key": "enabled",
                "default": False,
            },
        ],
    )

    assert result == {
        "system_defaults": {
            "alpha": 2,
        },
        "module_defaults": {
            "performance": {
                "enabled": True,
                "title": None,
            },
            "portal": {
                "enabled": False,
            },
        },
        "stats": {
            "system_total": 1,
            "module_total": 3,
            "module_group_total": 2,
        },
    }
