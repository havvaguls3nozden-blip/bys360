from __future__ import annotations

from pathlib import Path

import pytest

from app.services.performance import process_engine_phase5_notifications as service


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
        for table_name, required_columns in service._PHASE5_REQUIRED_SCHEMA.items()
    }


def test_phase5y_schema_guard_is_read_only_when_schema_is_ready(monkeypatch) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(service, "inspect", lambda engine: _FakeInspector(_complete_schema()))

    service.apply_phase5_schema()
    service.assert_phase5_schema_ready()


def test_phase5y_schema_guard_reports_missing_table_without_writes(monkeypatch) -> None:
    schema = _complete_schema()
    schema.pop("performance_process_notifications")
    monkeypatch.setattr(service, "db", _FakeDb())
    monkeypatch.setattr(service, "inspect", lambda engine: _FakeInspector(schema))

    with pytest.raises(service.Phase5SchemaNotReadyError) as exc_info:
        service.assert_phase5_schema_ready()

    message = str(exc_info.value)
    assert "f5e19f9107d7" in message
    assert "performance_process_notifications" in message
    assert "<tablo eksik>" in message


def test_phase5y_schema_guard_reports_missing_columns(monkeypatch) -> None:
    schema = _complete_schema()
    schema["performance_process_flows"].remove("current_owner_id")
    schema["performance_process_notifications"].remove("recipient_user_id")
    monkeypatch.setattr(service, "db", _FakeDb())
    monkeypatch.setattr(service, "inspect", lambda engine: _FakeInspector(schema))

    with pytest.raises(service.Phase5SchemaNotReadyError) as exc_info:
        service.assert_phase5_schema_ready()

    message = str(exc_info.value)
    assert "performance_process_flows: current_owner_id" in message
    assert "performance_process_notifications: recipient_user_id" in message


def test_phase5y_notifications_module_contains_no_runtime_schema_mutation_sql() -> None:
    source = Path(service.__file__).read_text(encoding="utf-8")
    forbidden = (
        "CREATE TABLE IF NOT EXISTS performance_process_",
        "ALTER TABLE performance_process_",
        "CREATE INDEX IF NOT EXISTS ix_perf_proc_notif_",
    )

    for fragment in forbidden:
        assert fragment not in source
