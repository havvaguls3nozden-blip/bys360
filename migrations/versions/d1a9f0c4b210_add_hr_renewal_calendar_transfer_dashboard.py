"""add hr renewal calendar transfer dashboard

Revision ID: d1a9f0c4b210
Revises: a91c7e4d2f30
Create Date: 2026-04-11 19:45:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d1a9f0c4b210"
down_revision = "a91c7e4d2f30"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personnel_asset_transfer_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_assignment_id", sa.Integer(), nullable=True),
        sa.Column("from_user_id", sa.Integer(), nullable=True),
        sa.Column("to_user_id", sa.Integer(), nullable=True),
        sa.Column("transferred_by_id", sa.Integer(), nullable=True),
        sa.Column("transfer_date", sa.Date(), nullable=False),
        sa.Column("transfer_type", sa.String(length=30), nullable=False, server_default="devir"),
        sa.Column("handover_status", sa.String(length=30), nullable=False, server_default="completed"),
        sa.Column("handover_document_no", sa.String(length=120), nullable=True),
        sa.Column("asset_name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("asset_code_snapshot", sa.String(length=120), nullable=True),
        sa.Column("serial_no_snapshot", sa.String(length=120), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asset_assignment_id"], ["personnel_asset_assignments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["transferred_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_personnel_asset_transfer_logs_asset_assignment_id"), "personnel_asset_transfer_logs", ["asset_assignment_id"], unique=False)
    op.create_index(op.f("ix_personnel_asset_transfer_logs_from_user_id"), "personnel_asset_transfer_logs", ["from_user_id"], unique=False)
    op.create_index(op.f("ix_personnel_asset_transfer_logs_to_user_id"), "personnel_asset_transfer_logs", ["to_user_id"], unique=False)
    op.create_index(op.f("ix_personnel_asset_transfer_logs_transferred_by_id"), "personnel_asset_transfer_logs", ["transferred_by_id"], unique=False)
    op.create_index(op.f("ix_personnel_asset_transfer_logs_transfer_date"), "personnel_asset_transfer_logs", ["transfer_date"], unique=False)
    op.create_index(op.f("ix_personnel_asset_transfer_logs_transfer_type"), "personnel_asset_transfer_logs", ["transfer_type"], unique=False)
    op.create_index(op.f("ix_personnel_asset_transfer_logs_handover_status"), "personnel_asset_transfer_logs", ["handover_status"], unique=False)
    op.create_index(op.f("ix_personnel_asset_transfer_logs_handover_document_no"), "personnel_asset_transfer_logs", ["handover_document_no"], unique=False)
    op.create_index(op.f("ix_personnel_asset_transfer_logs_asset_code_snapshot"), "personnel_asset_transfer_logs", ["asset_code_snapshot"], unique=False)
    op.create_index(op.f("ix_personnel_asset_transfer_logs_serial_no_snapshot"), "personnel_asset_transfer_logs", ["serial_no_snapshot"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_serial_no_snapshot"), table_name="personnel_asset_transfer_logs")
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_asset_code_snapshot"), table_name="personnel_asset_transfer_logs")
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_handover_document_no"), table_name="personnel_asset_transfer_logs")
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_handover_status"), table_name="personnel_asset_transfer_logs")
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_transfer_type"), table_name="personnel_asset_transfer_logs")
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_transfer_date"), table_name="personnel_asset_transfer_logs")
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_transferred_by_id"), table_name="personnel_asset_transfer_logs")
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_to_user_id"), table_name="personnel_asset_transfer_logs")
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_from_user_id"), table_name="personnel_asset_transfer_logs")
    op.drop_index(op.f("ix_personnel_asset_transfer_logs_asset_assignment_id"), table_name="personnel_asset_transfer_logs")
    op.drop_table("personnel_asset_transfer_logs")
