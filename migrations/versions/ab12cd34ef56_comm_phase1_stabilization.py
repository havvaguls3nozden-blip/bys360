"""communication phase1 stabilization

Revision ID: ab12cd34ef56
Revises: f5b1c2d3e4f9
Create Date: 2026-04-10 22:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "ab12cd34ef56"
down_revision = "f5b1c2d3e4f9"
branch_labels = None
depends_on = None


TABLE_NAME = "message_thread_participants"


def _get_columns(bind):
    inspector = inspect(bind)
    return {col["name"] for col in inspector.get_columns(TABLE_NAME)}


def _get_indexes(bind):
    inspector = inspect(bind)
    return {idx["name"] for idx in inspector.get_indexes(TABLE_NAME)}


def upgrade():
    bind = op.get_bind()
    columns = _get_columns(bind)
    indexes = _get_indexes(bind)

    if "is_pinned" not in columns:
        op.add_column(
            TABLE_NAME,
            sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        columns.add("is_pinned")

    pinned_index = op.f("ix_message_thread_participants_is_pinned")
    if pinned_index not in indexes:
        op.create_index(
            pinned_index,
            TABLE_NAME,
            ["is_pinned"],
            unique=False,
        )
        indexes.add(pinned_index)

    if "last_read_at" not in columns:
        op.add_column(
            TABLE_NAME,
            sa.Column("last_read_at", sa.DateTime(), nullable=True),
        )
        columns.add("last_read_at")

    last_read_index = op.f("ix_message_thread_participants_last_read_at")
    if last_read_index not in indexes:
        op.create_index(
            last_read_index,
            TABLE_NAME,
            ["last_read_at"],
            unique=False,
        )
        indexes.add(last_read_index)

    if {"is_pinned", "last_read_at"}.issubset(columns):
        op.execute(
            """
            UPDATE message_thread_participants
               SET is_pinned = COALESCE(is_pinned, false),
                   last_read_at = COALESCE(last_read_at, joined_at)
            """
        )


def downgrade():
    bind = op.get_bind()
    columns = _get_columns(bind)
    indexes = _get_indexes(bind)

    last_read_index = op.f("ix_message_thread_participants_last_read_at")
    if last_read_index in indexes:
        op.drop_index(last_read_index, table_name=TABLE_NAME)
    if "last_read_at" in columns:
        op.drop_column(TABLE_NAME, "last_read_at")

    pinned_index = op.f("ix_message_thread_participants_is_pinned")
    if pinned_index in indexes:
        op.drop_index(pinned_index, table_name=TABLE_NAME)
    if "is_pinned" in columns:
        op.drop_column(TABLE_NAME, "is_pinned")
