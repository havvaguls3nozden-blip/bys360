"""BYS360 Performans Tamamlama Faz 7 gecmis yil karne puan arsivi

Revision ID: a7c9e3f1b240
Revises: 9a5e1f4c2d60
Create Date: 2026-05-04 17:55:00
"""

from alembic import op
import sqlalchemy as sa


revision = "a7c9e3f1b240"
down_revision = "9a5e1f4c2d60"
branch_labels = None
depends_on = None


# performance_phase7
# scorecard_archive
# historical_score_archive
# manual_old_score_entry
# excel_import_supported
# personnel_self_history_only
# manager_scope_limited_history
# president_admin_full_archive
# source_document_tracking


def _has_table(bind, table_name):
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


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

    if not _has_table(bind, "performance_scorecard_archives"):
        op.create_table(
            "performance_scorecard_archives",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("period_id", sa.Integer(), nullable=True),
            sa.Column("calendar_year", sa.Integer(), nullable=False),
            sa.Column("period_title", sa.String(length=255), nullable=False),
            sa.Column("final_score", sa.Numeric(10, 2), nullable=False),
            sa.Column("score_band", sa.String(length=64), nullable=True),
            sa.Column("source_type", sa.String(length=32), nullable=True),
            sa.Column("source_file_name", sa.String(length=255), nullable=True),
            sa.Column("source_document_path", sa.String(length=500), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    if not _has_table(bind, "performance_scorecard_archive_imports"):
        op.create_table(
            "performance_scorecard_archive_imports",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("source_file_name", sa.String(length=255), nullable=True),
            sa.Column("total_rows", sa.Integer(), nullable=True),
            sa.Column("valid_rows", sa.Integer(), nullable=True),
            sa.Column("error_rows", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=64), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    _seed_setting(bind, "performance_phase7", "historical_score_archive", "true", "Geçmiş yıl karne ve puan arşivi aktiftir")
    _seed_setting(bind, "performance_phase7", "manual_old_score_entry", "true", "Manuel eski puan girişi desteklenir")
    _seed_setting(bind, "performance_phase7", "excel_import_supported", "true", "Excel/toplu geçmiş puan aktarımı desteklenir")
    _seed_setting(bind, "performance_phase7", "personnel_self_history_only", "true", "Personel yalnızca kendi geçmişini görür")
    _seed_setting(bind, "performance_phase7", "manager_scope_limited_history", "true", "Yönetici yalnızca yetkili kapsam geçmişini görür")
    _seed_setting(bind, "performance_phase7", "president_admin_full_archive", "true", "Başkan/Admin genel geçmiş arşivi görür")
    _seed_setting(bind, "performance_phase7", "source_document_tracking", "true", "Arşiv kaynak belge bilgisi izlenir")


def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "performance_scorecard_archive_imports"):
        op.drop_table("performance_scorecard_archive_imports")
    if _has_table(bind, "performance_scorecard_archives"):
        op.drop_table("performance_scorecard_archives")
