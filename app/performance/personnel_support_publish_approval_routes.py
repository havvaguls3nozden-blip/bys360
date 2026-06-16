# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.services.performance.personnel_support_publish_approval_service import (
    build_personnel_support_publish_approval_workspace,
    can_view_personnel_support_publish_approvals,
    decide_personnel_support_publish_approval,
)


def _access_denied():
    return render_template(
        "errors/403.html",
        title="Erişim Yetkiniz Bulunmamaktadır",
        message="Bu sayfa yalnızca Personel ve Destek Hizmetleri Grup Başkanı, Admin ve yetkili yayın kullanıcıları tarafından görüntülenebilir.",
        back_url=url_for("main.dashboard"),
    ), 403


@main_bp.route("/performans/personel-destek-yayin-onayi", methods=["GET"], endpoint="performance_personnel_support_publish_approvals")
@main_bp.route("/performance/personnel-support-publish-approvals", methods=["GET"])
@login_required
def performance_personnel_support_publish_approvals():
    if not can_view_personnel_support_publish_approvals(current_user):
        return _access_denied()
    status_filter = (request.args.get("status") or "pending").strip()
    workspace = build_personnel_support_publish_approval_workspace(current_user, status_filter=status_filter)
    return render_template("performance/personnel_support_publish_approvals.html", **workspace)


@main_bp.route("/performans/personel-destek-yayin-onayi/<int:approval_id>/onayla", methods=["POST"], endpoint="performance_personnel_support_publish_approval_approve")
@main_bp.route("/performance/personnel-support-publish-approvals/<int:approval_id>/approve", methods=["POST"])
@login_required
def performance_personnel_support_publish_approval_approve(approval_id: int):
    if not can_view_personnel_support_publish_approvals(current_user):
        return _access_denied()
    note = (request.form.get("note") or "").strip() or None
    result = decide_personnel_support_publish_approval(approval_id, current_user, "approved", note=note)
    flash(result.message, "success" if result.ok else "danger")
    return redirect(url_for("main.performance_personnel_support_publish_approvals", status="pending"))


@main_bp.route("/performans/personel-destek-yayin-onayi/<int:approval_id>/iade", methods=["POST"], endpoint="performance_personnel_support_publish_approval_return")
@main_bp.route("/performance/personnel-support-publish-approvals/<int:approval_id>/return", methods=["POST"])
@login_required
def performance_personnel_support_publish_approval_return(approval_id: int):
    if not can_view_personnel_support_publish_approvals(current_user):
        return _access_denied()
    note = (request.form.get("note") or "").strip() or None
    result = decide_personnel_support_publish_approval(approval_id, current_user, "returned", note=note)
    flash(result.message, "warning" if result.ok else "danger")
    return redirect(url_for("main.performance_personnel_support_publish_approvals", status="pending"))
