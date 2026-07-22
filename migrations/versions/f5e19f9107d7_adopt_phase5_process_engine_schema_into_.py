"""Adopt phase5 process engine schema into Alembic ownership.

Revision ID: f5e19f9107d7
Revises: 7c4e1a9b2d60
Create Date: 2026-07-22 21:04:30.723020

The process-flow, flow-step, and process-notification tables may already
exist in installations where the legacy application bootstrap (or the
Faz 5 runtime helper in
``app/services/performance/process_engine_phase5_notifications.py``) created
or extended them outside of Alembic. This migration preserves existing rows,
adopts the union of the known Phase 2-5 compatibility columns, and creates
the required indexes without deleting duplicates.
"""

from __future__ import annotations

from collections.abc import Iterable

import sqlalchemy as sa
from alembic import op

revision = "f5e19f9107d7"
down_revision = "7c4e1a9b2d60"
branch_labels = None
depends_on = None


_FLOWS_TABLE = "performance_process_flows"
_FLOW_STEPS_TABLE = "performance_process_flow_steps"
_NOTIFICATIONS_TABLE = "performance_process_notifications"
_RULE_VERSION = "phase2_process_engine_v1"
_PHASE5_VERSION = "2026-04-29-process-notifications-phase5"


def _table_exists(bind: sa.engine.Connection, table_name: str) -> bool:
    return table_name in sa.inspect(bind).get_table_names()


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _table_exists(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def _index_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _table_exists(bind, table_name):
        return set()
    return {
        index["name"]
        for index in sa.inspect(bind).get_indexes(table_name)
        if index.get("name")
    }


def _unique_column_sets(bind: sa.engine.Connection, table_name: str) -> set[tuple[str, ...]]:
    if not _table_exists(bind, table_name):
        return set()
    inspector = sa.inspect(bind)
    unique_sets = {
        tuple(constraint.get("column_names") or ())
        for constraint in inspector.get_unique_constraints(table_name)
    }
    unique_sets.update(
        tuple(index.get("column_names") or ())
        for index in inspector.get_indexes(table_name)
        if index.get("unique")
    )
    return unique_sets


def _add_missing_columns(
    bind: sa.engine.Connection,
    table_name: str,
    columns: Iterable[sa.Column],
) -> None:
    existing = _column_names(bind, table_name)
    missing = [column for column in columns if column.name not in existing]
    if not missing:
        return

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table_name, recreate="always") as batch_op:
            for column in missing:
                batch_op.add_column(column)
        return

    for column in missing:
        op.add_column(table_name, column)


def _create_index_if_missing(
    bind: sa.engine.Connection,
    index_name: str,
    table_name: str,
    columns: list[str],
    *,
    unique: bool = False,
) -> None:
    if index_name not in _index_names(bind, table_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _has_duplicate_flow_evaluation_ids(bind: sa.engine.Connection) -> bool:
    duplicate = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM performance_process_flows
            WHERE evaluation_id IS NOT NULL
            GROUP BY evaluation_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).scalar()
    return duplicate is not None


def _flow_columns() -> tuple[sa.Column, ...]:
    return (
        sa.Column("evaluation_id", sa.Integer(), nullable=False),
        sa.Column("period_id", sa.Integer(), nullable=True),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("current_owner_id", sa.Integer(), nullable=True),
        sa.Column("current_owner_label", sa.String(length=255), nullable=True),
        sa.Column(
            "current_step_key",
            sa.String(length=80),
            nullable=False,
            server_default=sa.text("'created'"),
        ),
        sa.Column(
            "current_status",
            sa.String(length=80),
            nullable=False,
            server_default=sa.text("'created'"),
        ),
        sa.Column("final_score", sa.Numeric(6, 2), nullable=True),
        sa.Column(
            "is_low_score",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "president_approval_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "president_approval_status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'not_required'"),
        ),
        sa.Column(
            "is_finalized",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("last_action_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "rule_version",
            sa.String(length=120),
            nullable=False,
            server_default=sa.text(f"'{_RULE_VERSION}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def _create_flows_table() -> None:
    op.create_table(
        _FLOWS_TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        *_flow_columns(),
    )


def _adopt_flows_table(bind: sa.engine.Connection) -> None:
    if not _table_exists(bind, _FLOWS_TABLE):
        _create_flows_table()
    else:
        _add_missing_columns(bind, _FLOWS_TABLE, _flow_columns())

    for index_name, columns in (
        ("ix_performance_process_flows_period_id", ["period_id"]),
        ("ix_performance_process_flows_employee_id", ["employee_id"]),
        ("ix_performance_process_flows_current_owner_id", ["current_owner_id"]),
        ("ix_performance_process_flows_current_status", ["current_status"]),
        ("ix_performance_process_flows_is_low_score", ["is_low_score"]),
        (
            "ix_performance_process_flows_president_approval_required",
            ["president_approval_required"],
        ),
        (
            "ix_performance_process_flows_president_approval_status",
            ["president_approval_status"],
        ),
        ("ix_performance_process_flows_is_finalized", ["is_finalized"]),
    ):
        _create_index_if_missing(bind, index_name, _FLOWS_TABLE, columns)

    if (
        ("evaluation_id",) not in _unique_column_sets(bind, _FLOWS_TABLE)
        and not _has_duplicate_flow_evaluation_ids(bind)
    ):
        _create_index_if_missing(
            bind,
            "ix_performance_process_flows_evaluation_id",
            _FLOWS_TABLE,
            ["evaluation_id"],
            unique=True,
        )


def _flow_step_columns(*, with_foreign_keys: bool) -> tuple[sa.Column, ...]:
    # NOTE: unnamed inline ForeignKey() defs are safe inside CREATE TABLE, but
    # Alembic's SQLite batch "add column" path requires named constraints, so
    # the flow_id FK is only attached for the fresh create_table() case; a
    # retrofitted column on an already-existing legacy table is added as a
    # plain integer (mirrors migrations 6f2b8c4d1a90 / 7c4e1a9b2d60).
    flow_id_column = (
        sa.Column("flow_id", sa.Integer(), sa.ForeignKey(f"{_FLOWS_TABLE}.id"), nullable=False)
        if with_foreign_keys
        else sa.Column("flow_id", sa.Integer(), nullable=False)
    )
    return (
        flow_id_column,
        sa.Column("evaluation_id", sa.Integer(), nullable=False),
        sa.Column(
            "step_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("step_key", sa.String(length=80), nullable=False),
        sa.Column("step_title", sa.String(length=255), nullable=False),
        sa.Column(
            "step_status",
            sa.String(length=80),
            nullable=False,
            server_default=sa.text("'created'"),
        ),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("actor_label", sa.String(length=255), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("owner_label", sa.String(length=255), nullable=True),
        sa.Column("action_summary", sa.String(length=500), nullable=True),
        sa.Column("action_note", sa.Text(), nullable=True),
        sa.Column("score_snapshot", sa.Numeric(6, 2), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "rule_version",
            sa.String(length=120),
            nullable=False,
            server_default=sa.text(f"'{_RULE_VERSION}'"),
        ),
    )


def _create_flow_steps_table() -> None:
    op.create_table(
        _FLOW_STEPS_TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        *_flow_step_columns(with_foreign_keys=True),
    )


def _adopt_flow_steps_table(bind: sa.engine.Connection) -> None:
    if not _table_exists(bind, _FLOW_STEPS_TABLE):
        _create_flow_steps_table()
    else:
        _add_missing_columns(bind, _FLOW_STEPS_TABLE, _flow_step_columns(with_foreign_keys=False))

    for index_name, columns in (
        ("ix_performance_process_flow_steps_flow_id", ["flow_id"]),
        ("ix_performance_process_flow_steps_evaluation_id", ["evaluation_id"]),
        ("ix_performance_process_flow_steps_step_key", ["step_key"]),
        ("ix_performance_process_flow_steps_step_status", ["step_status"]),
        ("ix_performance_process_flow_steps_actor_id", ["actor_id"]),
        ("ix_performance_process_flow_steps_owner_id", ["owner_id"]),
    ):
        _create_index_if_missing(bind, index_name, _FLOW_STEPS_TABLE, columns)


def _notification_columns(*, with_foreign_keys: bool) -> tuple[sa.Column, ...]:
    # See the matching note in _flow_step_columns(): the flow_id FK is only
    # attached for the fresh create_table() case, not for columns retrofitted
    # onto an already-existing legacy table via SQLite batch mode.
    flow_id_column = (
        sa.Column("flow_id", sa.Integer(), sa.ForeignKey(f"{_FLOWS_TABLE}.id"), nullable=True)
        if with_foreign_keys
        else sa.Column("flow_id", sa.Integer(), nullable=True)
    )
    return (
        flow_id_column,
        sa.Column("evaluation_id", sa.Integer(), nullable=True),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("target_url", sa.String(length=500), nullable=True),
        sa.Column(
            "delivery_status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("source_event_key", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column(
            "rule_version",
            sa.String(length=120),
            nullable=False,
            server_default=sa.text(f"'{_RULE_VERSION}'"),
        ),
        # Faz 5 runtime tarafindan eskiden ALTER TABLE ile eklenen sutunlar.
        sa.Column("recipient_user_id", sa.Integer(), nullable=True),
        sa.Column("recipient_name", sa.String(length=255), nullable=True),
        sa.Column(
            "notification_status",
            sa.String(length=80),
            nullable=True,
            server_default=sa.text("'bekliyor'"),
        ),
        sa.Column(
            "priority",
            sa.String(length=40),
            nullable=True,
            server_default=sa.text("'normal'"),
        ),
        sa.Column("action_url", sa.String(length=500), nullable=True),
        sa.Column("source_table", sa.String(length=120), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("flow_status_snapshot", sa.String(length=120), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("process_version", sa.String(length=120), nullable=True),
        sa.Column("app_notification_id", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def _create_notifications_table() -> None:
    op.create_table(
        _NOTIFICATIONS_TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        *_notification_columns(with_foreign_keys=True),
    )


def _backfill_notification_compatibility_columns(bind: sa.engine.Connection) -> None:
    bind.execute(
        sa.text(
            """
            UPDATE performance_process_notifications
               SET recipient_user_id = COALESCE(recipient_user_id, recipient_id),
                   notification_status = COALESCE(notification_status, delivery_status, 'bekliyor'),
                   process_version = COALESCE(process_version, rule_version, :version),
                   updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
            """
        ),
        {"version": _PHASE5_VERSION},
    )


def _adopt_notifications_table(bind: sa.engine.Connection) -> None:
    table_already_existed = _table_exists(bind, _NOTIFICATIONS_TABLE)
    if not table_already_existed:
        _create_notifications_table()
    else:
        _add_missing_columns(bind, _NOTIFICATIONS_TABLE, _notification_columns(with_foreign_keys=False))

    if table_already_existed:
        _backfill_notification_compatibility_columns(bind)

    for index_name, columns in (
        ("ix_performance_process_notifications_flow_id", ["flow_id"]),
        ("ix_performance_process_notifications_evaluation_id", ["evaluation_id"]),
        ("ix_performance_process_notifications_recipient_id", ["recipient_id"]),
        ("ix_performance_process_notifications_notification_type", ["notification_type"]),
        ("ix_performance_process_notifications_delivery_status", ["delivery_status"]),
        ("ix_performance_process_notifications_source_event_key", ["source_event_key"]),
        ("ix_performance_process_notifications_created_at", ["created_at"]),
        (
            "ix_perf_proc_notif_recipient_status_phase5",
            ["recipient_user_id", "notification_status"],
        ),
        ("ix_perf_proc_notif_source_phase5", ["source_table", "source_id"]),
        ("ix_perf_proc_notif_flow_type_phase5", ["flow_id", "notification_type"]),
    ):
        _create_index_if_missing(bind, index_name, _NOTIFICATIONS_TABLE, columns)


def upgrade() -> None:
    bind = op.get_bind()
    _adopt_flows_table(bind)
    _adopt_flow_steps_table(bind)
    _adopt_notifications_table(bind)


def downgrade() -> None:
    """Preserve adopted process-engine tables and their data.

    The migration cannot safely know whether each table existed before
    Alembic ownership was introduced, and legacy environments may hold live
    process/notification records. A destructive downgrade could therefore
    remove institutional data. Downgrade is intentionally a no-op.
    """
