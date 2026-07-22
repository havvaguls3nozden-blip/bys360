from __future__ import annotations

from pathlib import Path

import pytest

from app.services.performance import personnel_support_publish_approval_service as service


class _FakeInspector:
    def __init__(
        self,
        *,
        tables: set[str],
        columns: set[str],
        indexes: set[str],
    ) -> None:
        self.tables = tables
        self.columns = columns
        self.indexes = indexes

    def get_table_names(self) -> list[str]:
        return sorted(self.tables)

    def get_columns(self, table_name: str) -> list[dict[str, str]]:
        assert table_name == service.APPROVAL_TABLE
        return [{"name": name} for name in sorted(self.columns)]

    def get_indexes(self, table_name: str) -> list[dict[str, str]]:
        assert table_name == service.APPROVAL_TABLE
        return [{"name": name} for name in sorted(self.indexes)]


class _ForbiddenSession:
    def execute(self, *args, **kwargs):
        raise AssertionError("Schema readiness must not execute SQL")

    def commit(self) -> None:
        raise AssertionError("Schema readiness must not commit")


class _FakeDb:
    engine = object()
    session = _ForbiddenSession()


def _complete_inspector() -> _FakeInspector:
    return _FakeInspector(
        tables={service.APPROVAL_TABLE},
        columns=set(service._PHASE14B_REQUIRED_COLUMNS),
        indexes=set(service._PHASE14B_REQUIRED_INDEXES),
    )


def test_apply_phase14b_schema_is_read_only_compatibility_guard(monkeypatch) -> None:
    monkeypatch.setattr(service, "db", _FakeDb())
    monkeypatch.setattr(service, "inspect", lambda engine: _complete_inspector())

    service.apply_phase1_4b_schema()
    service.assert_phase1_4b_schema_ready()


def test_phase14b_schema_guard_reports_missing_table(monkeypatch) -> None:
    inspector = _FakeInspector(tables=set(), columns=set(), indexes=set())
    monkeypatch.setattr(service, "db", _FakeDb())
    monkeypatch.setattr(service, "inspect", lambda engine: inspector)

    with pytest.raises(service.PersonnelSupportPublishSchemaNotReadyError) as exc_info:
        service.assert_phase1_4b_schema_ready()

    message = str(exc_info.value)
    assert service.PHASE1_4B_SCHEMA_REVISION in message
    assert service.APPROVAL_TABLE in message
    assert "<tablo eksik>" in message


def test_phase14b_schema_guard_reports_missing_columns_and_indexes(
    monkeypatch,
) -> None:
    columns = set(service._PHASE14B_REQUIRED_COLUMNS)
    columns.remove("return_note")
    indexes = set(service._PHASE14B_REQUIRED_INDEXES)
    indexes.remove("ix_phase14b_publish_approval_employee")
    inspector = _FakeInspector(
        tables={service.APPROVAL_TABLE},
        columns=columns,
        indexes=indexes,
    )
    monkeypatch.setattr(service, "db", _FakeDb())
    monkeypatch.setattr(service, "inspect", lambda engine: inspector)

    with pytest.raises(service.PersonnelSupportPublishSchemaNotReadyError) as exc_info:
        service.assert_phase1_4b_schema_ready()

    message = str(exc_info.value)
    assert "return_note" in message
    assert "ix_phase14b_publish_approval_employee" in message


def test_phase14b_service_contains_no_runtime_schema_mutation_sql() -> None:
    source = Path(service.__file__).read_text(encoding="utf-8")
    forbidden = (
        "CREATE TABLE IF NOT EXISTS performance_personnel_support_publish_approvals",
        "ALTER TABLE performance_personnel_support_publish_approvals",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_phase14b_publish_approval_eval",
        "CREATE INDEX IF NOT EXISTS ix_phase14b_publish_approval_status",
    )

    for fragment in forbidden:
        assert fragment not in source
