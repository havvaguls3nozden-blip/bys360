"""add surveys module

Revision ID: 8d5e7f31c002
Revises: 7c4d9a21b001
Create Date: 2026-03-21 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8d5e7f31c002"
down_revision = "7c4d9a21b001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "surveys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("survey_type", sa.String(length=50), nullable=False, server_default="kurum_ici"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("allow_multiple_submissions", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("start_at", sa.DateTime(), nullable=True),
        sa.Column("end_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_surveys_created_by_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_surveys"),
    )
    op.create_index("ix_surveys_title", "surveys", ["title"], unique=False)
    op.create_index("ix_surveys_survey_type", "surveys", ["survey_type"], unique=False)
    op.create_index("ix_surveys_created_by_user_id", "surveys", ["created_by_user_id"], unique=False)
    op.create_index("ix_surveys_start_at", "surveys", ["start_at"], unique=False)
    op.create_index("ix_surveys_end_at", "surveys", ["end_at"], unique=False)
    op.create_index("ix_surveys_status", "surveys", ["status"], unique=False)

    op.create_table(
        "survey_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("survey_id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=30), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], name="fk_survey_questions_survey_id_surveys"),
        sa.PrimaryKeyConstraint("id", name="pk_survey_questions"),
    )
    op.create_index("ix_survey_questions_survey_id", "survey_questions", ["survey_id"], unique=False)
    op.create_index("ix_survey_questions_question_type", "survey_questions", ["question_type"], unique=False)

    op.create_table(
        "survey_question_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_text", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["survey_questions.id"], name="fk_survey_question_options_question_id_survey_questions"),
        sa.PrimaryKeyConstraint("id", name="pk_survey_question_options"),
    )
    op.create_index("ix_survey_question_options_question_id", "survey_question_options", ["question_id"], unique=False)

    op.create_table(
        "survey_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("survey_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_value", sa.String(length=255), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], name="fk_survey_assignments_survey_id_surveys"),
        sa.PrimaryKeyConstraint("id", name="pk_survey_assignments"),
    )
    op.create_index("ix_survey_assignments_survey_id", "survey_assignments", ["survey_id"], unique=False)
    op.create_index("ix_survey_assignments_target_type", "survey_assignments", ["target_type"], unique=False)
    op.create_index("ix_survey_assignments_target_value", "survey_assignments", ["target_value"], unique=False)

    op.create_table(
        "survey_responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("survey_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("assignment_id", sa.Integer(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("anonymous_token", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], name="fk_survey_responses_survey_id_surveys"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_survey_responses_user_id_users"),
        sa.ForeignKeyConstraint(["assignment_id"], ["survey_assignments.id"], name="fk_survey_responses_assignment_id_survey_assignments"),
        sa.PrimaryKeyConstraint("id", name="pk_survey_responses"),
    )
    op.create_index("ix_survey_responses_survey_id", "survey_responses", ["survey_id"], unique=False)
    op.create_index("ix_survey_responses_user_id", "survey_responses", ["user_id"], unique=False)
    op.create_index("ix_survey_responses_assignment_id", "survey_responses", ["assignment_id"], unique=False)
    op.create_index("ix_survey_responses_submitted_at", "survey_responses", ["submitted_at"], unique=False)
    op.create_index("ix_survey_responses_is_completed", "survey_responses", ["is_completed"], unique=False)
    op.create_index("ix_survey_responses_anonymous_token", "survey_responses", ["anonymous_token"], unique=False)

    op.create_table(
        "survey_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("response_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_option_id", sa.Integer(), nullable=True),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("answer_number", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["response_id"], ["survey_responses.id"], name="fk_survey_answers_response_id_survey_responses"),
        sa.ForeignKeyConstraint(["question_id"], ["survey_questions.id"], name="fk_survey_answers_question_id_survey_questions"),
        sa.ForeignKeyConstraint(["selected_option_id"], ["survey_question_options.id"], name="fk_survey_answers_selected_option_id_survey_question_options"),
        sa.PrimaryKeyConstraint("id", name="pk_survey_answers"),
    )
    op.create_index("ix_survey_answers_response_id", "survey_answers", ["response_id"], unique=False)
    op.create_index("ix_survey_answers_question_id", "survey_answers", ["question_id"], unique=False)


def downgrade():
    op.drop_index("ix_survey_answers_question_id", table_name="survey_answers")
    op.drop_index("ix_survey_answers_response_id", table_name="survey_answers")
    op.drop_table("survey_answers")

    op.drop_index("ix_survey_responses_anonymous_token", table_name="survey_responses")
    op.drop_index("ix_survey_responses_is_completed", table_name="survey_responses")
    op.drop_index("ix_survey_responses_submitted_at", table_name="survey_responses")
    op.drop_index("ix_survey_responses_assignment_id", table_name="survey_responses")
    op.drop_index("ix_survey_responses_user_id", table_name="survey_responses")
    op.drop_index("ix_survey_responses_survey_id", table_name="survey_responses")
    op.drop_table("survey_responses")

    op.drop_index("ix_survey_assignments_target_value", table_name="survey_assignments")
    op.drop_index("ix_survey_assignments_target_type", table_name="survey_assignments")
    op.drop_index("ix_survey_assignments_survey_id", table_name="survey_assignments")
    op.drop_table("survey_assignments")

    op.drop_index("ix_survey_question_options_question_id", table_name="survey_question_options")
    op.drop_table("survey_question_options")

    op.drop_index("ix_survey_questions_question_type", table_name="survey_questions")
    op.drop_index("ix_survey_questions_survey_id", table_name="survey_questions")
    op.drop_table("survey_questions")

    op.drop_index("ix_surveys_status", table_name="surveys")
    op.drop_index("ix_surveys_end_at", table_name="surveys")
    op.drop_index("ix_surveys_start_at", table_name="surveys")
    op.drop_index("ix_surveys_created_by_user_id", table_name="surveys")
    op.drop_index("ix_surveys_survey_type", table_name="surveys")
    op.drop_index("ix_surveys_title", table_name="surveys")
    op.drop_table("surveys")
