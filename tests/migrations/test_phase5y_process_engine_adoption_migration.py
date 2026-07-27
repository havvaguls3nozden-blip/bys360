from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, cast

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "f5e19f9107d7_adopt_phase5_process_engine_schema_into_.py"
)

FLOW_REQUIRED_COLUMNS = {
    "id",
    "evaluation_id",
    "period_id",
    "employee_id",
    "current_owner_id",
    "current_owner_label",
    "current_step_key",
    "current_status",
    "final_score",
    "is_low_score",
    "president_approval_required",
    "president_approval_status",
    "is_finalized",
    "started_at",
    "last_action_at",
    "completed_at",
    "rule_version",
    "created_at",
    "updated_at",
}
FLOW_STEP_REQUIRED_COLUMNS = {
    "id",
    "flow_id",
    "evaluation_id",
    "step_order",
    "step_key",
    "step_title",
    "step_status",
    "actor_id",
    "actor_label",
    "owner_id",
    "owner_label",
    "action_summary",
    "action_note",
    "score_snapshot",
    "occurred_at",
    "created_at",
    "rule_version",
}
NOTIFICATION_REQUIRED_COLUMNS = {
    "id",
    "flow_id",
    "evaluation_id",
    "recipient_id",
    "notification_type",
    "title",
    "body",
    "target_url",
    "delivery_status",
    "source_event_key",
    "created_at",
    "read_at",
    "rule_version",
    "recipient_user_id",
    "recipient_name",
    "notification_status",
    "priority",
    "action_url",
    "source_table",
    "source_id",
    "flow_status_snapshot",
    "actor_user_id",
    "sent_at",
    "process_version",
    "app_notification_id",
    "updated_at",
}


def _load_migration() -> Any:
    # The loaded migration module's op/upgrade/downgrade/revision attributes
    # are dynamically defined by whichever versions/*.py file is loaded, and
    # `op` is deliberately reassigned below before each upgrade/downgrade
    # call -- there is no fixed static contract to type against.
    spec = importlib.util.spec_from_file_location("phase5y_process_engine_adoption", MIGRATION_PATH)
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


def _index_names(connection: sa.Connection, table_name: str) -> set[str]:
    # Real indexes always have a real string name (SQLite/Postgres both
    # require one); ReflectedIndex.name is only str | None in SQLAlchemy's
    # generic reflection stub for dialects that could theoretically omit it.
    return {cast(str, index["name"]) for index in sa.inspect(connection).get_indexes(table_name)}


def test_phase5y_creates_complete_schema_on_empty_database() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        _run_upgrade(connection)

        tables = set(sa.inspect(connection).get_table_names())
        assert {
            "performance_process_flows",
            "performance_process_flow_steps",
            "performance_process_notifications",
        }.issubset(tables)

        assert _column_names(connection, "performance_process_flows") >= FLOW_REQUIRED_COLUMNS
        assert _column_names(connection, "performance_process_flow_steps") >= FLOW_STEP_REQUIRED_COLUMNS
        assert _column_names(connection, "performance_process_notifications") >= NOTIFICATION_REQUIRED_COLUMNS

        flow_indexes = _index_names(connection, "performance_process_flows")
        assert "ix_performance_process_flows_evaluation_id" in flow_indexes
        assert "ix_performance_process_flows_current_status" in flow_indexes

        notification_indexes = _index_names(connection, "performance_process_notifications")
        assert "ix_perf_proc_notif_recipient_status_phase5" in notification_indexes
        assert "ix_perf_proc_notif_source_phase5" in notification_indexes
        assert "ix_perf_proc_notif_flow_type_phase5" in notification_indexes


def test_phase5y_adopts_legacy_flows_table_without_losing_rows() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.execute(
            sa.text(
                """
                CREATE TABLE performance_process_flows (
                    id INTEGER PRIMARY KEY,
                    evaluation_id INTEGER,
                    current_status VARCHAR(80)
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_process_flows(id, evaluation_id, current_status)
                VALUES (1, 42, 'created')
                """
            )
        )

        _run_upgrade(connection)

        row = connection.execute(
            sa.text(
                "SELECT id, evaluation_id, current_status FROM performance_process_flows WHERE id = 1"
            )
        ).mappings().one()

        assert dict(row) == {"id": 1, "evaluation_id": 42, "current_status": "created"}
        assert _column_names(connection, "performance_process_flows") >= FLOW_REQUIRED_COLUMNS


def test_phase5y_duplicate_legacy_flow_evaluation_ids_are_preserved_without_unique_index() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.execute(
            sa.text(
                """
                CREATE TABLE performance_process_flows (
                    id INTEGER PRIMARY KEY,
                    evaluation_id INTEGER,
                    current_status VARCHAR(80)
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_process_flows(id, evaluation_id, current_status)
                VALUES (1, 42, 'created'), (2, 42, 'in_progress')
                """
            )
        )

        _run_upgrade(connection)

        count = connection.execute(
            sa.text("SELECT COUNT(*) FROM performance_process_flows")
        ).scalar_one()
        index_names = _index_names(connection, "performance_process_flows")

        assert count == 2
        assert "ix_performance_process_flows_evaluation_id" not in index_names


def test_phase5y_adopts_legacy_notifications_table_and_backfills_compatibility_columns() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.execute(
            sa.text(
                """
                CREATE TABLE performance_process_notifications (
                    id INTEGER PRIMARY KEY,
                    recipient_id INTEGER NOT NULL,
                    notification_type VARCHAR(80) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    delivery_status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    rule_version VARCHAR(120) NOT NULL DEFAULT 'phase2_process_engine_v1'
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_process_notifications
                    (id, recipient_id, notification_type, title, delivery_status, rule_version)
                VALUES (1, 7, 'performance_waiting_task', 'Görev bekliyor', 'pending', 'phase2_process_engine_v1')
                """
            )
        )

        _run_upgrade(connection)

        row = connection.execute(
            sa.text(
                """
                SELECT recipient_id, recipient_user_id, notification_status, process_version
                FROM performance_process_notifications
                WHERE id = 1
                """
            )
        ).mappings().one()

        assert row["recipient_user_id"] == row["recipient_id"] == 7
        # notification_status carries no explicit legacy value, so the newly
        # added column's own server default ("bekliyor") takes effect before
        # the backfill UPDATE runs; the backfill only rescues NULLs left by
        # columns without a server default (e.g. recipient_user_id, process_version).
        assert row["notification_status"] == "bekliyor"
        assert row["process_version"] == "phase2_process_engine_v1"
        assert _column_names(connection, "performance_process_notifications") >= NOTIFICATION_REQUIRED_COLUMNS


def test_phase5y_downgrade_is_non_destructive_for_adopted_tables() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        _run_upgrade(connection)

        connection.execute(
            sa.text(
                "INSERT INTO performance_process_flows (id, evaluation_id) VALUES (1, 4242)"
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_process_flow_steps
                    (id, flow_id, evaluation_id, step_key, step_title)
                VALUES (1, 1, 4242, 'created', 'Korunacak adim')
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_process_notifications
                    (id, flow_id, recipient_id, notification_type, title)
                VALUES (1, 1, 7, 'performance_waiting_task', 'Korunacak bildirim')
                """
            )
        )

        _run_downgrade(connection)

        tables = set(sa.inspect(connection).get_table_names())
        assert {
            "performance_process_flows",
            "performance_process_flow_steps",
            "performance_process_notifications",
        }.issubset(tables)

        flow_row = connection.execute(
            sa.text("SELECT evaluation_id FROM performance_process_flows WHERE id = 1")
        ).scalar_one()
        step_row = connection.execute(
            sa.text("SELECT step_title FROM performance_process_flow_steps WHERE id = 1")
        ).scalar_one()
        notification_row = connection.execute(
            sa.text("SELECT title FROM performance_process_notifications WHERE id = 1")
        ).scalar_one()

        assert flow_row == 4242
        assert step_row == "Korunacak adim"
        assert notification_row == "Korunacak bildirim"


def test_phase5y_upgrade_is_idempotent() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        _run_upgrade(connection)
        _run_upgrade(connection)

        tables = set(sa.inspect(connection).get_table_names())
        assert {
            "performance_process_flows",
            "performance_process_flow_steps",
            "performance_process_notifications",
        }.issubset(tables)
