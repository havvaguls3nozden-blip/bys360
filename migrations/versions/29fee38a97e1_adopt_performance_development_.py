"""Adopt performance development recommendations table into Alembic ownership.

Revision ID: 29fee38a97e1
Revises: b704bd9d68c0
Create Date: 2026-07-22 22:10:42.612687

The ``performance_development_recommendations`` table is currently
self-healed at request time by
``app/performance/phase10_development_guidance_ui.py``'s
``ensure_phase10_recommendation_table()`` (dialect-branched raw
``CREATE TABLE IF NOT EXISTS`` followed by an ``ALTER TABLE ADD COLUMN``
loop for any column still missing). This migration is a deliberately
cautious, migration-only first step, mirroring the approach taken for
``mobile_push_tokens`` in ``b704bd9d68c0``: it adopts the table into Alembic
ownership without changing the runtime self-heal helper, which is removed in
a later package. The column list below is the union of the runtime helper's
PostgreSQL ``create_sql`` and ``alter_defs`` (both describe the same 47
columns, including the primary key). One inconsistency was found between
those two runtime dicts: ``recommendation_text`` is declared
``TEXT NOT NULL`` in ``create_sql`` but ``"TEXT NULL"`` in ``alter_defs``.
This is not a live discrepancy -- ``recommendation_text`` is only ever
created via the initial ``CREATE TABLE`` (the same request always supplies
it, so the ``ALTER TABLE`` retrofit path for it is dead code in practice) --
so this migration takes the ``CREATE TABLE`` definition, ``NOT NULL``, as
authoritative. No unique constraint exists on this table in the runtime
source, so no duplicate-guard logic is needed. Column types below are
dialect-neutral SQLAlchemy types; SQLAlchemy already emits the correct SQL
per dialect (SQLite ``INTEGER``/``TEXT`` vs PostgreSQL ``BOOLEAN``/
``VARCHAR``/``TIMESTAMP``), so no SQLite/PostgreSQL branching is needed.
"""

from __future__ import annotations

import logging

import sqlalchemy as sa
from alembic import op

revision = "29fee38a97e1"
down_revision = "b704bd9d68c0"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

_TABLE_NAME = "performance_development_recommendations"


def _table_exists(bind: sa.engine.Connection, table_name: str) -> bool:
    return table_name in sa.inspect(bind).get_table_names()


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _table_exists(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def _create_table() -> None:
    op.create_table(
        _TABLE_NAME,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("employee_name", sa.Text(), nullable=True),
        sa.Column("period_id", sa.Integer(), nullable=True),
        sa.Column("period_name", sa.Text(), nullable=True),
        sa.Column(
            "recommendation_type",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'development'"),
        ),
        sa.Column(
            "development_area",
            sa.String(length=80),
            nullable=False,
            server_default=sa.text("'job_quality'"),
        ),
        sa.Column(
            "priority",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'normal'"),
        ),
        sa.Column(
            "follow_status",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'not_started'"),
        ),
        sa.Column(
            "follow_frequency",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'monthly'"),
        ),
        sa.Column(
            "visibility_scope",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'internal'"),
        ),
        sa.Column(
            "publication_status",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column("show_on_scorecard", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("approved_by_hr", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "supervisor_approval_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("supervisor_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "approval_role",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'group_head'"),
        ),
        sa.Column(
            "approval_flow",
            sa.String(length=60),
            nullable=False,
            server_default=sa.text("'group_head_then_hr'"),
        ),
        sa.Column("approver_name", sa.Text(), nullable=True),
        sa.Column("approval_note", sa.Text(), nullable=True),
        sa.Column("publish_lock", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("publish_lock_reason", sa.Text(), nullable=True),
        sa.Column("hr_publish_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hr_publish_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "scorecard_visibility_mode",
            sa.String(length=60),
            nullable=False,
            server_default=sa.text("'internal_only'"),
        ),
        sa.Column(
            "scorecard_detail_level",
            sa.String(length=60),
            nullable=False,
            server_default=sa.text("'summary'"),
        ),
        sa.Column("show_in_pdf", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "show_in_scorecard_history",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "employee_notification_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("employee_ack_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("visibility_reason", sa.Text(), nullable=True),
        sa.Column("employee_message", sa.Text(), nullable=True),
        sa.Column("owner_name", sa.Text(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("basis_note", sa.Text(), nullable=True),
        sa.Column("current_state", sa.Text(), nullable=True),
        sa.Column("target_outcome", sa.Text(), nullable=True),
        sa.Column("smart_goal", sa.Text(), nullable=True),
        sa.Column("action_steps", sa.Text(), nullable=True),
        sa.Column("support_needs", sa.Text(), nullable=True),
        sa.Column("success_criteria", sa.Text(), nullable=True),
        sa.Column("evidence_plan", sa.Text(), nullable=True),
        # NOT NULL per the runtime helper's CREATE TABLE (create_sql); see the
        # module docstring for why alter_defs's "TEXT NULL" is not used here.
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sqlite_autoincrement=True,
    )


_EXPECTED_COLUMNS = {
    "id",
    "employee_id",
    "employee_name",
    "period_id",
    "period_name",
    "recommendation_type",
    "development_area",
    "priority",
    "follow_status",
    "follow_frequency",
    "visibility_scope",
    "publication_status",
    "show_on_scorecard",
    "is_published",
    "approved_by_hr",
    "supervisor_approval_required",
    "supervisor_approved",
    "approval_role",
    "approval_flow",
    "approver_name",
    "approval_note",
    "publish_lock",
    "publish_lock_reason",
    "hr_publish_required",
    "hr_publish_approved",
    "scorecard_visibility_mode",
    "scorecard_detail_level",
    "show_in_pdf",
    "show_in_scorecard_history",
    "employee_notification_required",
    "employee_ack_required",
    "visibility_reason",
    "employee_message",
    "owner_name",
    "target_date",
    "basis_note",
    "current_state",
    "target_outcome",
    "smart_goal",
    "action_steps",
    "support_needs",
    "success_criteria",
    "evidence_plan",
    "recommendation_text",
    "created_by",
    "created_at",
    "updated_at",
}


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, _TABLE_NAME):
        _create_table()
        return

    # The runtime self-heal path in
    # app/performance/phase10_development_guidance_ui.py declares the exact
    # same shape, so no add-missing-column step is required here; this is a
    # lightweight sanity check only.
    missing = _EXPECTED_COLUMNS - _column_names(bind, _TABLE_NAME)
    if missing:
        logger.warning(
            "performance_development_recommendations tablosu zaten var ama "
            "beklenen kolonlar eksik: %s",
            ", ".join(sorted(missing)),
        )


def downgrade() -> None:
    """Preserve the adopted performance_development_recommendations table.

    The migration cannot safely know whether this table existed before
    Alembic ownership was introduced, and live installations may already
    hold published development recommendations shown on employee
    scorecards. A destructive downgrade could therefore erase institutional
    data. Downgrade is intentionally a no-op.
    """
