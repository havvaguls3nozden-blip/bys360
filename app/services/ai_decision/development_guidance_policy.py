# -*- coding: utf-8 -*-
"""
BYS360 AI Karar Destek Faz 11
Gelişim önerisi ve rehber alanı karar destek politikası.

Bu servis idari karar vermez, performans puanı üretmez ve personel hakkında
tek başına bağlayıcı sonuç oluşturmaz. Amacı; karne, dönem içi not ve geçmiş
eğilimlerden güvenli, uygulanabilir ve insan denetimli gelişim önerisi üretmektir.

BYS360_AI_DECISION_FAZ11_POLICY_OK
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


GUIDANCE_TYPE_LABELS: Dict[str, str] = {
    "low_score_recovery": "Düşük performans gelişim takibi",
    "high_score_sustain": "Yüksek başarıyı sürdürme",
    "criteria_focus": "Kriter bazlı gelişim odağı",
    "communication_feedback": "Geri bildirim görüşmesi",
    "interim_note_followup": "Dönem içi not takibi",
    "archive_trend": "Geçmiş performans eğilimi",
    "balanced_guidance": "Genel gelişim rehberi",
}

SENSITIVE_FIELD_HINTS = (
    "tc", "tckn", "kimlik", "adres", "telefon", "mail", "email", "e-posta",
    "iban", "hesap", "sağlık", "saglik", "rapor no", "şifre", "sifre", "parola",
)

TECHNICAL_STATUS_LABELS: Dict[str, str] = {
    "draft": "Hazırlık kaydı",
    "authorized_scope": "Yetkili kapsam",
    "workflow_state": "Süreç durumu",
    "workflow state": "Süreç durumu",
    "phase sync": "Süreç eşitleme",
    "scorecard_pending": "Karne hazırlığı bekliyor",
    "president_pending": "Başkan Onayı Bekliyor",
    "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
}


@dataclass(frozen=True)
class DevelopmentGuidanceCard:
    code: str
    title: str
    guidance_type: str
    message: str
    suggested_action: str
    priority: str = "normal"  # low | normal | high | critical
    visibility: str = "yetkili_kapsam"
    followup_label: str = "Takip et"

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _lower(value: Any) -> str:
    return _normalize(value).casefold()


def _get(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            return obj.get(name)
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except Exception:
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_text(text: Any, limit: int = 260) -> str:
    raw = _normalize(text)
    if not raw:
        return ""
    lowered = raw.casefold()
    if any(hint in lowered for hint in SENSITIVE_FIELD_HINTS):
        return "Bu içerik hassas bilgi içerebileceği için yalnızca rehberlik düzeyinde özetlendi."
    for technical, label in TECHNICAL_STATUS_LABELS.items():
        raw = raw.replace(technical, label)
        raw = raw.replace(technical.upper(), label)
    raw = " ".join(raw.split())
    return raw[:limit] + ("…" if len(raw) > limit else "")


def _score_band(score: Optional[float]) -> str:
    if score is None:
        return "puan_yok"
    if score < 70:
        return "dusuk"
    if score > 90:
        return "yuksek"
    return "standart"


def summarize_development_inputs(
    *,
    score: Any = None,
    previous_scores: Sequence[Any] | None = None,
    interim_summary: Mapping[str, Any] | None = None,
    criteria_results: Sequence[Any] | None = None,
    general_comment: Any = None,
    existing_recommendations: Sequence[Any] | None = None,
) -> Dict[str, Any]:
    """Gelişim önerisi üretmek için gerekli veriyi güvenli özetler."""
    numeric_score = _to_float(score)
    band = _score_band(numeric_score)
    previous_numeric = [_to_float(v) for v in (previous_scores or [])]
    previous_numeric = [v for v in previous_numeric if v is not None]
    trend_label = "Geçmiş eğilim bulunmuyor"
    if len(previous_numeric) >= 2:
        if previous_numeric[-1] < previous_numeric[0] - 5:
            trend_label = "Geçmiş puanlarda düşüş eğilimi var"
        elif previous_numeric[-1] > previous_numeric[0] + 5:
            trend_label = "Geçmiş puanlarda gelişim eğilimi var"
        else:
            trend_label = "Geçmiş puanlar dengeli seyrediyor"

    low_criteria: List[Dict[str, Any]] = []
    strong_criteria: List[Dict[str, Any]] = []
    for item in criteria_results or []:
        label = _safe_text(_get(item, "criterion_name", "name", "label", "title", default="Değerlendirme kriteri"), 120)
        point = _to_float(_get(item, "score", "point", "value", "score_value", default=None))
        if point is None:
            continue
        if point <= 2:
            low_criteria.append({"label": label, "score": point})
        elif point >= 4.5:
            strong_criteria.append({"label": label, "score": point})

    interim = dict(interim_summary or {})
    negative_total = _to_int(interim.get("negative_total") or interim.get("development_need_total"))
    positive_total = _to_int(interim.get("positive_total"))
    existing_count = len(existing_recommendations or [])

    return {
        "score": numeric_score,
        "score_band": band,
        "trend_label": trend_label,
        "previous_score_count": len(previous_numeric),
        "low_criteria": low_criteria[:5],
        "strong_criteria": strong_criteria[:5],
        "negative_note_total": negative_total,
        "positive_note_total": positive_total,
        "general_comment_summary": _safe_text(general_comment, 220),
        "existing_recommendation_count": existing_count,
    }


def build_development_guidance_cards(summary: Mapping[str, Any]) -> List[Dict[str, str]]:
    score = _to_float(summary.get("score"))
    band = _normalize(summary.get("score_band"))
    negative_total = _to_int(summary.get("negative_note_total"))
    positive_total = _to_int(summary.get("positive_note_total"))
    low_criteria = list(summary.get("low_criteria") or [])
    strong_criteria = list(summary.get("strong_criteria") or [])
    existing_count = _to_int(summary.get("existing_recommendation_count"))
    trend_label = _normalize(summary.get("trend_label"))

    cards: List[DevelopmentGuidanceCard] = []

    if band == "dusuk":
        cards.append(DevelopmentGuidanceCard(
            code="low_score_recovery_plan",
            title="Gelişim takip planı hazırlanmalı",
            guidance_type=GUIDANCE_TYPE_LABELS["low_score_recovery"],
            message="70 altı sonuç için gelişim odaklı takip notu hazırlanmalı ve süreç ilgili onay akışıyla birlikte izlenmelidir.",
            suggested_action="Görüşme tarihi, gelişim başlığı, takip sorumlusu ve beklenen iyileşme adımı belirlenmeli.",
            priority="critical",
            followup_label="Gelişim planı oluştur",
        ))
    elif band == "yuksek":
        cards.append(DevelopmentGuidanceCard(
            code="high_score_sustain_plan",
            title="Başarıyı sürdürme notu eklenebilir",
            guidance_type=GUIDANCE_TYPE_LABELS["high_score_sustain"],
            message="90 üstü sonuçlarda güçlü yönlerin korunması ve kurum içi iyi uygulama örneğine dönüştürülmesi değerlendirilebilir.",
            suggested_action="Güçlü yön, örnek davranış ve sürdürülebilir katkı kısa bir notla kayda alınmalı.",
            priority="normal",
            followup_label="Başarı notu ekle",
        ))
    else:
        cards.append(DevelopmentGuidanceCard(
            code="balanced_guidance",
            title="Genel gelişim rehberi hazırlanabilir",
            guidance_type=GUIDANCE_TYPE_LABELS["balanced_guidance"],
            message="Karne sonucu standart aralıkta. Gelişim önerisi güçlü yön ve iyileştirilebilir alan dengesinde hazırlanabilir.",
            suggested_action="Bir güçlü yön, bir gelişim alanı ve izlenecek kısa takip adımı belirlenmeli.",
            priority="low",
            followup_label="Rehber not hazırla",
        ))

    if low_criteria:
        labels = ", ".join(_safe_text(item.get("label"), 80) for item in low_criteria[:3])
        cards.append(DevelopmentGuidanceCard(
            code="criteria_focus_needed",
            title="Kriter bazlı gelişim odağı var",
            guidance_type=GUIDANCE_TYPE_LABELS["criteria_focus"],
            message=f"Düşük kalan değerlendirme kriterleri için hedefli gelişim notu önerilir: {labels}.",
            suggested_action="Her düşük kriter için ölçülebilir, takip edilebilir ve kısa vadeli bir gelişim adımı yazılmalı.",
            priority="high" if len(low_criteria) >= 2 else "normal",
            followup_label="Kriterleri incele",
        ))

    if negative_total > 0:
        cards.append(DevelopmentGuidanceCard(
            code="interim_note_followup",
            title="Dönem içi notlarla bağlantı kurulmalı",
            guidance_type=GUIDANCE_TYPE_LABELS["interim_note_followup"],
            message="Ara notlarda gelişim ihtiyacı veya olumsuz gözlem bulunuyor. Gelişim önerisi bu notlarla tutarlı hazırlanmalıdır.",
            suggested_action="Ara notlar gözden geçirilip kişisel mahremiyeti aşmadan gelişim başlığına dönüştürülmeli.",
            priority="high" if negative_total >= 3 else "normal",
            followup_label="Ara notları bağla",
        ))

    if positive_total > 0 or strong_criteria:
        cards.append(DevelopmentGuidanceCard(
            code="strengths_should_be_visible",
            title="Güçlü yönler de görünür olmalı",
            guidance_type=GUIDANCE_TYPE_LABELS["high_score_sustain"],
            message="Olumlu kayıtlar veya yüksek kriter puanları var. Rehber not yalnızca eksiklere değil, güçlü yönlerin korunmasına da yer vermelidir.",
            suggested_action="Karnede güçlü yönleri destekleyen kısa, somut ve kurumsal bir ifade kullanılmalı.",
            priority="normal",
            followup_label="Güçlü yön ekle",
        ))

    if "düşüş" in trend_label.casefold() or "dusus" in trend_label.casefold():
        cards.append(DevelopmentGuidanceCard(
            code="archive_trend_decline",
            title="Geçmiş eğilim takip edilmeli",
            guidance_type=GUIDANCE_TYPE_LABELS["archive_trend"],
            message="Geçmiş puanlarda düşüş eğilimi görünüyor. Gelişim önerisi tek dönemle sınırlı kalmadan eğilim üzerinden hazırlanmalıdır.",
            suggested_action="Önceki dönemlerle karşılaştırmalı kısa takip notu oluşturulmalı.",
            priority="high",
            followup_label="Geçmişi incele",
        ))

    if existing_count == 0:
        cards.append(DevelopmentGuidanceCard(
            code="recommendation_missing",
            title="Henüz gelişim önerisi kaydı yok",
            guidance_type=GUIDANCE_TYPE_LABELS["communication_feedback"],
            message="Bu kayıt için mevcut gelişim önerisi bulunamadı. Yayın öncesi rehber not eklenmesi önerilir.",
            suggested_action="Kısa, ölçülebilir ve personelin anlayacağı sade bir gelişim önerisi yazılmalı.",
            priority="normal",
            followup_label="Öneri yaz",
        ))

    return [card.to_dict() for card in cards]


def build_development_guidance_context(
    *,
    score: Any = None,
    previous_scores: Sequence[Any] | None = None,
    interim_summary: Mapping[str, Any] | None = None,
    criteria_results: Sequence[Any] | None = None,
    general_comment: Any = None,
    existing_recommendations: Sequence[Any] | None = None,
    viewer_role: str = "",
) -> Dict[str, Any]:
    summary = summarize_development_inputs(
        score=score,
        previous_scores=previous_scores,
        interim_summary=interim_summary,
        criteria_results=criteria_results,
        general_comment=general_comment,
        existing_recommendations=existing_recommendations,
    )
    cards = build_development_guidance_cards(summary)
    return {
        "module": "Gelişim Önerisi ve Rehber Alanı",
        "principle": "Bu çıktı idari karar değildir; yetkili kullanıcının karne sonrası gelişim notunu hazırlamasına yardımcı olur.",
        "viewer_role": viewer_role or "Yetkili kullanıcı",
        "summary": summary,
        "cards": cards,
        "recommendation_count": len(cards),
        "safe_visibility_note": "Kişisel ve hassas içerik yerine ölçülebilir gelişim başlığı, takip adımı ve kurumsal rehberlik gösterilir.",
        "status": "hazır",
    }
