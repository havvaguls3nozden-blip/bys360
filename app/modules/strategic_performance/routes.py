from __future__ import annotations

# BYS360 SP-1D KPI/Hedef Oluşturma, Listeleme ve Düzenleme Route Katmanı
# SP-1C route yapısının üzerine güvenli şekilde genişletilmiştir.



import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.services.role_guards import can_manage_strategic_targets, can_view_strategic_performance
logger = logging.getLogger(__name__)

try:
    from app.services.sp1c_kpi_dashboard_service import build_sp1c_kpi_dashboard_context
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    build_sp1c_kpi_dashboard_context = None

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

strategic_performance_bp = Blueprint(
    "strategic_performance",
    __name__,
    url_prefix="/performans/stratejik",
)


def _can_view_kpi_dashboard() -> bool:
    return can_view_strategic_performance(current_user)


def _can_manage_targets() -> bool:
    return can_manage_strategic_targets(current_user)


def _access_denied():
    return render_template(
        "strategic_performance/access_denied.html",
        page_title="Erişim Yetkisi Bulunmamaktadır",
    ), 403


@strategic_performance_bp.route("/kpi-dashboard")
@login_required
def kpi_dashboard():
    if not _can_view_kpi_dashboard():
        return _access_denied()
    from app.services.sp3a_kpi_dashboard_live_service import build_sp3a_kpi_dashboard_context
    context = build_sp3a_kpi_dashboard_context(current_user)
    return render_template(
        "strategic_performance/kpi_dashboard.html",
        **context,
    )

@strategic_performance_bp.route("/yetkinlik-kutuphanesi")
@login_required
def competency_library():
    if not _can_view_kpi_dashboard():
        return _access_denied()
    return render_template("strategic_performance/competency_library.html")


@strategic_performance_bp.route("/hedefler")
@login_required
def target_list():
    if not _can_view_kpi_dashboard():
        return _access_denied()
    targets = list_targets_for_user(current_user) if list_targets_for_user else []
    return render_template(
        "strategic_performance/target_list.html",
        page_title="KPI ve Hedef Listesi",
        targets=targets,
        can_manage=_can_manage_targets(),
    )


@strategic_performance_bp.route("/hedefler/yeni", methods=["GET", "POST"])
@login_required
def target_create():
    if not _can_manage_targets():
        return _access_denied()

    if request.method == "POST":
        if create_target_from_form:
            ok, message = create_target_from_form(request.form, current_user)
        else:
            ok, message = False, "Hedef kayıt servisi kullanılamıyor."
        flash(message, "success" if ok else "warning")
        if ok:
            return redirect(url_for("strategic_performance.target_list"))

    context = build_target_form_context(current_user) if build_target_form_context else {}
    return render_template(
        "strategic_performance/target_form.html",
        page_title="Yeni KPI / Hedef Oluştur",
        form_mode="create",
        target={},
        **context,
    )


@strategic_performance_bp.route("/hedefler/<int:target_id>/duzenle", methods=["GET", "POST"])
@login_required
def target_edit(target_id: int):
    if not _can_manage_targets():
        return _access_denied()

    target = get_target_for_edit(target_id, current_user) if get_target_for_edit else None
    if not target:
        flash("Hedef kaydı bulunamadı veya bu kayıt için yetkiniz yok.", "warning")
        return redirect(url_for("strategic_performance.target_list"))

    if request.method == "POST":
        ok, message = update_target_from_form(target_id, request.form, current_user) if update_target_from_form else (False, "Hedef güncelleme servisi kullanılamıyor.")
        flash(message, "success" if ok else "warning")
        if ok:
            return redirect(url_for("strategic_performance.target_list"))

    context = build_target_form_context(current_user) if build_target_form_context else {}
    return render_template(
        "strategic_performance/target_form.html",
        page_title="KPI / Hedef Düzenle",
        form_mode="edit",
        target=target,
        **context,
    )


@strategic_performance_bp.route("/oz-degerlendirme", methods=["GET", "POST"])
@login_required
def self_review():
    if request.method == "POST":
        flash("Öz değerlendirme kaydı alındı. Bu kayıt otomatik puan üretmez.", "success")
        return redirect(url_for("strategic_performance.self_review"))
    return render_template(
        "strategic_performance/self_review_form.html",
        page_title="Öz Değerlendirme",
    )


@strategic_performance_bp.route("/kpi-analiz")
@strategic_performance_bp.route("/ai-kpi-analiz")
@login_required
def ai_kpi_analysis():
    if not _can_view_kpi_dashboard():
        return _access_denied()
    return render_template(
        "strategic_performance/ai_kpi_analysis.html",
        page_title="KPI Analiz Merkezi",
    )


# BYS360_CLAUDE_10E_ROLE_GUARDS_IMPORTED
