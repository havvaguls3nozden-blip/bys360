"""add hr professional foundation

Revision ID: d8e4a1b2c301
Revises: c4a1d9e2f731
Create Date: 2026-04-11 21:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d8e4a1b2c301"
down_revision = "c4a1d9e2f731"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personnel_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="ozluk"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_no", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="aktif"),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("stored_filename", sa.String(length=255), nullable=True),
        sa.Column("storage_path", sa.String(length=500), nullable=True),
        sa.Column("mime_type", sa.String(length=150), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("is_confidential", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_personnel_documents_user_id"), "personnel_documents", ["user_id"], unique=False)
    op.create_index(op.f("ix_personnel_documents_category"), "personnel_documents", ["category"], unique=False)
    op.create_index(op.f("ix_personnel_documents_document_no"), "personnel_documents", ["document_no"], unique=False)
    op.create_index(op.f("ix_personnel_documents_status"), "personnel_documents", ["status"], unique=False)
    op.create_index(op.f("ix_personnel_documents_issue_date"), "personnel_documents", ["issue_date"], unique=False)
    op.create_index(op.f("ix_personnel_documents_expiry_date"), "personnel_documents", ["expiry_date"], unique=False)

    op.create_table(
        "personnel_process_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("note_type", sa.String(length=50), nullable=False, server_default="ozluk"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_personnel_process_notes_user_id"), "personnel_process_notes", ["user_id"], unique=False)
    op.create_index(op.f("ix_personnel_process_notes_note_type"), "personnel_process_notes", ["note_type"], unique=False)
    op.create_index(op.f("ix_personnel_process_notes_priority"), "personnel_process_notes", ["priority"], unique=False)
    op.create_index(op.f("ix_personnel_process_notes_status"), "personnel_process_notes", ["status"], unique=False)
    op.create_index(op.f("ix_personnel_process_notes_due_date"), "personnel_process_notes", ["due_date"], unique=False)

    op.create_table(
        "personnel_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False, server_default="durum"),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("effective_start_date", sa.Date(), nullable=True),
        sa.Column("effective_end_date", sa.Date(), nullable=True),
        sa.Column("organization_unit_id", sa.Integer(), sa.ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True),
        sa.Column("previous_value", sa.String(length=255), nullable=True),
        sa.Column("new_value", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("recorded_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_personnel_status_history_user_id"), "personnel_status_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_personnel_status_history_event_type"), "personnel_status_history", ["event_type"], unique=False)
    op.create_index(op.f("ix_personnel_status_history_event_date"), "personnel_status_history", ["event_date"], unique=False)
    op.create_index(op.f("ix_personnel_status_history_effective_start_date"), "personnel_status_history", ["effective_start_date"], unique=False)
    op.create_index(op.f("ix_personnel_status_history_effective_end_date"), "personnel_status_history", ["effective_end_date"], unique=False)
    op.create_index(op.f("ix_personnel_status_history_organization_unit_id"), "personnel_status_history", ["organization_unit_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_personnel_status_history_organization_unit_id"), table_name="personnel_status_history")
    op.drop_index(op.f("ix_personnel_status_history_effective_end_date"), table_name="personnel_status_history")
    op.drop_index(op.f("ix_personnel_status_history_effective_start_date"), table_name="personnel_status_history")
    op.drop_index(op.f("ix_personnel_status_history_event_date"), table_name="personnel_status_history")
    op.drop_index(op.f("ix_personnel_status_history_event_type"), table_name="personnel_status_history")
    op.drop_index(op.f("ix_personnel_status_history_user_id"), table_name="personnel_status_history")
    op.drop_table("personnel_status_history")

    op.drop_index(op.f("ix_personnel_process_notes_due_date"), table_name="personnel_process_notes")
    op.drop_index(op.f("ix_personnel_process_notes_status"), table_name="personnel_process_notes")
    op.drop_index(op.f("ix_personnel_process_notes_priority"), table_name="personnel_process_notes")
    op.drop_index(op.f("ix_personnel_process_notes_note_type"), table_name="personnel_process_notes")
    op.drop_index(op.f("ix_personnel_process_notes_user_id"), table_name="personnel_process_notes")
    op.drop_table("personnel_process_notes")

    op.drop_index(op.f("ix_personnel_documents_expiry_date"), table_name="personnel_documents")
    op.drop_index(op.f("ix_personnel_documents_issue_date"), table_name="personnel_documents")
    op.drop_index(op.f("ix_personnel_documents_status"), table_name="personnel_documents")
    op.drop_index(op.f("ix_personnel_documents_document_no"), table_name="personnel_documents")
    op.drop_index(op.f("ix_personnel_documents_category"), table_name="personnel_documents")
    op.drop_index(op.f("ix_personnel_documents_user_id"), table_name="personnel_documents")
    op.drop_table("personnel_documents")
