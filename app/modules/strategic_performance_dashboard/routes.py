"""
BYS360 SP-1B Stratejik Performans Dashboard Routes

Blueprint kayıt örneği:
from app.modules.strategic_performance_dashboard.routes import strategic_performance_dashboard_bp
app.register_blueprint(strategic_performance_dashboard_bp)
"""
from __future__ import annotations

try:
    from flask import Blueprint, render_template
    from flask_login import login_required, current_user
except ImportError:
    Blueprint = None
    render_template = None
    login_required = lambda f: f
    current_user = None

from .services.dashboard_service import build_dashboard_summary, build_role_scope_label
from .services.ai_summary_service import build_ai_safe_summary

if Blueprint:
    strategic_performance_dashboard_bp = Blueprint(
        "strategic_performance_dashboard",
        __name__,
        url_prefix="/performans/stratejik/panel",
        template_folder="templates",
        static_folder="static",
    )

    @strategic_performance_dashboard_bp.route("/dashboard")
    @login_required
    def dashboard():
        summary = build_dashboard_summary(current_user=current_user)
        ai_notes = build_ai_safe_summary(summary)
        return render_template(
            "strategic_performance_dashboard/dashboard.html",
            summary=summary,
            ai_notes=ai_notes,
            scope_label=build_role_scope_label(current_user),
        )

    @strategic_performance_dashboard_bp.route("/oz-degerlendirme-ozet")
    @login_required
    def self_review():
        return render_template("strategic_performance_dashboard/self_review.html")
else:
    strategic_performance_dashboard_bp = None

# BYS360_CLAUDE_10E_DASHBOARD_BLUEPRINT_PREFIX_ISOLATED
