# -*- coding: utf-8 -*-
from __future__ import annotations



from datetime import datetime
from typing import Any

from sqlalchemy import inspect, text

from app.extensions import db
import logging
logger = logging.getLogger(__name__)

PHASE12_PRESIDENT_CARD_ACCESS_VERSION = "2026-04-30-president-menu-card-final"


def _has_table(table_name: str) -> bool:
    try:
        return bool(inspect(db.engine).has_table(table_name))
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/performance/president_menu_card_access.py | line=19")
        return False


def _row(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    result = db.session.execute(text(sql), params or {}).mappings().first()
    return dict(result) if result else None


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [dict(row) for row in db.session.execute(text(sql), params or {}).mappings()]


def _safe_get(row: dict[str, Any] | None, *keys: str, default: Any = "-") -> Any:
    if not row:
        return default
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def _format_dt(value: Any) -> str:
    if value in (None, ""):
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    return str(value)


def _format_score(value: Any) -> str:
    if value in (None, ""):
        return "-"
    try:
        return f"{float(value):.2f}"
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/performance/president_menu_card_access.py | line=55")
        return str(value)


def _display_user_name(user: dict[str, Any] | None, fallback: str = "-") -> str:
    if not user:
        return fallback
    full = _safe_get(user, "full_name", "name", "display_name", default="")
    if full:
        return str(full).strip()
    parts = [str(_safe_get(user, "ad", "first_name", default="")).strip(), str(_safe_get(user, "soyad", "last_name", default="")).strip()]
    name = " ".join(part for part in parts if part).strip()
    if name:
        return name
    return str(_safe_get(user, "email", "username", default=fallback)).strip() or fallback


def _get_user(user_id: Any) -> dict[str, Any] | None:
    if not user_id or not _has_table("users"):
        return None
    try:
        return _row("SELECT * FROM users WHERE id = :id", {"id": user_id})
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/performance/president_menu_card_access.py | line=77")
        return None


def _get_period(period_id: Any) -> dict[str, Any] | None:
    if not period_id or not _has_table("performance_periods"):
        return None
    try:
        return _row("SELECT * FROM performance_periods WHERE id = :id", {"id": period_id})
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/performance/president_menu_card_access.py | line=86")
        return None


def _approval_status_label(status: Any) -> str:
    normalized = str(status or "pending").strip().lower()
    if normalized in {"approved", "onaylandi", "onaylandı"}:
        return "Onaylandı"
    if normalized in {"returned", "iade", "iade_edildi"}:
        return "İade edildi"
    return "Başkan onayı bekliyor"


def _history_rows(evaluation_id: Any) -> list[dict[str, Any]]:
    if not evaluation_id or not _has_table("performance_scoring_history"):
        return []
    try:
        rows = _rows(
            """
            SELECT *
              FROM performance_scoring_history
             WHERE evaluation_id = :evaluation_id
             ORDER BY action_at NULLS LAST, id
            """,
            {"evaluation_id": evaluation_id},
        )
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/performance/president_menu_card_access.py | line=112")
        return []
    cleaned: list[dict[str, Any]] = []
    for item in rows:
        cleaned.append(
            {
                "scorer_name": _safe_get(item, "scorer_name", default="-"),
                "manager_level": _safe_get(item, "manager_level", default="-"),
                "score": _format_score(_safe_get(item, "score_value", "score", default=None)),
                "action_at": _format_dt(_safe_get(item, "action_at", "created_at", default=None)),
                "status": _safe_get(item, "action_status", default="-"),
                "next_stage": _safe_get(item, "next_stage", default="-"),
                "next_owner_name": _safe_get(item, "next_owner_name", default="-"),
            }
        )
    return cleaned


def _step_rows(flow_id: Any, evaluation_id: Any) -> list[dict[str, Any]]:
    if not _has_table("performance_process_flow_steps"):
        return []
    where = []
    params: dict[str, Any] = {}
    if flow_id:
        where.append("flow_id = :flow_id")
        params["flow_id"] = flow_id
    if evaluation_id:
        where.append("evaluation_id = :evaluation_id")
        params["evaluation_id"] = evaluation_id
    if not where:
        return []
    try:
        rows = _rows(
            f"""
            SELECT *
              FROM performance_process_flow_steps
             WHERE {' OR '.join(where)}
             ORDER BY COALESCE(tracking_order, 0), action_at NULLS LAST, id
            """,
            params,
        )
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/performance/president_menu_card_access.py | line=153")
        return []
    cleaned: list[dict[str, Any]] = []
    for item in rows:
        cleaned.append(
            {
                "title": _safe_get(item, "step_title", "tracking_label", default="Süreç adımı"),
                "status": _safe_get(item, "status", default="-"),
                "date": _format_dt(_safe_get(item, "action_at", "created_at", default=None)),
                "summary": _safe_get(item, "description", default=""),
                "owner_user_id": _safe_get(item, "owner_user_id", default="-"),
            }
        )
    return cleaned


def build_president_approval_scorecard_context(approval_id: int) -> dict[str, Any]:
    if not _has_table("performance_president_approvals"):
        return {"approval": None, "error_message": "Başkan onayı tablosu bulunamadı."}

    approval = _row("SELECT * FROM performance_president_approvals WHERE id = :id", {"id": approval_id})
    if not approval:
        return {"approval": None, "error_message": "Başkan onayı kaydı bulunamadı."}

    flow = None
    flow_id = _safe_get(approval, "flow_id", default=None)
    if flow_id and _has_table("performance_process_flows"):
        flow = _row("SELECT * FROM performance_process_flows WHERE id = :id", {"id": flow_id})

    employee = _get_user(_safe_get(approval, "employee_id", default=None))
    president = _get_user(_safe_get(approval, "president_user_id", default=None))
    period = _get_period(_safe_get(approval, "period_id", default=None))

    evaluation_id = _safe_get(approval, "evaluation_id", default=None)
    score = _safe_get(approval, "final_score", "score", default=None)
    period_title = _safe_get(period, "title", "name", "period_name", default=f"Dönem #{_safe_get(approval, 'period_id', default='-')}")

    approval_card = {
        "approval_id": approval_id,
        "evaluation_id": evaluation_id,
        "employee_id": _safe_get(approval, "employee_id", default="-"),
        "employee_name": _display_user_name(employee, fallback=f"Personel #{_safe_get(approval, 'employee_id', default='-')}"),
        "sicil_no": _safe_get(employee, "sicil_no", "registration_no", "employee_no", default="-"),
        "unit": _safe_get(employee, "birim", "department", "organization_unit_name", default="-"),
        "title": _safe_get(employee, "unvan", "title", default="-"),
        "period_title": period_title,
        "final_score": _format_score(score),
        "status": _approval_status_label(_safe_get(approval, "status", "decision_status", default="pending")),
        "requested_at": _format_dt(_safe_get(approval, "requested_at", "created_at", default=None)),
        "president_name": _safe_get(approval, "president_name", default=_display_user_name(president, fallback="Başkan")),
        "decision_note": _safe_get(approval, "decision_note", "note", "description", default=""),
        "current_stage": _safe_get(flow, "current_stage", "tracking_label", default="Başkan onayı bekliyor"),
        "current_owner_name": _safe_get(flow, "current_owner_name", default=_safe_get(approval, "president_name", default="Başkan")),
        "publish_lock_status": _safe_get(flow, "publish_lock_status", default="-"),
        "publish_lock_reason": _safe_get(flow, "publish_lock_reason", default=""),
    }

    return {
        "approval": approval_card,
        "scoring_history": _history_rows(evaluation_id),
        "flow_steps": _step_rows(flow_id, evaluation_id),
        "back_url": "/performans/baskan-onaylari",
        "version": PHASE12_PRESIDENT_CARD_ACCESS_VERSION,
    }
