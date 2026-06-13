from __future__ import annotations


from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.route_registry import main_bp
from app.services.executive_mail_center_v2 import dashboard_context, ensure_defaults, run_task, save_location_from_form, save_recipients_from_form, save_tasks_from_form

ADMIN_ROLES = {"admin", "sistem_yoneticisi", "system_admin", "super_admin"}

def _role_text() -> str:
    return " ".join(str(getattr(current_user, a, "") or "").lower() for a in ("role", "role_key", "user_role", "authority_level"))

def _can_manage() -> bool:
    if not getattr(current_user, "is_authenticated", False): return False
    if getattr(current_user, "is_admin", False) or getattr(current_user, "is_superuser", False): return True
    return any(r in _role_text() for r in ADMIN_ROLES)

def _require() -> None:
    if not _can_manage(): abort(403)

@main_bp.route("/executive-summary/mail-center")
@main_bp.route("/executive-summary/daily-weather-mail")
@main_bp.route("/yonetici-ozeti/mail-center")
@login_required
def executive_mail_center_home():
    _require(); ensure_defaults(getattr(current_user, "id", None))
    return render_template("executive_summary/mail_center/overview.html", **dashboard_context(request.args.get("q")))

@main_bp.route("/executive-summary/mail-center/tasks", methods=["GET", "POST"])
@login_required
def executive_mail_center_tasks():
    _require(); ensure_defaults(getattr(current_user, "id", None))
    if request.method == "POST":
        save_tasks_from_form(request.form, getattr(current_user, "id", None))
        flash("Mail görevleri kaydedildi.", "success")
        return redirect(url_for("main.executive_mail_center_tasks"))
    return render_template("executive_summary/mail_center/tasks.html", **dashboard_context(request.args.get("q")))

@main_bp.route("/executive-summary/mail-center/recipients", methods=["GET", "POST"])
@login_required
def executive_mail_center_recipients():
    _require(); ensure_defaults(getattr(current_user, "id", None))
    if request.method == "POST":
        save_recipients_from_form(request.form, getattr(current_user, "id", None))
        flash("Alıcı listeleri kaydedildi.", "success")
        return redirect(url_for("main.executive_mail_center_recipients"))
    return render_template("executive_summary/mail_center/recipients.html", **dashboard_context(request.args.get("q")))

@main_bp.route("/executive-summary/mail-center/location", methods=["POST"])
@login_required
def executive_mail_center_location():
    _require(); save_location_from_form(request.form, getattr(current_user, "id", None))
    flash("Hava durumu konumu kaydedildi.", "success")
    return redirect(request.referrer or url_for("main.executive_mail_center_home"))

@main_bp.route("/executive-summary/mail-center/test", methods=["GET", "POST"])
@login_required
def executive_mail_center_test():
    _require(); ensure_defaults(getattr(current_user, "id", None)); result = None
    if request.method == "POST":
        result = run_task(request.form.get("task_key") or "staff_morning", dry_run=request.form.get("dry_run") == "1", actor_user_id=getattr(current_user, "id", None), only_user_id=getattr(current_user, "id", None) if request.form.get("only_me") == "1" else None)
        flash("Test çalıştırıldı. Sonuç aşağıda gösteriliyor.", "success" if result.get("ok") else "warning")
    return render_template("executive_summary/mail_center/test.html", result=result, **dashboard_context(request.args.get("q")))

@main_bp.route("/executive-summary/mail-center/send/<task_key>", methods=["POST"])
@login_required
def executive_mail_center_send_task(task_key):
    _require(); result = run_task(task_key, dry_run=False, actor_user_id=getattr(current_user, "id", None))
    flash(f"{result.get('task_title', task_key)} çalıştırıldı. Başarılı: {result.get('sent',0)}, Hatalı: {result.get('failed',0)}", "success" if result.get("ok") else "warning")
    return redirect(url_for("main.executive_mail_center_test"))

@main_bp.route("/executive-summary/mail-center/logs")
@login_required
def executive_mail_center_logs():
    _require(); return render_template("executive_summary/mail_center/logs.html", **dashboard_context(request.args.get("q")))

@main_bp.route("/executive-summary/mail-center/scheduler")
@login_required
def executive_mail_center_scheduler():
    _require(); return render_template("executive_summary/mail_center/scheduler.html", **dashboard_context(request.args.get("q")))
