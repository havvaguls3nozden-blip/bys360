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
    / "c51c29032d4f_close_performance_and_messaging_schema_.py"
)

EXPECTED_NEW_COLUMNS: dict[str, set[str]] = {
    "performance_evaluations": {
        "workflow_status",
        "level_1_submitted_to_level_2_at",
        "level_2_seen_level_1_at",
        "level_2_returned_to_level_1_at",
        "level_2_return_note",
        "level_2_returned_by_id",
        "level_1_last_resubmitted_at",
        "employee_score_viewed_at",
        "employee_score_acknowledged_at",
        "employee_score_acknowledged_note",
    },
    "personnel_leaves": {"performance_mode"},
    "attendance_exceptions": {"performance_mode"},
    "message_threads": {"badge_label", "icon_name", "accent_color"},
}


def _load_migration() -> Any:
    spec = importlib.util.spec_from_file_location("schema_contract_drift_closure", MIGRATION_PATH)
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


def _create_base_schema(connection: sa.Connection) -> None:
    """Mirrors the state of these four tables at revision 10858a18e9ac
    (this migration's down_revision): tables exist (created earlier in the
    chain -- fae32fb68b1b, d2a8c1f9e006, 7c4d9a21b001) but none of the 15
    schema-contract columns this migration adds exist yet."""
    connection.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
    connection.execute(
        sa.text(
            """
            CREATE TABLE performance_evaluations (
                id INTEGER PRIMARY KEY,
                period_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'bekliyor'
            )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            CREATE TABLE personnel_leaves (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                leave_type VARCHAR(50) NOT NULL
            )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            CREATE TABLE attendance_exceptions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                exception_type VARCHAR(50) NOT NULL
            )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            CREATE TABLE message_threads (
                id INTEGER PRIMARY KEY,
                thread_type VARCHAR(30) NOT NULL DEFAULT 'direct',
                created_by_user_id INTEGER NOT NULL
            )
            """
        )
    )


def test_adds_all_15_contract_columns_on_fresh_chain_state() -> None:
    """Fresh-chain scenario (matches a real `flask db upgrade` from empty):
    none of the 15 app/bootstrap/schema_contract.py columns exist on these
    four tables yet. The migration must add every one of them."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_base_schema(connection)
        _run_upgrade(connection)

        for table_name, expected_new in EXPECTED_NEW_COLUMNS.items():
            actual = _column_names(connection, table_name)
            missing = expected_new - actual
            assert not missing, f"{table_name}: columns not created: {sorted(missing)}"


def test_workflow_status_and_performance_mode_are_not_null_with_correct_defaults() -> None:
    """workflow_status and both performance_mode columns are NOT NULL in the
    model (app/models/performance_models.py, app/models/hr_models.py) --
    they must land that way here too, with the same default value the
    runtime schema_guard patches already use in production
    (app/schema_guard_patches.py, app/schema_guard_core_maintenances.py),
    so a pre-existing populated row is backfilled to a value the
    application already treats as correct."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_base_schema(connection)
        connection.execute(sa.text("INSERT INTO performance_evaluations (id, period_id, employee_id) VALUES (1, 1, 1)"))
        connection.execute(sa.text("INSERT INTO personnel_leaves (id, user_id, leave_type) VALUES (1, 1, 'yillik')"))
        connection.execute(
            sa.text("INSERT INTO attendance_exceptions (id, user_id, exception_type) VALUES (1, 1, 'devamsizlik')")
        )

        _run_upgrade(connection)

        assert (
            connection.execute(sa.text("SELECT workflow_status FROM performance_evaluations WHERE id=1")).scalar_one()
            == "taslak_1_amir"
        )
        assert (
            connection.execute(sa.text("SELECT performance_mode FROM personnel_leaves WHERE id=1")).scalar_one()
            == "partial"
        )
        assert (
            connection.execute(sa.text("SELECT performance_mode FROM attendance_exceptions WHERE id=1")).scalar_one()
            == "partial"
        )

        for table_name, column_name in (
            ("performance_evaluations", "workflow_status"),
            ("personnel_leaves", "performance_mode"),
            ("attendance_exceptions", "performance_mode"),
        ):
            column = next(c for c in sa.inspect(connection).get_columns(table_name) if c["name"] == column_name)
            assert column["nullable"] is False, f"{table_name}.{column_name} must be NOT NULL"


def test_adopts_legacy_database_where_columns_already_exist_without_losing_data() -> None:
    """Legacy/live-style scenario: these columns already exist because
    app/schema_guard_patches.py's raw ALTER TABLE ... ADD COLUMN IF NOT
    EXISTS statements (or manual DBA intervention) already added them, and
    a real row already carries non-default values. The migration must
    adopt them -- no duplicate-column error, no data loss, no overwrite of
    the real value with the column's default."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_base_schema(connection)
        connection.execute(
            sa.text("ALTER TABLE performance_evaluations ADD COLUMN workflow_status VARCHAR(50) NOT NULL DEFAULT 'taslak_1_amir'")
        )
        connection.execute(sa.text("ALTER TABLE performance_evaluations ADD COLUMN employee_score_acknowledged_at DATETIME"))
        connection.execute(
            sa.text("ALTER TABLE personnel_leaves ADD COLUMN performance_mode VARCHAR(20) NOT NULL DEFAULT 'partial'")
        )
        connection.execute(sa.text("INSERT INTO performance_evaluations (id, period_id, employee_id, workflow_status) VALUES (1, 1, 1, 'level_2_tamamlandi')"))
        connection.execute(sa.text("INSERT INTO personnel_leaves (id, user_id, leave_type, performance_mode) VALUES (1, 1, 'yillik', 'full')"))

        _run_upgrade(connection)

        assert (
            connection.execute(sa.text("SELECT workflow_status FROM performance_evaluations WHERE id=1")).scalar_one()
            == "level_2_tamamlandi"
        ), "Pre-existing real value must survive adoption, not be reset to the column default."
        assert (
            connection.execute(sa.text("SELECT performance_mode FROM personnel_leaves WHERE id=1")).scalar_one() == "full"
        ), "Pre-existing real value must survive adoption, not be reset to the column default."

        # The rest of the 15-column contract (not pre-seeded above) must
        # still have been added by the migration.
        remaining_pe_cols = EXPECTED_NEW_COLUMNS["performance_evaluations"] - {"workflow_status", "employee_score_acknowledged_at"}
        assert remaining_pe_cols <= _column_names(connection, "performance_evaluations")


def test_upgrade_is_idempotent_when_run_twice() -> None:
    """Running upgrade() a second time against a database it already
    migrated must not error or duplicate anything -- Alembic itself
    prevents replaying an applied revision in normal operation, but the
    upgrade() function's own logic (matches this project's established
    idempotency pattern, e.g. tests/migrations/test_file_center_schema_
    adoption_migration.py) should not silently assume single invocation."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_base_schema(connection)
        _run_upgrade(connection)
        _run_upgrade(connection)

        for table_name, expected_new in EXPECTED_NEW_COLUMNS.items():
            actual = _column_names(connection, table_name)
            assert expected_new <= actual


def test_downgrade_is_non_destructive() -> None:
    """Downgrade must be a no-op: performance_evaluations and
    personnel_leaves can hold years of live scoring/leave data on a
    production database. This project's own established convention for
    adopted/self-healed columns (29fee38a97e1, 10858a18e9ac) is a
    non-destructive no-op downgrade, not a DROP COLUMN."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_base_schema(connection)
        _run_upgrade(connection)
        connection.execute(
            sa.text(
                "INSERT INTO performance_evaluations (id, period_id, employee_id, workflow_status) "
                "VALUES (1, 1, 1, 'level_1_devam_ediyor')"
            )
        )

        _run_downgrade(connection)

        for table_name, expected_new in EXPECTED_NEW_COLUMNS.items():
            assert expected_new <= _column_names(connection, table_name), "Downgrade must not drop any adopted column."
        assert (
            connection.execute(sa.text("SELECT workflow_status FROM performance_evaluations WHERE id=1")).scalar_one()
            == "level_1_devam_ediyor"
        )


def test_skips_missing_tables_without_erroring() -> None:
    """On a database missing one of the four target tables entirely (an
    edge case, not a real supported state, but the migration must not
    crash the whole upgrade over one absent table -- every other table's
    columns should still be added)."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(
            sa.text(
                """
                CREATE TABLE message_threads (
                    id INTEGER PRIMARY KEY,
                    thread_type VARCHAR(30) NOT NULL DEFAULT 'direct',
                    created_by_user_id INTEGER NOT NULL
                )
                """
            )
        )
        # performance_evaluations, personnel_leaves, attendance_exceptions
        # deliberately absent.

        _run_upgrade(connection)

        assert EXPECTED_NEW_COLUMNS["message_threads"] <= _column_names(connection, "message_threads")
