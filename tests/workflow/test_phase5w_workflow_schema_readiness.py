from __future__ import annotations

from pathlib import Path

import pytest

from app.workflow import routes


class _FakeInspector:
    def __init__(self, schema: dict[str, set[str]]) -> None:
        self.schema = schema

    def get_table_names(self) -> list[str]:
        return list(self.schema)

    def get_columns(self, table_name: str) -> list[dict[str, str]]:
        return [{"name": name} for name in sorted(self.schema[table_name])]


class _ForbiddenSession:
    def execute(self, *args, **kwargs):
        raise AssertionError("Schema readiness must not execute SQL")

    def commit(self) -> None:
        raise AssertionError("Schema readiness must not commit")


class _FakeDb:
    engine = object()
    session = _ForbiddenSession()


def _complete_schema() -> dict[str, set[str]]:
    return {
        table_name: set(required_columns)
        for table_name, required_columns in routes._WORKFLOW_REQUIRED_SCHEMA.items()
    }


def test_phase5w_schema_guard_is_read_only_when_schema_is_ready(monkeypatch) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(routes, "db", fake_db)
    monkeypatch.setattr(routes, "inspect", lambda engine: _FakeInspector(_complete_schema()))

    routes.ensure_tables()
    routes.assert_workflow_schema_ready()


def test_phase5w_schema_guard_reports_missing_table_without_writes(monkeypatch) -> None:
    schema = _complete_schema()
    schema.pop("workflow_notifications")
    monkeypatch.setattr(routes, "db", _FakeDb())
    monkeypatch.setattr(routes, "inspect", lambda engine: _FakeInspector(schema))

    with pytest.raises(routes.WorkflowSchemaNotReadyError) as exc_info:
        routes.assert_workflow_schema_ready()

    message = str(exc_info.value)
    assert "6f2b8c4d1a90" in message
    assert "workflow_notifications" in message
    assert "<tablo eksik>" in message


def test_phase5w_schema_guard_reports_missing_columns(monkeypatch) -> None:
    schema = _complete_schema()
    schema["workflow_steps"].remove("delay_state")
    schema["performance_president_approvals"].remove("workflow_id")
    monkeypatch.setattr(routes, "db", _FakeDb())
    monkeypatch.setattr(routes, "inspect", lambda engine: _FakeInspector(schema))

    with pytest.raises(routes.WorkflowSchemaNotReadyError) as exc_info:
        routes.assert_workflow_schema_ready()

    message = str(exc_info.value)
    assert "workflow_steps: delay_state" in message
    assert "performance_president_approvals: workflow_id" in message


def test_phase5w_routes_contain_no_runtime_schema_mutation_sql() -> None:
    source = Path(routes.__file__).read_text(encoding="utf-8")
    forbidden = (
        "CREATE TABLE IF NOT EXISTS workflow_",
        "ALTER TABLE workflow_",
        "CREATE INDEX IF NOT EXISTS ix_workflow_",
        "CREATE TABLE IF NOT EXISTS performance_president_approvals",
        "CREATE INDEX IF NOT EXISTS ix_perf_pres_approvals_status",
    )

    for fragment in forbidden:
        assert fragment not in source
