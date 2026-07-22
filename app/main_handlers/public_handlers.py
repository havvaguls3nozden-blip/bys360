from __future__ import annotations

from flask import redirect, url_for
from flask_login import current_user

from app.route_support import safe_render
from app.services.home_dashboard_service import build_home_page_context
from app.services.kunye_settings_service import build_kunye_context

# BYS360 V4: Basında Tarihi Alan ana sayfa hero context'i kaldırıldı; modül kendi sayfasında kalır.
from app.services.portal_experience_service import portal_experience_context
from app.services.portal_experience_v2_service import portal_experience_v2_context

# BYS360_CORPORATE_PORTAL_V1_HOME_IMPORT
from app.services.portal_service import portal_home_context


def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    return redirect(url_for("main.login"))


def home():
    # Compatibility guard.
    context = build_home_page_context(current_user)
    # BYS360_CORPORATE_PORTAL_V1_HOME_CONTEXT
    context.update(portal_home_context(current_user))
    # BYS360_PORTAL_EXPERIENCE_V3A_HOME_PRESS_NEWS_CONTEXT_DISABLED_BY_V4
    context.update(portal_experience_context(current_user))
    context.update(portal_experience_v2_context(current_user))
    return safe_render(
        "home.html",
        "<h3>Anasayfa</h3>",
        **context,
    )


def strategy_management():
    return safe_render("strategy.html", "<h3>Strateji Yönetimi modülü yapım aşamasında</h3>")


def education_management():
    return safe_render("education.html", "<h3>Eğitim Yönetimi modülü yapım aşamasında</h3>")


def kunye():
    """BYS360 sistem künyesi sayfası."""
    return safe_render(
        "kunye.html",
        "<h3>BYS360 Sistem Künyesi</h3>",
        page_title="BYS360 Sistem Künyesi",
        kunye=build_kunye_context(),
    )
