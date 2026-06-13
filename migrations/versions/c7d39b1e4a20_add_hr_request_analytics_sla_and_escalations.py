"""add hr request sla policies and escalations

Revision ID: c7d39b1e4a20
Revises: b6a72f1c9d10
Create Date: 2026-04-11 19:05:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "c7d39b1e4a20"
down_revision = "b6a72f1c9d10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personnel_self_service_request_sla_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("request_type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("target_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("first_response_hours", sa.Integer(), nullable=True),
        sa.Column("escalation_hours", sa.Integer(), nullable=True),
        sa.Column("owner_role", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_personnel_self_service_request_sla_policy_code"),
    )
    op.create_index(op.f("ix_personnel_self_service_request_sla_policies_code"), "personnel_self_service_request_sla_policies", ["code"], unique=True)
    op.create_index(op.f("ix_personnel_self_service_request_sla_policies_is_active"), "personnel_self_service_request_sla_policies", ["is_active"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_sla_policies_owner_role"), "personnel_self_service_request_sla_policies", ["owner_role"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_sla_policies_priority"), "personnel_self_service_request_sla_policies", ["priority"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_sla_policies_request_type"), "personnel_self_service_request_sla_policies", ["request_type"], unique=False)

    op.create_table(
        "personnel_self_service_request_escalations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("escalated_from_user_id", sa.Integer(), nullable=True),
        sa.Column("escalated_to_user_id", sa.Integer(), nullable=True),
        sa.Column("escalated_by_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("escalated_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["escalated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escalated_from_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escalated_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["request_id"], ["personnel_self_service_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["personnel_self_service_request_tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_personnel_self_service_request_escalations_escalated_at"), "personnel_self_service_request_escalations", ["escalated_at"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_escalations_escalated_by_id"), "personnel_self_service_request_escalations", ["escalated_by_id"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_escalations_escalated_from_user_id"), "personnel_self_service_request_escalations", ["escalated_from_user_id"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_escalations_escalated_to_user_id"), "personnel_self_service_request_escalations", ["escalated_to_user_id"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_escalations_level"), "personnel_self_service_request_escalations", ["level"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_escalations_request_id"), "personnel_self_service_request_escalations", ["request_id"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_escalations_status"), "personnel_self_service_request_escalations", ["status"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_escalations_task_id"), "personnel_self_service_request_escalations", ["task_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_personnel_self_service_request_escalations_task_id"), table_name="personnel_self_service_request_escalations")
    op.drop_index(op.f("ix_personnel_self_service_request_escalations_status"), table_name="personnel_self_service_request_escalations")
    op.drop_index(op.f("ix_personnel_self_service_request_escalations_request_id"), table_name="personnel_self_service_request_escalations")
    op.drop_index(op.f("ix_personnel_self_service_request_escalations_level"), table_name="personnel_self_service_request_escalations")
    op.drop_index(op.f("ix_personnel_self_service_request_escalations_escalated_to_user_id"), table_name="personnel_self_service_request_escalations")
    op.drop_index(op.f("ix_personnel_self_service_request_escalations_escalated_from_user_id"), table_name="personnel_self_service_request_escalations")
    op.drop_index(op.f("ix_personnel_self_service_request_escalations_escalated_by_id"), table_name="personnel_self_service_request_escalations")
    op.drop_index(op.f("ix_personnel_self_service_request_escalations_escalated_at"), table_name="personnel_self_service_request_escalations")
    op.drop_table("personnel_self_service_request_escalations")

    op.drop_index(op.f("ix_personnel_self_service_request_sla_policies_request_type"), table_name="personnel_self_service_request_sla_policies")
    op.drop_index(op.f("ix_personnel_self_service_request_sla_policies_priority"), table_name="personnel_self_service_request_sla_policies")
    op.drop_index(op.f("ix_personnel_self_service_request_sla_policies_owner_role"), table_name="personnel_self_service_request_sla_policies")
    op.drop_index(op.f("ix_personnel_self_service_request_sla_policies_is_active"), table_name="personnel_self_service_request_sla_policies")
    op.drop_index(op.f("ix_personnel_self_service_request_sla_policies_code"), table_name="personnel_self_service_request_sla_policies")
    op.drop_table("personnel_self_service_request_sla_policies")
