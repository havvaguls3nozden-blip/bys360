"""Add DB-level single-active-PerformancePeriod invariant (BYS360 DEFECT AD).

Revision ID: v1a2d3e4f5b6
Revises: c51c29032d4f
Create Date: 2026-09-02

BYS360_DEFECT_AD_CONCURRENCY_RISK
==================================
Every code path that activates a PerformancePeriod (admin_core_routes.py's
performance_period_toggle_active, v2_1_6_category_period_integration.py's
create_or_update_period_from_plan -- BYS360 DEFECT W already fixed both to
correctly deactivate every OTHER period as part of the same activation) only
enforces "at most one active period" at the APPLICATION level, inside a
single ORM session/transaction. Nothing in the schema itself stops two
concurrent transactions from each reading "no conflicting active period yet"
and both committing their own row with is_active=true -- the classic
check-then-act race, invisible to any test that exercises one transaction
at a time. This migration adds the missing DB-level guarantee: a partial
unique index on performance_periods(is_active) WHERE is_active is true, so
the database itself -- not just careful call-site ordering -- refuses a
second concurrently-committed active row.

Pre-migration cleanup (winner-selection): a database that has ALREADY
accumulated more than one is_active=true row (possible today, precisely
because nothing has ever stopped it) cannot have this unique index created
directly -- CREATE UNIQUE INDEX would fail against existing duplicate
values. Before creating the index, any such pre-existing violation is
resolved deterministically by keeping exactly one winner and deactivating
the rest. The winner is chosen with the EXACT SAME ordering the app's own
get_active_period() (app/services/performance/common.py) already uses --
ORDER BY start_date DESC, id DESC, LIMIT 1 -- so this migration does not
invent new business policy; it just makes the schema agree, in advance,
with which row the application would already have treated as "the" active
period on read. On a database with zero or one active period (the expected,
already-invariant-respecting case for any environment that only went
through the W-fixed code paths) this cleanup step is a complete no-op.

DB-level mechanism note: a partial unique index (not a CHECK constraint,
not a trigger) is used because it is supported identically -- same
CREATE UNIQUE INDEX ... WHERE ... syntax -- on both PostgreSQL and SQLite
(SQLite has supported partial indexes since 3.8.0, and app/config.py's
own SQLite setup already assumes a modern bundled sqlite3), keeping this
migration's dual-database contract as simple as a single dialect-branched
literal for the boolean comparison (Postgres: true / SQLite: 1), matching
the existing precedent elsewhere in this chain for boolean SQL literals.

Downgrade: safe and fully reversible -- DROP INDEX only. No column was
added and no data was transformed destructively (the pre-clean step turns
is_active=true rows into is_active=false for losing rows only when a
genuine pre-existing multi-active violation existed, which is itself a
data-integrity bug being fixed, not intended state being discarded).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "v1a2d3e4f5b6"
down_revision = "c51c29032d4f"
branch_labels = None
depends_on = None

_INDEX_NAME = "uq_performance_periods_single_active"
_TABLE = "performance_periods"


def _has_table(bind, table_name: str) -> bool:
    return table_name in sa.inspect(bind).get_table_names()


def _has_index(bind, table_name: str, index_name: str) -> bool:
    if not _has_table(bind, table_name):
        return False
    return any(ix["name"] == index_name for ix in sa.inspect(bind).get_indexes(table_name))


def _preclean_multiple_active_periods(bind) -> None:
    """Deterministically resolve any pre-existing multi-active violation.

    Mirrors get_active_period()'s own winner ordering exactly (start_date
    DESC, id DESC) so the schema-level cleanup agrees with what the
    application already treats as "the" active period. No-op when zero or
    one row currently has is_active=true.
    """
    active_ids = [
        row[0]
        for row in bind.execute(
            sa.text(f"SELECT id FROM {_TABLE} WHERE is_active = :flag ORDER BY start_date DESC, id DESC"),
            {"flag": True if bind.dialect.name != "sqlite" else 1},
        )
    ]
    if len(active_ids) <= 1:
        return
    loser_ids = active_ids[1:]
    bind.execute(
        sa.text(f"UPDATE {_TABLE} SET is_active = :off WHERE id IN :loser_ids").bindparams(
            sa.bindparam("loser_ids", expanding=True)
        ),
        {"off": False if bind.dialect.name != "sqlite" else 0, "loser_ids": loser_ids},
    )


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_table(bind, _TABLE):
        return

    _preclean_multiple_active_periods(bind)

    if _has_index(bind, _TABLE, _INDEX_NAME):
        return

    active_literal = "true" if bind.dialect.name != "sqlite" else "1"
    op.execute(
        f"CREATE UNIQUE INDEX {_INDEX_NAME} ON {_TABLE} (is_active) WHERE is_active = {active_literal}"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_table(bind, _TABLE):
        return
    if not _has_index(bind, _TABLE, _INDEX_NAME):
        return
    op.execute(f"DROP INDEX {_INDEX_NAME}")
