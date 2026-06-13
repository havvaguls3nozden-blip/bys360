# -*- coding: utf-8 -*-
"""BYS360 Faz 5.4 — Performans teknik durum dili temizliği.

Bu servis kullanıcı ekranına teknik statü/kod sızmasını engellemek için Jinja filtreleri sağlar.
Kod değerleri backend ve veritabanında korunur; yalnızca görünür etiket Türkçeleştirilir.
"""
from __future__ import annotations

import logging

from typing import Any
logger = logging.getLogger(__name__)

# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP
_STATUS_LABELS: dict[str, str] = {
    "draft": "Taslak",
    "authorized_scope": "Yetkili Kapsam",
    "workflow state": "Süreç Durumu",
    "workflow_state": "Süreç Durumu",
    "president_pending": "Başkan Onayı Bekliyor",
    "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
    "scorecard_pending": "Karne Yayını Bekliyor",
    "hr_precheck": "İK/Admin Ön Kontrolünde",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "approved_by_president": "Başkan Tarafından Onaylandı",
    "rejected_by_president": "Başkan Tarafından İade Edildi",
    "pending": "Bekliyor",
    "waiting": "Bekliyor",
    "completed": "Tamamlandı",
    "published": "Yayınlandı",
    "returned": "İade Edildi",
    "rejected": "Reddedildi",
    "approved": "Onaylandı",
}

_TEXT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("blocked_president_pending", "Başkan Onayı Yayın Kilidi"),
    ("president_pending", "Başkan Onayı Bekliyor"),
    ("scorecard_pending", "Karne Yayını Bekliyor"),
    ("authorized_scope", "Yetkili Kapsam"),
    ("workflow state", "Süreç Durumu"),
    ("workflow_state", "Süreç Durumu"),
    ("phase sync", "Süreç kaydı güncellendiğinde"),
    ("Faz 3 senkronu", "Puanlama geçmişi güncellendiğinde"),
    ("faz 3 senkronu", "Puanlama geçmişi güncellendiğinde"),
)


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    try:
        text = str(value).strip()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return ""
    return text


def phase5_4_status_label(value: Any, fallback: str = "-") -> str:
    """Teknik durum değerini kurumsal Türkçe etikete çevirir."""
    text = _normalize(value)
    if not text:
        return fallback
    key = text.lower().strip()
    if key in _STATUS_LABELS:
        return _STATUS_LABELS[key]
    cleaned = phase5_4_clean_text(text)
    return cleaned or fallback


def phase5_4_clean_text(value: Any, fallback: str = "-") -> str:
    """Uzun metin içindeki teknik kod parçalarını Türkçeleştirir."""
    text = _normalize(value)
    if not text:
        return fallback
    out = text
    for raw, label in _TEXT_REPLACEMENTS:
        out = out.replace(raw, label)
    # İngilizce teknik kelimeleri yalnızca ayrı kelime ise değiştir.
    import re
    out = re.sub(r"(?<![A-Za-z0-9_])draft(?![A-Za-z0-9_])", "Taslak", out, flags=re.IGNORECASE)
    out = re.sub(r"(?<![A-Za-z0-9_])workflow state(?![A-Za-z0-9_])", "Süreç Durumu", out, flags=re.IGNORECASE)
    return out or fallback


def phase5_4_register_filters(app: Any) -> None:
    """Jinja filtre/globallerini güvenli biçimde kaydeder."""
    app.jinja_env.filters.setdefault("phase5_4_status_label", phase5_4_status_label)
    app.jinja_env.filters.setdefault("phase5_4_clean_text", phase5_4_clean_text)
    app.jinja_env.globals.setdefault("phase5_4_status_label", phase5_4_status_label)
    app.jinja_env.globals.setdefault("phase5_4_clean_text", phase5_4_clean_text)
