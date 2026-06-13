"""add leave delegation live flow backbone

Revision ID: d2a8c1f9e006
Revises: b4c2d1e9f005
Create Date: 2026-03-23 12:40:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision = 'd2a8c1f9e006'
down_revision = 'b4c2d1e9f005'
branch_labels = None
depends_on = None


def _has_table(bind, name: str) -> bool:
    return inspect(bind).has_table(name)


def _columns(bind, table: str) -> set[str]:
    return {col["name"] for col in inspect(bind).get_columns(table)} if _has_table(bind, table) else set()


def _run(stmt: str) -> None:
    op.execute(text(stmt))


def _ensure_indexes(table: str, index_map: dict[str, set[str]]) -> None:
    bind = op.get_bind()
    cols = _columns(bind, table)
    for index_name, needed in index_map.items():
        if needed.issubset(cols):
            _run(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({', '.join(sorted(needed))})")


def upgrade():
    bind = op.get_bind()

    if not _has_table(bind, 'leave_balances'):
        _run(
            """
            CREATE TABLE leave_balances (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                leave_type VARCHAR(50) NOT NULL,
                year INTEGER NULL,
                total_days DOUBLE PRECISION NOT NULL DEFAULT 0,
                carried_over_days DOUBLE PRECISION NOT NULL DEFAULT 0,
                used_days DOUBLE PRECISION NOT NULL DEFAULT 0,
                manual_override BOOLEAN NOT NULL DEFAULT FALSE,
                note TEXT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
    for stmt in (
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS user_id INTEGER",
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS leave_type VARCHAR(50) NOT NULL DEFAULT 'yillik'",
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS year INTEGER NULL",
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS total_days DOUBLE PRECISION NOT NULL DEFAULT 0",
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS carried_over_days DOUBLE PRECISION NOT NULL DEFAULT 0",
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS used_days DOUBLE PRECISION NOT NULL DEFAULT 0",
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS manual_override BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS note TEXT NULL",
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()",
        "ALTER TABLE leave_balances ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW()",
    ):
        _run(stmt)
    _ensure_indexes('leave_balances', {
        'ix_leave_balances_user_id': {'user_id'},
        'ix_leave_balances_leave_type': {'leave_type'},
        'ix_leave_balances_year': {'year'},
    })

    if not _has_table(bind, 'personnel_leaves'):
        _run(
            """
            CREATE TABLE personnel_leaves (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                period_id INTEGER NULL,
                leave_type VARCHAR(50) NOT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'onayli',
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                approved_day_count DOUBLE PRECISION NULL,
                start_half_day BOOLEAN NOT NULL DEFAULT FALSE,
                end_half_day BOOLEAN NOT NULL DEFAULT FALSE,
                blocks_performance_evaluation BOOLEAN NOT NULL DEFAULT TRUE,
                blocks_manager_duties BOOLEAN NOT NULL DEFAULT TRUE,
                description TEXT NULL,
                approved_by_id INTEGER NULL,
                approved_at TIMESTAMP NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
    for stmt in (
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS user_id INTEGER",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS period_id INTEGER NULL",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS leave_type VARCHAR(50) NOT NULL DEFAULT 'yillik'",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'onayli'",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS start_date DATE NOT NULL DEFAULT CURRENT_DATE",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS end_date DATE NOT NULL DEFAULT CURRENT_DATE",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS approved_day_count DOUBLE PRECISION NULL",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS start_half_day BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS end_half_day BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS blocks_performance_evaluation BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS blocks_manager_duties BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS description TEXT NULL",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS approved_by_id INTEGER NULL",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP NULL",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()",
        "ALTER TABLE personnel_leaves ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW()",
    ):
        _run(stmt)
    _ensure_indexes('personnel_leaves', {
        'ix_personnel_leaves_user_id': {'user_id'},
        'ix_personnel_leaves_period_id': {'period_id'},
        'ix_personnel_leaves_leave_type': {'leave_type'},
        'ix_personnel_leaves_status': {'status'},
        'ix_personnel_leaves_start_date': {'start_date'},
        'ix_personnel_leaves_end_date': {'end_date'},
    })

    if not _has_table(bind, 'attendance_exceptions'):
        _run(
            """
            CREATE TABLE attendance_exceptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                period_id INTEGER NULL,
                record_date DATE NOT NULL,
                exception_type VARCHAR(50) NOT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'onayli',
                day_fraction DOUBLE PRECISION NOT NULL DEFAULT 1,
                blocks_performance_evaluation BOOLEAN NOT NULL DEFAULT TRUE,
                blocks_manager_duties BOOLEAN NOT NULL DEFAULT TRUE,
                description TEXT NULL,
                approved_by_id INTEGER NULL,
                approved_at TIMESTAMP NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
    for stmt in (
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS user_id INTEGER",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS period_id INTEGER NULL",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS record_date DATE NOT NULL DEFAULT CURRENT_DATE",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS exception_type VARCHAR(50) NOT NULL DEFAULT 'devamsizlik'",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'onayli'",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS day_fraction DOUBLE PRECISION NOT NULL DEFAULT 1",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS blocks_performance_evaluation BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS blocks_manager_duties BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS description TEXT NULL",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS approved_by_id INTEGER NULL",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP NULL",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()",
        "ALTER TABLE attendance_exceptions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW()",
    ):
        _run(stmt)
    _ensure_indexes('attendance_exceptions', {
        'ix_attendance_exceptions_user_id': {'user_id'},
        'ix_attendance_exceptions_period_id': {'period_id'},
        'ix_attendance_exceptions_record_date': {'record_date'},
        'ix_attendance_exceptions_exception_type': {'exception_type'},
        'ix_attendance_exceptions_status': {'status'},
    })

    if not _has_table(bind, 'delegation_assignments'):
        _run(
            """
            CREATE TABLE delegation_assignments (
                id SERIAL PRIMARY KEY,
                delegator_user_id INTEGER NOT NULL,
                delegate_user_id INTEGER NOT NULL,
                source_leave_id INTEGER NULL,
                source_attendance_id INTEGER NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'aktif',
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                scope_type VARCHAR(30) NOT NULL DEFAULT 'performance',
                applies_level_1 BOOLEAN NOT NULL DEFAULT TRUE,
                applies_level_2 BOOLEAN NOT NULL DEFAULT TRUE,
                applies_level_3 BOOLEAN NOT NULL DEFAULT TRUE,
                note TEXT NULL,
                approved_by_id INTEGER NULL,
                approved_at TIMESTAMP NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
    for stmt in (
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS delegator_user_id INTEGER",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS delegate_user_id INTEGER",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS source_leave_id INTEGER NULL",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS source_attendance_id INTEGER NULL",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'aktif'",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS start_date DATE NOT NULL DEFAULT CURRENT_DATE",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS end_date DATE NOT NULL DEFAULT CURRENT_DATE",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS scope_type VARCHAR(30) NOT NULL DEFAULT 'performance'",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS applies_level_1 BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS applies_level_2 BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS applies_level_3 BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS note TEXT NULL",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS approved_by_id INTEGER NULL",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP NULL",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()",
        "ALTER TABLE delegation_assignments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW()",
    ):
        _run(stmt)
    _ensure_indexes('delegation_assignments', {
        'ix_delegation_assignments_delegator_user_id': {'delegator_user_id'},
        'ix_delegation_assignments_delegate_user_id': {'delegate_user_id'},
        'ix_delegation_assignments_source_leave_id': {'source_leave_id'},
        'ix_delegation_assignments_source_attendance_id': {'source_attendance_id'},
        'ix_delegation_assignments_status': {'status'},
        'ix_delegation_assignments_start_date': {'start_date'},
        'ix_delegation_assignments_end_date': {'end_date'},
    })

    for stmt in (
        "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS minimum_presence_days_for_evaluation DOUBLE PRECISION NOT NULL DEFAULT 0",
        "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS leave_skip_threshold_days DOUBLE PRECISION NULL",
        "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS absence_skip_threshold_days DOUBLE PRECISION NULL",
        "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS auto_skip_if_fully_absent BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS manager_delegation_required BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS evaluation_exempted BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS evaluation_exemption_reason VARCHAR(255) NULL",
        "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS employee_leave_days_in_period DOUBLE PRECISION NOT NULL DEFAULT 0",
        "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS employee_absence_days_in_period DOUBLE PRECISION NOT NULL DEFAULT 0",
        "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS employee_available_days_in_period DOUBLE PRECISION NOT NULL DEFAULT 0",
        "ALTER TABLE evaluation_assignments ADD COLUMN IF NOT EXISTS original_evaluator_id INTEGER NULL",
        "ALTER TABLE evaluation_assignments ADD COLUMN IF NOT EXISTS delegation_id INTEGER NULL",
        "ALTER TABLE evaluation_assignments ADD COLUMN IF NOT EXISTS assignment_source VARCHAR(30) NOT NULL DEFAULT 'standard'",
        "ALTER TABLE evaluation_assignments ADD COLUMN IF NOT EXISTS coverage_note VARCHAR(255) NULL",
    ):
        _run(stmt)

    _run("CREATE INDEX IF NOT EXISTS ix_performance_evaluations_evaluation_exempted ON performance_evaluations (evaluation_exempted)")


def downgrade():
    pass
