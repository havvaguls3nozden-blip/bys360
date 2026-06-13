from __future__ import annotations



from datetime import datetime

from flask import current_app, redirect, request, url_for
from flask_login import current_user

from app.route_support import ALLOWED_BYPASS_ENDPOINTS, build_menu_visibility_map, safe_db_rollback
from app.services.message_service import get_unread_notification_count
from app.services.performance.assignments import build_assignment_unit_summary, get_latest_assignment_generation_logs
from app.services.performance.assignments import build_assignment_log_summary
from app.services.query_health_service import build_dashboard_meeting_query
from app.services.ui_context import (
    build_dashboard_context,
    build_db_check_context,
    build_user_scope_context,
    get_global_risk_banner_context,
    get_route_helper_context,
)


def get_menu_visibility_context() -> dict[str, object]:
    if current_user.is_authenticated:
        try:
            visibility = build_menu_visibility_map(current_user)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/view_helpers.py:28")
            visibility = {}
    else:
        visibility = {}
    return {"menu_visibility_map": visibility}


def enforce_first_login_security_flow_redirect():
    if not current_user.is_authenticated:
        return None
    endpoint = request.endpoint or ""
    if endpoint.startswith("static") or endpoint in ALLOWED_BYPASS_ENDPOINTS:
        return None
    if getattr(current_user, "must_set_security_question", False):
        return redirect(url_for("main.account_security_setup"))
    if getattr(current_user, "must_change_password", False):
        return redirect(url_for("main.account_change_password"))
    return None


def get_notification_context() -> dict[str, int]:
    if current_user.is_authenticated:
        return {"unread_notification_count": get_unread_notification_count(current_user.id)}
    return {"unread_notification_count": 0}


def _empty_coverage_summary() -> dict[str, int]:
    return build_assignment_log_summary([])


def get_performance_context() -> dict:
    if not current_user.is_authenticated:
        return {
            "active_period": None,
            "periods": [],
            "criteria_count": 0,
            "employee_count": 0,
            "evaluation_count": 0,
            "waiting_feedback_count": 0,
            "today_meeting_count": 0,
            "coverage_summary": _empty_coverage_summary(),
            "assignment_generation_logs": {"run_key": None, "created_at": None, "rows": [], "summary": _empty_coverage_summary()},
        }

    context = build_dashboard_context(current_user)
    return {
        "active_period": context.get("active_period"),
        "periods": context.get("periods") or [],
        "criteria_count": context.get("criteria_count", 0),
        "employee_count": context.get("dashboard_scope", {}).get("scope_user_count", 0),
        "evaluation_count": context.get("total_evaluations", 0),
        "waiting_feedback_count": context.get("pending_feedback_requests", 0),
        "today_meeting_count": context.get("upcoming_meetings_count", 0),
        "coverage_summary": context.get("coverage_summary") or _empty_coverage_summary(),
        "assignment_generation_logs": {
            "run_key": None,
            "created_at": context.get("coverage_run_created_at"),
            "rows": context.get("today_coverage_alerts") or [],
            "summary": context.get("coverage_summary") or _empty_coverage_summary(),
        },
    }


def build_surface_scope_context(user, raw_scope: str | None) -> dict:
    scope = build_user_scope_context(user, raw_scope)
    selected_scope = scope.get("scope_mode") or "mine"
    employee_ids = list(scope.get("scope_user_ids") or [])
    if selected_scope == "mine" and getattr(user, "id", None):
        employee_ids = [user.id]

    scope_options = [
        {"value": row["value"], "label": row["label"]}
        for row in (scope.get("scope_options") or [])
    ]
    scope_option_pairs = [(row["value"], row["label"]) for row in scope_options]

    return {
        "scope_options": scope_options,
        "scope_option_pairs": scope_option_pairs,
        "selected_scope": selected_scope,
        "employee_ids": employee_ids,
        "scope_label": scope.get("scope_label"),
        "scope_heading": scope.get("scope_heading"),
        "scope_description": scope.get("scope_description"),
        "scope_user_count": scope.get("scope_user_count", len(employee_ids)),
        "scope_unit_count": scope.get("scope_unit_count", 0),
        "role_title": scope.get("role_title"),
    }


def build_scope_switch_context(
    user,
    raw_scope: str | None,
    endpoint: str | None = None,
    extra_params: dict | None = None,
    **_legacy_kwargs,
) -> dict:
    # Eski route'larda managed_scope_users / managed_scope_label gibi ek argumanlar
    # gonderilebiliyor. Yeni ortak helper bunlari zorunlu kullanmiyor; ancak
    # geriye donuk uyumluluk icin sessizce kabul ediyoruz.
    scope_ctx = build_surface_scope_context(user, raw_scope)
    endpoint = endpoint or request.endpoint
    options = []
    extra_params = extra_params or {}
    label_map = {row["value"]: row.get("label", row["value"]) for row in build_user_scope_context(user, raw_scope).get("scope_options", [])}
    for row in scope_ctx["scope_options"]:
        params = {**extra_params, "scope": row["value"]}
        options.append({
            "value": row["value"],
            "label": row["label"],
            "url": url_for(endpoint, **params),
            "selected": row["value"] == scope_ctx["selected_scope"],
        })
    return {
        **scope_ctx,
        "scope_switch_options": options,
        "scope_label": label_map.get(scope_ctx["selected_scope"], scope_ctx["selected_scope"]),
    }


# BYS360_PHASE3_6_VIEW_HELPERS_PEER_SCOPE_WRAPPER
_BYS360_PHASE3_6_ORIGINAL_BUILD_SURFACE_SCOPE_CONTEXT = build_surface_scope_context


def build_surface_scope_context(user, raw_scope: str | None) -> dict:
    context = _BYS360_PHASE3_6_ORIGINAL_BUILD_SURFACE_SCOPE_CONTEXT(user, raw_scope)
    try:
        from app.services.performance.peer_published_score_visibility import (
            decorate_surface_scope_context_for_peer_published_scores,
        )
        context = decorate_surface_scope_context_for_peer_published_scores(context, user=user, raw_scope=raw_scope)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/view_helpers.py)")
    return context
