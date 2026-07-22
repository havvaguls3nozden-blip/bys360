"""Adopt mobile push tokens table into Alembic ownership.

Revision ID: b704bd9d68c0
Revises: f6d6934ad77f
Create Date: 2026-07-22 21:52:23.651097

The ``mobile_push_tokens`` table is currently self-healed at request time by
``app/api/mobile/domains/push_notifications.py``'s
``_ensure_mobile_push_token_table()`` (dialect-branched raw
``CREATE TABLE IF NOT EXISTS`` / ``CREATE [UNIQUE] INDEX IF NOT EXISTS``
SQL). This migration is a deliberately cautious, migration-only first step:
it adopts the table into Alembic ownership without changing the runtime
helper, which keeps self-healing until a follow-up package removes it. The
column types below are dialect-neutral SQLAlchemy types; SQLAlchemy already
emits the correct SQL per dialect, so no SQLite/PostgreSQL branching is
needed here (unlike the raw SQL it is adopting).
"""

from __future__ import annotations

import logging

import sqlalchemy as sa
from alembic import op

revision = "b704bd9d68c0"
down_revision = "f6d6934ad77f"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

_TABLE_NAME = "mobile_push_tokens"


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


def _create_index_if_missing(
    bind: sa.engine.Connection,
    index_name: str,
    columns: list[str],
    *,
    unique: bool = False,
) -> None:
    if index_name not in _index_names(bind, _TABLE_NAME):
        op.create_index(index_name, _TABLE_NAME, columns, unique=unique)


def _has_duplicate_tokens(bind: sa.engine.Connection) -> bool:
    duplicate = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM mobile_push_tokens
            WHERE token IS NOT NULL
            GROUP BY token
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
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("platform", sa.String(length=30), nullable=True),
        sa.Column("device_id", sa.String(length=120), nullable=True),
        sa.Column("app_version", sa.String(length=60), nullable=True),
        sa.Column("device_label", sa.String(length=180), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sqlite_autoincrement=True,
    )


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, _TABLE_NAME):
        _create_table()
    else:
        # The runtime self-heal path in
        # app/api/mobile/domains/push_notifications.py declares the exact
        # same shape, so no add-missing-column step is required here; this
        # is a lightweight sanity check only.
        expected_columns = {
            "id",
            "user_id",
            "token",
            "platform",
            "device_id",
            "app_version",
            "device_label",
            "is_active",
            "last_seen_at",
            "created_at",
            "updated_at",
        }
        missing = expected_columns - _column_names(bind, _TABLE_NAME)
        if missing:
            logger.warning(
                "mobile_push_tokens tablosu zaten var ama beklenen kolonlar eksik: %s",
                ", ".join(sorted(missing)),
            )

    _create_index_if_missing(
        bind,
        "ix_mobile_push_tokens_user_active",
        ["user_id", "is_active"],
    )

    if ("token",) in _unique_column_sets(bind, _TABLE_NAME):
        pass  # already uniquely constrained by a prior run; nothing to do.
    elif _has_duplicate_tokens(bind):
        logger.warning(
            "mobile_push_tokens.token kolonunda mukerrer degerler bulundu; "
            "unique index atlanip normal (non-unique) index olusturuluyor."
        )
        _create_index_if_missing(bind, "ix_mobile_push_tokens_token", ["token"], unique=False)
    else:
        _create_index_if_missing(bind, "ix_mobile_push_tokens_token", ["token"], unique=True)


def downgrade() -> None:
    """Preserve the adopted mobile_push_tokens table and its data.

    The migration cannot safely know whether this table existed before
    Alembic ownership was introduced, and live installations may already
    hold registered device push tokens. A destructive downgrade could
    therefore break push notifications for real users. Downgrade is
    intentionally a no-op.
    """
