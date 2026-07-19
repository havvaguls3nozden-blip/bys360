from __future__ import annotations


import logging

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import admin_required, safe_render
from app.services.performance.v2_1_2_category_engine import list_categories, seed_default_categories
from app.services.performance.v2_1_3_personnel_category_card import (
    assign_personnel_category_from_card,
    bulk_assign_personnel_category,
    category_card_summary,
    ensure_v2_1_3_schema,
    get_category_audit,
    get_personnel_category_rows,
    template_get_user_category,
)
from app.services.performance.v2_1_3_personnel_category_card_gate import run_v2_1_3_personnel_category_card_gate
logger = logging.getLogger(__name__)


@main_bp.app_context_processor
def _v2_1_3_category_context_processor():
    return {"v213_get_user_category": template_get_user_category}


@main_bp.route("/performance/v2-1-3-personnel-category-card", methods=["GET", "POST"])
@login_required
@admin_required
def performance_v2_1_3_personnel_category_card():
    ensure_v2_1_3_schema()
    seed_default_categories(overwrite=False)

    if request.method == "POST":
        action = request.form.get("action") or "assign_user_category"
        actor_id = getattr(current_user, "id", None)
        try:
            if action == "assign_user_category":
                user_id = request.form.get("user_id")
                category_key = request.form.get("category_key") or "diger"
                notes = request.form.get("notes") or "V2.1.3 personel kategori kartı üzerinden atandı."
                if not user_id or not str(user_id).isdigit():
                    flash("Kategori ataması için geçerli bir kullanıcı ID girilmelidir.", "warning")
                else:
                    result = assign_personnel_category_from_card(int(user_id), category_key, actor_user_id=actor_id, notes=notes)
                    flash(f"Kullanıcı #{result.get('user_id')} için performans kategorisi güncellendi: {result.get('new_category_key')}", "success")
            elif action == "bulk_assign_category":
                user_ids = request.form.get("user_ids") or ""
                category_key = request.form.get("category_key") or "diger"
                notes = request.form.get("notes") or "V2.1.3 toplu kategori ataması."
                result = bulk_assign_personnel_category(user_ids, category_key, actor_user_id=actor_id, notes=notes)
                if result.get("assigned_count"):
                    flash(f"Toplu kategori ataması tamamlandı. Atanan kayıt: {result.get('assigned_count')}", "success")
                if result.get("errors"):
                    flash(f"Bazı kayıtlar işlenemedi. Hata sayısı: {len(result.get('errors') or [])}", "warning")
            elif action == "seed":
                result = seed_default_categories(overwrite=False)
                flash(f"Varsayılan kategoriler kontrol edildi. Yeni: {result.get('created', 0)}, mevcut: {result.get('unchanged', 0)}", "success")
        except Exception as exc:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            flash(f"Kategori işlemi tamamlanamadı: {exc}", "danger")
        return redirect(url_for("main.performance_v2_1_3_personnel_category_card", q=request.args.get("q", ""), category=request.args.get("category", "")))

    q = request.args.get("q") or ""
    category = request.args.get("category") or ""
    limit = request.args.get("limit") or 100
    try:
        limit_int = max(10, min(int(limit), 500))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        limit_int = 100

    return safe_render(
        "performance/v2_1_3_personnel_category_card.html",
        page_title="V2.1.3 Personel Kartı Kategori ve Atama Merkezi",
        categories=list_categories(include_inactive=True),
        personnel_rows=get_personnel_category_rows(limit=limit_int, search=q, category_key=category or None),
        audit_rows=get_category_audit(limit=30),
        summary=category_card_summary(),
        gate=run_v2_1_3_personnel_category_card_gate(),
        filters={"q": q, "category": category, "limit": limit_int},
    )
