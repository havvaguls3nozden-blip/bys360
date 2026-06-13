"""BYS360 Performans Tamamlama Faz 6 dusuk performans ust onay sureci

Revision ID: 9a5e1f4c2d60
Revises: 8e4a9c2d7b31
Create Date: 2026-05-04 17:35:00
"""

from alembic import op
import sqlalchemy as sa


revision = "9a5e1f4c2d60"
down_revision = "8e4a9c2d7b31"
branch_labels = None
depends_on = None


# performance_phase6
# low_score_approval
# low_score_threshold
# low_score_requires_upper_approval
# publish_block_until_approval
# process_record_required_after_approval
# fake_approval_records_forbidden
# first_second_low_score_tracking
# president_approval_card_detail_required


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

    if not _has_table(bind, "performance_low_score_process_events"):
        op.create_table(
            "performance_low_score_process_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("employee_id", sa.Integer(), nullable=True),
            sa.Column("period_id", sa.Integer(), nullable=True),
            sa.Column("scorecard_id", sa.Integer(), nullable=True),
            sa.Column("final_score", sa.Numeric(10, 2), nullable=True),
            sa.Column("calendar_year", sa.Integer(), nullable=True),
            sa.Column("repeat_level", sa.String(length=32), nullable=True),
            sa.Column("approval_status", sa.String(length=64), nullable=True),
            sa.Column("process_status", sa.String(length=64), nullable=True),
            sa.Column("publish_blocked", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    if _has_table(bind, "performance_president_approvals"):
        with op.batch_alter_table("performance_president_approvals") as batch_op:
            if not _has_column(bind, "performance_president_approvals", "phase6_low_score_marker"):
                batch_op.add_column(sa.Column("phase6_low_score_marker", sa.String(length=64), nullable=True))
            if not _has_column(bind, "performance_president_approvals", "publish_lock_label"):
                batch_op.add_column(sa.Column("publish_lock_label", sa.String(length=160), nullable=True))
            if not _has_column(bind, "performance_president_approvals", "low_score_repeat_level"):
                batch_op.add_column(sa.Column("low_score_repeat_level", sa.String(length=32), nullable=True))

    _seed_setting(bind, "performance_phase6", "low_score_threshold", "70", "70 altı sonuç düşük performans sürecine girer")
    _seed_setting(bind, "performance_phase6", "low_score_requires_upper_approval", "true", "70 altı sonuç Başkan/Üst Onay gerektirir")
    _seed_setting(bind, "performance_phase6", "publish_block_until_approval", "true", "Üst onay tamamlanmadan karne yayınlanmaz")
    _seed_setting(bind, "performance_phase6", "process_record_required_after_approval", "true", "Onay sonrası personel süreç kaydı zorunludur")
    _seed_setting(bind, "performance_phase6", "fake_approval_records_forbidden", "true", "Sahte Başkan onay kaydı üretilmez")
    _seed_setting(bind, "performance_phase6", "first_second_low_score_tracking", "true", "Aynı yıl ilk/ikinci düşük performans ayrımı yapılır")
    _seed_setting(bind, "performance_phase6", "president_approval_card_detail_required", "true", "Başkan karne inceleme detayı zorunludur")


def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "performance_president_approvals"):
        existing_cols = {c["name"] for c in sa.inspect(bind).get_columns("performance_president_approvals")}
        with op.batch_alter_table("performance_president_approvals") as batch_op:
            for col in ["low_score_repeat_level", "publish_lock_label", "phase6_low_score_marker"]:
                if col in existing_cols:
                    batch_op.drop_column(col)
    if _has_table(bind, "performance_low_score_process_events"):
        op.drop_table("performance_low_score_process_events")
