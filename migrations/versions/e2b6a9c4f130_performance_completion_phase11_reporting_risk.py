"""BYS360 Performans Tamamlama Faz 11 raporlama dashboard risk analizi

Revision ID: e2b6a9c4f130
Revises: d1a0e5c7b934
Create Date: 2026-05-04 19:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "e2b6a9c4f130"
down_revision = "d1a0e5c7b934"
branch_labels = None
depends_on = None


# performance_phase11
# reporting_risk
# executive_dashboard
# risk_analysis
# delayed_manager_summary
# category_average_privacy
# scope_limited_reports
# president_admin_full_visibility
# report_export_contract


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

    if not _has_table(bind, "performance_dashboard_snapshots"):
        op.create_table(
            "performance_dashboard_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("period_id", sa.Integer(), nullable=True),
            sa.Column("scope_type", sa.String(length=64), nullable=True),
            sa.Column("scope_value", sa.String(length=255), nullable=True),
            sa.Column("total_records", sa.Integer(), nullable=True),
            sa.Column("average_score", sa.Numeric(10, 2), nullable=True),
            sa.Column("low_score_count", sa.Integer(), nullable=True),
            sa.Column("high_score_count", sa.Integer(), nullable=True),
            sa.Column("risk_count", sa.Integer(), nullable=True),
            sa.Column("overdue_manager_count", sa.Integer(), nullable=True),
            sa.Column("snapshot_date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    if not _has_table(bind, "performance_risk_analysis_snapshots"):
        op.create_table(
            "performance_risk_analysis_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("employee_id", sa.Integer(), nullable=True),
            sa.Column("period_id", sa.Integer(), nullable=True),
            sa.Column("risk_type", sa.String(length=64), nullable=True),
            sa.Column("risk_level", sa.String(length=32), nullable=True),
            sa.Column("risk_score", sa.Numeric(10, 2), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("recommended_action", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    _seed_setting(bind, "performance_phase11", "executive_dashboard", "true", "Yönetici dashboard görünürlüğü aktiftir")
    _seed_setting(bind, "performance_phase11", "risk_analysis", "true", "Riskli personel ve süreç analizi aktiftir")
    _seed_setting(bind, "performance_phase11", "delayed_manager_summary", "true", "Aksatan amir özeti aktiftir")
    _seed_setting(bind, "performance_phase11", "category_average_privacy", "true", "Kategori ortalamalarında kişi detayı gizlenir")
    _seed_setting(bind, "performance_phase11", "scope_limited_reports", "true", "Raporlar yetki kapsamına göre sınırlandırılır")
    _seed_setting(bind, "performance_phase11", "president_admin_full_visibility", "true", "Başkan/Admin kurum geneli rapor görünürlüğüne sahiptir")
    _seed_setting(bind, "performance_phase11", "report_export_contract", "true", "Rapor dışa aktarım sözleşmesi aktiftir")


def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "performance_risk_analysis_snapshots"):
        op.drop_table("performance_risk_analysis_snapshots")
    if _has_table(bind, "performance_dashboard_snapshots"):
        op.drop_table("performance_dashboard_snapshots")
