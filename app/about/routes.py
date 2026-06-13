
"""BYS360 hakkında sayfası route ailesi."""
from __future__ import annotations

from flask_login import login_required

from app.main_handlers.about_handlers import about_bys360 as about_bys360_handler
from app.route_registry import main_bp
from app.route_support import menu_key_required

LEGACY_SHIM = False
LEGACY_RUNTIME_STATUS = "active_modular_main_blueprint_routes"
LEGACY_ROUTE_FAMILY = "about_bys360"
LEGACY_NOTE = (
    "BYS360 için kurumsal tanıtım ve proje vitrini sayfası eklendi. "
    "FlexCity benzeri ama BYS360'a özgü bir anlatı omurgası kullanılıyor."
)


@main_bp.route("/about-bys360")
@login_required
@menu_key_required("about_bys360")
def about_bys360():
    return about_bys360_handler()