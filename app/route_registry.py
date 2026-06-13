
"""BYS360 runtime route registry.

Blueprint tarafinda tek bir omurga kalir; moduller parcali olsa da ana URL
yapisi ve aktif route manifesti tek merkezden izlenir.
"""
from __future__ import annotations

from flask import Blueprint

from app.config.removed_modules import is_module_removed

PRIMARY_BLUEPRINT_NAME = "main"
PRIMARY_ROUTE_MODULE = "app.routes"

_BASE_MODULAR_ROUTE_MODULES = (
    "app.auth.routes",
    "app.account.routes",
    "app.admin.routes",
    "app.performance.routes",
    "app.workflow.routes",
    # performance alt modulleri (hierarchy/admin-core/evaluation-core/task/report/history/engagement)
    # paket importu ile aktif olur.
    "app.dashboard.routes",
    "app.institutional.routes",
    "app.communication.routes",
    "app.support.routes",
)


def _build_modular_route_modules() -> tuple[str, ...]:
    modules = list(_BASE_MODULAR_ROUTE_MODULES)
    if not is_module_removed("portal"):
        modules.append("app.portal.routes")
    return tuple(modules)


MODULAR_ROUTE_MODULES = _build_modular_route_modules()

LEGACY_SHIM_MODULES = (
    "app.routes_auth",
    "app.routes_dashboard",
    "app.routes_admin_personnel",
    "app.routes_performance_admin",
    "app.routes_hr",
    "app.routes_communication",
)

LEGACY_ARCHIVE_MODULE_ROOT = "app.legacy_routes_archive"
LEGACY_ARCHIVE_MODULES = (
    "app.legacy_routes_archive.routes_auth",
    "app.legacy_routes_archive.routes_dashboard",
    "app.legacy_routes_archive.routes_admin_personnel",
    "app.legacy_routes_archive.routes_performance_admin",
    "app.legacy_routes_archive.routes_hr",
    "app.legacy_routes_archive.routes_communication",
    "app.legacy_routes_archive.admin.routes",
    "app.legacy_routes_archive.performance.routes",
)

main_bp = Blueprint(PRIMARY_BLUEPRINT_NAME, __name__)


def get_runtime_route_manifest() -> dict[str, object]:
    return {
        "primary_blueprint": PRIMARY_BLUEPRINT_NAME,
        "primary_route_module": PRIMARY_ROUTE_MODULE,
        "modular_route_modules": list(MODULAR_ROUTE_MODULES),
        "legacy_shim_modules": list(LEGACY_SHIM_MODULES),
        "legacy_archive_module_root": LEGACY_ARCHIVE_MODULE_ROOT,
        "legacy_archive_modules": list(LEGACY_ARCHIVE_MODULES),
    }
