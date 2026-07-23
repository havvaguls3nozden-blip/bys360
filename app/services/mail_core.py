from __future__ import annotations

import logging
import smtplib
from collections import Counter
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from flask import current_app
from sqlalchemy import inspect as sa_inspect

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import (
    EvaluationAssignment,
    FeedbackMeeting,
    FeedbackRequest,
    MailLog,
    PerformanceEvaluation,
    PerformancePeriod,
    SystemSetting,
    User,
)

logger = logging.getLogger(__name__)


PERFORMANCE_REMINDER_MAIL_TYPE = "performance_assignment_reminder"
PERFORMANCE_RESULT_MAIL_TYPE = "performance_results_published"
PERFORMANCE_TEST_MAIL_TYPE = "performance_mail_test"
REMINDER_COOLDOWN_HOURS = 12
MAIL_TEMPLATE_GROUP_KEY = "performance_mail"

MAIL_TEMPLATE_DEFINITIONS: dict[str, dict[str, Any]] = {
    PERFORMANCE_REMINDER_MAIL_TYPE: {
        "label": "Görev hatırlatma maili",
        "subject_key": "performance.mail_template.reminder.subject",
        "body_key": "performance.mail_template.reminder.body",
        "default_subject": "BYS360 Görev Hatırlatması | {period_title}",
        "default_body": """Sayın {manager_name},

BYS360 Performans Değerlendirme sürecinde üzerinizde bekleyen görev bulunmaktadır.

Aktif dönem: {period_title}
Bekleyen görev sayısı: {pending_count}
Seviye dağılımı: {level_breakdown}
Gecikmiş görev sayısı: {overdue_count}
Yaklaşan görev sayısı: {due_soon_count}
En eski bekleyen görev yaşı: {oldest_pending_days} gün

Görev bekleyen personeller:
{employee_list}

Lütfen sisteme giriş yaparak değerlendirmenizi tamamlayınız.

Sistem bağlantısı:
{login_url}

İyi çalışmalar dileriz.
{app_name}
{institution_name}
""",
        "placeholders": [
            "{manager_name}",
            "{period_title}",
            "{pending_count}",
            "{level_breakdown}",
            "{overdue_count}",
            "{due_soon_count}",
            "{oldest_pending_days}",
            "{employee_list}",
            "{login_url}",
            "{app_name}",
            "{institution_name}",
        ],
    },
    PERFORMANCE_RESULT_MAIL_TYPE: {
        "label": "Sonuç yayın bilgilendirme maili",
        "subject_key": "performance.mail_template.result.subject",
        "body_key": "performance.mail_template.result.body",
        "default_subject": "BYS360 Değerlendirme Sonucu Yayımlandı | {period_title}",
        "default_body": """Sayın {recipient_name},

BYS360 Performans Değerlendirme sonucu yayımlanmıştır.

Dönem: {period_title}
Personel: {employee_name}
Sicil No: {sicil_no}
Nihai Puan: {final_score}
Yayın Tarihi: {publish_date}

Detayları görüntülemek için:
{login_url}

Bu e-posta bilgilendirme amaçlıdır.
{app_name}
{institution_name}
""",
        "placeholders": [
            "{recipient_name}",
            "{period_title}",
            "{employee_name}",
            "{sicil_no}",
            "{final_score}",
            "{publish_date}",
            "{login_url}",
            "{app_name}",
            "{institution_name}",
        ],
    },
}

PERFORMANCE_MAIL_AUTOMATION_ENABLED_KEY = "performance.mail_automation.enabled"
PERFORMANCE_MAIL_AUTOMATION_RUN_HOUR_KEY = "performance.mail_automation.run_hour"
PERFORMANCE_MAIL_AUTOMATION_MIN_PENDING_KEY = "performance.mail_automation.min_pending_count"
PERFORMANCE_MAIL_AUTOMATION_MAX_PERIODS_KEY = "performance.mail_automation.max_periods"
PERFORMANCE_MAIL_AUTOMATION_FORCE_SEND_KEY = "performance.mail_automation.force_send"
PERFORMANCE_MAIL_AUTOMATION_ONLY_ACTIVE_KEY = "performance.mail_automation.only_active_periods"
PERFORMANCE_MAIL_AUTOMATION_ONLY_WINDOW_KEY = "performance.mail_automation.only_during_window"
PERFORMANCE_MAIL_AUTOMATION_INTERVAL_KEY = "performance.mail_automation.interval_hours"

AUTOMATION_SETTING_DEFINITIONS: dict[str, dict[str, Any]] = {
    PERFORMANCE_MAIL_AUTOMATION_ENABLED_KEY: {
        "label": "Performans mail otomasyonu aktif",
        "default": "0",
        "value_type": "bool",
        "description": "1 olduğunda otomasyon scripti reminder çalıştırır.",
    },
    PERFORMANCE_MAIL_AUTOMATION_RUN_HOUR_KEY: {
        "label": "Performans mail otomasyon çalışma saati",
        "default": "9",
        "value_type": "int",
        "description": "Windows Görev Zamanlayıcı veya cron için önerilen saat bilgisi (24 saat formatı).",
    },
    PERFORMANCE_MAIL_AUTOMATION_MIN_PENDING_KEY: {
        "label": "Performans mail otomasyonu minimum bekleyen görev",
        "default": "1",
        "value_type": "int",
        "description": "Bu eşikten az bekleyen görevi olan yöneticiye otomatik reminder gönderilmez.",
    },
    PERFORMANCE_MAIL_AUTOMATION_MAX_PERIODS_KEY: {
        "label": "Performans mail otomasyonu maksimum dönem",
        "default": "3",
        "value_type": "int",
        "description": "Tek çalıştırmada işlenecek maksimum aktif dönem sayısı.",
    },
    PERFORMANCE_MAIL_AUTOMATION_FORCE_SEND_KEY: {
        "label": "Performans mail otomasyonu bekleme süresini geçersiz saysın",
        "default": "0",
        "value_type": "bool",
        "description": "1 ise cooldown dolmasa bile reminder gönderilir.",
    },
    PERFORMANCE_MAIL_AUTOMATION_ONLY_ACTIVE_KEY: {
        "label": "Performans mail otomasyonu sadece aktif dönemleri işlesin",
        "default": "1",
        "value_type": "bool",
        "description": "1 ise yalnızca aktif işaretli dönemler taranır.",
    },
    PERFORMANCE_MAIL_AUTOMATION_ONLY_WINDOW_KEY: {
        "label": "Performans mail otomasyonu sadece değerlendirme penceresinde çalışsın",
        "default": "1",
        "value_type": "bool",
        "description": "1 ise evaluation start/end aralığı dışında reminder gönderilmez.",
    },
    PERFORMANCE_MAIL_AUTOMATION_INTERVAL_KEY: {
        "label": "Performans mail otomasyonu bekleme saati",
        "default": str(REMINDER_COOLDOWN_HOURS),
        "value_type": "int",
        "description": "Otomatik runner için reminder cooldown süresi.",
    },
}


def get_smtp_settings() -> dict[str, Any]:
    return {
        "host": (current_app.config.get("MAIL_SERVER", "") or "").strip(),
        "port": int(current_app.config.get("MAIL_PORT", 587)),
        "username": (current_app.config.get("MAIL_USERNAME", "") or "").strip(),
        "password": current_app.config.get("MAIL_PASSWORD", "") or "",
        "use_tls": bool(current_app.config.get("MAIL_USE_TLS", True)),
        "default_sender": (current_app.config.get("MAIL_DEFAULT_SENDER", "") or "").strip(),
        "app_base_url": (current_app.config.get("APP_BASE_URL", "http://127.0.0.1:8000") or "http://127.0.0.1:8000").rstrip("/"),
        "app_name": (current_app.config.get("APP_NAME", "BYS360") or "BYS360").strip() or "BYS360",
        "institution_name": (
            current_app.config.get("MAIL_INSTITUTION_NAME", "Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı")
            or "Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı"
        ).strip(),
    }


def _clean_header_value(value: str) -> str:
    cleaned = (value or "").replace("\r", " ").replace("\n", " ").strip()
    return cleaned

def _coerce_bool_text(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "on", "yes", "evet"}:
        return True
    if normalized in {"0", "false", "off", "no", "hayir", "hayır"}:
        return False
    return bool(default)


def _coerce_int_text(value: Any, default: int, *, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        parsed = int(str(value).strip())
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/mail_core.py | line=210")
        parsed = int(default)
    if minimum is not None:
        parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed
def _normalize_email_address(value: str) -> str:
    email = _clean_header_value(value).strip().strip(",;")
    if not email or "@" not in email or " " in email:
        return ""
    return email

def _mask_email_address(value: str | None) -> str:
    email = _normalize_email_address(value or "")
    if not email:
        return "-"
    local, _, domain = email.partition("@")
    local_mask = (local[:1] or "*") + "***" if len(local) <= 2 else local[:2] + "***"
    return f"{local_mask}@{domain}"


def _manager_display_name(manager: User | None) -> str:
    if not manager:
        return "-"
    return f"{getattr(manager, 'ad', '')} {getattr(manager, 'soyad', '')}".strip() or getattr(manager, 'email', None) or f"Kullanıcı #{getattr(manager, 'id', '-') }"


def _employee_display_name(user: User | None) -> str:
    if not user:
        return "-"
    return f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}".strip() or getattr(user, 'sicil_no', None) or f"Personel #{getattr(user, 'id', '-') }"


def _manager_level_label(level: Any) -> str:
    try:
        return f"{int(level)}. Amir"
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/mail_core.py | line=250")
        return "Belirsiz seviye"


def _body_preview(body: str, limit: int = 1000) -> str:
    return (body or "").strip()[:limit]


def _system_settings_ready() -> bool:
    try:
        return bool(sa_inspect(db.engine).has_table("system_settings"))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/mail_core.py | line=261")
        return False


def _render_text_template(template: str, context: dict[str, Any]) -> str:
    rendered = template or ""
    for key, value in context.items():
        rendered = rendered.replace("{" + str(key) + "}", "-" if value is None else str(value))
    return rendered


def _get_mail_template_setting_value(setting_key: str, default: str) -> str:
    if not _system_settings_ready():
        return default
    try:
        row = SystemSetting.query.filter_by(setting_key=setting_key).first()
        value = (row.value_text or "").strip() if row else ""
        return value or default
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/mail_core.py | line=279")
        return default


def _upsert_template_setting(*, setting_key: str, label: str, value_text: str, description: str, updated_by_user_id: int | None) -> None:
    row = SystemSetting.query.filter_by(setting_key=setting_key).first()
    if row is None:
        row = SystemSetting(
            setting_key=setting_key,
            group_key=MAIL_TEMPLATE_GROUP_KEY,
            label=label,
            value_text=value_text,
            value_type="string",
            description=description,
            is_active=True,
            updated_by_user_id=updated_by_user_id,
        )
        db.session.add(row)
        return
    row.group_key = MAIL_TEMPLATE_GROUP_KEY
    row.label = label
    row.value_text = value_text
    row.value_type = "string"
    row.description = description
    row.is_active = True
    row.updated_by_user_id = updated_by_user_id


def get_mail_template_definition(mail_type: str) -> dict[str, Any]:
    return MAIL_TEMPLATE_DEFINITIONS.get(mail_type, {})


def get_mail_template_content(mail_type: str) -> dict[str, Any]:
    definition = get_mail_template_definition(mail_type)
    if not definition:
        return {
            "mail_type": mail_type,
            "label": mail_type,
            "subject": "",
            "body": "",
            "default_subject": "",
            "default_body": "",
            "placeholders": [],
            "subject_key": "",
            "body_key": "",
        }
    return {
        "mail_type": mail_type,
        "label": definition["label"],
        "subject": _get_mail_template_setting_value(definition["subject_key"], definition["default_subject"]),
        "body": _get_mail_template_setting_value(definition["body_key"], definition["default_body"]),
        "default_subject": definition["default_subject"],
        "default_body": definition["default_body"],
        "placeholders": list(definition.get("placeholders") or []),
        "subject_key": definition["subject_key"],
        "body_key": definition["body_key"],
    }


def get_performance_mail_template_rows() -> list[dict[str, Any]]:
    return [get_mail_template_content(key) for key in (PERFORMANCE_REMINDER_MAIL_TYPE, PERFORMANCE_RESULT_MAIL_TYPE)]


def save_performance_mail_templates(payload_by_mail_type: dict[str, dict[str, str]], *, actor_user_id: int | None = None) -> int:
    if not _system_settings_ready():
        raise RuntimeError("system_settings tablosu bulunamadı. Önce flask db upgrade çalıştırın.")

    changed = 0
    for mail_type, definition in MAIL_TEMPLATE_DEFINITIONS.items():
        payload = payload_by_mail_type.get(mail_type) or {}
        subject_value = (payload.get("subject") or definition["default_subject"]).strip() or definition["default_subject"]
        body_value = (payload.get("body") or definition["default_body"]).rstrip() or definition["default_body"]

        current = get_mail_template_content(mail_type)
        if current.get("subject") != subject_value:
            changed += 1
        if current.get("body") != body_value:
            changed += 1

        _upsert_template_setting(
            setting_key=definition["subject_key"],
            label=f"{definition['label']} konu şablonu",
            value_text=subject_value,
            description=f"{definition['label']} için e-posta konu şablonu",
            updated_by_user_id=actor_user_id,
        )
        _upsert_template_setting(
            setting_key=definition["body_key"],
            label=f"{definition['label']} içerik şablonu",
            value_text=body_value,
            description=f"{definition['label']} için e-posta gövde şablonu",
            updated_by_user_id=actor_user_id,
        )

    return changed


def create_mail_log(
    *,
    mail_type: str,
    recipient_email: str,
    subject: str,
    body: str,
    period_id: int | None = None,
    user_id: int | None = None,
    feedback_request_id: int | None = None,
    sent_by_id: int | None = None,
    is_success: bool = True,
    error_message: str | None = None,
) -> MailLog:
    log = MailLog(
        mail_type=mail_type,
        related_period_id=period_id,
        related_user_id=user_id,
        related_feedback_request_id=feedback_request_id,
        recipient_email=_normalize_email_address(recipient_email) or recipient_email,
        subject=_clean_header_value(subject),
        body_preview=_body_preview(body),
        sent_by_id=sent_by_id,
        is_success=bool(is_success),
        error_message=(error_message or "").strip() or None,
        sent_at=utc_now(),
    )
    db.session.add(log)
    return log


def send_email(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    settings = get_smtp_settings()
    target = _normalize_email_address(to_email)
    subject_line = _clean_header_value(subject)

    if not settings["host"]:
        return False, "MAIL_SERVER ayarı bulunamadı."
    if not settings["default_sender"]:
        return False, "MAIL_DEFAULT_SENDER ayarı bulunamadı."
    if not target:
        return False, "Alıcı e-posta adresi geçersiz ya da boş."
    if not subject_line:
        return False, "Mail konusu boş bırakılamaz."

    msg = MIMEMultipart()
    msg["From"] = settings["default_sender"]
    msg["To"] = target
    msg["Subject"] = subject_line
    msg.attach(MIMEText((body or "").strip() or "BYS360 bildirimi", "plain", "utf-8"))

    try:
        with smtplib.SMTP(settings["host"], settings["port"], timeout=30) as server:
            server.ehlo()
            if settings["use_tls"]:
                server.starttls()
                server.ehlo()
            if settings["username"] and settings["password"]:
                server.login(settings["username"], settings["password"])
            server.sendmail(settings["default_sender"], [target], msg.as_string())
        return True, "Mail başarıyla gönderildi."
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/mail_core.py | line=436")
        return False, str(exc)

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
]
