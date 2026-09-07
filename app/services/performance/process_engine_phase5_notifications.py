from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import inspect, text

from app.extensions import db
from app.security.sql_identifiers import quote_sql_identifier, validate_sql_identifier

PHASE5_VERSION = "2026-04-29-process-notifications-phase5"

_INSERT_ALLOWED_COLUMNS = {
    "notifications": frozenset(
        {
            "user_id",
            "title",
            "body",
            "notification_type",
            "source_type",
            "source_id",
            "link_url",
            "priority",
            "is_read",
            "created_at",
            "updated_at",
        }
    ),
    "performance_process_notifications": frozenset(
        {
            "flow_id",
            "evaluation_id",
            "recipient_id",
            "recipient_user_id",
            "recipient_name",
            "notification_type",
            "title",
            "body",
            "target_url",
            "action_url",
            "delivery_status",
            "notification_status",
            "priority",
            "source_event_key",
            "source_table",
            "source_id",
            "flow_status_snapshot",
            "actor_user_id",
            "created_at",
            "sent_at",
            "process_version",
            "rule_version",
            "updated_at",
            "app_notification_id",
        }
    ),
}
_PROCESS_NOTIFICATION_UPDATE_COLUMNS = frozenset(
    {
        "app_notification_id",
        "delivery_status",
        "notification_status",
        "sent_at",
        "updated_at",
    }
)


@dataclass(frozen=True)
class Phase5SyncResult:
    process_notifications_created: int = 0
    app_notifications_created: int = 0
    skipped: int = 0


def _scalar(sql: str, params: dict[str, Any] | None = None) -> Any:
    return db.session.execute(text(sql), params or {}).scalar()


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[Any]:
    return list(db.session.execute(text(sql), params or {}).mappings())


def table_exists(table_name: str) -> bool:
    """BYS360 DEFECT AL: raw PostgreSQL-only ``information_schema.tables``
    query replaced with SQLAlchemy's ``inspect()``, which is dialect-neutral
    by construction (works identically against SQLite/PostgreSQL) -- the
    same proven pattern already used elsewhere in this module family
    (process_engine_phase4_flow.py, phase6_president_approvals.py)."""
    return bool(inspect(db.engine).has_table(table_name))


def column_exists(table_name: str, column_name: str) -> bool:
    return column_name in _table_columns(table_name)


def _table_columns(table_name: str) -> set[str]:
    """BYS360 DEFECT AL: dialect-neutral via SQLAlchemy ``inspect()``,
    replacing the prior raw PostgreSQL-only ``information_schema.columns``
    query."""
    if not table_exists(table_name):
        return set()
    return {str(column["name"]) for column in inspect(db.engine).get_columns(table_name)}


class Phase5SchemaNotReadyError(RuntimeError):
    """Raised when the Alembic-owned Faz 5 process-engine schema is not ready."""


_PHASE5_REQUIRED_SCHEMA = {
    "performance_process_flows": frozenset(
        {
            "id",
            "evaluation_id",
            "period_id",
            "employee_id",
            "current_owner_id",
            "current_owner_label",
            "current_step_key",
            "current_status",
            "final_score",
            "is_low_score",
            "president_approval_required",
            "president_approval_status",
            "is_finalized",
            "started_at",
            "last_action_at",
            "completed_at",
            "rule_version",
            "created_at",
            "updated_at",
        }
    ),
    "performance_process_flow_steps": frozenset(
        {
            "id",
            "flow_id",
            "evaluation_id",
            "step_order",
            "step_key",
            "step_title",
            "step_status",
            "actor_id",
            "actor_label",
            "owner_id",
            "owner_label",
            "action_summary",
            "action_note",
            "score_snapshot",
            "occurred_at",
            "created_at",
            "rule_version",
        }
    ),
    "performance_process_notifications": frozenset(
        {
            "id",
            "flow_id",
            "evaluation_id",
            "recipient_id",
            "notification_type",
            "title",
            "body",
            "target_url",
            "delivery_status",
            "source_event_key",
            "created_at",
            "read_at",
            "rule_version",
            "recipient_user_id",
            "recipient_name",
            "notification_status",
            "priority",
            "action_url",
            "source_table",
            "source_id",
            "flow_status_snapshot",
            "actor_user_id",
            "sent_at",
            "process_version",
            "app_notification_id",
            "updated_at",
        }
    ),
}
_PHASE5_SCHEMA_REVISION = "f5e19f9107d7"


def _phase5_schema_gaps(schema_inspector) -> dict[str, tuple[str, ...]]:
    existing_tables = set(schema_inspector.get_table_names())
    gaps: dict[str, tuple[str, ...]] = {}
    for table_name, required_columns in _PHASE5_REQUIRED_SCHEMA.items():
        if table_name not in existing_tables:
            gaps[table_name] = ("<tablo eksik>",)
            continue
        existing_columns = {
            column["name"]
            for column in schema_inspector.get_columns(table_name)
        }
        missing_columns = tuple(sorted(required_columns - existing_columns))
        if missing_columns:
            gaps[table_name] = missing_columns
    return gaps


def assert_phase5_schema_ready() -> None:
    """Validate the Alembic-owned Faz 5 process-engine schema without changing it."""
    gaps = _phase5_schema_gaps(inspect(db.engine))
    if not gaps:
        return

    details = "; ".join(
        f"{table_name}: {', '.join(missing_items)}"
        for table_name, missing_items in sorted(gaps.items())
    )
    raise Phase5SchemaNotReadyError(
        "Faz 5 süreç bildirimleri veritabanı şeması hazır değil. "
        f"Alembic migrationlarını en az {_PHASE5_SCHEMA_REVISION} revisionına kadar "
        f"uygulayın. Eksikler: {details}"
    )


def apply_phase5_schema() -> None:
    """Backward-compatible, read-only Faz 5 schema readiness guard."""
    assert_phase5_schema_ready()


def _insert_if_columns(table_name: str, payload: dict[str, Any]) -> int | None:
    safe_table_name = validate_sql_identifier(
        table_name,
        allowed=_INSERT_ALLOWED_COLUMNS,
    )
    allowed_columns = _INSERT_ALLOWED_COLUMNS[safe_table_name]
    quoted_table_name = quote_sql_identifier(
        safe_table_name,
        dialect=db.engine.dialect,
        allowed=_INSERT_ALLOWED_COLUMNS,
    )
    available = _table_columns(safe_table_name)
    filtered = {
        key: value
        for key, value in payload.items()
        if key in available and key in allowed_columns
    }
    if not filtered:
        return None
    columns = ", ".join(
        quote_sql_identifier(
            key,
            dialect=db.engine.dialect,
            allowed=allowed_columns,
        )
        for key in filtered
    )
    values = ", ".join(f":{key}" for key in filtered)
    suffix = ""
    if safe_table_name == "performance_process_notifications":
        suffix = " RETURNING id"
    if safe_table_name == "notifications" and "id" in available:
        suffix = " RETURNING id"
    result = db.session.execute(
        text(
            f"INSERT INTO {quoted_table_name} ({columns}) "
            f"VALUES ({values}){suffix}"
        ),
        filtered,
    )
    returned = result.scalar() if suffix else None
    return int(returned) if returned else None


def _update_process_notification(notification_id: int, payload: dict[str, Any]) -> None:
    available = _table_columns("performance_process_notifications")
    filtered = {
        key: value
        for key, value in payload.items()
        if key in available and key in _PROCESS_NOTIFICATION_UPDATE_COLUMNS
    }
    if not filtered:
        return
    assignments = ", ".join(
        f"{quote_sql_identifier(key, dialect=db.engine.dialect, allowed=_PROCESS_NOTIFICATION_UPDATE_COLUMNS)} = :{key}"
        for key in filtered
    )
    filtered["notification_id"] = notification_id
    db.session.execute(
        text(f"UPDATE performance_process_notifications SET {assignments} WHERE id = :notification_id"),
        filtered,
    )


def _process_notification_exists(recipient_id: int, notification_type: str, event_key: str) -> bool:
    return bool(
        _scalar(
            """
            SELECT EXISTS (
                SELECT 1
                FROM performance_process_notifications
                WHERE recipient_id = :recipient_id
                  AND notification_type = :notification_type
                  AND COALESCE(source_event_key, '') = :event_key
            )
            """,
            {
                "recipient_id": recipient_id,
                "notification_type": notification_type,
                "event_key": event_key,
            },
        )
    )


def _application_notification_exists(user_id: int, source_id: int | None, source_type: str, title: str) -> bool:
    if not table_exists("notifications"):
        return False
    cols = _table_columns("notifications")
    clauses = []
    params: dict[str, Any] = {"user_id": user_id, "title": title}
    if "user_id" not in cols or "title" not in cols:
        return False
    clauses.append("user_id = :user_id")
    clauses.append("title = :title")
    if "source_type" in cols:
        clauses.append("COALESCE(source_type, '') = :source_type")
        params["source_type"] = source_type
    if "source_id" in cols and source_id is not None:
        clauses.append("COALESCE(source_id, -1) = :source_id")
        params["source_id"] = source_id
    where_sql = " AND ".join(clauses)
    return bool(_scalar(f"SELECT EXISTS (SELECT 1 FROM notifications WHERE {where_sql})", params))


def _mirror_to_application_notifications(
    *,
    recipient_id: int,
    title: str,
    body: str,
    target_url: str,
    priority: str,
    source_type: str,
    source_id: int | None,
) -> int | None:
    if not table_exists("notifications"):
        return None
    if _application_notification_exists(recipient_id, source_id, source_type, title):
        return None

    now = datetime.utcnow()
    payload = {
        "user_id": recipient_id,
        "title": title,
        "body": body,
        "notification_type": "performance",
        "source_type": source_type,
        "source_id": source_id,
        "link_url": target_url,
        "priority": priority,
        "is_read": False,
        "created_at": now,
        "updated_at": now,
    }
    return _insert_if_columns("notifications", payload)


def _safe_text(value: Any, fallback: str | None = "") -> str | None:
    text_value = str(value or "").strip()
    return text_value if text_value else fallback


def _build_process_notification(
    *,
    flow_id: int | None,
    evaluation_id: int | None,
    period_id: int | None,
    employee_id: int | None,
    recipient_id: int,
    recipient_name: str | None,
    notification_type: str,
    title: str,
    body: str,
    target_url: str,
    priority: str,
    event_key: str,
    source_table: str,
    source_id: int | None,
    flow_status: str | None,
    actor_user_id: int | None = None,
) -> int | None:
    if _process_notification_exists(recipient_id, notification_type, event_key):
        return None

    now = datetime.utcnow()
    process_id = _insert_if_columns(
        "performance_process_notifications",
        {
            "flow_id": flow_id,
            "evaluation_id": evaluation_id,
            "recipient_id": recipient_id,
            "recipient_user_id": recipient_id,
            "recipient_name": recipient_name,
            "notification_type": notification_type,
            "title": title,
            "body": body,
            "target_url": target_url,
            "action_url": target_url,
            "delivery_status": "pending",
            "notification_status": "bekliyor",
            "priority": priority,
            "source_event_key": event_key,
            "source_table": source_table,
            "source_id": source_id,
            "flow_status_snapshot": flow_status,
            "actor_user_id": actor_user_id,
            "created_at": now,
            "sent_at": now,
            "process_version": PHASE5_VERSION,
            "rule_version": PHASE5_VERSION,
            "updated_at": now,
        },
    )
    app_notification_id = _mirror_to_application_notifications(
        recipient_id=recipient_id,
        title=title,
        body=body,
        target_url=target_url,
        priority=priority,
        source_type="performance_process",
        source_id=flow_id or evaluation_id,
    )
    if process_id and app_notification_id:
        _update_process_notification(process_id, {"app_notification_id": app_notification_id})
    return process_id


def _waiting_flow_rows() -> list[Any]:
    """BYS360 DEFECT AM: query referenced ``current_owner_user_id``, which
    does not exist on performance_process_flows -- the real column is
    ``current_owner_id`` (confirmed by the model and by every migration that
    owns this table). ``current_owner_name``/``current_stage`` are also not
    real columns; neither is created by any migration or reachable runtime
    schema-repair path, so they are read with the same column-presence
    gating this file family already uses elsewhere (see
    _history_from_scoring_table() in president_card_review_service.py) --
    both callers of these two fields already tolerate a missing value.
    ``flow_summary``/``last_action_title`` were dropped: neither is read by
    sync_phase5_notifications()."""
    if not table_exists("performance_process_flows"):
        return []
    cols = _table_columns("performance_process_flows")
    owner_name_expr = "current_owner_name" if "current_owner_name" in cols else "NULL"
    current_stage_expr = "current_stage" if "current_stage" in cols else "NULL"
    return _rows(
        f"""
        SELECT
            id,
            evaluation_id,
            period_id,
            employee_id,
            current_owner_id,
            {owner_name_expr} AS current_owner_name,
            {current_stage_expr} AS current_stage,
            current_status,
            current_step_key,
            last_action_at
        FROM performance_process_flows
        WHERE current_owner_id IS NOT NULL
          AND LOWER(COALESCE(current_status, '')) IN ('bekliyor', 'waiting', 'takipte')
        ORDER BY COALESCE(last_action_at, CURRENT_TIMESTAMP) DESC, id DESC
        """
    )


def _president_waiting_rows() -> list[Any]:
    if not table_exists("performance_president_approvals"):
        return []
    if not column_exists("performance_president_approvals", "president_user_id"):
        return []
    return _rows(
        """
        SELECT
            id,
            flow_id,
            evaluation_id,
            period_id,
            employee_id,
            president_user_id,
            final_score,
            status,
            requested_at
        FROM performance_president_approvals
        WHERE president_user_id IS NOT NULL
          AND LOWER(COALESCE(status, '')) IN ('bekliyor', 'pending', 'baskan_onayi_bekliyor', 'başkan_onayı_bekliyor')
        ORDER BY COALESCE(requested_at, CURRENT_TIMESTAMP) DESC, id DESC
        """
    )


def sync_phase5_notifications() -> Phase5SyncResult:
    process_created = 0
    app_created = 0
    skipped = 0

    for row in _waiting_flow_rows():
        recipient_id = row.get("current_owner_id")
        if not recipient_id:
            skipped += 1
            continue

        flow_id = row.get("id")
        stage = _safe_text(row.get("current_stage"), "Performans değerlendirme süreci")
        owner_name = _safe_text(row.get("current_owner_name"), None)
        event_key = f"phase5_waiting_flow_{flow_id}_{recipient_id}_{stage}"

        before_app_count = _scalar("SELECT COUNT(*) FROM notifications") if table_exists("notifications") else 0
        inserted_id = _build_process_notification(
            flow_id=flow_id,
            evaluation_id=row.get("evaluation_id"),
            period_id=row.get("period_id"),
            employee_id=row.get("employee_id"),
            recipient_id=int(recipient_id),
            recipient_name=owner_name,
            notification_type="performance_waiting_task",
            title="Performans değerlendirme göreviniz var",
            body=f"{stage} aşamasındaki performans süreci işlem bekliyor.",
            target_url="/performance/dashboard",
            priority="high",
            event_key=event_key,
            source_table="performance_process_flows",
            source_id=flow_id,
            flow_status=row.get("current_status"),
            actor_user_id=None,
        )
        if inserted_id:
            process_created += 1
            after_app_count = _scalar("SELECT COUNT(*) FROM notifications") if table_exists("notifications") else before_app_count
            app_created += max(0, int(after_app_count or 0) - int(before_app_count or 0))
        else:
            skipped += 1

    for row in _president_waiting_rows():
        recipient_id = row.get("president_user_id")
        if not recipient_id:
            skipped += 1
            continue
        approval_id = row.get("id")
        flow_id = row.get("flow_id")
        event_key = f"phase5_president_approval_{approval_id}_{recipient_id}"

        before_app_count = _scalar("SELECT COUNT(*) FROM notifications") if table_exists("notifications") else 0
        inserted_id = _build_process_notification(
            flow_id=flow_id,
            evaluation_id=row.get("evaluation_id"),
            period_id=row.get("period_id"),
            employee_id=row.get("employee_id"),
            recipient_id=int(recipient_id),
            recipient_name=None,
            notification_type="performance_president_approval",
            title="Başkan onayı bekleyen performans sonucu var",
            body="70 altı nihai performans sonucu için Başkan onayı bekleniyor.",
            target_url="/performans/baskan-onaylari",
            priority="urgent",
            event_key=event_key,
            source_table="performance_president_approvals",
            source_id=approval_id,
            flow_status=row.get("status"),
            actor_user_id=None,
        )
        if inserted_id:
            process_created += 1
            after_app_count = _scalar("SELECT COUNT(*) FROM notifications") if table_exists("notifications") else before_app_count
            app_created += max(0, int(after_app_count or 0) - int(before_app_count or 0))
        else:
            skipped += 1

    db.session.commit()
    return Phase5SyncResult(
        process_notifications_created=process_created,
        app_notifications_created=app_created,
        skipped=skipped,
    )


def phase5_required_columns() -> dict[str, list[str]]:
    return {
        "performance_process_notifications": [
            "recipient_id",
            "recipient_user_id",
            "notification_type",
            "title",
            "body",
            "target_url",
            "action_url",
            "delivery_status",
            "notification_status",
            "priority",
            "source_event_key",
            "source_table",
            "source_id",
            "flow_status_snapshot",
            "process_version",
            "app_notification_id",
        ],
    }
