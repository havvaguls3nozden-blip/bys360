# -*- coding: utf-8 -*-
from __future__ import annotations



from flask import render_template
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_development_gate import build_meeting_test_context


@main_bp.route("/performance/meeting-development/test-scenarios", endpoint="performance_meeting_test_scenarios")
@main_bp.route("/performans/toplanti-test-senaryolari", endpoint="performance_meeting_test_scenarios_tr")
@login_required
@manager_required
def performance_meeting_test_scenarios():
    return render_template("performance/meeting_development_scenarios.html", **build_meeting_test_context())
