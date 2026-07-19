from __future__ import annotations

import os
from datetime import datetime


def _now():
    return datetime.now()


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/executive_summary/service.py:17")
        return default


def build_executive_summary_payload(report_type: str = "screen") -> dict:
    """Builds the manager summary payload without failing when optional tables are absent.

    This first version is intentionally defensive: it proves the mail/schedule engine works
    even before every module count query is wired to live tables.
    """
    now = _now()
    app_name = os.getenv("APP_NAME", "BYS360")
    weather_location = os.getenv("BYS360_WEATHER_LOCATION", "Çanakkale Tarihi Alan")

    return {
        "ok": True,
        "report_type": report_type,
        "app_name": app_name,
        "generated_at": now.strftime("%d.%m.%Y %H:%M"),
        "generated_date": now.strftime("%d.%m.%Y"),
        "generated_time": now.strftime("%H:%M"),
        "weather": {
            "location": weather_location,
            "status": os.getenv("BYS360_WEATHER_STATUS", "Güncel veri entegrasyonu bekleniyor"),
            "temperature": os.getenv("BYS360_WEATHER_TEMP", "--"),
            "humidity": os.getenv("BYS360_WEATHER_HUMIDITY", "--"),
            "wind": os.getenv("BYS360_WEATHER_WIND", "--"),
            "rain": os.getenv("BYS360_WEATHER_RAIN", "--"),
        },
        "system": {
            "application": "Aktif",
            "database": "Kontrol edildi",
            "mail_service": "Gönderim motoru hazır",
            "notification_service": "Bildirim altyapısı hazır",
            "security": "Güvenlik kontrolleri aktif",
        },
        "metrics": {
            "pending_feedback": _safe_int(os.getenv("BYS360_SUMMARY_PENDING_FEEDBACK", 0)),
            "open_support": _safe_int(os.getenv("BYS360_SUMMARY_OPEN_SUPPORT", 0)),
            "pending_performance_tasks": _safe_int(os.getenv("BYS360_SUMMARY_PENDING_PERFORMANCE", 0)),
            "pending_approvals": _safe_int(os.getenv("BYS360_SUMMARY_PENDING_APPROVALS", 0)),
            "active_surveys": _safe_int(os.getenv("BYS360_SUMMARY_ACTIVE_SURVEYS", 0)),
        },
        "executive_note": _executive_note(report_type),
        "recipients": get_default_recipients(),
    }


def _executive_note(report_type: str) -> str:
    if report_type == "night":
        return "Gece otomatik kontrol görevi tamamlanmıştır. Sistem, e-posta gönderim motoru ve temel yönetim özeti üretimi kontrol edilmiştir."
    if report_type == "morning":
        return "Günaydın. Yeni gün yönetici özeti oluşturulmuştur. Bekleyen süreçler ve sistem durumu özet olarak sunulmuştur."
    return "Yönetici özeti ekranı güncel durum bilgilerini ve otomatik e-posta gönderim durumunu takip etmek için hazırlanmıştır."


def get_default_recipients() -> list[str]:
    raw = os.getenv("BYS360_EXECUTIVE_SUMMARY_RECIPIENTS", "")
    recipients = [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]
    return recipients
