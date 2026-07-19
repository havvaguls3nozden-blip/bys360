from __future__ import annotations

from collections.abc import Callable

from flask import Flask


def run_runtime_pipeline(
    app: Flask,
    *,
    register_template_safety: Callable[[Flask], None],
    configure_operational_logging: Callable[[Flask], None],
    register_error_handlers: Callable[[Flask], None],
    register_service_unavailable_handler: Callable[[Flask], None],
    register_teardown_guards: Callable[[Flask], None],
    register_operational_guards: Callable[[Flask], None],
    register_response_hardening: Callable[[Flask], None],
) -> None:
    register_template_safety(app)
    configure_operational_logging(app)
    log_startup_summary(app)
    register_error_handlers(app)
    register_service_unavailable_handler(app)
    register_teardown_guards(app)
    register_operational_guards(app)
    register_response_hardening(app)


def log_startup_summary(app: Flask) -> None:
    database_uri = (app.config.get("SQLALCHEMY_DATABASE_URI") or "").strip()
    db_backend = database_uri.split(":", 1)[0] if database_uri else "tanimsiz"
    maintenance_mode = str(app.config.get("MAINTENANCE_MODE", "")).strip().lower() in {"1", "true", "yes", "on"}
    schema_errors = list(app.extensions.get("schema_check_errors", []) or [])
    route_manifest = app.extensions.get("runtime_route_manifest") or {}

    live_scope_summary = {}
    try:
        from app.config import get_live_scope_summary
        live_scope_summary = get_live_scope_summary() or {}
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/bootstrap/startup.py:42")
        live_scope_summary = {}

    app.logger.info(
        "Startup ozeti | env=%s | db=%s | maintenance=%s | route_count=%s | schema_errors=%s | core_scope=%s | removed_scope=%s",
        app.config.get("APP_ENV", "development"),
        db_backend,
        "on" if maintenance_mode else "off",
        len(route_manifest) if isinstance(route_manifest, dict) else 0,
        len(schema_errors),
        live_scope_summary.get("active_core_count", 0),
        live_scope_summary.get("removed_module_count", 0),
    )
