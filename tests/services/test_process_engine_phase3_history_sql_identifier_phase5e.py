from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.services.performance import (
    process_engine_phase3_history as service,
)


class _FakeIdentifierPreparer:
    def quote(self, value: str) -> str:
        return f'"{value}"'


class _FakeDialect:
    identifier_preparer = _FakeIdentifierPreparer()


class _FakeEngine:
    dialect = _FakeDialect()


@dataclass
class _FakeResult:
    scalar_value: object = None

    def scalar(self):
        return self.scalar_value


class _FakeSession:
    def __init__(self, scalar_values=None) -> None:
        self.scalar_values = list(scalar_values or [])
        self.calls: list[tuple[str, Any]] = []

    def execute(self, statement, params=None) -> _FakeResult:
        self.calls.append((str(statement), params))
        value = (
            self.scalar_values.pop(0)
            if self.scalar_values
            else None
        )
        return _FakeResult(value)


class _FakeDb:
    def __init__(self, scalar_values=None) -> None:
        self.engine = _FakeEngine()
        self.session = _FakeSession(scalar_values)


def _prepare(monkeypatch, *, scalar_values=None) -> _FakeDb:
    fake_db = _FakeDb(scalar_values)
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(
        service,
        "_table_exists",
        lambda table_name: True,
    )
    monkeypatch.setattr(
        service,
        "_columns",
        lambda table_name: {"event_key", "score_value"},
    )
    return fake_db


def test_insert_if_columns_quotes_binds_and_fails_closed(monkeypatch) -> None:
    fake_db = _prepare(
        monkeypatch,
        scalar_values=[False],
    )

    inserted = service._insert_if_columns(
        service.SCORING_HISTORY_TABLE,
        {
            "event_key": "evt-1",
            "score_value": 95,
            "ignored": "not-in-schema",
        },
        unique_key="event_key",
    )

    assert inserted is True
    assert len(fake_db.session.calls) == 2

    duplicate_sql, duplicate_params = fake_db.session.calls[0]
    assert duplicate_sql == (
        'SELECT 1 FROM "performance_scoring_history" '
        'WHERE "event_key" = :event_key LIMIT 1'
    )
    assert duplicate_params == {"event_key": "evt-1"}

    insert_sql, insert_params = fake_db.session.calls[1]
    assert insert_sql == (
        'INSERT INTO "performance_scoring_history" '
        '("event_key", "score_value") '
        'VALUES (:value_0, :value_1)'
    )
    assert insert_params == {
        "value_0": "evt-1",
        "value_1": 95,
    }

    existing_db = _prepare(
        monkeypatch,
        scalar_values=[True],
    )
    assert service._insert_if_columns(
        service.SCORING_HISTORY_TABLE,
        {"event_key": "evt-1", "score_value": 95},
        unique_key="event_key",
    ) is False
    assert len(existing_db.session.calls) == 1

    invalid_calls = (
        (
            "performance_scoring_history; DROP TABLE users",
            {"event_key": "evt-1"},
            "event_key",
        ),
        (
            "other_safe_table",
            {"event_key": "evt-1"},
            "event_key",
        ),
        (
            service.SCORING_HISTORY_TABLE,
            {"event_key": "evt-1"},
            "event_key; DROP TABLE users",
        ),
        (
            service.SCORING_HISTORY_TABLE,
            {"event_key": "evt-1"},
            "other_column",
        ),
    )

    rejection_db = _prepare(monkeypatch)
    for table_name, payload, unique_key in invalid_calls:
        with pytest.raises(ValueError):
            service._insert_if_columns(
                table_name,
                payload,
                unique_key=unique_key,
            )
    assert rejection_db.session.calls == []
