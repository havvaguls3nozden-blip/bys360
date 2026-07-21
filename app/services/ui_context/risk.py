from __future__ import annotations

from typing import Any

from flask import request
from flask_login import current_user

from app.services.performance.assignments import (
    build_assignment_log_summary,
    get_latest_assignment_generation_logs,
    is_informational_special_case,
)

from .scope import build_user_scope_context

BANNER_ALLOWED_PREFIXES = (
    "main.dashboard",
    "main.performance_",
    "main.hr_",
    "main.repository_",
    "main.education_",
    "main.strategy_",
)


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

def _row_value(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def _is_risk_special_case(row: Any) -> bool:
    return is_informational_special_case(_row_value(row, "reason", None), _row_value(row, "event_type", None), _row_value(row, "manager_level", None))

def _risk_rows(rows: list[Any]) -> list[Any]:
    return [
        row for row in (rows or [])
        if not is_informational_special_case(_row_value(row, "reason", None), _row_value(row, "event_type", None), _row_value(row, "manager_level", None))
    ]

def get_global_risk_banner_context() -> dict[str, Any]:
    endpoint = (request.endpoint or "").strip()
    if not getattr(current_user, "is_authenticated", False):
        return {"show_global_risk_banner": False, "global_risk_banner": None}
    if endpoint and not endpoint.startswith(BANNER_ALLOWED_PREFIXES):
        return {"show_global_risk_banner": False, "global_risk_banner": None}

    from app.models import PerformancePeriod

    period = (
        PerformancePeriod.query
        .filter_by(is_active=True)
        .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
        .first()
    )
    if not period:
        return {"show_global_risk_banner": False, "global_risk_banner": None}

    scope = build_user_scope_context(current_user, (request.args.get("scope") or "").strip().lower() or None)
    payload = get_latest_assignment_generation_logs(period.id, limit=200, employee_ids=list(scope.get("scope_user_ids") or []))
    all_rows = payload.get("rows") or []
    filtered_rows = _risk_rows(all_rows)
    summary = build_assignment_log_summary(filtered_rows)
    special_case_count = int((payload.get("summary") or {}).get("special_case", 0))
    score = _risk_score(summary)
    tone, label = _coverage_tone(score)
    if score <= 0 or not filtered_rows:
        return {"show_global_risk_banner": False, "global_risk_banner": None}

    focus_rows = [
        {
            "employee_name": getattr(_row_value(row, "employee", None), "full_name", None)
            or f"{getattr(_row_value(row, 'employee', None), 'ad', '')} {getattr(getattr(row, 'employee', None), 'soyad', '')}".strip()
            or "Personel",
            "unit_name": getattr(_row_value(row, "employee", None), "birim", None)
            or getattr(_row_value(row, "employee", None), "ust_birim", None)
            or "Tanımsız Birim",
            "manager_level": _row_value(row, "manager_level", None),
            "reason": _row_value(row, "reason", None),
            "event_label": (_row_value(row, "event_type", "") or "").replace("_", " ").title(),
        }
        for row in filtered_rows
        if (_row_value(row, "event_type", "") or "") in {"uncovered", "chain_issue", "warning", "exempted"}
    ][:5]

    return {
        "show_global_risk_banner": True,
        "global_risk_banner": {
            "tone": tone,
            "title": "Canlı kapsama riski izleniyor",
            "message": "Son görev üretim koşusuna göre açıkta kalan zincirler, muaf kayıtlar veya uyarılar görünüyor.",
            "scope_role_title": scope.get("role_title"),
            "scope_label": scope.get("scope_label"),
            "scope_user_count": scope.get("scope_user_count"),
            "scope_unit_count": scope.get("scope_unit_count"),
            "period_title": getattr(period, "title", "Aktif dönem"),
            "label": label,
            "open_issue_count": int(summary.get("uncovered", 0)) + int(summary.get("chain_issue", 0)) + int(summary.get("warning", 0)),
            "impacted_employee_count": len({_row_value(row, "employee_id", None) for row in filtered_rows if _row_value(row, "employee_id", None)}),
            "summary": summary,
            "special_case_count": special_case_count,
            "today_critical_count": len(focus_rows),
            "run_created_at": payload.get("created_at"),
            "focus_rows": focus_rows,
            "action_url": "/dashboard",
            "action_label": "Dashboardı aç",
        },
    }