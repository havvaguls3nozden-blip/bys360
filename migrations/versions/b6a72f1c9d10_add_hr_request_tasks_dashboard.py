"""add hr request tasks dashboard

Revision ID: b6a72f1c9d10
Revises: aa51c0d9e221
Create Date: 2026-04-11 18:35:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "b6a72f1c9d10"
down_revision = "aa51c0d9e221"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personnel_self_service_request_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("assigned_to_id", sa.Integer(), nullable=True),
        sa.Column("assigned_by_id", sa.Integer(), nullable=True),
        sa.Column("task_type", sa.String(length=50), nullable=False, server_default="review"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("completion_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["request_id"], ["personnel_self_service_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_personnel_self_service_request_tasks_assigned_by_id"), "personnel_self_service_request_tasks", ["assigned_by_id"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_tasks_assigned_to_id"), "personnel_self_service_request_tasks", ["assigned_to_id"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_tasks_completed_at"), "personnel_self_service_request_tasks", ["completed_at"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_tasks_due_at"), "personnel_self_service_request_tasks", ["due_at"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_tasks_is_primary"), "personnel_self_service_request_tasks", ["is_primary"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_tasks_priority"), "personnel_self_service_request_tasks", ["priority"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_tasks_request_id"), "personnel_self_service_request_tasks", ["request_id"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_tasks_status"), "personnel_self_service_request_tasks", ["status"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_tasks_task_type"), "personnel_self_service_request_tasks", ["task_type"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_personnel_self_service_request_tasks_task_type"), table_name="personnel_self_service_request_tasks")
    op.drop_index(op.f("ix_personnel_self_service_request_tasks_status"), table_name="personnel_self_service_request_tasks")
    op.drop_index(op.f("ix_personnel_self_service_request_tasks_request_id"), table_name="personnel_self_service_request_tasks")
    op.drop_index(op.f("ix_personnel_self_service_request_tasks_priority"), table_name="personnel_self_service_request_tasks")
    op.drop_index(op.f("ix_personnel_self_service_request_tasks_is_primary"), table_name="personnel_self_service_request_tasks")
    op.drop_index(op.f("ix_personnel_self_service_request_tasks_due_at"), table_name="personnel_self_service_request_tasks")
    op.drop_index(op.f("ix_personnel_self_service_request_tasks_completed_at"), table_name="personnel_self_service_request_tasks")
    op.drop_index(op.f("ix_personnel_self_service_request_tasks_assigned_to_id"), table_name="personnel_self_service_request_tasks")
    op.drop_index(op.f("ix_personnel_self_service_request_tasks_assigned_by_id"), table_name="personnel_self_service_request_tasks")
    op.drop_table("personnel_self_service_request_tasks")
