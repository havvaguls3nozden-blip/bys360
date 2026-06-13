# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import admin_required, safe_render
from app.services.performance.v2_1_rule_engine import DEFAULT_SETTINGS, build_rule_snapshot_dict
from app.services.performance.v2_1_settings_seed import seed_performance_v2_1_1_settings, update_performance_v2_1_1_settings
from app.services.performance.v2_1_quality_gate import run_v2_1_1_quality_gate
logger = logging.getLogger(__name__)


@main_bp.route("/performance/v2-1-1-rule-settings", methods=["GET", "POST"])
@login_required
@admin_required
def performance_v2_1_1_rule_settings():
    if request.method == "POST":
        action = request.form.get("action") or "save"
        if action == "seed":
            result = seed_performance_v2_1_1_settings(actor_user_id=getattr(current_user, "id", None), overwrite=False)
            flash(f"V2.1.1 varsayılan ayarları işlendi. Yeni: {result.get('created', 0)}, güncellenen: {result.get('updated', 0)}", "success")
        else:
            payload = {}
            for key, meta in DEFAULT_SETTINGS.items():
                if meta.get("value_type") == "bool":
                    payload[key] = "true" if request.form.get(key) in {"1", "true", "on"} else "false"
                else:
                    payload[key] = request.form.get(key, "")
            result = update_performance_v2_1_1_settings(payload, actor_user_id=getattr(current_user, "id", None))
            if result.get("rejected"):
                flash("Bazı ayarlar doğrulanamadı: " + ", ".join(result.get("rejected") or []), "warning")
            flash(f"V2.1.1 ayar merkezi kaydedildi. Değişen ayar: {result.get('changed', 0)}", "success")
        return redirect(url_for("main.performance_v2_1_1_rule_settings"))

    # Ekran ilk açıldığında eksik varsayılanları güvenli şekilde tamamla.
    try:
        seed_performance_v2_1_1_settings(actor_user_id=getattr(current_user, "id", None), overwrite=False)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        pass

    return safe_render(
        "performance/v2_1_1_rule_settings.html",
        page_title="V2.1.1 Kural Motoru ve Ayar Merkezi",
        settings_meta=DEFAULT_SETTINGS,
        snapshot=build_rule_snapshot_dict(),
        gate=run_v2_1_1_quality_gate(),
    )
