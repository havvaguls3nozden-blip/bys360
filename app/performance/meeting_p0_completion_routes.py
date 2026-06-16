# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_p0_completion import build_p0_completion_context, run_p0_completion


@main_bp.route("/performance/meeting-development/p0", endpoint="performance_meeting_p0_completion")
@main_bp.route("/performans/toplanti-gelistirme/p0-tamamlama", endpoint="performance_meeting_p0_completion_tr")
@login_required
@manager_required
def performance_meeting_p0_completion():
    return render_template(
        "performance/meeting_p0_completion.html",
        **build_p0_completion_context(viewer=current_user),
    )


@main_bp.route("/performance/meeting-development/p0/apply", methods=["POST"], endpoint="performance_meeting_p0_completion_apply")
@main_bp.route("/performans/toplanti-gelistirme/p0-tamamlama/uygula", methods=["POST"], endpoint="performance_meeting_p0_completion_apply_tr")
@login_required
@manager_required
def performance_meeting_p0_completion_apply():
    result = run_p0_completion(actor_user_id=getattr(current_user, "id", None))
    flash(result.message, "success" if result.ok else "warning")
    for warning in result.warnings or []:
        flash(warning, "warning")
    return redirect(url_for("main.performance_meeting_p0_completion"))
