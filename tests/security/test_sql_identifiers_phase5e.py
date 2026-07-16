from __future__ import annotations

import pytest

from app.security.sql_identifiers import (
    quote_sql_identifier,
    validate_sql_identifier,
)


class _FakeIdentifierPreparer:
    def quote(self, value: str) -> str:
        return f'"{value}"'


class _FakeDialect:
    identifier_preparer = _FakeIdentifierPreparer()


def test_validate_sql_identifier_accepts_safe_closed_set() -> None:
    assert validate_sql_identifier(
        "event_key",
        allowed={"event_key", "score_value"},
    ) == "event_key"


def test_validate_sql_identifier_rejects_unsafe_values() -> None:
    invalid_values = (
        "",
        "event key",
        "event-key",
        "event_key; DROP TABLE users",
        'event_key"',
        "schema.event_key",
    )
    for value in invalid_values:
        with pytest.raises(
            ValueError,
            match="Unsafe SQL identifier",
        ):
            validate_sql_identifier(value)


def test_validate_sql_identifier_rejects_unknown_allowlist_value() -> None:
    with pytest.raises(
        ValueError,
        match="outside the allowed set",
    ):
        validate_sql_identifier(
            "other_column",
            allowed={"event_key"},
        )


def test_quote_sql_identifier_uses_active_dialect() -> None:
    assert quote_sql_identifier(
        "performance_scoring_history",
        dialect=_FakeDialect(),
        allowed={"performance_scoring_history"},
    ) == '"performance_scoring_history"'
