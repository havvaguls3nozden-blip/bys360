"""add survey logic and partial responses

Revision ID: g6c1d2e3f4a5
Revises: f5b1c2d3e4f9
Create Date: 2026-04-29

BYS360 canlı kapsam idempotent düzeltmesi.

Bu migration canlıda survey/anket tabloları daha önce schema guard veya ara overlay ile
oluşmuşsa DuplicateColumn hatasına düşmemek için güvenli hale getirilmiştir.
Mevcut kolonlara dokunmaz; eksik bilinen kolonları IF NOT EXISTS mantığıyla ekler.
"""
from alembic import op
import sqlalchemy as sa


revision = "g6c1d2e3f4a5"
down_revision = "f5b1c2d3e4f9"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    try:
        return table_name in inspector.get_table_names()
    except Exception:
        return False


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    try:
        return any(col.get("name") == column_name for col in inspector.get_columns(table_name))
    except Exception:
        return False


def _add_column_if_missing(inspector, table_name: str, column: sa.Column) -> None:
    if _has_table(inspector, table_name) and not _has_column(inspector, table_name, column.name):
        op.add_column(table_name, column)


def _create_table_if_missing(inspector, table_name: str, *columns) -> None:
    if not _has_table(inspector, table_name):
        op.create_table(table_name, *columns)


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Anket soru mantığı / yardımcı metin alanları.
    # Kolon zaten varsa tekrar eklenmez; böylece canlıda DuplicateColumn oluşmaz.
    _add_column_if_missing(inspector, "survey_questions", sa.Column("helper_text", sa.Text(), nullable=True))
    _add_column_if_missing(inspector, "survey_questions", sa.Column("logic_json", sa.JSON(), nullable=True))
    _add_column_if_missing(inspector, "survey_questions", sa.Column("visibility_rule", sa.Text(), nullable=True))
    _add_column_if_missing(inspector, "survey_questions", sa.Column("is_conditional", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    _add_column_if_missing(inspector, "survey_questions", sa.Column("display_order", sa.Integer(), nullable=True))

    # Anket genel ayarları.
    _add_column_if_missing(inspector, "surveys", sa.Column("logic_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    _add_column_if_missing(inspector, "surveys", sa.Column("allow_partial_responses", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    _add_column_if_missing(inspector, "surveys", sa.Column("show_progress", sa.Boolean(), nullable=False, server_default=sa.text("true")))

    # Kısmi cevap / taslak cevap alanları.
    _add_column_if_missing(inspector, "survey_responses", sa.Column("is_partial", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    _add_column_if_missing(inspector, "survey_responses", sa.Column("completion_percent", sa.Integer(), nullable=False, server_default=sa.text("0")))
    _add_column_if_missing(inspector, "survey_responses", sa.Column("current_step", sa.Integer(), nullable=True))
    _add_column_if_missing(inspector, "survey_responses", sa.Column("last_saved_at", sa.DateTime(), nullable=True))

    # Bazı sürümlerde taslak cevaplar ayrı tablo olarak beklenebilir; yoksa güvenli şekilde oluşturulur.
    _create_table_if_missing(
        inspector,
        "survey_response_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("survey_id", sa.Integer(), nullable=True, index=True),
        sa.Column("user_id", sa.Integer(), nullable=True, index=True),
        sa.Column("response_id", sa.Integer(), nullable=True, index=True),
        sa.Column("draft_payload", sa.JSON(), nullable=True),
        sa.Column("current_step", sa.Integer(), nullable=True),
        sa.Column("completion_percent", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Soru görünürlük/koşul mantığı ayrı tabloyla modellenmişse eksik olmasın; mevcutsa dokunulmaz.
    _create_table_if_missing(
        inspector,
        "survey_question_logic_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("survey_id", sa.Integer(), nullable=True, index=True),
        sa.Column("question_id", sa.Integer(), nullable=True, index=True),
        sa.Column("source_question_id", sa.Integer(), nullable=True, index=True),
        sa.Column("operator", sa.String(length=50), nullable=True),
        sa.Column("expected_value", sa.Text(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=True),
        sa.Column("target_question_id", sa.Integer(), nullable=True, index=True),
        sa.Column("rule_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    # Canlı kapsam hijyeni: downgrade tarafında veri/kolon silinmez.
    # Bu dosyanın amacı upgrade zincirini güvenli ve idempotent hale getirmektir.
    pass
