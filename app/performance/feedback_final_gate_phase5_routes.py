# -*- coding: utf-8 -*-
from __future__ import annotations



from flask import render_template
from flask_login import current_user, login_required

from app.route_registry import main_bp
# BYS360_STUB_AI_V60_FINAL_GATE_IMPORT
from app.services.ai.stub_panel_bridge import attach_process_tracking_ai_panel
# /BYS360_STUB_AI_V60_FINAL_GATE_IMPORT
from app.services.performance.feedback_final_gate_phase5 import build_phase5_context


MANAGER_ROLES = {
    "admin", "super_admin", "system_admin", "sistem_yoneticisi",
    "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir",
    "koordinator", "birim_sorumlusu", "yonetici", "manager", "performans_yetkilisi"
}


def _role() -> str:
    return (getattr(current_user, "role", "") or "").strip().lower()


def _is_admin() -> bool:
    return bool(getattr(current_user, "is_admin", False) or getattr(current_user, "is_superuser", False) or _role() in {"admin", "super_admin", "system_admin", "sistem_yoneticisi"})


def _allowed() -> bool:
    return bool(_is_admin() or _role() in MANAGER_ROLES)


@main_bp.route("/performance/feedback-final-gate", endpoint="performance_feedback_final_gate")
@main_bp.route("/performans/geri-bildirim-final-kontrol", endpoint="performance_feedback_final_gate_tr")
@login_required
def performance_feedback_final_gate():
    context = build_phase5_context(include_database=True)
    context["access_denied"] = not _allowed()
    # BYS360_STUB_AI_V60_FINAL_GATE_CONTEXT_ATTACH
    context = attach_process_tracking_ai_panel(context)
    # /BYS360_STUB_AI_V60_FINAL_GATE_CONTEXT_ATTACH
    return render_template("performance/feedback_final_gate_phase5.html", **context)
