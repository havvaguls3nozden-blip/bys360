"""BYS360 Performans Tamamlama Faz 4 3. amir opsiyonelligi

Revision ID: 7c2d4f8a91b0
Revises: 6d3f8a1b2c44
Create Date: 2026-05-04 16:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = "7c2d4f8a91b0"
down_revision = "6d3f8a1b2c44"
branch_labels = None
depends_on = None


PHASE4_MARKERS = [
    "performance.phase4.third_manager_enabled",
    "performance.phase4.third_manager_mode",
    "performance.phase4.hide_empty_third_manager_column",
    "performance.phase4.prevent_fake_third_manager_task",
    "performance.phase4.third_manager_comment_no_score",
    "performance.phase4.normalize_manager_weights_100",
]


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

    if _has_table(bind, "evaluation_assignments"):
        with op.batch_alter_table("evaluation_assignments") as batch_op:
            if not _has_column(bind, "evaluation_assignments", "third_manager_mode"):
                batch_op.add_column(sa.Column("third_manager_mode", sa.String(length=32), nullable=True))
            if not _has_column(bind, "evaluation_assignments", "third_manager_task_required"):
                batch_op.add_column(sa.Column("third_manager_task_required", sa.Boolean(), nullable=True))
            if not _has_column(bind, "evaluation_assignments", "third_manager_score_required"):
                batch_op.add_column(sa.Column("third_manager_score_required", sa.Boolean(), nullable=True))
            if not _has_column(bind, "evaluation_assignments", "third_manager_comment_required"):
                batch_op.add_column(sa.Column("third_manager_comment_required", sa.Boolean(), nullable=True))

    _seed_setting(bind, "performance_phase4", "third_manager_enabled", "true", "3. amir opsiyonelliği aktif")
    _seed_setting(bind, "performance_phase4", "third_manager_mode", "comment", "3. amir varsayılan yorum/görüş modu")
    _seed_setting(bind, "performance_phase4", "hide_empty_third_manager_column", "true", "3. amir yoksa boş kolon gösterilmez")
    _seed_setting(bind, "performance_phase4", "prevent_fake_third_manager_task", "true", "3. amir yoksa sahte görev üretilmez")
    _seed_setting(bind, "performance_phase4", "third_manager_comment_no_score", "true", "3. amir yorum modunda puan beklemez")
    _seed_setting(bind, "performance_phase4", "normalize_manager_weights_100", "true", "Amir ağırlıkları yüzde 100'e normalize edilir")


def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "evaluation_assignments"):
        existing_cols = {c["name"] for c in sa.inspect(bind).get_columns("evaluation_assignments")}
        with op.batch_alter_table("evaluation_assignments") as batch_op:
            for col in [
                "third_manager_comment_required",
                "third_manager_score_required",
                "third_manager_task_required",
                "third_manager_mode",
            ]:
                if col in existing_cols:
                    batch_op.drop_column(col)

# BYS360_PHASE4_MIGRATION_CHAIN_AND_GATE_FIX: Faz 4 migration doğru Faz 3 head'ine bağlıdır.
