from __future__ import annotations

from pathlib import Path

from app.services.performance import meeting_p1_scope as service


class _FakeInspector:
    def __init__(self, columns: set[str], *, table_exists: bool = True) -> None:
        self._columns = columns
        self._table_exists = table_exists

    def has_table(self, table_name: str) -> bool:
        return self._table_exists

    def get_columns(self, table_name: str) -> list[dict[str, str]]:
        return [{"name": name} for name in sorted(self._columns)]


class _ForbiddenSession:
    def execute(self, *args, **kwargs):
        raise AssertionError("ensure_p1_period_scope_columns must not execute SQL")

    def commit(self) -> None:
        raise AssertionError("ensure_p1_period_scope_columns must not commit")


class _FakeDb:
    engine = object()
    session = _ForbiddenSession()


def test_phase5z_ensure_p1_period_scope_columns_is_read_only_when_schema_ready(monkeypatch) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(
        service,
        "inspect",
        lambda engine: _FakeInspector(set(service.P1_PERIOD_SCOPE_COLUMNS)),
    )

    ready, warnings = service.ensure_p1_period_scope_columns()

    assert ready == len(service.P1_PERIOD_SCOPE_COLUMNS)
    assert warnings == []


def test_phase5z_ensure_p1_period_scope_columns_reports_missing_columns_with_revision(
    monkeypatch,
) -> None:
    existing = set(service.P1_PERIOD_SCOPE_COLUMNS) - {
        "scope_unit_label",
        "level_3_column_visible",
    }
    fake_db = _FakeDb()
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(service, "inspect", lambda engine: _FakeInspector(existing))

    ready, warnings = service.ensure_p1_period_scope_columns()

    assert ready == len(existing)
    assert any(
        "scope_unit_label" in warning and service.P1_SCOPE_SCHEMA_REVISION in warning
        for warning in warnings
    )
    assert any(
        "level_3_column_visible" in warning and service.P1_SCOPE_SCHEMA_REVISION in warning
        for warning in warnings
    )
    # scope_type is intentionally owned by earlier migrations, not this
    # package's revision, so it must never be reported as missing here.
    assert not any("scope_type" in warning for warning in warnings)


def test_phase5z_ensure_p1_period_scope_columns_reports_missing_table(monkeypatch) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(
        service,
        "inspect",
        lambda engine: _FakeInspector(set(), table_exists=False),
    )

    ready, warnings = service.ensure_p1_period_scope_columns()

    assert ready == 0
    assert any("performance_periods" in warning for warning in warnings)


def test_phase5z_meeting_p1_scope_module_contains_no_runtime_schema_mutation_sql() -> None:
    source = Path(service.__file__).read_text(encoding="utf-8")
    # Matches the literal DDL fragment the old runtime ALTER used, not the
    # explanatory prose in ensure_p1_period_scope_columns()'s docstring.
    assert "ALTER TABLE performance_periods" not in source
