# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import admin_required, safe_render
from app.services.performance.v2_1_2_category_engine import (
    DEFAULT_CATEGORIES,
    assign_user_category,
    category_scope_summary,
    ensure_category_schema,
    list_categories,
    seed_default_categories,
)
from app.services.performance.v2_1_2_category_quality_gate import run_v2_1_2_category_quality_gate
logger = logging.getLogger(__name__)


@main_bp.route("/performance/v2-1-2-categories", methods=["GET", "POST"])
@login_required
@admin_required
def performance_v2_1_2_categories():
    if request.method == "POST":
        action = request.form.get("action") or "seed"
        if action == "seed":
            schema = ensure_category_schema()
            result = seed_default_categories(overwrite=False)
            flash(f"V2.1.2 kategori altyapısı işlendi. Yeni: {result.get('created', 0)}, mevcut: {result.get('unchanged', 0)}", "success")
        elif action == "assign_user_category":
            user_id = request.form.get("user_id")
            category_key = request.form.get("category_key") or "diger"
            if not user_id or not str(user_id).isdigit():
                flash("Kategori ataması için geçerli bir kullanıcı ID girilmelidir.", "warning")
            else:
                result = assign_user_category(
                    user_id=int(user_id),
                    category_key=category_key,
                    source="manual_v2_1_2",
                    notes="V2.1.2 kategori merkezi üzerinden atandı.",
                    actor_user_id=getattr(current_user, "id", None),
                )
                flash(f"Kullanıcı #{result.get('user_id')} için kategori güncellendi: {result.get('category_key')}", "success")
        return redirect(url_for("main.performance_v2_1_2_categories"))

    try:
        seed_default_categories(overwrite=False)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        pass

    return safe_render(
        "performance/v2_1_2_categories.html",
        page_title="V2.1.2 Personel Grup/Kategori Altyapısı",
        default_categories=DEFAULT_CATEGORIES,
        categories=list_categories(include_inactive=True),
        summary=category_scope_summary(),
        gate=run_v2_1_2_category_quality_gate(),
    )
