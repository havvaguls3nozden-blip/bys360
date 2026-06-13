"""BYS360 performans puanlama başlangıç tarihi alanları

Revision ID: 20260521_01_perf_scoring_window
Revises: 
Create Date: 2026-05-21
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260521_01_perf_scoring_window"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col.get("name") == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table = "performance_periods"
    if not _has_table(inspector, table):
        return
    with op.batch_alter_table(table) as batch_op:
        if not _has_column(inspector, table, "scoring_start_date"):
            batch_op.add_column(sa.Column("scoring_start_date", sa.DateTime(), nullable=True))
        if not _has_column(inspector, table, "scoring_end_date"):
            batch_op.add_column(sa.Column("scoring_end_date", sa.DateTime(), nullable=True))
        if not _has_column(inspector, table, "scoring_auto_start_after_period"):
            batch_op.add_column(sa.Column("scoring_auto_start_after_period", sa.Boolean(), nullable=False, server_default=sa.text("true")))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table = "performance_periods"
    if not _has_table(inspector, table):
        return
    with op.batch_alter_table(table) as batch_op:
        for column in ("scoring_auto_start_after_period", "scoring_end_date", "scoring_start_date"):
            if _has_column(inspector, table, column):
                batch_op.drop_column(column)
