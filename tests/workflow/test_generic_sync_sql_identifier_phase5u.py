from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.workflow import routes


class _FakeIdentifierPreparer:
    def quote(self, value: str) -> str:
        return f'"{value}"'


class _FakeDialect:
    identifier_preparer = _FakeIdentifierPreparer()


class _FakeEngine:
    dialect = _FakeDialect()


@dataclass
class _FakeResult:
    rows: list[object]

    def mappings(self) -> _FakeResult:
        return self

    def all(self) -> list[object]:
        return list(self.rows)


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object] | None]] = []
        self.commit_count = 0

    def execute(self, statement, params=None) -> _FakeResult:
        self.calls.append((str(statement), params))
        return _FakeResult([])

    def commit(self) -> None:
        self.commit_count += 1


class _FakeDb:
    def __init__(self) -> None:
        self.engine = _FakeEngine()
        self.session = _FakeSession()


def _normalize_sql(value: str) -> str:
    return " ".join(value.split())


def test_sync_generic_table_quotes_closed_table_and_column_sets(
    monkeypatch,
) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(routes, "db", fake_db)
    monkeypatch.setattr(routes, "_table_exists", lambda table_name: True)

    available = {"title", "created_by_id", "status"}
    monkeypatch.setattr(
        routes,
        "_first_existing_column",
        lambda table_name, candidates: next(
            (column for column in candidates if column in available),
            None,
        ),
    )

    created = routes._sync_generic_table(
        table_name="support_tickets",
        module="support",
        entity_type="support_ticket",
        title_prefix="Destek Talebi",
        title_candidates=["title", "subject", "summary"],
        subject_candidates=["created_by_id", "requester_id", "user_id"],
        status_candidates=["status", "state"],
        step_name="Destek Talebi İncelemesi",
        workflow_family="SUPPORT",
        limit=25,
    )

    assert created == 0
    assert fake_db.session.commit_count == 1
    assert len(fake_db.session.calls) == 1
    sql, params = fake_db.session.calls[0]
    assert _normalize_sql(sql) == (
        'SELECT t.id AS entity_id, '
        'COALESCE(CAST(t."title" AS TEXT), :fallback_title) AS source_title, '
        't."created_by_id" AS subject_user_id, '
        'COALESCE(CAST(t."status" AS TEXT), \'ACTIVE\') AS source_status '
        'FROM "support_tickets" t LEFT JOIN workflow_instances wi '
        'ON wi.module = :module AND wi.entity_type = :entity_type '
        'AND wi.entity_id = t.id WHERE wi.id IS NULL '
        'ORDER BY t.id DESC LIMIT :limit'
    )
    assert params == {
        "module": "support",
        "entity_type": "support_ticket",
        "fallback_title": "Destek Talebi",
        "limit": 25,
    }


def test_sync_generic_table_rejects_unknown_or_unsafe_table(
    monkeypatch,
) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(routes, "db", fake_db)

    for table_name in (
        "other_table",
        "support_tickets; DROP TABLE users",
        "public.support_tickets",
    ):
        with pytest.raises(ValueError):
            routes._sync_generic_table(
                table_name=table_name,
                module="support",
                entity_type="support_ticket",
                title_prefix="Destek Talebi",
                title_candidates=["title"],
                subject_candidates=["created_by_id"],
                status_candidates=["status"],
                step_name="Destek Talebi İncelemesi",
                workflow_family="SUPPORT",
            )

    assert fake_db.session.calls == []


def test_sync_generic_table_rejects_column_outside_table_contract(
    monkeypatch,
) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(routes, "db", fake_db)

    with pytest.raises(ValueError):
        routes._sync_generic_table(
            table_name="support_tickets",
            module="support",
            entity_type="support_ticket",
            title_prefix="Destek Talebi",
            title_candidates=["title; DROP TABLE users"],
            subject_candidates=["created_by_id"],
            status_candidates=["status"],
            step_name="Destek Talebi İncelemesi",
            workflow_family="SUPPORT",
        )

    assert fake_db.session.calls == []
