# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

from flask import request
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_render
from app.services.performance.v2_1_10_evaluation_live_tracking import (
    build_evaluation_live_tracking_state,
    run_v2_1_10_evaluation_live_tracking_gate,
    status_label,
)
from app.services.performance.v2_1_6a_category_ui_cleanup import corporate_gate_label
logger = logging.getLogger(__name__)


@main_bp.route("/performance/v2-1-10-evaluation-live-tracking", methods=["GET"])
@main_bp.route("/performans/canli-degerlendirme-takibi", methods=["GET"])
@login_required
@menu_key_required("performance_evaluation_live_tracking")
def performance_v2_1_10_evaluation_live_tracking():
    period_raw = request.args.get("period_id") or request.args.get("period") or ""
    try:
        period_id = int(period_raw) if period_raw else None
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        period_id = None
    state = build_evaluation_live_tracking_state(
        period_id=period_id,
        status_filter=request.args.get("status") or "",
        manager_level=request.args.get("manager_level") or "",
        q=request.args.get("q") or "",
        include_rows=True,
    )
    return safe_render(
        "performance/v2_1_10_evaluation_live_tracking.html",
        page_title="Değerlendirme Süreci Canlı Takip",
        state=state,
        gate=run_v2_1_10_evaluation_live_tracking_gate(),
        status_label=status_label,
        corporate_gate_label=corporate_gate_label,
    )
