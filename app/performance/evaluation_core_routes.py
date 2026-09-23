from __future__ import annotations

import logging
from typing import Any, cast

from flask import (
    current_app,
    flash,
    redirect,
    render_template as flask_render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import (
    EvaluationAssignment,
    PerformanceEvaluation,
    PerformancePeriod,
)
from app.route_registry import main_bp
from app.route_support import (
    admin_required,
    manager_required,
    render_access_denied,
    safe_render,
    user_has_any_role,
)
from app.services.availability_service import refresh_assignment_live_coverages
from app.services.feedback_service import can_create_feedback_request, get_open_feedback_request
from app.services.performance.evaluation_ui_service import (
    build_employee_cards as _build_employee_cards,
    build_scorecard_detail_context as _build_scorecard_detail_context,
    can_access_assignment_for_actor as _can_access_assignment_for_actor,
)
from app.services.performance.hardening_service import (
    build_period_download_name,
    humanize_export_exception,
)
from app.services.performance.history import (
    build_history_summary,
    get_evaluation_history,
    humanize_workflow_status,
)
from app.services.performance.interim_notes_runtime import build_scorecard_interim_notes
from app.services.performance.meeting_p4_development_guidance import (
    build_scorecard_development_guidance_context,
)
from app.services.performance.phase3_backend_route_guard import (
    phase3_enforce_evaluation_access,  # BYS360_PHASE3_3_BACKEND_ROUTE_IMPORT
)
from app.services.performance.team_compare_service import (
    STATUS_OPTIONS as TEAM_COMPARE_STATUS_OPTIONS,
    apply_filters as apply_team_compare_filters,
    build_empty_payload as build_team_compare_empty_payload,
    build_excel_workbook as build_team_compare_workbook,
    build_rows as build_team_compare_rows,
    build_view_payload as build_team_compare_view_payload,
    choose_period_id as choose_team_compare_period_id,
)
from app.services.performance_v2.chain import build_resolved_chain
from app.services.performance_v2.scoring import compute_final_score
from app.services.performance_v2.weights import resolve_weight_plan
from app.services.publish_service import get_evaluation_visibility_state
from app.services.query_health_service import (
    apply_assignment_board_filters,
    attach_workflow_meta,
    build_assignment_board_query,
    build_workflow_filter_items,
    ordered_assignment_rows,
)
from app.view_helpers import build_surface_scope_context

logger = logging.getLogger(__name__)
"""Performans degerlendirme cekirdek route'lari.

Personel – , mesai dışı saat:25.
Burasi projenin kalbi gibi. Fazla oyuncakli bir soyutlama yapmak istemedim;
insan acinca akisi gorebilsin istedim. Ama ana routes.py de artik bogulmasin diye
kriterden sonraki agir akisi buraya aldim.
"""

# Bir ara bunu daha da parcali yapayim dedim ama decorator zinciri dagilinca keyfim kacti.
# Simdilik en dogru orta yol bu gibi duruyor.


"""Faz C: değerlendirme görünürlük ve kart yardımcıları service katmanına taşındı."""

@main_bp.route("/performance/scorecard")
@login_required
def performance_scorecard():
    return redirect(url_for("main.performance_v2_phase5_scorecard", **cast("dict[str, Any]", request.args.to_dict(flat=True))))

@main_bp.route("/performance/scorecard/<int:evaluation_id>")
@login_required
def performance_scorecard_detail(evaluation_id):
    evaluation = PerformanceEvaluation.query.get_or_404(evaluation_id)

    phase3_access_denied = phase3_enforce_evaluation_access(current_user, evaluation)  # BYS360_PHASE3_3_SCORECARD_DETAIL_BACKEND_GUARD
    if phase3_access_denied is not None:
        return phase3_access_denied
    detail_ctx = _build_scorecard_detail_context(
        evaluation=evaluation,
        actor=current_user,
        selected_scope=request.args.get("scope"),
        selected_period_id=request.args.get("period_id", type=int),
    )
    scope_ctx = detail_ctx["scope_ctx"]
    visibility = detail_ctx["visibility"]
    redirect_params = detail_ctx["redirect_params"]

    if not visibility.get("can_view"):
        if evaluation.employee_id != current_user.id:
            return render_access_denied()  # BYS360_PHASE3_SCORECARD_BACKEND_ACCESS_DENIED
        flash(visibility.get("reason") or "Bu karne henüz görüntülenebilir durumda değil.", "warning")
        return redirect(url_for("main.performance_scorecard", **redirect_params))

    if evaluation.employee_id == current_user.id and visibility.get("employee_visible") and not getattr(evaluation, "employee_score_viewed_at", None):
        evaluation.employee_score_viewed_at = utc_now()
        db.session.commit()

    detail_row = detail_ctx["detail_row"]
    open_feedback_request = get_open_feedback_request(evaluation.period_id, evaluation.employee_id)
    can_request_feedback, feedback_block_reason = can_create_feedback_request(evaluation.period, evaluation)

    return flask_render_template(
        "performance_scorecard_detail.html",
        evaluation=evaluation,
        row=detail_row,
        employee=evaluation.employee,
        period=evaluation.period,
        visibility_state=visibility,
        selected_scope=scope_ctx.get("selected_scope"),
        scope_label=scope_ctx.get("scope_label"),
        scope_role_title=scope_ctx.get("role_title"),
        open_feedback_request=open_feedback_request,
        can_request_feedback=bool(can_request_feedback and evaluation.employee_id == current_user.id),
        feedback_block_reason=feedback_block_reason,
        interim_notes_context=build_scorecard_interim_notes(evaluation=evaluation, viewer=current_user),  # BYS360_INTERIM_NOTES_SCORECARD_CONTEXT_BINDING
        development_guidance_context=build_scorecard_development_guidance_context(evaluation=evaluation, viewer=current_user),  # BYS360_PHASE10_SCORECARD_DEVELOPMENT_CONTEXT
    )


@main_bp.route("/performance/scorecard/<int:evaluation_id>/acknowledge", methods=["POST"])
@login_required
def performance_scorecard_acknowledge(evaluation_id):
    evaluation = PerformanceEvaluation.query.get_or_404(evaluation_id)
    detail_ctx = _build_scorecard_detail_context(
        evaluation=evaluation,
        actor=current_user,
        selected_scope=request.args.get("scope"),
        selected_period_id=request.args.get("period_id", type=int),
    )
    detail_ctx["scope_ctx"]
    visibility = detail_ctx["visibility"]
    redirect_params = detail_ctx["redirect_params"]
    if evaluation.employee_id != current_user.id:
        flash("Yalnızca kendi not karnenizi onaylayabilirsiniz.", "danger")
        return redirect(url_for("main.performance_scorecard_detail", evaluation_id=evaluation.id, **redirect_params))
    if not visibility.get("employee_visible"):
        flash("Bu karne henüz personele açılmadığı için onaylanamaz.", "warning")
        return redirect(url_for("main.performance_scorecard_detail", evaluation_id=evaluation.id, **redirect_params))

    note = (request.form.get("ack_note") or "").strip()
    if not getattr(evaluation, "employee_score_viewed_at", None):
        evaluation.employee_score_viewed_at = utc_now()
    evaluation.employee_score_acknowledged_at = utc_now()
    evaluation.employee_score_acknowledged_note = note or None
    db.session.commit()
    flash("Not karnenizi gördüğünüz bilgisi amirlerinize işlendi.", "success")
    return redirect(url_for("main.performance_scorecard_detail", evaluation_id=evaluation.id, **redirect_params))


@main_bp.route("/performance/scorecard/<int:evaluation_id>/pdf")
@login_required
def performance_scorecard_pdf(evaluation_id):
    evaluation = PerformanceEvaluation.query.get_or_404(evaluation_id)

    phase3_access_denied = phase3_enforce_evaluation_access(current_user, evaluation)  # BYS360_PHASE3_3_SCORECARD_PDF_BACKEND_GUARD
    if phase3_access_denied is not None:
        return phase3_access_denied
    detail_ctx = _build_scorecard_detail_context(
        evaluation=evaluation,
        actor=current_user,
        selected_scope=request.args.get("scope"),
        selected_period_id=request.args.get("period_id", type=int),
    )
    detail_ctx["scope_ctx"]
    visibility = detail_ctx["visibility"]
    redirect_params = detail_ctx["redirect_params"]

    if not visibility.get("can_view"):
        if evaluation.employee_id != current_user.id:
            return render_access_denied()  # BYS360_PHASE3_SCORECARD_BACKEND_ACCESS_DENIED
        flash(visibility.get("reason") or "Bu karne henüz görüntülenebilir durumda değil.", "warning")
        return redirect(url_for("main.performance_scorecard", **redirect_params))

    detail_row = detail_ctx["detail_row"]

    return flask_render_template(
        "scorecard_pdf.html",
        evaluation=evaluation,
        row=detail_row,
        employee=evaluation.employee,
        period=evaluation.period,
        visibility_state=visibility,
        interim_notes_context=build_scorecard_interim_notes(evaluation=evaluation, viewer=current_user),  # BYS360_INTERIM_NOTES_SCORECARD_PDF_CONTEXT_BINDING
        development_guidance_context=build_scorecard_development_guidance_context(evaluation=evaluation, viewer=current_user),  # BYS360_PHASE10_SCORECARD_DEVELOPMENT_PDF_CONTEXT
    )

@main_bp.route("/performance/team-compare")
@main_bp.route("/performance/personel-analizi")
@main_bp.route("/performance/personnel-analysis")
@main_bp.route("/performance/team-comparison")
@login_required
@manager_required
def performance_team_compare():
    selected_period_id = request.args.get("period_id", type=int)
    selected_birim = (request.args.get("birim") or "").strip()
    selected_status = (request.args.get("durum") or "").strip()
    selected_quick = (request.args.get("quick") or "").strip()
    q = (request.args.get("q") or "").strip()
    scope_ctx = build_surface_scope_context(current_user, request.args.get("scope"))
    selected_scope = scope_ctx["selected_scope"]

    periods = (
        PerformancePeriod.query
        .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
        .all()
    )

    empty_payload = build_team_compare_empty_payload(
        periods=periods,
        selected_period_id=selected_period_id,
        selected_scope=selected_scope,
        scope_ctx=scope_ctx,
        selected_birim=selected_birim,
        selected_status=selected_status,
        selected_quick=selected_quick,
        q=q,
    )

    if not periods:
        return safe_render("team_compare.html", "<h3>Personel Analizi</h3>", **empty_payload)

    active_period = PerformancePeriod.query.filter_by(is_active=True).first()
    selected_period_id = choose_team_compare_period_id(periods, selected_period_id, active_period)
    empty_payload["selected_period_id"] = selected_period_id

    scope_employee_ids = list(scope_ctx.get("employee_ids") or [])
    if selected_scope == "mine" and getattr(current_user, "id", None):
        scope_employee_ids = [current_user.id]

    evaluations = []
    if scope_employee_ids:
        evaluations = (
            PerformanceEvaluation.query
            .filter(
                PerformanceEvaluation.period_id == selected_period_id,
                PerformanceEvaluation.employee_id.in_(scope_employee_ids),
            )
            .order_by(PerformanceEvaluation.id.desc())
            .all()
        )

    def _visible_score(evaluation):
        if bool(getattr(evaluation, "level_1_completed", False)):
            try:
                resolved_chain = build_resolved_chain(employee=evaluation.employee, period=evaluation.period)
                weight_plan = resolve_weight_plan(employee=evaluation.employee, period=evaluation.period, resolved_chain=resolved_chain)
                return float(compute_final_score(
                    level_scores={
                        1: float(getattr(evaluation, "level_1_total_100", 0) or 0),
                        2: float(getattr(evaluation, "level_2_total_100", 0) or 0),
                        3: float(getattr(evaluation, "level_3_total_100", 0) or 0),
                    },
                    weights=weight_plan.level_weights,
                ) or 0)
            except Exception:
                logger.exception("Performans modulu kritik isleminde hata olustu", exc_info=True)
                return float(getattr(evaluation, "final_total_100", 0) or 0)
        if bool(getattr(evaluation, "level_2_completed", False)):
            return float(getattr(evaluation, "level_2_total_100", 0) or 0)
        if bool(getattr(evaluation, "level_3_completed", False)):
            return float(getattr(evaluation, "level_3_total_100", 0) or 0)
        return float(
            getattr(evaluation, "level_2_total_100", 0)
            or getattr(evaluation, "level_3_total_100", 0)
            or getattr(evaluation, "level_1_total_100", 0)
            or 0
        )

    rows = build_team_compare_rows(
        evaluations,
        visible_score_fn=_visible_score,
        status_options=list(TEAM_COMPARE_STATUS_OPTIONS),
        visibility_resolver=lambda evaluation: get_evaluation_visibility_state(
            evaluation,
            current_user,
            allowed_employee_ids=scope_employee_ids,
        ),
    )
    rows = apply_team_compare_filters(
        rows,
        selected_birim=selected_birim,
        selected_status=selected_status,
        selected_quick=selected_quick,
        q=q,
    )

    if (request.args.get("export") or "").lower() == "xlsx":
        try:
            output = build_team_compare_workbook(rows)
            selected_period = db.session.get(PerformancePeriod, selected_period_id) if selected_period_id else None
            return send_file(
                output,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name=build_period_download_name("personel_analizi", selected_period, "xlsx"),
            )
        except Exception as exc:
            current_app.logger.exception("Personel analizi export hatası: %s", exc)
            flash(f"Personel analizi dışa aktarma sırasında hata oluştu: {humanize_export_exception(exc)}", "danger")
            redirect_args: dict[str, Any] = request.args.to_dict(flat=True)
            redirect_args.pop("export", None)
            return redirect(url_for("main.performance_team_compare", **redirect_args))

    payload = build_team_compare_view_payload(
        rows=rows,
        periods=periods,
        selected_period_id=selected_period_id,
        selected_scope=selected_scope,
        scope_ctx=scope_ctx,
        selected_birim=selected_birim,
        selected_status=selected_status,
        selected_quick=selected_quick,
        q=q,
    )
    return safe_render("team_compare.html", "<h3>Personel Analizi</h3>", **payload)

@main_bp.route("/performance/tasks", endpoint="performance_tasks")
@main_bp.route("/performance/assignments")
@login_required
def performance_tasks():
    return redirect(url_for("main.performance_v2_phase3_dashboard", **cast("dict[str, Any]", request.args.to_dict(flat=True))))
@main_bp.route("/performance/evaluation-tasks", endpoint="performance_evaluation_tasks")
@login_required
@admin_required
def performance_evaluation_tasks():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    selected_unit = (request.args.get("unit") or "").strip()
    workflow_status = (request.args.get("workflow") or "").strip()

    total_assignments = ordered_assignment_rows(build_assignment_board_query(admin_mode=True))
    attach_workflow_meta(total_assignments)

    unit_options = sorted({
        (assignment.employee.birim or "").strip()
        for assignment in total_assignments
        if assignment.employee and (assignment.employee.birim or "").strip()
    })
    pending_count = sum(1 for assignment in total_assignments if assignment.status == "bekliyor")
    partial_count = sum(1 for assignment in total_assignments if assignment.status == "kismen_tamamlandi")
    completed_count = sum(1 for assignment in total_assignments if assignment.status == "tamamlandi")

    unit_scope_query, _, _ = apply_assignment_board_filters(build_assignment_board_query(admin_mode=True), unit=selected_unit)
    unit_scope_assignments = ordered_assignment_rows(unit_scope_query)
    attach_workflow_meta(unit_scope_assignments)
    unit_total_count = len(unit_scope_assignments)
    unit_pending_count = sum(1 for assignment in unit_scope_assignments if assignment.status == "bekliyor")
    unit_partial_count = sum(1 for assignment in unit_scope_assignments if assignment.status == "kismen_tamamlandi")
    unit_completed_count = sum(1 for assignment in unit_scope_assignments if assignment.status == "tamamlandi")

    filtered_query, status, workflow_status = apply_assignment_board_filters(
        build_assignment_board_query(admin_mode=True),
        q=q,
        status=status,
        unit=selected_unit,
        workflow_status=workflow_status,
    )
    assignments = ordered_assignment_rows(filtered_query)
    attach_workflow_meta(assignments)
    workflow_items = build_workflow_filter_items(assignments, workflow_status)
    employee_cards = _build_employee_cards(assignments, include_coverage=False)

    return safe_render(
        "evaluation_tasks.html",
        "<h3>Değerlendirme Görevleri</h3>",
        employee_cards=employee_cards,
        assignments=assignments,
        total_count=len(total_assignments),
        pending_count=pending_count,
        partial_count=partial_count,
        completed_count=completed_count,
        filtered_count=len(assignments),
        q=q,
        selected_status=status,
        selected_workflow=workflow_status,
        workflow_items=workflow_items,
        unit_options=unit_options,
        selected_unit=selected_unit,
        unit_total_count=unit_total_count,
        unit_pending_count=unit_pending_count,
        unit_partial_count=unit_partial_count,
        unit_completed_count=unit_completed_count,
        employee_card_count=len(employee_cards),
    )

@main_bp.route("/performance/evaluations/<int:evaluation_id>/history", endpoint="performance_evaluation_history")
@login_required
def performance_evaluation_history(evaluation_id):
    evaluation = PerformanceEvaluation.query.get_or_404(evaluation_id)
    assignment = EvaluationAssignment.query.filter_by(
        period_id=evaluation.period_id,
        employee_id=evaluation.employee_id,
        evaluator_id=current_user.id,
    ).order_by(EvaluationAssignment.manager_level.asc()).first()
    history_allowed = bool(assignment)
    if not history_allowed:
        privileged_scope = build_surface_scope_context(current_user, None)
        privileged_roles = {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"}
        if user_has_any_role(current_user, privileged_roles):
            history_allowed = evaluation.employee_id in set(privileged_scope.get("employee_ids") or [])
    if not history_allowed and not getattr(current_user, "is_admin", False) and not user_has_any_role(current_user, {"admin"}):
        flash("Bu süreç geçmişini görüntüleme yetkiniz yok.", "warning")
        return redirect(url_for("main.performance_tasks"))

    rows = get_evaluation_history(evaluation_id)
    history_summary = build_history_summary(rows)
    return flask_render_template(
        "performance_evaluation_history.html",
        evaluation=evaluation,
        employee=evaluation.employee,
        period=evaluation.period,
        history_rows=rows,
        history_summary=history_summary,
        workflow_status_label=humanize_workflow_status(evaluation.workflow_status),
        back_url=request.referrer or url_for("main.performance_tasks"),
    )

@main_bp.route("/performance/evaluate/<int:assignment_id>", methods=["GET", "POST"])
@login_required
def performance_evaluate(assignment_id):
    assignment = db.session.get(EvaluationAssignment, assignment_id)
    if not assignment:
        flash("Değerlendirme görevi bulunamadı.", "danger")
        return redirect(url_for("main.performance_tasks"))

    refresh_assignment_live_coverages(period_id=assignment.period_id)
    assignment = db.session.get(EvaluationAssignment, assignment_id)
    if not assignment:
        flash("Değerlendirme görevi bulunamadı.", "danger")
        return redirect(url_for("main.performance_tasks"))

    if not _can_access_assignment_for_actor(assignment, current_user):
        flash("Bu değerlendirme görevine erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.performance_tasks"))

    flash("Değerlendirme çalışma alanı V2 Faz 8 ana akışına taşındı.", "info")
    return redirect(url_for("main.performance_v2_phase8_assignment", assignment_id=assignment.id))
