"""BYS360_DEFECT_AD_CONCURRENCY_RISK migration proof.

Drives the real migrations/versions/v1a2d3e4f5b6_add_performance_period_
single_active_constraint.py upgrade()/downgrade() against a real SQLite
engine (same established pattern as
tests/migrations/test_v58a1c2d3e4f_period_scope_type_safety_migration.py),
proving:

1. A completely empty database (no performance_periods table yet) upgrades
   as a safe no-op -- matters for a fresh empty->head install where this
   migration runs before any data exists.
2. Zero active periods: upgrade succeeds, creates the index, no rows
   touched.
3. Exactly one active period: upgrade succeeds, that period stays active,
   the index exists.
4. Multiple pre-existing active periods (the actual bug this migration
   closes -- possible today because nothing has ever enforced this at the
   DB level): upgrade deterministically keeps exactly the winner
   get_active_period() would already have picked (ORDER BY start_date
   DESC, id DESC) and deactivates every other row, THEN creates the index
   -- proving the pre-clean step actually runs before index creation, not
   after (an index creation on a still-violating table would raise here,
   so a passing test IS the proof).
5. After upgrade, the unique index actually rejects a second concurrently
   inserted active row -- the real DB-level guarantee AD exists to add,
   not just "an index was created."
6. downgrade() drops only the index -- table and data are untouched.

A second, independent, one-time-only real-PostgreSQL verification (created
and dropped a throwaway database, not part of the permanent suite) is
described in the AA-AH final report rather than encoded here, matching the
pattern already established for Defects AB and AC in this same phase.
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
    / "v1a2d3e4f5b6_add_performance_period_single_active_constraint.py"
)

_INDEX_NAME = "uq_performance_periods_single_active"


def _load_migration() -> Any:
    spec = importlib.util.spec_from_file_location(
        "v1a2d3e4f5b6_add_performance_period_single_active_constraint", MIGRATION_PATH
    )
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


def _table_names(connection: sa.Connection) -> set[str]:
    return set(sa.inspect(connection).get_table_names())


def _index_names(connection: sa.Connection, table_name: str) -> set[str]:
    return {str(ix["name"]) for ix in sa.inspect(connection).get_indexes(table_name)}


def _create_performance_periods(connection: sa.Connection) -> None:
    connection.execute(
        sa.text(
            "CREATE TABLE performance_periods ("
            "id INTEGER PRIMARY KEY, title VARCHAR(200), "
            "start_date DATE, is_active BOOLEAN NOT NULL DEFAULT 0)"
        )
    )


def _insert_period(connection: sa.Connection, period_id: int, start_date: str, is_active: bool) -> None:
    connection.execute(
        sa.text(
            "INSERT INTO performance_periods (id, title, start_date, is_active) "
            "VALUES (:id, :title, :start_date, :is_active)"
        ),
        {"id": period_id, "title": f"P{period_id}", "start_date": start_date, "is_active": 1 if is_active else 0},
    )


def _active_ids(connection: sa.Connection) -> list[int]:
    rows = connection.execute(
        sa.text("SELECT id FROM performance_periods WHERE is_active = 1 ORDER BY id")
    ).fetchall()
    return [row[0] for row in rows]


# ---------------------------------------------------------------------------
# Fresh empty->head install
# ---------------------------------------------------------------------------


def test_upgrade_on_a_completely_empty_database_is_a_safe_noop() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)  # must not raise
        assert _table_names(connection) == set()


# ---------------------------------------------------------------------------
# Zero / one active period -- already-invariant-respecting states
# ---------------------------------------------------------------------------


def test_upgrade_with_zero_active_periods_creates_index_and_touches_no_rows() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _insert_period(connection, 1, "2026-01-01", is_active=False)
        _insert_period(connection, 2, "2026-02-01", is_active=False)

        _run_upgrade(connection)

        assert _INDEX_NAME in _index_names(connection, "performance_periods")
        assert _active_ids(connection) == []


def test_upgrade_with_exactly_one_active_period_leaves_it_active() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _insert_period(connection, 1, "2026-01-01", is_active=False)
        _insert_period(connection, 2, "2026-02-01", is_active=True)

        _run_upgrade(connection)

        assert _INDEX_NAME in _index_names(connection, "performance_periods")
        assert _active_ids(connection) == [2]


# ---------------------------------------------------------------------------
# Pre-existing multiple-active-period violation -- the actual bug AD closes
# ---------------------------------------------------------------------------


def test_upgrade_with_multiple_active_periods_deterministically_keeps_the_get_active_period_winner() -> None:
    """Winner must match get_active_period()'s own ordering: start_date DESC,
    id DESC. Period 3 (latest start_date) must survive; 1 and 2 deactivated."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _insert_period(connection, 1, "2026-01-01", is_active=True)
        _insert_period(connection, 2, "2026-02-01", is_active=True)
        _insert_period(connection, 3, "2026-03-01", is_active=True)

        _run_upgrade(connection)  # would raise on index creation if pre-clean didn't run first

        assert _active_ids(connection) == [3]
        assert _INDEX_NAME in _index_names(connection, "performance_periods")


def test_upgrade_winner_tiebreak_uses_highest_id_when_start_dates_tie() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _insert_period(connection, 5, "2026-06-01", is_active=True)
        _insert_period(connection, 7, "2026-06-01", is_active=True)

        _run_upgrade(connection)

        assert _active_ids(connection) == [7]


def test_upgrade_is_idempotent_when_run_twice() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _insert_period(connection, 1, "2026-01-01", is_active=True)
        _insert_period(connection, 2, "2026-02-01", is_active=True)

        _run_upgrade(connection)
        _run_upgrade(connection)  # must not raise (index-exists guard)

        assert _active_ids(connection) == [2]


# ---------------------------------------------------------------------------
# The actual DB-level guarantee: a second active row is now rejected
# ---------------------------------------------------------------------------


def test_index_rejects_a_second_concurrently_inserted_active_row() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _insert_period(connection, 1, "2026-01-01", is_active=True)

        _run_upgrade(connection)

        with __import__("pytest").raises(sa.exc.IntegrityError):
            _insert_period(connection, 2, "2026-02-01", is_active=True)


def test_index_still_allows_multiple_inactive_rows() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _insert_period(connection, 1, "2026-01-01", is_active=True)

        _run_upgrade(connection)

        _insert_period(connection, 2, "2026-02-01", is_active=False)
        _insert_period(connection, 3, "2026-03-01", is_active=False)
        assert _active_ids(connection) == [1]


# ---------------------------------------------------------------------------
# downgrade(): drops only the index
# ---------------------------------------------------------------------------


def test_downgrade_drops_only_the_index_leaving_table_and_data_intact() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _insert_period(connection, 1, "2026-01-01", is_active=True)

        _run_upgrade(connection)
        assert _INDEX_NAME in _index_names(connection, "performance_periods")

        _run_downgrade(connection)

        assert _INDEX_NAME not in _index_names(connection, "performance_periods")
        assert _table_names(connection) == {"performance_periods"}
        assert _active_ids(connection) == [1]

        # And a second active row can now be inserted again post-downgrade,
        # confirming the constraint really is gone (not merely renamed).
        _insert_period(connection, 2, "2026-02-01", is_active=True)
        assert _active_ids(connection) == [1, 2]


def test_downgrade_on_a_database_that_never_had_the_index_is_a_safe_noop() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_performance_periods(connection)
        _run_downgrade(connection)  # must not raise
        assert _table_names(connection) == {"performance_periods"}
