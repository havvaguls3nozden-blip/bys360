# -*- coding: utf-8 -*-
from __future__ import annotations



from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_rule_enforcement import (
    build_rule_enforcement_context,
    run_meeting_rule_enforcement,
)


@main_bp.route("/performance/meeting-development/rules", endpoint="performance_meeting_rule_enforcement")
@main_bp.route("/performans/toplanti-gelistirme/kurallar", endpoint="performance_meeting_rule_enforcement_tr")
@login_required
@manager_required
def performance_meeting_rule_enforcement():
    period_id = request.args.get("period_id", type=int)
    return render_template(
        "performance/meeting_rule_enforcement.html",
        **build_rule_enforcement_context(period_id=period_id, viewer=current_user),
    )


@main_bp.route("/performance/meeting-development/rules/apply", methods=["POST"], endpoint="performance_meeting_rule_enforcement_apply")
@main_bp.route("/performans/toplanti-gelistirme/kurallar/uygula", methods=["POST"], endpoint="performance_meeting_rule_enforcement_apply_tr")
@login_required
@manager_required
def performance_meeting_rule_enforcement_apply():
    period_id = request.form.get("period_id", type=int)
    result = run_meeting_rule_enforcement(period_id=period_id, actor_user_id=getattr(current_user, "id", None))
    flash(result.message, "success" if result.ok else "danger")
    for warning in result.warnings or []:
        flash(warning, "warning")
    return redirect(url_for("main.performance_meeting_rule_enforcement", period_id=period_id or ""))
