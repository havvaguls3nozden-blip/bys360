"""add hr asset checklist and reminder layer

Revision ID: a91c7e4d2f30
Revises: f8c4e2d1a7b9
Create Date: 2026-04-11 21:05:00
"""

from alembic import op
import sqlalchemy as sa

revision = 'a91c7e4d2f30'
down_revision = 'f8c4e2d1a7b9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'personnel_asset_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('asset_category', sa.String(length=50), nullable=False),
        sa.Column('asset_name', sa.String(length=255), nullable=False),
        sa.Column('asset_code', sa.String(length=120), nullable=True),
        sa.Column('serial_no', sa.String(length=120), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('assigned_date', sa.Date(), nullable=False),
        sa.Column('due_return_date', sa.Date(), nullable=True),
        sa.Column('returned_date', sa.Date(), nullable=True),
        sa.Column('assigned_by_id', sa.Integer(), nullable=True),
        sa.Column('received_by_id', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['received_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_asset_assignments_asset_code'), 'personnel_asset_assignments', ['asset_code'], unique=False)
    op.create_index(op.f('ix_personnel_asset_assignments_assigned_date'), 'personnel_asset_assignments', ['assigned_date'], unique=False)
    op.create_index(op.f('ix_personnel_asset_assignments_due_return_date'), 'personnel_asset_assignments', ['due_return_date'], unique=False)
    op.create_index(op.f('ix_personnel_asset_assignments_serial_no'), 'personnel_asset_assignments', ['serial_no'], unique=False)
    op.create_index(op.f('ix_personnel_asset_assignments_status'), 'personnel_asset_assignments', ['status'], unique=False)
    op.create_index(op.f('ix_personnel_asset_assignments_user_id'), 'personnel_asset_assignments', ['user_id'], unique=False)

    op.create_table(
        'personnel_checklist_template_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_personnel_checklist_template_items_category'), 'personnel_checklist_template_items', ['category'], unique=False)
    op.create_index(op.f('ix_personnel_checklist_template_items_code'), 'personnel_checklist_template_items', ['code'], unique=False)
    op.create_index(op.f('ix_personnel_checklist_template_items_is_active'), 'personnel_checklist_template_items', ['is_active'], unique=False)
    op.create_index(op.f('ix_personnel_checklist_template_items_is_required'), 'personnel_checklist_template_items', ['is_required'], unique=False)

    op.create_table(
        'personnel_checklist_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('template_item_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('checked_by_id', sa.Integer(), nullable=True),
        sa.Column('checked_at', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['checked_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['template_item_id'], ['personnel_checklist_template_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'template_item_id', name='uq_personnel_checklist_user_template')
    )
    op.create_index(op.f('ix_personnel_checklist_reviews_checked_at'), 'personnel_checklist_reviews', ['checked_at'], unique=False)
    op.create_index(op.f('ix_personnel_checklist_reviews_expiry_date'), 'personnel_checklist_reviews', ['expiry_date'], unique=False)
    op.create_index(op.f('ix_personnel_checklist_reviews_status'), 'personnel_checklist_reviews', ['status'], unique=False)
    op.create_index(op.f('ix_personnel_checklist_reviews_template_item_id'), 'personnel_checklist_reviews', ['template_item_id'], unique=False)
    op.create_index(op.f('ix_personnel_checklist_reviews_user_id'), 'personnel_checklist_reviews', ['user_id'], unique=False)

    op.create_table(
        'personnel_document_reminder_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('reminder_type', sa.String(length=30), nullable=False),
        sa.Column('channel', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('reminder_text', sa.Text(), nullable=True),
        sa.Column('triggered_by_id', sa.Integer(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['personnel_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personnel_document_reminder_logs_channel'), 'personnel_document_reminder_logs', ['channel'], unique=False)
    op.create_index(op.f('ix_personnel_document_reminder_logs_document_id'), 'personnel_document_reminder_logs', ['document_id'], unique=False)
    op.create_index(op.f('ix_personnel_document_reminder_logs_due_date'), 'personnel_document_reminder_logs', ['due_date'], unique=False)
    op.create_index(op.f('ix_personnel_document_reminder_logs_reminder_type'), 'personnel_document_reminder_logs', ['reminder_type'], unique=False)
    op.create_index(op.f('ix_personnel_document_reminder_logs_status'), 'personnel_document_reminder_logs', ['status'], unique=False)
    op.create_index(op.f('ix_personnel_document_reminder_logs_user_id'), 'personnel_document_reminder_logs', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_personnel_document_reminder_logs_user_id'), table_name='personnel_document_reminder_logs')
    op.drop_index(op.f('ix_personnel_document_reminder_logs_status'), table_name='personnel_document_reminder_logs')
    op.drop_index(op.f('ix_personnel_document_reminder_logs_reminder_type'), table_name='personnel_document_reminder_logs')
    op.drop_index(op.f('ix_personnel_document_reminder_logs_due_date'), table_name='personnel_document_reminder_logs')
    op.drop_index(op.f('ix_personnel_document_reminder_logs_document_id'), table_name='personnel_document_reminder_logs')
    op.drop_index(op.f('ix_personnel_document_reminder_logs_channel'), table_name='personnel_document_reminder_logs')
    op.drop_table('personnel_document_reminder_logs')

    op.drop_index(op.f('ix_personnel_checklist_reviews_user_id'), table_name='personnel_checklist_reviews')
    op.drop_index(op.f('ix_personnel_checklist_reviews_template_item_id'), table_name='personnel_checklist_reviews')
    op.drop_index(op.f('ix_personnel_checklist_reviews_status'), table_name='personnel_checklist_reviews')
    op.drop_index(op.f('ix_personnel_checklist_reviews_expiry_date'), table_name='personnel_checklist_reviews')
    op.drop_index(op.f('ix_personnel_checklist_reviews_checked_at'), table_name='personnel_checklist_reviews')
    op.drop_table('personnel_checklist_reviews')

    op.drop_index(op.f('ix_personnel_checklist_template_items_is_required'), table_name='personnel_checklist_template_items')
    op.drop_index(op.f('ix_personnel_checklist_template_items_is_active'), table_name='personnel_checklist_template_items')
    op.drop_index(op.f('ix_personnel_checklist_template_items_code'), table_name='personnel_checklist_template_items')
    op.drop_index(op.f('ix_personnel_checklist_template_items_category'), table_name='personnel_checklist_template_items')
    op.drop_table('personnel_checklist_template_items')

    op.drop_index(op.f('ix_personnel_asset_assignments_user_id'), table_name='personnel_asset_assignments')
    op.drop_index(op.f('ix_personnel_asset_assignments_status'), table_name='personnel_asset_assignments')
    op.drop_index(op.f('ix_personnel_asset_assignments_serial_no'), table_name='personnel_asset_assignments')
    op.drop_index(op.f('ix_personnel_asset_assignments_due_return_date'), table_name='personnel_asset_assignments')
    op.drop_index(op.f('ix_personnel_asset_assignments_assigned_date'), table_name='personnel_asset_assignments')
    op.drop_index(op.f('ix_personnel_asset_assignments_asset_code'), table_name='personnel_asset_assignments')
    op.drop_table('personnel_asset_assignments')
