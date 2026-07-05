"""create digital archive tables

Revision ID: da2d_digital_archive_20260705
Revises: bys360_portal_v2121
Create Date: 2026-07-05

DA-2D:
- Yalnızca digital_archive_* tablo ailesini oluşturur.
- Mevcut BYS360 tablolarını değiştirmez.
- Bu dosya oluşturulduktan sonra ayrıca güvenlik kontrolünden geçirilmelidir.
"""

from alembic import op
import sqlalchemy as sa


revision = "da2d_digital_archive_20260705"
down_revision = "bys360_portal_v2121"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "digital_archive_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["digital_archive_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_digital_archive_categories_code",
        "digital_archive_categories",
        ["code"],
        unique=False,
    )

    op.create_table(
        "digital_archive_retention_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("retention_years", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "digital_archive_physical_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("archive_room", sa.String(length=120), nullable=True),
        sa.Column("cabinet_no", sa.String(length=80), nullable=True),
        sa.Column("shelf_no", sa.String(length=80), nullable=True),
        sa.Column("box_no", sa.String(length=80), nullable=True),
        sa.Column("folder_no", sa.String(length=80), nullable=True),
        sa.Column("file_no", sa.String(length=80), nullable=True),
        sa.Column("physical_status", sa.String(length=80), nullable=False),
        sa.Column("delivered_to_user_id", sa.Integer(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("returned_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["delivered_to_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "digital_archive_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_no", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("document_type", sa.String(length=120), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("organization_unit_id", sa.Integer(), nullable=True),
        sa.Column("related_personnel_id", sa.Integer(), nullable=True),
        sa.Column("confidentiality_level", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("retention_policy_id", sa.Integer(), nullable=True),
        sa.Column("physical_location_id", sa.Integer(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["digital_archive_categories.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_unit_id"], ["organization_units.id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["physical_location_id"], ["digital_archive_physical_locations.id"]),
        sa.ForeignKeyConstraint(["related_personnel_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["retention_policy_id"], ["digital_archive_retention_policies.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_no"),
    )
    op.create_index(
        "ix_digital_archive_documents_document_no",
        "digital_archive_documents",
        ["document_no"],
        unique=False,
    )

    op.create_table(
        "digital_archive_document_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=500), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("mime_type", sa.String(length=180), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("sha256_hash", sa.String(length=128), nullable=True),
        sa.Column("revision_note", sa.Text(), nullable=True),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["digital_archive_documents.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_digital_archive_document_versions_document_id",
        "digital_archive_document_versions",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_digital_archive_document_versions_sha256_hash",
        "digital_archive_document_versions",
        ["sha256_hash"],
        unique=False,
    )

    op.create_table(
        "digital_archive_access_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("role_name", sa.String(length=120), nullable=True),
        sa.Column("organization_unit_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("can_view", sa.Boolean(), nullable=False),
        sa.Column("can_download", sa.Boolean(), nullable=False),
        sa.Column("can_update", sa.Boolean(), nullable=False),
        sa.Column("can_delete", sa.Boolean(), nullable=False),
        sa.Column("can_manage_access", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["digital_archive_documents.id"]),
        sa.ForeignKeyConstraint(["organization_unit_id"], ["organization_units.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_digital_archive_access_rules_document_id",
        "digital_archive_access_rules",
        ["document_id"],
        unique=False,
    )

    op.create_table(
        "digital_archive_audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["digital_archive_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_digital_archive_audit_events_document_id",
        "digital_archive_audit_events",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_digital_archive_audit_events_event_type",
        "digital_archive_audit_events",
        ["event_type"],
        unique=False,
    )

    op.create_table(
        "digital_archive_entity_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("relation_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["digital_archive_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_digital_archive_entity_links_document_id",
        "digital_archive_entity_links",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_digital_archive_entity_links_entity_id",
        "digital_archive_entity_links",
        ["entity_id"],
        unique=False,
    )
    op.create_index(
        "ix_digital_archive_entity_links_entity_type",
        "digital_archive_entity_links",
        ["entity_type"],
        unique=False,
    )

    op.create_table(
        "digital_archive_ocr_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_version_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["digital_archive_document_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_digital_archive_ocr_jobs_document_version_id",
        "digital_archive_ocr_jobs",
        ["document_version_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_digital_archive_ocr_jobs_document_version_id",
        table_name="digital_archive_ocr_jobs",
    )
    op.drop_table("digital_archive_ocr_jobs")

    op.drop_index(
        "ix_digital_archive_entity_links_entity_type",
        table_name="digital_archive_entity_links",
    )
    op.drop_index(
        "ix_digital_archive_entity_links_entity_id",
        table_name="digital_archive_entity_links",
    )
    op.drop_index(
        "ix_digital_archive_entity_links_document_id",
        table_name="digital_archive_entity_links",
    )
    op.drop_table("digital_archive_entity_links")

    op.drop_index(
        "ix_digital_archive_audit_events_event_type",
        table_name="digital_archive_audit_events",
    )
    op.drop_index(
        "ix_digital_archive_audit_events_document_id",
        table_name="digital_archive_audit_events",
    )
    op.drop_table("digital_archive_audit_events")

    op.drop_index(
        "ix_digital_archive_access_rules_document_id",
        table_name="digital_archive_access_rules",
    )
    op.drop_table("digital_archive_access_rules")

    op.drop_index(
        "ix_digital_archive_document_versions_sha256_hash",
        table_name="digital_archive_document_versions",
    )
    op.drop_index(
        "ix_digital_archive_document_versions_document_id",
        table_name="digital_archive_document_versions",
    )
    op.drop_table("digital_archive_document_versions")

    op.drop_index(
        "ix_digital_archive_documents_document_no",
        table_name="digital_archive_documents",
    )
    op.drop_table("digital_archive_documents")

    op.drop_table("digital_archive_physical_locations")
    op.drop_table("digital_archive_retention_policies")

    op.drop_index(
        "ix_digital_archive_categories_code",
        table_name="digital_archive_categories",
    )
    op.drop_table("digital_archive_categories")
