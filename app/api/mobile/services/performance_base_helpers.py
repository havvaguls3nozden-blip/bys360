from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _label(value: Any, default: str = "Bekliyor") -> str:
    raw = str(value or "").strip()
    key = raw.lower()
    mapping = {
        "pending": "Bekliyor",
        "open": "Bekliyor",
        "assigned": "Atandı",
        "atandi": "Atandı",
        "atandı": "Atandı",
        "in_progress": "Devam Ediyor",
        "devam": "Devam Ediyor",
        "devam_ediyor": "Devam Ediyor",
        "tamamlandi": "Tamamlandı",
        "tamamlandı": "Tamamlandı",
        "completed": "Tamamlandı",
        "done": "Tamamlandı",
        "published": "Yayınlandı",
        "yayinda": "Yayında",
        "yayında": "Yayında",
        "president_pending": "Başkan Onayı Bekliyor",
        "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
        "hr_precheck": "Ön Kontrol Bekliyor",
        "approved": "Onaylandı",
        "rejected": "İade Edildi",
        "active": "Aktif",
        "inactive": "Pasif",
        "draft": "Hazırlıkta",
        "closed": "Kapandı",
    }
    return mapping.get(key, raw or default)


def _period_name(period: Any) -> str:
    return str(getattr(period, "title", None) or getattr(period, "name", None) or getattr(period, "period_name", None) or "Performans Dönemi")


def _date_text(value: Any) -> str:
    if not value:
        return ""
    try:
        return value.strftime("%d.%m.%Y")
    except (AttributeError, TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return str(value)[:10]


def _date_range(period: Any) -> str:
    start = _date_text(getattr(period, "start_date", None) or getattr(period, "start", None))
    end = _date_text(getattr(period, "end_date", None) or getattr(period, "end", None))
    return f"{start} - {end}".strip(" -")


def _period_scope(period: Any) -> str:
    for name in ("scope_label", "scope_type", "period_type", "evaluation_type", "target_scope", "kapsam_tipi"):
        value = getattr(period, name, None)
        if value:
            raw = str(value).strip()
            return {
                "all": "Tüm Kurum",
                "organization": "Birim",
                "unit": "Birim",
                "upper_unit": "Üst Birim",
                "category": "Kategori / Grup",
                "selected_users": "Seçili Personel",
                "personnel": "Seçili Personel",
                "special": "Özel Dönem",
                "yearly": "Yıllık",
                "annual": "Yıllık",
                "monthly": "Aylık",
                "quarterly": "3 Aylık",
                "semiannual": "6 Aylık",
            }.get(raw.lower(), raw)
    return "Genel Kapsam"


def _period_status(period: Any) -> str:
    if getattr(period, "is_active", False):
        return "Aktif"
    status = getattr(period, "status", None) or getattr(period, "state", None)
    return _label(status, "Hazırlık")
