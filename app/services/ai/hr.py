from __future__ import annotations

from flask_login import current_user

from app.models import PerformancePeriod
from app.services.leave_delegation_service import (
    build_leave_delegation_health_snapshot,
    build_leave_overview,
)

from .audit import ensure_recommendation_rows, log_ai_request, upsert_ai_summary_cache
from .client import get_ai_client
from .guardrails import ensure_ai_access, sanitize_output_text
from .prompts import get_prompt_definition
from .redaction import redact_payload


def _hr_leave_payload() -> dict:
    overview = build_leave_overview()
    health = build_leave_delegation_health_snapshot()
    current_period = PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()
    pending_requests = []
    for row in list(overview.pending_requests or [])[:6]:
        pending_requests.append({
            "user": getattr(getattr(row, "user", None), "full_name", None),
            "status": getattr(row, "status", None),
            "start_date": str(getattr(row, "start_date", None)) if getattr(row, "start_date", None) else None,
            "end_date": str(getattr(row, "end_date", None)) if getattr(row, "end_date", None) else None,
            "leave_type": getattr(row, "leave_type", None),
            "blocks_manager_duties": bool(getattr(row, "blocks_manager_duties", False)),
        })
    active_delegations = []
    for row in list(overview.active_delegations or [])[:6]:
        active_delegations.append({
            "delegator": getattr(getattr(row, "delegator", None), "full_name", None),
            "delegate": getattr(getattr(row, "delegate", None), "full_name", None),
            "start_date": str(getattr(row, "start_date", None)) if getattr(row, "start_date", None) else None,
            "end_date": str(getattr(row, "end_date", None)) if getattr(row, "end_date", None) else None,
            "scope_type": getattr(row, "scope_type", None),
            "status": getattr(row, "status", None),
        })
    payload = {
        "current_year": overview.current_year,
        "period_id": health.get("period_id") or getattr(current_period, "id", None) or 0,
        "period_title": health.get("period_title") or getattr(current_period, "title", None),
        "summary": dict(overview.summary or {}),
        "health": health,
        "leave_modes": health.get("leave_modes") or {},
        "pending_requests": pending_requests,
        "active_delegations": active_delegations,
        "notes": list(overview.notes or [])[:4],
        "active_delegation_count": len(list(overview.active_delegations or [])),
        "pending_request_count": len(list(overview.pending_requests or [])),
    }
    return redact_payload(payload)


def _recommendation_titles(payload: dict) -> list[str]:
    titles: list[str] = []
    coverage = (payload.get("health") or {}).get("coverage_summary") or {}
    if int(coverage.get("uncovered") or 0) > 0:
        titles.append("İzin / vekâlet görünümünde açıkta kalan amir zinciri sinyali var.")
    if int((payload.get("summary") or {}).get("pending_count") or 0) >= 3:
        titles.append("Bekleyen izin kararları operasyon temposunu yavaşlatabilir.")
    if int((payload.get("health") or {}).get("delegated_open_assignments") or 0) > 0:
        titles.append("Delegasyon üzerinden yürüyen açık görevler ayrıca izlenmeli.")
    return titles


def build_hr_leave_brief_response() -> dict:
    policy = ensure_ai_access("hr", "leave_brief")
    payload = _hr_leave_payload()
    prompt = get_prompt_definition("hr", "leave_brief")
    user_prompt = (
        "Aşağıdaki izin ve vekâlet görünümü için kısa yönetici özeti üret. "
        "Birim baskısı, vekâlet, bekleyen karar ve açık görev etkisini sakin dille yaz:\n"
        f"{payload}"
    )
    result = get_ai_client().generate(
        system_prompt=prompt["system"],
        user_prompt=user_prompt,
        prompt_version=prompt["version"],
    )
    summary_text = sanitize_output_text(result.text)
    target_id = int(payload.get("period_id") or 0)
    log_row = log_ai_request(
        module_type="hr",
        feature_type="leave_brief",
        target_table="hr_leave_overview",
        target_id=target_id,
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
    rec_rows = ensure_recommendation_rows(
        module_type="hr",
        target_table="hr_leave_overview",
        target_id=target_id,
        recommendation_type="leave_governance",
        titles=_recommendation_titles(payload),
        ai_request_log_id=getattr(log_row, "id", None),
        created_by_id=getattr(current_user, "id", None),
        severity="warning",
    )
    upsert_ai_summary_cache(
        module_type="hr",
        target_table="hr_leave_overview",
        target_id=target_id,
        summary_kind="leave_brief",
        summary_text=summary_text,
        source_hash=f"hr-leave:{target_id}:{payload.get('pending_request_count') or 0}:{payload.get('active_delegation_count') or 0}",
    )
    health = payload.get("health") or {}
    coverage = health.get("coverage_summary") or {}
    return {
        "ok": True,
        "data": {
            "summary": summary_text,
            "ai_request_log_id": getattr(log_row, "id", None),
            "recommendation_ids": [row.id for row in rec_rows],
            "metrics": {
                "uncovered": int(coverage.get("uncovered") or 0),
                "delegated_open_assignments": int(health.get("delegated_open_assignments") or 0),
                "active_delegation_count": int(payload.get("active_delegation_count") or 0),
                "pending_request_count": int(payload.get("pending_request_count") or 0),
            },
        },
    }
