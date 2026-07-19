from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.extensions import db

PHASE5_VERSION = "2026-04-29-process-notifications-phase5"


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
    return bool(
        _scalar(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = :table_name
            )
            """,
            {"table_name": table_name},
        )
    )


def column_exists(table_name: str, column_name: str) -> bool:
    return bool(
        _scalar(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND column_name = :column_name
            )
            """,
            {"table_name": table_name, "column_name": column_name},
        )
    )


def _table_columns(table_name: str) -> set[str]:
    return {
        row["column_name"]
        for row in _rows(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
            """,
            {"table_name": table_name},
        )
    }


def _add_column(table_name: str, column_name: str, ddl_type: str) -> None:
    db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {ddl_type}"))


def _create_index(index_name: str, ddl: str) -> None:
    db.session.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} {ddl}"))


def apply_phase5_schema() -> None:
    required_tables = [
        "performance_process_flows",
        "performance_process_flow_steps",
        "performance_process_notifications",
    ]
    missing = [name for name in required_tables if not table_exists(name)]
    if missing:
        raise RuntimeError("Faz 5 icin once Faz 2-4 altyapisi gerekli: " + ", ".join(missing))

    notification_columns = {
        "recipient_user_id": "INTEGER",
        "recipient_name": "VARCHAR(255)",
        "notification_status": "VARCHAR(80) DEFAULT 'bekliyor'",
        "priority": "VARCHAR(40) DEFAULT 'normal'",
        "action_url": "VARCHAR(500)",
        "source_table": "VARCHAR(120)",
        "source_id": "INTEGER",
        "flow_status_snapshot": "VARCHAR(120)",
        "actor_user_id": "INTEGER",
        "sent_at": "TIMESTAMP",
        "process_version": "VARCHAR(120)",
        "app_notification_id": "INTEGER",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }
    for column_name, ddl_type in notification_columns.items():
        _add_column("performance_process_notifications", column_name, ddl_type)

    db.session.execute(
        text(
            """
            UPDATE performance_process_notifications
               SET recipient_user_id = COALESCE(recipient_user_id, recipient_id),
                   notification_status = COALESCE(notification_status, delivery_status, 'bekliyor'),
                   process_version = COALESCE(process_version, rule_version, :version),
                   updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
            """
        ),
        {"version": PHASE5_VERSION},
    )

    _create_index(
        "ix_perf_proc_notif_recipient_status_phase5",
        "ON performance_process_notifications(recipient_user_id, notification_status)",
    )
    _create_index(
        "ix_perf_proc_notif_source_phase5",
        "ON performance_process_notifications(source_table, source_id)",
    )
    _create_index(
        "ix_perf_proc_notif_flow_type_phase5",
        "ON performance_process_notifications(flow_id, notification_type)",
    )
    db.session.commit()


def _insert_if_columns(table_name: str, payload: dict[str, Any]) -> int | None:
    available = _table_columns(table_name)
    filtered = {key: value for key, value in payload.items() if key in available}
    if not filtered:
        return None
    columns = ", ".join(filtered.keys())
    values = ", ".join(f":{key}" for key in filtered.keys())
    suffix = ""
    if table_name == "performance_process_notifications":
        suffix = " RETURNING id"
    if table_name == "notifications" and "id" in available:
        suffix = " RETURNING id"
    result = db.session.execute(text(f"INSERT INTO {table_name} ({columns}) VALUES ({values}){suffix}"), filtered)
    returned = result.scalar() if suffix else None
    return int(returned) if returned else None


def _update_process_notification(notification_id: int, payload: dict[str, Any]) -> None:
    available = _table_columns("performance_process_notifications")
    filtered = {key: value for key, value in payload.items() if key in available}
    if not filtered:
        return
    assignments = ", ".join(f"{key} = :{key}" for key in filtered.keys())
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


def _safe_text(value: Any, fallback: str = "") -> str:
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
    if not table_exists("performance_process_flows"):
        return []
    return _rows(
        """
        SELECT
            id,
            evaluation_id,
            period_id,
            employee_id,
            current_owner_user_id,
            current_owner_name,
            current_stage,
            current_status,
            current_step_key,
            flow_summary,
            last_action_title,
            last_action_at
        FROM performance_process_flows
        WHERE current_owner_user_id IS NOT NULL
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
        recipient_id = row.get("current_owner_user_id")
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
