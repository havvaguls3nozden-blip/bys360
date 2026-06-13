"""add communication phase4 reporting tables

Revision ID: f4a1b2c3d4e8
Revises: e3f1a2b3c4d7
Create Date: 2026-04-10 11:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = "f4a1b2c3d4e8"
down_revision = "e3f1a2b3c4d7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "communication_executive_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False, server_default="weekly_summary"),
        sa.Column("period_label", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("metrics_json", sa.JSON(), nullable=True),
        sa.Column("recommendations_json", sa.JSON(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_executive_reports_title"), "communication_executive_reports", ["title"], unique=False)
    op.create_index(op.f("ix_communication_executive_reports_report_type"), "communication_executive_reports", ["report_type"], unique=False)
    op.create_index(op.f("ix_communication_executive_reports_period_label"), "communication_executive_reports", ["period_label"], unique=False)
    op.create_index(op.f("ix_communication_executive_reports_status"), "communication_executive_reports", ["status"], unique=False)
    op.create_index(op.f("ix_communication_executive_reports_created_by_user_id"), "communication_executive_reports", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_communication_executive_reports_approved_by_user_id"), "communication_executive_reports", ["approved_by_user_id"], unique=False)
    op.create_index(op.f("ix_communication_executive_reports_approved_at"), "communication_executive_reports", ["approved_at"], unique=False)

    op.create_table(
        "communication_report_export_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("export_type", sa.String(length=50), nullable=False),
        sa.Column("export_format", sa.String(length=20), nullable=False, server_default="csv"),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("criteria_json", sa.JSON(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_report_export_logs_export_type"), "communication_report_export_logs", ["export_type"], unique=False)
    op.create_index(op.f("ix_communication_report_export_logs_export_format"), "communication_report_export_logs", ["export_format"], unique=False)
    op.create_index(op.f("ix_communication_report_export_logs_created_by_user_id"), "communication_report_export_logs", ["created_by_user_id"], unique=False)

    op.create_table(
        "communication_governance_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_governance_reviews_review_type"), "communication_governance_reviews", ["review_type"], unique=False)
    op.create_index(op.f("ix_communication_governance_reviews_target_id"), "communication_governance_reviews", ["target_id"], unique=False)
    op.create_index(op.f("ix_communication_governance_reviews_decision"), "communication_governance_reviews", ["decision"], unique=False)
    op.create_index(op.f("ix_communication_governance_reviews_requested_by_user_id"), "communication_governance_reviews", ["requested_by_user_id"], unique=False)
    op.create_index(op.f("ix_communication_governance_reviews_reviewed_by_user_id"), "communication_governance_reviews", ["reviewed_by_user_id"], unique=False)
    op.create_index("ix_comm_governance_review_target", "communication_governance_reviews", ["review_type", "target_id"], unique=False)

    op.create_table(
        "communication_daily_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("metric_group", sa.String(length=50), nullable=False),
        sa.Column("metric_name", sa.String(length=120), nullable=False),
        sa.Column("metric_value", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("unit_label", sa.String(length=30), nullable=True),
        sa.Column("snapshot_json", sa.JSON(), nullable=True),
        sa.Column("captured_by_user_id", sa.Integer(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["captured_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("metric_date", "metric_group", "metric_name", name="uq_comm_daily_metric_name"),
    )
    op.create_index(op.f("ix_communication_daily_metrics_metric_date"), "communication_daily_metrics", ["metric_date"], unique=False)
    op.create_index(op.f("ix_communication_daily_metrics_metric_group"), "communication_daily_metrics", ["metric_group"], unique=False)
    op.create_index(op.f("ix_communication_daily_metrics_metric_name"), "communication_daily_metrics", ["metric_name"], unique=False)
    op.create_index(op.f("ix_communication_daily_metrics_captured_by_user_id"), "communication_daily_metrics", ["captured_by_user_id"], unique=False)
    op.create_index(op.f("ix_communication_daily_metrics_captured_at"), "communication_daily_metrics", ["captured_at"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_communication_daily_metrics_captured_at"), table_name="communication_daily_metrics")
    op.drop_index(op.f("ix_communication_daily_metrics_captured_by_user_id"), table_name="communication_daily_metrics")
    op.drop_index(op.f("ix_communication_daily_metrics_metric_name"), table_name="communication_daily_metrics")
    op.drop_index(op.f("ix_communication_daily_metrics_metric_group"), table_name="communication_daily_metrics")
    op.drop_index(op.f("ix_communication_daily_metrics_metric_date"), table_name="communication_daily_metrics")
    op.drop_table("communication_daily_metrics")

    op.drop_index("ix_comm_governance_review_target", table_name="communication_governance_reviews")
    op.drop_index(op.f("ix_communication_governance_reviews_reviewed_by_user_id"), table_name="communication_governance_reviews")
    op.drop_index(op.f("ix_communication_governance_reviews_requested_by_user_id"), table_name="communication_governance_reviews")
    op.drop_index(op.f("ix_communication_governance_reviews_decision"), table_name="communication_governance_reviews")
    op.drop_index(op.f("ix_communication_governance_reviews_target_id"), table_name="communication_governance_reviews")
    op.drop_index(op.f("ix_communication_governance_reviews_review_type"), table_name="communication_governance_reviews")
    op.drop_table("communication_governance_reviews")

    op.drop_index(op.f("ix_communication_report_export_logs_created_by_user_id"), table_name="communication_report_export_logs")
    op.drop_index(op.f("ix_communication_report_export_logs_export_format"), table_name="communication_report_export_logs")
    op.drop_index(op.f("ix_communication_report_export_logs_export_type"), table_name="communication_report_export_logs")
    op.drop_table("communication_report_export_logs")

    op.drop_index(op.f("ix_communication_executive_reports_approved_at"), table_name="communication_executive_reports")
    op.drop_index(op.f("ix_communication_executive_reports_approved_by_user_id"), table_name="communication_executive_reports")
    op.drop_index(op.f("ix_communication_executive_reports_created_by_user_id"), table_name="communication_executive_reports")
    op.drop_index(op.f("ix_communication_executive_reports_status"), table_name="communication_executive_reports")
    op.drop_index(op.f("ix_communication_executive_reports_period_label"), table_name="communication_executive_reports")
    op.drop_index(op.f("ix_communication_executive_reports_report_type"), table_name="communication_executive_reports")
    op.drop_index(op.f("ix_communication_executive_reports_title"), table_name="communication_executive_reports")
    op.drop_table("communication_executive_reports")
