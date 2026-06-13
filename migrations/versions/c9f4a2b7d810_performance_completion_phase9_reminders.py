"""BYS360 Performans Tamamlama Faz 9 otomatik hatirlatma aksatan amir

Revision ID: c9f4a2b7d810
Revises: b8e2d4c6f901
Create Date: 2026-05-04 18:35:00
"""

from alembic import op
import sqlalchemy as sa


revision = "c9f4a2b7d810"
down_revision = "b8e2d4c6f901"
branch_labels = None
depends_on = None


# performance_phase9
# reminder_policy
# pending_tasks_tracked
# due_soon_reminders
# overdue_manager_detection
# delayed_manager_report
# notification_payload
# email_log_payload
# duplicate_task_notification_prevented
# completed_tasks_ignored


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

    if not _has_table(bind, "performance_task_reminder_logs"):
        op.create_table(
            "performance_task_reminder_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("task_id", sa.Integer(), nullable=True),
            sa.Column("manager_id", sa.Integer(), nullable=True),
            sa.Column("employee_id", sa.Integer(), nullable=True),
            sa.Column("period_id", sa.Integer(), nullable=True),
            sa.Column("reminder_level", sa.String(length=32), nullable=True),
            sa.Column("channel", sa.String(length=32), nullable=True),
            sa.Column("subject", sa.String(length=255), nullable=True),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=64), nullable=True),
            sa.Column("overdue", sa.Boolean(), nullable=True),
            sa.Column("overdue_days", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    if not _has_table(bind, "performance_delayed_manager_snapshots"):
        op.create_table(
            "performance_delayed_manager_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("manager_id", sa.Integer(), nullable=True),
            sa.Column("period_id", sa.Integer(), nullable=True),
            sa.Column("pending_count", sa.Integer(), nullable=True),
            sa.Column("overdue_count", sa.Integer(), nullable=True),
            sa.Column("max_overdue_days", sa.Integer(), nullable=True),
            sa.Column("snapshot_date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    for table_name in ["performance_evaluation_assignments", "evaluation_assignments", "performance_tasks"]:
        if _has_table(bind, table_name):
            with op.batch_alter_table(table_name) as batch_op:
                if not _has_column(bind, table_name, "due_date"):
                    batch_op.add_column(sa.Column("due_date", sa.Date(), nullable=True))
                if not _has_column(bind, table_name, "last_reminder_at"):
                    batch_op.add_column(sa.Column("last_reminder_at", sa.DateTime(), nullable=True))
                if not _has_column(bind, table_name, "overdue_notified_at"):
                    batch_op.add_column(sa.Column("overdue_notified_at", sa.DateTime(), nullable=True))
                if not _has_column(bind, table_name, "is_overdue"):
                    batch_op.add_column(sa.Column("is_overdue", sa.Boolean(), nullable=True))

    _seed_setting(bind, "performance_phase9", "reminders_enabled", "true", "Bekleyen değerlendirme görevleri için otomatik hatırlatma aktiftir")
    _seed_setting(bind, "performance_phase9", "due_soon_days", "3", "Son tarih yaklaşma eşiği gün sayısı")
    _seed_setting(bind, "performance_phase9", "overdue_tracking_enabled", "true", "Süre geçen görevlerde aksatan amir takibi aktiftir")
    _seed_setting(bind, "performance_phase9", "default_channel", "both", "Varsayılan hatırlatma kanalı")
    _seed_setting(bind, "performance_phase9", "delayed_manager_report", "true", "Aksatan amir raporu aktiftir")
    _seed_setting(bind, "performance_phase9", "notification_log_required", "true", "Hatırlatma bildirim/mail log kaydı zorunludur")


def downgrade():
    bind = op.get_bind()

    for table_name in ["performance_evaluation_assignments", "evaluation_assignments", "performance_tasks"]:
        if _has_table(bind, table_name):
            existing_cols = {c["name"] for c in sa.inspect(bind).get_columns(table_name)}
            with op.batch_alter_table(table_name) as batch_op:
                for col in ["is_overdue", "overdue_notified_at", "last_reminder_at", "due_date"]:
                    if col in existing_cols:
                        batch_op.drop_column(col)

    if _has_table(bind, "performance_delayed_manager_snapshots"):
        op.drop_table("performance_delayed_manager_snapshots")
    if _has_table(bind, "performance_task_reminder_logs"):
        op.drop_table("performance_task_reminder_logs")
