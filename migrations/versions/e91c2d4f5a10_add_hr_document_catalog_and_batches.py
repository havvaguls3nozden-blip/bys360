"""add hr document catalog and batches

Revision ID: e91c2d4f5a10
Revises: d8e4a1b2c301
Create Date: 2026-04-11 23:05:00.000000
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "e91c2d4f5a10"
down_revision = "d8e4a1b2c301"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personnel_document_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("validity_days", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_personnel_document_categories_code"), "personnel_document_categories", ["code"], unique=True)
    op.create_index(op.f("ix_personnel_document_categories_is_required"), "personnel_document_categories", ["is_required"], unique=False)
    op.create_index(op.f("ix_personnel_document_categories_is_active"), "personnel_document_categories", ["is_active"], unique=False)

    op.create_table(
        "personnel_document_upload_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_code", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="tamamlandi"),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("total_file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_personnel_document_upload_batches_user_id"), "personnel_document_upload_batches", ["user_id"], unique=False)
    op.create_index(op.f("ix_personnel_document_upload_batches_category_code"), "personnel_document_upload_batches", ["category_code"], unique=False)
    op.create_index(op.f("ix_personnel_document_upload_batches_status"), "personnel_document_upload_batches", ["status"], unique=False)

    document_categories = sa.table(
        "personnel_document_categories",
        sa.column("code", sa.String()),
        sa.column("label", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_required", sa.Boolean()),
        sa.column("validity_days", sa.Integer()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    now = datetime.utcnow()
    op.bulk_insert(document_categories, [
        {"code": "ozluk", "label": "Özlük", "description": "Temel kimlik, göreve başlama ve personel dosyası evrakları.", "is_required": True, "validity_days": None, "sort_order": 10, "is_active": True, "created_at": now, "updated_at": now},
        {"code": "gorevlendirme", "label": "Görevlendirme", "description": "Geçici görev, vekâlet ve görev yazıları.", "is_required": False, "validity_days": 365, "sort_order": 20, "is_active": True, "created_at": now, "updated_at": now},
        {"code": "sertifika", "label": "Sertifika", "description": "Eğitim, yetkinlik ve sertifika kanıtları.", "is_required": False, "validity_days": None, "sort_order": 30, "is_active": True, "created_at": now, "updated_at": now},
        {"code": "izin", "label": "İzin / Onay", "description": "İzin, sağlık raporu ve onay belgeleri.", "is_required": False, "validity_days": 180, "sort_order": 40, "is_active": True, "created_at": now, "updated_at": now},
        {"code": "disiplin", "label": "Disiplin", "description": "Soruşturma, savunma ve disiplin karar evrakları.", "is_required": False, "validity_days": None, "sort_order": 50, "is_active": True, "created_at": now, "updated_at": now},
        {"code": "odul", "label": "Ödül", "description": "Takdir, teşekkür ve ödül belgeleri.", "is_required": False, "validity_days": None, "sort_order": 60, "is_active": True, "created_at": now, "updated_at": now},
        {"code": "diger", "label": "Diğer", "description": "Sınıflanmayan veya destekleyici personel dokümanları.", "is_required": False, "validity_days": None, "sort_order": 90, "is_active": True, "created_at": now, "updated_at": now},
    ])


def downgrade():
    op.drop_index(op.f("ix_personnel_document_upload_batches_status"), table_name="personnel_document_upload_batches")
    op.drop_index(op.f("ix_personnel_document_upload_batches_category_code"), table_name="personnel_document_upload_batches")
    op.drop_index(op.f("ix_personnel_document_upload_batches_user_id"), table_name="personnel_document_upload_batches")
    op.drop_table("personnel_document_upload_batches")

    op.drop_index(op.f("ix_personnel_document_categories_is_active"), table_name="personnel_document_categories")
    op.drop_index(op.f("ix_personnel_document_categories_is_required"), table_name="personnel_document_categories")
    op.drop_index(op.f("ix_personnel_document_categories_code"), table_name="personnel_document_categories")
    op.drop_table("personnel_document_categories")
