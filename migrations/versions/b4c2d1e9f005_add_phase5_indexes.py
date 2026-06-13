"""add phase5 indexes

Revision ID: b4c2d1e9f005
Revises: 9b6f2c11d003
Create Date: 2026-03-21 20:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = 'b4c2d1e9f005'
down_revision = '9b6f2c11d003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_perf_eval_period_status_employee', 'performance_evaluations', ['period_id', 'status', 'employee_id'], unique=False)
    op.create_index('ix_perf_eval_period_published', 'performance_evaluations', ['period_id', 'is_published_to_employee'], unique=False)
    op.create_index('ix_perf_item_eval_level', 'performance_evaluation_items', ['evaluation_id', 'manager_level'], unique=False)
    op.create_index('ix_perf_item_eval_criteria_level', 'performance_evaluation_items', ['evaluation_id', 'criteria_id', 'manager_level'], unique=False)
    op.create_index('ix_eval_assignment_period_status_evaluator', 'evaluation_assignments', ['period_id', 'status', 'evaluator_id'], unique=False)
    op.create_index('ix_eval_assignment_period_employee_level', 'evaluation_assignments', ['period_id', 'employee_id', 'manager_level'], unique=False)
    op.create_index('ix_snapshot_period_current_final', 'performance_result_snapshots', ['period_id', 'is_current', 'final_total_100'], unique=False)
    op.create_index('ix_snapshot_period_unit_current', 'performance_result_snapshots', ['period_id', 'organization_unit_id_snapshot', 'is_current'], unique=False)


def downgrade():
    op.drop_index('ix_snapshot_period_unit_current', table_name='performance_result_snapshots')
    op.drop_index('ix_snapshot_period_current_final', table_name='performance_result_snapshots')
    op.drop_index('ix_eval_assignment_period_employee_level', table_name='evaluation_assignments')
    op.drop_index('ix_eval_assignment_period_status_evaluator', table_name='evaluation_assignments')
    op.drop_index('ix_perf_item_eval_criteria_level', table_name='performance_evaluation_items')
    op.drop_index('ix_perf_item_eval_level', table_name='performance_evaluation_items')
    op.drop_index('ix_perf_eval_period_published', table_name='performance_evaluations')
    op.drop_index('ix_perf_eval_period_status_employee', table_name='performance_evaluations')
