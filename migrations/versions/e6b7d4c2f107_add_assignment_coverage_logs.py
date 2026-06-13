"""add assignment coverage logs

Revision ID: e6b7d4c2f107
Revises: d2a8c1f9e006
Create Date: 2026-03-23 13:25:00
"""

from alembic import op
from sqlalchemy import inspect, text

revision = 'e6b7d4c2f107'
down_revision = 'd2a8c1f9e006'
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

    if not _has_table(bind, 'assignment_coverage_logs'):
        _run(
            """
            CREATE TABLE assignment_coverage_logs (
                id SERIAL PRIMARY KEY,
                period_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                manager_level INTEGER NULL,
                event_scope VARCHAR(30) NOT NULL DEFAULT 'generation',
                event_type VARCHAR(30) NOT NULL,
                severity VARCHAR(20) NOT NULL DEFAULT 'warning',
                reason VARCHAR(255) NULL,
                run_key VARCHAR(40) NULL,
                original_evaluator_id INTEGER NULL,
                acting_evaluator_id INTEGER NULL,
                delegation_id INTEGER NULL,
                created_by_user_id INTEGER NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )

    for stmt in (
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS period_id INTEGER",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS employee_id INTEGER",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS manager_level INTEGER NULL",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS event_scope VARCHAR(30) NOT NULL DEFAULT 'generation'",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS event_type VARCHAR(30) NOT NULL DEFAULT 'info'",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS severity VARCHAR(20) NOT NULL DEFAULT 'warning'",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS reason VARCHAR(255) NULL",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS run_key VARCHAR(40) NULL",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS original_evaluator_id INTEGER NULL",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS acting_evaluator_id INTEGER NULL",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS delegation_id INTEGER NULL",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER NULL",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()",
        "ALTER TABLE assignment_coverage_logs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW()",
    ):
        _run(stmt)

    cols = _columns(bind, 'assignment_coverage_logs')
    index_map = {
        'ix_assignment_coverage_logs_period_id': {'period_id'},
        'ix_assignment_coverage_logs_employee_id': {'employee_id'},
        'ix_assignment_coverage_logs_manager_level': {'manager_level'},
        'ix_assignment_coverage_logs_event_scope': {'event_scope'},
        'ix_assignment_coverage_logs_event_type': {'event_type'},
        'ix_assignment_coverage_logs_severity': {'severity'},
        'ix_assignment_coverage_logs_run_key': {'run_key'},
        'ix_assignment_coverage_logs_original_evaluator_id': {'original_evaluator_id'},
        'ix_assignment_coverage_logs_acting_evaluator_id': {'acting_evaluator_id'},
        'ix_assignment_coverage_logs_delegation_id': {'delegation_id'},
        'ix_assignment_coverage_logs_created_by_user_id': {'created_by_user_id'},
    }
    for index_name, needed in index_map.items():
        if needed.issubset(cols):
            _run(f"CREATE INDEX IF NOT EXISTS {index_name} ON assignment_coverage_logs ({', '.join(sorted(needed))})")


def downgrade():
    pass
