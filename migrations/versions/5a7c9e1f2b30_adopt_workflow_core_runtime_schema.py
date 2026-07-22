"""Adopt workflow core runtime schema into Alembic ownership.

Revision ID: 5a7c9e1f2b30
Revises: bys360_portal_v2121
Create Date: 2026-07-22 19:30:00

This migration is deliberately idempotent because the workflow tables may
already exist in installations where the legacy application-level
``ensure_tables`` helper created them. Existing rows are preserved; only the
known Phase 3 compatibility columns and required indexes are added.
"""

from __future__ import annotations

from collections.abc import Iterable

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "5a7c9e1f2b30"
down_revision = "bys360_portal_v2121"
branch_labels = None
depends_on = None


_JSON_TYPE = postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def _table_exists(bind: sa.engine.Connection, table_name: str) -> bool:
    return table_name in sa.inspect(bind).get_table_names()


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _table_exists(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def _index_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _table_exists(bind, table_name):
        return set()
    return {index["name"] for index in sa.inspect(bind).get_indexes(table_name) if index.get("name")}


def _add_missing_columns(
    bind: sa.engine.Connection,
    table_name: str,
    columns: Iterable[sa.Column],
) -> None:
    existing = _column_names(bind, table_name)
    for column in columns:
        if column.name not in existing:
            op.add_column(table_name, column)
            existing.add(column.name)


def _create_index_if_missing(
    bind: sa.engine.Connection,
    index_name: str,
    table_name: str,
    columns: list[str],
) -> None:
    if index_name not in _index_names(bind, table_name):
        op.create_index(index_name, table_name, columns, unique=False)


def _create_workflow_instances(bind: sa.engine.Connection) -> None:
    if not _table_exists(bind, "workflow_instances"):
        op.create_table(
            "workflow_instances",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("module", sa.String(length=80), nullable=False),
            sa.Column("entity_type", sa.String(length=120), nullable=True),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("subject_user_id", sa.Integer(), nullable=True),
            sa.Column("period_id", sa.Integer(), nullable=True),
            sa.Column("score", sa.Numeric(8, 2), nullable=True),
            sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'ACTIVE'")),
            sa.Column("current_step_name", sa.String(length=255), nullable=True),
            sa.Column("priority", sa.String(length=30), nullable=False, server_default=sa.text("'NORMAL'")),
            sa.Column("workflow_family", sa.String(length=80), nullable=True, server_default=sa.text("'GENERAL'")),
            sa.Column("delayed_step_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("payload_json", _JSON_TYPE, nullable=True),
        )
    else:
        _add_missing_columns(
            bind,
            "workflow_instances",
            (
                sa.Column("workflow_family", sa.String(length=80), nullable=True, server_default=sa.text("'GENERAL'")),
                sa.Column("delayed_step_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            ),
        )

    _create_index_if_missing(
        bind,
        "ix_workflow_instances_module_status",
        "workflow_instances",
        ["module", "status"],
    )
    _create_index_if_missing(
        bind,
        "ix_workflow_instances_subject_period",
        "workflow_instances",
        ["subject_user_id", "period_id"],
    )


def _create_workflow_steps(bind: sa.engine.Connection) -> None:
    if not _table_exists(bind, "workflow_steps"):
        op.create_table(
            "workflow_steps",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "workflow_id",
                sa.Integer(),
                sa.ForeignKey("workflow_instances.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("step_order", sa.Integer(), nullable=False),
            sa.Column("step_code", sa.String(length=80), nullable=True),
            sa.Column("step_type", sa.String(length=40), nullable=True),
            sa.Column("step_name", sa.String(length=255), nullable=False),
            sa.Column("assigned_user_id", sa.Integer(), nullable=True),
            sa.Column("visible_to_user_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'PENDING'")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("started_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("due_at", sa.DateTime(), nullable=True),
            sa.Column("duration_minutes", sa.Integer(), nullable=True),
            sa.Column("delay_state", sa.String(length=30), nullable=False, server_default=sa.text("'NORMAL'")),
            sa.Column("delay_days", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
            sa.Column("escalation_level", sa.String(length=30), nullable=False, server_default=sa.text("'NONE'")),
            sa.Column("last_reminded_at", sa.DateTime(), nullable=True),
            sa.Column("reminder_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("notification_status", sa.String(length=30), nullable=False, server_default=sa.text("'READY'")),
            sa.Column("note", sa.Text(), nullable=True),
        )
    else:
        _add_missing_columns(
            bind,
            "workflow_steps",
            (
                sa.Column("step_type", sa.String(length=40), nullable=True),
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
                sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
                sa.Column("delay_state", sa.String(length=30), nullable=False, server_default=sa.text("'NORMAL'")),
                sa.Column("visible_to_user_id", sa.Integer(), nullable=True),
                sa.Column("delay_days", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
                sa.Column("escalation_level", sa.String(length=30), nullable=False, server_default=sa.text("'NONE'")),
                sa.Column("last_reminded_at", sa.DateTime(), nullable=True),
                sa.Column("reminder_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
                sa.Column("notification_status", sa.String(length=30), nullable=False, server_default=sa.text("'READY'")),
            ),
        )

    _create_index_if_missing(
        bind,
        "ix_workflow_steps_workflow_order",
        "workflow_steps",
        ["workflow_id", "step_order"],
    )
    _create_index_if_missing(bind, "ix_workflow_steps_status", "workflow_steps", ["status"])


def _create_workflow_logs(bind: sa.engine.Connection) -> None:
    if not _table_exists(bind, "workflow_logs"):
        op.create_table(
            "workflow_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "workflow_id",
                sa.Integer(),
                sa.ForeignKey("workflow_instances.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("step_id", sa.Integer(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("old_status", sa.String(length=40), nullable=True),
            sa.Column("new_status", sa.String(length=40), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )


def _create_workflow_notifications(bind: sa.engine.Connection) -> None:
    if not _table_exists(bind, "workflow_notifications"):
        op.create_table(
            "workflow_notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "workflow_id",
                sa.Integer(),
                sa.ForeignKey("workflow_instances.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "step_id",
                sa.Integer(),
                sa.ForeignKey("workflow_steps.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column("target_user_id", sa.Integer(), nullable=True),
            sa.Column("notification_type", sa.String(length=80), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'PENDING'")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("delivered_at", sa.DateTime(), nullable=True),
            sa.Column("payload_json", _JSON_TYPE, nullable=True),
        )

    _create_index_if_missing(
        bind,
        "ix_workflow_notifications_status",
        "workflow_notifications",
        ["status"],
    )
    _create_index_if_missing(
        bind,
        "ix_workflow_notifications_target",
        "workflow_notifications",
        ["target_user_id", "status"],
    )


def upgrade() -> None:
    bind = op.get_bind()
    _create_workflow_instances(bind)
    _create_workflow_steps(bind)
    _create_workflow_logs(bind)
    _create_workflow_notifications(bind)


def downgrade() -> None:
    """Preserve adopted runtime tables and their data.

    The migration cannot safely know whether each table existed before Alembic
    ownership was introduced. A destructive downgrade could therefore remove
    live institutional records. Downgrade is intentionally a no-op.
    """
