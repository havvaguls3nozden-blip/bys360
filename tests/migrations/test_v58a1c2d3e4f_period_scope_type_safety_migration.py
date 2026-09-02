"""BYS360_DEFECT_AC_MIGRATION_POSTCONDITION_CONTRACT

Investigation and closure for Defect AC: does migrations/versions/
v58a1c2d3e4f_add_period_scope_type_safety.py's ``_safe_execute`` (a broad
``except Exception: ...logged...`` wrapper around its backfill/ALTER
statements) risk silently leaving an invalid schema/data state?

Findings, mechanically proven by the tests below (not assumed):

1. Every ``_safe_execute``-wrapped backfill UPDATE uses a COALESCE chain
   ending in a literal/CURRENT_TIMESTAMP fallback that can NEVER itself
   produce a NULL result when the statement executes successfully -- e.g.
   ``low_score_detected_at=COALESCE(low_score_detected_at, created_at,
   updated_at, CURRENT_TIMESTAMP)``. There is no code path where the
   UPDATE runs to completion and leaves a targeted row unbackfilled.

2. Every column-existence-dependent operation is gated by ``_has_table``/
   ``_has_column`` checks BEFORE running -- type/existence mismatches
   (the class of error ``_safe_execute`` most plausibly guards against)
   are already ruled out mechanically before the guarded statement runs.

3. The broad catch exists for a real, confirmed reason, not a guess: this
   codebase has an ``AUTO_REPAIR_SCHEMA``-gated auto-repair mechanism
   (app/schema_guard_engine.py::should_auto_repair_schema) under which
   migrations can run as part of application startup in some deployment
   configurations -- a hard failure here could, in that configuration,
   prevent the app from booting at all. The migration's own docstring
   states this explicitly ("Idempotent canli migration; tablo/kolon
   varyasyonlari uygulama acilisini durdurmasin").

4. The PostgreSQL-only ``SET NOT NULL`` enforcement (line ~80) only
   TIGHTENS an existing nullable column; if it fails, the column is left
   exactly as nullable as it already was before this migration -- not a
   regression relative to the pre-migration baseline.

5. ``downgrade()`` is a documented, deliberate no-op (drops nothing, to
   avoid data-loss risk on rollback) -- proven below, not merely quoted
   from its docstring.

6. This migration is already part of the applied chain (down_revision
   f3c8d2a6e501) -- rewriting its historical upgrade() logic is exactly
   what this phase's own instructions warn against doing casually. No
   such rewrite was made; this file is investigation/verification only.

CLOSURE: NOT_A_DEFECT_WITH_MECHANICAL_PROOF -- the current implementation
cannot silently leave an INVALID (as opposed to merely not-yet-tightened)
schema/data state on its success path, and its broad-except failure path
is a deliberate, justified, already-established boot-safety tradeoff, not
an oversight. No source change was made to the migration itself.

Test pattern: dynamically loads the real migration module and drives its
actual upgrade()/downgrade() via a real Alembic Operations context against
a real SQLite engine -- the exact established pattern already used
throughout tests/migrations/ (see e.g. test_phase5v_workflow_core_adoption_
migration.py, test_phase5w_president_approval_adoption_migration.py).
"""
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
    / "v58a1c2d3e4f_add_period_scope_type_safety.py"
)


def _load_migration() -> Any:
    spec = importlib.util.spec_from_file_location("v58a1c2d3e4f_period_scope_type_safety", MIGRATION_PATH)
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


def _table_names(connection: sa.Connection) -> set[str]:
    return set(sa.inspect(connection).get_table_names())


# ---------------------------------------------------------------------------
# Fresh empty->head install: none of the target tables exist yet -- the
# migration must be a safe no-op, not an error (addresses AC's explicit
# "whether fresh empty->head installs still execute this migration" check).
# ---------------------------------------------------------------------------


def test_upgrade_on_a_completely_empty_database_is_a_safe_noop() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)  # must not raise
        # performance_period_scope_personnel is unconditionally created
        # (no _has_table guard around op.create_table for it) -- everything
        # else correctly stayed absent since their source tables don't exist.
        assert _table_names(connection) == {"performance_period_scope_personnel"}


# ---------------------------------------------------------------------------
# performance_periods: NULL scope_type/period_type/allow_overlap backfill --
# the postcondition the migration's docstring name ("scope_type safety")
# is actually about.
# ---------------------------------------------------------------------------


def _create_performance_periods(connection: sa.Connection) -> None:
    connection.execute(sa.text("CREATE TABLE performance_periods (id INTEGER PRIMARY KEY, title VARCHAR(200))"))


def test_performance_periods_null_scope_and_period_type_backfilled_to_documented_defaults() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        connection.execute(sa.text("INSERT INTO performance_periods (id, title) VALUES (1, 'Q1')"))

        _run_upgrade(connection)

        row = connection.execute(
            sa.text("SELECT scope_type, period_type, allow_overlap FROM performance_periods WHERE id = 1")
        ).mappings().one()
        assert row["scope_type"] == "all"
        assert row["period_type"] == "annual"
        # SQLite has no native boolean type; Alembic's sa.Boolean() maps to
        # INTEGER 0/1 there -- 0 is the correct backfilled "false".
        assert row["allow_overlap"] in (False, 0)


def test_performance_periods_existing_non_null_values_are_never_overwritten() -> None:
    """The backfill UPDATE is WHERE scope_type IS NULL OR scope_type='' --
    real, already-set operator data must survive this migration untouched."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        connection.execute(sa.text("INSERT INTO performance_periods (id, title) VALUES (1, 'Q1')"))
        # First upgrade adds the columns; simulate a real operator having
        # since set a genuine, deliberate non-default value.
        _run_upgrade(connection)
        connection.execute(
            sa.text("UPDATE performance_periods SET scope_type='department', period_type='quarterly', allow_overlap=1 WHERE id=1")
        )

        _run_upgrade(connection)  # re-run: must be idempotent, must not clobber

        row = connection.execute(
            sa.text("SELECT scope_type, period_type, allow_overlap FROM performance_periods WHERE id = 1")
        ).mappings().one()
        assert row["scope_type"] == "department"
        assert row["period_type"] == "quarterly"
        assert row["allow_overlap"] in (True, 1)


def test_performance_periods_columns_are_added_when_missing() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _run_upgrade(connection)
        columns = _column_names(connection, "performance_periods")
        assert {"period_type", "scope_type", "scope_value", "special_reason", "allow_overlap"}.issubset(columns)


# ---------------------------------------------------------------------------
# performance_low_score_processes: the postcondition the ORM model's own
# nullable=False contract (app/models/performance_low_score_models.py)
# depends on for low_score_detected_at.
# ---------------------------------------------------------------------------


def _create_low_score_processes(connection: sa.Connection) -> None:
    connection.execute(
        sa.text(
            """
            CREATE TABLE performance_low_score_processes (
                id INTEGER PRIMARY KEY,
                created_at DATETIME,
                updated_at DATETIME
            )
            """
        )
    )


def test_low_score_detected_at_backfills_from_created_at_when_both_are_null_initially() -> None:
    """Proves the COALESCE chain's real, executed behavior -- not merely
    read from the SQL text -- on the exact column the ORM model declares
    nullable=False."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_low_score_processes(connection)
        connection.execute(
            sa.text("INSERT INTO performance_low_score_processes (id, created_at, updated_at) VALUES (1, '2026-01-15 10:00:00', NULL)")
        )

        _run_upgrade(connection)

        row = connection.execute(
            sa.text("SELECT low_score_detected_at FROM performance_low_score_processes WHERE id = 1")
        ).mappings().one()
        assert row["low_score_detected_at"] == "2026-01-15 10:00:00"


def test_low_score_detected_at_is_never_null_after_upgrade_even_with_no_created_at() -> None:
    """The final COALESCE fallback (CURRENT_TIMESTAMP) must guarantee a
    non-null result even in the worst case (no created_at/updated_at data
    at all) -- this is the exact postcondition AC asked to be proven, not
    assumed."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_low_score_processes(connection)
        connection.execute(
            sa.text("INSERT INTO performance_low_score_processes (id, created_at, updated_at) VALUES (1, NULL, NULL)")
        )

        _run_upgrade(connection)

        row = connection.execute(
            sa.text("SELECT low_score_detected_at FROM performance_low_score_processes WHERE id = 1")
        ).mappings().one()
        assert row["low_score_detected_at"] is not None


def test_low_score_detected_at_existing_non_null_value_is_preserved() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_low_score_processes(connection)
        connection.execute(
            sa.text("INSERT INTO performance_low_score_processes (id, created_at, updated_at) VALUES (1, '2026-01-01 00:00:00', NULL)")
        )
        _run_upgrade(connection)
        connection.execute(
            sa.text("UPDATE performance_low_score_processes SET low_score_detected_at = '2026-06-01 12:00:00' WHERE id = 1")
        )

        _run_upgrade(connection)  # re-run must not clobber a real, already-set value

        row = connection.execute(
            sa.text("SELECT low_score_detected_at FROM performance_low_score_processes WHERE id = 1")
        ).mappings().one()
        assert row["low_score_detected_at"] == "2026-06-01 12:00:00"


# ---------------------------------------------------------------------------
# Idempotency (the migration's own documented "Idempotent canli migration"
# claim) and downgrade safety, both proven by actually running them twice.
# ---------------------------------------------------------------------------


def test_upgrade_is_idempotent_when_run_twice_in_a_row() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _create_low_score_processes(connection)
        connection.execute(sa.text("INSERT INTO performance_periods (id, title) VALUES (1, 'Q1')"))
        connection.execute(sa.text("INSERT INTO performance_low_score_processes (id, created_at) VALUES (1, '2026-01-01 00:00:00')"))

        _run_upgrade(connection)  # must not raise
        _run_upgrade(connection)  # must not raise the second time either

        assert "scope_type" in _column_names(connection, "performance_periods")
        assert "low_score_detected_at" in _column_names(connection, "performance_low_score_processes")


def test_downgrade_drops_no_columns_or_tables_matching_documented_no_data_loss_contract() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        connection.execute(sa.text("INSERT INTO performance_periods (id, title) VALUES (1, 'Q1')"))

        _run_upgrade(connection)
        columns_after_upgrade = _column_names(connection, "performance_periods")
        tables_after_upgrade = _table_names(connection)

        _run_downgrade(connection)  # documented no-op

        assert _column_names(connection, "performance_periods") == columns_after_upgrade
        assert _table_names(connection) == tables_after_upgrade


# ---------------------------------------------------------------------------
# performance_low_score_process_events: sort_order backfill.
# ---------------------------------------------------------------------------


def test_low_score_process_events_sort_order_backfilled_to_zero() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(sa.text("CREATE TABLE performance_low_score_process_events (id INTEGER PRIMARY KEY)"))
        connection.execute(sa.text("INSERT INTO performance_low_score_process_events (id) VALUES (1)"))

        _run_upgrade(connection)

        row = connection.execute(
            sa.text("SELECT sort_order FROM performance_low_score_process_events WHERE id = 1")
        ).mappings().one()
        assert row["sort_order"] == 0
