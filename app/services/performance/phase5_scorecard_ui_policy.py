"""
BYS360 Performans Tamamlama Faz 5
Karne ve Puanlama Ekranı Kurumsal UI Politika Merkezi

Amaç:
- Karne ve puanlama ekranlarında teknik/geliştirici dili göstermemek.
- Nihai puanı, kriterleri, amir görüşlerini ve süreç geçmişini daha okunur hale getirmek.
- Başkan, amir ve personel ekranlarında aynı Türkçe statü dilini kullanmak.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


PHASE5_POLICY_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_POLICY"

TECHNICAL_STATUS_LABELS: dict[str, str] = {
    "draft": "Taslak",
    "authorized_scope": "Yetkili Kapsam",
    "president_pending": "Başkan Onayı Bekliyor",
    "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
    "scorecard_pending": "Karne Yayın Süreci Bekliyor",
    "workflow_state": "Süreç Durumu",
    "sync_pending": "Senkronizasyon Bekliyor",
    "phase_sync": "Süreç Güncellemesi",
    "hr_precheck": "Ön Kontrol Sürecinde",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "approved_by_president": "Başkan Tarafından Onaylandı",
    "rejected_by_president": "Başkan Tarafından İade Edildi",
    "published": "Yayınlandı",
    "blocked": "Yayın Kilidi",
    "completed": "Tamamlandı",
    "pending": "Bekliyor",
}

TECHNICAL_REPLACEMENTS: dict[str, str] = {
    "authorized_scope": "Yetkili Kapsam",
    "workflow state": "süreç durumu",
    "workflow_state": "Süreç Durumu",
    "phase sync": "süreç güncellemesi",
    "phase_sync": "Süreç Güncellemesi",
    "sync": "süreç güncellemesi",
    "scorecard_pending": "Karne Yayın Süreci Bekliyor",
    "president_pending": "Başkan Onayı Bekliyor",
    "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
    "draft": "Taslak",
    "Faz 3 senkronu": "Süreç kayıtları güncellendiğinde",
    "Faz 3": "Süreç",
    "Faz 4": "Süreç",
    "Faz 5": "Süreç",
}

HIDDEN_TECHNICAL_TERMS = [
    "authorized_scope",
    "workflow state",
    "workflow_state",
    "phase sync",
    "phase_sync",
    "scorecard_pending",
    "president_pending",
    "blocked_president_pending",
    "Faz 3 senkronu",
]


@dataclass(frozen=True)
class ScoreBand:
    key: str
    label: str
    tone: str
    explanation: str


def translate_status(value: Any, default: str = "Süreç Durumu") -> str:
    raw = str(value or "").strip()
    if not raw:
        return default
    normalized = raw.lower().replace(" ", "_").replace("-", "_")
    return TECHNICAL_STATUS_LABELS.get(normalized, raw)


def sanitize_technical_text(text: Any) -> str:
    """
    Kullanıcı ekranına gidecek metinde teknik statü/kod ifadelerini kurumsal Türkçeye çevirir.
    """
    value = "" if text is None else str(text)
    for old, new in TECHNICAL_REPLACEMENTS.items():
        value = value.replace(old, new)
    return value


def contains_visible_technical_language(text: Any) -> bool:
    value = "" if text is None else str(text)
    lower = value.lower()
    return any(term.lower() in lower for term in HIDDEN_TECHNICAL_TERMS)


def score_band(score: Any) -> ScoreBand:
    try:
        numeric = float(score)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return ScoreBand("unknown", "Puan Bekleniyor", "muted", "Nihai puan henüz oluşmadı.")

    if numeric < 70:
        return ScoreBand(
            "low",
            "Düşük Performans",
            "danger",
            "70 altı sonuç üst onay ve süreç takibi gerektirir.",
        )
    if numeric >= 90:
        return ScoreBand(
            "high",
            "Çok Başarılı",
            "success",
            "90 ve üzeri sonuç ayrıntılı genel görüşle desteklenmelidir.",
        )
    return ScoreBand(
        "normal",
        "Beklenen Düzey",
        "neutral",
        "Sonuç normal performans bandındadır.",
    )


def score_display(score: Any) -> str:
    try:
        return f"{float(score):.2f}"
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return "-"


def manager_level_label(level: Any) -> str:
    raw = str(level or "").strip().lower()
    mapping = {
        "1": "1. Amir",
        "2": "2. Amir",
        "3": "3. Amir",
        "first": "1. Amir",
        "second": "2. Amir",
        "third": "3. Amir",
        "manager_1": "1. Amir",
        "manager_2": "2. Amir",
        "manager_3": "3. Amir",
    }
    return mapping.get(raw, str(level or "Amir"))


def build_manager_opinion_cards(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in rows or []:
        level = manager_level_label(row.get("manager_level") or row.get("level") or row.get("amir_seviyesi"))
        opinion = sanitize_technical_text(row.get("opinion") or row.get("comment") or row.get("general_comment") or "")
        score = score_display(row.get("score") or row.get("total_score") or row.get("weighted_score"))
        cards.append(
            {
                "level_label": level,
                "manager_name": row.get("manager_name") or row.get("amir_adi") or "Amir",
                "score": score,
                "opinion": opinion or "Görüş metni bulunmuyor.",
                "status": translate_status(row.get("status") or row.get("state") or "completed"),
            }
        )
    return cards


def phase5_empty_history_message(kind: str = "scoring") -> str:
    if kind == "process":
        return "Süreç geçmişi henüz oluşmamış. Kayıt oluştuğunda bu alanda gösterilecektir."
    if kind == "manager":
        return "Amir görüşü henüz oluşmamış. Değerlendirme tamamlandığında bu alanda gösterilecektir."
    return "Puanlama geçmişi henüz oluşmamış. Değerlendirme kaydı tamamlandığında bu alanda gösterilecektir."


def phase5_scorecard_contract() -> dict[str, Any]:
    return {
        "technical_language_hidden": True,
        "large_score_surface": True,
        "criteria_table_readable": True,
        "manager_opinion_cards": True,
        "process_history_turkish": True,
        "mobile_responsive": True,
        "president_card_detail": True,
        "personnel_scorecard_readable": True,
        "phase_marker": PHASE5_POLICY_MARKER,
    }
