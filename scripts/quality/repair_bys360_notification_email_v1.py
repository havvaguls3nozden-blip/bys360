from __future__ import annotations

import argparse
import py_compile
import shutil
from datetime import datetime
from pathlib import Path

SERVICE_REL = Path("app/services/notification_mailer.py")
INIT_REL = Path("app/__init__.py")
REGISTRATION_LINE = '    ("app.services.notification_mailer", "register_notification_mailer"),'

SERVICE_CODE = 'from __future__ import annotations\n\nimport logging\nfrom typing import Any\n\nfrom flask import current_app, has_app_context\nfrom sqlalchemy import event, text\nfrom sqlalchemy.orm import Session\n\nfrom app.core.datetime_utils import utc_now\nfrom app.extensions import db\nfrom app.models import Notification\nfrom app.services.mail_core import send_email\n\nlogger = logging.getLogger(__name__)\n\nMAIL_TYPE = "system_notification_alert"\n_INFO_PAYLOADS = "bys360_notification_mail_payloads_v1"\n_INFO_SEEN = "bys360_notification_mail_seen_v1"\n_REGISTERED = False\n\n\ndef _safe_int(value: Any) -> int | None:\n    try:\n        parsed = int(value)\n    except (TypeError, ValueError):\n        return None\n    return parsed if parsed > 0 else None\n\n\ndef _clean(value: Any, *, limit: int = 500) -> str:\n    text_value = str(value or "").replace("\\r", " ").replace("\\n", " ").strip()\n    while "  " in text_value:\n        text_value = text_value.replace("  ", " ")\n    return text_value[:limit]\n\n\ndef _enabled() -> bool:\n    if not has_app_context():\n        return False\n    raw = current_app.config.get("BYS360_NOTIFICATION_EMAILS_ENABLED", True)\n    return str(raw).strip().lower() not in {"0", "false", "off", "hayir", "hayır", "no"}\n\n\ndef _base_url() -> str:\n    if not has_app_context():\n        return ""\n    return str(current_app.config.get("APP_BASE_URL") or current_app.config.get("BASE_URL") or "").rstrip("/")\n\n\ndef _absolute_link(link_url: Any) -> str:\n    link = str(link_url or "").strip()\n    if not link:\n        return _base_url() or "/"\n    if link.startswith("http://") or link.startswith("https://"):\n        return link\n    base = _base_url()\n    if not base:\n        return link if link.startswith("/") else f"/{link}"\n    return f"{base}/{link.lstrip(\'/\')}"\n\n\ndef _collect_notification_payloads(session: Session, flush_context: Any) -> None:  # noqa: ARG001\n    """Yeni Notification kayıtlarını commit sonrası mail gönderimi için kuyruklar."""\n    if not _enabled():\n        return\n\n    payloads = session.info.setdefault(_INFO_PAYLOADS, [])\n    seen = session.info.setdefault(_INFO_SEEN, set())\n\n    for obj in list(session.new):\n        if not isinstance(obj, Notification):\n            continue\n        user_id = _safe_int(getattr(obj, "user_id", None))\n        if not user_id:\n            continue\n        notification_id = _safe_int(getattr(obj, "id", None))\n        key = notification_id or (\n            user_id,\n            _clean(getattr(obj, "title", ""), limit=255),\n            _clean(getattr(obj, "notification_type", ""), limit=50),\n            _clean(getattr(obj, "source_type", ""), limit=50),\n            _safe_int(getattr(obj, "source_id", None)),\n        )\n        if key in seen:\n            continue\n        seen.add(key)\n        payloads.append(\n            {\n                "notification_id": notification_id,\n                "user_id": user_id,\n                "title": _clean(getattr(obj, "title", ""), limit=255) or "BYS360 bildirimi",\n                "body": _clean(getattr(obj, "body", ""), limit=700),\n                "notification_type": _clean(getattr(obj, "notification_type", ""), limit=50) or "system",\n                "source_type": _clean(getattr(obj, "source_type", ""), limit=50),\n                "source_id": _safe_int(getattr(obj, "source_id", None)),\n                "link_url": str(getattr(obj, "link_url", "") or "").strip(),\n                "priority": _clean(getattr(obj, "priority", ""), limit=20) or "normal",\n            }\n        )\n\n\ndef _clear_notification_payloads(session: Session) -> None:\n    session.info.pop(_INFO_PAYLOADS, None)\n    session.info.pop(_INFO_SEEN, None)\n\n\ndef _user_mail_row(user_id: int) -> dict[str, Any] | None:\n    sql = text("SELECT id, email, ad, soyad FROM users WHERE id = :user_id LIMIT 1")\n    with db.engine.connect() as connection:\n        row = connection.execute(sql, {"user_id": user_id}).mappings().first()\n        return dict(row) if row else None\n\n\ndef _recipient_name(row: dict[str, Any]) -> str:\n    name = " ".join(part for part in [_clean(row.get("ad"), limit=80), _clean(row.get("soyad"), limit=80)] if part).strip()\n    return name or "BYS360 kullanıcısı"\n\n\ndef _build_mail(row: dict[str, Any], payload: dict[str, Any]) -> tuple[str, str]:\n    app_name = "BYS360"\n    if has_app_context():\n        app_name = str(current_app.config.get("APP_NAME", "BYS360") or "BYS360").strip() or "BYS360"\n    title = _clean(payload.get("title"), limit=220) or "Yeni bildirim"\n    link = _absolute_link(payload.get("link_url"))\n    subject = f"{app_name} | Yeni bildiriminiz var"\n    body = f"""Sayın {_recipient_name(row)},\n\n{app_name} sisteminde size ait yeni bir bildirim bulunmaktadır.\n\nBildirim başlığı: {title}\n\nDetayları görüntülemek için lütfen sisteme giriş yapınız.\nSistem bağlantısı: {link}\n\nBu e-posta yalnızca bilgilendirme amacıyla gönderilmiştir.\nİyi çalışmalar dileriz.\n{app_name}\n""".strip()\n    return subject, body\n\n\ndef _insert_mail_log(\n    *,\n    user_id: int,\n    recipient_email: str,\n    subject: str,\n    body: str,\n    ok: bool,\n    message: str,\n) -> None:\n    sql = text(\n        """\n        INSERT INTO mail_logs\n            (mail_type, related_user_id, recipient_email, subject, body_preview, sent_at, is_success, error_message)\n        VALUES\n            (:mail_type, :related_user_id, :recipient_email, :subject, :body_preview, :sent_at, :is_success, :error_message)\n        """\n    )\n    with db.engine.begin() as connection:\n        connection.execute(\n            sql,\n            {\n                "mail_type": MAIL_TYPE,\n                "related_user_id": user_id,\n                "recipient_email": recipient_email,\n                "subject": subject[:255],\n                "body_preview": body[:1000],\n                "sent_at": utc_now(),\n                "is_success": bool(ok),\n                "error_message": None if ok else _clean(message, limit=900),\n            },\n        )\n\n\ndef _deliver_notification_mail(payload: dict[str, Any]) -> None:\n    user_id = _safe_int(payload.get("user_id"))\n    if not user_id:\n        return\n    row = _user_mail_row(user_id)\n    if not row:\n        return\n    recipient = _clean(row.get("email"), limit=255)\n    if not recipient or "@" not in recipient:\n        logger.info("BYS360 notification mail skipped: user_id=%s has no valid email", user_id)\n        return\n\n    subject, body = _build_mail(row, payload)\n    ok, message = send_email(recipient, subject, body)\n    _insert_mail_log(\n        user_id=user_id,\n        recipient_email=recipient,\n        subject=subject,\n        body=body,\n        ok=ok,\n        message=message,\n    )\n\n\ndef _send_after_commit(session: Session) -> None:\n    payloads = list(session.info.pop(_INFO_PAYLOADS, []) or [])\n    session.info.pop(_INFO_SEEN, None)\n    if not payloads or not _enabled():\n        return\n\n    for payload in payloads:\n        try:\n            _deliver_notification_mail(payload)\n        except Exception:\n            logger.exception("BYS360 bildirim e-posta gönderimi başarısız oldu.")\n\n\ndef _clear_after_rollback(session: Session) -> None:\n    _clear_notification_payloads(session)\n\n\ndef register_notification_mailer(app: Any | None = None) -> None:  # noqa: ARG001\n    """Yeni sistem içi bildirimler için e-posta bilgilendirme dinleyicisini kurar."""\n    global _REGISTERED\n    if _REGISTERED:\n        return\n    event.listen(Session, "after_flush", _collect_notification_payloads)\n    event.listen(Session, "after_commit", _send_after_commit)\n    event.listen(Session, "after_rollback", _clear_after_rollback)\n    _REGISTERED = True\n    logger.info("BYS360 Notification Mailer V1 aktif edildi.")\n\n\n__all__ = ["MAIL_TYPE", "register_notification_mailer"]\n'


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _backup(path: Path, project_root: Path, backup_root: Path) -> None:
    if path.exists():
        target = backup_root / path.relative_to(project_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def _patch_init(init_path: Path) -> bool:
    text = init_path.read_text(encoding="utf-8")
    if REGISTRATION_LINE in text:
        return False
    marker = '    ("app.services.assistant_shortcut_visibility", "register_assistant_shortcut_visibility_context"),\n'
    if marker in text:
        text = text.replace(marker, marker + REGISTRATION_LINE + "\n", 1)
    else:
        start = text.find("OPTIONAL_STARTUP_REGISTRATIONS")
        close = text.find(")\n\n\n@login_manager.user_loader", start)
        if start == -1 or close == -1:
            raise RuntimeError("OPTIONAL_STARTUP_REGISTRATIONS bloğu bulunamadı.")
        text = text[:close] + REGISTRATION_LINE + "\n" + text[close:]
    init_path.write_text(text, encoding="utf-8")
    return True


def apply(project_root: Path) -> None:
    project_root = project_root.resolve()
    init_path = project_root / INIT_REL
    service_path = project_root / SERVICE_REL
    if not init_path.exists():
        raise FileNotFoundError(f"Bulunamadı: {init_path}")

    backup_root = project_root / "backups" / f"notification_mail_v1_{_timestamp()}"
    backup_root.mkdir(parents=True, exist_ok=True)
    _backup(init_path, project_root, backup_root)
    _backup(service_path, project_root, backup_root)

    service_path.parent.mkdir(parents=True, exist_ok=True)
    service_path.write_text(SERVICE_CODE, encoding="utf-8")
    changed = _patch_init(init_path)

    py_compile.compile(str(service_path), doraise=True)
    py_compile.compile(str(init_path), doraise=True)

    print("BYS360 Notification Email V1 uygulandı.")
    print(f"Yedek klasörü: {backup_root}")
    print(f"Servis dosyası: {service_path}")
    print("app/__init__.py kayıt durumu:", "eklendi" if changed else "zaten vardı")


def check(project_root: Path) -> None:
    project_root = project_root.resolve()
    init_path = project_root / INIT_REL
    service_path = project_root / SERVICE_REL
    missing = []
    if not init_path.exists():
        missing.append(str(init_path))
    if not service_path.exists():
        missing.append(str(service_path))
    if missing:
        raise FileNotFoundError("Eksik dosya: " + ", ".join(missing))
    init_text = init_path.read_text(encoding="utf-8")
    service_text = service_path.read_text(encoding="utf-8")
    required = [
        REGISTRATION_LINE.strip(),
        "register_notification_mailer",
        "after_commit",
        "MAIL_TYPE = \"system_notification_alert\"",
        "INSERT INTO mail_logs",
        "send_email(recipient, subject, body)",
    ]
    for needle in required:
        haystack = init_text + "\n" + service_text
        if needle not in haystack:
            raise RuntimeError(f"Kontrol başarısız, beklenen işaret bulunamadı: {needle}")
    py_compile.compile(str(service_path), doraise=True)
    py_compile.compile(str(init_path), doraise=True)
    print("BYS360 Notification Email V1 kontrolü başarılı.")


def main() -> None:
    parser = argparse.ArgumentParser(description="BYS360 Notification Email V1 overlay")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", choices=["apply", "check", "all"], default="all")
    args = parser.parse_args()
    root = Path(args.project_root)
    if args.mode in {"apply", "all"}:
        apply(root)
    if args.mode in {"check", "all"}:
        check(root)


if __name__ == "__main__":
    main()
