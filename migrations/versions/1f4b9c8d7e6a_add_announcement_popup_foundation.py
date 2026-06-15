"""add announcement popup foundation

Revision ID: 1f4b9c8d7e6a
Revises: 9bd13f42a001, c7d39b1e4a20, g6c1d2e3f4a5
Create Date: 2026-04-24 12:10:00
"""

from alembic import op
import sqlalchemy as sa

# BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_HELPERS
def _bys360_has_table(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _bys360_has_index(table_name, index_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        return any(idx.get("name") == index_name for idx in inspector.get_indexes(table_name))
    except Exception:
        return False

revision = "1f4b9c8d7e6a"
down_revision = ("9bd13f42a001", "c7d39b1e4a20", "g6c1d2e3f4a5")
branch_labels = None
depends_on = None


def upgrade():
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: announcements tablosu zaten varsa tekrar oluşturma.
    if not _bys360_has_table('announcements'):
        op.create_table(
            "announcements",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("announcement_type", sa.String(length=30), nullable=False, server_default="info"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("show_rule", sa.String(length=30), nullable=False, server_default="once"),
            sa.Column("target_scope", sa.String(length=30), nullable=False, server_default="all"),
            sa.Column("target_role", sa.String(length=80), nullable=True),
            sa.Column("target_unit_id", sa.Integer(), nullable=True),
            sa.Column("publish_start_at", sa.DateTime(), nullable=True),
            sa.Column("publish_end_at", sa.DateTime(), nullable=True),
            sa.Column("button_text", sa.String(length=80), nullable=False, server_default="Okudum"),
            sa.Column("media_type", sa.String(length=30), nullable=False, server_default="none"),
            sa.Column("media_url", sa.String(length=1000), nullable=True),
            sa.Column("media_file_path", sa.String(length=500), nullable=True),
            sa.Column("cover_image_path", sa.String(length=500), nullable=True),
            sa.Column("cta_text", sa.String(length=120), nullable=True),
            sa.Column("cta_url", sa.String(length=1000), nullable=True),
            sa.Column("created_by_user_id", sa.Integer(), nullable=True),
            sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint("announcement_type IN ('info', 'warning', 'important', 'maintenance')", name="ck_announcements_type"),
            sa.CheckConstraint("show_rule IN ('every_login', 'once_per_day', 'once')", name="ck_announcements_show_rule"),
            sa.CheckConstraint("target_scope IN ('all', 'role', 'unit', 'custom')", name="ck_announcements_target_scope"),
            sa.CheckConstraint("media_type IN ('none', 'youtube', 'vimeo', 'upload_video', 'image', 'pdf')", name="ck_announcements_media_type"),
            sa.ForeignKeyConstraint(["target_unit_id"], ["organization_units.id"], ondelete="SET NULL", name="fk_announcements_target_unit_id_organization_units"),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL", name="fk_announcements_created_by_user_id_users"),
            sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL", name="fk_announcements_updated_by_user_id_users"),
            sa.PrimaryKeyConstraint("id", name="pk_announcements"),
        )
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_announcement_type index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_announcement_type'):
        op.create_index("ix_announcements_announcement_type", "announcements", ["announcement_type"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_is_active index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_is_active'):
        op.create_index("ix_announcements_is_active", "announcements", ["is_active"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_is_required index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_is_required'):
        op.create_index("ix_announcements_is_required", "announcements", ["is_required"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_show_rule index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_show_rule'):
        op.create_index("ix_announcements_show_rule", "announcements", ["show_rule"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_target_scope index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_target_scope'):
        op.create_index("ix_announcements_target_scope", "announcements", ["target_scope"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_target_role index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_target_role'):
        op.create_index("ix_announcements_target_role", "announcements", ["target_role"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_target_unit_id index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_target_unit_id'):
        op.create_index("ix_announcements_target_unit_id", "announcements", ["target_unit_id"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_publish_start_at index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_publish_start_at'):
        op.create_index("ix_announcements_publish_start_at", "announcements", ["publish_start_at"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_publish_end_at index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_publish_end_at'):
        op.create_index("ix_announcements_publish_end_at", "announcements", ["publish_end_at"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_media_type index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_media_type'):
        op.create_index("ix_announcements_media_type", "announcements", ["media_type"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_created_by_user_id index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_created_by_user_id'):
        op.create_index("ix_announcements_created_by_user_id", "announcements", ["created_by_user_id"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcements_updated_by_user_id index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcements', 'ix_announcements_updated_by_user_id'):
        op.create_index("ix_announcements_updated_by_user_id", "announcements", ["updated_by_user_id"], unique=False)

    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: announcement_reads tablosu zaten varsa tekrar oluşturma.

    if not _bys360_has_table('announcement_reads'):

        op.create_table(
            "announcement_reads",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("announcement_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("first_seen_at", sa.DateTime(), nullable=True),
            sa.Column("last_seen_at", sa.DateTime(), nullable=True),
            sa.Column("dismissed_at", sa.DateTime(), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
            sa.Column("seen_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("ip_address", sa.String(length=80), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE", name="fk_announcement_reads_announcement_id_announcements"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_announcement_reads_user_id_users"),
            sa.PrimaryKeyConstraint("id", name="pk_announcement_reads"),
            sa.UniqueConstraint("announcement_id", "user_id", name="uq_announcement_reads_announcement_user"),
        )
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcement_reads_announcement_id index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcement_reads', 'ix_announcement_reads_announcement_id'):
        op.create_index("ix_announcement_reads_announcement_id", "announcement_reads", ["announcement_id"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcement_reads_user_id index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcement_reads', 'ix_announcement_reads_user_id'):
        op.create_index("ix_announcement_reads_user_id", "announcement_reads", ["user_id"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcement_reads_last_seen_at index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcement_reads', 'ix_announcement_reads_last_seen_at'):
        op.create_index("ix_announcement_reads_last_seen_at", "announcement_reads", ["last_seen_at"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcement_reads_dismissed_at index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcement_reads', 'ix_announcement_reads_dismissed_at'):
        op.create_index("ix_announcement_reads_dismissed_at", "announcement_reads", ["dismissed_at"], unique=False)
    # BYS360_ANNOUNCEMENT_POPUP_IDEMPOTENT_PATCH: ix_announcement_reads_acknowledged_at index'i zaten varsa tekrar oluşturma.
    if not _bys360_has_index('announcement_reads', 'ix_announcement_reads_acknowledged_at'):
        op.create_index("ix_announcement_reads_acknowledged_at", "announcement_reads", ["acknowledged_at"], unique=False)


def downgrade():
    op.drop_index("ix_announcement_reads_acknowledged_at", table_name="announcement_reads")
    op.drop_index("ix_announcement_reads_dismissed_at", table_name="announcement_reads")
    op.drop_index("ix_announcement_reads_last_seen_at", table_name="announcement_reads")
    op.drop_index("ix_announcement_reads_user_id", table_name="announcement_reads")
    op.drop_index("ix_announcement_reads_announcement_id", table_name="announcement_reads")
    op.drop_table("announcement_reads")

    op.drop_index("ix_announcements_updated_by_user_id", table_name="announcements")
    op.drop_index("ix_announcements_created_by_user_id", table_name="announcements")
    op.drop_index("ix_announcements_media_type", table_name="announcements")
    op.drop_index("ix_announcements_publish_end_at", table_name="announcements")
    op.drop_index("ix_announcements_publish_start_at", table_name="announcements")
    op.drop_index("ix_announcements_target_unit_id", table_name="announcements")
    op.drop_index("ix_announcements_target_role", table_name="announcements")
    op.drop_index("ix_announcements_target_scope", table_name="announcements")
    op.drop_index("ix_announcements_show_rule", table_name="announcements")
    op.drop_index("ix_announcements_is_required", table_name="announcements")
    op.drop_index("ix_announcements_is_active", table_name="announcements")
    op.drop_index("ix_announcements_announcement_type", table_name="announcements")
    op.drop_table("announcements")
