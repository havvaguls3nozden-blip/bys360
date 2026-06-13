"""add communication phase5 operations tables

Revision ID: f5b1c2d3e4f9
Revises: f4a1b2c3d4e8
Create Date: 2026-04-10 11:40:00
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "f5b1c2d3e4f9"
down_revision = "f4a1b2c3d4e8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "communication_notification_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("daily_digest_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("weekly_digest_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("digest_hour", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("quiet_hours_start", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("quiet_hours_end", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_comm_notification_preference_user"),
    )
    op.create_index(op.f("ix_communication_notification_preferences_user_id"), "communication_notification_preferences", ["user_id"], unique=False)

    op.create_table(
        "communication_digest_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("digest_type", sa.String(length=20), nullable=False, server_default="daily"),
        sa.Column("period_label", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_digest_jobs_user_id"), "communication_digest_jobs", ["user_id"], unique=False)
    op.create_index(op.f("ix_communication_digest_jobs_digest_type"), "communication_digest_jobs", ["digest_type"], unique=False)
    op.create_index(op.f("ix_communication_digest_jobs_period_label"), "communication_digest_jobs", ["period_label"], unique=False)
    op.create_index(op.f("ix_communication_digest_jobs_status"), "communication_digest_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_communication_digest_jobs_scheduled_for"), "communication_digest_jobs", ["scheduled_for"], unique=False)
    op.create_index(op.f("ix_communication_digest_jobs_executed_at"), "communication_digest_jobs", ["executed_at"], unique=False)

    op.create_table(
        "communication_escalation_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_name", sa.String(length=50), nullable=False, server_default="support"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("trigger_type", sa.String(length=30), nullable=False, server_default="sla_breach"),
        sa.Column("threshold_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("target_role", sa.String(length=50), nullable=True),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("notify_template", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_escalation_rules_module_name"), "communication_escalation_rules", ["module_name"], unique=False)
    op.create_index(op.f("ix_communication_escalation_rules_priority"), "communication_escalation_rules", ["priority"], unique=False)
    op.create_index(op.f("ix_communication_escalation_rules_trigger_type"), "communication_escalation_rules", ["trigger_type"], unique=False)
    op.create_index(op.f("ix_communication_escalation_rules_target_role"), "communication_escalation_rules", ["target_role"], unique=False)
    op.create_index(op.f("ix_communication_escalation_rules_target_user_id"), "communication_escalation_rules", ["target_user_id"], unique=False)
    op.create_index(op.f("ix_communication_escalation_rules_is_active"), "communication_escalation_rules", ["is_active"], unique=False)

    op.create_table(
        "communication_retention_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data_scope", sa.String(length=50), nullable=False),
        sa.Column("keep_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("archive_after_days", sa.Integer(), nullable=True),
        sa.Column("anonymize_after_days", sa.Integer(), nullable=True),
        sa.Column("purge_after_days", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("data_scope", name="uq_comm_retention_scope"),
    )
    op.create_index(op.f("ix_communication_retention_policies_data_scope"), "communication_retention_policies", ["data_scope"], unique=False)
    op.create_index(op.f("ix_communication_retention_policies_is_active"), "communication_retention_policies", ["is_active"], unique=False)

    op.create_table(
        "communication_operation_health",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("check_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ok"),
        sa.Column("metric_value", sa.String(length=100), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_operation_health_check_name"), "communication_operation_health", ["check_name"], unique=False)
    op.create_index(op.f("ix_communication_operation_health_status"), "communication_operation_health", ["status"], unique=False)
    op.create_index(op.f("ix_communication_operation_health_checked_at"), "communication_operation_health", ["checked_at"], unique=False)

    op.create_table(
        "communication_automation_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("target_table", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_automation_logs_action_type"), "communication_automation_logs", ["action_type"], unique=False)
    op.create_index(op.f("ix_communication_automation_logs_status"), "communication_automation_logs", ["status"], unique=False)
    op.create_index(op.f("ix_communication_automation_logs_actor_user_id"), "communication_automation_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_communication_automation_logs_target_table"), "communication_automation_logs", ["target_table"], unique=False)
    op.create_index(op.f("ix_communication_automation_logs_target_id"), "communication_automation_logs", ["target_id"], unique=False)
    op.create_index(op.f("ix_communication_automation_logs_executed_at"), "communication_automation_logs", ["executed_at"], unique=False)

    ts = datetime.utcnow()
    retention_table = sa.table(
        "communication_retention_policies",
        sa.column("data_scope", sa.String()),
        sa.column("keep_days", sa.Integer()),
        sa.column("archive_after_days", sa.Integer()),
        sa.column("anonymize_after_days", sa.Integer()),
        sa.column("purge_after_days", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
        sa.column("notes", sa.Text()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    op.bulk_insert(
        retention_table,
        [
            {"data_scope": "notifications", "keep_days": 365, "archive_after_days": 180, "anonymize_after_days": None, "purge_after_days": 730, "is_active": True, "notes": "Varsayılan Faz 5 saklama politikası", "created_at": ts, "updated_at": ts},
            {"data_scope": "support", "keep_days": 1095, "archive_after_days": 365, "anonymize_after_days": None, "purge_after_days": 1825, "is_active": True, "notes": "Varsayılan Faz 5 saklama politikası", "created_at": ts, "updated_at": ts},
            {"data_scope": "surveys", "keep_days": 1095, "archive_after_days": 365, "anonymize_after_days": None, "purge_after_days": 1825, "is_active": True, "notes": "Varsayılan Faz 5 saklama politikası", "created_at": ts, "updated_at": ts},
            {"data_scope": "digest_logs", "keep_days": 365, "archive_after_days": 90, "anonymize_after_days": None, "purge_after_days": 730, "is_active": True, "notes": "Varsayılan Faz 5 saklama politikası", "created_at": ts, "updated_at": ts},
            {"data_scope": "automation_logs", "keep_days": 365, "archive_after_days": 90, "anonymize_after_days": None, "purge_after_days": 730, "is_active": True, "notes": "Varsayılan Faz 5 saklama politikası", "created_at": ts, "updated_at": ts},
        ],
    )

    escalation_table = sa.table(
        "communication_escalation_rules",
        sa.column("module_name", sa.String()),
        sa.column("priority", sa.String()),
        sa.column("trigger_type", sa.String()),
        sa.column("threshold_hours", sa.Integer()),
        sa.column("target_role", sa.String()),
        sa.column("target_user_id", sa.Integer()),
        sa.column("notify_template", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    op.bulk_insert(
        escalation_table,
        [
            {"module_name": "support", "priority": "normal", "trigger_type": "sla_breach", "threshold_hours": 72, "target_role": "grup_baskani", "target_user_id": None, "notify_template": "SLA ihlali bildirimi", "is_active": True, "created_at": ts, "updated_at": ts},
            {"module_name": "support", "priority": "high", "trigger_type": "sla_breach", "threshold_hours": 48, "target_role": "grup_baskani", "target_user_id": None, "notify_template": "SLA ihlali bildirimi", "is_active": True, "created_at": ts, "updated_at": ts},
            {"module_name": "support", "priority": "critical", "trigger_type": "sla_breach", "threshold_hours": 24, "target_role": "baskan_yardimcisi", "target_user_id": None, "notify_template": "Kritik SLA ihlali bildirimi", "is_active": True, "created_at": ts, "updated_at": ts},
        ],
    )


def downgrade():
    op.drop_index(op.f("ix_communication_automation_logs_executed_at"), table_name="communication_automation_logs")
    op.drop_index(op.f("ix_communication_automation_logs_target_id"), table_name="communication_automation_logs")
    op.drop_index(op.f("ix_communication_automation_logs_target_table"), table_name="communication_automation_logs")
    op.drop_index(op.f("ix_communication_automation_logs_actor_user_id"), table_name="communication_automation_logs")
    op.drop_index(op.f("ix_communication_automation_logs_status"), table_name="communication_automation_logs")
    op.drop_index(op.f("ix_communication_automation_logs_action_type"), table_name="communication_automation_logs")
    op.drop_table("communication_automation_logs")

    op.drop_index(op.f("ix_communication_operation_health_checked_at"), table_name="communication_operation_health")
    op.drop_index(op.f("ix_communication_operation_health_status"), table_name="communication_operation_health")
    op.drop_index(op.f("ix_communication_operation_health_check_name"), table_name="communication_operation_health")
    op.drop_table("communication_operation_health")

    op.drop_index(op.f("ix_communication_retention_policies_is_active"), table_name="communication_retention_policies")
    op.drop_index(op.f("ix_communication_retention_policies_data_scope"), table_name="communication_retention_policies")
    op.drop_table("communication_retention_policies")

    op.drop_index(op.f("ix_communication_escalation_rules_is_active"), table_name="communication_escalation_rules")
    op.drop_index(op.f("ix_communication_escalation_rules_target_user_id"), table_name="communication_escalation_rules")
    op.drop_index(op.f("ix_communication_escalation_rules_target_role"), table_name="communication_escalation_rules")
    op.drop_index(op.f("ix_communication_escalation_rules_trigger_type"), table_name="communication_escalation_rules")
    op.drop_index(op.f("ix_communication_escalation_rules_priority"), table_name="communication_escalation_rules")
    op.drop_index(op.f("ix_communication_escalation_rules_module_name"), table_name="communication_escalation_rules")
    op.drop_table("communication_escalation_rules")

    op.drop_index(op.f("ix_communication_digest_jobs_executed_at"), table_name="communication_digest_jobs")
    op.drop_index(op.f("ix_communication_digest_jobs_scheduled_for"), table_name="communication_digest_jobs")
    op.drop_index(op.f("ix_communication_digest_jobs_status"), table_name="communication_digest_jobs")
    op.drop_index(op.f("ix_communication_digest_jobs_period_label"), table_name="communication_digest_jobs")
    op.drop_index(op.f("ix_communication_digest_jobs_digest_type"), table_name="communication_digest_jobs")
    op.drop_index(op.f("ix_communication_digest_jobs_user_id"), table_name="communication_digest_jobs")
    op.drop_table("communication_digest_jobs")

    op.drop_index(op.f("ix_communication_notification_preferences_user_id"), table_name="communication_notification_preferences")
    op.drop_table("communication_notification_preferences")
