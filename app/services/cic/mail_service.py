"""Canonical CIC mail dispatch and recipient service."""

from __future__ import annotations

import logging
import time
from typing import Any

from flask import current_app

import app.services.cic.template_service as _template_service
from app.extensions import db
from app.models import User
from app.services.cic.config_context import (
    _dumps_json,
    _now,
    ensure_defaults,
    get_config,
    get_setting,
    set_setting,
)
from app.services.cic.task_contract import BASE_KEY, TASK_DEFINITIONS

try:
    from app.services.mail_core import create_mail_log, send_email as _mail_core_send_email
except Exception:  # pragma: no cover
    create_mail_log = None  # type: ignore[assignment]
    _mail_core_send_email = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)
_CIC_V40_CELEBRATION_TASKS = {
    "staff_birthday",
    "work_anniversary",
    "special_day",
}

__all__ = [
    "_cic_phase5_mail_health",
    "_cic_phase6_missing_email_count",
    "_cic_v11_bool",
    "_cic_v11_clean_header",
    "_cic_v11_get_setting_value",
    "_cic_v11_mail_settings",
    "_cic_v11_normalize_email",
    "_cic_v11_send_email_direct",
    "_recipients_for_task",
    "_recipients_for_task_base",
    "_send_task_base",
    "get_recipients",
    "send_task",
]


def _cic_v11_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return bool(default)
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "on", "yes", "evet", "tls", "ssl"}:
        return True
    if normalized in {
        "0",
        "false",
        "off",
        "no",
        "hayir",
        "hayır",
        "none",
        "null",
    }:
        return False
    return bool(default)


def _cic_v11_clean_header(value: Any) -> str:
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()


def _cic_v11_normalize_email(value: Any) -> str:
    email = _cic_v11_clean_header(value).strip().strip(",;")
    if not email or "@" not in email or " " in email:
        return ""
    return email


def _app_config() -> Any:
    try:
        return getattr(current_app, "config", {})
    except Exception:
        return {}


def get_recipients() -> dict[str, Any]:
    from app.services.cic.query_service import _active_staff_users, _users_by_ids

    cfg = get_config()
    managers = _users_by_ids(cfg["manager_recipient_ids"])
    if cfg["staff_recipient_mode"] == "all_active":
        staff = _active_staff_users()
    else:
        staff = _users_by_ids(cfg["staff_recipient_ids"])
    return {
        "managers": managers,
        "staff": staff,
        "staff_mode": cfg["staff_recipient_mode"],
    }


def _recipients_for_task_base(task_key: str, override_users: list[User] | None = None) -> list[User]:
    if override_users is not None:
        return override_users
    group = TASK_DEFINITIONS[task_key]["recipient_group"]
    rec = get_recipients()
    return rec["managers"] if group == "managers" else rec["staff"]


def _cic_v11_get_setting_value(keys: Any, default: Any = "") -> Any:
    cfg = _app_config()
    for key in keys or []:
        try:
            value = cfg.get(key) if hasattr(cfg, "get") else None
            if value is not None and str(value).strip() != "":
                return value
        except Exception as exc:
            logger.debug("CIC config read skipped for %s: %s", key, exc)

    for key in keys or []:
        try:
            value = get_setting(str(key), "")
            if value is not None and str(value).strip() != "":
                return value
        except Exception as exc:
            logger.debug("CIC setting read skipped for %s: %s", key, exc)

    aliases: list[str] = []
    for key in keys or []:
        text = str(key).lower()
        aliases.extend([text, text.replace("_", "."), text.replace("_", "-")])
    for key in aliases:
        try:
            value = get_setting(key, "")
            if value is not None and str(value).strip() != "":
                return value
        except Exception as exc:
            logger.debug("CIC alias setting read skipped for %s: %s", key, exc)
    return default


def _cic_v11_mail_settings() -> dict[str, Any]:
    server = _cic_v11_get_setting_value(["MAIL_SERVER", "SMTP_SERVER", "mail_server", "smtp_server", "corporate_information_center.mail_server", "corporate_information_center.smtp_server"], "")
    port = _cic_v11_get_setting_value(["MAIL_PORT", "SMTP_PORT", "mail_port", "smtp_port", "corporate_information_center.mail_port", "corporate_information_center.smtp_port"], 587)
    username = _cic_v11_get_setting_value(["MAIL_USERNAME", "SMTP_USERNAME", "mail_username", "smtp_username", "corporate_information_center.mail_username", "corporate_information_center.smtp_username"], "")
    password = _cic_v11_get_setting_value(["MAIL_PASSWORD", "SMTP_PASSWORD", "mail_password", "smtp_password", "corporate_information_center.mail_password", "corporate_information_center.smtp_password"], "")
    sender = _cic_v11_get_setting_value(["MAIL_DEFAULT_SENDER", "SMTP_SENDER", "MAIL_SENDER", "mail_default_sender", "mail_sender", "smtp_sender", "corporate_information_center.mail_sender", "corporate_information_center.smtp_sender"], "") or username
    use_tls = _cic_v11_bool(_cic_v11_get_setting_value(["MAIL_USE_TLS", "SMTP_USE_TLS", "mail_use_tls", "smtp_use_tls", "corporate_information_center.mail_use_tls"], True), True)
    use_ssl = _cic_v11_bool(_cic_v11_get_setting_value(["MAIL_USE_SSL", "SMTP_USE_SSL", "mail_use_ssl", "smtp_use_ssl", "corporate_information_center.mail_use_ssl"], False), False)
    suppress = _cic_v11_bool(_cic_v11_get_setting_value(["MAIL_SUPPRESS_SEND", "mail_suppress_send", "corporate_information_center.mail_suppress_send"], False), False)
    try:
        port = int(str(port).strip())
    except Exception:
        logger.exception("CIC mail port setting could not be parsed")
        port = 587
    return {
        "server": str(server or "").strip(),
        "port": port,
        "username": str(username or "").strip(),
        "password": password or "",
        "sender": str(sender or "").strip(),
        "use_tls": bool(use_tls),
        "use_ssl": bool(use_ssl),
        "suppress_send": bool(suppress),
    }


def _cic_v11_send_email_direct(to_email, subject, body):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    settings = _cic_v11_mail_settings()
    target = _cic_v11_normalize_email(to_email)
    sender = _cic_v11_normalize_email(settings.get("sender"))
    subject_line = _cic_v11_clean_header(subject)

    if settings.get("suppress_send"):
        return True, "MAIL_SUPPRESS_SEND aktif: gerçek gönderim yapılmadı."
    if not settings.get("server"):
        return False, "MAIL_SERVER / SMTP_SERVER sistem ayarı bulunamadı."
    if not sender:
        return False, "MAIL_DEFAULT_SENDER / SMTP_SENDER sistem ayarı bulunamadı veya geçersiz."
    if not target:
        return False, "Alıcı e-posta adresi geçersiz ya da boş."
    if not subject_line:
        return False, "Mail konusu boş bırakılamaz."

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = target
    msg["Subject"] = subject_line
    msg.attach(MIMEText((body or "").strip() or "BYS360 bildirimi", "plain", "utf-8"))

    try:
        smtp: smtplib.SMTP
        if settings.get("use_ssl"):
            smtp = smtplib.SMTP_SSL(settings["server"], settings["port"], timeout=30)
        else:
            smtp = smtplib.SMTP(settings["server"], settings["port"], timeout=30)
        with smtp as server:
            server.ehlo()
            if settings.get("use_tls") and not settings.get("use_ssl"):
                server.starttls()
                server.ehlo()
            if settings.get("username") and settings.get("password"):
                server.login(settings["username"], settings["password"])
            server.sendmail(sender, [target], msg.as_string())
        return True, "Mail başarıyla gönderildi."
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        try:
            current_app.logger.warning(
                "Kurumsal Bilgilendirme mail gönderim hatası | to=%s | server=%s:%s | detail=%s",
                target, settings.get("server"), settings.get("port"), detail,
            )
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1453")
            pass
        return False, detail


def _recipients_for_task(
    task_key: str,
    override_users: list[User] | None = None,
) -> list[User]:
    if override_users is not None:
        return override_users
    if task_key in {"staff_birthday", "work_anniversary"}:
        from app.services.cic.celebration_service import (
            _cic_v40_anniversary_users,
            _cic_v40_birthday_users,
        )

        if task_key == "staff_birthday":
            return _cic_v40_birthday_users()
        return _cic_v40_anniversary_users()
    if task_key == "special_day":
        from app.services.cic.query_service import _cic_v40_special_day_users

        return _cic_v40_special_day_users()
    return _recipients_for_task_base(task_key, override_users)


def _send_task_base(task_key: str, *, dry_run: bool = False, override_users=None, actor_user_id: int | None = None):
    ensure_defaults(actor_user_id=actor_user_id)
    if task_key not in TASK_DEFINITIONS:
        return {"ok": False, "message": "Bilinmeyen görev.", "task_key": task_key}

    cfg = get_config()
    task_cfg = cfg["tasks"].get(task_key, {})
    if not task_cfg.get("enabled", False) and not dry_run:
        return {"ok": False, "skipped": True, "message": "Görev pasif.", "task_key": task_key}

    raw_users = _recipients_for_task(task_key, override_users)
    users = [u for u in raw_users if _cic_v11_normalize_email(getattr(u, "email", None))]
    missing_mail = max(0, len(raw_users) - len(users))
    tmpl = _template_service.get_template(task_key)
    started = time.time()
    ok_count = 0
    fail_count = 0
    errors = []
    sent_preview = []
    mail_settings = _cic_v11_mail_settings()

    for user in users:
        email = _cic_v11_normalize_email(getattr(user, "email", ""))
        subject = _template_service._render_template_text(tmpl["subject"], user, task_key)
        body = _template_service._render_template_text(tmpl["body"], user, task_key)
        if dry_run:
            ok, msg = True, "Kuru çalışma: gönderim yapılmadı."
        else:
            ok, msg = _cic_v11_send_email_direct(email, subject, body)

        if ok:
            ok_count += 1
        else:
            fail_count += 1
            errors.append(f"{email}: {msg}")
        sent_preview.append(email)

        try:
            if create_mail_log is not None:
                create_mail_log(
                    mail_type=f"corporate_information_{task_key}",
                    recipient_email=email,
                    subject=subject,
                    body=body,
                    user_id=getattr(user, "id", None),
                    sent_by_id=actor_user_id,
                    is_success=ok,
                    error_message=None if ok else msg,
                )
        except Exception as log_exc:
            try:
                current_app.logger.warning("Kurumsal Bilgilendirme mail log yazılamadı | detail=%s", log_exc)
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1510")
                pass

    elapsed = round(time.time() - started, 2)
    status = f"Başarılı: {ok_count}, Hatalı: {fail_count}, Eksik e-posta: {missing_mail}, Süre: {elapsed} sn"
    tasks = cfg["tasks"]
    tasks.setdefault(task_key, {}).update({
        "last_status": status,
        "last_run_at": _now().strftime("%d.%m.%Y %H:%M"),
        "last_error": errors[0] if errors else "",
    })
    set_setting(f"{BASE_KEY}.tasks", _dumps_json(tasks), label="Kurumsal bilgilendirme görevleri", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_status", f"{TASK_DEFINITIONS[task_key]['label']}: {status}", label="Son kurumsal bilgilendirme durumu", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_error", errors[0] if errors else "", label="Son kurumsal bilgilendirme hatası", value_type="text", actor_user_id=actor_user_id)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    label = TASK_DEFINITIONS[task_key]["label"]
    if dry_run:
        message = f"{label} kuru çalışma tamamlandı: {len(users)} alıcı kontrol edildi, {missing_mail} eksik e-posta."
    else:
        message = f"{label} çalıştırıldı: {ok_count} başarılı, {fail_count} hatalı."
        if missing_mail:
            message += f" Eksik e-posta: {missing_mail}."
        if errors:
            message += f" İlk hata: {errors[0]}"

    return {
        "ok": fail_count == 0,
        "message": message,
        "task_key": task_key,
        "task_label": label,
        "dry_run": dry_run,
        "recipient_count": len(users),
        "success_count": ok_count,
        "fail_count": fail_count,
        "missing_mail_count": missing_mail,
        "errors": errors[:20],
        "recipients": sent_preview[:20],
        "elapsed_seconds": elapsed,
        "mail_server": mail_settings.get("server"),
        "mail_port": mail_settings.get("port"),
        "mail_sender": mail_settings.get("sender"),
    }


def send_task(task_key: str, *, dry_run: bool = False, override_users: list[User] | None = None, actor_user_id: int | None = None) -> dict[str, Any]:
    """Send CIC mail task through one explicit public layer.

    Preserves current runtime behavior:
    - V11 direct mail implementation is handled by _send_task_base.
    - V40 celebration system notifications are applied after successful base execution path.
    """
    users_for_notification: list[User] = []
    if task_key in _CIC_V40_CELEBRATION_TASKS and override_users is None:
        users_for_notification = list(_recipients_for_task(task_key) or [])
    elif task_key in _CIC_V40_CELEBRATION_TASKS and override_users is not None:
        users_for_notification = list(override_users or [])

    result = _send_task_base(
        task_key,
        dry_run=dry_run,
        override_users=override_users,
        actor_user_id=actor_user_id,
    )

    if task_key in _CIC_V40_CELEBRATION_TASKS and not dry_run:
        from app.services.cic.cic_context import _cic_v40_create_system_notifications

        result["system_notification_count"] = _cic_v40_create_system_notifications(
            task_key,
            users_for_notification,
            actor_user_id=actor_user_id,
        )

    return result


def _cic_phase5_mail_health() -> dict[str, Any]:
    cfg = _app_config()
    server = (cfg.get("MAIL_SERVER") or cfg.get("SMTP_SERVER") or "").strip() if hasattr(cfg, "get") else ""
    sender = (cfg.get("MAIL_DEFAULT_SENDER") or cfg.get("DEFAULT_MAIL_SENDER") or cfg.get("MAIL_USERNAME") or "").strip() if hasattr(cfg, "get") else ""
    username = (cfg.get("MAIL_USERNAME") or "").strip() if hasattr(cfg, "get") else ""
    suppressed = bool(cfg.get("MAIL_SUPPRESS_SEND", False)) if hasattr(cfg, "get") else False
    problems: list[str] = []
    if not server:
        problems.append("Mail sunucusu tanımlı değil")
    if not sender:
        problems.append("Gönderici e-posta tanımlı değil")
    if suppressed:
        problems.append("Mail gönderimi bastırılmış durumda")
    if _mail_core_send_email is None:
        problems.append("Mail gönderim servisi yüklenemedi")
    status = "ok" if not problems else ("warn" if server or sender else "danger")
    return {
        "status": status,
        "server_defined": bool(server),
        "sender_defined": bool(sender),
        "username_defined": bool(username),
        "suppressed": suppressed,
        "service_loaded": _mail_core_send_email is not None,
        "label": "Hazır" if status == "ok" else "Kontrol gerekli",
        "problems": problems,
    }


def _cic_phase6_missing_email_count(users: list[Any]) -> int:
    total = 0
    for user in users or []:
        try:
            if not (getattr(user, "email", "") or "").strip():
                total += 1
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("BYS360 kurumsal bilgi merkezi isleminde hata yakalandi")
            total += 1
    return total
