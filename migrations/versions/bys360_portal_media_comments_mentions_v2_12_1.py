"""Portal media upload limit, comment replies and mentions V2.12.1

Revision ID: bys360_portal_v2121
Revises: 733e87cebd16
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa


revision = "bys360_portal_v2121"
down_revision = "733e87cebd16"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "portal_post_comments" in tables:
        columns = {col["name"] for col in inspector.get_columns("portal_post_comments")}
        if "parent_comment_id" not in columns:
            op.add_column("portal_post_comments", sa.Column("parent_comment_id", sa.Integer(), nullable=True))
            op.create_index("ix_portal_post_comments_parent_comment_id", "portal_post_comments", ["parent_comment_id"], unique=False)
            op.create_foreign_key(
                "fk_portal_post_comments_parent_comment_id",
                "portal_post_comments",
                "portal_post_comments",
                ["parent_comment_id"],
                ["id"],
                ondelete="CASCADE",
            )

    if "portal_comment_mentions" not in tables:
        op.create_table(
            "portal_comment_mentions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("comment_id", sa.Integer(), nullable=False),
            sa.Column("mentioned_user_id", sa.Integer(), nullable=False),
            sa.Column("mentioned_by_user_id", sa.Integer(), nullable=True),
            sa.Column("source_type", sa.String(length=30), nullable=False, server_default="comment"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["comment_id"], ["portal_post_comments.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["mentioned_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["mentioned_by_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("comment_id", "mentioned_user_id", name="uq_portal_comment_mention_user"),
        )
        op.create_index("ix_portal_comment_mentions_comment_id", "portal_comment_mentions", ["comment_id"], unique=False)
        op.create_index("ix_portal_comment_mentions_mentioned_user_id", "portal_comment_mentions", ["mentioned_user_id"], unique=False)
        op.create_index("ix_portal_comment_mentions_mentioned_by_user_id", "portal_comment_mentions", ["mentioned_by_user_id"], unique=False)
        op.create_index("ix_portal_comment_mentions_source_type", "portal_comment_mentions", ["source_type"], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "portal_comment_mentions" in tables:
        op.drop_table("portal_comment_mentions")

    if "portal_post_comments" in tables:
        columns = {col["name"] for col in inspector.get_columns("portal_post_comments")}
        if "parent_comment_id" in columns:
            try:
                op.drop_constraint("fk_portal_post_comments_parent_comment_id", "portal_post_comments", type_="foreignkey")
            except Exception:
                pass
            try:
                op.drop_index("ix_portal_post_comments_parent_comment_id", table_name="portal_post_comments")
            except Exception:
                pass
            op.drop_column("portal_post_comments", "parent_comment_id")
