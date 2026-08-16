"""reconstruct portal comment base schema

Revision ID: c3d8e5f19a02
Revises: 733e87cebd16
Create Date: 2026-08-16

TD-032 (portal_post_comments missing-migration repair): forensic proof
(see wave report) established that portal_groups, portal_posts and
portal_post_comments were never created by any Alembic migration in this
repo's tracked history (CASE E -- OUT_OF_BAND_SCHEMA_EVIDENCE_ONLY: the
live database's copy of these tables was provisioned directly from
SQLAlchemy metadata by
scripts/archive/pre_handover_20260708/windows/repair_bys360_live_portal_db_after_bys36043_v1_3.py,
never through Alembic). app/models/portal_models.py has been schema-stable
since this repo's root commit (only whitespace/import-order changes since
then), so it is used verbatim as the DDL source here.

Scope is limited to the 3 tables actually required, by hard FK, to unblock
bys360_portal_v2121's existing (unmodified) portal_comment_mentions
creation: portal_post_comments (direct target) requires portal_posts
(post_id, NOT NULL FK) which requires portal_groups (group_id FK target,
referenced table must exist regardless of the column's nullability). The
other 12 portal_* tables are not referenced by bys360_portal_v2121 and are
out of scope for this repair.

This migration only creates tables; it does not alter or remove any DDL
in bys360_portal_v2121 or any other existing revision.
"""

from alembic import op
import sqlalchemy as sa


revision = "c3d8e5f19a02"
down_revision = "733e87cebd16"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("group_type", sa.String(length=30), nullable=False, server_default="official"),
        sa.Column("visibility_scope", sa.String(length=30), nullable=False, server_default="members"),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL", name="fk_portal_groups_owner_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_portal_groups"),
    )
    op.create_index("ix_portal_groups_name", "portal_groups", ["name"], unique=False)
    op.create_index("ix_portal_groups_slug", "portal_groups", ["slug"], unique=True)
    op.create_index("ix_portal_groups_group_type", "portal_groups", ["group_type"], unique=False)
    op.create_index("ix_portal_groups_visibility_scope", "portal_groups", ["visibility_scope"], unique=False)
    op.create_index("ix_portal_groups_owner_user_id", "portal_groups", ["owner_user_id"], unique=False)
    op.create_index("ix_portal_groups_is_active", "portal_groups", ["is_active"], unique=False)

    op.create_table(
        "portal_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=True),
        sa.Column("wall_owner_user_id", sa.Integer(), nullable=True),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("post_type", sa.String(length=40), nullable=False, server_default="normal"),
        sa.Column("visibility_scope", sa.String(length=30), nullable=False, server_default="public"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="published"),
        sa.Column("comments_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_featured_home", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("target_unit_name", sa.String(length=180), nullable=True),
        sa.Column("target_upper_unit_name", sa.String(length=180), nullable=True),
        sa.Column("target_role_name", sa.String(length=80), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("hidden_at", sa.DateTime(), nullable=True),
        sa.Column("hidden_by_user_id", sa.Integer(), nullable=True),
        sa.Column("hidden_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="SET NULL", name="fk_portal_posts_author_user_id_users"),
        sa.ForeignKeyConstraint(["wall_owner_user_id"], ["users.id"], ondelete="SET NULL", name="fk_portal_posts_wall_owner_user_id_users"),
        sa.ForeignKeyConstraint(["group_id"], ["portal_groups.id"], ondelete="SET NULL", name="fk_portal_posts_group_id_portal_groups"),
        sa.ForeignKeyConstraint(["hidden_by_user_id"], ["users.id"], ondelete="SET NULL", name="fk_portal_posts_hidden_by_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_portal_posts"),
    )
    op.create_index("ix_portal_posts_author_user_id", "portal_posts", ["author_user_id"], unique=False)
    op.create_index("ix_portal_posts_wall_owner_user_id", "portal_posts", ["wall_owner_user_id"], unique=False)
    op.create_index("ix_portal_posts_group_id", "portal_posts", ["group_id"], unique=False)
    op.create_index("ix_portal_posts_post_type", "portal_posts", ["post_type"], unique=False)
    op.create_index("ix_portal_posts_visibility_scope", "portal_posts", ["visibility_scope"], unique=False)
    op.create_index("ix_portal_posts_status", "portal_posts", ["status"], unique=False)
    op.create_index("ix_portal_posts_is_pinned", "portal_posts", ["is_pinned"], unique=False)
    op.create_index("ix_portal_posts_is_featured_home", "portal_posts", ["is_featured_home"], unique=False)
    op.create_index("ix_portal_posts_target_unit_name", "portal_posts", ["target_unit_name"], unique=False)
    op.create_index("ix_portal_posts_target_upper_unit_name", "portal_posts", ["target_upper_unit_name"], unique=False)
    op.create_index("ix_portal_posts_target_role_name", "portal_posts", ["target_role_name"], unique=False)
    op.create_index("ix_portal_posts_published_at", "portal_posts", ["published_at"], unique=False)
    op.create_index("ix_portal_posts_hidden_by_user_id", "portal_posts", ["hidden_by_user_id"], unique=False)

    op.create_table(
        "portal_post_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=True),
        sa.Column("parent_comment_id", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="published"),
        sa.Column("hidden_at", sa.DateTime(), nullable=True),
        sa.Column("hidden_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["portal_posts.id"], ondelete="CASCADE", name="fk_portal_post_comments_post_id_portal_posts"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="SET NULL", name="fk_portal_post_comments_author_user_id_users"),
        sa.ForeignKeyConstraint(["parent_comment_id"], ["portal_post_comments.id"], ondelete="CASCADE", name="fk_portal_post_comments_parent_comment_id_portal_post_comments"),
        sa.ForeignKeyConstraint(["hidden_by_user_id"], ["users.id"], ondelete="SET NULL", name="fk_portal_post_comments_hidden_by_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_portal_post_comments"),
    )
    op.create_index("ix_portal_post_comments_post_id", "portal_post_comments", ["post_id"], unique=False)
    op.create_index("ix_portal_post_comments_author_user_id", "portal_post_comments", ["author_user_id"], unique=False)
    op.create_index("ix_portal_post_comments_parent_comment_id", "portal_post_comments", ["parent_comment_id"], unique=False)
    op.create_index("ix_portal_post_comments_status", "portal_post_comments", ["status"], unique=False)
    op.create_index("ix_portal_post_comments_hidden_by_user_id", "portal_post_comments", ["hidden_by_user_id"], unique=False)


def downgrade():
    op.drop_index("ix_portal_post_comments_hidden_by_user_id", table_name="portal_post_comments")
    op.drop_index("ix_portal_post_comments_status", table_name="portal_post_comments")
    op.drop_index("ix_portal_post_comments_parent_comment_id", table_name="portal_post_comments")
    op.drop_index("ix_portal_post_comments_author_user_id", table_name="portal_post_comments")
    op.drop_index("ix_portal_post_comments_post_id", table_name="portal_post_comments")
    op.drop_table("portal_post_comments")

    op.drop_index("ix_portal_posts_hidden_by_user_id", table_name="portal_posts")
    op.drop_index("ix_portal_posts_published_at", table_name="portal_posts")
    op.drop_index("ix_portal_posts_target_role_name", table_name="portal_posts")
    op.drop_index("ix_portal_posts_target_upper_unit_name", table_name="portal_posts")
    op.drop_index("ix_portal_posts_target_unit_name", table_name="portal_posts")
    op.drop_index("ix_portal_posts_is_featured_home", table_name="portal_posts")
    op.drop_index("ix_portal_posts_is_pinned", table_name="portal_posts")
    op.drop_index("ix_portal_posts_status", table_name="portal_posts")
    op.drop_index("ix_portal_posts_visibility_scope", table_name="portal_posts")
    op.drop_index("ix_portal_posts_post_type", table_name="portal_posts")
    op.drop_index("ix_portal_posts_group_id", table_name="portal_posts")
    op.drop_index("ix_portal_posts_wall_owner_user_id", table_name="portal_posts")
    op.drop_index("ix_portal_posts_author_user_id", table_name="portal_posts")
    op.drop_table("portal_posts")

    op.drop_index("ix_portal_groups_is_active", table_name="portal_groups")
    op.drop_index("ix_portal_groups_owner_user_id", table_name="portal_groups")
    op.drop_index("ix_portal_groups_visibility_scope", table_name="portal_groups")
    op.drop_index("ix_portal_groups_group_type", table_name="portal_groups")
    op.drop_index("ix_portal_groups_slug", table_name="portal_groups")
    op.drop_index("ix_portal_groups_name", table_name="portal_groups")
    op.drop_table("portal_groups")
