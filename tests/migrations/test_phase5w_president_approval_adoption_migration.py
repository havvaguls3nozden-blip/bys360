from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "6f2b8c4d1a90_adopt_workflow_president_approval_schema.py"
)
REQUIRED_COLUMNS = {
    "id",
    "evaluation_id",
    "period_id",
    "employee_id",
    "score",
    "final_score",
    "status",
    "workflow_id",
    "flow_id",
    "requested_by_id",
    "president_id",
    "president_user_id",
    "president_name",
    "requested_at",
    "decided_at",
    "decision_note",
    "process_version",
    "phase6_low_score_marker",
    "publish_lock_label",
    "low_score_repeat_level",
    "created_at",
    "updated_at",
}


def _load_migration() -> Any:
    # The loaded migration module's op/upgrade/downgrade/revision attributes
    # are dynamically defined by whichever versions/*.py file is loaded, and
    # `op` is deliberately reassigned below before each upgrade/downgrade
    # call -- there is no fixed static contract to type against.
    spec = importlib.util.spec_from_file_location("phase5w_migration", MIGRATION_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_upgrade(connection: sa.Connection) -> None:
    module = _load_migration()
    context = MigrationContext.configure(connection)
    operations = Operations(context)
    original_op = module.op
    module.op = operations
    try:
        module.upgrade()
    finally:
        module.op = original_op


def _create_workflow_instances(connection: sa.Connection) -> None:
    connection.execute(
        sa.text(
            """
            CREATE TABLE workflow_instances (
                id INTEGER PRIMARY KEY
            )
            """
        )
    )


def test_phase5w_creates_complete_approval_schema_on_empty_database() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_workflow_instances(connection)
        _run_upgrade(connection)

        inspector = sa.inspect(connection)
        columns = {
            column["name"]
            for column in inspector.get_columns("performance_president_approvals")
        }
        indexes = {
            index["name"]: index
            for index in inspector.get_indexes("performance_president_approvals")
        }

        assert columns >= REQUIRED_COLUMNS
        assert "ix_perf_pres_approvals_status" in indexes
        assert "ix_perf_phase7_president_eval" in indexes
        assert bool(indexes["uq_perf_pres_approvals_evaluation_id"]["unique"]) is True


def test_phase5w_adopts_legacy_table_without_losing_rows() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_workflow_instances(connection)
        connection.execute(
            sa.text(
                """
                CREATE TABLE performance_president_approvals (
                    id INTEGER PRIMARY KEY,
                    evaluation_id INTEGER,
                    status VARCHAR(40)
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_president_approvals(id, evaluation_id, status)
                VALUES (1, 42, 'PENDING')
                """
            )
        )

        _run_upgrade(connection)

        row = connection.execute(
            sa.text(
                """
                SELECT id, evaluation_id, status
                FROM performance_president_approvals
                WHERE id = 1
                """
            )
        ).mappings().one()
        columns = {
            column["name"]
            for column in sa.inspect(connection).get_columns("performance_president_approvals")
        }

        assert dict(row) == {"id": 1, "evaluation_id": 42, "status": "PENDING"}
        assert columns >= REQUIRED_COLUMNS


def test_phase5w_duplicate_legacy_evaluations_are_preserved_without_unique_index() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_workflow_instances(connection)
        connection.execute(
            sa.text(
                """
                CREATE TABLE performance_president_approvals (
                    id INTEGER PRIMARY KEY,
                    evaluation_id INTEGER,
                    status VARCHAR(40)
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_president_approvals(id, evaluation_id, status)
                VALUES (1, 42, 'PENDING'), (2, 42, 'RETURNED')
                """
            )
        )

        _run_upgrade(connection)

        count = connection.execute(
            sa.text("SELECT COUNT(*) FROM performance_president_approvals")
        ).scalar_one()
        index_names = {
            index["name"]
            for index in sa.inspect(connection).get_indexes("performance_president_approvals")
        }

        assert count == 2
        assert "uq_perf_pres_approvals_evaluation_id" not in index_names


def test_phase5w_upgrade_is_idempotent() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_workflow_instances(connection)
        _run_upgrade(connection)
        _run_upgrade(connection)

        assert "performance_president_approvals" in sa.inspect(connection).get_table_names()
