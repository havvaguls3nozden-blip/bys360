"""add communication phase2 editors

Revision ID: d2f1a2b3e4f6
Revises: c9f1a2b3d4e5
Create Date: 2026-04-10 09:40:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2f1a2b3e4f6"
down_revision = "c9f1a2b3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "communication_bulletin_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bulletin_id", sa.Integer(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("bulletin_type", sa.String(length=50), nullable=False, server_default="duyuru"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("change_note", sa.String(length=500), nullable=True),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bulletin_id"], ["communication_bulletins.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bulletin_id", "version_no", name="uq_comm_bulletin_revision_version"),
    )
    op.create_index(op.f("ix_communication_bulletin_revisions_bulletin_id"), "communication_bulletin_revisions", ["bulletin_id"], unique=False)
    op.create_index(op.f("ix_communication_bulletin_revisions_version_no"), "communication_bulletin_revisions", ["version_no"], unique=False)

    op.create_table(
        "communication_survey_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("survey_type", sa.String(length=50), nullable=False, server_default="kurum_ici"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_survey_templates_title"), "communication_survey_templates", ["title"], unique=False)
    op.create_index(op.f("ix_communication_survey_templates_survey_type"), "communication_survey_templates", ["survey_type"], unique=False)
    op.create_index(op.f("ix_communication_survey_templates_is_active"), "communication_survey_templates", ["is_active"], unique=False)

    op.create_table(
        "communication_survey_template_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=30), nullable=False, server_default="single_choice"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("options_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["communication_survey_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_communication_survey_template_questions_template_id"), "communication_survey_template_questions", ["template_id"], unique=False)
    op.create_index(op.f("ix_communication_survey_template_questions_question_type"), "communication_survey_template_questions", ["question_type"], unique=False)
    op.create_index(op.f("ix_communication_survey_template_questions_sort_order"), "communication_survey_template_questions", ["sort_order"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_communication_survey_template_questions_sort_order"), table_name="communication_survey_template_questions")
    op.drop_index(op.f("ix_communication_survey_template_questions_question_type"), table_name="communication_survey_template_questions")
    op.drop_index(op.f("ix_communication_survey_template_questions_template_id"), table_name="communication_survey_template_questions")
    op.drop_table("communication_survey_template_questions")

    op.drop_index(op.f("ix_communication_survey_templates_is_active"), table_name="communication_survey_templates")
    op.drop_index(op.f("ix_communication_survey_templates_survey_type"), table_name="communication_survey_templates")
    op.drop_index(op.f("ix_communication_survey_templates_title"), table_name="communication_survey_templates")
    op.drop_table("communication_survey_templates")

    op.drop_index(op.f("ix_communication_bulletin_revisions_version_no"), table_name="communication_bulletin_revisions")
    op.drop_index(op.f("ix_communication_bulletin_revisions_bulletin_id"), table_name="communication_bulletin_revisions")
    op.drop_table("communication_bulletin_revisions")
