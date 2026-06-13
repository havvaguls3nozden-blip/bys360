# -*- coding: utf-8 -*-
from __future__ import annotations



from flask import render_template
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_development_final_gate import build_final_gate_context


@main_bp.route("/performance/meeting-development/final-gate", endpoint="performance_meeting_final_gate")
@main_bp.route("/performans/toplanti-gelistirme/final-kontrol", endpoint="performance_meeting_final_gate_tr")
@login_required
@manager_required
def performance_meeting_final_gate():
    return render_template("performance/meeting_development_faz4.html", **build_final_gate_context())
