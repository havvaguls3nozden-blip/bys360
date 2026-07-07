"""add communication phase1 bulletins

Revision ID: c9f1a2b3d4e5
Revises: b2c3d4e5f6a7
Create Date: 2026-04-10 12:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c9f1a2b3d4e5"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "communication_bulletins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("bulletin_type", sa.String(length=50), nullable=False, server_default="duyuru"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("require_ack", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("publish_at", sa.DateTime(), nullable=True),
        sa.Column("expire_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("published_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["published_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_bulletins_title"), "communication_bulletins", ["title"], unique=False)
    op.create_index(op.f("ix_communication_bulletins_bulletin_type"), "communication_bulletins", ["bulletin_type"], unique=False)
    op.create_index(op.f("ix_communication_bulletins_priority"), "communication_bulletins", ["priority"], unique=False)
    op.create_index(op.f("ix_communication_bulletins_status"), "communication_bulletins", ["status"], unique=False)
    op.create_index(op.f("ix_communication_bulletins_is_pinned"), "communication_bulletins", ["is_pinned"], unique=False)
    op.create_index(op.f("ix_communication_bulletins_publish_at"), "communication_bulletins", ["publish_at"], unique=False)
    op.create_index(op.f("ix_communication_bulletins_expire_at"), "communication_bulletins", ["expire_at"], unique=False)
    op.create_index(op.f("ix_communication_bulletins_created_by_user_id"), "communication_bulletins", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_communication_bulletins_published_by_user_id"), "communication_bulletins", ["published_by_user_id"], unique=False)

    op.create_table(
        "communication_bulletin_audiences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bulletin_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_value", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["bulletin_id"], ["communication_bulletins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_bulletin_audiences_bulletin_id"), "communication_bulletin_audiences", ["bulletin_id"], unique=False)
    op.create_index(op.f("ix_communication_bulletin_audiences_target_type"), "communication_bulletin_audiences", ["target_type"], unique=False)
    op.create_index(op.f("ix_communication_bulletin_audiences_target_value"), "communication_bulletin_audiences", ["target_value"], unique=False)
    op.create_index("ix_comm_bulletin_audience_type_value", "communication_bulletin_audiences", ["target_type", "target_value"], unique=False)

    op.create_table(
        "communication_bulletin_receipts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bulletin_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["bulletin_id"], ["communication_bulletins.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bulletin_id", "user_id", name="uq_comm_bulletin_receipt_user"),
    )
    op.create_index(op.f("ix_communication_bulletin_receipts_bulletin_id"), "communication_bulletin_receipts", ["bulletin_id"], unique=False)
    op.create_index(op.f("ix_communication_bulletin_receipts_user_id"), "communication_bulletin_receipts", ["user_id"], unique=False)
    op.create_index(op.f("ix_communication_bulletin_receipts_is_read"), "communication_bulletin_receipts", ["is_read"], unique=False)
    op.create_index(op.f("ix_communication_bulletin_receipts_is_acknowledged"), "communication_bulletin_receipts", ["is_acknowledged"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_communication_bulletin_receipts_is_acknowledged"), table_name="communication_bulletin_receipts")
    op.drop_index(op.f("ix_communication_bulletin_receipts_is_read"), table_name="communication_bulletin_receipts")
    op.drop_index(op.f("ix_communication_bulletin_receipts_user_id"), table_name="communication_bulletin_receipts")
    op.drop_index(op.f("ix_communication_bulletin_receipts_bulletin_id"), table_name="communication_bulletin_receipts")
    op.drop_table("communication_bulletin_receipts")

    op.drop_index("ix_comm_bulletin_audience_type_value", table_name="communication_bulletin_audiences")
    op.drop_index(op.f("ix_communication_bulletin_audiences_target_value"), table_name="communication_bulletin_audiences")
    op.drop_index(op.f("ix_communication_bulletin_audiences_target_type"), table_name="communication_bulletin_audiences")
    op.drop_index(op.f("ix_communication_bulletin_audiences_bulletin_id"), table_name="communication_bulletin_audiences")
    op.drop_table("communication_bulletin_audiences")

    op.drop_index(op.f("ix_communication_bulletins_published_by_user_id"), table_name="communication_bulletins")
    op.drop_index(op.f("ix_communication_bulletins_created_by_user_id"), table_name="communication_bulletins")
    op.drop_index(op.f("ix_communication_bulletins_expire_at"), table_name="communication_bulletins")
    op.drop_index(op.f("ix_communication_bulletins_publish_at"), table_name="communication_bulletins")
    op.drop_index(op.f("ix_communication_bulletins_is_pinned"), table_name="communication_bulletins")
    op.drop_index(op.f("ix_communication_bulletins_status"), table_name="communication_bulletins")
    op.drop_index(op.f("ix_communication_bulletins_priority"), table_name="communication_bulletins")
    op.drop_index(op.f("ix_communication_bulletins_bulletin_type"), table_name="communication_bulletins")
    op.drop_index(op.f("ix_communication_bulletins_title"), table_name="communication_bulletins")
    op.drop_table("communication_bulletins")
