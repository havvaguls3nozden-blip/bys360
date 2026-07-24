from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

"""BYS360 AI Karar Destek Faz 8 dönem ve kapsam politikası.

Çoklu dönem, özel dönem, kategori dönemi ve seçili personel kapsamlarını
karar destek merkezi için güvenli, açıklanabilir ve insan denetimli sinyallere
dönüştürür.

BYS360_AI_DECISION_FAZ8_PERIOD_SCOPE_POLICY
"""

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PeriodScopePolicy:
    """Dönem/kapsam karar destek politikası."""

    allow_multiple_periods: bool = True
    allow_special_periods: bool = True
    require_scope_for_special_period: bool = True
    overlap_warning_enabled: bool = True
    selected_personnel_limit: int = 500
    low_assignment_warning_limit: int = 1


PERIOD_TYPE_LABELS = {
    "annual": "Yıllık Dönem",
    "yearly": "Yıllık Dönem",
    "six_month": "6 Aylık Dönem",
    "semiannual": "6 Aylık Dönem",
    "quarterly": "3 Aylık Dönem",
    "monthly": "Aylık Dönem",
    "special": "Özel Dönem",
    "custom": "Özel Dönem",
}

SCOPE_TYPE_LABELS = {
    "all": "Tüm Kurum",
    "institution": "Tüm Kurum",
    "unit": "Birim Kapsamı",
    "upper_unit": "Üst Birim Kapsamı",
    "category": "Kategori/Grup Kapsamı",
    "group": "Kategori/Grup Kapsamı",
    "selected_personnel": "Seçili Personel Kapsamı",
    "personnel": "Seçili Personel Kapsamı",
}


_FALSE_VALUES = {"0", "false", "hayır", "hayir", "no", "off", "kapalı", "kapali"}
_TRUE_VALUES = {"1", "true", "evet", "yes", "on", "açık", "acik"}


def safe_attr(source: Any, *names: str, default: Any = None) -> Any:
    """Mapping, SQLAlchemy row veya nesne üzerinden güvenli alan okur."""

    if source is None:
        return default
    mapping = dict(source._mapping) if hasattr(source, "_mapping") else source if isinstance(source, Mapping) else None
    if isinstance(mapping, Mapping):
        for name in names:
            if name in mapping:
                return mapping.get(name)
    for name in names:
        if hasattr(source, name):
            return getattr(source, name)
    return default


def to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).replace(",", ".")))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def to_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt).date()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/ai_decision/period_scope_policy.py:105)")
            continue
    return None


def date_display(value: Any) -> str:
    parsed = to_date(value)
    return parsed.strftime("%d.%m.%Y") if parsed else "—"


def build_period_scope_policy(settings: Mapping[str, Any] | None = None) -> PeriodScopePolicy:
    settings = settings or {}
    return PeriodScopePolicy(
        allow_multiple_periods=to_bool(settings.get("faz8_allow_multiple_periods"), True),
        allow_special_periods=to_bool(settings.get("faz8_allow_special_periods"), True),
        require_scope_for_special_period=to_bool(settings.get("faz8_require_scope_for_special_period"), True),
        overlap_warning_enabled=to_bool(settings.get("faz8_overlap_warning_enabled"), True),
        selected_personnel_limit=to_int(settings.get("faz8_selected_personnel_limit"), 500),
        low_assignment_warning_limit=to_int(settings.get("faz8_low_assignment_warning_limit"), 1),
    )


def normalize_period_type(value: Any) -> str:
    key = str(value or "annual").strip().lower()
    return PERIOD_TYPE_LABELS.get(key, PERIOD_TYPE_LABELS["annual"])


def normalize_scope_type(value: Any) -> str:
    key = str(value or "all").strip().lower()
    return SCOPE_TYPE_LABELS.get(key, SCOPE_TYPE_LABELS["all"])


def periods_overlap(start_a: Any, end_a: Any, start_b: Any, end_b: Any) -> bool:
    a_start = to_date(start_a)
    a_end = to_date(end_a)
    b_start = to_date(start_b)
    b_end = to_date(end_b)
    if not a_start or not a_end or not b_start or not b_end:
        return False
    return a_start <= b_end and b_start <= a_end


def count_overlaps(period: Any, existing_periods: Iterable[Any]) -> int:
    period_id = safe_attr(period, "id", "period_id", default=None)
    start = safe_attr(period, "start_date", "date_start", "baslangic_tarihi", default=None)
    end = safe_attr(period, "end_date", "date_end", "bitis_tarihi", default=None)
    count = 0
    for item in existing_periods:
        item_id = safe_attr(item, "id", "period_id", default=None)
        if period_id is not None and item_id == period_id:
            continue
        if periods_overlap(start, end, safe_attr(item, "start_date", "date_start", default=None), safe_attr(item, "end_date", "date_end", default=None)):
            count += 1
    return count


def normalize_period(period: Any, assignment_count: int = 0, overlap_count: int = 0) -> dict[str, Any]:
    period_type = safe_attr(period, "period_type", "type", "donem_turu", default="annual")
    scope_type = safe_attr(period, "scope_type", "scope", "kapsam_tipi", default="all")
    return {
        "id": safe_attr(period, "id", "period_id", default=None),
        "title": safe_attr(period, "title", "name", "period_name", "donem_adi", default="Performans Dönemi"),
        "period_type": str(period_type or "annual"),
        "period_type_label": normalize_period_type(period_type),
        "scope_type": str(scope_type or "all"),
        "scope_type_label": normalize_scope_type(scope_type),
        "scope_reference": safe_attr(period, "scope_reference", "scope_id", "category_id", "unit_id", default=None),
        "start_date": safe_attr(period, "start_date", "date_start", "baslangic_tarihi", default=None),
        "end_date": safe_attr(period, "end_date", "date_end", "bitis_tarihi", default=None),
        "start_date_display": date_display(safe_attr(period, "start_date", "date_start", "baslangic_tarihi", default=None)),
        "end_date_display": date_display(safe_attr(period, "end_date", "date_end", "bitis_tarihi", default=None)),
        "is_active": to_bool(safe_attr(period, "is_active", "active", default=True), True),
        "assignment_count": assignment_count,
        "overlap_count": overlap_count,
    }


def build_period_decision(period: Any, policy: PeriodScopePolicy | None = None, assignment_count: int = 0, overlap_count: int = 0) -> dict[str, Any]:
    """Tek dönem için karar destek çıktısı üretir."""

    policy = policy or build_period_scope_policy()
    item = normalize_period(period, assignment_count=assignment_count, overlap_count=overlap_count)
    attention: list[str] = []
    recommendations: list[str] = []

    if item["period_type"] in {"special", "custom"} and not policy.allow_special_periods:
        attention.append("Özel dönem açma ayarı kapalı görünüyor.")
    if item["period_type"] in {"special", "custom"} and policy.require_scope_for_special_period and item["scope_type"] in {"all", "institution"}:
        attention.append("Özel dönem için daha dar bir kapsam seçilmesi önerilir.")
    if item["scope_type"] in {"category", "group", "selected_personnel", "personnel"} and not item.get("scope_reference"):
        attention.append("Kapsam tipi seçilmiş ancak kapsam referansı görünmüyor.")
    if policy.overlap_warning_enabled and item["overlap_count"] > 0:
        attention.append("Aynı tarih aralığına yakın başka dönem kaydı bulunuyor.")
    if item["assignment_count"] < policy.low_assignment_warning_limit:
        attention.append("Bu dönem için değerlendirme görevi henüz yeterli görünmüyor.")
    if item["scope_type"] in {"selected_personnel", "personnel"} and item["assignment_count"] > policy.selected_personnel_limit:
        attention.append("Seçili personel kapsamı beklenenden geniş görünüyor.")

    if not attention:
        recommendations.append("Dönem ve kapsam yapısı karar destek açısından düzenli görünüyor.")
    else:
        recommendations.append("Dönem yayına alınmadan önce kapsam, tarih ve görev üretimi birlikte kontrol edilmelidir.")

    return {
        **item,
        "attention_count": len(attention),
        "attention_items": attention,
        "recommendations": recommendations,
        "risk_level": "Dikkat Gerektirir" if attention else "Düzenli",
        "safety_note": "Bu çıktı idari karar değildir; dönem ve kapsam hazırlığını insan denetimli kontrol için özetler.",
        "marker": "BYS360_AI_DECISION_FAZ8_PERIOD_DECISION_PAYLOAD",
    }


def summarize_periods(period_decisions: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(period_decisions)
    by_type: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    attention_total = 0
    active_count = 0
    for row in rows:
        by_type[row.get("period_type_label") or "Dönem Türü Yok"] = by_type.get(row.get("period_type_label") or "Dönem Türü Yok", 0) + 1
        by_scope[row.get("scope_type_label") or "Kapsam Yok"] = by_scope.get(row.get("scope_type_label") or "Kapsam Yok", 0) + 1
        attention_total += to_int(row.get("attention_count"), 0)
        if row.get("is_active"):
            active_count += 1
    return {
        "period_count": len(rows),
        "active_period_count": active_count,
        "attention_total": attention_total,
        "period_type_distribution": by_type,
        "scope_type_distribution": by_scope,
        "manager_note": "Dikkat gerektiren dönemler önce kapsam ve görev üretimi açısından gözden geçirilmelidir." if attention_total else "Dönem/kapsam kayıtları karar destek açısından düzenli görünüyor.",
    }
