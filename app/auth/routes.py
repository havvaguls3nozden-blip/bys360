
"""Phase 43 modular authentication route family for the shared main blueprint."""
from __future__ import annotations

from app import routes as _core
from app.route_registry import main_bp

LEGACY_SHIM = False
LEGACY_RUNTIME_STATUS = "active_modular_main_blueprint_routes"
LEGACY_ROUTE_FAMILY = "auth_and_bootstrap"
LEGACY_NOTE = (
    "Phase 43 ile giriş, şifre sıfırlama, çıkış ve ilk admin kurulumu "
    "route kayıtları modüler yapıya taşındı. Gövde implementasyonları "
    "uyumluluk için app.routes içinde helper olarak korunur."
)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    return _core.login()


@main_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    return _core.forgot_password()


@main_bp.route("/logout", methods=["GET", "POST"])
def logout():
    return _core.logout()


@main_bp.route("/setup-admin", methods=["GET", "POST"])
def setup_admin():
    return _core.setup_admin()