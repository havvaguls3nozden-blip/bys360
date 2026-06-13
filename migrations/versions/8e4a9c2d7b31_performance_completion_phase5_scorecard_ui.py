"""BYS360 Performans Tamamlama Faz 5 karne puanlama UI ayarlari

Revision ID: 8e4a9c2d7b31
Revises: 7c2d4f8a91b0
Create Date: 2026-05-04 17:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "8e4a9c2d7b31"
down_revision = "7c2d4f8a91b0"
branch_labels = None
depends_on = None


# performance_phase5
# phase5_scorecard_ui
# hide_technical_language
# large_score_surface
# manager_opinion_cards
# readable_criteria_table
# process_history_turkish
# mobile_scorecard_responsive
# president_scorecard_detail


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
    _seed_setting(bind, "performance_phase5", "hide_technical_language", "true", "Karne ekranlarında teknik/geliştirici dili gizlenir")
    _seed_setting(bind, "performance_phase5", "large_score_surface", "true", "Nihai puan alanı daha okunur gösterilir")
    _seed_setting(bind, "performance_phase5", "manager_opinion_cards", "true", "Amir görüşleri ayrı kartlarda gösterilir")
    _seed_setting(bind, "performance_phase5", "readable_criteria_table", "true", "Kriter bazlı puan tablosu okunur hale getirilir")
    _seed_setting(bind, "performance_phase5", "process_history_turkish", "true", "Süreç geçmişi Türkçe kurumsal ifadelerle gösterilir")
    _seed_setting(bind, "performance_phase5", "mobile_scorecard_responsive", "true", "Karne ekranları mobil uyumlu tutulur")
    _seed_setting(bind, "performance_phase5", "president_scorecard_detail", "true", "Başkan karne inceleme detay yüzeyi korunur")


def downgrade():
    # Ayar kayıtları canlıda geriye dönük iz bırakması için silinmez.
    pass
