from __future__ import annotations

# BYS360_PHASE3_3_PRESIDENT_APPROVAL_BACKEND_NOTE:
# Başkan onayı URL'leri backend route seviyesinde yalnızca Başkan/Admin ailesine veri vermelidir.
# Bu dosyadaki mevcut can_access_president_approvals / abort(403) kontrolleri Faz 3.3 kapsamının parçasıdır.
# -*- coding: utf-8 -*-

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.services.performance.process_engine_phase6_president_approvals import (
    build_president_approval_workspace,
    can_view_president_approvals,
    decide_president_approval,
    delete_president_approval_record,
)
from app.services.performance.president_card_review_service import build_president_card_review_context


def _render_president_approvals_access_denied():
    return render_template(
        "errors/403.html",
        title="Erişim Yetkiniz Bulunmamaktadır",
        message="Bu sayfa yalnızca Başkan ve yetkili sistem yöneticileri tarafından görüntülenebilir.",
        back_url=url_for("main.dashboard"),
    ), 403


@main_bp.route("/performans/baskan-onaylari", methods=["GET", "POST"])
@main_bp.route("/performance/president-approvals", endpoint="performance_president_approvals")
@main_bp.route("/performans/baskan-onaylari")
@login_required
def performance_president_approvals():
    if not can_view_president_approvals(current_user):
        return _render_president_approvals_access_denied()
    status_filter = (request.args.get("status") or "pending").strip()
    workspace = build_president_approval_workspace(current_user, status_filter=status_filter)
    return render_template("performance/process_engine_president_approvals.html", **workspace)


@main_bp.route("/performans/baskan-onaylari/<int:approval_id>/karne", methods=["GET"], endpoint="performance_president_card_review")
@main_bp.route("/performance/president-approvals/<int:approval_id>/scorecard", methods=["GET"])
@main_bp.route("/performance/president-approvals/<int:approval_id>/card", methods=["GET"])
@login_required
def performance_president_card_review(approval_id: int):
    if not can_view_president_approvals(current_user):
        return _render_president_approvals_access_denied()
    context = build_president_card_review_context(approval_id, current_user)
    if not context.get("approval"):
        abort(404)
    return render_template("performance/president_card_review.html", **context)


@main_bp.route("/performance/president-approvals/<int:approval_id>/approve", methods=["POST"], endpoint="performance_president_approval_approve")
@main_bp.route("/performans/baskan-onaylari/<int:approval_id>/onayla", methods=["POST"])
@login_required
def performance_president_approval_approve(approval_id: int):
    if not can_view_president_approvals(current_user):
        return _render_president_approvals_access_denied()
    note = (request.form.get("note") or "").strip() or None
    result = decide_president_approval(approval_id, current_user, "approved", note=note)
    flash(result.message, "success" if result.ok else "danger")
    return redirect(url_for("main.performance_president_approvals", status="pending"))


@main_bp.route("/performance/president-approvals/<int:approval_id>/return", methods=["POST"], endpoint="performance_president_approval_return")
@main_bp.route("/performans/baskan-onaylari/<int:approval_id>/iade", methods=["POST"])
@login_required
def performance_president_approval_return(approval_id: int):
    if not can_view_president_approvals(current_user):
        return _render_president_approvals_access_denied()
    note = (request.form.get("note") or "").strip() or None
    result = decide_president_approval(approval_id, current_user, "returned", note=note)
    flash(result.message, "warning" if result.ok else "danger")
    return redirect(url_for("main.performance_president_approvals", status="pending"))


@main_bp.route("/performance/president-approvals/<int:approval_id>/delete", methods=["POST"], endpoint="performance_president_approval_delete")
@main_bp.route("/performans/baskan-onaylari/<int:approval_id>/sil", methods=["POST"])
@login_required
def performance_president_approval_delete(approval_id: int):
    if not can_view_president_approvals(current_user):
        return _render_president_approvals_access_denied()
    status_filter = (request.form.get("status_filter") or request.args.get("status") or "all").strip()
    result = delete_president_approval_record(approval_id, current_user)
    flash(result.message, "success" if result.ok else "danger")
    return redirect(url_for("main.performance_president_approvals", status=status_filter or "all"))

# BYS360_PHASE12_ROUTE_ALIAS_REPAIR

# BYS360_PHASE12_ROUTE_ALIAS_STABLE_REPAIR

# BYS360_PRESIDENT_MENU_CARD_HISTORY_STATUS_FINAL_V1

# BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_APPROVAL_BOUND
# 70 altı düşük performans üst onay/yayın kilidi phase6_low_score_approval_policy ile izlenir.
