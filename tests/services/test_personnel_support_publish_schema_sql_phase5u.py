from __future__ import annotations

from dataclasses import dataclass

from app.services.performance import personnel_support_publish_approval_service as service


@dataclass
class _FakeDialect:
    name: str


class _FakeEngine:
    def __init__(self, dialect_name: str) -> None:
        self.dialect = _FakeDialect(dialect_name)


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.commit_count = 0

    def execute(self, statement, params=None):
        assert params in (None, {})
        self.calls.append(" ".join(str(statement).split()))
        return None

    def commit(self) -> None:
        self.commit_count += 1


class _FakeDb:
    def __init__(self, dialect_name: str) -> None:
        self.engine = _FakeEngine(dialect_name)
        self.session = _FakeSession()


def test_apply_phase14b_schema_uses_static_postgresql_statements(
    monkeypatch,
) -> None:
    fake_db = _FakeDb("postgresql")
    monkeypatch.setattr(service, "db", fake_db)

    service.apply_phase1_4b_schema()

    assert len(fake_db.session.calls) == 12
    assert fake_db.session.commit_count == 1
    assert fake_db.session.calls[0].startswith(
        "CREATE TABLE IF NOT EXISTS "
        "performance_personnel_support_publish_approvals ( id SERIAL PRIMARY KEY"
    )
    assert all("{table}" not in sql for sql in fake_db.session.calls)
    assert all(service.APPROVAL_TABLE in sql for sql in fake_db.session.calls)
    assert any("ADD COLUMN IF NOT EXISTS final_score" in sql for sql in fake_db.session.calls)
    assert any("ux_phase14b_publish_approval_eval" in sql for sql in fake_db.session.calls)


def test_apply_phase14b_schema_uses_static_sqlite_statement_without_alter(
    monkeypatch,
) -> None:
    fake_db = _FakeDb("sqlite")
    monkeypatch.setattr(service, "db", fake_db)

    service.apply_phase1_4b_schema()

    assert len(fake_db.session.calls) == 5
    assert fake_db.session.commit_count == 1
    assert fake_db.session.calls[0].startswith(
        "CREATE TABLE IF NOT EXISTS "
        "performance_personnel_support_publish_approvals "
        "( id INTEGER PRIMARY KEY AUTOINCREMENT"
    )
    assert not any(sql.startswith("ALTER TABLE") for sql in fake_db.session.calls)
    assert all("{table}" not in sql for sql in fake_db.session.calls)
