from __future__ import annotations

import app.institutional.hr_common as _hr_common
from app.institutional.hr_form_helpers import (
    AttendanceException,
    DelegationAssignment,
    LeaveBalance,
    PersonnelLeave,
    _create_delegation_from_form,
    _handle_leave_post,
    _handle_leave_balance_post,
    _handle_attendance_post,
    _handle_manual_delegation_post,
)
from app.institutional.hr_scope_helpers import (
    utc_now,
    date,
    datetime,
    timedelta,
    import_module,
    SimpleNamespace,
    Any,
    Iterable,
    csv,
    io,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    request,
    url_for,
    current_user,
    login_required,
    inspect,
    or_,
    BuildError,
    db,
    main_bp,
    consume_form_token,
    issue_form_token,
    manager_required,
    menu_key_required,
    safe_db_rollback,
    safe_render,
    LEGACY_SHIM,
    LEGACY_RUNTIME_STATUS,
    LEGACY_ROUTE_FAMILY,
    LEGACY_NOTE,
    LEAVE_TYPE_CHOICES,
    LEAVE_STATUS_CHOICES,
    ATTENDANCE_TYPE_CHOICES,
    DELEGATION_SCOPE_CHOICES,
    DELEGATION_STATUS_CHOICES,
    PERFORMANCE_MODE_LABELS,
    ACTIVE_STATUSES,
    PENDING_STATUSES,
    _safe_import,
    _endpoint_registered,
    _url_or_hash,
    _table_exists,

    _current_user_id,
    _model_ready,
    _safe_text,
    _safe_int,
    _safe_float,
    _safe_commit,
    _resolve_period_id_from_form,
    _date_range_weekday_count,
    _calculate_leave_day_count,
    _active_delegation_exists,
    _leave_overlaps,
    _attendance_overlaps,
    _bool_from_form,
    _active_period,
    _parse_date,
    _status_label,
    _scope_label,
    _leave_type_label,
    _attendance_type_label,
    _performance_mode_label,
    _full_name,
    _unit_name,
    _role_key,
    _profile_missing_fields,
    _profile_score,
    _period_options,
    _selected_period_id,
    _selected_user_id,
    _all_personnel,
    _requested_scope_mode,
    _fallback_scope_context,
    _hr_scope_context,
    _scope_user_ids,
    _filter_users_in_scope,
    _scope_bundle,
    _empty_overview,
    _leave_overview,
    _delegation_health,
    _query_rows,
    _count_rows,
    _selected_user_guard,
    _unit_pulse,
)

def _reports_context() -> dict[str, Any]:
    hr_scope, scope_users, scope_user_ids = _scope_bundle()
    selected_scope_mode = hr_scope.get("scope_mode") or "personal"
    active_period = _active_period()
    leaves = _query_rows(PersonnelLeave, scope_user_ids=scope_user_ids, date_field="start_date", limit=500)
    attendance = _query_rows(AttendanceException, scope_user_ids=scope_user_ids, date_field="record_date", limit=500)
    delegations = []
    if _model_ready(DelegationAssignment):
        try:
            q = DelegationAssignment.query
            if scope_user_ids:
                q = q.filter(or_(DelegationAssignment.delegator_user_id.in_(scope_user_ids), DelegationAssignment.delegate_user_id.in_(scope_user_ids)))
            delegations = q.order_by(DelegationAssignment.id.desc()).limit(500).all()
        except Exception:
            safe_db_rollback()
    health = _delegation_health(getattr(active_period, "id", None))
    unit_stats = []
    for row in _unit_pulse(scope_users, scope_user_ids):
        unit_stats.append({"unit_name": row["unit_name"], "user_count": row["employee_count"], "leave_count": row["leave_today"], "attendance_count": row["attendance_today"], "delegation_count": 0, "risk_score": row["risk_score"]})
    readiness = {
        "ready": True,
        "ready_for_go_live": True,
        "warning_count": int(bool(((health.get("coverage_summary") or {}).get("uncovered") or 0))),
        "critical_count": 0,
        "notes": list(health.get("notes") or [])[:6],
    }
    return {
        "hr_scope": hr_scope,
        "selected_scope_mode": selected_scope_mode,
        "scope_label": hr_scope.get("scope_label") or "Kapsam",
        "scope_heading": hr_scope.get("scope_heading") or "Kapsam",
        "scope_description": hr_scope.get("scope_description") or "",
        "scope_options": hr_scope.get("scope_options") or [],
        "scope_user_count": len(scope_users),
        "scope_unit_count": len({_unit_name(u) for u in scope_users}),
        "active_period": active_period,
        "active_period_title": getattr(active_period, "title", None),
        "leave_count": len(leaves),
        "attendance_count": len(attendance),
        "delegation_count": len(delegations),
        "unit_stats": unit_stats,
        "leave_type_stats": _stats_by(leaves, "leave_type", _leave_type_label),
        "attendance_type_stats": _stats_by(attendance, "exception_type", _attendance_type_label),
        "coverage_unit_rows": [],
        "uncovered_rows": [],
        "exempt_rows": [],
        "special_case_logs": [],
        "latest_assignment_logs": [],
        "latest_assignment_log_summary": {"info": 0, "warning": 0, "error": 0},
        "latest_assignment_log_severity_summary": {"info": 0, "warning": 0, "error": 0},
        "latest_assignment_log_created_at": None,
        "latest_assignment_log_run_key": None,
        "readiness": readiness,
        "pilot_notes": readiness["notes"],
        "pilot_scenarios": [],
        "pilot_scenario_summary": {"passed": 0, "warning": 0, "error": 0},
        "pilot_smoke_rows": [],
        "go_live_approval_rows": [],
        "security_runtime": _security_runtime(),
        "leave_type_label": _leave_type_label,
        "attendance_type_label": _attendance_type_label,
    }


def _stats_by(rows: list[Any], attr: str, label_fn) -> list[dict[str, Any]]:
    data: dict[str, int] = {}
    for row in rows:
        key = _safe_text(getattr(row, attr, None), "diger")
        data[key] = data.get(key, 0) + 1
    return [{"code": key, "label": label_fn(key), "count": value} for key, value in sorted(data.items(), key=lambda item: (-item[1], item[0]))]


def _security_runtime() -> dict[str, Any]:
    cfg = current_app.config if current_app else {}
    return {
        "session_cookie_secure": bool(cfg.get("SESSION_COOKIE_SECURE", False)),
        "session_cookie_samesite": cfg.get("SESSION_COOKIE_SAMESITE", "Lax"),
        "csrf_time_limit": cfg.get("WTF_CSRF_TIME_LIMIT", None),
        "max_content_length": cfg.get("MAX_CONTENT_LENGTH", None),
    }


@main_bp.route("/hr-management/reports")
@login_required
@manager_required
@menu_key_required("hr_reports")
def hr_reports():
    return safe_render("hr_reports.html", **_reports_context())


@main_bp.route("/hr-management/reports/print")
@login_required
@manager_required
@menu_key_required("hr_reports")
def hr_reports_print():
    ctx = _reports_context()
    return safe_render("hr_reports_print.html", **ctx)


def _export_simple_report(filename: str, context: dict[str, Any]) -> Response:
    fmt = _safe_text(request.args.get("format"), "csv").lower()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Başlık", "Değer"])
    writer.writerow(["Kapsam", context.get("scope_label") or context.get("hr_scope", {}).get("scope_label") or "Kapsam"])
    writer.writerow(["Personel", context.get("scope_user_count") or len(context.get("users") or [])])
    writer.writerow(["İzin", context.get("leave_count") or len(context.get("leaves") or [])])
    writer.writerow(["Devamsızlık", context.get("attendance_count") or len(context.get("attendance_rows") or [])])
    writer.writerow(["Vekâlet", context.get("delegation_count") or len(context.get("active_delegations") or context.get("delegations") or [])])
    data = output.getvalue().encode("utf-8-sig")
    download_name = f"{filename}.{ 'csv' if fmt != 'xlsx' else 'csv' }"
    return Response(data, mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={download_name}"})


@main_bp.route("/hr-management/reports/export")
@login_required
@manager_required
@menu_key_required("hr_reports")
def hr_reports_export():
    return _export_simple_report("personel_raporlari", _reports_context())


@main_bp.route("/hr-management/reports/readiness.json")
@login_required
@manager_required
@menu_key_required("hr_reports")
def hr_reports_readiness():
    return jsonify(_reports_context().get("readiness") or {})


@main_bp.route("/hr-management/reports/pilot-acceptance.json")
@login_required
@manager_required
@menu_key_required("hr_reports")
def hr_reports_pilot_acceptance():
    ctx = _reports_context()
    return jsonify({"ok": True, "scope": ctx.get("scope_label"), "user_count": ctx.get("scope_user_count"), "notes": ctx.get("pilot_notes", [])})


@main_bp.route("/hr-management/reports/smoke-check.json")
@login_required
@manager_required
@menu_key_required("hr_reports")
def hr_reports_smoke_check():
    return jsonify({"ok": True, "routes": ["hr_management", "hr_leave_management", "hr_attendance_management", "hr_reports"]})


@main_bp.route("/hr-management/reports/go-live-approval.json")
@login_required
@manager_required
@menu_key_required("hr_reports")
def hr_reports_go_live_approval():
    readiness = _reports_context().get("readiness") or {}
    return jsonify({"ready_for_go_live": bool(readiness.get("ready_for_go_live", False)), "readiness": readiness})


def _fallback_personnel_operations():
    try:
        from app.services.hr_operations_service import build_hr_personnel_operations_context
        hr_scope, scope_users, _ids = _scope_bundle()
        payload = build_hr_personnel_operations_context(hr_scope, scope_users, _active_period())
        return safe_render("hr_personnel_operations.html", **payload)
    except Exception as exc:
        safe_db_rollback()
        current_app.logger.exception("Personel özlük fallback ekranı açılamadı")
        flash(f"Personel özlük ekranı geçici olarak açılamadı: {exc}", "warning")
        return redirect(_url_or_hash("main.personnel_list"))


# Canlı çekirdek alt route aileleri. Kapsam dışı modüller bilinçli yüklenmez.
LOADED_CHILD_ROUTE_MODULES: list[str] = []
for _module in (
    "app.institutional.org_unit_routes",
    "app.institutional.hr_personnel_operations_routes",
    "app.institutional.hr_personnel_extension_routes",
    "app.institutional.hr_personnel_phase10_routes",
    "app.institutional.hr_personnel_phase11_routes",
    "app.institutional.hr_personnel_phase12_routes",
    "app.institutional.hr_personnel_phase13_routes",
    "app.institutional.hr_request_task_routes",
    "app.institutional.hr_request_analytics_routes",
):
    if _safe_import(_module):
        LOADED_CHILD_ROUTE_MODULES.append(_module)


# /admin/org-units endpointi gerçek app.institutional.org_unit_routes modülündedir.
# Burada fallback kaydı yapılmaz; aynı endpointin ikinci kez eklenmesi Flask açılışını durdurur.


if not _endpoint_registered("hr_personnel_operations"):
    main_bp.add_url_rule(
        "/hr-management/personnel-operations",
        endpoint="hr_personnel_operations",
        view_func=login_required(manager_required(menu_key_required("hr_leave_tracking")(_fallback_personnel_operations))),
    )


__all__ = [name for name in globals() if not name.startswith("__")]
