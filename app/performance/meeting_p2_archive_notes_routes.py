from __future__ import annotations

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_p2_archive_notes import (
    build_p2_archive_notes_context,
    run_p2_archive_notes,
)


@main_bp.route("/performance/meeting-development/p2", endpoint="performance_meeting_p2_archive_notes")
@main_bp.route("/performans/toplanti-gelistirme/p2-arsiv-ara-not", endpoint="performance_meeting_p2_archive_notes_tr")
@login_required
@manager_required
def performance_meeting_p2_archive_notes():
    return render_template(
        "performance/meeting_p2_archive_notes.html",
        **build_p2_archive_notes_context(viewer=current_user),
    )


@main_bp.route("/performance/meeting-development/p2/apply", methods=["POST"], endpoint="performance_meeting_p2_archive_notes_apply")
@main_bp.route("/performans/toplanti-gelistirme/p2-arsiv-ara-not/uygula", methods=["POST"], endpoint="performance_meeting_p2_archive_notes_apply_tr")
@login_required
@manager_required
def performance_meeting_p2_archive_notes_apply():
    result = run_p2_archive_notes(actor_user_id=getattr(current_user, "id", None))
    flash(result.message, "success" if result.ok else "warning")
    for warning in result.warnings or []:
        flash(warning, "warning")
    return redirect(url_for("main.performance_meeting_p2_archive_notes"))
