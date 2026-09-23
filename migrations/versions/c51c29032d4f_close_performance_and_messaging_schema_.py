"""Close performance/messaging schema-contract drift (adopt into Alembic).

Revision ID: c51c29032d4f
Revises: 10858a18e9ac
Create Date: 2026-08-25

app/bootstrap/schema_contract.py's ``get_expected_schema()`` (the contract
``app/bootstrap/schema_validation.py`` enforces at boot when
``STRICT_SCHEMA_CHECK`` is on -- the default for APP_ENV in
{production, staging}, see config.py) requires 15 columns across four
tables that no migration in this chain has ever created:

  performance_evaluations: employee_score_viewed_at,
    employee_score_acknowledged_at, employee_score_acknowledged_note,
    workflow_status, level_1_submitted_to_level_2_at,
    level_2_seen_level_1_at, level_2_returned_to_level_1_at,
    level_2_return_note, level_2_returned_by_id,
    level_1_last_resubmitted_at
  personnel_leaves: performance_mode
  message_threads: badge_label, icon_name, accent_color
  attendance_exceptions: performance_mode

All four tables themselves ARE created earlier in this chain (users:
fae32fb68b1b, personnel_leaves/attendance_exceptions: d2a8c1f9e006,
message_threads: 7c4d9a21b001) -- only these 15 columns are missing. A
database built purely via ``flask db upgrade`` from empty (disaster
recovery restore-from-scratch, or a brand-new environment) reaches head
without them and then fails ``validate_required_schema()`` at boot with
"Şema doğrulama başarısız", listing all 15 as missing columns. Confirmed by
grepping every migration file for each column name: zero matches anywhere
in migrations/versions/ prior to this one.

Root cause: these columns exist in real/legacy databases only because
app/schema_guard_patches.py (SCHEMA_PATCHES) and
app/schema_guard_core_maintenances.py (TABLE_REPAIRS, personnel_leaves and
attendance_exceptions entries) contain raw ``ALTER TABLE ... ADD COLUMN IF
NOT EXISTS`` statements for this exact column set -- a historical
out-of-band DDL mechanism that was never captured as a formal Alembic
migration. That guard only runs at boot when ``AUTO_REPAIR_SCHEMA=True``
(app/startup_checks.py:run_schema_guard_bootstrap), which defaults to
False everywhere including production (config.py:646) and is explicitly
discouraged there ("Canlı ortamda migration sonrası geçici kullanım
dışında önerilmez" -- app/startup_checks.py:93). app/schema_guard.py's own
anchor comment states the intended policy directly: "Üretimde şema
düzeltme akışı otomatik onarım yerine kontrollü migration / db upgrade
süreciyle yürütülmelidir" (production schema fixes should go through
migration/db upgrade, not automatic repair). This migration is what makes
that policy actually true -- it does not touch or replace the schema_guard
safety net (left intact as a legacy/live self-heal fallback for OTHER
databases that skip migrations), it just gives Alembic the same 15 columns
schema_guard has been silently supplying so a fresh chain is self-sufficient.

Column types/defaults mirror both sources exactly, which already agree
with each other: app/models/performance_models.py, app/models/hr_models.py,
app/models/communication_models.py (SQLAlchemy truth used by
schema_validation's `sqlalchemy.inspect`) and the raw DDL strings in
schema_guard_patches.py / schema_guard_core_maintenances.py (real
production column shapes). workflow_status and the two performance_mode
columns are NOT NULL with a server_default, so this migration is safe on
a populated legacy table too: existing rows are backfilled to the same
default value the schema_guard patches already use ('taslak_1_amir',
'partial') in the same ADD COLUMN statement, in one atomic step -- no
separate backfill/UPDATE pass is needed because these are simple constant
defaults, not computed ones.

Idempotent for both starting states this repository's chain has to
tolerate (no reliable way to know in advance which a given target
database is in -- same reasoning as 10858a18e9ac and 3a9d2f1c8b70):

  A) Fresh database, upgraded head-to-head through this chain: none of
     the 15 columns exist yet. This migration adds them.

  B) Legacy/live-style database where schema_guard's raw-SQL patches (or
     manual DBA intervention) already added some/all of these columns in
     the past: each ADD COLUMN is guarded by an inspector column-existence
     check first, so an already-present column is left untouched -- no
     duplicate-column error, no data touched, no-op for that column.

level_2_returned_by_id gets a real FK constraint to users.id (matching
app/models/performance_models.py's ``db.ForeignKey("users.id")``), added
as a separate guarded step after the column exists -- SQLite's ALTER TABLE
cannot add a named FK constraint after the fact, so that step is skipped
on SQLite (mirrors the existing precedent in
2f6c1e9a2b30_add_personnel_categories_phase2.py for the identical
constraint-portability reason).

Downgrade policy: intentionally a no-op, matching this project's own
established convention for adopted/self-healed columns that may carry
real institutional data on legacy databases (see 29fee38a97e1 and
10858a18e9ac's downgrade docstrings for the identical reasoning). A
production performance_evaluations or personnel_leaves table can hold
years of live scoring/workflow/leave data; a destructive downgrade that
dropped these columns could erase it with no way back. Rolling back this
migration on a fresh/dev database just leaves the 15 columns in place,
which is harmless (matches the schema_guard-patched shape every existing
environment already has).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c51c29032d4f"
down_revision = "10858a18e9ac"
branch_labels = None
depends_on = None


def _has_table(bind, table_name: str) -> bool:
    return table_name in sa.inspect(bind).get_table_names()


def _has_column(bind, table_name: str, column_name: str) -> bool:
    if not _has_table(bind, table_name):
        return False
    return column_name in {c["name"] for c in sa.inspect(bind).get_columns(table_name)}


def _has_fk_on_column(bind, table_name: str, column_name: str, referred_table: str) -> bool:
    """True if ANY foreign key (any name) already ties column_name to referred_table.

    Checked by (column, target table) rather than by this migration's own
    constraint name, because a legacy database may already carry an
    equivalent constraint under a different name (e.g. hand-applied DBA
    DDL, or a name Postgres auto-generated). Guarding on name alone would
    add a second, redundant constraint instead of recognizing the column
    is already properly linked.
    """
    if not _has_table(bind, table_name):
        return False
    for fk in sa.inspect(bind).get_foreign_keys(table_name):
        if column_name in (fk.get("constrained_columns") or []) and fk.get("referred_table") == referred_table:
            return True
    return False


def _add_column_if_missing(bind, table_name: str, column: sa.Column) -> None:
    if not _has_table(bind, table_name):
        return
    if _has_column(bind, table_name, column.name):
        return
    op.add_column(table_name, column)


def upgrade() -> None:
    bind = op.get_bind()

    # -- performance_evaluations ------------------------------------------------
    _add_column_if_missing(
        bind, "performance_evaluations",
        sa.Column("workflow_status", sa.String(length=50), nullable=False, server_default=sa.text("'taslak_1_amir'")),
    )
    _add_column_if_missing(bind, "performance_evaluations", sa.Column("level_1_submitted_to_level_2_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(bind, "performance_evaluations", sa.Column("level_2_seen_level_1_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(bind, "performance_evaluations", sa.Column("level_2_returned_to_level_1_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(bind, "performance_evaluations", sa.Column("level_2_return_note", sa.Text(), nullable=True))
    _add_column_if_missing(bind, "performance_evaluations", sa.Column("level_2_returned_by_id", sa.Integer(), nullable=True))
    _add_column_if_missing(bind, "performance_evaluations", sa.Column("level_1_last_resubmitted_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(bind, "performance_evaluations", sa.Column("employee_score_viewed_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(bind, "performance_evaluations", sa.Column("employee_score_acknowledged_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(bind, "performance_evaluations", sa.Column("employee_score_acknowledged_note", sa.Text(), nullable=True))

    if _has_table(bind, "performance_evaluations"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_performance_evaluations_workflow_status "
            "ON performance_evaluations (workflow_status)"
        )

        if bind.dialect.name != "sqlite" and not _has_fk_on_column(bind, "performance_evaluations", "level_2_returned_by_id", "users"):
            op.create_foreign_key(
                "fk_performance_evaluations_level_2_returned_by_id",
                "performance_evaluations",
                "users",
                ["level_2_returned_by_id"],
                ["id"],
            )

    # -- personnel_leaves ---------------------------------------------------
    _add_column_if_missing(
        bind, "personnel_leaves",
        sa.Column("performance_mode", sa.String(length=20), nullable=False, server_default=sa.text("'partial'")),
    )
    if _has_table(bind, "personnel_leaves"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_personnel_leaves_performance_mode "
            "ON personnel_leaves (performance_mode)"
        )

    # -- attendance_exceptions -----------------------------------------------
    _add_column_if_missing(
        bind, "attendance_exceptions",
        sa.Column("performance_mode", sa.String(length=20), nullable=False, server_default=sa.text("'partial'")),
    )
    if _has_table(bind, "attendance_exceptions"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_attendance_exceptions_performance_mode "
            "ON attendance_exceptions (performance_mode)"
        )

    # -- message_threads ------------------------------------------------------
    _add_column_if_missing(bind, "message_threads", sa.Column("badge_label", sa.String(length=120), nullable=True))
    _add_column_if_missing(bind, "message_threads", sa.Column("icon_name", sa.String(length=100), nullable=True))
    _add_column_if_missing(bind, "message_threads", sa.Column("accent_color", sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Intentional no-op.

    See the module docstring's "Downgrade policy" section: this mirrors the
    project's own established convention (29fee38a97e1, 10858a18e9ac) for
    adopted/self-healed columns that may already hold real institutional
    data on legacy or production databases.
    """
