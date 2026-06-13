"""add hr phase13 approval doc risk

Revision ID: 9bd13f42a001
Revises: f1c8e2a7b450
Create Date: 2026-04-11 20:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "9bd13f42a001"
down_revision = "f1c8e2a7b450"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personnel_approval_stations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lifecycle_case_id", sa.Integer(), sa.ForeignKey("personnel_lifecycle_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("handover_id", sa.Integer(), sa.ForeignKey("personnel_handover_records.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("acted_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("module_name", sa.String(length=50), nullable=False, server_default="clearance"),
        sa.Column("station_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("station_name", sa.String(length=255), nullable=False),
        sa.Column("role_label", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("decision_at", sa.DateTime(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_personnel_approval_stations_user_id"), "personnel_approval_stations", ["user_id"], unique=False)
    op.create_index(op.f("ix_personnel_approval_stations_status"), "personnel_approval_stations", ["status"], unique=False)
    op.create_index(op.f("ix_personnel_approval_stations_station_order"), "personnel_approval_stations", ["station_order"], unique=False)

    op.create_table(
        "personnel_digital_handover_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lifecycle_case_id", sa.Integer(), sa.ForeignKey("personnel_lifecycle_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("handover_id", sa.Integer(), sa.ForeignKey("personnel_handover_records.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("signed_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_type", sa.String(length=50), nullable=False, server_default="devir_teslim"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_no", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("hash_value", sa.String(length=128), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_personnel_digital_handover_documents_user_id"), "personnel_digital_handover_documents", ["user_id"], unique=False)
    op.create_index(op.f("ix_personnel_digital_handover_documents_status"), "personnel_digital_handover_documents", ["status"], unique=False)
    op.create_index(op.f("ix_personnel_digital_handover_documents_hash_value"), "personnel_digital_handover_documents", ["hash_value"], unique=False)

    op.create_table(
        "personnel_exit_risk_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lifecycle_case_id", sa.Integer(), sa.ForeignKey("personnel_lifecycle_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assessed_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="dusuk"),
        sa.Column("knowledge_loss_risk", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("asset_risk", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("access_risk", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("process_risk", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("mitigation_plan", sa.Text(), nullable=True),
        sa.Column("assessed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_personnel_exit_risk_assessments_user_id"), "personnel_exit_risk_assessments", ["user_id"], unique=False)
    op.create_index(op.f("ix_personnel_exit_risk_assessments_risk_score"), "personnel_exit_risk_assessments", ["risk_score"], unique=False)
    op.create_index(op.f("ix_personnel_exit_risk_assessments_risk_level"), "personnel_exit_risk_assessments", ["risk_level"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_personnel_exit_risk_assessments_risk_level"), table_name="personnel_exit_risk_assessments")
    op.drop_index(op.f("ix_personnel_exit_risk_assessments_risk_score"), table_name="personnel_exit_risk_assessments")
    op.drop_index(op.f("ix_personnel_exit_risk_assessments_user_id"), table_name="personnel_exit_risk_assessments")
    op.drop_table("personnel_exit_risk_assessments")

    op.drop_index(op.f("ix_personnel_digital_handover_documents_hash_value"), table_name="personnel_digital_handover_documents")
    op.drop_index(op.f("ix_personnel_digital_handover_documents_status"), table_name="personnel_digital_handover_documents")
    op.drop_index(op.f("ix_personnel_digital_handover_documents_user_id"), table_name="personnel_digital_handover_documents")
    op.drop_table("personnel_digital_handover_documents")

    op.drop_index(op.f("ix_personnel_approval_stations_station_order"), table_name="personnel_approval_stations")
    op.drop_index(op.f("ix_personnel_approval_stations_status"), table_name="personnel_approval_stations")
    op.drop_index(op.f("ix_personnel_approval_stations_user_id"), table_name="personnel_approval_stations")
    op.drop_table("personnel_approval_stations")
