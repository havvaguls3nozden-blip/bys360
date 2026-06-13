"""Merge multiple heads

Revision ID: 09f1b5a75a70
Revises: b31c7a5d9e2f, c32f8a1e4b9d
Create Date: 2026-03-24 07:24:02.940068

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09f1b5a75a70'
down_revision = ('b31c7a5d9e2f', 'c32f8a1e4b9d')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
