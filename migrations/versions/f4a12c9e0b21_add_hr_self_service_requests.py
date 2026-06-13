
"""add hr self service requests

Revision ID: f4a12c9e0b21
Revises: e91c2d4f5a10
Create Date: 2026-04-11 20:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'f4a12c9e0b21'
down_revision = 'e91c2d4f5a10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'personnel_self_service_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('current_handler_id', sa.Integer(), nullable=True),
        sa.Column('last_action_by_id', sa.Integer(), nullable=True),
        sa.Column('request_type', sa.String(length=50), nullable=False, server_default='bilgi_guncelleme'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('requested_effective_date', sa.Date(), nullable=True),
        sa.Column('desired_completion_date', sa.Date(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('decision_note', sa.Text(), nullable=True),
        sa.Column('hr_visible', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['current_handler_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['last_action_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_self_service_requests_user_id'), 'personnel_self_service_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_created_by_id'), 'personnel_self_service_requests', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_current_handler_id'), 'personnel_self_service_requests', ['current_handler_id'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_last_action_by_id'), 'personnel_self_service_requests', ['last_action_by_id'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_request_type'), 'personnel_self_service_requests', ['request_type'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_priority'), 'personnel_self_service_requests', ['priority'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_status'), 'personnel_self_service_requests', ['status'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_requested_effective_date'), 'personnel_self_service_requests', ['requested_effective_date'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_desired_completion_date'), 'personnel_self_service_requests', ['desired_completion_date'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_submitted_at'), 'personnel_self_service_requests', ['submitted_at'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_requests_hr_visible'), 'personnel_self_service_requests', ['hr_visible'], unique=False)

    op.create_table(
        'personnel_self_service_request_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False, server_default='created'),
        sa.Column('from_status', sa.String(length=30), nullable=True),
        sa.Column('to_status', sa.String(length=30), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['request_id'], ['personnel_self_service_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_self_service_request_logs_request_id'), 'personnel_self_service_request_logs', ['request_id'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_request_logs_actor_user_id'), 'personnel_self_service_request_logs', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_request_logs_action'), 'personnel_self_service_request_logs', ['action'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_request_logs_from_status'), 'personnel_self_service_request_logs', ['from_status'], unique=False)
    op.create_index(op.f('ix_personnel_self_service_request_logs_to_status'), 'personnel_self_service_request_logs', ['to_status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_personnel_self_service_request_logs_to_status'), table_name='personnel_self_service_request_logs')
    op.drop_index(op.f('ix_personnel_self_service_request_logs_from_status'), table_name='personnel_self_service_request_logs')
    op.drop_index(op.f('ix_personnel_self_service_request_logs_action'), table_name='personnel_self_service_request_logs')
    op.drop_index(op.f('ix_personnel_self_service_request_logs_actor_user_id'), table_name='personnel_self_service_request_logs')
    op.drop_index(op.f('ix_personnel_self_service_request_logs_request_id'), table_name='personnel_self_service_request_logs')
    op.drop_table('personnel_self_service_request_logs')

    op.drop_index(op.f('ix_personnel_self_service_requests_hr_visible'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_submitted_at'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_desired_completion_date'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_requested_effective_date'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_status'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_priority'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_request_type'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_last_action_by_id'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_current_handler_id'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_created_by_id'), table_name='personnel_self_service_requests')
    op.drop_index(op.f('ix_personnel_self_service_requests_user_id'), table_name='personnel_self_service_requests')
    op.drop_table('personnel_self_service_requests')
