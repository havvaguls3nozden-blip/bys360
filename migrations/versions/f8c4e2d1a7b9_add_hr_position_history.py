"""add hr position history

Revision ID: f8c4e2d1a7b9
Revises: f4a12c9e0b21
Create Date: 2026-04-11 21:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'f8c4e2d1a7b9'
down_revision = 'f4a12c9e0b21'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'personnel_position_histories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organization_unit_id', sa.Integer(), nullable=True),
        sa.Column('manager_user_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('position_title', sa.String(length=150), nullable=False),
        sa.Column('position_grade', sa.String(length=50), nullable=True),
        sa.Column('assignment_type', sa.String(length=50), nullable=False, server_default='atama'),
        sa.Column('appointment_kind', sa.String(length=50), nullable=True),
        sa.Column('decision_no', sa.String(length=120), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('unit_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('parent_unit_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['manager_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_unit_id'], ['organization_units.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_position_histories_user_id'), 'personnel_position_histories', ['user_id'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_organization_unit_id'), 'personnel_position_histories', ['organization_unit_id'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_manager_user_id'), 'personnel_position_histories', ['manager_user_id'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_created_by_id'), 'personnel_position_histories', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_position_title'), 'personnel_position_histories', ['position_title'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_assignment_type'), 'personnel_position_histories', ['assignment_type'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_appointment_kind'), 'personnel_position_histories', ['appointment_kind'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_decision_no'), 'personnel_position_histories', ['decision_no'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_start_date'), 'personnel_position_histories', ['start_date'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_end_date'), 'personnel_position_histories', ['end_date'], unique=False)
    op.create_index(op.f('ix_personnel_position_histories_is_current'), 'personnel_position_histories', ['is_current'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_personnel_position_histories_is_current'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_end_date'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_start_date'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_decision_no'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_appointment_kind'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_assignment_type'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_position_title'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_created_by_id'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_manager_user_id'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_organization_unit_id'), table_name='personnel_position_histories')
    op.drop_index(op.f('ix_personnel_position_histories_user_id'), table_name='personnel_position_histories')
    op.drop_table('personnel_position_histories')
