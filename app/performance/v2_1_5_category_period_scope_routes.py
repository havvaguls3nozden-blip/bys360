from __future__ import annotations


import logging

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import admin_required, safe_render
from app.services.performance.v2_1_2_category_engine import seed_default_categories
from app.services.performance.v2_1_5_category_period_scope import (
    PERIOD_TYPES,
    assignment_precheck_for_plan,
    category_period_scope_summary,
    deactivate_category_period_scope_plan,
    ensure_category_period_scope_schema,
    list_category_period_scope_plans,
    list_plan_items,
    preview_category_period_scope,
    upsert_category_period_scope_plan,
)
from app.services.performance.v2_1_5_category_period_scope_gate import run_v2_1_5_category_period_scope_gate
from app.services.performance.v2_1_6a_category_ui_cleanup import active_categories, corporate_gate_label, label_status
logger = logging.getLogger(__name__)


@main_bp.route("/performance/v2-1-5-category-period-scope", methods=["GET", "POST"])
@login_required
@admin_required
def performance_v2_1_5_category_period_scope():
    ensure_category_period_scope_schema()
    seed_default_categories(overwrite=False)
    if request.method == "POST":
        action = request.form.get("action") or "create_plan"
        try:
            if action == "create_plan":
                result = upsert_category_period_scope_plan(
                    category_key=request.form.get("category_key") or "diger",
                    plan_name=request.form.get("plan_name") or None,
                    period_type=request.form.get("period_type") or "special",
                    start_date=request.form.get("start_date") or None,
                    end_date=request.form.get("end_date") or None,
                    notes=request.form.get("notes") or "Kategori dönem kapsam hazırlığı.",
                    created_by=getattr(current_user, "id", None),
                    scope_visibility_mode=request.form.get("scope_visibility_mode") or "summary_only",
                )
                status = "Plan hazırlandı" if result.get("ready_for_assignment") else "Plan kaydedildi, kontrol gerekiyor"
                flash(f"{status}: {result.get('plan_name')}", "success" if result.get("ready_for_assignment") else "warning")
            elif action == "deactivate_plan":
                plan_key = request.form.get("plan_key") or ""
                if plan_key:
                    deactivate_category_period_scope_plan(plan_key)
                    flash("Dönem kapsam planı pasife alındı.", "success")
            elif action == "seed":
                seed_default_categories(overwrite=False)
                flash("Kategori listesi kontrol edildi.", "success")
        except Exception as exc:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            flash(f"Kapsam işlemi tamamlanamadı: {exc}", "danger")
        return redirect(url_for("main.performance_v2_1_5_category_period_scope"))

    cats = active_categories()
    selected_category = request.args.get("category") or (cats[0].category_key if cats else "diger")
    selected_plan = request.args.get("plan") or ""
    return safe_render(
        "performance/v2_1_5_category_period_scope.html",
        page_title="Kategoriye Göre Dönem Hazırlığı",
        categories=cats,
        period_types=PERIOD_TYPES,
        selected_category=selected_category,
        selected_preview=preview_category_period_scope(selected_category, include_person_details=True),
        summary=category_period_scope_summary(),
        plans=list_category_period_scope_plans(include_inactive=False),
        selected_plan=selected_plan,
        plan_items=list_plan_items(selected_plan, include_person_details=True, limit=80) if selected_plan else [],
        precheck=assignment_precheck_for_plan(selected_plan) if selected_plan else None,
        gate=run_v2_1_5_category_period_scope_gate(create_probe=False),
        label_status=label_status,
        corporate_gate_label=corporate_gate_label,
    )
