from __future__ import annotations

# BYS360_PHASE3_3_PRESIDENT_APPROVAL_BACKEND_NOTE:
# Başkan onayı URL'leri backend route seviyesinde yalnızca Başkan/Admin ailesine veri vermelidir.
# Bu dosyadaki mevcut can_access_president_approvals / abort(403) kontrolleri Faz 3.3 kapsamının parçasıdır.
# -*- coding: utf-8 -*-
from flask import abort, render_template
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.services.performance.president_menu_card_access import (
    build_president_approval_scorecard_context,
)
from app.services.performance.process_engine_phase6_president_approvals import (
    can_view_president_approvals,
)


@main_bp.route(
    "/performans/baskan-onaylari/<int:approval_id>/karne",
    endpoint="performance_president_approval_scorecard",
    methods=["GET"],
)
@main_bp.route("/performance/president-approvals/<int:approval_id>/scorecard", methods=["GET"])
@login_required
def performance_president_approval_scorecard(approval_id: int):
    if not can_view_president_approvals(current_user):
        abort(403)
    context = build_president_approval_scorecard_context(approval_id)
    if not context.get("approval"):
        abort(404)
    return render_template("performance/president_approval_scorecard.html", **context)
