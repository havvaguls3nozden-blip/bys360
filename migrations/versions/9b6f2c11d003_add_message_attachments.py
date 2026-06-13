"""add message attachments

Revision ID: 9b6f2c11d003
Revises: 8d5e7f31c002
Create Date: 2026-03-21 22:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "9b6f2c11d003"
down_revision = "8d5e7f31c002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "message_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_ext", sa.String(length=20), nullable=True),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], name="fk_message_attachments_message_id_messages"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], name="fk_message_attachments_uploaded_by_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_message_attachments"),
    )
    op.create_index("ix_message_attachments_message_id", "message_attachments", ["message_id"], unique=False)
    op.create_index("ix_message_attachments_stored_filename", "message_attachments", ["stored_filename"], unique=True)
    op.create_index("ix_message_attachments_file_ext", "message_attachments", ["file_ext"], unique=False)


def downgrade():
    op.drop_index("ix_message_attachments_file_ext", table_name="message_attachments")
    op.drop_index("ix_message_attachments_stored_filename", table_name="message_attachments")
    op.drop_index("ix_message_attachments_message_id", table_name="message_attachments")
    op.drop_table("message_attachments")