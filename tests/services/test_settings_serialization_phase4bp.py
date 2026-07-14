from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import app.services.settings.serialization as serialization


def test_normalize_setting_and_menu_keys() -> None:
    assert serialization.normalize_setting_key(None) == ""
    assert serialization.normalize_setting_key("  portal_title  ") == (
        "portal_title"
    )
    assert serialization.normalize_setting_key(17) == "17"

    assert serialization.normalize_menu_key(None) == ""
    assert serialization.normalize_menu_key(
        "  Performance Center  "
    ) == "performance_center"
    assert serialization.normalize_menu_key("ADMIN MENU") == (
        "admin_menu"
    )


def test_to_bool_covers_boolean_none_known_and_unknown_values(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        serialization,
        "BOOLEAN_TRUE_VALUES",
        {"yes", "on"},
    )
    monkeypatch.setattr(
        serialization,
        "BOOLEAN_FALSE_VALUES",
        {"no", "off"},
    )

    assert serialization.to_bool(True) is True
    assert serialization.to_bool(False) is False

    assert serialization.to_bool(None) is False
    assert serialization.to_bool(None, default=True) is True

    assert serialization.to_bool(" YES ") is True
    assert serialization.to_bool(" off ") is False

    assert serialization.to_bool("unknown") is False
    assert serialization.to_bool(
        "unknown",
        default=True,
    ) is True


def test_mask_sensitive_value_covers_protected_heuristic_and_plain_keys(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        serialization,
        "PROTECTED_SETTING_KEYS",
        {"database_url"},
    )

    assert serialization.mask_sensitive_value(
        " database_url ",
        "postgresql://secret",
        mask="[MASKED]",
    ) == "[MASKED]"

    assert serialization.mask_sensitive_value(
        "database_url",
        "",
    ) == ""

    assert serialization.mask_sensitive_value(
        "database_url",
        None,
    ) is None

    assert serialization.mask_sensitive_value(
        "api_token",
        "token-value",
    ) == "********"

    assert serialization.mask_sensitive_value(
        "client_secret",
        "",
    ) == ""

    plain_value = object()

    assert serialization.mask_sensitive_value(
        "portal_title",
        plain_value,
    ) is plain_value


def test_json_safe_converts_dates_decimal_and_plain_values() -> None:
    assert serialization.json_safe(
        datetime(2026, 7, 14, 10, 30, 45)
    ) == "2026-07-14T10:30:45"

    assert serialization.json_safe(
        date(2026, 7, 14)
    ) == "2026-07-14"

    assert serialization.json_safe(
        Decimal("12.50")
    ) == 12.5

    plain = object()

    assert serialization.json_safe(plain) is plain


def test_json_safe_converts_nested_collection_types() -> None:
    value = {
        "when": date(2026, 7, 14),
        7: (
            Decimal("2.50"),
            {"alpha", "beta"},
        ),
        "items": [
            Decimal("1.25"),
            date(2026, 1, 2),
        ],
        "frozen": frozenset({1, 2}),
    }

    result = serialization.json_safe(value)

    assert set(result) == {
        "when",
        "7",
        "items",
        "frozen",
    }

    assert result["when"] == "2026-07-14"
    assert result["7"][0] == 2.5
    assert sorted(result["7"][1]) == [
        "alpha",
        "beta",
    ]
    assert result["items"] == [
        1.25,
        "2026-01-02",
    ]
    assert sorted(result["frozen"]) == [1, 2]


def test_dumps_json_is_sorted_json_safe_and_unicode_preserving() -> None:
    value = {
        "z": Decimal("1.5"),
        "a": "caf\u00e9",
    }

    assert serialization.dumps_json(value) == (
        '{"a": "caf\u00e9", "z": 1.5}'
    )


def test_loads_json_covers_defaults_identity_success_and_failure() -> None:
    sentinel = object()

    assert serialization.loads_json(
        None,
        default=sentinel,
    ) is sentinel

    assert serialization.loads_json(
        "",
        default=sentinel,
    ) is sentinel

    existing_dict = {
        "ready": True,
    }
    existing_list = [
        1,
        2,
    ]

    assert serialization.loads_json(
        existing_dict
    ) is existing_dict

    assert serialization.loads_json(
        existing_list
    ) is existing_list

    assert serialization.loads_json(
        '{"count": 3}'
    ) == {
        "count": 3,
    }

    assert serialization.loads_json(
        "[1, 2]"
    ) == [
        1,
        2,
    ]

    assert serialization.loads_json(
        "{broken",
        default=sentinel,
    ) is sentinel


def test_value_to_storage_covers_bool_int_failure_and_text(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        serialization,
        "BOOLEAN_TRUE_VALUES",
        {"yes"},
    )
    monkeypatch.setattr(
        serialization,
        "BOOLEAN_FALSE_VALUES",
        {"no"},
    )

    assert serialization.value_to_storage(
        "yes",
        "bool",
    ) == "true"

    assert serialization.value_to_storage(
        "no",
        "bool",
    ) == "false"

    assert serialization.value_to_storage(
        " 12 ",
        "int",
    ) == "12"

    assert serialization.value_to_storage(
        -4,
        "int",
    ) == "-4"

    assert serialization.value_to_storage(
        None,
        "int",
    ) == "0"

    assert serialization.value_to_storage(
        "not-an-int",
        "int",
    ) == "0"

    assert serialization.value_to_storage(
        "  report  ",
        "string",
    ) == "report"

    assert serialization.value_to_storage(
        None,
        "custom",
    ) == ""


def test_value_to_python_covers_bool_int_failure_and_text(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        serialization,
        "BOOLEAN_TRUE_VALUES",
        {"yes"},
    )
    monkeypatch.setattr(
        serialization,
        "BOOLEAN_FALSE_VALUES",
        {"no"},
    )

    assert serialization.value_to_python(
        " yes ",
        "bool",
    ) is True

    assert serialization.value_to_python(
        "no",
        "bool",
    ) is False

    assert serialization.value_to_python(
        " 15 ",
        "int",
    ) == 15

    assert serialization.value_to_python(
        None,
        "int",
    ) == 0

    assert serialization.value_to_python(
        "",
        "int",
    ) == 0

    assert serialization.value_to_python(
        "invalid",
        "int",
    ) == 0

    assert serialization.value_to_python(
        "  note  ",
        "string",
    ) == "note"

    assert serialization.value_to_python(
        None,
        "custom",
    ) == ""
