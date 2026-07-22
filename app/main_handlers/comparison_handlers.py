from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import PerformanceEvaluation, PerformancePeriod, PerformanceResultSnapshot, User
from app.route_registry import main_bp
from app.route_support import safe_render
from app.services.comparison_service import (
    build_change_summary as _build_change_summary,
)
from app.services.comparison_service import (
    compare_two_snapshots as _compare_two_snapshots,
)
from app.services.comparison_service import (
    comparison_band as _comparison_band,
)
from app.services.comparison_service import (
    safe_float as _safe_float,
)
from app.services.comparison_service import (
    snapshot_period_options_for_user as _snapshot_period_options_for_user,
)
from app.services.hierarchy_admin_service import get_manager_scope_users


def _display_name(user):
    if not user:
        return ""
    return (getattr(user, "full_name", "") or f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}").strip()


def _sortable_name(user):
    return (_display_name(user) or "").lower()


def _scope_employee_options(user):
    role = (getattr(user, "role", "") or "").strip().lower()
    if role in {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"}:
        scope_users = get_manager_scope_users(user) or []
        return [u for u in scope_users if getattr(u, "role", "") != "admin"]
    return [user] if getattr(user, "id", None) else []


def _comparison_data_user_ids(scope_users):
    scope_ids = [u.id for u in scope_users if getattr(u, "id", None)]
    if not scope_ids:
        return set()

    snapshot_ids = {
        row[0]
        for row in (
            db.session.query(PerformanceResultSnapshot.employee_id)
            .filter(
                PerformanceResultSnapshot.employee_id.in_(scope_ids),
                PerformanceResultSnapshot.is_current.is_(True),
            )
            .distinct()
            .all()
        )
    }
    published_eval_ids = {
        row[0]
        for row in (
            db.session.query(PerformanceEvaluation.employee_id)
            .filter(
                PerformanceEvaluation.employee_id.in_(scope_ids),
                PerformanceEvaluation.is_published_to_employee.is_(True),
            )
            .distinct()
            .all()
        )
    }
    return snapshot_ids | published_eval_ids


@main_bp.route("/performance/my-comparison", endpoint="my_performance_comparison")
@login_required
def my_performance_comparison():
    scope_employee_options = sorted(_scope_employee_options(current_user), key=_sortable_name)
    data_user_ids = _comparison_data_user_ids(scope_employee_options)
    employee_options = [u for u in scope_employee_options if getattr(u, "id", None) in data_user_ids]
    if not employee_options:
        employee_options = scope_employee_options[:80]
    employee_options_by_id = {u.id: u for u in employee_options if getattr(u, "id", None)}

    selected_employee_id = request.args.get("employee_id", type=int)
    if selected_employee_id not in employee_options_by_id:
        selected_employee_id = None

    selected_employee = employee_options_by_id.get(selected_employee_id)

    if not selected_employee:
        if getattr(current_user, "id", None) in employee_options_by_id and getattr(current_user, "id", None) in data_user_ids:
            selected_employee = employee_options_by_id[current_user.id]
        else:
            selected_employee = next((u for u in employee_options if u.id in data_user_ids), None)
        selected_employee_id = getattr(selected_employee, "id", None)

    if not selected_employee and getattr(current_user, "id", None):
        selected_employee = current_user
        selected_employee_id = current_user.id

    periods, snapshots_by_period, period_rows = _snapshot_period_options_for_user(selected_employee or current_user)
    available_period_ids = [getattr(period, "id", None) for period in periods if getattr(period, "id", None)]

    selected_current_period_id = request.args.get("current_period_id", type=int)
    if selected_current_period_id not in available_period_ids:
        selected_current_period_id = available_period_ids[0] if available_period_ids else None

    selected_previous_period_id = request.args.get("previous_period_id", type=int)
    if selected_previous_period_id not in available_period_ids or selected_previous_period_id == selected_current_period_id:
        selected_previous_period_id = None

    if not selected_previous_period_id and len(available_period_ids) > 1:
        selected_previous_period_id = next((pid for pid in available_period_ids if pid != selected_current_period_id), None)

    current_snapshot = snapshots_by_period.get(selected_current_period_id)
    previous_snapshot = snapshots_by_period.get(selected_previous_period_id) if selected_previous_period_id else None

    current_score = _safe_float(getattr(current_snapshot, "final_total_100", 0)) if current_snapshot else 0
    previous_score = _safe_float(getattr(previous_snapshot, "final_total_100", 0)) if previous_snapshot else 0
    diff = round(current_score - previous_score, 2)
    diff_pct = None
    if previous_snapshot and previous_score != 0:
        diff_pct = round((diff / previous_score) * 100, 2)

    criteria_rows = _compare_two_snapshots(previous_snapshot, current_snapshot)
    change_summary = _build_change_summary(criteria_rows)

    timeline = []
    for period, snapshot in reversed(period_rows):
        timeline.append(
            {
                "period_id": period.id,
                "title": period.title,
                "score": round(_safe_float(getattr(snapshot, "final_total_100", 0)), 2),
                "band": _comparison_band(getattr(snapshot, "final_total_100", 0)),
                "ranking_in_unit": getattr(snapshot, "ranking_in_unit", None),
                "ranking_in_scope": getattr(snapshot, "ranking_in_scope", None),
            }
        )

    return safe_render(
        "my_performance_comparison.html",
        "<h3>Personel Analizi</h3>",
        periods=periods,
        current_snapshot=current_snapshot,
        previous_snapshot=previous_snapshot,
        current_period_id=selected_current_period_id,
        previous_period_id=selected_previous_period_id,
        criteria_rows=criteria_rows,
        summary={
            "current_score": current_score,
            "previous_score": previous_score,
            "diff": diff,
            "diff_pct": diff_pct,
            "best": change_summary.get("best"),
            "worst": change_summary.get("worst"),
        },
        timeline=timeline,
        employee_options=employee_options,
        selected_employee_id=selected_employee_id,
        selected_employee=selected_employee,
        no_data_message=(
            "Seçilen personel için yayımlanmış sonuç bulunamadı."
            if selected_employee_id and not periods
            else "Bu kullanıcı için henüz yayımlanmış sonuç bulunmuyor."
        ),
    )


@main_bp.route("/performance/team-comparison-history", endpoint="team_performance_comparison_history")
@login_required
def team_performance_comparison_history():
    period_options = PerformancePeriod.query.order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc()).limit(24).all()
    scope_users = get_manager_scope_users(current_user)
    scope_user_ids = [u.id for u in scope_users]

    selected_employee_id = request.args.get("employee_id", type=int)
    period_a_id = request.args.get("period_a_id", type=int)
    period_b_id = request.args.get("period_b_id", type=int)
    selected_birim = (request.args.get("birim") or "").strip()

    employees = [u for u in scope_users if not selected_birim or (u.birim or "") == selected_birim]
    employees = sorted(employees, key=lambda x: ((_display_name(x))).lower())
    birimler = sorted({(u.birim or "").strip() for u in scope_users if (u.birim or "").strip()})

    selected_employee = None
    current_snapshot = None
    previous_snapshot = None
    criteria_rows = []
    comparison_summary = None
    roster_rows = []

    if selected_employee_id and selected_employee_id in scope_user_ids:
        selected_employee = db.session.get(User, selected_employee_id)

        employee_snaps = (
            PerformanceResultSnapshot.query
            .filter_by(employee_id=selected_employee_id, is_current=True)
            .order_by(PerformanceResultSnapshot.published_at.desc(), PerformanceResultSnapshot.id.desc())
            .all()
        )
        snaps_by_period = {s.period_id: s for s in employee_snaps}

        if not period_a_id and employee_snaps:
            period_a_id = employee_snaps[0].period_id
        if not period_b_id and len(employee_snaps) > 1:
            period_b_id = employee_snaps[1].period_id

        current_snapshot = snaps_by_period.get(period_a_id)
        previous_snapshot = snaps_by_period.get(period_b_id) if period_b_id else None

        criteria_rows = _compare_two_snapshots(previous_snapshot, current_snapshot)
        current_score = _safe_float(getattr(current_snapshot, "final_total_100", 0)) if current_snapshot else 0
        previous_score = _safe_float(getattr(previous_snapshot, "final_total_100", 0)) if previous_snapshot else 0
        diff = round(current_score - previous_score, 2)

        change_summary = _build_change_summary(criteria_rows)
        comparison_summary = {
            "current_score": current_score,
            "previous_score": previous_score,
            "diff": diff,
            "best": change_summary.get("best"),
            "worst": change_summary.get("worst"),
        }

    if period_a_id and period_b_id and scope_user_ids:
        current_rows = (
            PerformanceResultSnapshot.query
            .filter(
                PerformanceResultSnapshot.period_id == period_a_id,
                PerformanceResultSnapshot.employee_id.in_(scope_user_ids),
                PerformanceResultSnapshot.is_current.is_(True),
            )
            .all()
        )
        previous_rows = (
            PerformanceResultSnapshot.query
            .filter(
                PerformanceResultSnapshot.period_id == period_b_id,
                PerformanceResultSnapshot.employee_id.in_(scope_user_ids),
                PerformanceResultSnapshot.is_current.is_(True),
            )
            .all()
        )
        prev_map = {r.employee_id: r for r in previous_rows}

        for row in current_rows:
            if selected_birim and (row.birim_snapshot or "") != selected_birim:
                continue
            prev = prev_map.get(row.employee_id)
            current_score = round(_safe_float(row.final_total_100), 2)
            previous_score = round(_safe_float(prev.final_total_100), 2) if prev else 0
            diff = round(current_score - previous_score, 2)
            roster_rows.append(
                {
                    "employee_id": row.employee_id,
                    "employee_name": row.employee_name_snapshot,
                    "sicil_no": row.sicil_no_snapshot,
                    "birim": row.birim_snapshot,
                    "current_score": current_score,
                    "previous_score": previous_score,
                    "diff": diff,
                    "band": _comparison_band(current_score),
                }
            )

        roster_rows.sort(key=lambda x: (-(x["diff"]), -(x["current_score"]), (x["employee_name"] or "").lower()))

    return safe_render(
        "team_performance_comparison_history.html",
        "<h3>Personel Dönem Analizi</h3>",
        period_options=period_options,
        employees=employees,
        birimler=birimler,
        selected_employee_id=selected_employee_id,
        selected_employee=selected_employee,
        period_a_id=period_a_id,
        period_b_id=period_b_id,
        selected_birim=selected_birim,
        current_snapshot=current_snapshot,
        previous_snapshot=previous_snapshot,
        criteria_rows=criteria_rows,
        comparison_summary=comparison_summary,
        roster_rows=roster_rows,
    )
