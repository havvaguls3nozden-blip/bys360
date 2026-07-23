from __future__ import annotations

from flask import render_template
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.services.performance.feedback_corporate_cleanup_phase6 import build_phase6_context

MANAGER_ROLES = {
    "admin", "super_admin", "system_admin", "sistem_yoneticisi",
    "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir",
    "koordinator", "birim_sorumlusu", "yonetici", "manager", "performans_yetkilisi"
}


def _role() -> str:
    return (getattr(current_user, "role", "") or "").strip().lower()


def _is_admin() -> bool:
    return bool(
        getattr(current_user, "is_admin", False)
        or getattr(current_user, "is_superuser", False)
        or _role() in {"admin", "super_admin", "system_admin", "sistem_yoneticisi"}
    )


def _allowed() -> bool:
    return bool(_is_admin() or _role() in MANAGER_ROLES)


@main_bp.route("/performance/feedback-corporate-cleanup", endpoint="performance_feedback_corporate_cleanup")
@main_bp.route("/performans/geri-bildirim-canli-kontrol", endpoint="performance_feedback_corporate_cleanup_tr")
@login_required
def performance_feedback_corporate_cleanup():
    context = build_phase6_context(include_database=True)
    context["access_denied"] = not _allowed()
    return render_template("performance/feedback_corporate_cleanup_phase6.html", **context)
