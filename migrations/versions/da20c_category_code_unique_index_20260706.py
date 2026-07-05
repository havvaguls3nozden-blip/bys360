"""DA-20C digital archive category code unique index.

Revision ID: da20c_category_code_unique_20260706
Revises: da2d_digital_archive_20260705
Create Date: 2026-07-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "da20c_category_code_unique_20260706"
down_revision = "da2d_digital_archive_20260705"
branch_labels = None
depends_on = None


INDEX_NAME = "ux_digital_archive_categories_code"
TABLE_NAME = "digital_archive_categories"


def _table_exists(bind) -> bool:
    inspector = sa.inspect(bind)
    return TABLE_NAME in inspector.get_table_names()


def _index_exists(bind) -> bool:
    inspector = sa.inspect(bind)
    for index in inspector.get_indexes(TABLE_NAME):
        if index.get("name") == INDEX_NAME:
            return True
    return False


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind):
        return

    duplicate_count = bind.execute(
        sa.text(
            """
            SELECT COUNT(*) FROM (
                SELECT code
                FROM digital_archive_categories
                WHERE code IS NOT NULL AND TRIM(code) <> ''
                GROUP BY code
                HAVING COUNT(*) > 1
            ) duplicate_codes
            """
        )
    ).scalar_one()

    if duplicate_count:
        raise RuntimeError(
            "digital_archive_categories.code unique index uygulanamaz: duplicate code mevcut."
        )

    blank_count = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM digital_archive_categories
            WHERE code IS NULL OR TRIM(code) = ''
            """
        )
    ).scalar_one()

    if blank_count:
        raise RuntimeError(
            "digital_archive_categories.code unique index uygulanamaz: boş/null code mevcut."
        )

    if not _index_exists(bind):
        op.create_index(
            INDEX_NAME,
            TABLE_NAME,
            ["code"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind):
        return

    if _index_exists(bind):
        op.drop_index(INDEX_NAME, table_name=TABLE_NAME)
