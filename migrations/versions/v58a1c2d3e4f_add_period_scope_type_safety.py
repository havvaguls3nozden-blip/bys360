"""BYS360 v58 period scope_type safety migration

Revision ID: v58a1c2d3e4f
Revises: f3c8d2a6e501
Create Date: 2026-05-04 18:58:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "v58a1c2d3e4f"
down_revision = "f3c8d2a6e501"
branch_labels = None
depends_on = None


def _has_table(bind, table_name: str) -> bool:
    try:
        return table_name in sa.inspect(bind).get_table_names()
    except Exception:
        return False


def _has_column(bind, table_name: str, column_name: str) -> bool:
    try:
        return column_name in {c["name"] for c in sa.inspect(bind).get_columns(table_name)}
    except Exception:
        return False


def _add_column_if_missing(bind, table_name: str, column: sa.Column) -> None:
    if not _has_table(bind, table_name):
        return
    if _has_column(bind, table_name, column.name):
        return
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.add_column(column)


def _safe_execute(bind, sql: str) -> None:
    try:
        bind.execute(sa.text(sql))
    except Exception:
        # İdempotent canlı migration; tablo/kolon varyasyonları uygulama açılışını durdurmasın.
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (migrations/versions/v58a1c2d3e4f_add_period_scope_type_safety.py:47)")


def upgrade() -> None:
    bind = op.get_bind()

    for table_name in ("performance_periods", "performance_evaluation_periods"):
        if not _has_table(bind, table_name):
            continue
        _add_column_if_missing(bind, table_name, sa.Column("period_type", sa.String(length=32), nullable=True))
        _add_column_if_missing(bind, table_name, sa.Column("scope_type", sa.String(length=64), nullable=True))
        _add_column_if_missing(bind, table_name, sa.Column("scope_value", sa.String(length=255), nullable=True))
        _add_column_if_missing(bind, table_name, sa.Column("special_reason", sa.String(length=64), nullable=True))
        _add_column_if_missing(bind, table_name, sa.Column("allow_overlap", sa.Boolean(), nullable=True))

        if _has_column(bind, table_name, "scope_type"):
            _safe_execute(bind, f"UPDATE {table_name} SET scope_type='all' WHERE scope_type IS NULL OR scope_type='' ")
        if _has_column(bind, table_name, "period_type"):
            _safe_execute(bind, f"UPDATE {table_name} SET period_type='annual' WHERE period_type IS NULL OR period_type='' ")
        if _has_column(bind, table_name, "allow_overlap"):
            _safe_execute(bind, f"UPDATE {table_name} SET allow_overlap=false WHERE allow_overlap IS NULL")


    # Claude raporunda görünen düşük performans süreci NOT NULL güvenliği.
    if _has_table(bind, "performance_low_score_processes"):
        _add_column_if_missing(bind, "performance_low_score_processes", sa.Column("low_score_detected_at", sa.DateTime(), nullable=True))
        _add_column_if_missing(bind, "performance_low_score_processes", sa.Column("rule_version", sa.String(length=120), nullable=True))
        _add_column_if_missing(bind, "performance_low_score_processes", sa.Column("current_stage_key", sa.String(length=80), nullable=True))
        _add_column_if_missing(bind, "performance_low_score_processes", sa.Column("current_owner_label", sa.String(length=160), nullable=True))
        if _has_column(bind, "performance_low_score_processes", "low_score_detected_at"):
            _safe_execute(bind, "UPDATE performance_low_score_processes SET low_score_detected_at=COALESCE(low_score_detected_at, created_at, updated_at, CURRENT_TIMESTAMP) WHERE low_score_detected_at IS NULL")
            if bind.dialect.name == "postgresql":
                _safe_execute(bind, "ALTER TABLE performance_low_score_processes ALTER COLUMN low_score_detected_at SET DEFAULT CURRENT_TIMESTAMP")
                _safe_execute(bind, "ALTER TABLE performance_low_score_processes ALTER COLUMN low_score_detected_at SET NOT NULL")
        if _has_column(bind, "performance_low_score_processes", "rule_version"):
            _safe_execute(bind, "UPDATE performance_low_score_processes SET rule_version='2026-05-v58-low-score-safety' WHERE rule_version IS NULL OR rule_version='' ")

    if _has_table(bind, "performance_low_score_process_events"):
        _add_column_if_missing(bind, "performance_low_score_process_events", sa.Column("sort_order", sa.Integer(), nullable=True))
        if _has_column(bind, "performance_low_score_process_events", "sort_order"):
            _safe_execute(bind, "UPDATE performance_low_score_process_events SET sort_order=0 WHERE sort_order IS NULL")

    if not _has_table(bind, "performance_period_scope_personnel"):
        op.create_table(
            "performance_period_scope_personnel",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("period_id", sa.Integer(), nullable=False),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("scope_source", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    # Canlı güvenlik migration'ı geri alımda veri kaybı riski oluşturmamak için kolon düşürmez.
    pass
