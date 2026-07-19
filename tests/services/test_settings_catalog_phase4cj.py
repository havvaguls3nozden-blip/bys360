from __future__ import annotations

import logging
from pathlib import Path

import app.services.settings.catalog as catalog

CATALOG_PATH = Path(
    catalog.__file__
).resolve()

SOURCE_LINES = CATALOG_PATH.read_text(
    encoding="utf-8-sig",
    errors="strict",
).splitlines(
    keepends=True
)


def _find_unique_exact_line(
    expected: str,
) -> int:
    matches = [
        line_number
        for line_number, line
        in enumerate(
            SOURCE_LINES,
            start=1,
        )
        if line.rstrip(
            "\r\n"
        ) == expected
    ]

    assert len(matches) == 1, (
        expected,
        matches,
    )

    return matches[0]


def _find_unique_line_containing(
    expected: str,
) -> int:
    matches = [
        line_number
        for line_number, line
        in enumerate(
            SOURCE_LINES,
            start=1,
        )
        if expected in line
    ]

    assert len(matches) == 1, (
        expected,
        matches,
    )

    return matches[0]


def _execute_catalog_lines(
    start_line: int,
    end_line: int,
    namespace: dict,
) -> dict:
    block = "".join(
        SOURCE_LINES[
            start_line - 1:end_line
        ]
    )

    padded_source = (
        "\n" * (
            start_line - 1
        )
        + block
    )

    namespace.setdefault(
        "__name__",
        "phase4cj_catalog_probe",
    )

    namespace.setdefault(
        "__file__",
        str(CATALOG_PATH),
    )

    code = compile(
        padded_source,
        str(CATALOG_PATH),
        "exec",
    )

    exec(
        code,
        namespace,
    )

    return namespace


def _manual_fallback_range() -> tuple[int, int]:
    marker = _find_unique_exact_line(
        "# BYS360_SETTINGS_"
        "MANUAL_V1_CATALOG_BEGIN"
    )

    return (
        marker + 1,
        marker + 4,
    )


def _manual_merge_range() -> tuple[int, int]:
    start_line = _find_unique_exact_line(
        "_BYS360_EXISTING_PAIRS = {"
    )

    end_marker = _find_unique_exact_line(
        "# BYS360_SETTINGS_"
        "MANUAL_V1_CATALOG_END"
    )

    return (
        start_line,
        end_marker - 1,
    )


def _ay1_merge_range() -> tuple[int, int]:
    begin_marker = (
        _find_unique_exact_line(
            "# BYS360_AY1_AI_PERFORMANCE_"
            "SETTINGS_INTEGRATION_V1_BEGIN"
        )
    )

    existing_line = (
        _find_unique_line_containing(
            "_existing_ay1_defs ="
        )
    )

    end_marker = (
        _find_unique_exact_line(
            "# BYS360_AY1_AI_PERFORMANCE_"
            "SETTINGS_INTEGRATION_V1_END"
        )
    )

    assert (
        begin_marker
        < existing_line
        < end_marker
    )

    return (
        existing_line - 1,
        end_marker - 1,
    )


def test_manual_catalog_name_error_fallback_creates_empty_collection() -> None:
    start_line, end_line = (
        _manual_fallback_range()
    )

    result = _execute_catalog_lines(
        start_line,
        end_line,
        {},
    )

    assert (
        result[
            "MODULE_SETTING_DEFINITIONS"
        ]
        == []
    )


def test_manual_catalog_does_not_append_existing_pair() -> None:
    existing_definition = {
        "module_key": "phase4cj",
        "setting_key": "duplicate",
    }

    module_definitions = [
        dict(
            existing_definition
        ),
    ]

    namespace = {
        "MODULE_SETTING_DEFINITIONS": (
            module_definitions
        ),
        "_BYS360_MANUAL_MODULE_SETTING_DEFINITIONS": [
            dict(
                existing_definition
            ),
        ],
    }

    start_line, end_line = (
        _manual_merge_range()
    )

    result = _execute_catalog_lines(
        start_line,
        end_line,
        namespace,
    )

    assert (
        result[
            "MODULE_SETTING_DEFINITIONS"
        ]
        is module_definitions
    )

    assert module_definitions == [
        existing_definition,
    ]

    assert result[
        "_BYS360_EXISTING_PAIRS"
    ] == {
        (
            "phase4cj",
            "duplicate",
        ),
    }


def test_ay1_catalog_does_not_append_existing_pair() -> None:
    existing_definition = {
        "module_key": "ai_agent",
        "setting_key": "enabled",
    }

    module_definitions = [
        dict(
            existing_definition
        ),
    ]

    namespace = {
        "MODULE_SETTING_DEFINITIONS": (
            module_definitions
        ),
        "_BYS360_AY1_MODULE_SETTING_DEFINITIONS": [
            dict(
                existing_definition
            ),
        ],
    }

    start_line, end_line = (
        _ay1_merge_range()
    )

    result = _execute_catalog_lines(
        start_line,
        end_line,
        namespace,
    )

    assert (
        result[
            "MODULE_SETTING_DEFINITIONS"
        ]
        is module_definitions
    )

    assert module_definitions == [
        existing_definition,
    ]


def test_ay1_catalog_logs_unexpected_merge_error(
    caplog,
) -> None:
    class ExplodingDictionary(
        dict
    ):
        def get(
            self,
            *args,
            **kwargs,
        ):
            raise RuntimeError(
                "phase4cj probe error"
            )

    caplog.set_level(
        logging.ERROR
    )

    namespace = {
        "MODULE_SETTING_DEFINITIONS": [
            ExplodingDictionary(
                {
                    "module_key": "broken",
                    "setting_key": "broken",
                }
            ),
        ],
        "_BYS360_AY1_MODULE_SETTING_DEFINITIONS": [
            {
                "module_key": "ai_agent",
                "setting_key": "enabled",
            },
        ],
    }

    start_line, end_line = (
        _ay1_merge_range()
    )

    _execute_catalog_lines(
        start_line,
        end_line,
        namespace,
    )

    assert any(
        (
            "BYS360 kalite denetimi: "
            "sessiz except/pass yakalandi "
            "(app/services/settings/catalog.py)"
        )
        in message
        for message in caplog.messages
    )
