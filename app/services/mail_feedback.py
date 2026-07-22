from __future__ import annotations

from app.services.mail_core import (
    utc_now,
    smtplib,
    Counter,
    datetime,
    timedelta,
    MIMEMultipart,
    MIMEText,
    Any,
    current_app,
    sa_inspect,
    db,
    EvaluationAssignment,
    FeedbackMeeting,
    FeedbackRequest,
    MailLog,
    PerformanceEvaluation,
    PerformancePeriod,
    SystemSetting,
    User,
    logging,
    logger,
    PERFORMANCE_REMINDER_MAIL_TYPE,
    PERFORMANCE_RESULT_MAIL_TYPE,
    PERFORMANCE_TEST_MAIL_TYPE,
    REMINDER_COOLDOWN_HOURS,
    MAIL_TEMPLATE_GROUP_KEY,
    MAIL_TEMPLATE_DEFINITIONS,
    PERFORMANCE_MAIL_AUTOMATION_ENABLED_KEY,
    PERFORMANCE_MAIL_AUTOMATION_RUN_HOUR_KEY,
    PERFORMANCE_MAIL_AUTOMATION_MIN_PENDING_KEY,
    PERFORMANCE_MAIL_AUTOMATION_MAX_PERIODS_KEY,
    PERFORMANCE_MAIL_AUTOMATION_FORCE_SEND_KEY,
    PERFORMANCE_MAIL_AUTOMATION_ONLY_ACTIVE_KEY,
    PERFORMANCE_MAIL_AUTOMATION_ONLY_WINDOW_KEY,
    PERFORMANCE_MAIL_AUTOMATION_INTERVAL_KEY,
    AUTOMATION_SETTING_DEFINITIONS,
    get_smtp_settings,
    _clean_header_value,
    _coerce_bool_text,
    _coerce_int_text,
    _normalize_email_address,
    _mask_email_address,
    _manager_display_name,
    _employee_display_name,
    _manager_level_label,
    _body_preview,
    _system_settings_ready,
    _render_text_template,
    _get_mail_template_setting_value,
    _upsert_template_setting,
    get_mail_template_definition,
    get_mail_template_content,
    get_performance_mail_template_rows,
    save_performance_mail_templates,
    create_mail_log,
    send_email,
)

def send_feedback_request_mail(feedback: FeedbackRequest) -> dict[str, Any]:
    employee = feedback.employee
    recipients: list[User] = []
    seen_emails: set[str] = set()

    for manager in [feedback.level_1_manager, feedback.level_2_manager, feedback.level_3_manager]:
        email = _normalize_email_address(getattr(manager, "email", "") or "") if manager else ""
        if manager and email and email not in seen_emails:
            recipients.append(manager)
            seen_emails.add(email)

    success_count = 0
    failed_count = 0
    failed_items = []

    for manager in recipients:
        subject = "BYS360 Performans Geri Bildirim Talebi"
        body = f"""Sayın {manager.ad} {manager.soyad},

{employee.ad} {employee.soyad} tarafından performans değerlendirmesine ilişkin geri bildirim talebi oluşturulmuştur.

Personel: {employee.ad} {employee.soyad}
Sicil No: {employee.sicil_no or '-'}
Dönem: {feedback.period.title if feedback.period else '-'}
Durum: {feedback.status}

Talep Açıklaması:
{feedback.reason or '-'}

Lütfen BYS360 sistemine giriş yaparak talebi inceleyiniz.

BYS360
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
"""
        ok, message = send_email(manager.email, subject, body)

        if ok:
            success_count += 1
        else:
            failed_count += 1
            failed_items.append({
                "manager_id": manager.id,
                "manager_name": f"{manager.ad} {manager.soyad}",
                "email": manager.email,
                "error": message,
            })

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_items": failed_items,
    }


def send_feedback_response_mail(feedback: FeedbackRequest) -> tuple[bool, str]:
    employee = feedback.employee

    if not employee or not _normalize_email_address(getattr(employee, "email", "") or ""):
        return False, "Personel e-posta adresi bulunamadı."

    subject = "BYS360 Geri Bildirim Talebinize Yanıt"
    body = f"""Sayın {employee.ad} {employee.soyad},

Performans değerlendirme geri bildirim talebiniz güncellenmiştir.

Durum: {feedback.status}

Yanıt:
{feedback.response or 'Henüz yanıt girilmedi.'}

BYS360 sistemi üzerinden detayları görüntüleyebilirsiniz.

BYS360
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
"""

    return send_email(employee.email, subject, body)


def send_feedback_meeting_created_mail(meeting: FeedbackMeeting) -> dict[str, Any]:
    employee = meeting.employee
    manager = meeting.manager
    feedback = meeting.feedback_request

    recipients: list[tuple[str, str]] = []
    seen_emails: set[str] = set()

    def _append(email: str, display_name: str) -> None:
        normalized = _normalize_email_address(email)
        if normalized and normalized not in seen_emails:
            recipients.append((normalized, display_name))
            seen_emails.add(normalized)

    if employee and employee.email:
        _append(employee.email, f"{employee.ad} {employee.soyad}")

    if feedback:
        for mgr in [feedback.level_1_manager, feedback.level_2_manager, feedback.level_3_manager]:
            if mgr and mgr.email:
                _append(mgr.email, f"{mgr.ad} {mgr.soyad}")

    meeting_date = meeting.meeting_date.strftime("%d.%m.%Y") if meeting.meeting_date else "-"
    meeting_start = meeting.meeting_start.strftime("%H:%M") if meeting.meeting_start else "-"
    meeting_end = meeting.meeting_end.strftime("%H:%M") if meeting.meeting_end else "-"

    subject = "BYS360 Geri Bildirim Görüşmesi Planlandı"

    success_count = 0
    failed_count = 0
    failed_items: list[dict[str, Any]] = []

    for to_email, display_name in recipients:
        body = f"""Sayın {display_name},

BYS360 kapsamında bir geri bildirim görüşmesi planlanmıştır.

Personel: {f'{employee.ad} {employee.soyad}' if employee else '-'}
Planlayan Yönetici: {f'{manager.ad} {manager.soyad}' if manager else '-'}
Tarih: {meeting_date}
Saat: {meeting_start} - {meeting_end}
Toplantı Türü: {meeting.meeting_type or '-'}
Konum / Bağlantı: {meeting.location or '-'}
Durum: {meeting.status or '-'}

Toplantı Notu:
{meeting.note or 'Not girilmedi.'}

BYS360
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
"""
        ok, message = send_email(to_email, subject, body)

        if ok:
            success_count += 1
        else:
            failed_count += 1
            failed_items.append({
                "email": to_email,
                "name": display_name,
                "error": message,
            })

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_items": failed_items,
    }


def send_feedback_meeting_status_update_mail(meeting: FeedbackMeeting) -> dict[str, Any]:
    employee = meeting.employee
    manager = meeting.manager
    feedback = meeting.feedback_request

    recipients: list[tuple[str, str]] = []
    seen_emails: set[str] = set()

    def _append(email: str, display_name: str) -> None:
        normalized = _normalize_email_address(email)
        if normalized and normalized not in seen_emails:
            recipients.append((normalized, display_name))
            seen_emails.add(normalized)

    if employee and employee.email:
        _append(employee.email, f"{employee.ad} {employee.soyad}")

    if manager and manager.email:
        _append(manager.email, f"{manager.ad} {manager.soyad}")

    if feedback:
        for mgr in [feedback.level_1_manager, feedback.level_2_manager, feedback.level_3_manager]:
            if mgr and mgr.email:
                _append(mgr.email, f"{mgr.ad} {mgr.soyad}")

    meeting_date = meeting.meeting_date.strftime("%d.%m.%Y") if meeting.meeting_date else "-"
    meeting_start = meeting.meeting_start.strftime("%H:%M") if meeting.meeting_start else "-"
    meeting_end = meeting.meeting_end.strftime("%H:%M") if meeting.meeting_end else "-"

    status_label_map = {
        "planlandi": "Planlandı",
        "tamamlandi": "Tamamlandı",
        "ertelendi": "Ertelendi",
        "iptal_edildi": "İptal Edildi",
    }
    status_label = status_label_map.get(meeting.status, meeting.status or "-")

    subject = f"BYS360 Randevu Durumu Güncellendi | {status_label}"

    success_count = 0
    failed_count = 0
    failed_items: list[dict[str, Any]] = []

    for to_email, display_name in recipients:
        body = f"""Sayın {display_name},

BYS360 kapsamında planlanan geri bildirim görüşmesinin durumu güncellenmiştir.

Personel: {f'{employee.ad} {employee.soyad}' if employee else '-'}
Yönetici: {f'{manager.ad} {manager.soyad}' if manager else '-'}
Tarih: {meeting_date}
Saat: {meeting_start} - {meeting_end}
Toplantı Türü: {meeting.meeting_type or '-'}
Konum / Bağlantı: {meeting.location or '-'}
Yeni Durum: {status_label}

Güncel Not:
{meeting.note or 'Not girilmedi.'}

BYS360
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
"""
        ok, message = send_email(to_email, subject, body)

        if ok:
            success_count += 1
        else:
            failed_count += 1
            failed_items.append({
                "email": to_email,
                "name": display_name,
                "error": message,
            })

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_items": failed_items,
    }


# Mail geri bildirim yardımcıları kurumsal bildirim akışı için kullanılır.

__all__ = [
    "annotations",
    "utc_now",
    "smtplib",
    "Counter",
    "datetime",
    "timedelta",
    "MIMEMultipart",
    "MIMEText",
    "Any",
    "current_app",
    "sa_inspect",
    "db",
    "EvaluationAssignment",
    "FeedbackMeeting",
    "FeedbackRequest",
    "MailLog",
    "PerformanceEvaluation",
    "PerformancePeriod",
    "SystemSetting",
    "User",
    "logging",
    "logger",
    "PERFORMANCE_REMINDER_MAIL_TYPE",
    "PERFORMANCE_RESULT_MAIL_TYPE",
    "PERFORMANCE_TEST_MAIL_TYPE",
    "REMINDER_COOLDOWN_HOURS",
    "MAIL_TEMPLATE_GROUP_KEY",
    "MAIL_TEMPLATE_DEFINITIONS",
    "PERFORMANCE_MAIL_AUTOMATION_ENABLED_KEY",
    "PERFORMANCE_MAIL_AUTOMATION_RUN_HOUR_KEY",
    "PERFORMANCE_MAIL_AUTOMATION_MIN_PENDING_KEY",
    "PERFORMANCE_MAIL_AUTOMATION_MAX_PERIODS_KEY",
    "PERFORMANCE_MAIL_AUTOMATION_FORCE_SEND_KEY",
    "PERFORMANCE_MAIL_AUTOMATION_ONLY_ACTIVE_KEY",
    "PERFORMANCE_MAIL_AUTOMATION_ONLY_WINDOW_KEY",
    "PERFORMANCE_MAIL_AUTOMATION_INTERVAL_KEY",
    "AUTOMATION_SETTING_DEFINITIONS",
    "get_smtp_settings",
    "_clean_header_value",
    "_coerce_bool_text",
    "_coerce_int_text",
    "_normalize_email_address",
    "_mask_email_address",
    "_manager_display_name",
    "_employee_display_name",
    "_manager_level_label",
    "_body_preview",
    "_system_settings_ready",
    "_render_text_template",
    "_get_mail_template_setting_value",
    "_upsert_template_setting",
    "get_mail_template_definition",
    "get_mail_template_content",
    "get_performance_mail_template_rows",
    "save_performance_mail_templates",
    "create_mail_log",
    "send_email",
    "send_feedback_request_mail",
    "send_feedback_response_mail",
    "send_feedback_meeting_created_mail",
    "send_feedback_meeting_status_update_mail",
]
