"""BYS360 Workflow Engine Faz 9 - Yönetici Dashboard Upgrade routes."""
from __future__ import annotations

from flask import Blueprint, render_template
from flask_login import login_required

from app.services.workflow.dashboard_upgrade import demo_dashboard_data

workflow_dashboard_upgrade_bp = Blueprint(
    "workflow_dashboard_upgrade",
    __name__,
    url_prefix="/workflow",
    template_folder="templates",
)


@workflow_dashboard_upgrade_bp.get("/executive-dashboard")
@login_required
def executive_dashboard():
    data = demo_dashboard_data()
    return render_template(
        "workflow/executive_dashboard.html",
        performance_map=data["performance_map"],
        delayed_managers=data["delayed_managers"],
        risky_personnel=data["risky_personnel"],
    )
