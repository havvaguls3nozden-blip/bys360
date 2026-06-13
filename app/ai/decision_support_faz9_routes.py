from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

"""BYS360 AI Karar Destek Faz 9 route ekleri.

Otomatik hatırlatma, son tarih yaklaşımı, geciken değerlendirme görevleri ve
aksatan amir yoğunluğunu güvenli karar destek JSON çıktılarıyla sunar.

BYS360_AI_DECISION_FAZ9_ROUTES
"""

from typing import Any, Callable

from flask import jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import text

from app.extensions import db
from app.route_registry import main_bp
from app.route_support import safe_db_rollback
from app.services.ai_decision.reminder_integration import (
    build_evaluator_delay_payload,
    build_reminder_action_plan_payload,
    build_reminder_summary_payload,
)

ResponseBuilder = Callable[..., dict[str, Any]]


def _run_faz9_json(builder: ResponseBuilder, *args: Any) -> tuple[Any, int]:
    try:
        payload = builder(*args)
        return jsonify(payload), 200
    except PermissionError as exc:
        safe_db_rollback()
        return jsonify({"ok": False, "error": str(exc) or "Bu sayfaya erişim yetkiniz bulunmamaktadır."}), 403
    except LookupError as exc:
        safe_db_rollback()
        return jsonify({"ok": False, "error": str(exc) or "Kayıt bulunamadı."}), 404
    except ValueError as exc:
        safe_db_rollback()
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover
        logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz9_routes.py | line=44")
        safe_db_rollback()
        return jsonify({"ok": False, "error": f"Hatırlatma karar destek kontrolünde beklenmeyen hata: {exc}"}), 500


def _load_settings() -> dict[str, Any]:
    rows = db.session.execute(
        text(
            """
            SELECT setting_key, value_text
              FROM module_settings
             WHERE module_key = 'ai_decision'
               AND setting_key IN (
                'faz9_reminders_enabled', 'faz9_reminder_before_days',
                'faz9_overdue_after_days', 'faz9_critical_overdue_days',
                'faz9_max_detail_rows', 'faz9_send_email_if_enabled',
                'faz9_create_notification_if_enabled'
               )
            """
        )
    ).mappings().all()
    return {row["setting_key"]: row["value_text"] for row in rows}


def _limit(default: int = 1000) -> int:
    try:
        value = int(request.args.get("limit", default))
        return max(1, min(value, 5000))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz9_routes.py | line=72")
        return default


def _table_columns(table_name: str) -> set[str]:
    rows = db.session.execute(
        text(
            """
            SELECT column_name
              FROM information_schema.columns
             WHERE table_name = :table_name
            """
        ),
        {"table_name": table_name},
    ).scalars().all()
    return {str(item) for item in rows}


def _select_expr(columns: set[str], name: str, aliases: tuple[str, ...] = (), fallback: str = "NULL") -> str:
    for candidate in (name, *aliases):
        if candidate in columns:
            return f"{candidate} AS {name}"
    return f"{fallback} AS {name}"


def _assignments(limit: int = 1000, period_id: int | None = None) -> list[Any]:
    columns = _table_columns("evaluation_assignments")
    if not columns:
        return []
    select_parts = [
        _select_expr(columns, "id", ("assignment_id",)),
        _select_expr(columns, "period_id", ("performance_period_id",)),
        _select_expr(columns, "evaluator_id", ("manager_id", "supervisor_id")),
        _select_expr(columns, "evaluated_user_id", ("personnel_id", "employee_id")),
        _select_expr(columns, "status", ("assignment_status", "state"), "'pending'"),
        _select_expr(columns, "due_date", ("deadline", "evaluation_deadline", "end_date")),
        _select_expr(columns, "created_at", (), "NOW()"),
        _select_expr(columns, "updated_at", (), "NOW()"),
    ]
    where = ""
    params: dict[str, Any] = {"limit": limit}
    if period_id is not None and ("period_id" in columns or "performance_period_id" in columns):
        col = "period_id" if "period_id" in columns else "performance_period_id"
        where = f"WHERE {col} = :period_id"
        params["period_id"] = period_id
    sql = f"""
        SELECT {', '.join(select_parts)}
          FROM evaluation_assignments
          {where}
         ORDER BY id DESC
         LIMIT :limit
    """
    return db.session.execute(text(sql), params).mappings().all()


def _notification_rows(limit: int = 500) -> list[Any]:
    columns = _table_columns("notifications")
    if not columns:
        return []
    message_filter = ""
    if "module_key" in columns:
        message_filter = "WHERE module_key IN ('performance', 'ai_decision')"
    elif "title" in columns:
        message_filter = "WHERE title ILIKE '%performans%' OR title ILIKE '%değerlendirme%'"
    sql = f"SELECT id FROM notifications {message_filter} ORDER BY id DESC LIMIT :limit"
    return db.session.execute(text(sql), {"limit": limit}).mappings().all()


def _mail_log_rows(limit: int = 500) -> list[Any]:
    columns = _table_columns("mail_logs")
    if not columns:
        return []
    filter_sql = ""
    if "subject" in columns:
        filter_sql = "WHERE subject ILIKE '%performans%' OR subject ILIKE '%değerlendirme%'"
    sql = f"SELECT id FROM mail_logs {filter_sql} ORDER BY id DESC LIMIT :limit"
    return db.session.execute(text(sql), {"limit": limit}).mappings().all()


@main_bp.route("/ai/decision-support/faz9/health")
@login_required
def ai_decision_faz9_health():
    return jsonify({
        "ok": True,
        "phase": "Faz 9",
        "module": "AI Karar Destek Merkezi",
        "scope": "Otomatik Hatırlatma ve Aksatan Amir",
        "marker": "BYS360_AI_DECISION_FAZ9_HEALTH_OK",
    })


@main_bp.route("/ai/decision-support/performance/reminders/summary")
@login_required
def ai_decision_faz9_reminder_summary():
    settings = _load_settings()
    return _run_faz9_json(
        build_reminder_summary_payload,
        _assignments(_limit()),
        _notification_rows(),
        _mail_log_rows(),
        current_user,
        settings,
    )


@main_bp.route("/ai/decision-support/performance/reminders/evaluators")
@login_required
def ai_decision_faz9_evaluator_delays():
    settings = _load_settings()
    return _run_faz9_json(build_evaluator_delay_payload, _assignments(_limit()), settings)


@main_bp.route("/ai/decision-support/performance/reminders/action-plan")
@login_required
def ai_decision_faz9_reminder_action_plan():
    settings = _load_settings()
    period_id = request.args.get("period_id", type=int)
    return _run_faz9_json(build_reminder_action_plan_payload, _assignments(_limit(), period_id=period_id), settings)
