"""add history and snapshot models

Revision ID: 3f2a9c4b7d10
Revises: fae32fb68b1b
Create Date: 2026-03-20 21:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f2a9c4b7d10'
down_revision = 'fae32fb68b1b'
branch_labels = None
depends_on = None


def upgrade():
    # --- existing tables: organization_units ---
    with op.batch_alter_table('organization_units', schema=None) as batch_op:
        batch_op.add_column(sa.Column('unit_code', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('closed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('closure_reason', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('successor_unit_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_organization_units_unit_code'), ['unit_code'], unique=True)
        batch_op.create_index(batch_op.f('ix_organization_units_successor_unit_id'), ['successor_unit_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_organization_units_successor_unit_id',
            'organization_units',
            ['successor_unit_id'],
            ['id']
        )

    # --- existing tables: performance_criteria ---
    with op.batch_alter_table('performance_criteria', schema=None) as batch_op:
        batch_op.add_column(sa.Column('criteria_code', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('effective_start_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('effective_end_date', sa.Date(), nullable=True))
        batch_op.create_index(batch_op.f('ix_performance_criteria_criteria_code'), ['criteria_code'], unique=True)

    # --- existing tables: performance_periods ---
    with op.batch_alter_table('performance_periods', schema=None) as batch_op:
        batch_op.add_column(sa.Column('snapshot_status', sa.String(length=30), nullable=False, server_default='not_started'))
        batch_op.add_column(sa.Column('snapshot_generated_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('snapshot_generated_by_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_performance_periods_snapshot_status'), ['snapshot_status'], unique=False)
        batch_op.create_foreign_key(
            'fk_performance_periods_snapshot_generated_by_id',
            'users',
            ['snapshot_generated_by_id'],
            ['id']
        )

    # --- organization_unit_versions ---
    op.create_table(
        'organization_unit_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_unit_id', sa.Integer(), nullable=False),
        sa.Column('unit_code_snapshot', sa.String(length=100), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('unit_type', sa.String(length=50), nullable=True),
        sa.Column('parent_unit_id_snapshot', sa.Integer(), nullable=True),
        sa.Column('parent_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('org_path_snapshot', sa.Text(), nullable=True),
        sa.Column('effective_start_date', sa.Date(), nullable=False),
        sa.Column('effective_end_date', sa.Date(), nullable=True),
        sa.Column('change_reason', sa.String(length=255), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_unit_id'], ['organization_units.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('organization_unit_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_organization_unit_versions_organization_unit_id'), ['organization_unit_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_unit_versions_unit_code_snapshot'), ['unit_code_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_unit_versions_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_unit_versions_unit_type'), ['unit_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_unit_versions_parent_unit_id_snapshot'), ['parent_unit_id_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_unit_versions_effective_start_date'), ['effective_start_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_unit_versions_effective_end_date'), ['effective_end_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_organization_unit_versions_is_current'), ['is_current'], unique=False)

    # --- employee_org_assignment_history ---
    op.create_table(
        'employee_org_assignment_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('organization_unit_id', sa.Integer(), nullable=True),
        sa.Column('organization_unit_version_id', sa.Integer(), nullable=True),
        sa.Column('unit_name_snapshot', sa.String(length=255), nullable=False),
        sa.Column('parent_unit_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('org_path_snapshot', sa.Text(), nullable=True),
        sa.Column('manager_1_user_id', sa.Integer(), nullable=True),
        sa.Column('manager_2_user_id', sa.Integer(), nullable=True),
        sa.Column('manager_3_user_id', sa.Integer(), nullable=True),
        sa.Column('manager_1_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('manager_2_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('manager_3_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('manager_1_sicil_snapshot', sa.String(length=50), nullable=True),
        sa.Column('manager_2_sicil_snapshot', sa.String(length=50), nullable=True),
        sa.Column('manager_3_sicil_snapshot', sa.String(length=50), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('assignment_type', sa.String(length=50), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['users.id']),
        sa.ForeignKeyConstraint(['manager_1_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['manager_2_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['manager_3_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['organization_unit_id'], ['organization_units.id']),
        sa.ForeignKeyConstraint(['organization_unit_version_id'], ['organization_unit_versions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('employee_org_assignment_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_employee_id'), ['employee_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_organization_unit_id'), ['organization_unit_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_organization_unit_version_id'), ['organization_unit_version_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_unit_name_snapshot'), ['unit_name_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_parent_unit_name_snapshot'), ['parent_unit_name_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_manager_1_sicil_snapshot'), ['manager_1_sicil_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_manager_2_sicil_snapshot'), ['manager_2_sicil_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_manager_3_sicil_snapshot'), ['manager_3_sicil_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_start_date'), ['start_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_end_date'), ['end_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_assignment_type'), ['assignment_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_employee_org_assignment_history_is_current'), ['is_current'], unique=False)

    # --- performance_result_snapshots ---
    op.create_table(
        'performance_result_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=True),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('employee_name_snapshot', sa.String(length=255), nullable=False),
        sa.Column('sicil_no_snapshot', sa.String(length=50), nullable=False),
        sa.Column('organization_unit_id_snapshot', sa.Integer(), nullable=True),
        sa.Column('organization_unit_code_snapshot', sa.String(length=100), nullable=True),
        sa.Column('birim_snapshot', sa.String(length=255), nullable=True),
        sa.Column('ust_birim_snapshot', sa.String(length=255), nullable=True),
        sa.Column('org_path_snapshot', sa.Text(), nullable=True),
        sa.Column('manager_1_user_id_snapshot', sa.Integer(), nullable=True),
        sa.Column('manager_1_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('manager_1_sicil_snapshot', sa.String(length=50), nullable=True),
        sa.Column('manager_2_user_id_snapshot', sa.Integer(), nullable=True),
        sa.Column('manager_2_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('manager_2_sicil_snapshot', sa.String(length=50), nullable=True),
        sa.Column('manager_3_user_id_snapshot', sa.Integer(), nullable=True),
        sa.Column('manager_3_name_snapshot', sa.String(length=255), nullable=True),
        sa.Column('manager_3_sicil_snapshot', sa.String(length=50), nullable=True),
        sa.Column('level_1_total_100', sa.Float(), nullable=False, server_default='0'),
        sa.Column('level_2_total_100', sa.Float(), nullable=False, server_default='0'),
        sa.Column('level_3_total_100', sa.Float(), nullable=False, server_default='0'),
        sa.Column('final_total_100', sa.Float(), nullable=False, server_default='0'),
        sa.Column('evaluation_status_snapshot', sa.String(length=50), nullable=True),
        sa.Column('ranking_in_unit', sa.Integer(), nullable=True),
        sa.Column('ranking_in_scope', sa.Integer(), nullable=True),
        sa.Column('level_1_general_comment', sa.Text(), nullable=True),
        sa.Column('level_2_general_comment', sa.Text(), nullable=True),
        sa.Column('level_3_general_comment', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('published_by_user_id', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='system_published'),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('version_no', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['users.id']),
        sa.ForeignKeyConstraint(['evaluation_id'], ['performance_evaluations.id']),
        sa.ForeignKeyConstraint(['period_id'], ['performance_periods.id']),
        sa.ForeignKeyConstraint(['published_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period_id', 'employee_id', 'version_no', name='uq_snapshot_period_employee_version')
    )
    with op.batch_alter_table('performance_result_snapshots', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_period_id'), ['period_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_evaluation_id'), ['evaluation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_employee_id'), ['employee_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_employee_name_snapshot'), ['employee_name_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_sicil_no_snapshot'), ['sicil_no_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_organization_unit_id_snapshot'), ['organization_unit_id_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_organization_unit_code_snapshot'), ['organization_unit_code_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_birim_snapshot'), ['birim_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_ust_birim_snapshot'), ['ust_birim_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_manager_1_user_id_snapshot'), ['manager_1_user_id_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_manager_1_sicil_snapshot'), ['manager_1_sicil_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_manager_2_user_id_snapshot'), ['manager_2_user_id_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_manager_2_sicil_snapshot'), ['manager_2_sicil_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_manager_3_user_id_snapshot'), ['manager_3_user_id_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_manager_3_sicil_snapshot'), ['manager_3_sicil_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_evaluation_status_snapshot'), ['evaluation_status_snapshot'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_published_at'), ['published_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_source_type'), ['source_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_result_snapshots_is_current'), ['is_current'], unique=False)

    # --- performance_import_batches ---
    op.create_table(
        'performance_import_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('import_type', sa.String(length=50), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='hazirlaniyor'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['period_id'], ['performance_periods.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('performance_import_batches', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_performance_import_batches_import_type'), ['import_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_import_batches_period_id'), ['period_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_import_batches_status'), ['status'], unique=False)

    # --- performance_import_batch_rows ---
    op.create_table(
        'performance_import_batch_rows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('row_no', sa.Integer(), nullable=False),
        sa.Column('sicil_no', sa.String(length=50), nullable=True),
        sa.Column('employee_name_raw', sa.String(length=255), nullable=True),
        sa.Column('birim_raw', sa.String(length=255), nullable=True),
        sa.Column('ust_birim_raw', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='bekliyor'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('raw_payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['performance_import_batches.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('performance_import_batch_rows', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_performance_import_batch_rows_batch_id'), ['batch_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_import_batch_rows_sicil_no'), ['sicil_no'], unique=False)
        batch_op.create_index(batch_op.f('ix_performance_import_batch_rows_status'), ['status'], unique=False)


def downgrade():
    with op.batch_alter_table('performance_import_batch_rows', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_performance_import_batch_rows_status'))
        batch_op.drop_index(batch_op.f('ix_performance_import_batch_rows_sicil_no'))
        batch_op.drop_index(batch_op.f('ix_performance_import_batch_rows_batch_id'))
    op.drop_table('performance_import_batch_rows')

    with op.batch_alter_table('performance_import_batches', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_performance_import_batches_status'))
        batch_op.drop_index(batch_op.f('ix_performance_import_batches_period_id'))
        batch_op.drop_index(batch_op.f('ix_performance_import_batches_import_type'))
    op.drop_table('performance_import_batches')

    with op.batch_alter_table('performance_result_snapshots', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_is_current'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_source_type'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_published_at'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_evaluation_status_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_manager_3_sicil_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_manager_3_user_id_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_manager_2_sicil_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_manager_2_user_id_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_manager_1_sicil_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_manager_1_user_id_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_ust_birim_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_birim_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_organization_unit_code_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_organization_unit_id_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_sicil_no_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_employee_name_snapshot'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_employee_id'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_evaluation_id'))
        batch_op.drop_index(batch_op.f('ix_performance_result_snapshots_period_id'))
    op.drop_table('performance_result_snapshots')

    with op.batch_alter_table('employee_org_assignment_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_is_current'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_assignment_type'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_end_date'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_start_date'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_manager_3_sicil_snapshot'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_manager_2_sicil_snapshot'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_manager_1_sicil_snapshot'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_parent_unit_name_snapshot'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_unit_name_snapshot'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_organization_unit_version_id'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_organization_unit_id'))
        batch_op.drop_index(batch_op.f('ix_employee_org_assignment_history_employee_id'))
    op.drop_table('employee_org_assignment_history')

    with op.batch_alter_table('organization_unit_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_organization_unit_versions_is_current'))
        batch_op.drop_index(batch_op.f('ix_organization_unit_versions_effective_end_date'))
        batch_op.drop_index(batch_op.f('ix_organization_unit_versions_effective_start_date'))
        batch_op.drop_index(batch_op.f('ix_organization_unit_versions_parent_unit_id_snapshot'))
        batch_op.drop_index(batch_op.f('ix_organization_unit_versions_unit_type'))
        batch_op.drop_index(batch_op.f('ix_organization_unit_versions_name'))
        batch_op.drop_index(batch_op.f('ix_organization_unit_versions_unit_code_snapshot'))
        batch_op.drop_index(batch_op.f('ix_organization_unit_versions_organization_unit_id'))
    op.drop_table('organization_unit_versions')

    with op.batch_alter_table('performance_periods', schema=None) as batch_op:
        batch_op.drop_constraint('fk_performance_periods_snapshot_generated_by_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_performance_periods_snapshot_status'))
        batch_op.drop_column('snapshot_generated_by_id')
        batch_op.drop_column('snapshot_generated_at')
        batch_op.drop_column('snapshot_status')

    with op.batch_alter_table('performance_criteria', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_performance_criteria_criteria_code'))
        batch_op.drop_column('effective_end_date')
        batch_op.drop_column('effective_start_date')
        batch_op.drop_column('criteria_code')

    with op.batch_alter_table('organization_units', schema=None) as batch_op:
        batch_op.drop_constraint('fk_organization_units_successor_unit_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_organization_units_successor_unit_id'))
        batch_op.drop_index(batch_op.f('ix_organization_units_unit_code'))
        batch_op.drop_column('successor_unit_id')
        batch_op.drop_column('closure_reason')
        batch_op.drop_column('closed_at')
        batch_op.drop_column('unit_code')
