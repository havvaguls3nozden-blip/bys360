from __future__ import annotations

from unittest.mock import patch

import app.services.settings.effective_menu as target


def test_log_warning_returns_when_logger_is_missing() -> None:
    target._log_warning(
        None,
        "unused warning %s",
        "value",
    )


def test_log_warning_delegates_message_and_arguments() -> None:
    calls: list[
        tuple[str, tuple[object, ...]]
    ] = []

    class RecordingLogger:
        def warning(
            self,
            message: str,
            *args: object,
        ) -> None:
            calls.append(
                (
                    message,
                    args,
                )
            )

    target._log_warning(
        RecordingLogger(),
        "menu warning %s %s",
        "alpha",
        42,
    )

    assert calls == [
        (
            "menu warning %s %s",
            (
                "alpha",
                42,
            ),
        ),
    ]


def test_log_warning_records_failure_when_custom_logger_raises() -> None:
    logger_names: list[str | None] = []
    recovery_messages: list[str] = []

    class ExplodingLogger:
        def warning(
            self,
            message: str,
            *args: object,
        ) -> None:
            raise RuntimeError(
                "phase4cq logger failure"
            )

    class RecoveryLogger:
        def exception(
            self,
            message: str,
            *args: object,
            **kwargs: object,
        ) -> None:
            recovery_messages.append(
                message
            )

    def fake_get_logger(
        name: str | None = None,
    ) -> RecoveryLogger:
        logger_names.append(name)
        return RecoveryLogger()

    with patch(
        "logging.getLogger",
        side_effect=fake_get_logger,
    ):
        target._log_warning(
            ExplodingLogger(),
            "broken warning",
        )

    assert logger_names == [
        target.__name__,
    ]

    assert recovery_messages == [
        (
            "BYS360_MAINTENANCE_V13_P1_"
            "SILENT_EXCEPTION_LOGGER | "
            "app/services/settings/"
            "effective_menu.py"
        ),
    ]


def test_active_menu_items_filters_removed_menu_keys(
    monkeypatch,
) -> None:
    items = [
        {
            "key": "active_a",
            "label": "Active A",
        },
        {
            "key": "removed_menu",
            "label": "Removed",
        },
        {
            "key": "active_b",
            "label": "Active B",
        },
    ]

    checked_keys: list[
        object,
    ] = []

    def fake_flatten_menu_definitions():
        return items

    def fake_is_removed_menu_key(
        key,
    ) -> bool:
        checked_keys.append(key)
        return key == "removed_menu"

    monkeypatch.setattr(
        target,
        "flatten_menu_definitions",
        fake_flatten_menu_definitions,
    )

    monkeypatch.setattr(
        target,
        "is_removed_menu_key",
        fake_is_removed_menu_key,
    )

    result = target._active_menu_items()

    assert result == [
        items[0],
        items[2],
    ]

    assert result[0] is items[0]
    assert result[1] is items[2]

    assert checked_keys == [
        "active_a",
        "removed_menu",
        "active_b",
    ]


def test_truthy_bool_handles_boolean_and_text_values() -> None:
    assert target._truthy_bool(
        True
    ) is True

    assert target._truthy_bool(
        False
    ) is False

    for value in (
        "1",
        " TRUE ",
        "evet",
        "yes",
        "on",
        "aktif",
        "visible",
        "a\u00e7\u0131k",
        "acik",
    ):
        assert target._truthy_bool(
            value
        ) is True

    for falsy_value in (
        None,
        0,
        "",
        "0",
        "false",
        "hayir",
        "off",
    ):
        assert target._truthy_bool(
            falsy_value
        ) is False
