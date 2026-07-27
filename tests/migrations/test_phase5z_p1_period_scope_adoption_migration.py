from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "f6d6934ad77f_adopt_p1_meeting_development_period_.py"
)

NEW_SCOPE_COLUMNS = {
    "scope_unit_label",
    "scope_category_label",
    "scope_personnel_filter",
    "level_3_column_visible",
    "scorecard_readability_mode",
}


def _load_migration() -> Any:
    # The loaded migration module's op/upgrade/downgrade/revision attributes
    # are dynamically defined by whichever versions/*.py file is loaded, and
    # `op` is deliberately reassigned below before each upgrade/downgrade
    # call -- there is no fixed static contract to type against.
    spec = importlib.util.spec_from_file_location("phase5z_p1_period_scope_adoption", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_upgrade(connection: sa.Connection) -> None:
    module = _load_migration()
    module.op = Operations(MigrationContext.configure(connection))
    module.upgrade()


def _run_downgrade(connection: sa.Connection) -> None:
    module = _load_migration()
    module.op = Operations(MigrationContext.configure(connection))
    module.downgrade()


def _column_names(connection: sa.Connection, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(connection).get_columns(table_name)}


def _create_minimal_periods_table(connection: sa.Connection) -> None:
    connection.execute(
        sa.text(
            """
            CREATE TABLE performance_periods (
                id INTEGER PRIMARY KEY,
                title VARCHAR(255),
                scope_type VARCHAR(64)
            )
            """
        )
    )


def test_phase5z_adds_missing_p1_scope_columns_without_touching_scope_type() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_minimal_periods_table(connection)
        connection.execute(
            sa.text(
                "INSERT INTO performance_periods (id, title, scope_type) VALUES (1, 'Donem 1', 'all')"
            )
        )

        _run_upgrade(connection)

        columns = _column_names(connection, "performance_periods")
        assert NEW_SCOPE_COLUMNS.issubset(columns)

        row = connection.execute(
            sa.text("SELECT title, scope_type FROM performance_periods WHERE id = 1")
        ).mappings().one()
        assert dict(row) == {"title": "Donem 1", "scope_type": "all"}


def test_phase5z_upgrade_raises_clear_error_when_periods_table_missing() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection, pytest.raises(RuntimeError, match="performance_periods"):
        _run_upgrade(connection)


def test_phase5z_upgrade_is_idempotent() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_minimal_periods_table(connection)
        _run_upgrade(connection)
        _run_upgrade(connection)

        columns = _column_names(connection, "performance_periods")
        assert NEW_SCOPE_COLUMNS.issubset(columns)


def test_phase5z_downgrade_is_non_destructive_for_adopted_columns() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_minimal_periods_table(connection)
        connection.execute(
            sa.text(
                "INSERT INTO performance_periods (id, title, scope_type) VALUES (1, 'Donem 1', 'all')"
            )
        )
        _run_upgrade(connection)
        connection.execute(
            sa.text(
                "UPDATE performance_periods SET scope_unit_label = 'Korunacak birim' WHERE id = 1"
            )
        )

        _run_downgrade(connection)

        assert "performance_periods" in sa.inspect(connection).get_table_names()
        row = connection.execute(
            sa.text("SELECT scope_unit_label FROM performance_periods WHERE id = 1")
        ).scalar_one()
        assert row == "Korunacak birim"
