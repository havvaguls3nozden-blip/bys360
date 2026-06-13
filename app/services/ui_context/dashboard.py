from __future__ import annotations



from app.core.datetime_utils import utc_now
from datetime import datetime, timedelta
from typing import Any

from flask import request
from sqlalchemy import or_

from app.models import AssignmentCoverageLog, DelegationAssignment, EvaluationAssignment, FeedbackMeeting, FeedbackRequest, Notification, PerformancePeriod
from app.route_support import safe_all, safe_count, safe_db_rollback
from app.services.decision_support_service import build_dashboard_signal_context
from app.services.performance.assignments import (
    build_assignment_log_summary,
    build_assignment_unit_summary,
    get_latest_assignment_generation_logs,
    is_informational_special_case,
)
from app.services.query_health_service import build_dashboard_assignment_query, build_dashboard_meeting_query
from app.services.recommendation_service import build_dashboard_focus_hints
from app.services.performance_v2.reporting_workspace import build_publish_workspace_context
from app.services.sql_refactor_report_helpers import build_dashboard_evaluation_metrics_sql
from .scope import build_user_scope_context


def _coverage_tone(score: int) -> tuple[str, str]:
    if score >= 12:
        return "critical", "Kritik"
    if score >= 5:
        return "watch", "İzlenmeli"
    return "calm", "Dengeli"


def _risk_score(summary: dict[str, Any]) -> int:
    return (
        int(summary.get("uncovered", 0)) * 4
        + int(summary.get("chain_issue", 0)) * 3
        + int(summary.get("exempted", 0)) * 2
        + int(summary.get("warning", 0))
    )


def _active_period() -> Any:
    return (
        PerformancePeriod.query
        .filter_by(is_active=True)
        .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
        .first()
    )

def _row_value(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def _is_risk_special_case(row: Any) -> bool:
    return is_informational_special_case(_row_value(row, "reason", None), _row_value(row, "event_type", None))




def _period_rows(limit: int = 8) -> list[Any]:
    return (
        PerformancePeriod.query
        .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
        .limit(limit)
        .all()
    )


def _assignment_counts(user_id: int) -> tuple[int, int, list[Any], list[Any]]:
    pending_rows = build_dashboard_assignment_query(user_id, statuses=("bekliyor",)).limit(5).all()
    partial_rows = build_dashboard_assignment_query(user_id, statuses=("kismen_tamamlandi",)).limit(5).all()
    pending_count = safe_count(build_dashboard_assignment_query(user_id, statuses=("bekliyor",)), label="dashboard_pending_tasks")
    completed_count = safe_count(build_dashboard_assignment_query(user_id, statuses=("tamamlandi",)), label="dashboard_completed_tasks")
    return pending_count, completed_count, pending_rows, partial_rows


def _assignment_deadline_metrics(user_id: int) -> tuple[int, int, list[Any]]:
    now = utc_now()
    base_query = build_dashboard_assignment_query(user_id).filter(
        EvaluationAssignment.status.in_(("bekliyor", "kismen_tamamlandi")),
        EvaluationAssignment.due_date.isnot(None),
    )
    overdue_query = base_query.filter(EvaluationAssignment.due_date < now)
    due_soon_query = base_query.filter(
        EvaluationAssignment.due_date >= now,
        EvaluationAssignment.due_date <= (now + timedelta(days=2)),
    )

    overdue_count = safe_count(overdue_query, label="dashboard_overdue_tasks")
    due_soon_count = safe_count(due_soon_query, label="dashboard_due_soon_tasks")

    try:
        overdue_rows = safe_all(
            overdue_query.order_by(EvaluationAssignment.due_date.asc(), EvaluationAssignment.assigned_at.asc()).limit(5),
            label="dashboard_overdue_task_rows",
        )
    except Exception:
        safe_db_rollback()
        overdue_rows = []

    return overdue_count, due_soon_count, overdue_rows


def _feedback_meeting_count(user_id: int) -> int:
    try:
        return safe_count(build_dashboard_meeting_query(user_id, utc_now().date()), label="dashboard_meetings")
    except Exception:
        safe_db_rollback()
        return 0


def _feedback_request_count(scope_user_ids: list[int]) -> int:
    if not scope_user_ids:
        return 0
    try:
        return (
            FeedbackRequest.query
            .filter(FeedbackRequest.employee_id.in_(scope_user_ids))
            .count()
        )
    except Exception:
        safe_db_rollback()
        return 0


def _published_period_count() -> int:
    try:
        return PerformancePeriod.query.filter_by(results_published=True).count()
    except Exception:
        safe_db_rollback()
        return 0


def _evaluation_metrics(period_id: int | None, scope_user_ids: list[int]) -> tuple[int, int, int, int, int]:
    """Dashboard değerlendirme sayaçlarını Python liste yerine SQL aggregate ile üretir."""
    if not period_id or not scope_user_ids:
        return 0, 0, 0, 0, 0
    try:
        return build_dashboard_evaluation_metrics_sql(period_id, scope_user_ids).as_tuple()
    except Exception:
        safe_db_rollback()
        return 0, 0, 0, 0, 0


def _latest_scope_log(period_id: int | None, scope_user_ids: list[int]) -> dict[str, Any]:
    if not period_id:
        return {"created_at": None, "rows": [], "summary": build_assignment_log_summary([])}
    try:
        return get_latest_assignment_generation_logs(period_id, limit=400, employee_ids=scope_user_ids)
    except Exception:
        safe_db_rollback()
        return {"created_at": None, "rows": [], "summary": build_assignment_log_summary([])}


def _period_risk_rows(periods: list[Any], scope_user_ids: list[int]) -> list[dict[str, Any]]:
    rows = []
    for period in periods[:6]:
        try:
            payload = get_latest_assignment_generation_logs(period.id, limit=400, employee_ids=scope_user_ids)
        except Exception:
            safe_db_rollback()
            payload = {"created_at": None, "rows": [], "summary": build_assignment_log_summary([])}
        summary = payload.get("summary") or build_assignment_log_summary([])
        score = _risk_score(summary)
        tone, label = _coverage_tone(score)
        rows.append({
            "period": period,
            "summary": summary,
            "run_created_at": payload.get("created_at"),
            "risk_score": score,
            "risk_tone": tone,
            "risk_label": label,
        })
    return rows




def _notification_unread_count(user_id: int) -> int:
    try:
        return safe_count(
            Notification.query.filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            ),
            label="dashboard_unread_notifications",
        )
    except Exception:
        safe_db_rollback()
        return 0


def _delegation_watch_count(scope_user_ids: list[int]) -> int:
    if not scope_user_ids:
        return 0
    today = utc_now().date()
    try:
        return safe_count(
            DelegationAssignment.query.filter(
                DelegationAssignment.status == "aktif",
                DelegationAssignment.start_date <= today,
                DelegationAssignment.end_date >= today,
                or_(
                    DelegationAssignment.delegator_user_id.in_(scope_user_ids),
                    DelegationAssignment.delegate_user_id.in_(scope_user_ids),
                ),
            ),
            label="dashboard_active_delegations",
        )
    except Exception:
        safe_db_rollback()
        return 0


def _open_assignment_count(user_id: int) -> int:
    try:
        return safe_count(
            build_dashboard_assignment_query(user_id, statuses=("bekliyor", "kismen_tamamlandi")),
            label="dashboard_open_assignments",
        )
    except Exception:
        safe_db_rollback()
        return 0


def _build_executive_snapshot(
    *,
    user,
    active_period,
    scope_user_ids: list[int],
    overdue_tasks_count: int,
    today_coverage_alerts: list[Any],
) -> dict[str, Any]:
    publish_summary = (
        build_publish_workspace_context(active_period, viewer=user, allowed_employee_ids=scope_user_ids)
        if active_period else {
            "ready_count": 0,
            "blocked_count": 0,
            "internal_preview_count": 0,
            "published_count": 0,
        }
    )

    pending_approvals = _open_assignment_count(getattr(user, "id", 0) or 0)
    unread_notifications = _notification_unread_count(getattr(user, "id", 0) or 0)
    delegation_watch = _delegation_watch_count(scope_user_ids)

    blocked_publish = int(publish_summary.get("blocked_count") or 0)
    ready_publish = int(publish_summary.get("ready_count") or 0)
    internal_preview = int(publish_summary.get("internal_preview_count") or 0)
    risk_threads = int(len(today_coverage_alerts or [])) + int(overdue_tasks_count or 0) + blocked_publish

    if blocked_publish > 0:
        focus_text = f"Yayın öncesi {blocked_publish} blokaj kapanmalı; personel analizi ve bildirim akışı birlikte izlenmeli."
    elif pending_approvals > 0:
        focus_text = f"{pending_approvals} açık değerlendirme görevi yönetici işlemi bekliyor."
    elif ready_publish > 0:
        focus_text = f"{ready_publish} kayıt yayına hazır; personele açılmadan önce son kontrol tamamlanmalı."
    else:
        focus_text = "Performans, izin–vekâlet ve bildirim akışı birlikte izlenmeli."

    memory_bits: list[str] = []
    if unread_notifications > 0:
        memory_bits.append(f"{unread_notifications} okunmamış bildirim")
    if delegation_watch > 0:
        memory_bits.append(f"{delegation_watch} aktif vekâlet")
    if internal_preview > 0:
        memory_bits.append(f"{internal_preview} iç kullanım kaydı")
    memory_text = ", ".join(memory_bits) + " var." if memory_bits else "Karar ve bildirim hareketleri denetim iziyle birlikte tutulmalıdır."

    return {
        "pending_approvals": pending_approvals,
        "risk_threads": risk_threads,
        "publish_ready": ready_publish,
        "delegation_watch": delegation_watch,
        "unread_notifications": unread_notifications,
        "blocked_publish": blocked_publish,
        "internal_preview": internal_preview,
        "focus_text": focus_text,
        "memory_text": memory_text,
    }

def _build_executive_snapshot_light(
    *,
    user,
    scope_user_ids: list[int],
    overdue_tasks_count: int,
) -> dict[str, Any]:
    pending_approvals = _open_assignment_count(getattr(user, "id", 0) or 0)
    unread_notifications = _notification_unread_count(getattr(user, "id", 0) or 0)
    delegation_watch = _delegation_watch_count(scope_user_ids)
    risk_threads = int(overdue_tasks_count or 0) + int(pending_approvals or 0)

    if pending_approvals > 0:
        focus_text = f"{pending_approvals} açık değerlendirme görevi yönetici işlemi bekliyor."
    elif overdue_tasks_count > 0:
        focus_text = f"{overdue_tasks_count} geciken görev için öncelikli müdahale gerekiyor."
    else:
        focus_text = "Performans, izin–vekâlet ve bildirim akışı birlikte izlenmeli."

    memory_bits: list[str] = []
    if unread_notifications > 0:
        memory_bits.append(f"{unread_notifications} okunmamış bildirim")
    if delegation_watch > 0:
        memory_bits.append(f"{delegation_watch} aktif vekâlet")
    memory_text = ", ".join(memory_bits) + " var." if memory_bits else "Karar ve bildirim hareketleri denetim iziyle birlikte tutulmalıdır."

    return {
        "pending_approvals": pending_approvals,
        "risk_threads": risk_threads,
        "publish_ready": 0,
        "delegation_watch": delegation_watch,
        "unread_notifications": unread_notifications,
        "blocked_publish": 0,
        "internal_preview": 0,
        "focus_text": focus_text,
        "memory_text": memory_text,
    }


def build_dashboard_context(user, detail_level: str = "full") -> dict[str, Any]:
    active_period = _active_period()
    periods = _period_rows() if detail_level != "core" else []
    scope = build_user_scope_context(user, (request.args.get("scope") or "").strip().lower() or None)
    scope_user_ids = list(scope.get("scope_user_ids") or [])

    if detail_level == "core":
        pending_count = safe_count(build_dashboard_assignment_query(user.id, statuses=("bekliyor",)), label="dashboard_pending_tasks")
        completed_task_count = safe_count(build_dashboard_assignment_query(user.id, statuses=("tamamlandi",)), label="dashboard_completed_tasks")
        pending_rows: list[Any] = []
        partial_rows: list[Any] = []
        now = utc_now()
        base_query = build_dashboard_assignment_query(user.id).filter(
            EvaluationAssignment.status.in_(("bekliyor", "kismen_tamamlandi")),
            EvaluationAssignment.due_date.isnot(None),
        )
        overdue_tasks_count = safe_count(base_query.filter(EvaluationAssignment.due_date < now), label="dashboard_overdue_tasks")
        due_soon_tasks_count = safe_count(
            base_query.filter(
                EvaluationAssignment.due_date >= now,
                EvaluationAssignment.due_date <= (now + timedelta(days=2)),
            ),
            label="dashboard_due_soon_tasks",
        )
        overdue_task_rows: list[Any] = []
    else:
        pending_count, completed_task_count, pending_rows, partial_rows = _assignment_counts(user.id)
        overdue_tasks_count, due_soon_tasks_count, overdue_task_rows = _assignment_deadline_metrics(user.id)
    upcoming_meetings_count = _feedback_meeting_count(user.id)
    my_feedback_requests = _feedback_request_count(scope_user_ids)

    total_evaluations, completed_evaluations, unpublished_results_count, pending_feedback_requests, total_assignments = _evaluation_metrics(
        getattr(active_period, "id", None), scope_user_ids,
    )
    latest_log_payload = {"created_at": None, "rows": [], "summary": build_assignment_log_summary([])}
    coverage_summary = build_assignment_log_summary([])
    coverage_risk_score = 0
    coverage_risk_tone, coverage_risk_label = _coverage_tone(coverage_risk_score)
    critical_units: list[dict[str, Any]] = []
    period_risk_rows: list[dict[str, Any]] = []
    today_coverage_alerts: list[Any] = []
    informational_special_cases: list[Any] = []

    completion_rate = round((completed_evaluations / total_evaluations) * 100, 2) if total_evaluations else 0
    executive_snapshot = _build_executive_snapshot_light(
        user=user,
        scope_user_ids=scope_user_ids,
        overdue_tasks_count=overdue_tasks_count,
    )

    if detail_level != "core":
        latest_log_payload = _latest_scope_log(getattr(active_period, "id", None), scope_user_ids)
        coverage_summary = latest_log_payload.get("summary") or build_assignment_log_summary([])
        # BYS360_SPECIAL_SCOPE_RISK_GRACE_FILTER
        # Özel dönemlerde amirler yalnızca değerlendirici olarak tutulduğunda
        # dashboard bunu canlı kapsam riski gibi şişirmemelidir. Gerçek risk
        # yalnızca açıkta/zincir hatası gibi müdahale gerektiren satırlardan gelir.
        if active_period and str(getattr(active_period, "scope_type", "all") or "all") != "all":
            special_rows = [
                row for row in (latest_log_payload.get("rows") or [])
                if (_row_value(row, "event_type", "") or "") in {"uncovered", "chain_issue", "warning"}
                and not is_informational_special_case(_row_value(row, "reason", None), _row_value(row, "event_type", None))
            ]
            if not special_rows:
                coverage_summary = build_assignment_log_summary([])
        coverage_risk_score = _risk_score(coverage_summary)
        coverage_risk_tone, coverage_risk_label = _coverage_tone(coverage_risk_score)
        critical_units = build_assignment_unit_summary(latest_log_payload.get("rows") or [], top_n=8)
        period_risk_rows = _period_risk_rows(periods, scope_user_ids)

        today_coverage_alerts = [
            row for row in (latest_log_payload.get("rows") or [])
            if (_row_value(row, "event_type", "") or "") in {"uncovered", "chain_issue", "warning", "exempted"}
            and not is_informational_special_case(_row_value(row, "reason", None), _row_value(row, "event_type", None))
        ][:6]

        informational_special_cases = [
            row for row in (latest_log_payload.get("rows") or [])
            if is_informational_special_case(_row_value(row, "reason", None), _row_value(row, "event_type", None))
        ][:6]

        executive_snapshot = _build_executive_snapshot(
            user=user,
            active_period=active_period,
            scope_user_ids=scope_user_ids,
            overdue_tasks_count=overdue_tasks_count,
            today_coverage_alerts=today_coverage_alerts,
        )

    context = {
        "active_period": active_period,
        "periods": periods,
        "dashboard_scope": scope,
        "my_pending_tasks": pending_count,
        "my_completed_tasks": completed_task_count,
        "my_overdue_tasks": overdue_tasks_count,
        "my_due_soon_tasks": due_soon_tasks_count,
        "my_feedback_requests": my_feedback_requests,
        "pending_feedback_requests": pending_feedback_requests,
        "upcoming_meetings_count": upcoming_meetings_count,
        "coverage_summary": coverage_summary,
        "coverage_risk_score": coverage_risk_score,
        "coverage_risk_tone": coverage_risk_tone,
        "coverage_risk_label": coverage_risk_label,
        "coverage_run_created_at": latest_log_payload.get("created_at"),
        "today_coverage_alerts": today_coverage_alerts,
        "informational_special_cases": informational_special_cases,
        "critical_units": critical_units,
        "period_risk_rows": period_risk_rows,
        "pending_tasks": pending_rows,
        "partial_tasks": partial_rows,
        "overdue_tasks": overdue_task_rows,
        "total_assignments": total_assignments,
        "total_evaluations": total_evaluations,
        "completed_evaluations": completed_evaluations,
        "completion_rate": completion_rate,
        "published_period_count": _published_period_count(),
        "unpublished_results_count": unpublished_results_count,
        "executive_snapshot": executive_snapshot,
    }
    if detail_level != "core":
        try:
            context.update(build_dashboard_signal_context(user))
        except Exception:
            safe_db_rollback()
        try:
            context["dashboard_focus_hints"] = build_dashboard_focus_hints(context)
        except Exception:
            context["dashboard_focus_hints"] = []
    else:
        context["dashboard_focus_hints"] = []
    return context