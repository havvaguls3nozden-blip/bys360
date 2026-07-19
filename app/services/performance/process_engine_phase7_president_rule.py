from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from collections.abc import Iterable

from sqlalchemy import text

from app.extensions import db

logger = logging.getLogger(__name__)

PHASE7_VERSION = "2026-04-29-performance-process-engine-phase7"
PRESIDENT_PENDING = "president_pending"
PRESIDENT_APPROVED = "president_approved"
PRESIDENT_RETURNED = "president_returned"
MANAGER_CHAIN_IN_PROGRESS = "manager_chain_in_progress"
FINALIZED = "finalized"

FINAL_STATUS_VALUES = {
    "completed",
    "complete",
    "finished",
    "final",
    "finalized",
    "published",
    "tamamlandi",
    "tamamlandı",
    "sonuclandi",
    "sonuçlandı",
    "kesinlesti",
    "kesinleşti",
}

OPEN_STATUS_VALUES = {
    "pending",
    "waiting",
    "open",
    "assigned",
    "in_progress",
    "bekliyor",
    "beklemede",
    "atanmis",
    "atanmış",
    "devam",
    "devam_ediyor",
}

TASK_TABLE_CANDIDATES = (
    "performance_evaluation_tasks",
    "performance_tasks",
    "performance_assignments",
    "performance_v2_tasks",
    "performance_manager_tasks",
)

SCORE_COLUMNS = (
    "final_total_100",
    "final_score",
    "total_score_100",
    "score_100",
    "final_total",
    "total_score",
)

STATUS_COLUMNS = ("status", "state", "task_status", "assignment_status")
USER_NAME_COLUMNS = ("full_name", "name", "display_name", "username", "email")
USER_TITLE_COLUMNS = ("title", "unvan", "position", "role", "role_name")


@dataclass(frozen=True)
class PresidentUser:
    id: int | None
    name: str


def _exec(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = db.session.execute(text(sql), params or {}).mappings().all()
    return [dict(row) for row in rows]


def _table_exists(table_name: str) -> bool:
    row = db.session.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                  AND table_name = :table_name
            )
            """
        ),
        {"table_name": table_name},
    ).scalar()
    return bool(row)


def _columns(table_name: str) -> set[str]:
    rows = db.session.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    ).scalars().all()
    return {str(row) for row in rows}


def _first_existing(columns: set[str], candidates: Iterable[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _safe_text(value: Any, fallback: str = "") -> str:
    value = "" if value is None else str(value).strip()
    return value or fallback


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def ensure_phase7_schema() -> None:
    statements = [
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS phase7_rule_version VARCHAR(120)",
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS chain_completed_at TIMESTAMP",
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS president_required BOOLEAN DEFAULT FALSE",
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS president_requested_at TIMESTAMP",
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS president_completed_at TIMESTAMP",
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS current_owner_user_id INTEGER",
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS current_owner_name VARCHAR(255)",
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS final_score NUMERIC(6,2)",
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS current_status VARCHAR(80)",
        "ALTER TABLE performance_process_flows ADD COLUMN IF NOT EXISTS president_status VARCHAR(80)",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS flow_id INTEGER",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS evaluation_id INTEGER",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS period_id INTEGER",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS employee_id INTEGER",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS final_score NUMERIC(6,2)",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS president_user_id INTEGER",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS president_name VARCHAR(255)",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS status VARCHAR(80) DEFAULT 'pending'",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS decided_at TIMESTAMP",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS decision_note TEXT",
        "ALTER TABLE performance_president_approvals ADD COLUMN IF NOT EXISTS process_version VARCHAR(120)",
        "ALTER TABLE performance_process_notifications ADD COLUMN IF NOT EXISTS president_approval_id INTEGER",
        "ALTER TABLE performance_process_notifications ADD COLUMN IF NOT EXISTS process_version VARCHAR(120)",
        "CREATE INDEX IF NOT EXISTS ix_perf_phase7_flow_eval ON performance_process_flows(evaluation_id)",
        "CREATE INDEX IF NOT EXISTS ix_perf_phase7_flow_status ON performance_process_flows(current_status, president_status)",
        "CREATE INDEX IF NOT EXISTS ix_perf_phase7_president_eval ON performance_president_approvals(evaluation_id, status)",
        "CREATE INDEX IF NOT EXISTS ix_perf_phase7_notifications_recipient ON performance_process_notifications(recipient_user_id, notification_status)",
    ]
    for statement in statements:
        db.session.execute(text(statement))
    db.session.commit()


def _evaluation_columns() -> set[str]:
    if not _table_exists("performance_evaluations"):
        return set()
    return _columns("performance_evaluations")


def _evaluation_row(evaluation_id: int) -> dict[str, Any] | None:
    columns = _evaluation_columns()
    if not columns:
        return None
    select_columns = ["id"]
    for col in ("period_id", "employee_id", "user_id", "status", "state", *SCORE_COLUMNS):
        if col in columns and col not in select_columns:
            select_columns.append(col)
    row = db.session.execute(
        text(f"SELECT {', '.join(select_columns)} FROM performance_evaluations WHERE id = :id"),
        {"id": evaluation_id},
    ).mappings().first()
    return dict(row) if row else None


def _final_score_from_row(row: dict[str, Any]) -> Decimal | None:
    for column in SCORE_COLUMNS:
        value = _decimal_or_none(row.get(column))
        if value is not None:
            return value
    return None


def _evaluation_status(row: dict[str, Any]) -> str:
    return _safe_text(row.get("status") or row.get("state")).lower()


def _open_task_count(evaluation_id: int) -> int:
    total = 0
    for table_name in TASK_TABLE_CANDIDATES:
        if not _table_exists(table_name):
            continue
        columns = _columns(table_name)
        if "evaluation_id" not in columns:
            continue
        status_col = _first_existing(columns, STATUS_COLUMNS)
        if not status_col:
            continue
        placeholders = ", ".join(f":s{i}" for i, _ in enumerate(OPEN_STATUS_VALUES))
        params = {f"s{i}": status for i, status in enumerate(OPEN_STATUS_VALUES)}
        params["evaluation_id"] = evaluation_id
        total += int(
            db.session.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM {table_name}
                    WHERE evaluation_id = :evaluation_id
                      AND LOWER(COALESCE({status_col}, '')) IN ({placeholders})
                    """
                ),
                params,
            ).scalar()
            or 0
        )
    return total


def manager_chain_completed(evaluation_id: int) -> bool:
    row = _evaluation_row(evaluation_id)
    if not row:
        return False

    open_tasks = _open_task_count(evaluation_id)
    if open_tasks > 0:
        return False

    status = _evaluation_status(row)
    if status in FINAL_STATUS_VALUES:
        return True

    if _table_exists("performance_scoring_history"):
        cols = _columns("performance_scoring_history")
        if {"evaluation_id", "action_status"}.issubset(cols):
            count = int(
                db.session.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM performance_scoring_history
                        WHERE evaluation_id = :evaluation_id
                          AND LOWER(COALESCE(action_status, '')) IN ('completed', 'tamamlandi', 'tamamlandı')
                        """
                    ),
                    {"evaluation_id": evaluation_id},
                ).scalar()
                or 0
            )
            if count >= 1 and _final_score_from_row(row) is not None:
                return True

    return False


def find_president_user() -> PresidentUser:
    if not _table_exists("users"):
        return PresidentUser(None, "Başkan")
    cols = _columns("users")
    id_col = "id" if "id" in cols else None
    if not id_col:
        return PresidentUser(None, "Başkan")

    name_expr_parts = []
    for col in USER_NAME_COLUMNS:
        if col in cols:
            name_expr_parts.append(f"NULLIF(TRIM(CAST({col} AS TEXT)), '')")
    if "ad" in cols and "soyad" in cols:
        name_expr_parts.insert(0, "NULLIF(TRIM(COALESCE(ad, '') || ' ' || COALESCE(soyad, '')), '')")
    name_expr = "COALESCE(" + ", ".join(name_expr_parts + ["'Başkan'"]) + ")"

    title_conditions = []
    for col in USER_TITLE_COLUMNS:
        if col in cols:
            title_conditions.append(
                f"(LOWER(COALESCE(CAST({col} AS TEXT), '')) LIKE '%başkan%' "
                f"AND LOWER(COALESCE(CAST({col} AS TEXT), '')) NOT LIKE '%yardımcı%' "
                f"AND LOWER(COALESCE(CAST({col} AS TEXT), '')) NOT LIKE '%grup%')"
            )
    if not title_conditions:
        return PresidentUser(None, "Başkan")

    row = db.session.execute(
        text(
            f"""
            SELECT {id_col} AS id, {name_expr} AS name
            FROM users
            WHERE {' OR '.join(title_conditions)}
            ORDER BY {id_col}
            LIMIT 1
            """
        )
    ).mappings().first()
    if not row:
        return PresidentUser(None, "Başkan")
    return PresidentUser(int(row["id"]), _safe_text(row.get("name"), "Başkan"))


def _ensure_flow(evaluation_id: int, period_id: int | None, employee_id: int | None) -> int:
    row = db.session.execute(
        text("SELECT id FROM performance_process_flows WHERE evaluation_id = :evaluation_id LIMIT 1"),
        {"evaluation_id": evaluation_id},
    ).mappings().first()
    if row:
        return int(row["id"])

    new_id = db.session.execute(
        text(
            """
            INSERT INTO performance_process_flows
                (evaluation_id, period_id, employee_id, current_status, phase7_rule_version, created_at, updated_at)
            VALUES
                (:evaluation_id, :period_id, :employee_id, :current_status, :version, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
            """
        ),
        {
            "evaluation_id": evaluation_id,
            "period_id": period_id,
            "employee_id": employee_id,
            "current_status": MANAGER_CHAIN_IN_PROGRESS,
            "version": PHASE7_VERSION,
        },
    ).scalar()
    return int(new_id)


def _step_exists(flow_id: int, event_key: str) -> bool:
    return bool(
        db.session.execute(
            text(
                """
                SELECT 1
                FROM performance_process_flow_steps
                WHERE flow_id = :flow_id
                  AND event_key = :event_key
                LIMIT 1
                """
            ),
            {"flow_id": flow_id, "event_key": event_key},
        ).first()
    )


def _insert_step(
    *,
    flow_id: int,
    evaluation_id: int,
    period_id: int | None,
    employee_id: int | None,
    event_key: str,
    step_code: str,
    step_title: str,
    description: str,
    status: str,
    owner_user_id: int | None,
) -> None:
    if _step_exists(flow_id, event_key):
        return
    db.session.execute(
        text(
            """
            INSERT INTO performance_process_flow_steps
                (flow_id, evaluation_id, period_id, employee_id, event_key, step_code, step_title,
                 description, status, owner_user_id, action_at, created_at, updated_at)
            VALUES
                (:flow_id, :evaluation_id, :period_id, :employee_id, :event_key, :step_code, :step_title,
                 :description, :status, :owner_user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        ),
        {
            "flow_id": flow_id,
            "evaluation_id": evaluation_id,
            "period_id": period_id,
            "employee_id": employee_id,
            "event_key": event_key,
            "step_code": step_code,
            "step_title": step_title,
            "description": description,
            "status": status,
            "owner_user_id": owner_user_id,
        },
    )


def _approval_exists(evaluation_id: int, active_only: bool = True) -> dict[str, Any] | None:
    sql = "SELECT * FROM performance_president_approvals WHERE evaluation_id = :evaluation_id"
    if active_only:
        sql += " AND LOWER(COALESCE(status, '')) IN ('pending', 'president_pending', 'waiting')"
    sql += " ORDER BY id DESC LIMIT 1"
    row = db.session.execute(text(sql), {"evaluation_id": evaluation_id}).mappings().first()
    return dict(row) if row else None


def _ensure_approval(
    *,
    flow_id: int,
    evaluation_id: int,
    period_id: int | None,
    employee_id: int | None,
    final_score: Decimal,
    president: PresidentUser,
) -> int:
    existing = _approval_exists(evaluation_id, active_only=True)
    if existing:
        db.session.execute(
            text(
                """
                UPDATE performance_president_approvals
                SET flow_id = COALESCE(flow_id, :flow_id),
                    final_score = :final_score,
                    president_user_id = COALESCE(president_user_id, :president_user_id),
                    president_name = COALESCE(NULLIF(president_name, ''), :president_name),
                    status = 'pending',
                    process_version = :version,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {
                "id": existing["id"],
                "flow_id": flow_id,
                "final_score": final_score,
                "president_user_id": president.id,
                "president_name": president.name,
                "version": PHASE7_VERSION,
            },
        )
        return int(existing["id"])

    new_id = db.session.execute(
        text(
            """
            INSERT INTO performance_president_approvals
                (flow_id, evaluation_id, period_id, employee_id, score, final_score, president_user_id,
                 president_name, status, requested_at, process_version, created_at, updated_at)
            VALUES
                (:flow_id, :evaluation_id, :period_id, :employee_id, :final_score, :final_score, :president_user_id,
                 :president_name, 'pending', CURRENT_TIMESTAMP, :version, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
            """
        ),
        {
            "flow_id": flow_id,
            "evaluation_id": evaluation_id,
            "period_id": period_id,
            "employee_id": employee_id,
            "final_score": final_score,
            "president_user_id": president.id,
            "president_name": president.name,
            "version": PHASE7_VERSION,
        },
    ).scalar()
    return int(new_id)


def _notification_exists(flow_id: int, recipient_id: int | None, source_event_key: str) -> bool:
    if recipient_id is None:
        return False
    row = db.session.execute(
        text(
            """
            SELECT 1
            FROM performance_process_notifications
            WHERE flow_id = :flow_id
              AND recipient_user_id = :recipient_id
              AND source_event_key = :source_event_key
            LIMIT 1
            """
        ),
        {"flow_id": flow_id, "recipient_id": recipient_id, "source_event_key": source_event_key},
    ).first()
    return bool(row)


def _insert_process_notification(
    *,
    flow_id: int,
    evaluation_id: int,
    approval_id: int,
    president: PresidentUser,
) -> None:
    if president.id is None:
        return
    source_key = f"phase7_president_pending:{evaluation_id}"
    if _notification_exists(flow_id, president.id, source_key):
        return
    target_url = "/performans/baskan-onaylari"
    db.session.execute(
        text(
            """
            INSERT INTO performance_process_notifications
                (flow_id, evaluation_id, president_approval_id, recipient_id, recipient_user_id,
                 notification_type, title, body, target_url, action_url, delivery_status,
                 notification_status, priority, source_event_key, source_table, source_id,
                 flow_status_snapshot, process_version, created_at, updated_at)
            VALUES
                (:flow_id, :evaluation_id, :approval_id, :recipient_id, :recipient_user_id,
                 'president_approval', :title, :body, :target_url, :action_url, 'created',
                 'unread', 'high', :source_event_key, 'performance_president_approvals', :approval_id,
                 :snapshot, :version, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        ),
        {
            "flow_id": flow_id,
            "evaluation_id": evaluation_id,
            "approval_id": approval_id,
            "recipient_id": president.id,
            "recipient_user_id": president.id,
            "title": "Başkan onayı bekleyen performans sonucu var",
            "body": "Nihai puanı 70 altında kalan performans sonucu Başkan onayı bekliyor.",
            "target_url": target_url,
            "action_url": target_url,
            "source_event_key": source_key,
            "snapshot": PRESIDENT_PENDING,
            "version": PHASE7_VERSION,
        },
    )


def _update_flow_for_president(
    *,
    flow_id: int,
    final_score: Decimal,
    president: PresidentUser,
) -> None:
    db.session.execute(
        text(
            """
            UPDATE performance_process_flows
            SET current_status = :current_status,
                president_status = 'pending',
                president_required = TRUE,
                president_requested_at = COALESCE(president_requested_at, CURRENT_TIMESTAMP),
                current_owner_user_id = :president_user_id,
                current_owner_name = :president_name,
                final_score = :final_score,
                phase7_rule_version = :version,
                chain_completed_at = COALESCE(chain_completed_at, CURRENT_TIMESTAMP),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :flow_id
            """
        ),
        {
            "flow_id": flow_id,
            "current_status": PRESIDENT_PENDING,
            "president_user_id": president.id,
            "president_name": president.name,
            "final_score": final_score,
            "version": PHASE7_VERSION,
        },
    )


def _mark_chain_in_progress(evaluation_id: int, period_id: int | None, employee_id: int | None) -> None:
    flow_id = _ensure_flow(evaluation_id, period_id, employee_id)
    db.session.execute(
        text(
            """
            UPDATE performance_process_flows
            SET current_status = :status,
                president_status = NULL,
                president_required = FALSE,
                phase7_rule_version = :version,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :flow_id
              AND COALESCE(president_status, '') NOT IN ('approved', 'returned')
            """
        ),
        {"flow_id": flow_id, "status": MANAGER_CHAIN_IN_PROGRESS, "version": PHASE7_VERSION},
    )
    db.session.execute(
        text(
            """
            UPDATE performance_president_approvals
            SET status = 'cancelled_before_final_chain',
                decision_note = COALESCE(decision_note, 'Amir zinciri tamamlanmadan oluşturulan kayıt kapatıldı.'),
                updated_at = CURRENT_TIMESTAMP
            WHERE evaluation_id = :evaluation_id
              AND LOWER(COALESCE(status, '')) IN ('pending', 'president_pending', 'waiting')
            """
        ),
        {"evaluation_id": evaluation_id},
    )


def reconcile_evaluation(evaluation_id: int) -> dict[str, Any]:
    row = _evaluation_row(evaluation_id)
    if not row:
        return {"evaluation_id": evaluation_id, "action": "missing_evaluation"}

    period_id = row.get("period_id")
    employee_id = row.get("employee_id") or row.get("user_id")
    final_score = _final_score_from_row(row)

    if final_score is None:
        return {"evaluation_id": evaluation_id, "action": "no_final_score"}

    if final_score >= Decimal("70"):
        return {"evaluation_id": evaluation_id, "action": "score_not_in_president_scope", "final_score": str(final_score)}

    if not manager_chain_completed(evaluation_id):
        _mark_chain_in_progress(evaluation_id, period_id, employee_id)
        db.session.commit()
        return {"evaluation_id": evaluation_id, "action": "manager_chain_in_progress", "final_score": str(final_score)}

    president = find_president_user()
    flow_id = _ensure_flow(evaluation_id, period_id, employee_id)
    approval_id = _ensure_approval(
        flow_id=flow_id,
        evaluation_id=evaluation_id,
        period_id=period_id,
        employee_id=employee_id,
        final_score=final_score,
        president=president,
    )
    _update_flow_for_president(flow_id=flow_id, final_score=final_score, president=president)
    _insert_step(
        flow_id=flow_id,
        evaluation_id=evaluation_id,
        period_id=period_id,
        employee_id=employee_id,
        event_key=f"phase7_president_pending:{evaluation_id}",
        step_code="president_pending",
        step_title="Başkan onayı bekliyor",
        description="Nihai puan 70 altında kaldığı için süreç doğrudan Başkan onayına açıldı.",
        status=PRESIDENT_PENDING,
        owner_user_id=president.id,
    )
    _insert_process_notification(flow_id=flow_id, evaluation_id=evaluation_id, approval_id=approval_id, president=president)
    db.session.commit()
    return {
        "evaluation_id": evaluation_id,
        "action": "president_pending_created_or_updated",
        "flow_id": flow_id,
        "approval_id": approval_id,
        "president_user_id": president.id,
        "final_score": str(final_score),
    }


def candidate_evaluation_ids(limit: int = 500) -> list[int]:
    if not _table_exists("performance_evaluations"):
        return []
    cols = _evaluation_columns()
    score_col = _first_existing(cols, SCORE_COLUMNS)
    if not score_col:
        return []
    rows = db.session.execute(
        text(
            f"""
            SELECT id
            FROM performance_evaluations
            WHERE {score_col} IS NOT NULL
              AND {score_col} < 70
            ORDER BY id DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).scalars().all()
    return [int(row) for row in rows]


def reconcile_all(limit: int = 500) -> dict[str, Any]:
    ensure_phase7_schema()
    results = []
    for evaluation_id in candidate_evaluation_ids(limit=limit):
        results.append(reconcile_evaluation(evaluation_id))
    summary: dict[str, Any] = {"checked": len(results), "version": PHASE7_VERSION}
    for result in results:
        key = str(result.get("action", "unknown"))
        summary[key] = int(summary.get(key, 0)) + 1
    return summary

# PHASE7_SCORE_REPAIR_COMPAT: score and final_score are kept in sync for legacy president approval schema.

# PHASE7_INSERT_SCORE_FINAL_SCORE_COMPAT

# PHASE7_INSERT_REPAIR_V2_SCORE_FINAL_SCORE_COMPAT

# PHASE7_SQLALCHEMY_PARAM_COMPAT: President approval INSERT uses SQLAlchemy :named parameters.
