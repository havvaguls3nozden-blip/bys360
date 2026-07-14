from __future__ import annotations

from app.services.settings.value_codec import (
    normalize_bool,
    value_to_python,
    value_to_storage,
)


def test_normalize_bool_accepts_supported_values() -> None:
    values = [
        1,
        "1",
        " true ",
        "ON",
        "yes",
        "EVET",
        "AKTIF",
    ]

    assert all(normalize_bool(value) for value in values)


def test_normalize_bool_rejects_false_and_unknown_values() -> None:
    values = [
        None,
        0,
        False,
        "",
        "0",
        "false",
        "off",
        "hayir",
        "pasif",
        [],
    ]

    assert not any(normalize_bool(value) for value in values)


def test_value_to_storage_serializes_boolean_values() -> None:
    assert value_to_storage("yes", "bool") == "true"
    assert value_to_storage("off", "bool") == "false"
    assert value_to_storage(None, "bool") == "false"


def test_value_to_storage_serializes_integer_values() -> None:
    assert value_to_storage(" 12 ", "int") == "12"
    assert value_to_storage(-4, "int") == "-4"
    assert value_to_storage(None, "int") == "0"
    assert value_to_storage("", "int") == "0"
    assert value_to_storage("not-an-int", "int") == "0"


def test_value_to_storage_serializes_text_values() -> None:
    assert value_to_storage("  report  ", "string") == "report"
    assert value_to_storage(None, "string") == ""
    assert value_to_storage(17, "custom") == "17"


def test_value_to_python_decodes_boolean_and_integer_values() -> None:
    assert value_to_python(" TRUE ", "bool") is True
    assert value_to_python("off", "bool") is False
    assert value_to_python(" 15 ", "int") == 15
    assert value_to_python(None, "int") == 0
    assert value_to_python("", "int") == 0
    assert value_to_python("invalid", "int") == 0


def test_value_to_python_decodes_text_values() -> None:
    assert value_to_python("  note  ", "string") == "note"
    assert value_to_python(None, "string") == ""
    assert value_to_python("", "custom") == ""
