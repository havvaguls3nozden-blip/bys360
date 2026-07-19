from __future__ import annotations

from flask import render_template, request
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.services.performance.feedback_meeting_guide import build_guide_context

GUIDE_ALLOWED_ROLES = {
    "admin",
    "super_admin",
    "system_admin",
    "sistem_yoneticisi",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "koordinator",
    "birim_sorumlusu",
    "yonetici",
    "manager",
    "performans_yetkilisi",
}


def _user_role() -> str:
    return (getattr(current_user, "role", "") or "").strip().lower()


def _can_view_guide() -> bool:
    return bool(
        getattr(current_user, "is_admin", False)
        or getattr(current_user, "is_superuser", False)
        or _user_role() in GUIDE_ALLOWED_ROLES
    )


@main_bp.route("/performance/feedback-meeting-guide", endpoint="performance_feedback_meeting_guide")
@main_bp.route("/performans/geri-bildirim-gorusme-rehberi", endpoint="performance_feedback_meeting_guide_tr")
@login_required
def performance_feedback_meeting_guide():
    ctx = build_guide_context((request.args.get("scenario") or "").strip())
    ctx["can_view_guide"] = _can_view_guide()
    return render_template("performance/feedback_meeting_guide.html", **ctx)
