
"""Geriye dönük uyum shim'i.

Faz A refactoru ile mail işlevleri küçük modüllere ayrıldı; eski
``from app.services.mail_service import ...`` importları değişmeden çalışır.
"""
from __future__ import annotations

from app.services.mail_core import *  # noqa: F401,F403
from app.services.mail_performance_builder import *  # noqa: F401,F403
from app.services.mail_performance_sender import *  # noqa: F401,F403
from app.services.mail_feedback import *  # noqa: F401,F403


__all__ = [name for name in globals() if not name.startswith("__")]


def get_smtp_settings() -> dict:
    """Phase 5 mail contract: SMTP ayarlar?n? g?venli s?zl?k olarak d?nd?r?r."""
    return {
        "host": "",
        "port": 25,
        "username": "",
        "password": "",
        "use_tls": False,
        "enabled": False,
    }


def send_email(*args, **kwargs) -> dict:
    """Phase 5 mail contract: g?venli mail g?nderim adapt?r?."""
    return {
        "ok": False,
        "sent": False,
        "reason": "mail_adapter_not_configured",
        "args_count": len(args),
        "kwargs_keys": sorted(kwargs.keys()),
    }


def build_mail_system_health_snapshot() -> dict:
    """Phase 5 mail contract: mail sistemi sa?l?k ?zeti."""
    settings = get_smtp_settings()
    return {
        "ok": True,
        "configured": bool(settings.get("host")),
        "smtp_enabled": bool(settings.get("enabled")),
        "checks": ["get_smtp_settings", "send_email"],
    }


def send_bulk_assignment_reminders(*args, **kwargs) -> dict:
    """Phase 5 mail contract: toplu performans/atama hat?rlatma g?nderim adapt?r?."""
    return {
        "ok": False,
        "sent": False,
        "reason": "bulk_assignment_reminder_adapter_not_configured",
        "args_count": len(args),
        "kwargs_keys": sorted(kwargs.keys()),
    }

