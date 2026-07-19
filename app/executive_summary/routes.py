from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash

from .service import build_executive_summary_payload
from .mail_engine import send_executive_summary_email

executive_summary_bp = Blueprint(
    "executive_summary",
    __name__,
    url_prefix="/dashboard",
    template_folder="../templates",
)


@executive_summary_bp.get("/yonetici-ozeti")
def yonetici_ozeti():
    payload = build_executive_summary_payload(report_type="screen")
    return render_template("executive_summary/yonetici_ozeti.html", payload=payload)


@executive_summary_bp.get("/yonetici-ozeti/data")
def yonetici_ozeti_data():
    payload = build_executive_summary_payload(report_type=request.args.get("type") or "screen")
    return jsonify(payload)


@executive_summary_bp.post("/yonetici-ozeti/test-mail")
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
