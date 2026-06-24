from __future__ import annotations

import logging
from app.core.datetime_utils import utc_now
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy.orm import joinedload

from app.models import EvaluationAssignment, PerformanceEvaluation

from .chain import build_resolved_chain
from .weights import resolve_weight_plan
from .scoring import compute_final_score
from app.services.performance.category_stats import build_category_average_for_evaluation
from app.services.publish_service import (
    get_evaluation_visibility_state,
    is_evaluation_publish_exempt,
    is_evaluation_publishable,
    summarize_skip_reasons,
)
logger = logging.getLogger(__name__)


FINAL_STATUSES = {"tamamlandi"}


def _normalize_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _safe_full_name(user: Any) -> str:
    if not user:
        return "Personel kaydı bulunamadı"
    full_name = _normalize_text(getattr(user, "full_name", ""))
    if full_name:
        return full_name
    ad = _normalize_text(getattr(user, "ad", ""))
    soyad = _normalize_text(getattr(user, "soyad", ""))
    combined = f"{ad} {soyad}".strip()
    return combined or "İsimsiz kullanıcı"


def _score_band(final_score: float) -> tuple[str, str]:
    if final_score < 70:
        return "Başarısız", "risk"
    if final_score > 90:
        return "Çok Başarılı", "success"
    return "Normal", "neutral"

def _effective_final_total(evaluation: Any) -> float:
    if not evaluation:
        return 0.0

    stored = float(getattr(evaluation, "final_total_100", 0.0) or 0.0)
    status = _normalize_text(getattr(evaluation, "status", "")).lower()

    # V2 özet ve yayın ekranlarında performans için önce saklanan nihai puanı kullan.
    # Kayıtlı puan yoksa veya eski/verisiz kayıt ise hesaplayıcıya düş.
    if stored > 0 or status in FINAL_STATUSES:
        return round(stored, 2)

    employee = getattr(evaluation, "employee", None)
    period = getattr(evaluation, "period", None)
    if not employee:
        return round(stored, 2)

    try:
        resolved_chain = build_resolved_chain(employee=employee, period=period)
        weight_plan = resolve_weight_plan(employee=employee, period=period, resolved_chain=resolved_chain)
        level_scores = {
            1: float(getattr(evaluation, "level_1_total_100", 0.0) or 0.0),
            2: float(getattr(evaluation, "level_2_total_100", 0.0) or 0.0),
            3: float(getattr(evaluation, "level_3_total_100", 0.0) or 0.0),
        }
        computed = float(compute_final_score(level_scores=level_scores, weights=weight_plan.level_weights) or 0.0)
        return round(computed if computed > 0 else stored, 2)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return round(stored, 2)


def _coerce_employee_ids(values: Iterable[Any] | None) -> list[int]:
    result: list[int] = []
    for item in values or []:
        try:
            if item is None:
                continue
            result.append(int(item))
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance_v2/reporting_workspace.py:90)")
            continue
    return sorted(set(result))

def _skip_publish_exempt(evaluation: Any) -> bool:
    try:
        return bool(is_evaluation_publish_exempt(evaluation))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _is_assignment_completed(assignment: Any) -> bool:
    completed_attr = getattr(assignment, "is_completed", None)
    if isinstance(completed_attr, bool):
        return completed_attr
    if callable(completed_attr):
        try:
            return bool(completed_attr())
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return False
    status = _normalize_text(getattr(assignment, "status", "")).lower()
    return bool(getattr(assignment, "completed_at", None) or status == "tamamlandi")


def _is_assignment_overdue(assignment: Any) -> bool:
    overdue_attr = getattr(assignment, "is_overdue", None)
    if isinstance(overdue_attr, bool):
        return overdue_attr
    if callable(overdue_attr):
        try:
            return bool(overdue_attr())
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return False

    due_date = getattr(assignment, "due_date", None)
    if not due_date or _is_assignment_completed(assignment):
        return False

    try:
        return due_date < utc_now()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False

def _load_period_evaluations(period_id: int, employee_ids: list[int] | None = None):
    query = (
        PerformanceEvaluation.query
        .options(
            joinedload(PerformanceEvaluation.employee),
            joinedload(PerformanceEvaluation.period),
        )
        .filter_by(period_id=period_id)
    )
    if employee_ids:
        query = query.filter(PerformanceEvaluation.employee_id.in_(employee_ids))
    return [evaluation for evaluation in query.all() if not _skip_publish_exempt(evaluation)]

# BYS360_REPORTING_WORKSPACE_FLOW_STATUS_REPAIR_V1
_FLOW_STATUS_COLUMN_CACHE: set[str] | None = None


def _get_process_flow_columns() -> set[str]:
    """Return available process-flow columns without making dashboard rendering fragile."""
    global _FLOW_STATUS_COLUMN_CACHE
    if _FLOW_STATUS_COLUMN_CACHE is not None:
        return _FLOW_STATUS_COLUMN_CACHE
    try:
        from sqlalchemy import text
        from app.extensions import db
        rows = db.session.execute(text("""
            SELECT column_name
              FROM information_schema.columns
             WHERE table_schema = ANY (current_schemas(false))
               AND table_name = 'performance_process_flows'
        """)).fetchall()
        _FLOW_STATUS_COLUMN_CACHE = {str(row[0]) for row in rows}
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _FLOW_STATUS_COLUMN_CACHE = set()
    return _FLOW_STATUS_COLUMN_CACHE


def _load_latest_process_flow(evaluation_id: int) -> dict[str, Any] | None:
    """Load the latest process-flow row for an evaluation if the phase tables exist."""
    if not evaluation_id:
        return None
    columns = _get_process_flow_columns()
    if "evaluation_id" not in columns:
        return None

    wanted_columns = [
        "id", "evaluation_id", "current_status", "current_stage", "current_owner_user_id",
        "current_owner_name", "president_status", "president_approval_status", "president_required",
        "publish_lock_status", "publish_lock_reason", "publish_lock_required_action", "publish_allowed",
        "tracking_status", "tracking_label", "tracking_bucket", "tracking_priority", "tracking_url",
        "is_overdue", "overdue_days", "waiting_days", "last_visible_action", "last_action_title",
        "last_action_at", "last_action_user_name", "final_score", "updated_at", "tracking_updated_at", "created_at",
    ]
    select_columns = [column for column in wanted_columns if column in columns]
    if not select_columns:
        return None

    order_column = None
    for candidate in ("tracking_updated_at", "updated_at", "created_at", "id"):
        if candidate in columns:
            order_column = candidate
            break
    order_clause = f"{order_column} DESC NULLS LAST" if order_column and order_column != "id" else "id DESC"

    try:
        from sqlalchemy import text
        from app.extensions import db
        sql = text(f"""
            SELECT {', '.join(select_columns)}
              FROM performance_process_flows
             WHERE evaluation_id = :evaluation_id
             ORDER BY {order_clause}
             LIMIT 1
        """)
        row = db.session.execute(sql, {"evaluation_id": evaluation_id}).mappings().first()
        return dict(row) if row else None
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def build_evaluation_flow_status(evaluation: Any) -> dict[str, Any]:
    """Build a safe, UI-friendly process status for dashboard/publish widgets.

    This function must never break dashboard rendering. If process-engine tables or
    newer phase columns are missing, it falls back to the evaluation's own fields.
    """
    try:
        evaluation_id = int(getattr(evaluation, "id", 0) or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        evaluation_id = 0

    final_score = _effective_final_total(evaluation)
    raw_status = _normalize_text(getattr(evaluation, "workflow_status", "")) or _normalize_text(getattr(evaluation, "status", ""))
    is_published = bool(getattr(evaluation, "is_published_to_employee", False))
    is_completed = _normalize_text(getattr(evaluation, "status", "")).lower() in FINAL_STATUSES

    fallback_label = "Yayınlandı" if is_published else ("Tamamlandı" if is_completed else "Süreç devam ediyor")
    fallback_class = "success" if is_published else ("internal" if is_completed else "neutral")

    payload: dict[str, Any] = {
        "source": "evaluation",
        "exists": False,
        "evaluation_id": evaluation_id,
        "status": raw_status or "-",
        "label": fallback_label,
        "title": fallback_label,
        "badge_class": fallback_class,
        "class": fallback_class,
        "current_stage": fallback_label,
        "current_owner_user_id": None,
        "current_owner_name": "-",
        "owner_name": "-",
        "tracking_url": "",
        "is_overdue": False,
        "overdue_days": 0,
        "waiting_days": 0,
        "final_score": round(float(final_score or 0.0), 2),
        "president_required": bool(final_score and final_score < 70),
        "president_status": "",
        "publish_allowed": is_published,
        "publish_lock_status": "",
        "publish_lock_reason": "",
    }

    flow = _load_latest_process_flow(evaluation_id)
    if not flow:
        if final_score and final_score < 70 and not is_published:
            payload.update({
                "label": "Başkan onayı kontrolü gerekiyor",
                "title": "Başkan onayı kontrolü gerekiyor",
                "badge_class": "warning",
                "class": "warning",
                "current_stage": "Başkan onayı kontrolü gerekiyor",
            })
        return payload

    current_status = _normalize_text(flow.get("current_status")) or _normalize_text(flow.get("tracking_status")) or payload["status"]
    current_stage = (
        _normalize_text(flow.get("tracking_label"))
        or _normalize_text(flow.get("current_stage"))
        or _normalize_text(flow.get("last_visible_action"))
        or _normalize_text(flow.get("last_action_title"))
        or fallback_label
    )
    president_status = _normalize_text(flow.get("president_status") or flow.get("president_approval_status"))
    publish_lock_status = _normalize_text(flow.get("publish_lock_status"))
    publish_allowed = bool(flow.get("publish_allowed")) if flow.get("publish_allowed") is not None else is_published
    owner_name = _normalize_text(flow.get("current_owner_name")) or "-"

    badge_class = "neutral"
    label = current_stage
    lower_status = f"{current_status} {president_status} {publish_lock_status}".lower()
    if "iade" in lower_status or "rejected" in lower_status:
        badge_class = "danger"
        label = current_stage or "Süreç iade edildi"
    elif "president" in lower_status or "başkan" in lower_status or "baskan" in lower_status:
        badge_class = "warning"
        label = current_stage or "Başkan onayı bekliyor"
    elif publish_lock_status and publish_lock_status.lower() not in {"none", "yok", "allowed", "acik"}:
        badge_class = "danger"
        label = current_stage or "Yayın kilidi var"
    elif bool(flow.get("is_overdue")):
        badge_class = "danger"
        label = current_stage or "Süreç gecikti"
    elif publish_allowed or is_published:
        badge_class = "success"
        label = current_stage or "Yayınlanabilir"
    elif is_completed:
        badge_class = "internal"
        label = current_stage or "Tamamlandı"

    payload.update({
        "source": "performance_process_flows",
        "exists": True,
        "flow_id": flow.get("id"),
        "status": current_status or "-",
        "label": label,
        "title": label,
        "badge_class": badge_class,
        "class": badge_class,
        "current_stage": current_stage,
        "current_owner_user_id": flow.get("current_owner_user_id"),
        "current_owner_name": owner_name,
        "owner_name": owner_name,
        "tracking_url": _normalize_text(flow.get("tracking_url")),
        "is_overdue": bool(flow.get("is_overdue")),
        "overdue_days": int(flow.get("overdue_days") or 0),
        "waiting_days": int(flow.get("waiting_days") or 0),
        "last_action_title": _normalize_text(flow.get("last_action_title")),
        "last_visible_action": _normalize_text(flow.get("last_visible_action")),
        "last_action_at": flow.get("last_action_at"),
        "last_action_user_name": _normalize_text(flow.get("last_action_user_name")),
        "final_score": round(float(flow.get("final_score") or final_score or 0.0), 2),
        "president_required": bool(flow.get("president_required")) or bool(final_score and final_score < 70),
        "president_status": president_status,
        "publish_allowed": publish_allowed,
        "publish_lock_status": publish_lock_status,
        "publish_lock_reason": _normalize_text(flow.get("publish_lock_reason")),
        "publish_lock_required_action": _normalize_text(flow.get("publish_lock_required_action")),
    })
    return payload

def build_period_scorecard_context(period, viewer=None, allowed_employee_ids: Iterable[Any] | None = None):
    if not period:
        return {
            "period": None,
            "rows": [],
            "count": 0,
            "published_count": 0,
            "completed_count": 0,
            "hidden_count": 0,
            "low_count": 0,
            "high_count": 0,
            "avg_score": 0.0,
        }

    employee_ids = _coerce_employee_ids(allowed_employee_ids)
    evaluations = _load_period_evaluations(period.id, employee_ids=employee_ids)

    rows = []
    hidden_count = 0
    published_count = 0
    completed_count = 0
    low_count = 0
    high_count = 0
    score_values: list[float] = []

    for evaluation in evaluations:
        visibility = get_evaluation_visibility_state(
            evaluation,
            viewer,
            allowed_employee_ids=employee_ids,
        )
        if viewer is not None and not bool(visibility.get("can_view")):
            hidden_count += 1
            continue

        employee = getattr(evaluation, "employee", None)
        final_total = _effective_final_total(evaluation)
        band_label, band_class = _score_band(final_total)
        status = _normalize_text(getattr(evaluation, "status", "")) or "-"
        workflow_status = _normalize_text(getattr(evaluation, "workflow_status", "")) or "-"
        is_completed = status.lower() in FINAL_STATUSES
        is_published = bool(getattr(evaluation, "is_published_to_employee", False))
        publish_allowed, publish_block_reason = is_evaluation_publishable(period, evaluation)
        if is_published:
            publish_action_label = "Yayında"
            publish_action_class = "success"
        elif publish_allowed:
            publish_action_label = "Tek tek yayınlanabilir"
            publish_action_class = "ready"
        else:
            publish_action_label = publish_block_reason or "Yayına hazır değil"
            publish_action_class = "blocked"

        if is_published:
            published_count += 1
        if is_completed:
            completed_count += 1
        if final_total < 70:
            low_count += 1
        if final_total > 90:
            high_count += 1
        score_values.append(final_total)

        acknowledged_at = getattr(evaluation, "employee_score_acknowledged_at", None)
        viewed_at = getattr(evaluation, "employee_score_viewed_at", None)
        if acknowledged_at:
            acknowledgement_label = "Onaylandı"
            acknowledgement_class = "success"
        elif viewed_at:
            acknowledgement_label = "Görüldü"
            acknowledgement_class = "internal"
        else:
            acknowledgement_label = "Bekliyor"
            acknowledgement_class = "locked"

        rows.append({
            "evaluation": evaluation,
            "employee": employee,
            "display_name": _safe_full_name(employee),
            "sicil_no": _normalize_text(getattr(employee, "sicil_no", "")) or "-",
            "unit_name": _normalize_text(getattr(employee, "birim", "")) or "-",
            "published": is_published,
            "publish_allowed": bool(publish_allowed),
            "publish_block_reason": publish_block_reason,
            "publish_action_label": publish_action_label,
            "publish_action_class": publish_action_class,
            "status": status,
            "workflow_status": workflow_status,
            "final_total": round(final_total, 2),
            "score_band_label": band_label,
            "score_band_class": band_class,
            "visibility": visibility,
            "employee_viewed_at": viewed_at,
            "employee_acknowledged_at": acknowledged_at,
            "acknowledgement_label": acknowledgement_label,
            "acknowledgement_class": acknowledgement_class,
            "flow_status": build_evaluation_flow_status(evaluation),
            "category_average": build_category_average_for_evaluation(evaluation),  # BYS360_PHASE2_SCORECARD_CATEGORY_AVERAGE_NO_DETAILS
        })

    rows.sort(key=lambda row: (-float(row.get("final_total") or 0.0), str(row.get("display_name") or "").lower()))
    avg_score = round(sum(score_values) / len(score_values), 2) if score_values else 0.0

    payload = {
        "period": period,
        "rows": rows,
        "count": len(rows),
        "published_count": published_count,
        "completed_count": completed_count,
        "hidden_count": hidden_count,
        "low_count": low_count,
        "high_count": high_count,
        "avg_score": avg_score,
    }
    # BYS360_MEETING_RULE_SCORECARD_DECORATOR
    try:
        from app.services.performance.meeting_rule_enforcement import decorate_period_scorecard_context
        payload = decorate_period_scorecard_context(payload, viewer=viewer, period=period)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance_v2/reporting_workspace.py")
    return payload


def build_publish_workspace_context(period, viewer=None, allowed_employee_ids: Iterable[Any] | None = None, limit: int = 8):
    if not period:
        return {
            "period": None,
            "total_count": 0,
            "completed_count": 0,
            "published_count": 0,
            "ready_count": 0,
            "blocked_count": 0,
            "internal_preview_count": 0,
            "publish_rate": 0.0,
            "ready_rate": 0.0,
            "blocked_reasons_summary": [],
            "blocked_rows": [],
        }

    employee_ids = _coerce_employee_ids(allowed_employee_ids)
    evaluations = _load_period_evaluations(period.id, employee_ids=employee_ids)

    total_count = len(evaluations)
    completed_count = 0
    published_count = 0
    ready_count = 0
    blocked_count = 0
    internal_preview_count = 0
    blocked_rows: list[dict[str, Any]] = []
    blocked_reason_rows: list[dict[str, Any]] = []

    for evaluation in evaluations:
        employee = getattr(evaluation, "employee", None)
        is_completed = _normalize_text(getattr(evaluation, "status", "")).lower() in FINAL_STATUSES
        is_published = bool(getattr(evaluation, "is_published_to_employee", False))

        if is_completed:
            completed_count += 1
        if is_published:
            published_count += 1
        if is_completed and not is_published:
            internal_preview_count += 1

        ok, reason = is_evaluation_publishable(period, evaluation)
        if ok and not is_published:
            ready_count += 1
            continue
        if not ok:
            blocked_count += 1
            blocked_reason_rows.append({"reason": reason})
            if len(blocked_rows) < max(int(limit or 0), 0):
                blocked_rows.append({
                    "evaluation": evaluation,
                    "employee": employee,
                    "display_name": _safe_full_name(employee),
                    "sicil_no": _normalize_text(getattr(employee, "sicil_no", "")) or "-",
                    "unit_name": _normalize_text(getattr(employee, "birim", "")) or "-",
                    "status": _normalize_text(getattr(evaluation, "status", "")) or "-",
                    "final_total": _effective_final_total(evaluation),
                    "reason": reason,
                    "flow_status": build_evaluation_flow_status(evaluation),
                })

    publish_rate = round((published_count / total_count) * 100, 1) if total_count else 0.0
    ready_rate = round((ready_count / total_count) * 100, 1) if total_count else 0.0

    return {
        "period": period,
        "total_count": total_count,
        "completed_count": completed_count,
        "published_count": published_count,
        "ready_count": ready_count,
        "blocked_count": blocked_count,
        "internal_preview_count": internal_preview_count,
        "publish_rate": publish_rate,
        "ready_rate": ready_rate,
        "blocked_reasons_summary": summarize_skip_reasons(blocked_reason_rows),
        "blocked_rows": blocked_rows,
    }


def build_manager_summary_context(period):
    if not period:
        return {"period": None, "rows": []}

    assignments = EvaluationAssignment.query.filter_by(period_id=period.id).all()
    summary = defaultdict(lambda: {"total": 0, "completed": 0, "overdue": 0, "user": None})

    for assignment in assignments:
        slot = summary[getattr(assignment, "evaluator_id", None)]
        slot["user"] = getattr(assignment, "evaluator", None)
        slot["total"] += 1
        if _is_assignment_completed(assignment):
            slot["completed"] += 1
        if _is_assignment_overdue(assignment):
            slot["overdue"] += 1

    rows = []
    for payload in summary.values():
        user = payload["user"]
        rows.append({
            "user": user,
            "display_name": _safe_full_name(user),
            "total": payload["total"],
            "completed": payload["completed"],
            "overdue": payload["overdue"],
        })

    rows.sort(key=lambda item: (item["display_name"].lower(), item["total"]))
    return {
        "period": period,
        "rows": rows,
    }