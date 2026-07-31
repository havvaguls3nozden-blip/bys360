from __future__ import annotations

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app.route_support import menu_key_required

from .mail_engine import send_executive_summary_email
from .service import build_executive_summary_payload

executive_summary_bp = Blueprint(
    "executive_summary",
    __name__,
    url_prefix="/dashboard",
    template_folder="../templates",
)

# BYS360_P13B_AUTH002_FIX: bu ucu view hicbir backend yetkilendirmesi olmadan
# kayitliydi (Phase 13B AUTH-002, confirmed anonim read + test-mail write).
# "executive_summary" menu anahtari zaten menu_registry.py icinde yalniz
# sistem yoneticisi ailesine kilitli (_BYS360_EXEC_ADMIN_ONLY_ROLES); canonical
# menu_key_required decorator'i bu canli politikayi backend'de de zorunlu kilar.


@executive_summary_bp.get("/yonetici-ozeti")
@menu_key_required("executive_summary")
def yonetici_ozeti():
    payload = build_executive_summary_payload(report_type="screen")
    return render_template("executive_summary/yonetici_ozeti.html", payload=payload)


@executive_summary_bp.get("/yonetici-ozeti/data")
@menu_key_required("executive_summary")
def yonetici_ozeti_data():
    payload = build_executive_summary_payload(report_type=request.args.get("type") or "screen")
    return jsonify(payload)


@executive_summary_bp.post("/yonetici-ozeti/test-mail")
@menu_key_required("executive_summary")
def yonetici_ozeti_test_mail():
    report_type = request.form.get("type") or request.args.get("type") or "morning"
    result = send_executive_summary_email(report_type=report_type, manual=True)
    if request.headers.get("Accept", "").startswith("application/json"):
        return jsonify(result), (200 if result.get("ok") else 500)
    if result.get("ok"):
        flash("Yönetici özeti test e-postası başarıyla gönderildi.", "success")
    else:
        flash("Yönetici özeti test e-postası gönderilemedi. Mail loglarını kontrol edin.", "danger")
    return redirect(url_for("executive_summary.yonetici_ozeti"))
