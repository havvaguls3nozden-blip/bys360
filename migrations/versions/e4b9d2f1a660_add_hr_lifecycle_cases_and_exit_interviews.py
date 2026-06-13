"""add hr lifecycle cases and exit interviews

Revision ID: e4b9d2f1a660
Revises: d1a9f0c4b210
Create Date: 2026-04-11 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'e4b9d2f1a660'
down_revision = 'd1a9f0c4b210'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'personnel_lifecycle_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organization_unit_id', sa.Integer(), nullable=True),
        sa.Column('owner_user_id', sa.Integer(), nullable=True),
        sa.Column('coordinator_user_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('lifecycle_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('decision_no', sa.String(length=120), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_unit_id'], ['organization_units.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['coordinator_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_lifecycle_cases_user_id'), 'personnel_lifecycle_cases', ['user_id'], unique=False)
    op.create_index(op.f('ix_personnel_lifecycle_cases_status'), 'personnel_lifecycle_cases', ['status'], unique=False)
    op.create_index(op.f('ix_personnel_lifecycle_cases_lifecycle_type'), 'personnel_lifecycle_cases', ['lifecycle_type'], unique=False)
    op.create_index(op.f('ix_personnel_lifecycle_cases_target_date'), 'personnel_lifecycle_cases', ['target_date'], unique=False)

    op.create_table(
        'personnel_lifecycle_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['personnel_lifecycle_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_lifecycle_tasks_case_id'), 'personnel_lifecycle_tasks', ['case_id'], unique=False)
    op.create_index(op.f('ix_personnel_lifecycle_tasks_status'), 'personnel_lifecycle_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_personnel_lifecycle_tasks_due_date'), 'personnel_lifecycle_tasks', ['due_date'], unique=False)

    op.create_table(
        'personnel_exit_interviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lifecycle_case_id', sa.Integer(), nullable=True),
        sa.Column('interviewed_by_id', sa.Integer(), nullable=True),
        sa.Column('interview_date', sa.Date(), nullable=False),
        sa.Column('separation_reason', sa.String(length=50), nullable=True),
        sa.Column('satisfaction_score', sa.Integer(), nullable=True),
        sa.Column('would_rehire', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('risk_flags', sa.Text(), nullable=True),
        sa.Column('action_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lifecycle_case_id'], ['personnel_lifecycle_cases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['interviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_exit_interviews_user_id'), 'personnel_exit_interviews', ['user_id'], unique=False)
    op.create_index(op.f('ix_personnel_exit_interviews_interview_date'), 'personnel_exit_interviews', ['interview_date'], unique=False)
    op.create_index(op.f('ix_personnel_exit_interviews_separation_reason'), 'personnel_exit_interviews', ['separation_reason'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_personnel_exit_interviews_separation_reason'), table_name='personnel_exit_interviews')
    op.drop_index(op.f('ix_personnel_exit_interviews_interview_date'), table_name='personnel_exit_interviews')
    op.drop_index(op.f('ix_personnel_exit_interviews_user_id'), table_name='personnel_exit_interviews')
    op.drop_table('personnel_exit_interviews')
    op.drop_index(op.f('ix_personnel_lifecycle_tasks_due_date'), table_name='personnel_lifecycle_tasks')
    op.drop_index(op.f('ix_personnel_lifecycle_tasks_status'), table_name='personnel_lifecycle_tasks')
    op.drop_index(op.f('ix_personnel_lifecycle_tasks_case_id'), table_name='personnel_lifecycle_tasks')
    op.drop_table('personnel_lifecycle_tasks')
    op.drop_index(op.f('ix_personnel_lifecycle_cases_target_date'), table_name='personnel_lifecycle_cases')
    op.drop_index(op.f('ix_personnel_lifecycle_cases_lifecycle_type'), table_name='personnel_lifecycle_cases')
    op.drop_index(op.f('ix_personnel_lifecycle_cases_status'), table_name='personnel_lifecycle_cases')
    op.drop_index(op.f('ix_personnel_lifecycle_cases_user_id'), table_name='personnel_lifecycle_cases')
    op.drop_table('personnel_lifecycle_cases')
