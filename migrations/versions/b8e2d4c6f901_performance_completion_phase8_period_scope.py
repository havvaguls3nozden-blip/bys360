"""BYS360 Performans Tamamlama Faz 8 coklu donem ve kapsam yonetimi

Revision ID: b8e2d4c6f901
Revises: a7c9e3f1b240
Create Date: 2026-05-04 18:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "b8e2d4c6f901"
down_revision = "a7c9e3f1b240"
branch_labels = None
depends_on = None


# performance_phase8
# period_scope
# multiple_periods_same_year
# period_types_annual_semiannual_quarterly_monthly_special
# scope_types_all_unit_parent_unit_category_selected_personnel
# category_specific_period
# selected_personnel_period
# assignment_generation_scope_limited
# period_overlap_warning


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

    # Farklı projelerde periods tablosu adı değişmiş olabileceği için en yaygın adları güvenli kontrol eder.
    for table_name in ["performance_periods", "performance_evaluation_periods"]:
        if _has_table(bind, table_name):
            with op.batch_alter_table(table_name) as batch_op:
                if not _has_column(bind, table_name, "period_type"):
                    batch_op.add_column(sa.Column("period_type", sa.String(length=32), nullable=True))
                if not _has_column(bind, table_name, "scope_type"):
                    batch_op.add_column(sa.Column("scope_type", sa.String(length=64), nullable=True))
                if not _has_column(bind, table_name, "scope_value"):
                    batch_op.add_column(sa.Column("scope_value", sa.String(length=255), nullable=True))
                if not _has_column(bind, table_name, "special_reason"):
                    batch_op.add_column(sa.Column("special_reason", sa.String(length=64), nullable=True))
                if not _has_column(bind, table_name, "allow_overlap"):
                    batch_op.add_column(sa.Column("allow_overlap", sa.Boolean(), nullable=True))

    if not _has_table(bind, "performance_period_scope_personnel"):
        op.create_table(
            "performance_period_scope_personnel",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("period_id", sa.Integer(), nullable=False),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("scope_source", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    _seed_setting(bind, "performance_phase8", "multiple_periods_same_year", "true", "Aynı yıl içinde birden fazla performans dönemi desteklenir")
    _seed_setting(bind, "performance_phase8", "period_types", "annual,semiannual,quarterly,monthly,special", "Yıllık, 6 aylık, 3 aylık, aylık ve özel dönem tipleri")
    _seed_setting(bind, "performance_phase8", "scope_types", "all,unit,parent_unit,category,selected_personnel", "Dönem kapsam tipleri")
    _seed_setting(bind, "performance_phase8", "category_specific_period", "true", "Kategori/grup özel dönemleri desteklenir")
    _seed_setting(bind, "performance_phase8", "selected_personnel_period", "true", "Seçili personele özel dönem desteklenir")
    _seed_setting(bind, "performance_phase8", "assignment_generation_scope_limited", "true", "Görev üretimi dönem kapsamına göre sınırlanır")
    _seed_setting(bind, "performance_phase8", "period_overlap_warning", "true", "Aynı personel için çakışan dönemlerde uyarı üretilir")


def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "performance_period_scope_personnel"):
        op.drop_table("performance_period_scope_personnel")

    for table_name in ["performance_periods", "performance_evaluation_periods"]:
        if _has_table(bind, table_name):
            existing_cols = {c["name"] for c in sa.inspect(bind).get_columns(table_name)}
            with op.batch_alter_table(table_name) as batch_op:
                for col in ["allow_overlap", "special_reason", "scope_value", "scope_type", "period_type"]:
                    if col in existing_cols:
                        batch_op.drop_column(col)
