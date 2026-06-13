from __future__ import annotations



from flask_login import current_user

from .audit import log_ai_request, upsert_ai_summary_cache
from .client import get_ai_client
from .guardrails import ensure_ai_access, sanitize_output_text
from .prompts import get_prompt_definition
from .redaction import redact_payload



def _build_dashboard_context(*args, **kwargs):
    from app.services.ui_context.dashboard import build_dashboard_context as _impl
    return _impl(*args, **kwargs)

def _dashboard_payload() -> dict:
    context = _build_dashboard_context(current_user) or {}
    coverage_summary = context.get("coverage_summary") or {}
    critical_units = []
    for row in list(context.get("critical_units") or [])[:6]:
        critical_units.append({
            "unit_name": row.get("unit_name"),
            "risk_score": row.get("risk_score"),
            "uncovered": row.get("uncovered"),
            "delegated": row.get("delegated"),
        })

    alerts = []
    for row in list(context.get("today_coverage_alerts") or [])[:4]:
        employee = row.get("employee")
        employee_name = getattr(employee, 'full_name', None) or None
        alerts.append({
            "employee": employee_name,
            "event_type": row.get("event_type"),
            "reason": row.get("reason"),
            "manager_level": row.get("manager_level"),
        })

    payload = {
        "active_period": getattr(context.get("active_period"), "title", None),
        "scope_heading": (context.get("dashboard_scope") or {}).get("scope_heading"),
        "scope_label": (context.get("dashboard_scope") or {}).get("scope_label"),
        "my_pending_tasks": context.get("my_pending_tasks"),
        "my_completed_tasks": context.get("my_completed_tasks"),
        "my_overdue_tasks": context.get("my_overdue_tasks"),
        "pending_feedback_requests": context.get("pending_feedback_requests"),
        "upcoming_meetings_count": context.get("upcoming_meetings_count"),
        "coverage_risk_score": context.get("coverage_risk_score"),
        "coverage_risk_label": context.get("coverage_risk_label"),
        "completion_rate": context.get("completion_rate"),
        "unpublished_results_count": context.get("unpublished_results_count"),
        "coverage_summary": coverage_summary,
        "critical_units": critical_units,
        "today_alerts": alerts,
    }
    return redact_payload(payload)


def build_dashboard_brief_response() -> dict:
    policy = ensure_ai_access("dashboard", "brief")
    payload = _dashboard_payload()

    prompt = get_prompt_definition("dashboard", "brief")
    user_prompt = (
        "Aşağıdaki dashboard görünümü için anlık kullanıcı özeti üret. "
        "Genel durum, dikkat gerektirenler ve bugün için öneriyi kısa yaz:\n"
        f"{payload}"
    )
    result = get_ai_client().generate(
        system_prompt=prompt["system"],
        user_prompt=user_prompt,
        prompt_version=prompt["version"],
    )
    summary_text = sanitize_output_text(result.text)
    log_row = log_ai_request(
        module_type="dashboard",
        feature_type="brief",
        target_table="dashboard_runtime",
        target_id=getattr(current_user, "id", None),
        user_id=getattr(current_user, "id", None),
        request_text=user_prompt,
        response_text=summary_text,
        provider_name=result.provider_name,
        model_name=result.model_name,
        prompt_version=result.prompt_version,
        latency_ms=result.latency_ms,
        token_in=result.token_in,
        token_out=result.token_out,
        was_masked=True,
        was_user_visible=policy.user_visible,
    )
    upsert_ai_summary_cache(
        module_type="dashboard",
        target_table="dashboard_runtime",
        target_id=int(getattr(current_user, "id", 0) or 0),
        summary_kind="brief",
        summary_text=summary_text,
    )
    return {
        "ok": True,
        "data": {
            "summary": summary_text,
            "ai_request_log_id": log_row.id if log_row else None,
            "metrics": {
                "coverage_risk_score": payload.get("coverage_risk_score"),
                "my_overdue_tasks": payload.get("my_overdue_tasks"),
                "pending_feedback_requests": payload.get("pending_feedback_requests"),
                "upcoming_meetings_count": payload.get("upcoming_meetings_count"),
            },
        },
    }