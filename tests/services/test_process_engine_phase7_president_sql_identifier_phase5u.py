from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.services.performance import process_engine_phase7_president_rule as service


class _FakeIdentifierPreparer:
    def quote(self, value: str) -> str:
        return f'"{value}"'


class _FakeDialect:
    identifier_preparer = _FakeIdentifierPreparer()


class _FakeEngine:
    dialect = _FakeDialect()


@dataclass
class _FakeResult:
    values: list[int]

    def scalars(self) -> _FakeResult:
        return self

    def all(self) -> list[int]:
        return list(self.values)


class _FakeSession:
    def __init__(self, values: list[int] | None = None) -> None:
        self.values = list(values or [])
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def execute(self, statement, params=None) -> _FakeResult:
        self.calls.append((str(statement), params))
        return _FakeResult(self.values)


class _FakeDb:
    def __init__(self, values: list[int] | None = None) -> None:
        self.engine = _FakeEngine()
        self.session = _FakeSession(values)


def _normalize_sql(value: str) -> str:
    return " ".join(value.split())


def test_candidate_evaluation_ids_quotes_score_column_and_binds_limit(
    monkeypatch,
) -> None:
    fake_db = _FakeDb([91, 88])
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(service, "_table_exists", lambda table_name: True)
    monkeypatch.setattr(
        service,
        "_evaluation_columns",
        lambda: {"id", "final_total_100", "unsafe; DROP TABLE users"},
    )

    assert service.candidate_evaluation_ids(limit=25) == [91, 88]

    assert len(fake_db.session.calls) == 1
    sql, params = fake_db.session.calls[0]
    assert _normalize_sql(sql) == (
        'SELECT id FROM performance_evaluations '
        'WHERE "final_total_100" IS NOT NULL '
        'AND "final_total_100" < 70 '
        'ORDER BY id DESC LIMIT :limit'
    )
    assert "unsafe" not in sql
    assert params == {"limit": 25}


def test_candidate_evaluation_ids_rejects_unsafe_selected_identifier(
    monkeypatch,
) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(service, "_table_exists", lambda table_name: True)
    monkeypatch.setattr(service, "_evaluation_columns", lambda: {"id"})
    monkeypatch.setattr(
        service,
        "_first_existing",
        lambda columns, candidates: "final_score; DROP TABLE users",
    )

    with pytest.raises(ValueError, match="Unsafe SQL identifier"):
        service.candidate_evaluation_ids()

    assert fake_db.session.calls == []
