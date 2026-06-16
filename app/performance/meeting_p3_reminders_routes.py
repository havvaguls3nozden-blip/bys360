# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_p3_reminders import build_p3_reminders_context, run_p3_reminders


@main_bp.route("/performance/meeting-development/faz9", endpoint="performance_meeting_p3_reminders")
@main_bp.route("/performans/toplanti-gelistirme/faz9-hatirlatma", endpoint="performance_meeting_p3_reminders_tr")
@login_required
@manager_required
def performance_meeting_p3_reminders():
    return render_template(
        "performance/meeting_p3_reminders.html",
        **build_p3_reminders_context(viewer=current_user),
    )


@main_bp.route("/performance/meeting-development/faz9/apply", methods=["POST"], endpoint="performance_meeting_p3_reminders_apply")
@main_bp.route("/performans/toplanti-gelistirme/faz9-hatirlatma/uygula", methods=["POST"], endpoint="performance_meeting_p3_reminders_apply_tr")
@login_required
@manager_required
def performance_meeting_p3_reminders_apply():
    result = run_p3_reminders(actor_user_id=getattr(current_user, "id", None))
    flash(result.message, "success" if result.ok else "warning")
    for warning in result.warnings or []:
        flash(warning, "warning")
    return redirect(url_for("main.performance_meeting_p3_reminders"))
