"""add hr handover and clearance records

Revision ID: f1c8e2a7b450
Revises: e4b9d2f1a660
Create Date: 2026-04-11 20:05:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1c8e2a7b450'
down_revision = 'e4b9d2f1a660'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'personnel_handover_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lifecycle_case_id', sa.Integer(), nullable=True),
        sa.Column('organization_unit_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('operation_type', sa.String(length=30), nullable=False, server_default='offboarding'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('planned_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('handover_no', sa.String(length=120), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lifecycle_case_id'], ['personnel_lifecycle_cases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_unit_id'], ['organization_units.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_handover_records_user_id'), 'personnel_handover_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_lifecycle_case_id'), 'personnel_handover_records', ['lifecycle_case_id'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_organization_unit_id'), 'personnel_handover_records', ['organization_unit_id'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_created_by_id'), 'personnel_handover_records', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_approved_by_id'), 'personnel_handover_records', ['approved_by_id'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_operation_type'), 'personnel_handover_records', ['operation_type'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_status'), 'personnel_handover_records', ['status'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_planned_date'), 'personnel_handover_records', ['planned_date'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_due_date'), 'personnel_handover_records', ['due_date'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_completed_at'), 'personnel_handover_records', ['completed_at'], unique=False)
    op.create_index(op.f('ix_personnel_handover_records_handover_no'), 'personnel_handover_records', ['handover_no'], unique=False)

    op.create_table(
        'personnel_handover_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('handover_id', sa.Integer(), nullable=False),
        sa.Column('responsible_user_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='genel'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('evidence_note', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['handover_id'], ['personnel_handover_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['responsible_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_handover_items_handover_id'), 'personnel_handover_items', ['handover_id'], unique=False)
    op.create_index(op.f('ix_personnel_handover_items_responsible_user_id'), 'personnel_handover_items', ['responsible_user_id'], unique=False)
    op.create_index(op.f('ix_personnel_handover_items_created_by_id'), 'personnel_handover_items', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_personnel_handover_items_category'), 'personnel_handover_items', ['category'], unique=False)
    op.create_index(op.f('ix_personnel_handover_items_status'), 'personnel_handover_items', ['status'], unique=False)
    op.create_index(op.f('ix_personnel_handover_items_due_date'), 'personnel_handover_items', ['due_date'], unique=False)
    op.create_index(op.f('ix_personnel_handover_items_completed_at'), 'personnel_handover_items', ['completed_at'], unique=False)
    op.create_index(op.f('ix_personnel_handover_items_is_required'), 'personnel_handover_items', ['is_required'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_personnel_handover_items_is_required'), table_name='personnel_handover_items')
    op.drop_index(op.f('ix_personnel_handover_items_completed_at'), table_name='personnel_handover_items')
    op.drop_index(op.f('ix_personnel_handover_items_due_date'), table_name='personnel_handover_items')
    op.drop_index(op.f('ix_personnel_handover_items_status'), table_name='personnel_handover_items')
    op.drop_index(op.f('ix_personnel_handover_items_category'), table_name='personnel_handover_items')
    op.drop_index(op.f('ix_personnel_handover_items_created_by_id'), table_name='personnel_handover_items')
    op.drop_index(op.f('ix_personnel_handover_items_responsible_user_id'), table_name='personnel_handover_items')
    op.drop_index(op.f('ix_personnel_handover_items_handover_id'), table_name='personnel_handover_items')
    op.drop_table('personnel_handover_items')

    op.drop_index(op.f('ix_personnel_handover_records_handover_no'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_completed_at'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_due_date'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_planned_date'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_status'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_operation_type'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_approved_by_id'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_created_by_id'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_organization_unit_id'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_lifecycle_case_id'), table_name='personnel_handover_records')
    op.drop_index(op.f('ix_personnel_handover_records_user_id'), table_name='personnel_handover_records')
    op.drop_table('personnel_handover_records')
