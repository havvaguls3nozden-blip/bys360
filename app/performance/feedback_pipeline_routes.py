from __future__ import annotations

from flask import render_template
from flask_login import current_user, login_required

from app.route_registry import main_bp
# BYS360_STUB_AI_V60_PIPELINE_IMPORT
from app.services.ai.stub_panel_bridge import attach_pipeline_ai_panel
# /BYS360_STUB_AI_V60_PIPELINE_IMPORT
from app.services.performance.feedback_pipeline import build_feedback_pipeline_context


@main_bp.route("/performance/feedback-pipeline", endpoint="performance_feedback_pipeline")
@main_bp.route("/performans/geri-bildirim-surec-hatti", endpoint="performance_feedback_pipeline_tr")
@login_required
def performance_feedback_pipeline():
    context = build_feedback_pipeline_context(current_user)
    # BYS360_STUB_AI_V60_PIPELINE_CONTEXT_ATTACH
    context = attach_pipeline_ai_panel(context)
    # /BYS360_STUB_AI_V60_PIPELINE_CONTEXT_ATTACH
    return render_template("performance/feedback_pipeline.html", **context)
