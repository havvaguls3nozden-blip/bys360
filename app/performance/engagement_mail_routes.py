from __future__ import annotations

import logging

from flask import current_app, flash, redirect, request, send_file, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import PerformancePeriod, User
from app.route_registry import main_bp
from app.route_support import admin_required, safe_render
from app.services.ai.dashboard_panels import build_mail_reminder_ai_panel
from app.services.mail_service import (
    PERFORMANCE_REMINDER_MAIL_TYPE,
    PERFORMANCE_RESULT_MAIL_TYPE,
    build_assignment_reminder_email,
    build_failed_mail_dashboard,
    build_mail_system_health_snapshot,
    build_pending_assignment_manager_dashboard,
    build_performance_mail_history_rows,
    build_reminder_activity_dashboard,
    get_failed_performance_mail_logs,
    get_performance_mail_automation_settings,
    get_performance_mail_template_rows,
    retry_failed_performance_mail_logs,
    retry_mail_log,
    run_performance_mail_automation,
    save_performance_mail_automation_settings,
    save_performance_mail_templates,
    send_bulk_assignment_reminders,
    send_selected_assignment_reminders,
    send_single_assignment_reminder,
    send_test_performance_mail,
)
from app.services.performance.hardening_service import (
    build_period_download_name,
    humanize_export_exception,
)

from .mail_helpers import build_styled_excel_bytes

"""Performans mail hatırlatma ve otomasyon route ailesi."""
logger = logging.getLogger(__name__)

@main_bp.route("/performance/mail-reminders/automation-settings", methods=["POST"])
@login_required
@admin_required
def performance_mail_automation_settings():
    period_id = request.form.get("period_id", type=int)
    payload = {
        "enabled": request.form.get("automation_enabled"),
        "force_send": request.form.get("automation_force_send"),
        "only_active_periods": request.form.get("automation_only_active_periods"),
        "only_during_window": request.form.get("automation_only_during_window"),
        "run_hour": request.form.get("automation_run_hour"),
        "reminder_interval_hours": request.form.get("automation_reminder_interval_hours"),
        "min_pending_count": request.form.get("automation_min_pending_count"),
        "max_periods": request.form.get("automation_max_periods"),
    }
    try:
        changed = save_performance_mail_automation_settings(payload, actor_user_id=getattr(current_user, "id", None))
        db.session.commit()
        flash(f"Otomatik hatırlatma ayarları kaydedildi. Değişen alan sayısı: {changed}", "success")
    except Exception as exc:
        current_app.logger.exception("Mail otomasyon ayarları kaydedilemedi: %s", exc)
        db.session.rollback()
        flash(f"Mail otomasyon ayarları kaydedilemedi: {exc}", "danger")

    if period_id:
        return redirect(url_for("main.performance_mail_reminders", period_id=period_id))
    return redirect(url_for("main.performance_mail_reminders"))


@main_bp.route("/performance/mail-reminders/run-automation", methods=["POST"])
@login_required
@admin_required
def performance_run_mail_automation():
    period_id = request.form.get("period_id", type=int)
    force_send = str(request.form.get("force_send") or "").strip().lower() in {"1", "true", "on", "yes", "evet"}
    dry_run = str(request.form.get("dry_run") or "").strip().lower() in {"1", "true", "on", "yes", "evet"}
    try:
        result = run_performance_mail_automation(
            actor_user_id=getattr(current_user, "id", None),
            period_id=period_id,
            force=force_send,
            dry_run=dry_run,
        )
        if dry_run:
            flash(
                f"Otomasyon önizlemesi üretildi. Dönem: {result.get('period_count', 0)}, yönetici: {result.get('total_managers', 0)}, bekleyen görev: {result.get('total_pending', 0)}.",
                "info",
            )
        else:
            db.session.commit()
            flash(
                f"Otomasyon çalıştı. Dönem: {result.get('period_count', 0)}, yönetici: {result.get('total_managers', 0)}, başarılı: {result.get('success_count', 0)}, başarısız: {result.get('failed_count', 0)}, atlanan: {result.get('skipped_count', 0)}",
                "success" if int(result.get("failed_count", 0) or 0) == 0 else "warning",
            )
    except Exception as exc:
        current_app.logger.exception("Mail otomasyonu çalıştırılamadı: %s", exc)
        db.session.rollback()
        flash(f"Mail otomasyonu çalıştırılamadı: {exc}", "danger")

    if period_id:
        return redirect(url_for("main.performance_mail_reminders", period_id=period_id))
    return redirect(url_for("main.performance_mail_reminders"))


@main_bp.route("/performance/mail-reminders/history-export/<int:period_id>")
@login_required
@admin_required
def performance_mail_history_export(period_id):
    period = db.session.get(PerformancePeriod, period_id)
    if not period:
        flash("Dönem bulunamadı.", "danger")
        return redirect(url_for("main.performance_mail_reminders"))

    try:
        rows = build_performance_mail_history_rows(period_id=period.id, limit=5000)
        excel_rows = [
            [
                row.get("sent_at").strftime("%d.%m.%Y %H:%M") if row.get("sent_at") else "-",
                row.get("mail_type") or "-",
                row.get("user_name") or "-",
                row.get("recipient_email") or "-",
                row.get("subject") or "-",
                "Başarılı" if row.get("is_success") else "Başarısız",
                row.get("error_message") or "-",
                row.get("sent_by_name") or "-",
            ]
            for row in rows
        ]
        output = build_styled_excel_bytes(
            title="Mail Geçmişi",
            headers=["Gönderim Zamanı", "Mail Türü", "Kullanıcı", "Alıcı", "Konu", "Durum", "Hata", "Gönderen"],
            rows=excel_rows,
            widths={"A": 22, "B": 22, "C": 28, "D": 30, "E": 48, "F": 14, "G": 36, "H": 28},
        )

        return send_file(
            output,
            as_attachment=True,
            download_name=build_period_download_name("bys360_performans_mail_gecmisi", period, "xlsx"),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as exc:
        current_app.logger.exception("Performans mail geçmişi export hatası: %s", exc)
        flash(f"Mail geçmişi dışa aktarma sırasında hata oluştu: {humanize_export_exception(exc)}", "danger")
        return redirect(url_for("main.performance_mail_reminders", period_id=period.id))

@main_bp.route("/performance/mail-reminders/test-mail", methods=["POST"])
@login_required
@admin_required
def performance_send_test_mail():
    period_id = request.form.get("period_id", type=int)
    target_email = (request.form.get("test_email") or getattr(current_user, "email", "") or "").strip()
    try:
        result = send_test_performance_mail(target_email, actor_user_id=getattr(current_user, "id", None))
        if result.get("ok"):
            db.session.commit()
            flash(f"Test maili gönderildi: {result.get('recipient_email')}", "success")
        else:
            db.session.rollback()
            flash(result.get("message") or "Test maili gönderilemedi.", "danger")
    except Exception as exc:
        current_app.logger.exception("Performans test maili gönderilemedi: %s", exc)
        db.session.rollback()
        flash(f"Test maili gönderilemedi: {exc}", "danger")

    if period_id:
        return redirect(url_for("main.performance_mail_reminders", period_id=period_id))
    return redirect(url_for("main.performance_mail_reminders"))


@main_bp.route("/performance/mail-reminders")
@login_required
@admin_required
def performance_mail_reminders():
    periods = (
        PerformancePeriod.query
        .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
        .all()
    )

    selected_period_id = request.args.get("period_id", type=int)
    selected_period = db.session.get(PerformancePeriod, selected_period_id) if selected_period_id else None

    manager_summary = []
    manager_dashboard = {}
    blocked_manager_rows = []
    total_pending = 0
    preview_subject = None
    preview_body = None
    failed_mail_logs = []
    history_rows = []
    reminder_activity = {}
    failed_mail_dashboard = {}
    automation_settings = get_performance_mail_automation_settings()
    automation_preview = run_performance_mail_automation(period_id=selected_period_id, dry_run=True) if selected_period_id else run_performance_mail_automation(dry_run=True)
    mail_health = build_mail_system_health_snapshot(period_id=selected_period.id if selected_period else None)

    if selected_period:
        manager_dashboard = build_pending_assignment_manager_dashboard(
            selected_period.id,
            reminder_interval_hours=int(automation_settings.get("reminder_interval_hours") or 12),
        )
        manager_summary = list(manager_dashboard.get("eligible_rows") or [])
        blocked_manager_rows = list(manager_dashboard.get("blocked_rows") or [])
        total_pending = int(manager_dashboard.get("total_pending") or 0)

        for item in manager_summary:
            manager = item["manager"]
            pending_count = item["count"]
            subject, body = build_assignment_reminder_email(manager, selected_period, pending_count)
            item["preview_subject"] = subject
            item["preview_body"] = body

        if manager_summary:
            preview_subject = manager_summary[0]["preview_subject"]
            preview_body = manager_summary[0]["preview_body"]

        failed_mail_logs = get_failed_performance_mail_logs(period_id=selected_period.id, limit=30)
        history_rows = build_performance_mail_history_rows(period_id=selected_period.id, limit=80)
        reminder_activity = build_reminder_activity_dashboard(selected_period.id, limit=12)
        failed_mail_dashboard = build_failed_mail_dashboard(period_id=selected_period.id, limit=100)
        mail_health = build_mail_system_health_snapshot(period_id=selected_period.id)

    return safe_render(
        "performance_mail_reminders.html",
        "<h3>Mail Hatırlatma Sistemi</h3>",
        periods=periods,
        selected_period=selected_period,
        manager_summary=manager_summary,
        total_pending=total_pending,
        preview_subject=preview_subject,
        preview_body=preview_body,
        failed_mail_logs=failed_mail_logs,
        reminder_mail_type=PERFORMANCE_REMINDER_MAIL_TYPE,
        result_mail_type=PERFORMANCE_RESULT_MAIL_TYPE,
        history_rows=history_rows,
        reminder_activity=reminder_activity,
        failed_mail_dashboard=failed_mail_dashboard,
        automation_settings=automation_settings,
        automation_preview=automation_preview,
        manager_dashboard=manager_dashboard,
        blocked_manager_rows=blocked_manager_rows,
        mail_health=mail_health,
        default_test_email=(getattr(current_user, "email", "") or "").strip(),
        ai_reminder_panel=build_mail_reminder_ai_panel(
            manager_summary=manager_summary,
            total_pending=total_pending,
            selected_period=selected_period,
        ),
    )


@main_bp.route("/performance/mail-reminders/send/<int:period_id>", methods=["POST"])
@login_required
@admin_required
def performance_send_mail_reminders(period_id):
    period = db.session.get(PerformancePeriod, period_id)
    if not period:
        flash("Dönem bulunamadı.", "danger")
        return redirect(url_for("main.performance_mail_reminders"))

    try:
        force_send = str(request.form.get('force_send') or '').strip().lower() in {'1', 'true', 'on', 'yes', 'evet'}
        result = send_bulk_assignment_reminders(period, actor_user_id=current_user.id, force=force_send)
        db.session.commit()
        if result["failed_count"] == 0 and result.get('skipped_count', 0) == 0:
            flash(f"Hatırlatma mailleri gönderildi. Toplam yönetici: {result['total_managers']}, başarılı: {result['success_count']}", "success")
        elif result["failed_count"] == 0:
            flash(f"Gönderim tamamlandı. Başarılı: {result['success_count']}, bekleme süresi nedeniyle atlanan: {result.get('skipped_count', 0)}", "warning")
        else:
            flash(f"Mail gönderimi tamamlandı. Başarılı: {result['success_count']}, başarısız: {result['failed_count']}, atlanan: {result.get('skipped_count', 0)}", "warning")
    except Exception as exc:
        current_app.logger.exception('Toplu hatırlatma gönderimi başarısız: %s', exc)
        db.session.rollback()
        flash(f"Mail gönderimi sırasında hata oluştu: {exc}", "danger")

    return redirect(url_for("main.performance_mail_reminders", period_id=period_id))


@main_bp.route("/performance/mail-reminders/send-selected/<int:period_id>", methods=["POST"])
@login_required
@admin_required
def performance_send_selected_mail_reminders(period_id):
    period = db.session.get(PerformancePeriod, period_id)
    if not period:
        flash("Dönem bulunamadı.", "danger")
        return redirect(url_for("main.performance_mail_reminders"))

    manager_ids = request.form.getlist('manager_ids')
    if not manager_ids:
        flash('Önce en az bir yönetici seçin.', 'warning')
        return redirect(url_for('main.performance_mail_reminders', period_id=period_id))

    force_send = str(request.form.get('force_send') or '').strip().lower() in {'1', 'true', 'on', 'yes', 'evet'}
    try:
        result = send_selected_assignment_reminders(period, manager_ids, actor_user_id=current_user.id, force=force_send)
        db.session.commit()
        flash(
            f"Seçili yöneticiler için gönderim tamamlandı. Başarılı: {result.get('success_count', 0)}, başarısız: {result.get('failed_count', 0)}, atlanan: {result.get('skipped_count', 0)}",
            'success' if result.get('failed_count', 0) == 0 else 'warning',
        )
    except Exception as exc:
        current_app.logger.exception('Seçili hatırlatma gönderimi başarısız: %s', exc)
        db.session.rollback()
        flash(f'Mail gönderimi sırasında hata oluştu: {exc}', 'danger')

    return redirect(url_for('main.performance_mail_reminders', period_id=period_id))


@main_bp.route("/performance/mail-reminders/templates", methods=["GET", "POST"])
@login_required
@admin_required
def performance_mail_templates():
    if request.method == 'POST':
        payload = {
            PERFORMANCE_REMINDER_MAIL_TYPE: {
                'subject': request.form.get('reminder_subject'),
                'body': request.form.get('reminder_body'),
            },
            PERFORMANCE_RESULT_MAIL_TYPE: {
                'subject': request.form.get('result_subject'),
                'body': request.form.get('result_body'),
            },
        }
        try:
            changed = save_performance_mail_templates(payload, actor_user_id=getattr(current_user, 'id', None))
            db.session.commit()
            flash(f'Mail şablonları kaydedildi. Değişen alan sayısı: {changed}', 'success')
        except Exception as exc:
            current_app.logger.exception('Mail şablonu kaydı başarısız: %s', exc)
            db.session.rollback()
            flash(str(exc), 'danger')
        return redirect(url_for('main.performance_mail_templates'))

    template_rows = get_performance_mail_template_rows()
    return safe_render(
        'performance_mail_templates.html',
        '<h3>Mail Şablonları</h3>',
        template_rows=template_rows,
    )


@main_bp.route("/performance/mail-reminders/retry-failed/<int:period_id>", methods=["POST"])
@login_required
@admin_required
def performance_retry_failed_mail_logs(period_id):
    period = db.session.get(PerformancePeriod, period_id)
    if not period:
        flash('Dönem bulunamadı.', 'danger')
        return redirect(url_for('main.performance_mail_reminders'))

    try:
        result = retry_failed_performance_mail_logs(period_id=period.id, actor_user_id=getattr(current_user, 'id', None), limit=50)
        db.session.commit()
        flash(
            f"Başarısız mailler yeniden denendi. Toplam: {result.get('total_logs', 0)}, başarılı: {result.get('success_count', 0)}, başarısız: {result.get('failed_count', 0)}",
            'success' if result.get('failed_count', 0) == 0 else 'warning',
        )
    except Exception as exc:
        current_app.logger.exception('Başarısız mailleri yeniden deneme başarısız: %s', exc)
        db.session.rollback()
        flash(f'Yeniden deneme sırasında hata oluştu: {exc}', 'danger')

    return redirect(url_for('main.performance_mail_reminders', period_id=period_id))


@main_bp.route("/performance/mail-reminders/retry-log/<int:mail_log_id>", methods=["POST"])
@login_required
@admin_required
def performance_retry_single_mail_log(mail_log_id):
    period_id = request.form.get('period_id', type=int)
    try:
        result = retry_mail_log(mail_log_id, actor_user_id=getattr(current_user, 'id', None))
        db.session.commit()
        if result.get('ok'):
            flash('Mail yeniden gönderildi.', 'success')
        else:
            flash(result.get('message') or 'Mail yeniden gönderilemedi.', 'danger')
    except Exception as exc:
        current_app.logger.exception('Tekil mail yeniden deneme başarısız: %s', exc)
        db.session.rollback()
        flash(f'Yeniden deneme sırasında hata oluştu: {exc}', 'danger')

    return redirect(url_for('main.performance_mail_reminders', period_id=period_id))

@main_bp.route("/performance/mail-reminders/send-single/<int:period_id>/<int:manager_id>", methods=["POST"])
@login_required
@admin_required
def performance_send_single_mail_reminder(period_id, manager_id):
    """Tek bir yöneticiye seçili dönem için hatırlatma gönderir."""
    period = db.session.get(PerformancePeriod, period_id)
    manager = db.session.get(User, manager_id)
    if not period or not manager:
        flash("Dönem veya yönetici bulunamadı.", "danger")
        return redirect(url_for("main.performance_mail_reminders", period_id=period_id))

    force_send = str(request.form.get('force_send') or '').strip().lower() in {'1', 'true', 'on', 'yes', 'evet'}
    try:
        result = send_single_assignment_reminder(period, manager, actor_user_id=current_user.id, force=force_send)
        db.session.commit()
    except Exception as exc:
        current_app.logger.exception('Tekil hatırlatma gönderimi başarısız: %s', exc)
        db.session.rollback()
        flash(f"Mail gönderimi sırasında hata oluştu: {exc}", "danger")
        return redirect(url_for("main.performance_mail_reminders", period_id=period_id))

    if result.get('status') == 'sent':
        flash(f"{manager.ad} {manager.soyad} için hatırlatma maili gönderildi.", "success")
    elif result.get('status') == 'skipped':
        flash(result.get('message') or 'Bu yönetici için bekleme süresi henüz dolmadı.', "warning")
    else:
        flash(f"Mail gönderilemedi: {result.get('message') or 'Bilinmeyen hata'}", "danger")

    return redirect(url_for("main.performance_mail_reminders", period_id=period_id))
