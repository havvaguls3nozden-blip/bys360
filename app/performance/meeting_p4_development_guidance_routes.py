from __future__ import annotations

import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import PerformanceEvaluation
from app.route_registry import main_bp
from app.route_support import manager_required

# BYS360_STUB_AI_V60_DEVELOPMENT_IMPORT
from app.services.ai.stub_panel_bridge import attach_development_guidance_ai_panel

# /BYS360_STUB_AI_V60_DEVELOPMENT_IMPORT
from app.services.performance.meeting_p4_development_guidance import (
    build_p4_development_guidance_context,
    can_manage_development_guidance,
    run_p4_development_guidance,
    save_development_recommendation,
)

logger = logging.getLogger(__name__)

try:
    from app.performance.phase10_development_guidance_ui import (
        build_phase10_meeting_development_context,
        save_phase10_recommendation_from_request,
    )
    PHASE10_UI_AVAILABLE = True
except Exception as exc:  # pragma: no cover - opsiyonel UI yükleme güvenliği
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    PHASE10_UI_AVAILABLE = False
    PHASE10_UI_IMPORT_ERROR = exc

    def build_phase10_meeting_development_context():
        context = build_p4_development_guidance_context()
        context["ui_warning"] = "Gelişim rehberi arayüz bileşeni yüklenemedi; temel rehber görünümü açıldı."
        return context

    def save_phase10_recommendation_from_request():
        raise RuntimeError(f"Gelişim rehberi kayıt bileşeni yüklenemedi: {PHASE10_UI_IMPORT_ERROR}")


@main_bp.route("/performance/meeting-development/faz10", methods=["GET", "POST"], endpoint="performance_meeting_p4_development_guidance")
@main_bp.route("/performans/toplanti-gelistirme/faz10-gelisim-rehberi", methods=["GET", "POST"], endpoint="performance_meeting_p4_development_guidance_tr")
@login_required
@manager_required
def performance_meeting_p4_development_guidance():
    if request.method == "POST":
        try:
            save_phase10_recommendation_from_request()
            flash("Gelişim rehberi kaydı alındı.", "success")
        except Exception as exc:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            flash(f"Gelişim rehberi kaydı alınamadı: {exc}", "warning")
        return redirect(request.path)

    context = build_phase10_meeting_development_context()
    # BYS360_STUB_AI_V60_DEVELOPMENT_CONTEXT_ATTACH
    context = attach_development_guidance_ai_panel(context)
    # /BYS360_STUB_AI_V60_DEVELOPMENT_CONTEXT_ATTACH
    return render_template('performance/meeting_development_faz10.html', **context)

@main_bp.route("/performance/meeting-development/faz10/apply", methods=["POST"], endpoint="performance_meeting_p4_development_guidance_apply")
@main_bp.route("/performans/toplanti-gelistirme/faz10-gelisim-rehberi/uygula", methods=["POST"], endpoint="performance_meeting_p4_development_guidance_apply_tr")
@login_required
@manager_required
def performance_meeting_p4_development_guidance_apply():
    result = run_p4_development_guidance(actor_user_id=getattr(current_user, "id", None))
    flash(result.message, "success" if result.ok else "warning")
    for warning in result.warnings or []:
        flash(warning, "warning")
    return redirect(url_for("main.performance_meeting_p4_development_guidance"))


@main_bp.route("/performance/scorecard/<int:evaluation_id>/development-note", methods=["POST"], endpoint="performance_scorecard_development_note_save")
@login_required
@manager_required
def performance_scorecard_development_note_save(evaluation_id: int):
    evaluation = PerformanceEvaluation.query.get_or_404(evaluation_id)
    if not can_manage_development_guidance(current_user):
        flash("Gelişim önerisi kaydetme yetkiniz bulunmamaktadır.", "danger")
        return redirect(url_for("main.performance_scorecard_detail", evaluation_id=evaluation.id, period_id=evaluation.period_id or ""))

    recommendation_type = (request.form.get("recommendation_type") or "guidance_note").strip()
    title = (request.form.get("title") or "").strip()
    recommendation_text = (request.form.get("recommendation_text") or "").strip()
    visibility_scope = (request.form.get("visibility_scope") or "authorized_scope").strip()
    is_required = request.form.get("is_required") == "on"

    if not recommendation_text:
        flash("Gelişim önerisi veya güçlü yön notu açıklaması zorunludur.", "warning")
        return redirect(url_for("main.performance_scorecard_detail", evaluation_id=evaluation.id, period_id=evaluation.period_id or ""))

    inserted_id = save_development_recommendation(
        evaluation=evaluation,
        created_by=getattr(current_user, "id", None),
        recommendation_type=recommendation_type,
        title=title,
        recommendation_text=recommendation_text,
        visibility_scope=visibility_scope,
        is_required=is_required,
        source="manual_scorecard",
        status="draft",
    )
    if inserted_id:
        db.session.commit()
        flash("Gelişim önerisi / güçlü yön notu karneye bağlandı.", "success")
    else:
        db.session.rollback()
        flash("Gelişim önerisi kaydedilemedi. Lütfen açıklama alanını kontrol edin.", "warning")
    return redirect(url_for("main.performance_scorecard_detail", evaluation_id=evaluation.id, period_id=evaluation.period_id or ""))

# BYS360_PHASE11_DEVELOPMENT_GUIDANCE_ROUTE_POST_READY: Gelişim Rehberi kayıt formu GET/POST uyumlu hale getirildi.
