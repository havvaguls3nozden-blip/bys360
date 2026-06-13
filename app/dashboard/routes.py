
"""BYS360 Dashboard Rebuild route ailesi.

D1-D5 kapsamında HTML dashboard, dashboard JSON veri ucu ve grafik JSON uçları
aynı yetki koruması altında çalışır.
"""
from __future__ import annotations

from flask import jsonify
from flask_login import current_user, login_required

from app.main_handlers.dashboard_handlers import dashboard as dashboard_handler
from app.main_handlers.dashboard_handlers import dashboard_heavy_panels as dashboard_heavy_panels_handler
from app.main_handlers.dashboard_handlers import db_check as db_check_handler
from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required
from app.services.dashboard_rebuild_service import build_dashboard_chart_payload, build_dashboard_json_payload

BYS360_DASHBOARD_REBUILD_ROUTES_OK = True


@main_bp.route("/dashboard")
@main_bp.route("/performance/dashboard")
@login_required
@menu_key_required("dashboard")
def dashboard():
    return dashboard_handler()


@main_bp.route("/dashboard/rebuild-data")
@main_bp.route("/performance/dashboard/rebuild-data")
@login_required
@menu_key_required("dashboard")
def dashboard_rebuild_data():
    # BYS360_DASHBOARD_REBUILD_D2_JSON_ENDPOINT_OK
    return jsonify(build_dashboard_json_payload(current_user))


@main_bp.route("/dashboard/rebuild-chart/<chart_key>")
@main_bp.route("/performance/dashboard/rebuild-chart/<chart_key>")
@login_required
@menu_key_required("dashboard")
def dashboard_rebuild_chart(chart_key: str):
    # BYS360_DASHBOARD_REBUILD_D2_CHART_ENDPOINT_OK
    return jsonify(build_dashboard_chart_payload(current_user, chart_key))


@main_bp.route("/performance/dashboard/heavy-panels", methods=["GET"])
@main_bp.route("/dashboard/heavy-panels")
@main_bp.route("/performance/dashboard/heavy-panels")
@login_required
@menu_key_required("dashboard")
def dashboard_heavy_panels():
    return dashboard_heavy_panels_handler()


@main_bp.route("/db-check")
@login_required
@admin_required
@menu_key_required("db_check")
def db_check():
    return db_check_handler()

# BYS360_PHASE12_ROUTE_ALIAS_REPAIR
# BYS360_PHASE12_ROUTE_ALIAS_STABLE_REPAIR
