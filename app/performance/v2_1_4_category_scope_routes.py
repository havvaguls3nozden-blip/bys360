from __future__ import annotations

import logging

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import admin_required, safe_render
from app.services.performance.v2_1_2_category_engine import seed_default_categories
from app.services.performance.v2_1_4_category_scope_visibility import (
    category_scope_dashboard_summary,
    category_scope_summaries,
    category_visibility_policy_for_user,
    deactivate_scope_draft,
    ensure_category_scope_schema,
    list_scope_drafts,
    upsert_category_scope_draft,
)
from app.services.performance.v2_1_4_category_scope_visibility_gate import (
    run_v2_1_4_category_scope_visibility_gate,
)
from app.services.performance.v2_1_6a_category_ui_cleanup import (
    active_categories,
    all_categories_with_usage,
    corporate_gate_label,
    create_or_update_category,
    delete_category_safely,
    label_status,
    restore_category,
)

logger = logging.getLogger(__name__)


@main_bp.route("/performance/v2-1-4-category-scope", methods=["GET", "POST"])
@login_required
@admin_required
def performance_v2_1_4_category_scope():
    ensure_category_scope_schema()
    seed_default_categories(overwrite=False)
    if request.method == "POST":
        action = request.form.get("action") or "create_scope_draft"
        try:
            if action == "create_scope_draft":
                result = upsert_category_scope_draft(
                    request.form.get("category_key") or "diger",
                    request.form.get("scope_name") or None,
                    request.form.get("notes") or "Kategori kapsam hazırlığı.",
                    getattr(current_user, "id", None),
                    request.form.get("visibility_mode") or "summary_only",
                )
                flash(f"Kategori kapsam taslağı kaydedildi: {result.get('scope_name')}", "success")
            elif action == "deactivate_scope_draft":
                scope_key = request.form.get("scope_key") or ""
                if scope_key:
                    deactivate_scope_draft(scope_key)
                    flash("Kapsam taslağı pasife alındı.", "success")
            elif action == "create_category":
                result = create_or_update_category(request.form.get("display_name") or "", request.form.get("description") or "")
                flash(result.get("message") or f"Kategori kaydedildi: {result.get('display_name')}", "success" if result.get("ok") else "warning")
            elif action == "delete_category":
                result = delete_category_safely(request.form.get("category_key") or "")
                flash(result.get("message") or "Kategori işlemi tamamlandı.", "success" if result.get("ok") else "warning")
            elif action == "restore_category":
                result = restore_category(request.form.get("category_key") or "")
                flash(result.get("message") or "Kategori yeniden aktifleştirildi.", "success")
            elif action == "seed":
                result = seed_default_categories(overwrite=False)
                flash(f"Kategori listesi kontrol edildi. Yeni: {result.get('created', 0)}, mevcut: {result.get('unchanged', 0)}", "success")
        except Exception as exc:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı. | exc=%s", exc)
            flash("Kategori kapsam işlemi tamamlanamadı.", "danger")
        return redirect(url_for("main.performance_v2_1_4_category_scope"))

    policy = category_visibility_policy_for_user(current_user)
    active_keys = {item.category_key for item in active_categories()}
    scopes = [item for item in category_scope_summaries(include_person_details=policy.get("can_see_person_details", False)) if item.get("category_key") in active_keys]
    return safe_render(
        "performance/v2_1_4_category_scope.html",
        page_title="Kategori ve Kapsam Yönetimi",
        categories=active_categories(),
        all_categories=all_categories_with_usage(),
        category_scopes=scopes,
        drafts=list_scope_drafts(include_inactive=False),
        summary=category_scope_dashboard_summary(),
        visibility_policy=policy,
        gate=run_v2_1_4_category_scope_visibility_gate(create_probe=False),
        label_status=label_status,
        corporate_gate_label=corporate_gate_label,
    )
