"""BYS360 v55 schema compatibility aliases.

Revision ID: 3a9d2f1c8b70
Revises: 2f6c1e9a2b30
Create Date: 2026-05-04

Bu migration, v55 sürecinde görülen eski SQL alias bağımlılıklarını model metadata ile uyumlu hale getirir.
Amaç: process tracking / reports gibi ekranların `users.full_name` ve `performance_periods.name`
gibi eski sorgu beklentilerinde canlı DB ile kodun ayrışmasını engellemek.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "3a9d2f1c8b70"
down_revision = "2f6c1e9a2b30"
branch_labels = None
depends_on = None


BYS360_V55_SCHEMA_COMPAT_ALIASES = True


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        return {col["name"] for col in inspector.get_columns(table_name)}
    except Exception:
        return set()


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        return table_name in set(inspector.get_table_names())
    except Exception:
        return False


def upgrade() -> None:
    if _table_exists("users"):
        user_cols = _columns("users")
        if "full_name" not in user_cols:
            op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
        op.execute("CREATE INDEX IF NOT EXISTS ix_users_full_name ON users (full_name)")
        # PostgreSQL ve SQLite uyumlu concat kullanımı.
        op.execute(
            """
            UPDATE users
               SET full_name = COALESCE(
                    NULLIF(full_name, ''),
                    NULLIF(full_name_cache, ''),
                    NULLIF(TRIM(COALESCE(ad, '') || ' ' || COALESCE(soyad, '')), '')
               )
             WHERE full_name IS NULL OR full_name = ''
            """
        )

    if _table_exists("performance_periods"):
        period_cols = _columns("performance_periods")
        if "name" not in period_cols:
            op.add_column("performance_periods", sa.Column("name", sa.String(length=255), nullable=True))
        op.execute("CREATE INDEX IF NOT EXISTS ix_performance_periods_name ON performance_periods (name)")
        op.execute(
            """
            UPDATE performance_periods
               SET name = COALESCE(NULLIF(name, ''), NULLIF(title, ''))
             WHERE name IS NULL OR name = ''
            """
        )


def downgrade() -> None:
    if _table_exists("performance_periods"):
        period_cols = _columns("performance_periods")
        if "name" in period_cols:
            op.execute("DROP INDEX IF EXISTS ix_performance_periods_name")
            op.drop_column("performance_periods", "name")

    if _table_exists("users"):
        user_cols = _columns("users")
        if "full_name" in user_cols:
            op.execute("DROP INDEX IF EXISTS ix_users_full_name")
            op.drop_column("users", "full_name")
