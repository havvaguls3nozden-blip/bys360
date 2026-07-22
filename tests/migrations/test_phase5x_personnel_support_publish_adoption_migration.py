from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "7c4e1a9b2d60_adopt_personnel_support_publish_approval_schema.py"
)
REQUIRED_COLUMNS = {
    "id",
    "evaluation_id",
    "period_id",
    "employee_id",
    "final_score",
    "status",
    "requested_at",
    "requested_by_user_id",
    "decided_at",
    "decided_by_user_id",
    "decision_note",
    "return_note",
    "rule_version",
    "created_at",
    "updated_at",
}
REQUIRED_INDEXES = {
    "ix_phase14b_publish_approval_status",
    "ix_phase14b_publish_approval_period_status",
    "ix_phase14b_publish_approval_employee",
}


def _load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("phase5x_migration", MIGRATION_PATH)
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


def _run_downgrade(connection: sa.Connection) -> None:
    module = _load_migration()
    context = MigrationContext.configure(connection)
    operations = Operations(context)
    original_op = module.op
    module.op = operations
    try:
        module.downgrade()
    finally:
        module.op = original_op


def test_phase5x_creates_complete_schema_on_empty_database() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)

        inspector = sa.inspect(connection)
        columns = {
            column["name"]
            for column in inspector.get_columns(
                "performance_personnel_support_publish_approvals"
            )
        }
        indexes = {
            index["name"]: index
            for index in inspector.get_indexes(
                "performance_personnel_support_publish_approvals"
            )
        }

        assert columns >= REQUIRED_COLUMNS
        assert set(indexes) >= REQUIRED_INDEXES
        assert bool(indexes["ux_phase14b_publish_approval_eval"]["unique"]) is True


def test_phase5x_adopts_legacy_table_without_losing_rows() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                CREATE TABLE performance_personnel_support_publish_approvals (
                    id INTEGER PRIMARY KEY,
                    evaluation_id INTEGER NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending'
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_personnel_support_publish_approvals(
                    id, evaluation_id, status
                )
                VALUES (1, 42, 'approved')
                """
            )
        )

        _run_upgrade(connection)

        row = connection.execute(
            sa.text(
                """
                SELECT id, evaluation_id, status, rule_version
                FROM performance_personnel_support_publish_approvals
                WHERE id = 1
                """
            )
        ).mappings().one()
        columns = {
            column["name"]
            for column in sa.inspect(connection).get_columns(
                "performance_personnel_support_publish_approvals"
            )
        }

        assert dict(row) == {
            "id": 1,
            "evaluation_id": 42,
            "status": "approved",
            "rule_version": "phase1.4b-personnel-support-publish-approval-v1",
        }
        assert columns >= REQUIRED_COLUMNS


def test_phase5x_duplicate_legacy_evaluations_are_preserved() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                CREATE TABLE performance_personnel_support_publish_approvals (
                    id INTEGER PRIMARY KEY,
                    evaluation_id INTEGER NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending'
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_personnel_support_publish_approvals(
                    id, evaluation_id, status
                )
                VALUES (1, 42, 'pending'), (2, 42, 'returned')
                """
            )
        )

        _run_upgrade(connection)

        count = connection.execute(
            sa.text(
                "SELECT COUNT(*) "
                "FROM performance_personnel_support_publish_approvals"
            )
        ).scalar_one()
        index_names = {
            index["name"]
            for index in sa.inspect(connection).get_indexes(
                "performance_personnel_support_publish_approvals"
            )
        }

        assert count == 2
        assert "ux_phase14b_publish_approval_eval" not in index_names


def test_phase5x_upgrade_is_idempotent() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        _run_upgrade(connection)

        table_names = sa.inspect(connection).get_table_names()
        assert "performance_personnel_support_publish_approvals" in table_names


def test_phase5x_downgrade_is_non_destructive() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_personnel_support_publish_approvals(
                    id, evaluation_id, status
                )
                VALUES (1, 88, 'pending')
                """
            )
        )

        _run_downgrade(connection)

        value = connection.execute(
            sa.text(
                "SELECT evaluation_id "
                "FROM performance_personnel_support_publish_approvals "
                "WHERE id = 1"
            )
        ).scalar_one()
        assert value == 88


def test_phase5x_revision_extends_phase5w() -> None:
    module = _load_migration()

    assert module.revision == "7c4e1a9b2d60"
    assert module.down_revision == "6f2b8c4d1a90"
