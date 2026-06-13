"""BYS360 Performans Tamamlama Faz 12 final gate canli hazirlik

Revision ID: f3c8d2a6e501
Revises: e2b6a9c4f130
Create Date: 2026-05-04 19:35:00
"""

from alembic import op
import sqlalchemy as sa


revision = "f3c8d2a6e501"
down_revision = "e2b6a9c4f130"
branch_labels = None
depends_on = None


# performance_phase12
# final_readiness
# final_gate
# ten_scenario_test
# migration_chain_required
# jinja_gate_required
# critical_route_smoke_required
# live_readiness_report
# all_previous_phases_chained


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

    if not _has_table(bind, "performance_final_readiness_audits"):
        op.create_table(
            "performance_final_readiness_audits",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("audit_key", sa.String(length=120), nullable=True),
            sa.Column("score", sa.Numeric(10, 2), nullable=True),
            sa.Column("passed", sa.Boolean(), nullable=True),
            sa.Column("scenario_total", sa.Integer(), nullable=True),
            sa.Column("scenario_ok", sa.Integer(), nullable=True),
            sa.Column("scenario_failed", sa.Integer(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    _seed_setting(bind, "performance_phase12", "final_gate", "true", "Final gate aktiftir")
    _seed_setting(bind, "performance_phase12", "ten_scenario_test", "true", "10 kritik iş senaryosu testi zorunludur")
    _seed_setting(bind, "performance_phase12", "migration_chain_required", "true", "Migration zinciri tek head ile doğrulanır")
    _seed_setting(bind, "performance_phase12", "jinja_gate_required", "true", "Kritik Jinja şablonları doğrulanır")
    _seed_setting(bind, "performance_phase12", "critical_route_smoke_required", "true", "Kritik route smoke testi zorunludur")
    _seed_setting(bind, "performance_phase12", "live_readiness_report", "true", "Canlı hazırlık raporu üretilebilir")
    _seed_setting(bind, "performance_phase12", "all_previous_phases_chained", "true", "Faz 1-11 zinciri korunur")


def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "performance_final_readiness_audits"):
        op.drop_table("performance_final_readiness_audits")
