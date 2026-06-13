"""add messages and notifications

Revision ID: 7c4d9a21b001
Revises: 3f2a9c4b7d10
Create Date: 2026-03-21 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7c4d9a21b001"
down_revision = "3f2a9c4b7d10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "message_threads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("thread_type", sa.String(length=30), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),

        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_message_threads_created_by_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_message_threads"),
    )
    op.create_index("ix_message_threads_thread_type", "message_threads", ["thread_type"], unique=False)
    op.create_index("ix_message_threads_created_by_user_id", "message_threads", ["created_by_user_id"], unique=False)
    op.create_index("ix_message_threads_is_active", "message_threads", ["is_active"], unique=False)
    op.create_index("ix_message_threads_last_message_at", "message_threads", ["last_message_at"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("sender_user_id", sa.Integer(), nullable=False),

        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(length=30), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("edited_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(["thread_id"], ["message_threads.id"], name="fk_messages_thread_id_message_threads"),
        sa.ForeignKeyConstraint(["sender_user_id"], ["users.id"], name="fk_messages_sender_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_messages"),
    )
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"], unique=False)
    op.create_index("ix_messages_sender_user_id", "messages", ["sender_user_id"], unique=False)
    op.create_index("ix_messages_message_type", "messages", ["message_type"], unique=False)
    op.create_index("ix_messages_sent_at", "messages", ["sent_at"], unique=False)
    op.create_index("ix_messages_is_deleted", "messages", ["is_deleted"], unique=False)

    op.create_table(
        "message_thread_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),

        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("left_at", sa.DateTime(), nullable=True),
        sa.Column("is_muted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_read_message_id", sa.Integer(), nullable=True),

        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(["thread_id"], ["message_threads.id"], name="fk_message_thread_participants_thread_id_message_threads"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_message_thread_participants_user_id_users"),
        sa.ForeignKeyConstraint(["last_read_message_id"], ["messages.id"], name="fk_message_thread_participants_last_read_message_id_messages"),
        sa.PrimaryKeyConstraint("id", name="pk_message_thread_participants"),
        sa.UniqueConstraint("thread_id", "user_id", name="uq_message_thread_participant"),
    )
    op.create_index("ix_message_thread_participants_thread_id", "message_thread_participants", ["thread_id"], unique=False)
    op.create_index("ix_message_thread_participants_user_id", "message_thread_participants", ["user_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),

        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),

        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("link_url", sa.String(length=500), nullable=True),

        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(), nullable=True),

        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_notifications_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_notification_type", "notifications", ["notification_type"], unique=False)
    op.create_index("ix_notifications_source_type", "notifications", ["source_type"], unique=False)
    op.create_index("ix_notifications_source_id", "notifications", ["source_id"], unique=False)
    op.create_index("ix_notifications_priority", "notifications", ["priority"], unique=False)
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"], unique=False)


def downgrade():
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_priority", table_name="notifications")
    op.drop_index("ix_notifications_source_id", table_name="notifications")
    op.drop_index("ix_notifications_source_type", table_name="notifications")
    op.drop_index("ix_notifications_notification_type", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_message_thread_participants_user_id", table_name="message_thread_participants")
    op.drop_index("ix_message_thread_participants_thread_id", table_name="message_thread_participants")
    op.drop_table("message_thread_participants")

    op.drop_index("ix_messages_is_deleted", table_name="messages")
    op.drop_index("ix_messages_sent_at", table_name="messages")
    op.drop_index("ix_messages_message_type", table_name="messages")
    op.drop_index("ix_messages_sender_user_id", table_name="messages")
    op.drop_index("ix_messages_thread_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_message_threads_last_message_at", table_name="message_threads")
    op.drop_index("ix_message_threads_is_active", table_name="message_threads")
    op.drop_index("ix_message_threads_created_by_user_id", table_name="message_threads")
    op.drop_index("ix_message_threads_thread_type", table_name="message_threads")
    op.drop_table("message_threads")