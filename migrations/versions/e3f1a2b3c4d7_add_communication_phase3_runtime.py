"""add communication phase3 runtime tables

Revision ID: e3f1a2b3c4d7
Revises: d2f1a2b3e4f6
Create Date: 2026-04-10 10:15:00
"""

from alembic import op
from datetime import datetime
import sqlalchemy as sa


revision = "e3f1a2b3c4d7"
down_revision = "d2f1a2b3e4f6"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    try:
        return inspector.has_table(table_name)
    except Exception:
        return False


def _sla_seed_exists(bind) -> bool:
    try:
        result = bind.execute(sa.text("SELECT 1 FROM communication_support_sla_policies LIMIT 1"))
        return result.first() is not None
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    op.create_table(
        "communication_support_sla_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_name", sa.String(length=120), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("first_response_target_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("resolution_target_hours", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_name", "priority", name="uq_comm_support_sla_module_priority"),
    )
    op.create_index(op.f("ix_communication_support_sla_policies_module_name"), "communication_support_sla_policies", ["module_name"], unique=False)
    op.create_index(op.f("ix_communication_support_sla_policies_priority"), "communication_support_sla_policies", ["priority"], unique=False)
    op.create_index(op.f("ix_communication_support_sla_policies_is_active"), "communication_support_sla_policies", ["is_active"], unique=False)
    op.create_index(op.f("ix_communication_support_sla_policies_created_by_user_id"), "communication_support_sla_policies", ["created_by_user_id"], unique=False)

    op.create_table(
        "communication_support_assignment_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("old_assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("new_assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["new_assigned_to_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["old_assigned_to_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["support_tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_support_assignment_logs_ticket_id"), "communication_support_assignment_logs", ["ticket_id"], unique=False)
    op.create_index(op.f("ix_communication_support_assignment_logs_old_assigned_to_user_id"), "communication_support_assignment_logs", ["old_assigned_to_user_id"], unique=False)
    op.create_index(op.f("ix_communication_support_assignment_logs_new_assigned_to_user_id"), "communication_support_assignment_logs", ["new_assigned_to_user_id"], unique=False)
    op.create_index(op.f("ix_communication_support_assignment_logs_assigned_by_user_id"), "communication_support_assignment_logs", ["assigned_by_user_id"], unique=False)

    op.create_table(
        "communication_survey_reminder_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("survey_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=True),
        sa.Column("reminder_type", sa.String(length=30), nullable=False, server_default="in_app"),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["survey_assignments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_survey_reminder_logs_survey_id"), "communication_survey_reminder_logs", ["survey_id"], unique=False)
    op.create_index(op.f("ix_communication_survey_reminder_logs_user_id"), "communication_survey_reminder_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_communication_survey_reminder_logs_assignment_id"), "communication_survey_reminder_logs", ["assignment_id"], unique=False)
    op.create_index(op.f("ix_communication_survey_reminder_logs_reminder_type"), "communication_survey_reminder_logs", ["reminder_type"], unique=False)
    op.create_index(op.f("ix_communication_survey_reminder_logs_sent_at"), "communication_survey_reminder_logs", ["sent_at"], unique=False)

    help_article_view_log_columns = [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("search_term", sa.String(length=255), nullable=True),
        sa.Column("viewed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    ]
    if _has_table(inspector, "support_help_articles"):
        help_article_view_log_columns.insert(
            -1,
            sa.ForeignKeyConstraint(["article_id"], ["support_help_articles.id"], ondelete="CASCADE"),
        )

    op.create_table("communication_help_article_view_logs", *help_article_view_log_columns)
    op.create_index(op.f("ix_communication_help_article_view_logs_article_id"), "communication_help_article_view_logs", ["article_id"], unique=False)
    op.create_index(op.f("ix_communication_help_article_view_logs_user_id"), "communication_help_article_view_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_communication_help_article_view_logs_search_term"), "communication_help_article_view_logs", ["search_term"], unique=False)
    op.create_index(op.f("ix_communication_help_article_view_logs_viewed_at"), "communication_help_article_view_logs", ["viewed_at"], unique=False)

    if not _sla_seed_exists(bind):
        seed_now = datetime.utcnow()
        op.bulk_insert(
            sa.table(
                "communication_support_sla_policies",
                sa.column("module_name", sa.String),
                sa.column("priority", sa.String),
                sa.column("first_response_target_hours", sa.Integer),
                sa.column("resolution_target_hours", sa.Integer),
                sa.column("is_active", sa.Boolean),
                sa.column("created_at", sa.DateTime),
                sa.column("updated_at", sa.DateTime),
            ),
            [
                {"module_name": "genel", "priority": "low", "first_response_target_hours": 48, "resolution_target_hours": 120, "is_active": True, "created_at": seed_now, "updated_at": seed_now},
                {"module_name": "genel", "priority": "normal", "first_response_target_hours": 24, "resolution_target_hours": 72, "is_active": True, "created_at": seed_now, "updated_at": seed_now},
                {"module_name": "genel", "priority": "high", "first_response_target_hours": 8, "resolution_target_hours": 48, "is_active": True, "created_at": seed_now, "updated_at": seed_now},
                {"module_name": "genel", "priority": "critical", "first_response_target_hours": 4, "resolution_target_hours": 24, "is_active": True, "created_at": seed_now, "updated_at": seed_now},
            ],
        )


def downgrade():
    op.drop_index(op.f("ix_communication_help_article_view_logs_viewed_at"), table_name="communication_help_article_view_logs")
    op.drop_index(op.f("ix_communication_help_article_view_logs_search_term"), table_name="communication_help_article_view_logs")
    op.drop_index(op.f("ix_communication_help_article_view_logs_user_id"), table_name="communication_help_article_view_logs")
    op.drop_index(op.f("ix_communication_help_article_view_logs_article_id"), table_name="communication_help_article_view_logs")
    op.drop_table("communication_help_article_view_logs")

    op.drop_index(op.f("ix_communication_survey_reminder_logs_sent_at"), table_name="communication_survey_reminder_logs")
    op.drop_index(op.f("ix_communication_survey_reminder_logs_reminder_type"), table_name="communication_survey_reminder_logs")
    op.drop_index(op.f("ix_communication_survey_reminder_logs_assignment_id"), table_name="communication_survey_reminder_logs")
    op.drop_index(op.f("ix_communication_survey_reminder_logs_user_id"), table_name="communication_survey_reminder_logs")
    op.drop_index(op.f("ix_communication_survey_reminder_logs_survey_id"), table_name="communication_survey_reminder_logs")
    op.drop_table("communication_survey_reminder_logs")

    op.drop_index(op.f("ix_communication_support_assignment_logs_assigned_by_user_id"), table_name="communication_support_assignment_logs")
    op.drop_index(op.f("ix_communication_support_assignment_logs_new_assigned_to_user_id"), table_name="communication_support_assignment_logs")
    op.drop_index(op.f("ix_communication_support_assignment_logs_old_assigned_to_user_id"), table_name="communication_support_assignment_logs")
    op.drop_index(op.f("ix_communication_support_assignment_logs_ticket_id"), table_name="communication_support_assignment_logs")
    op.drop_table("communication_support_assignment_logs")

    op.drop_index(op.f("ix_communication_support_sla_policies_created_by_user_id"), table_name="communication_support_sla_policies")
    op.drop_index(op.f("ix_communication_support_sla_policies_is_active"), table_name="communication_support_sla_policies")
    op.drop_index(op.f("ix_communication_support_sla_policies_priority"), table_name="communication_support_sla_policies")
    op.drop_index(op.f("ix_communication_support_sla_policies_module_name"), table_name="communication_support_sla_policies")
    op.drop_table("communication_support_sla_policies")
