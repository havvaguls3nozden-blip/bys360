"""
BYS360 SP-2F Stratejik Performans görünür sekme route uyumluluğu

Bu dosya main blueprint'e bağlı çalışır.
Ayrı blueprint kaydı gerektirmez; app/routes.py tarafından import edilince
route'lar aktif olur.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import render_access_denied, safe_render
from app.services.role_guards import can_manage_strategic_targets, is_top_or_manager

logger = logging.getLogger(__name__)


build_sp1c_kpi_dashboard_context: Callable[[Any], dict[str, Any]] | None
try:
    from app.services.sp1c_kpi_dashboard_service import build_sp1c_kpi_dashboard_context
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    build_sp1c_kpi_dashboard_context = None

build_target_form_context: Callable[[Any], dict[str, Any]] | None
create_target_from_form: Callable[[Any, Any], tuple[bool, str]] | None
get_target_for_edit: Callable[[int, Any], dict[str, Any] | None] | None
list_targets_for_user: Callable[[Any], list[dict[str, Any]]] | None
update_target_from_form: Callable[[int, Any, Any], tuple[bool, str]] | None
try:
    from app.services.sp1d_target_management_service import (
        build_target_form_context,
        create_target_from_form,
        get_target_for_edit,
        list_targets_for_user,
        update_target_from_form,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    build_target_form_context = None
    create_target_from_form = None
    get_target_for_edit = None
    list_targets_for_user = None
    update_target_from_form = None


def _is_top_or_manager() -> bool:
    return is_top_or_manager(current_user)


def _can_manage_targets() -> bool:
    return can_manage_strategic_targets(current_user)


def _access_denied():
    return render_access_denied("Bu sayfaya erişim yetkiniz bulunmamaktadır.", status_code=403)


def _empty_dashboard_context():
    return {
        "summary": {
            "total_targets": 0,
            "completed_targets": 0,
            "risk_targets": 0,
            "critical_targets": 0,
            "average_completion": 0,
        },
        "targets": [],
        "ai_notes": [
            "KPI ve hedef verileri stratejik performans omurgasına bağlanmaya hazır."
        ],
    }


@main_bp.route("/performance/kpi/dashboard", endpoint="sp1_kpi_dashboard")
@main_bp.route("/performans/stratejik/kpi-dashboard", endpoint="sp1_kpi_dashboard_tr")
@login_required
def sp1_kpi_dashboard():
    if not _is_top_or_manager():
        return _access_denied()

    if build_sp1c_kpi_dashboard_context:
        context = build_sp1c_kpi_dashboard_context(current_user)
    else:
        context = _empty_dashboard_context()

    return safe_render(
        "strategic_performance/kpi_dashboard.html",
        fallback_html="<h3>KPI Dashboardu</h3>",
        **context,
    )


@main_bp.route("/performance/kpi/targets", endpoint="sp1_kpi_targets")
@main_bp.route("/performans/stratejik/hedefler", endpoint="sp1_kpi_targets_tr")
@login_required
def sp1_kpi_targets():
    if not _is_top_or_manager():
        return _access_denied()

    targets = list_targets_for_user(current_user) if list_targets_for_user else []
    return safe_render(
        "strategic_performance/target_list.html",
        fallback_html="<h3>KPI ve Hedef Yönetimi</h3>",
        page_title="KPI ve Hedef Listesi",
        targets=targets,
        can_manage=_can_manage_targets(),
    )


@main_bp.route("/performance/kpi/targets/new", methods=["GET", "POST"], endpoint="sp1_kpi_target_create")
@main_bp.route("/performance/kpi/targets/yeni", methods=["GET", "POST"], endpoint="sp1_kpi_target_create_tr")
@login_required
def sp1_kpi_target_create():
    if not _can_manage_targets():
        return _access_denied()

    if request.method == "POST":
        if create_target_from_form:
            ok, message = create_target_from_form(request.form, current_user)
        else:
            ok, message = False, "Hedef kayıt servisi kullanılamıyor."
        flash(message, "success" if ok else "warning")
        if ok:
            return redirect(url_for("main.sp1_kpi_targets"))

    context = build_target_form_context(current_user) if build_target_form_context else {}
    context.setdefault("target_types", [
        ("kurumsal", "Kurumsal"),
        ("birim", "Birim"),
        ("personel", "Personel"),
    ])
    context.setdefault("categories", [
        ("kpi", "KPI"),
        ("operasyon", "Operasyon"),
        ("stratejik", "Stratejik"),
    ])
    context.setdefault("periods", [])

    return safe_render(
        "strategic_performance/target_form.html",
        fallback_html="<h3>Yeni KPI / Hedef Oluştur</h3>",
        page_title="Yeni KPI / Hedef Oluştur",
        form_mode="create",
        target={},
        **context,
    )


@main_bp.route("/performance/kpi/targets/<int:target_id>/edit", methods=["GET", "POST"], endpoint="sp1_kpi_target_edit")
@main_bp.route("/performance/kpi/targets/<int:target_id>/duzenle", methods=["GET", "POST"], endpoint="sp1_kpi_target_edit_tr")
@login_required
def sp1_kpi_target_edit(target_id: int):
    if not _can_manage_targets():
        return _access_denied()

    target = get_target_for_edit(target_id, current_user) if get_target_for_edit else None
    if not target:
        flash("Hedef kaydı bulunamadı veya bu kayıt için yetkiniz yok.", "warning")
        return redirect(url_for("main.sp1_kpi_targets"))

    if request.method == "POST":
        if update_target_from_form:
            ok, message = update_target_from_form(target_id, request.form, current_user)
        else:
            ok, message = False, "Hedef güncelleme servisi kullanılamıyor."
        flash(message, "success" if ok else "warning")
        if ok:
            return redirect(url_for("main.sp1_kpi_targets"))

    context = build_target_form_context(current_user) if build_target_form_context else {}
    context.setdefault("target_types", [
        ("kurumsal", "Kurumsal"),
        ("birim", "Birim"),
        ("personel", "Personel"),
    ])
    context.setdefault("categories", [
        ("kpi", "KPI"),
        ("operasyon", "Operasyon"),
        ("stratejik", "Stratejik"),
    ])
    context.setdefault("periods", [])

    return safe_render(
        "strategic_performance/target_form.html",
        fallback_html="<h3>KPI / Hedef Düzenle</h3>",
        page_title="KPI / Hedef Düzenle",
        form_mode="edit",
        target=target,
        **context,
    )


@main_bp.route("/performance/competencies", endpoint="sp1_competency_library")
@main_bp.route("/performans/stratejik/yetkinlik-kutuphanesi", endpoint="sp1_competency_library_tr")
@login_required
def sp1_competency_library():
    if not _is_top_or_manager():
        return _access_denied()
    return safe_render(
        "strategic_performance/competency_library.html",
        fallback_html="<h3>Yetkinlik Kütüphanesi</h3>",
    )


@main_bp.route("/performance/self-review", methods=["GET", "POST"], endpoint="sp1_self_review")
@main_bp.route("/performans/stratejik/oz-degerlendirme", methods=["GET", "POST"], endpoint="sp1_self_review_tr")
@login_required
def sp1_self_review():
    if request.method == "POST":
        # SP-1G veri omurgası varsa servis tarafı daha sonra bağlanır.
        flash("Öz değerlendirme kaydı alındı. Bu kayıt otomatik puan üretmez.", "success")
        return redirect(url_for("main.sp1_self_review"))

    return safe_render(
        "strategic_performance/self_review_form.html",
        fallback_html="<h3>Öz Değerlendirme</h3>",
    )


@main_bp.route("/performance/kpi/ai-analysis", endpoint="sp1_ai_kpi_analysis")
@main_bp.route("/performans/stratejik/ai-kpi-analiz", endpoint="sp1_ai_kpi_analysis_tr")
@login_required
def sp1_ai_kpi_analysis():
    if not _is_top_or_manager():
        return _access_denied()
    return safe_render(
        "strategic_performance/ai_kpi_analysis.html",
        fallback_html="<h3>KPI Analiz Merkezi</h3>",
    )

# BYS360_MAINTENANCE_10E_SIDEBAR_ROLE_GUARDS_IMPORTED
