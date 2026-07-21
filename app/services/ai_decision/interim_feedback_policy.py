"""
BYS360 AI Karar Destek Faz 10
Performans içi ara not / geri bildirim karar destek politikası.

Bu servis idari karar vermez, otomatik puan üretmez ve personel hakkında
tek başına bağlayıcı sonuç oluşturmaz. Amacı dönem içinde girilmiş notları
amir ve yetkili kullanıcı için güvenli, kısa ve kurumsal bir hatırlatma
özetine dönüştürmektir.

BYS360_AI_DECISION_FAZ10_POLICY_OK
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any

NOTE_TYPE_LABELS: dict[str, str] = {
    "positive_event": "Olumlu olay",
    "negative_event": "Olumsuz olay",
    "success": "Başarı",
    "development_need": "Gelişim ihtiyacı",
    "general_observation": "Genel gözlem",
    "feedback": "Geri bildirim",
    "other": "Diğer",
}

NOTE_TYPE_ALIASES: dict[str, str] = {
    "olumlu": "positive_event",
    "olumlu olay": "positive_event",
    "pozitif": "positive_event",
    "başarı": "success",
    "basari": "success",
    "olumsuz": "negative_event",
    "olumsuz olay": "negative_event",
    "gelişim": "development_need",
    "gelisim": "development_need",
    "gelişim ihtiyacı": "development_need",
    "gelisim ihtiyaci": "development_need",
    "gözlem": "general_observation",
    "gozlem": "general_observation",
    "genel gözlem": "general_observation",
    "genel gozlem": "general_observation",
    "geri bildirim": "feedback",
    "feedback": "feedback",
}

SENSITIVE_FIELD_HINTS = (
    "tc", "tckn", "kimlik", "adres", "telefon", "mail", "email", "e-posta",
    "iban", "hesap", "saglik", "sağlık", "rapor no",
)

TECHNICAL_STATUS_LABELS: dict[str, str] = {
    "draft": "Taslak",
    "pending": "İşlem Bekliyor",
    "submitted": "Gönderildi",
    "approved": "Onaylandı",
    "rejected": "İade Edildi",
    "authorized_scope": "Yetkili Kapsam",
    "workflow_state": "Süreç Durumu",
    "sync": "Eşitleme",
}


@dataclass(frozen=True)
class InterimFeedbackSignal:
    code: str
    title: str
    message: str
    severity: str = "info"  # info | attention | risk | success
    action_label: str = "İncele"

    def to_dict(self) -> dict[str, str]:
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


def _safe_text(text: Any, limit: int = 220) -> str:
    """Kullanıcıya gösterilecek kısa metni sadeleştirir ve sınırlar."""
    raw = _normalize(text)
    if not raw:
        return ""
    lowered = raw.casefold()
    if any(hint in lowered for hint in SENSITIVE_FIELD_HINTS):
        return "Bu not hassas bilgi içerebileceği için özet düzeyinde gösterildi."
    for technical, label in TECHNICAL_STATUS_LABELS.items():
        raw = raw.replace(technical, label)
        raw = raw.replace(technical.upper(), label)
    raw = " ".join(raw.split())
    return raw[:limit] + ("…" if len(raw) > limit else "")


def normalize_note_type(note_type: Any) -> str:
    normalized = _lower(note_type)
    if not normalized:
        return "other"
    if normalized in NOTE_TYPE_LABELS:
        return normalized
    return NOTE_TYPE_ALIASES.get(normalized, "other")


def note_type_label(note_type: Any) -> str:
    return NOTE_TYPE_LABELS.get(normalize_note_type(note_type), NOTE_TYPE_LABELS["other"])


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _normalize(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).date()
        except ValueError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/ai_decision/interim_feedback_policy.py:139)")
            continue
    return None


def summarize_interim_notes(
    notes: Sequence[Any],
    *,
    period_start: Any = None,
    period_end: Any = None,
    include_examples: bool = True,
    max_examples: int = 3,
) -> dict[str, Any]:
    """Dönem içi notları kişi mahremiyetini zorlamadan özetler."""
    counts: dict[str, int] = {key: 0 for key in NOTE_TYPE_LABELS}
    examples: list[dict[str, str]] = []
    out_of_period_count = 0
    start = _parse_date(period_start)
    end = _parse_date(period_end)

    for note in notes or []:
        ntype = normalize_note_type(_get(note, "note_type", "type", "category", default="other"))
        counts[ntype] = counts.get(ntype, 0) + 1
        created = _parse_date(_get(note, "created_at", "note_date", "date", default=None))
        if created and ((start and created < start) or (end and created > end)):
            out_of_period_count += 1
        if include_examples and len(examples) < max_examples:
            text = _safe_text(_get(note, "note_text", "description", "content", "summary", default=""))
            if text:
                examples.append({
                    "type": note_type_label(ntype),
                    "text": text,
                    "date": created.isoformat() if created else "",
                })

    total = sum(counts.values())
    negative_total = counts.get("negative_event", 0) + counts.get("development_need", 0)
    positive_total = counts.get("positive_event", 0) + counts.get("success", 0)

    if total == 0:
        balance_label = "Dönem içi not kaydı bulunmuyor"
        balance_level = "info"
    elif negative_total >= 3 and negative_total > positive_total:
        balance_label = "Gelişim ihtiyacı yoğunluğu dikkat gerektiriyor"
        balance_level = "risk"
    elif positive_total >= negative_total and positive_total > 0:
        balance_label = "Olumlu kayıtlar ve başarı notları öne çıkıyor"
        balance_level = "success"
    else:
        balance_label = "Dengeli ara gözlem kaydı bulunuyor"
        balance_level = "attention"

    return {
        "total_notes": total,
        "counts": counts,
        "counts_labelled": {NOTE_TYPE_LABELS.get(k, k): v for k, v in counts.items() if v},
        "positive_total": positive_total,
        "negative_total": negative_total,
        "development_need_total": counts.get("development_need", 0),
        "out_of_period_count": out_of_period_count,
        "balance_label": balance_label,
        "balance_level": balance_level,
        "examples": examples,
    }


def build_interim_feedback_signals(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    total = int(summary.get("total_notes") or 0)
    positive_total = int(summary.get("positive_total") or 0)
    negative_total = int(summary.get("negative_total") or 0)
    development_total = int(summary.get("development_need_total") or 0)
    out_of_period_count = int(summary.get("out_of_period_count") or 0)

    signals: list[InterimFeedbackSignal] = []
    if total == 0:
        signals.append(InterimFeedbackSignal(
            code="no_interim_note",
            title="Ara not kaydı bulunmuyor",
            message="Bu dönem için değerlendirmeye destek olacak ara gözlem kaydı bulunamadı.",
            severity="attention",
            action_label="Not ekle",
        ))
    if negative_total >= 2:
        signals.append(InterimFeedbackSignal(
            code="negative_concentration",
            title="Olumsuz/gelişim odaklı kayıt yoğunluğu",
            message="Dönem içi notlarda birden fazla olumsuz olay veya gelişim ihtiyacı görünüyor. Puanlama öncesinde notların birlikte değerlendirilmesi önerilir.",
            severity="risk" if negative_total >= 3 else "attention",
            action_label="Notları incele",
        ))
    if development_total > 0:
        signals.append(InterimFeedbackSignal(
            code="development_need",
            title="Gelişim önerisi bağlantısı kurulabilir",
            message="Gelişim ihtiyacı içeren ara notlar var. Karne yayınından önce gelişim önerisi alanıyla ilişkilendirilmesi yararlı olur.",
            severity="attention",
            action_label="Gelişim notu hazırla",
        ))
    if positive_total > 0:
        signals.append(InterimFeedbackSignal(
            code="positive_records",
            title="Olumlu kayıtlar dikkate alınmalı",
            message="Başarı veya olumlu olay notları bulunuyor. Nihai değerlendirme yapılırken bu kayıtların da görülmesi önerilir.",
            severity="success",
            action_label="Olumlu notları gör",
        ))
    if out_of_period_count > 0:
        signals.append(InterimFeedbackSignal(
            code="period_scope_check",
            title="Dönem kapsamı kontrolü",
            message="Bazı ara notların tarihi dönem aralığı dışında görünüyor. Kayıt tarihi ve dönem ilişkisi kontrol edilmelidir.",
            severity="attention",
            action_label="Kapsamı kontrol et",
        ))
    return [s.to_dict() for s in signals]


def build_interim_feedback_decision_support(
    notes: Sequence[Any],
    *,
    period_start: Any = None,
    period_end: Any = None,
    viewer_role: str = "",
) -> dict[str, Any]:
    summary = summarize_interim_notes(notes, period_start=period_start, period_end=period_end)
    signals = build_interim_feedback_signals(summary)
    return {
        "module": "Performans İçi Ara Not / Geri Bildirim",
        "principle": "Bu çıktı puan üretmez; yalnızca dönem içi notların değerlendirme öncesi hatırlatılmasını sağlar.",
        "viewer_role": viewer_role or "Yetkili kullanıcı",
        "summary": summary,
        "signals": signals,
        "safe_visibility_note": "Kişi detayı ve hassas içerik yerine yetki kapsamındaki özet ve yönlendirme gösterilir.",
        "status": "hazır",
    }
