"""Adopt workflow president approval schema into Alembic ownership.

Revision ID: 6f2b8c4d1a90
Revises: 5a7c9e1f2b30
Create Date: 2026-07-22 20:30:00

The approval table may already exist because the legacy workflow routes and
performance services created or extended it at request time. This migration
preserves existing rows and adopts the union of the known workflow, Phase 6,
and Phase 7 compatibility columns required by those consumers.
"""

from __future__ import annotations

from collections.abc import Iterable

import sqlalchemy as sa
from alembic import op

revision = "6f2b8c4d1a90"
down_revision = "5a7c9e1f2b30"
branch_labels = None
depends_on = None


_TABLE_NAME = "performance_president_approvals"


def _table_exists(bind: sa.engine.Connection, table_name: str) -> bool:
    return table_name in sa.inspect(bind).get_table_names()


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _table_exists(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def _index_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _table_exists(bind, table_name):
        return set()
    return {
        index["name"]
        for index in sa.inspect(bind).get_indexes(table_name)
        if index.get("name")
    }


def _unique_column_sets(bind: sa.engine.Connection, table_name: str) -> set[tuple[str, ...]]:
    if not _table_exists(bind, table_name):
        return set()
    inspector = sa.inspect(bind)
    unique_sets = {
        tuple(constraint.get("column_names") or ())
        for constraint in inspector.get_unique_constraints(table_name)
    }
    unique_sets.update(
        tuple(index.get("column_names") or ())
        for index in inspector.get_indexes(table_name)
        if index.get("unique")
    )
    return unique_sets


def _add_missing_columns(
    bind: sa.engine.Connection,
    columns: Iterable[sa.Column],
) -> None:
    existing = _column_names(bind, _TABLE_NAME)
    missing = [column for column in columns if column.name not in existing]
    if not missing:
        return

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(_TABLE_NAME, recreate="always") as batch_op:
            for column in missing:
                batch_op.add_column(column)
        return

    for column in missing:
        op.add_column(_TABLE_NAME, column)


def _create_index_if_missing(
    bind: sa.engine.Connection,
    index_name: str,
    columns: list[str],
    *,
    unique: bool = False,
) -> None:
    if index_name not in _index_names(bind, _TABLE_NAME):
        op.create_index(index_name, _TABLE_NAME, columns, unique=unique)


def _has_duplicate_evaluation_ids(bind: sa.engine.Connection) -> bool:
    duplicate = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM performance_president_approvals
            WHERE evaluation_id IS NOT NULL
            GROUP BY evaluation_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).scalar()
    return duplicate is not None


def _create_table() -> None:
    op.create_table(
        _TABLE_NAME,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evaluation_id", sa.Integer(), nullable=True),
        sa.Column("period_id", sa.Integer(), nullable=True),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Numeric(8, 2), nullable=True),
        sa.Column("final_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("status", sa.String(length=80), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column(
            "workflow_id",
            sa.Integer(),
            sa.ForeignKey("workflow_instances.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("flow_id", sa.Integer(), nullable=True),
        sa.Column("requested_by_id", sa.Integer(), nullable=True),
        sa.Column("president_id", sa.Integer(), nullable=True),
        sa.Column("president_user_id", sa.Integer(), nullable=True),
        sa.Column("president_name", sa.String(length=255), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("process_version", sa.String(length=120), nullable=True),
        sa.Column("phase6_low_score_marker", sa.String(length=64), nullable=True),
        sa.Column("publish_lock_label", sa.String(length=160), nullable=True),
        sa.Column("low_score_repeat_level", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, _TABLE_NAME):
        _create_table()
    else:
        _add_missing_columns(
            bind,
            (
                sa.Column("evaluation_id", sa.Integer(), nullable=True),
                sa.Column("period_id", sa.Integer(), nullable=True),
                sa.Column("employee_id", sa.Integer(), nullable=True),
                sa.Column("score", sa.Numeric(8, 2), nullable=True),
                sa.Column("final_score", sa.Numeric(6, 2), nullable=True),
                sa.Column("status", sa.String(length=80), nullable=False, server_default=sa.text("'PENDING'")),
                sa.Column("workflow_id", sa.Integer(), nullable=True),
                sa.Column("flow_id", sa.Integer(), nullable=True),
                sa.Column("requested_by_id", sa.Integer(), nullable=True),
                sa.Column("president_id", sa.Integer(), nullable=True),
                sa.Column("president_user_id", sa.Integer(), nullable=True),
                sa.Column("president_name", sa.String(length=255), nullable=True),
                sa.Column("requested_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
                sa.Column("decided_at", sa.DateTime(), nullable=True),
                sa.Column("decision_note", sa.Text(), nullable=True),
                sa.Column("process_version", sa.String(length=120), nullable=True),
                sa.Column("phase6_low_score_marker", sa.String(length=64), nullable=True),
                sa.Column("publish_lock_label", sa.String(length=160), nullable=True),
                sa.Column("low_score_repeat_level", sa.String(length=32), nullable=True),
                sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
                sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            ),
        )

    _create_index_if_missing(
        bind,
        "ix_perf_pres_approvals_status",
        ["status"],
    )
    _create_index_if_missing(
        bind,
        "ix_perf_phase7_president_eval",
        ["evaluation_id", "status"],
    )

    if (
        ("evaluation_id",) not in _unique_column_sets(bind, _TABLE_NAME)
        and not _has_duplicate_evaluation_ids(bind)
    ):
        _create_index_if_missing(
            bind,
            "uq_perf_pres_approvals_evaluation_id",
            ["evaluation_id"],
            unique=True,
        )


def downgrade() -> None:
    """Preserve the adopted table and institutional approval records."""
