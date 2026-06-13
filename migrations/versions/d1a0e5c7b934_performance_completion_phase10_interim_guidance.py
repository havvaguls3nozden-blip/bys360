"""BYS360 Performans Tamamlama Faz 10 donem ici not gelisim onerisi bagi

Revision ID: d1a0e5c7b934
Revises: c9f4a2b7d810
Create Date: 2026-05-04 18:55:00
"""

from alembic import op
import sqlalchemy as sa


revision = "d1a0e5c7b934"
down_revision = "c9f4a2b7d810"
branch_labels = None
depends_on = None


# performance_phase10
# interim_guidance_link
# development_guidance
# guidance_write_area_required
# group_head_approval_required
# personnel_visible_after_scorecard_publish
# low_score_publish_lock_respected
# technical_language_hidden
# empty_note_message_corporate


def _has_table(bind, table_name):
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(bind, table_name, column_name):
    inspector = sa.inspect(bind)
    try:
        return column_name in [c["name"] for c in inspector.get_columns(table_name)]
    except Exception:
        return False


def _seed_setting(bind, module_key, setting_key, value, label):
    if not _has_table(bind, "module_settings"):
        return
    cols = {c["name"] for c in sa.inspect(bind).get_columns("module_settings")}
    if not {"module_key", "setting_key"}.issubset(cols):
        return

    existing = bind.execute(
        sa.text("SELECT id FROM module_settings WHERE module_key=:m AND setting_key=:s LIMIT 1"),
        {"m": module_key, "s": setting_key},
    ).fetchone()
    if existing:
        return

    values = {"module_key": module_key, "setting_key": setting_key}
    insert_cols = ["module_key", "setting_key"]
    insert_vals = [":module_key", ":setting_key"]

    if "setting_value" in cols:
        values["setting_value"] = value
        insert_cols.append("setting_value")
        insert_vals.append(":setting_value")
    elif "value" in cols:
        values["value"] = value
        insert_cols.append("value")
        insert_vals.append(":value")

    if "label" in cols:
        values["label"] = label
        insert_cols.append("label")
        insert_vals.append(":label")
    if "description" in cols:
        values["description"] = label
        insert_cols.append("description")
        insert_vals.append(":description")
    if "created_at" in cols:
        insert_cols.append("created_at")
        insert_vals.append("CURRENT_TIMESTAMP")
    if "updated_at" in cols:
        insert_cols.append("updated_at")
        insert_vals.append("CURRENT_TIMESTAMP")

    bind.execute(
        sa.text("INSERT INTO module_settings (" + ", ".join(insert_cols) + ") VALUES (" + ", ".join(insert_vals) + ")"),
        values,
    )


def upgrade():
    bind = op.get_bind()

    if not _has_table(bind, "performance_development_guidance"):
        op.create_table(
            "performance_development_guidance",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("period_id", sa.Integer(), nullable=False),
            sa.Column("scorecard_id", sa.Integer(), nullable=True),
            sa.Column("interim_note_id", sa.Integer(), nullable=True),
            sa.Column("guidance_text", sa.Text(), nullable=False),
            sa.Column("source_summary", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=64), nullable=True),
            sa.Column("group_head_approved", sa.Boolean(), nullable=True),
            sa.Column("group_head_approved_by_id", sa.Integer(), nullable=True),
            sa.Column("group_head_approved_at", sa.DateTime(), nullable=True),
            sa.Column("visible_to_personnel", sa.Boolean(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    # Mevcut dönem içi not tablosu varsa güvenli bağ alanları eklenir.
    for table_name in ["performance_interim_notes", "interim_notes", "performance_period_notes"]:
        if _has_table(bind, table_name):
            with op.batch_alter_table(table_name) as batch_op:
                if not _has_column(bind, table_name, "development_guidance_id"):
                    batch_op.add_column(sa.Column("development_guidance_id", sa.Integer(), nullable=True))
                if not _has_column(bind, table_name, "converted_to_guidance"):
                    batch_op.add_column(sa.Column("converted_to_guidance", sa.Boolean(), nullable=True))

    _seed_setting(bind, "performance_phase10", "interim_notes_to_guidance_link", "true", "Dönem içi notlar gelişim önerisine bağlanır")
    _seed_setting(bind, "performance_phase10", "guidance_write_area_required", "true", "Gelişim önerisi yazma alanı desteklenir")
    _seed_setting(bind, "performance_phase10", "group_head_approval_required", "true", "Gelişim önerisi için Grup Başkanı onayı gerekir")
    _seed_setting(bind, "performance_phase10", "personnel_visible_after_scorecard_publish", "true", "Gelişim önerisi karne yayınlandıktan sonra personele görünür")
    _seed_setting(bind, "performance_phase10", "low_score_publish_lock_respected", "true", "Düşük performans yayın kilidi gelişim önerisi görünürlüğünde dikkate alınır")
    _seed_setting(bind, "performance_phase10", "technical_language_hidden", "true", "Gelişim önerisi ekranında teknik dil gizlenir")
    _seed_setting(bind, "performance_phase10", "empty_note_message_corporate", "true", "Boş dönem içi not mesajları kurumsal Türkçe gösterilir")


def downgrade():
    bind = op.get_bind()
    for table_name in ["performance_interim_notes", "interim_notes", "performance_period_notes"]:
        if _has_table(bind, table_name):
            existing_cols = {c["name"] for c in sa.inspect(bind).get_columns(table_name)}
            with op.batch_alter_table(table_name) as batch_op:
                for col in ["converted_to_guidance", "development_guidance_id"]:
                    if col in existing_cols:
                        batch_op.drop_column(col)

    if _has_table(bind, "performance_development_guidance"):
        op.drop_table("performance_development_guidance")
