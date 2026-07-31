"""Add security_stamp session-invalidation column to users.

Revision ID: e0efcd07abf7
Revises: 29fee38a97e1
Create Date: 2026-07-30

Phase 13B security closure (AUTH-003 / session hardening): a password reset
via ``/forgot-password`` did not invalidate any other active session for the
same account, so a session cookie issued before the reset stayed valid
afterwards (Phase 13B, confirmed end-to-end: an anonymous reset did not
evict the victim's already-authenticated browser session). ``User.get_id()``
(``app/models/core_models.py``) now embeds this stamp in the session cookie
as ``"<id>:<security_stamp>"``; the Flask-Login ``user_loader``
(``app/__init__.py``) rejects a session whose embedded stamp no longer
matches the current database value, and ``forgot_password()`` rotates the
stamp on every successful reset.

Existing (pre-migration) session cookies carry no stamp at all and are
treated as legacy-valid by the loader for backward compatibility, so this
migration does not force a mass logout by itself; only accounts that go
through a reset (or any future stamp rotation) after this deploy gain the
new protection.

The column is added nullable first, backfilled per-row with an
unpredictable value using a portable Python loop (no dialect-specific
random-string function is used, keeping this safe on both SQLite and
PostgreSQL), then tightened to NOT NULL.
"""
from __future__ import annotations

import secrets

import sqlalchemy as sa
from alembic import op

revision = "e0efcd07abf7"
down_revision = "29fee38a97e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("security_stamp", sa.String(length=64), nullable=True))

    bind = op.get_bind()
    users = sa.table("users", sa.column("id", sa.Integer), sa.column("security_stamp", sa.String))
    rows = bind.execute(sa.select(users.c.id)).fetchall()
    for (user_id,) in rows:
        bind.execute(
            users.update().where(users.c.id == user_id).values(security_stamp=secrets.token_hex(16))
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("security_stamp", existing_type=sa.String(length=64), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("security_stamp")
