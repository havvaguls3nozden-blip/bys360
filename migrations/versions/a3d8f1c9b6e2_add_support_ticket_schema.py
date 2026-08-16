"""add support ticket schema

Revision ID: a3d8f1c9b6e2
Revises: d2f1a2b3e4f6
Create Date: 2026-08-16 10:00:00

TD-032: this repository's tracked git history has never contained a migration
that creates the support-ticket schema (support_categories, support_tickets,
support_ticket_messages, support_ticket_attachments,
support_ticket_status_history, support_feedback_ratings,
support_help_articles), even though the corresponding SQLAlchemy models have
existed in app/models/support_models.py since this repo's first commit and
the app.support blueprint is actively registered. An exhaustive search across
every branch and tag found no deleted or disconnected migration for this
schema anywhere in git history -- the gap predates this repository (the same
class of loss documented by the 7 *_historical_placeholder.py stub
revisions). This migration reconstructs the schema from the current,
schema-stable ORM models (support_models.py has had zero structural changes
since the repo's root commit -- only two purely cosmetic import-order edits),
and is inserted directly ahead of
migrations/versions/e3f1a2b3c4d7_add_communication_phase3_runtime.py, the
sole consumer that requires support_tickets/support_help_articles to already
exist.
"""

from alembic import op
import sqlalchemy as sa


revision = "a3d8f1c9b6e2"
down_revision = "d2f1a2b3e4f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('support_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    with op.batch_alter_table('support_categories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_categories_is_active'), ['is_active'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_categories_name'), ['name'], unique=True)

    op.create_table('support_help_articles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('summary', sa.String(length=500), nullable=True),
    sa.Column('category_slug', sa.String(length=80), nullable=False),
    sa.Column('role_slugs_text', sa.Text(), nullable=True),
    sa.Column('tags_text', sa.Text(), nullable=True),
    sa.Column('content_text', sa.Text(), nullable=True),
    sa.Column('steps_text', sa.Text(), nullable=True),
    sa.Column('notes_text', sa.Text(), nullable=True),
    sa.Column('related_slugs_text', sa.Text(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('is_published', sa.Boolean(), nullable=False),
    sa.Column('is_featured', sa.Boolean(), nullable=False),
    sa.Column('source_type', sa.String(length=30), nullable=False),
    sa.Column('created_by_user_id', sa.Integer(), nullable=True),
    sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    with op.batch_alter_table('support_help_articles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_help_articles_category_slug'), ['category_slug'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_help_articles_created_by_user_id'), ['created_by_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_help_articles_is_featured'), ['is_featured'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_help_articles_is_published'), ['is_published'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_help_articles_slug'), ['slug'], unique=True)
        batch_op.create_index(batch_op.f('ix_support_help_articles_sort_order'), ['sort_order'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_help_articles_source_type'), ['source_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_help_articles_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_help_articles_updated_by_user_id'), ['updated_by_user_id'], unique=False)

    op.create_table('support_tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_no', sa.String(length=40), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('ticket_type', sa.String(length=50), nullable=False),
    sa.Column('module_name', sa.String(length=120), nullable=False),
    sa.Column('page_url', sa.String(length=255), nullable=True),
    sa.Column('priority', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.Column('created_by_user_id', sa.Integer(), nullable=False),
    sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
    sa.Column('organization_unit_id', sa.Integer(), nullable=True),
    sa.Column('sicil_no_snapshot', sa.String(length=50), nullable=True),
    sa.Column('full_name_snapshot', sa.String(length=255), nullable=True),
    sa.Column('unit_name_snapshot', sa.String(length=255), nullable=True),
    sa.Column('is_private', sa.Boolean(), nullable=False),
    sa.Column('closed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['category_id'], ['support_categories.id'], ),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['organization_unit_id'], ['organization_units.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ticket_no')
    )
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_tickets_assigned_to_user_id'), ['assigned_to_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_created_by_user_id'), ['created_by_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_module_name'), ['module_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_organization_unit_id'), ['organization_unit_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_priority'), ['priority'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_sicil_no_snapshot'), ['sicil_no_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_ticket_no'), ['ticket_no'], unique=True)
        batch_op.create_index(batch_op.f('ix_support_tickets_ticket_type'), ['ticket_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_title'), ['title'], unique=False)

    op.create_table('support_ticket_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('message_type', sa.String(length=30), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('is_internal', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('support_ticket_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_ticket_messages_is_internal'), ['is_internal'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_ticket_messages_message_type'), ['message_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_ticket_messages_ticket_id'), ['ticket_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_ticket_messages_user_id'), ['user_id'], unique=False)

    op.create_table('support_ticket_attachments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('uploaded_by_user_id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('stored_name', sa.String(length=255), nullable=False),
    sa.Column('mime_type', sa.String(length=120), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('attachment_type', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('stored_name')
    )
    with op.batch_alter_table('support_ticket_attachments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_ticket_attachments_attachment_type'), ['attachment_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_ticket_attachments_stored_name'), ['stored_name'], unique=True)
        batch_op.create_index(batch_op.f('ix_support_ticket_attachments_ticket_id'), ['ticket_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_ticket_attachments_uploaded_by_user_id'), ['uploaded_by_user_id'], unique=False)

    op.create_table('support_ticket_status_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('old_status', sa.String(length=30), nullable=True),
    sa.Column('new_status', sa.String(length=30), nullable=False),
    sa.Column('changed_by_user_id', sa.Integer(), nullable=False),
    sa.Column('note', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['changed_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('support_ticket_status_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_ticket_status_history_changed_by_user_id'), ['changed_by_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_ticket_status_history_new_status'), ['new_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_ticket_status_history_ticket_id'), ['ticket_id'], unique=False)

    op.create_table('support_feedback_ratings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('feedback_note', sa.String(length=500), nullable=True),
    sa.Column('created_by_user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('support_feedback_ratings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_feedback_ratings_created_by_user_id'), ['created_by_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_feedback_ratings_ticket_id'), ['ticket_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('support_feedback_ratings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_feedback_ratings_ticket_id'))
        batch_op.drop_index(batch_op.f('ix_support_feedback_ratings_created_by_user_id'))

    op.drop_table('support_feedback_ratings')
    with op.batch_alter_table('support_ticket_status_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_ticket_status_history_ticket_id'))
        batch_op.drop_index(batch_op.f('ix_support_ticket_status_history_new_status'))
        batch_op.drop_index(batch_op.f('ix_support_ticket_status_history_changed_by_user_id'))

    op.drop_table('support_ticket_status_history')
    with op.batch_alter_table('support_ticket_attachments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_ticket_attachments_uploaded_by_user_id'))
        batch_op.drop_index(batch_op.f('ix_support_ticket_attachments_ticket_id'))
        batch_op.drop_index(batch_op.f('ix_support_ticket_attachments_stored_name'))
        batch_op.drop_index(batch_op.f('ix_support_ticket_attachments_attachment_type'))

    op.drop_table('support_ticket_attachments')
    with op.batch_alter_table('support_ticket_messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_ticket_messages_user_id'))
        batch_op.drop_index(batch_op.f('ix_support_ticket_messages_ticket_id'))
        batch_op.drop_index(batch_op.f('ix_support_ticket_messages_message_type'))
        batch_op.drop_index(batch_op.f('ix_support_ticket_messages_is_internal'))

    op.drop_table('support_ticket_messages')
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_tickets_title'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_ticket_type'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_ticket_no'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_status'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_sicil_no_snapshot'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_priority'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_organization_unit_id'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_module_name'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_created_by_user_id'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_category_id'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_assigned_to_user_id'))

    op.drop_table('support_tickets')
    with op.batch_alter_table('support_help_articles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_help_articles_updated_by_user_id'))
        batch_op.drop_index(batch_op.f('ix_support_help_articles_source_type'))
        batch_op.drop_index(batch_op.f('ix_support_help_articles_sort_order'))
        batch_op.drop_index(batch_op.f('ix_support_help_articles_slug'))
        batch_op.drop_index(batch_op.f('ix_support_help_articles_is_published'))
        batch_op.drop_index(batch_op.f('ix_support_help_articles_is_featured'))
        batch_op.drop_index(batch_op.f('ix_support_help_articles_created_by_user_id'))
        batch_op.drop_index(batch_op.f('ix_support_help_articles_category_slug'))

    op.drop_table('support_help_articles')
    with op.batch_alter_table('support_categories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_categories_name'))
        batch_op.drop_index(batch_op.f('ix_support_categories_is_active'))

    op.drop_table('support_categories')
    # ### end Alembic commands ###
