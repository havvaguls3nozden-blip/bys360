# -*- coding: utf-8 -*-
from __future__ import annotations



from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_p1_scope import build_p1_scope_context, run_p1_scope


@main_bp.route("/performance/meeting-development/p1", endpoint="performance_meeting_p1_scope")
@main_bp.route("/performans/toplanti-gelistirme/p1-gelistirme", endpoint="performance_meeting_p1_scope_tr")
@login_required
@manager_required
def performance_meeting_p1_scope():
    return render_template(
        "performance/meeting_p1_scope.html",
        **build_p1_scope_context(viewer=current_user),
    )


@main_bp.route("/performance/meeting-development/p1/apply", methods=["POST"], endpoint="performance_meeting_p1_scope_apply")
@main_bp.route("/performans/toplanti-gelistirme/p1-gelistirme/uygula", methods=["POST"], endpoint="performance_meeting_p1_scope_apply_tr")
@login_required
@manager_required
def performance_meeting_p1_scope_apply():
    result = run_p1_scope(actor_user_id=getattr(current_user, "id", None))
    flash(result.message, "success" if result.ok else "warning")
    for warning in result.warnings or []:
        flash(warning, "warning")
    return redirect(url_for("main.performance_meeting_p1_scope"))
