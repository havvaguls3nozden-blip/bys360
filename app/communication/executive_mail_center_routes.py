from __future__ import annotations

from flask import abort, flash, redirect, render_template, request
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.services.executive_mail_center import (
    DEFAULT_TASKS,
    get_mail_tasks,
    get_recent_mail_logs,
    get_scheduled_task_statuses,
    get_selected_recipients,
    list_users,
    run_task_script,
    save_mail_tasks,
    save_recipients,
)

def _can_manage_exec_mail_center() -> bool:
    if not getattr(current_user, "is_authenticated", False):
        return False
    role = (getattr(current_user, "role", "") or "").lower()
    username = (getattr(current_user, "username", "") or "").lower()
    return bool(
        getattr(current_user, "is_admin", False)
        or "admin" in role
        or "sistem" in role
        or username in {"admin", "superadmin"}
    )

def _require_exec_mail_center() -> None:
    if not _can_manage_exec_mail_center():
        abort(403)

def _context(**extra):
    tasks = get_mail_tasks()
    recipients = get_selected_recipients()
    ctx = {
        "tasks": tasks,
        "recipients": recipients,
        "recipient_count": len(recipients),
        "logs": get_recent_mail_logs(30),
        "task_statuses": get_scheduled_task_statuses(),
        "users": list_users(request.args.get("q", "")),
        "q": request.args.get("q", ""),
    }
    ctx.update(extra)
    return ctx

@main_bp.route("/executive-summary/daily-weather-mail", methods=["GET", "POST"])
@main_bp.route("/yonetici-ozeti/gunluk-hava-maili", methods=["GET", "POST"])
@login_required
def executive_mail_center_home():
    _require_exec_mail_center()
    return render_template("executive_summary/executive_mail_center.html", **_context(active_tab="overview"))

@main_bp.route("/executive-summary/mail-center/tasks", methods=["GET", "POST"])
@login_required
def executive_mail_center_tasks():
    _require_exec_mail_center()
    if request.method == "POST":
        tasks = []
        for t in DEFAULT_TASKS:
            key = t["key"]
            tasks.append({
                **t,
                "enabled": "1" if request.form.get(f"{key}_enabled") else "0",
                "time": request.form.get(f"{key}_time") or t["default_time"],
                "subject": request.form.get(f"{key}_subject") or t["title"],
            })
        save_mail_tasks(tasks)
        flash("Otomatik mail görevleri kaydedildi.", "success")
        return redirect("/executive-summary/mail-center/tasks")
    return render_template("executive_summary/executive_mail_tasks.html", **_context(active_tab="tasks"))

@main_bp.route("/executive-summary/mail-center/recipients", methods=["GET", "POST"])
@login_required
def executive_mail_center_recipients():
    _require_exec_mail_center()
    if request.method == "POST":
        ids = request.form.getlist("recipient_user_ids")
        save_recipients(ids)
        flash("Mail alıcı listesi güncellendi.", "success")
        return redirect("/executive-summary/mail-center/recipients")
    return render_template("executive_summary/executive_mail_recipients.html", **_context(active_tab="recipients"))

@main_bp.route("/executive-summary/mail-center/logs", methods=["GET"])
@login_required
def executive_mail_center_logs():
    _require_exec_mail_center()
    return render_template("executive_summary/executive_mail_logs.html", **_context(active_tab="logs"))

@main_bp.route("/executive-summary/mail-center/scheduled-jobs", methods=["GET"])
@login_required
def executive_mail_center_scheduled_jobs():
    _require_exec_mail_center()
    return render_template("executive_summary/executive_mail_scheduled_jobs.html", **_context(active_tab="jobs"))

@main_bp.route("/executive-summary/mail-center/test-send", methods=["GET", "POST"])
@login_required
def executive_mail_center_test_send():
    _require_exec_mail_center()
    result = None
    if request.method == "POST":
        script = request.form.get("script") or "scripts/communication/send_daily_weather_personnel_mail.py"
        dry_run = bool(request.form.get("dry_run"))
        result = run_task_script(script, dry_run=dry_run)
        flash("Test gönderimi çalıştırıldı." if result.get("ok") else "Test gönderiminde hata oluştu.", "success" if result.get("ok") else "danger")
    return render_template("executive_summary/executive_mail_test.html", **_context(active_tab="test", result=result))
