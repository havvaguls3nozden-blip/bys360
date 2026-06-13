from __future__ import annotations



from typing import Any

from sqlalchemy import text

from app.extensions import db


def _safe_scalar(sql: str, params: dict[str, Any] | None = None, default: int = 0) -> int:
    try:
        value = db.session.execute(text(sql), params or {}).scalar()
        return int(value or 0)
    except Exception:
        return default


def table_exists(table_name: str) -> bool:
    try:
        value = db.session.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = :table_name
                )
            """),
            {"table_name": table_name},
        ).scalar()
        return bool(value)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return False


def table_columns(table_name: str) -> set[str]:
    if not table_exists(table_name):
        return set()
    try:
        rows = db.session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table_name
            """),
            {"table_name": table_name},
        ).fetchall()
        return {str(row[0]) for row in rows}
    except Exception:
        return set()


def count_table(table_name: str, where_sql: str = "", params: dict[str, Any] | None = None) -> int:
    if not table_exists(table_name):
        return 0
    where_clause = f" WHERE {where_sql}" if where_sql else ""
    return _safe_scalar(f"SELECT COUNT(*) FROM {table_name}{where_clause}", params=params)


def safe_count_with_columns(
    table_name: str,
    *,
    required_columns: set[str] | None = None,
    where_sql: str = "",
    params: dict[str, Any] | None = None,
) -> int:
    columns = table_columns(table_name)
    if required_columns and not required_columns.issubset(columns):
        return 0
    return count_table(table_name, where_sql, params=params)


def insert_agent_request_log(*, user_id: int | None, prompt: str, intent: str, response_summary: str) -> int | None:
    if not table_exists("ai_agent_request_logs"):
        return None
    try:
        result = db.session.execute(
            text("""
                INSERT INTO ai_agent_request_logs
                    (user_id, prompt_text, detected_intent, response_summary, safety_status, created_at)
                VALUES
                    (:user_id, :prompt_text, :detected_intent, :response_summary, 'safe_ag2', NOW())
                RETURNING id
            """),
            {
                "user_id": user_id,
                "prompt_text": prompt[:2000],
                "detected_intent": intent[:80],
                "response_summary": response_summary[:2000],
            },
        )
        return int(result.scalar() or 0) or None
    except Exception:
        db.session.rollback()
        return None


def insert_agent_audit_log(*, user_id: int | None, action_key: str, detail: str) -> int | None:
    if not table_exists("ai_agent_action_audit_logs"):
        return None
    try:
        result = db.session.execute(
            text("""
                INSERT INTO ai_agent_action_audit_logs
                    (user_id, action_key, target_table, target_id, action_status, detail, created_at)
                VALUES
                    (:user_id, :action_key, 'performance_summary', NULL, 'read_only_summary', :detail, NOW())
                RETURNING id
            """),
            {
                "user_id": user_id,
                "action_key": action_key[:120],
                "detail": detail[:2000],
            },
        )
        return int(result.scalar() or 0) or None
    except Exception:
        db.session.rollback()
        return None


def collect_safe_counts_for_user(user_id: int | None) -> dict[str, int]:
    """Kişisel/hassas içerik dökmeden sayı düzeyi güvenli özet üretir."""
    counts: dict[str, int] = {
        "unread_notifications": 0,
        "open_support_tickets": 0,
        "pending_feedback_items": 0,
        "ai_agent_requests": 0,
        "pending_performance_assignments": 0,
        "president_approval_waiting": 0,
        "publish_locked_scorecards": 0,
        "delayed_performance_tasks": 0,
    }

    if user_id:
        counts["unread_notifications"] = safe_count_with_columns(
            "notifications",
            required_columns={"user_id"},
            where_sql="user_id = :user_id AND COALESCE(is_read, false) = false" if "is_read" in table_columns("notifications") else "user_id = :user_id",
            params={"user_id": user_id},
        )
        counts["open_support_tickets"] = safe_count_with_columns(
            "support_tickets",
            required_columns={"created_by_id"},
            where_sql="created_by_id = :user_id AND COALESCE(status, '') NOT IN ('closed', 'resolved', 'kapandi', 'kapandı')",
            params={"user_id": user_id},
        )
        counts["ai_agent_requests"] = safe_count_with_columns(
            "ai_agent_request_logs",
            required_columns={"user_id"},
            where_sql="user_id = :user_id",
            params={"user_id": user_id},
        )

    assignment_columns = table_columns("evaluation_assignments")
    if "status" in assignment_columns:
        counts["pending_performance_assignments"] = count_table(
            "evaluation_assignments",
            "COALESCE(status, '') IN ('pending', 'assigned', 'waiting', 'bekliyor', 'in_progress')",
        )
    if "due_date" in assignment_columns and "status" in assignment_columns:
        counts["delayed_performance_tasks"] = count_table(
            "evaluation_assignments",
            "due_date < NOW() AND COALESCE(status, '') IN ('pending', 'assigned', 'waiting', 'bekliyor', 'in_progress')",
        )

    evaluation_columns = table_columns("performance_evaluations")
    if "status" in evaluation_columns:
        counts["president_approval_waiting"] = count_table(
            "performance_evaluations",
            "COALESCE(status, '') IN ('president_pending', 'blocked_president_pending', 'Başkan Onayı Bekliyor', 'baskan_onayi_bekliyor')",
        )
        counts["publish_locked_scorecards"] = count_table(
            "performance_evaluations",
            "COALESCE(status, '') IN ('blocked_president_pending', 'publish_locked', 'Başkan Onayı Yayın Kilidi', 'yayin_kilidi')",
        )

    if table_exists("feedback_requests") and "status" in table_columns("feedback_requests"):
        counts["pending_feedback_items"] = count_table(
            "feedback_requests",
            "COALESCE(status, '') IN ('open', 'pending', 'waiting', 'bekliyor')",
        )
    return counts
