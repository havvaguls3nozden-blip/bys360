"""add audit logs table

Revision ID: c1d9f4b2a001
Revises: 9b6f2c11d003
Create Date: 2026-03-22 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "c1d9f4b2a001"
down_revision = "9b6f2c11d003"
branch_labels = None
depends_on = None


def _has_table(bind, name: str) -> bool:
    return inspect(bind).has_table(name)


def _columns(bind, table: str) -> set[str]:
    return {col["name"] for col in inspect(bind).get_columns(table)} if _has_table(bind, table) else set()


def _run(stmt: str) -> None:
    op.execute(text(stmt))


def upgrade():
    bind = op.get_bind()

    if not _has_table(bind, "audit_logs"):
        _run(
            """
            CREATE TABLE audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NULL,
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(100) NOT NULL,
                entity_id INTEGER NULL,
                old_data_json TEXT NULL,
                new_data_json TEXT NULL,
                summary VARCHAR(255) NULL,
                endpoint VARCHAR(255) NULL,
                ip_address VARCHAR(64) NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
            """
        )

    statements = (
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_id INTEGER NULL",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS action VARCHAR(100) NOT NULL DEFAULT 'bilinmiyor'",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS entity_type VARCHAR(100) NOT NULL DEFAULT 'genel'",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS entity_id INTEGER NULL",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS old_data_json TEXT NULL",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS new_data_json TEXT NULL",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS summary VARCHAR(255) NULL",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS endpoint VARCHAR(255) NULL",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(64) NULL",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW()",
    )
    for stmt in statements:
        _run(stmt)

    cols = _columns(bind, "audit_logs")
    index_map = {
        "ix_audit_logs_action": {"action"},
        "ix_audit_logs_created_at": {"created_at"},
        "ix_audit_logs_entity_id": {"entity_id"},
        "ix_audit_logs_entity_type": {"entity_type"},
        "ix_audit_logs_endpoint": {"endpoint"},
        "ix_audit_logs_user_id": {"user_id"},
    }
    for index_name, needed in index_map.items():
        if needed.issubset(cols):
            _run(f"CREATE INDEX IF NOT EXISTS {index_name} ON audit_logs ({', '.join(sorted(needed))})")


def downgrade():
    op.execute(text("DROP TABLE IF EXISTS audit_logs CASCADE"))
