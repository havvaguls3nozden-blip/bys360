# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_development import (
    add_legacy_scorecard,
    assign_employee_category,
    build_meeting_faz3_context,
)


@main_bp.route("/performance/meeting-development/faz3", endpoint="performance_meeting_development_faz3")
@main_bp.route("/performans/toplanti-gelistirme/derinlestirme", endpoint="performance_meeting_development_faz3_tr")
@login_required
@manager_required
def performance_meeting_development_faz3():
    return render_template("performance/meeting_development_faz3.html", **build_meeting_faz3_context(current_user))


@main_bp.route("/performance/meeting-development/faz3/category-assignment", methods=["POST"], endpoint="performance_meeting_faz3_category_assignment")
@login_required
@manager_required
def performance_meeting_faz3_category_assignment():
    employee_id = request.form.get("employee_id", type=int)
    category_id = request.form.get("category_id", type=int)
    if not employee_id or not category_id:
        flash("Personel ve kategori seçimi zorunludur.", "warning")
        return redirect(url_for("main.performance_meeting_development_faz3"))
    assign_employee_category(employee_id, category_id, getattr(current_user, "id", None))
    flash("Personel kategori eşleştirmesi kaydedildi.", "success")
    return redirect(url_for("main.performance_meeting_development_faz3"))


@main_bp.route("/performance/meeting-development/faz3/legacy-scorecard", methods=["POST"], endpoint="performance_meeting_faz3_legacy_scorecard")
@login_required
@manager_required
def performance_meeting_faz3_legacy_scorecard():
    employee_id = request.form.get("employee_id", type=int)
    period_year = request.form.get("period_year", type=int)
    period_title = (request.form.get("period_title") or "").strip()
    score_raw = (request.form.get("score_100") or "").strip()
    if not employee_id or not period_year or not period_title:
        flash("Personel, yıl ve dönem başlığı zorunludur.", "warning")
        return redirect(url_for("main.performance_meeting_development_faz3"))
    try:
        score_100 = float(score_raw.replace(",", ".")) if score_raw else None
    except ValueError:
        flash("Puan alanı sayısal olmalıdır.", "warning")
        return redirect(url_for("main.performance_meeting_development_faz3"))
    add_legacy_scorecard(
        employee_id=employee_id,
        period_year=period_year,
        period_title=period_title,
        score_100=score_100,
        category_name=(request.form.get("category_name") or "").strip(),
        unit_name=(request.form.get("unit_name") or "").strip(),
        general_comment=(request.form.get("general_comment") or "").strip(),
        source_note=(request.form.get("source_note") or "").strip(),
        visible_to_employee=request.form.get("is_visible_to_employee") == "on",
        actor_id=getattr(current_user, "id", None),
    )
    flash("Geçmiş karne kaydı arşive eklendi.", "success")
    return redirect(url_for("main.performance_meeting_development_faz3"))
