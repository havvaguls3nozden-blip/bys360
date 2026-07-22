from __future__ import annotations

from dataclasses import dataclass

from app import extensions
from app.services.performance_v2 import reporting_workspace as service


class _FakeIdentifierPreparer:
    def quote(self, value: str) -> str:
        return f'"{value}"'


class _FakeDialect:
    identifier_preparer = _FakeIdentifierPreparer()


class _FakeEngine:
    dialect = _FakeDialect()


@dataclass
class _FakeResult:
    row: dict[str, object] | None

    def mappings(self) -> _FakeResult:
        return self

    def first(self) -> dict[str, object] | None:
        return self.row


class _FakeSession:
    def __init__(self, row: dict[str, object] | None = None) -> None:
        self.row = row
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def execute(self, statement, params=None) -> _FakeResult:
        self.calls.append((str(statement), params))
        return _FakeResult(self.row)


class _FakeDb:
    def __init__(self, row: dict[str, object] | None = None) -> None:
        self.engine = _FakeEngine()
        self.session = _FakeSession(row)


def _normalize_sql(value: str) -> str:
    return " ".join(value.split())


def test_load_latest_process_flow_quotes_closed_set_and_binds_value(
    monkeypatch,
) -> None:
    fake_db = _FakeDb(
        {
            "id": 9,
            "evaluation_id": 42,
            "current_status": "president_pending",
            "tracking_updated_at": "2026-07-22T12:00:00",
        }
    )
    monkeypatch.setattr(extensions, "db", fake_db)
    monkeypatch.setattr(
        service,
        "_get_process_flow_columns",
        lambda: {
            "id",
            "evaluation_id",
            "current_status",
            "tracking_updated_at",
            "unsafe_column; DROP TABLE users",
        },
    )

    row = service._load_latest_process_flow(42)

    assert row == {
        "id": 9,
        "evaluation_id": 42,
        "current_status": "president_pending",
        "tracking_updated_at": "2026-07-22T12:00:00",
    }
    assert len(fake_db.session.calls) == 1
    sql, params = fake_db.session.calls[0]
    normalized_sql = _normalize_sql(sql)
    assert normalized_sql == (
        'SELECT "id", "evaluation_id", "current_status", '
        '"tracking_updated_at" FROM performance_process_flows '
        'WHERE evaluation_id = :evaluation_id '
        'ORDER BY "tracking_updated_at" DESC NULLS LAST LIMIT 1'
    )
    assert "unsafe_column" not in normalized_sql
    assert params == {"evaluation_id": 42}


def test_load_latest_process_flow_fails_closed_without_allowed_order_column(
    monkeypatch,
) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(extensions, "db", fake_db)
    monkeypatch.setattr(
        service,
        "_get_process_flow_columns",
        lambda: {"evaluation_id", "current_status"},
    )

    assert service._load_latest_process_flow(42) is None
    assert fake_db.session.calls == []
