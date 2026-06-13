"""add hr request templates attachments sla

Revision ID: aa51c0d9e221
Revises: f4a12c9e0b21
Create Date: 2026-04-11 23:55:00.000000
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "aa51c0d9e221"
down_revision = "f4a12c9e0b21"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personnel_self_service_request_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("request_type", sa.String(length=50), nullable=False, server_default="bilgi_guncelleme"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description_hint", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("sla_target_days", sa.Integer(), nullable=True),
        sa.Column("requires_attachment", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_personnel_self_service_request_templates_code"), "personnel_self_service_request_templates", ["code"], unique=True)
    op.create_index(op.f("ix_personnel_self_service_request_templates_request_type"), "personnel_self_service_request_templates", ["request_type"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_templates_priority"), "personnel_self_service_request_templates", ["priority"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_templates_requires_attachment"), "personnel_self_service_request_templates", ["requires_attachment"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_templates_is_active"), "personnel_self_service_request_templates", ["is_active"], unique=False)

    op.add_column("personnel_self_service_requests", sa.Column("template_id", sa.Integer(), nullable=True))
    op.add_column("personnel_self_service_requests", sa.Column("first_response_at", sa.DateTime(), nullable=True))
    op.add_column("personnel_self_service_requests", sa.Column("due_at", sa.DateTime(), nullable=True))
    op.add_column("personnel_self_service_requests", sa.Column("sla_target_days", sa.Integer(), nullable=True))
    op.add_column("personnel_self_service_requests", sa.Column("requires_attachment", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_foreign_key("fk_personnel_self_service_requests_template_id", "personnel_self_service_requests", "personnel_self_service_request_templates", ["template_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_personnel_self_service_requests_template_id"), "personnel_self_service_requests", ["template_id"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_requests_due_at"), "personnel_self_service_requests", ["due_at"], unique=False)

    op.create_table(
        "personnel_self_service_request_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=True),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=150), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["personnel_self_service_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_personnel_self_service_request_attachments_request_id"), "personnel_self_service_request_attachments", ["request_id"], unique=False)
    op.create_index(op.f("ix_personnel_self_service_request_attachments_uploaded_by_id"), "personnel_self_service_request_attachments", ["uploaded_by_id"], unique=False)

    templates = sa.table(
        "personnel_self_service_request_templates",
        sa.column("code", sa.String()),
        sa.column("request_type", sa.String()),
        sa.column("title", sa.String()),
        sa.column("description_hint", sa.Text()),
        sa.column("priority", sa.String()),
        sa.column("sla_target_days", sa.Integer()),
        sa.column("requires_attachment", sa.Boolean()),
        sa.column("is_active", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    now = datetime.utcnow()
    op.bulk_insert(templates, [
        {"code": "iletisim_bilgisi", "request_type": "bilgi_guncelleme", "title": "İletişim Bilgisi Güncelleme", "description_hint": "Telefon, adres veya kurumsal iletişim bilgisi değişikliğini kısa ve net şekilde yazın.", "priority": "normal", "sla_target_days": 3, "requires_attachment": False, "is_active": True, "sort_order": 10, "created_at": now, "updated_at": now},
        {"code": "ozluk_duzeltme", "request_type": "ozluk_duzeltme", "title": "Özlük Kaydı Düzeltme", "description_hint": "Sicil, unvan, birim veya personel dosyasında düzeltilmesi gereken alanı açıklayın.", "priority": "high", "sla_target_days": 5, "requires_attachment": True, "is_active": True, "sort_order": 20, "created_at": now, "updated_at": now},
        {"code": "belge_yukleme", "request_type": "belge_talebi", "title": "Belge Ekleme / Yenileme", "description_hint": "Personel dosyanıza eklenmesini istediğiniz belgeyi ve geçerlilik bilgisini belirtin.", "priority": "normal", "sla_target_days": 4, "requires_attachment": True, "is_active": True, "sort_order": 30, "created_at": now, "updated_at": now},
        {"code": "gorev_unvan", "request_type": "gorev_talebi", "title": "Görev / Unvan Yazısı Talebi", "description_hint": "Görev, görevlendirme veya unvan yazısı talebinizi gerekçesiyle birlikte girin.", "priority": "high", "sla_target_days": 7, "requires_attachment": False, "is_active": True, "sort_order": 40, "created_at": now, "updated_at": now},
        {"code": "diger", "request_type": "diger", "title": "Diğer Personel Talebi", "description_hint": "Standart şablonlara girmeyen özlük talebinizi yazın. Gerekliyse ek belge yükleyin.", "priority": "normal", "sla_target_days": 5, "requires_attachment": False, "is_active": True, "sort_order": 50, "created_at": now, "updated_at": now},
    ])


def downgrade():
    op.drop_index(op.f("ix_personnel_self_service_request_attachments_uploaded_by_id"), table_name="personnel_self_service_request_attachments")
    op.drop_index(op.f("ix_personnel_self_service_request_attachments_request_id"), table_name="personnel_self_service_request_attachments")
    op.drop_table("personnel_self_service_request_attachments")

    op.drop_index(op.f("ix_personnel_self_service_requests_due_at"), table_name="personnel_self_service_requests")
    op.drop_index(op.f("ix_personnel_self_service_requests_template_id"), table_name="personnel_self_service_requests")
    op.drop_constraint("fk_personnel_self_service_requests_template_id", "personnel_self_service_requests", type_="foreignkey")
    op.drop_column("personnel_self_service_requests", "requires_attachment")
    op.drop_column("personnel_self_service_requests", "sla_target_days")
    op.drop_column("personnel_self_service_requests", "due_at")
    op.drop_column("personnel_self_service_requests", "first_response_at")
    op.drop_column("personnel_self_service_requests", "template_id")

    op.drop_index(op.f("ix_personnel_self_service_request_templates_is_active"), table_name="personnel_self_service_request_templates")
    op.drop_index(op.f("ix_personnel_self_service_request_templates_requires_attachment"), table_name="personnel_self_service_request_templates")
    op.drop_index(op.f("ix_personnel_self_service_request_templates_priority"), table_name="personnel_self_service_request_templates")
    op.drop_index(op.f("ix_personnel_self_service_request_templates_request_type"), table_name="personnel_self_service_request_templates")
    op.drop_index(op.f("ix_personnel_self_service_request_templates_code"), table_name="personnel_self_service_request_templates")
    op.drop_table("personnel_self_service_request_templates")
