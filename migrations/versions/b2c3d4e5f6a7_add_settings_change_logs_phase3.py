"""Add settings change logs for settings phase3

Revision ID: b2c3d4e5f6a7
Revises: a9f2b7c4d001
Create Date: 2026-04-07 12:45:00
"""

from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a9f2b7c4d001"
branch_labels = None
depends_on = None


def _exec_many(statements):
    for stmt in statements:
        op.execute(stmt)


def upgrade():
    _exec_many([
        """
        CREATE TABLE IF NOT EXISTS settings_change_logs (
            id SERIAL PRIMARY KEY,
            actor_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            target_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            target_role_name VARCHAR(50) NULL,
            target_unit_name VARCHAR(150) NULL,
            change_scope VARCHAR(50) NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            summary VARCHAR(255) NULL,
            previous_state_json TEXT NULL,
            new_state_json TEXT NULL,
            reverted_from_log_id INTEGER NULL REFERENCES settings_change_logs(id) ON DELETE SET NULL,
            is_rollback BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_settings_change_logs_actor_user_id ON settings_change_logs(actor_user_id)",
        "CREATE INDEX IF NOT EXISTS ix_settings_change_logs_target_user_id ON settings_change_logs(target_user_id)",
        "CREATE INDEX IF NOT EXISTS ix_settings_change_logs_target_role_name ON settings_change_logs(target_role_name)",
        "CREATE INDEX IF NOT EXISTS ix_settings_change_logs_target_unit_name ON settings_change_logs(target_unit_name)",
        "CREATE INDEX IF NOT EXISTS ix_settings_change_logs_change_scope ON settings_change_logs(change_scope)",
        "CREATE INDEX IF NOT EXISTS ix_settings_change_logs_action_type ON settings_change_logs(action_type)",
        "CREATE INDEX IF NOT EXISTS ix_settings_change_logs_reverted_from_log_id ON settings_change_logs(reverted_from_log_id)",
        "CREATE INDEX IF NOT EXISTS ix_settings_change_logs_is_rollback ON settings_change_logs(is_rollback)",
    ])


def downgrade():
    _exec_many([
        "DROP INDEX IF EXISTS ix_settings_change_logs_is_rollback",
        "DROP INDEX IF EXISTS ix_settings_change_logs_reverted_from_log_id",
        "DROP INDEX IF EXISTS ix_settings_change_logs_action_type",
        "DROP INDEX IF EXISTS ix_settings_change_logs_change_scope",
        "DROP INDEX IF EXISTS ix_settings_change_logs_target_unit_name",
        "DROP INDEX IF EXISTS ix_settings_change_logs_target_role_name",
        "DROP INDEX IF EXISTS ix_settings_change_logs_target_user_id",
        "DROP INDEX IF EXISTS ix_settings_change_logs_actor_user_id",
        "DROP TABLE IF EXISTS settings_change_logs",
    ])
