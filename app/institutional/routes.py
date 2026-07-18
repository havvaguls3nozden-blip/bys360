
"""BYS360 canlı çekirdek kurumsal/personel route ailesi.

Faz A: Büyük dosya bölme refactoru. Bu dosya ana HR yönetim ekranını
ve alt route modüllerinin geriye dönük import uyumluluğunu korur.
"""
from __future__ import annotations

from app.institutional.hr_common import PerformanceEvaluation
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
    _model_ready,
    _safe_text,
    _safe_int,
    _safe_float,
    _current_user_id,
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

@main_bp.route("/hr-management")
@login_required
@manager_required
@menu_key_required("hr_management")
def hr_management():
    today = date.today()
    hr_scope, scope_users, scope_user_ids = _scope_bundle()
    selected_scope_mode = hr_scope.get("scope_mode") or "personal"
    active_period = _active_period()
    health = _delegation_health(getattr(active_period, "id", None))

    leave_today_count = 0
    attendance_today_count = 0
    pending_leave_count = 0
    pending_attendance_count = 0
    active_delegation_count = 0
    expiring_delegation_count = 0
    recent_delegations: list[Any] = []
    expiring_delegations: list[Any] = []

    if _model_ready(PersonnelLeave) and scope_user_ids:
        try:
            leave_today_count = PersonnelLeave.query.filter(PersonnelLeave.user_id.in_(scope_user_ids), PersonnelLeave.start_date <= today, PersonnelLeave.end_date >= today).count()
            pending_leave_count = PersonnelLeave.query.filter(PersonnelLeave.user_id.in_(scope_user_ids), PersonnelLeave.status.in_(["bekliyor", "taslak"])).count()
        except Exception:
            safe_db_rollback()
    if _model_ready(AttendanceException) and scope_user_ids:
        try:
            attendance_today_count = AttendanceException.query.filter(AttendanceException.user_id.in_(scope_user_ids), AttendanceException.record_date == today).count()
            pending_attendance_count = AttendanceException.query.filter(AttendanceException.user_id.in_(scope_user_ids), AttendanceException.status.in_(["bekliyor", "taslak"])).count()
        except Exception:
            safe_db_rollback()
    if _model_ready(DelegationAssignment):
        try:
            q = DelegationAssignment.query.filter(DelegationAssignment.start_date <= today, DelegationAssignment.end_date >= today, DelegationAssignment.status.in_(["aktif", "onaylandi"]))
            if scope_user_ids:
                q = q.filter(or_(DelegationAssignment.delegator_user_id.in_(scope_user_ids), DelegationAssignment.delegate_user_id.in_(scope_user_ids)))
            active_delegation_count = q.count()
            recent_delegations = q.order_by(DelegationAssignment.start_date.desc(), DelegationAssignment.id.desc()).limit(10).all()
            expiring_delegations = q.filter(DelegationAssignment.end_date <= today + timedelta(days=7)).order_by(DelegationAssignment.end_date.asc(), DelegationAssignment.id.desc()).limit(10).all()
            expiring_delegation_count = len(expiring_delegations)
        except Exception:
            safe_db_rollback()

    profile_scores = [_profile_score(user) for user in scope_users]
    completion_avg = int(round(sum(profile_scores) / len(profile_scores))) if profile_scores else 0
    incomplete_profile_count = sum(1 for user in scope_users if _profile_missing_fields(user))

    high_potential_count = 0
    development_watch_count = 0
    if _model_ready(PerformanceEvaluation) and scope_user_ids:
        try:
            perf_rows = PerformanceEvaluation.query.filter(PerformanceEvaluation.employee_id.in_(scope_user_ids)).order_by(PerformanceEvaluation.period_id.desc(), PerformanceEvaluation.id.desc()).all()
            seen: set[int] = set()
            for row in perf_rows:
                eid = int(getattr(row, "employee_id", 0) or 0)
                if not eid or eid in seen:
                    continue
                seen.add(eid)
                score = float(getattr(row, "final_total_100", 0) or 0)
                if score >= 90:
                    high_potential_count += 1
                elif score and score < 70:
                    development_watch_count += 1
        except Exception:
            safe_db_rollback()

    balance_risk_count = 0
    if _model_ready(LeaveBalance) and scope_user_ids:
        try:
            for row in LeaveBalance.query.filter(LeaveBalance.user_id.in_(scope_user_ids)).all():
                remaining = float(getattr(row, "remaining_days", 0) or 0)
                if remaining <= 3:
                    balance_risk_count += 1
        except Exception:
            safe_db_rollback()

    uncovered_count = int((health.get("coverage_summary") or {}).get("uncovered") or 0)

    module_cards = [
        {"title": "Personel özlük dosyaları", "text": "Belge, süreç notu, pozisyon geçmişi ve profil tamlığı.", "icon": "fa-folder-open", "href": _url_or_hash("main.hr_personnel_operations", scope=selected_scope_mode)},
        {"title": "Birim ve pozisyon yönetimi", "text": "Organizasyon birimleri, üst-alt ilişkiler ve yönetici bağlantıları.", "icon": "fa-sitemap", "href": _url_or_hash("main.admin_org_units")},
        {"title": "İzin ve devamsızlık", "text": "İzin, rapor, devamsızlık ve değerlendirme etkisi.", "icon": "fa-calendar-check", "href": _url_or_hash("main.hr_leave_management", scope=selected_scope_mode)},
        {"title": "Devamsızlık ve vekâlet", "text": "Amir yokluğu, vekâlet ve açık görev izleme.", "icon": "fa-people-arrows-left-right", "href": _url_or_hash("main.hr_attendance_management", scope=selected_scope_mode)},
        {"title": "Personel raporları", "text": "İzin, devamsızlık, vekâlet ve kapsam özetleri.", "icon": "fa-chart-column", "href": _url_or_hash("main.hr_reports", scope=selected_scope_mode)},
    ]

    action_rows = []
    if incomplete_profile_count:
        action_rows.append({"title": "Eksik özlük alanları", "detail": "Birim, unvan, sicil veya amir bilgisi eksik personel kayıtları tamamlanmalı.", "count": incomplete_profile_count, "tone": "critical", "href": _url_or_hash("main.hr_personnel_operations", scope=selected_scope_mode)})
    if pending_leave_count:
        action_rows.append({"title": "Bekleyen izin kayıtları", "detail": "Bekleyen izin/rapor kayıtları değerlendirme zincirini etkilemeden kapatılmalı.", "count": pending_leave_count, "tone": "watch", "href": _url_or_hash("main.hr_leave_management", scope=selected_scope_mode)})
    if uncovered_count:
        action_rows.append({"title": "Vekâletsiz açık görev uyarısı", "detail": "İzinli amir nedeniyle boşa düşen değerlendirme görevleri kontrol edilmeli.", "count": uncovered_count, "tone": "critical", "href": _url_or_hash("main.hr_attendance_management", scope=selected_scope_mode)})
    if not action_rows:
        action_rows.append({"title": "Çekirdek personel omurgası dengede", "detail": "Bu kapsamda acil işlem gerektiren kayıt görünmüyor.", "count": 0, "tone": "ok", "href": ""})

    return safe_render(
        "hr_management.html",
        active_period=active_period,
        leave_today_count=leave_today_count,
        attendance_today_count=attendance_today_count,
        active_delegation_count=active_delegation_count,
        uncovered_count=uncovered_count,
        pending_leave_count=pending_leave_count,
        pending_attendance_count=pending_attendance_count,
        incomplete_profile_count=incomplete_profile_count,
        balance_risk_count=balance_risk_count,
        high_potential_count=high_potential_count,
        development_watch_count=development_watch_count,
        completion_avg=completion_avg,
        expiring_delegation_count=expiring_delegation_count,
        recent_delegations=recent_delegations,
        expiring_delegations=expiring_delegations,
        scope_label=_scope_label,
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        module_cards=module_cards,
        action_rows=action_rows,
        unit_pulse_rows=_unit_pulse(scope_users, scope_user_ids),
    )

# Alt HR route ailelerini yükle ve eski app.institutional.routes import uyumluluğunu koru.
def _reexport_module(module, names):
    for name in names:
        globals()[name] = getattr(module, name)


_org_unit_routes = import_module("app.institutional.org_unit_routes")
_reexport_module(_org_unit_routes, [
    "LEGACY_SHIM",
    "LEGACY_RUNTIME_STATUS",
    "LEGACY_ROUTE_FAMILY",
    "LEGACY_NOTE",
    "admin_org_units",
    "admin_org_unit_create",
    "admin_org_unit_edit",
    "admin_org_unit_toggle_active",
    "org_units_list",
    "org_unit_add",
    "org_unit_edit",
    "org_unit_delete",
    "admin_org_unit_delete",
])
_hr_personnel_operations_routes = import_module("app.institutional.hr_personnel_operations_routes")
_reexport_module(_hr_personnel_operations_routes, [
    "login_required",
    "main_bp",
    "manager_required",
    "menu_key_required",
    "safe_db_rollback",
    "safe_render",
    "timedelta",
])
_hr_leave_attendance_routes = import_module(
    "app.institutional.hr_leave_attendance_routes"
)
from app.institutional.hr_leave_attendance_routes import (
    import_module,
    login_required,
    main_bp,
    manager_required,
    menu_key_required,
    _leave_page_context,
    hr_leave_management,
    _attendance_page_context,
    hr_attendance_management,
    hr_leave_ai_report_export,
    hr_attendance_ai_report_export,
    _set_status,
    _delete_row,
    hr_leave_update_status,
    hr_leave_delete,
    hr_attendance_update_status,
    hr_attendance_delete,
    hr_delegation_update_status,
    hr_delegation_delete,
)
_reexport_module(
    _hr_leave_attendance_routes,
    (
        "utc_now",
        "date",
        "datetime",
        "timedelta",
        "SimpleNamespace",
        "Any",
        "Iterable",
        "csv",
        "io",
        "Response",
        "current_app",
        "flash",
        "jsonify",
        "redirect",
        "request",
        "url_for",
    ),
)
_reexport_module(
    _hr_leave_attendance_routes,
    (
        "current_user",
        "inspect",
        "or_",
        "BuildError",
        "db",
        "consume_form_token",
        "issue_form_token",
        "safe_db_rollback",
        "safe_render",
        "LEGACY_SHIM",
        "LEGACY_RUNTIME_STATUS",
        "LEGACY_ROUTE_FAMILY",
        "LEGACY_NOTE",
        "LEAVE_TYPE_CHOICES",
        "LEAVE_STATUS_CHOICES",
        "ATTENDANCE_TYPE_CHOICES",
    ),
)
_reexport_module(
    _hr_leave_attendance_routes,
    (
        "DELEGATION_SCOPE_CHOICES",
        "DELEGATION_STATUS_CHOICES",
        "PERFORMANCE_MODE_LABELS",
        "ACTIVE_STATUSES",
        "PENDING_STATUSES",
        "_safe_import",
        "_endpoint_registered",
        "_url_or_hash",
        "_table_exists",
        "_model_ready",
        "_safe_text",
        "_safe_int",
        "_safe_float",
        "_current_user_id",
        "_safe_commit",
    ),
)
_reexport_module(
    _hr_leave_attendance_routes,
    (
        "_resolve_period_id_from_form",
        "_date_range_weekday_count",
        "_calculate_leave_day_count",
        "_active_delegation_exists",
        "_leave_overlaps",
        "_attendance_overlaps",
        "_bool_from_form",
        "_active_period",
        "_parse_date",
        "AttendanceException",
        "DelegationAssignment",
        "LeaveBalance",
        "PersonnelLeave",
        "_create_delegation_from_form",
        "_handle_leave_post",
    ),
)
_reexport_module(
    _hr_leave_attendance_routes,
    (
        "_handle_leave_balance_post",
        "_handle_attendance_post",
        "_handle_manual_delegation_post",
        "_status_label",
        "_scope_label",
        "_leave_type_label",
        "_attendance_type_label",
        "_performance_mode_label",
        "_full_name",
        "_unit_name",
        "_role_key",
        "_profile_missing_fields",
        "_profile_score",
        "_period_options",
        "_selected_period_id",
    ),
)
_reexport_module(
    _hr_leave_attendance_routes,
    (
        "_selected_user_id",
        "_all_personnel",
        "_requested_scope_mode",
        "_fallback_scope_context",
        "_hr_scope_context",
        "_scope_user_ids",
        "_filter_users_in_scope",
        "_scope_bundle",
        "_empty_overview",
        "_leave_overview",
        "_delegation_health",
        "_query_rows",
        "_count_rows",
        "_selected_user_guard",
        "_unit_pulse",
    ),
)
_hr_reports_routes = import_module(
    "app.institutional.hr_reports_routes"
)
from app.institutional.hr_reports_routes import (
    login_required,
    main_bp,
    manager_required,
    menu_key_required,
    import_module,
    _reports_context,
    _stats_by,
    _security_runtime,
    hr_reports,
    hr_reports_print,
    _export_simple_report,
    hr_reports_export,
    hr_reports_readiness,
    hr_reports_pilot_acceptance,
    hr_reports_smoke_check,
    hr_reports_go_live_approval,
    _fallback_personnel_operations,
LOADED_CHILD_ROUTE_MODULES,
)
_reexport_module(
    _hr_reports_routes,
    (
        "Any",
        "Response",
        "csv",
        "current_app",
        "flash",
        "io",
        "jsonify",
        "or_",
        "redirect",
        "request",
        "safe_db_rollback",
        "safe_render",
        "AttendanceException",
        "DelegationAssignment",
        "LeaveBalance",
        "PersonnelLeave",
    ),
)
_reexport_module(
    _hr_reports_routes,
    (
        "_active_delegation_exists",
        "_attendance_overlaps",
        "_bool_from_form",
        "_calculate_leave_day_count",
        "_current_user_id",
        "_leave_overlaps",
        "_model_ready",
        "_parse_date",
        "_resolve_period_id_from_form",
        "_safe_commit",
        "_safe_float",
        "_safe_int",
        "_safe_text",
        "consume_form_token",
        "date",
        "db",
    ),
)
_reexport_module(
    _hr_reports_routes,
    (
        "url_for",
        "utc_now",
        "_create_delegation_from_form",
        "_handle_leave_post",
        "_handle_leave_balance_post",
        "_handle_attendance_post",
        "_handle_manual_delegation_post",
        "datetime",
        "timedelta",
        "SimpleNamespace",
        "Iterable",
        "current_user",
        "inspect",
        "BuildError",
        "issue_form_token",
        "LEGACY_SHIM",
    ),
)
_reexport_module(
    _hr_reports_routes,
    (
        "LEGACY_RUNTIME_STATUS",
        "LEGACY_ROUTE_FAMILY",
        "LEGACY_NOTE",
        "LEAVE_TYPE_CHOICES",
        "LEAVE_STATUS_CHOICES",
        "ATTENDANCE_TYPE_CHOICES",
        "DELEGATION_SCOPE_CHOICES",
        "DELEGATION_STATUS_CHOICES",
        "PERFORMANCE_MODE_LABELS",
        "ACTIVE_STATUSES",
        "PENDING_STATUSES",
        "_safe_import",
        "_endpoint_registered",
        "_url_or_hash",
        "_table_exists",
        "_date_range_weekday_count",
    ),
)
_reexport_module(
    _hr_reports_routes,
    (
        "_active_period",
        "_status_label",
        "_scope_label",
        "_leave_type_label",
        "_attendance_type_label",
        "_performance_mode_label",
        "_full_name",
        "_unit_name",
        "_role_key",
        "_profile_missing_fields",
        "_profile_score",
        "_period_options",
        "_selected_period_id",
        "_selected_user_id",
        "_all_personnel",
        "_requested_scope_mode",
    ),
)
_reexport_module(
    _hr_reports_routes,
    (
        "_fallback_scope_context",
        "_hr_scope_context",
        "_scope_user_ids",
        "_filter_users_in_scope",
        "_scope_bundle",
        "_empty_overview",
        "_leave_overview",
        "_delegation_health",
        "_query_rows",
        "_count_rows",
        "_selected_user_guard",
        "_unit_pulse",
    ),
)


del _org_unit_routes, _hr_personnel_operations_routes, _hr_leave_attendance_routes, _hr_reports_routes, _reexport_module

__all__ = [name for name in globals() if not name.startswith("__")]
