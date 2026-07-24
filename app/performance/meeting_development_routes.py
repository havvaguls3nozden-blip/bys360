from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_development import (
    DEFAULT_SETTINGS,
    add_category,
    add_observation_note,
    add_period_target,
    build_meeting_development_context,
    update_setting,
)


@main_bp.route("/performance/meeting-development", endpoint="performance_meeting_development")
@main_bp.route("/performans/toplanti-gelistirme", endpoint="performance_meeting_development_tr")
@login_required
@manager_required
def performance_meeting_development():
    return render_template("performance/meeting_development.html", **build_meeting_development_context())


@main_bp.route("/performance/meeting-development/settings", methods=["POST"], endpoint="performance_meeting_development_settings")
@login_required
@manager_required
def performance_meeting_development_settings():
    # Faz 3 ile ayar listesi genişledi; yalnızca mevcut formda gönderilen/gönderilmeyen checkbox değerleri güvenli şekilde işlenir.
    for key in DEFAULT_SETTINGS:
        update_setting(key, request.form.get(key) == "on", actor_id=getattr(current_user, "id", None))
    flash("Toplantı kararlarına bağlı performans ayarları güncellendi.", "success")
    return redirect(url_for("main.performance_meeting_development"))


@main_bp.route("/performance/meeting-development/categories", methods=["POST"], endpoint="performance_meeting_development_category")
@login_required
@manager_required
def performance_meeting_development_category():
    name = (request.form.get("category_name") or "").strip()
    if not name:
        flash("Kategori adı zorunludur.", "warning")
        return redirect(url_for("main.performance_meeting_development"))
    add_category(name, request.form.get("description") or "", request.form.get("sort_order", type=int) or 0)
    flash("Personel kategorisi kaydedildi.", "success")
    return redirect(url_for("main.performance_meeting_development"))


@main_bp.route("/performance/meeting-development/period-targets", methods=["POST"], endpoint="performance_meeting_development_target")
@login_required
@manager_required
def performance_meeting_development_target():
    period_id = request.form.get("period_id", type=int)
    if not period_id:
        flash("Dönem seçimi zorunludur.", "warning")
        return redirect(url_for("main.performance_meeting_development"))
    add_period_target(
        period_id,
        (request.form.get("target_type") or "all").strip(),
        (request.form.get("target_value") or "").strip(),
        (request.form.get("notes") or "").strip(),
    )
    flash("Dönem kapsamı kaydedildi.", "success")
    return redirect(url_for("main.performance_meeting_development"))


@main_bp.route("/performance/meeting-development/notes", methods=["POST"], endpoint="performance_meeting_development_note")
@login_required
@manager_required
def performance_meeting_development_note():
    period_id = request.form.get("period_id", type=int)
    employee_id = request.form.get("employee_id", type=int)
    title = (request.form.get("title") or "").strip()
    note = (request.form.get("note") or "").strip()
    if not period_id or not employee_id or not title or not note:
        flash("Dönem, personel, başlık ve not alanları zorunludur.", "warning")
        return redirect(url_for("main.performance_meeting_development"))
    add_observation_note(
        period_id,
        employee_id,
        getattr(current_user, "id", None),
        (request.form.get("note_type") or "general").strip(),
        title,
        note,
        request.form.get("remind_in_evaluation") == "on",
    )
    flash("Ara dönem performans notu kaydedildi.", "success")
    return redirect(url_for("main.performance_meeting_development"))
