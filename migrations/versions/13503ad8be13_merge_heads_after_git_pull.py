"""Merge heads after git pull

Revision ID: 13503ad8be13
Revises: 09f1b5a75a70, d33a9c4e8f10
Create Date: 2026-03-24 09:08:25.927668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13503ad8be13'
down_revision = ('09f1b5a75a70', 'd33a9c4e8f10')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
