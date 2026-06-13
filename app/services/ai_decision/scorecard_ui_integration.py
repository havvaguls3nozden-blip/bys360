
"""BYS360 AI Karar Destek Faz 5 karne ve puanlama entegrasyonu.

Bu servis performans değerlendirme kayıtlarını, karar destek panelinde
kullanılabilecek güvenli ve kurumsal bir özet yapısına dönüştürür. Kişi
mahremiyeti korunur; çıktı karar yerine geçmez.

BYS360_AI_DECISION_FAZ5_SCORECARD_UI_INTEGRATION
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .scorecard_ui_policy import (
    ScorecardUIPolicy,
    build_scorecard_ui_policy,
    clean_screen_text,
    display_score,
    normalize_status_label,
    safe_attr,
    score_band,
    score_to_float,
)

def _person_name(evaluation: Any) -> str:
    person = safe_attr(evaluation, "user", "employee", "personnel", default=None)
    full = safe_attr(person, "full_name", "name", "display_name", default=None)
    if full:
        return str(full)
    first = safe_attr(person, "first_name", "ad", default="")
    last = safe_attr(person, "last_name", "soyad", default="")
    return f"{first} {last}".strip() or "Personel"

def _period_title(evaluation: Any) -> str:
    period = safe_attr(evaluation, "period", default=None)
    title = safe_attr(period, "title", "name", "period_name", default=None)
    if title:
        return str(title)
    return str(safe_attr(evaluation, "period_title", "period_name", default="Dönem Bilgisi Yok"))

def _evaluation_score(evaluation: Any) -> Any:
    return safe_attr(evaluation, "final_score", "weighted_score", "score", "overall_score", "average_score", "result_score", default=None)

def _evaluation_status(evaluation: Any) -> str:
    return normalize_status_label(safe_attr(evaluation, "status", "state", "result_status", "publish_status", default=None))

def _general_comment(evaluation: Any) -> str:
    return clean_screen_text(
        safe_attr(evaluation, "general_comment", "comment", "summary", "result_note", "manager_comment", default=None),
        fallback="Bu kayıt için genel değerlendirme metni bulunamadı.",
    )

def _extract_items(evaluation: Any) -> list[Any]:
    for name in ("items", "evaluation_items", "criteria_items", "criterion_scores"):
        value = safe_attr(evaluation, name, default=None)
        if value is None:
            continue
        try:
            return list(value)
        except TypeError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/ai_decision/scorecard_ui_integration.py:60)")
            continue
    return []

def _criterion_title(item: Any) -> str:
    criterion = safe_attr(item, "criterion", default=None)
    return str(safe_attr(item, "criterion_title", "title", "name", default=None) or safe_attr(criterion, "title", "name", default="Değerlendirme Kriteri"))

def _build_criteria_cards(evaluation: Any) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for item in _extract_items(evaluation)[:80]:
        cards.append({
            "title": clean_screen_text(_criterion_title(item), fallback="Değerlendirme Kriteri"),
            "score": display_score(safe_attr(item, "score", "value", "converted_score", "weighted_score", default=None)),
            "comment": clean_screen_text(safe_attr(item, "comment", "explanation", "note", default=None), fallback="Kriter açıklaması bulunmuyor."),
        })
    return cards

def _build_supervisor_cards(evaluation: Any) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for prefix, title in [("first", "1. Amir"), ("second", "2. Amir"), ("third", "3. Amir")]:
        score = safe_attr(evaluation, f"{prefix}_supervisor_score", f"{prefix}_score", default=None)
        comment = safe_attr(evaluation, f"{prefix}_supervisor_comment", f"{prefix}_comment", default=None)
        supervisor = safe_attr(evaluation, f"{prefix}_supervisor", default=None)
        name = safe_attr(supervisor, "full_name", "name", default=None)
        if score in (None, "") and comment in (None, "") and name in (None, ""):
            continue
        cards.append({"title": title, "name": str(name or "Amir bilgisi"), "score": display_score(score), "comment": clean_screen_text(comment, fallback="Amir görüşü bulunmuyor.")})
    return cards

def _build_process_notes(evaluation: Any, policy: ScorecardUIPolicy) -> list[dict[str, str]]:
    score = score_to_float(_evaluation_score(evaluation))
    status = _evaluation_status(evaluation)
    notes: list[dict[str, str]] = [{"title": "Karne durumu", "body": status, "tone": "neutral"}]
    if score is None:
        notes.append({"title": "Puan oluşumu", "body": "Nihai puan henüz oluşmadı; yayın öncesi kontrol tamamlanmalıdır.", "tone": "neutral"})
    elif score < policy.low_score_limit:
        notes.append({"title": "Düşük performans kontrolü", "body": "Bu karne Başkan/Üst Onay tamamlanmadan personele açılmamalıdır.", "tone": "warning"})
        if policy.require_low_score_explanation:
            notes.append({"title": "Açıklama zorunluluğu", "body": "70 altı sonuç için ayrıntılı genel görüş bulunmalıdır.", "tone": "warning"})
    elif score >= policy.high_score_limit:
        notes.append({"title": "Yüksek başarı notu", "body": "90 ve üzeri sonuçlarda güçlü yönler ve sürdürülebilir gelişim notu görünür olmalıdır.", "tone": "success"})
        if policy.require_high_score_explanation:
            notes.append({"title": "Gerekçeli değerlendirme", "body": "90 üstü sonuç için ayrıntılı genel görüş kontrol edilmelidir.", "tone": "success"})
    else:
        notes.append({"title": "Yayın hazırlığı", "body": "Sonuç beklenen aralıkta; yetkili yayın kontrolü sonrası personele açılabilir.", "tone": "info"})
    return notes

def build_scorecard_decision_panel(evaluation: Any, settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    policy = build_scorecard_ui_policy(settings)
    score = _evaluation_score(evaluation)
    band = score_band(score, policy)
    return {
        "ok": True,
        "module": "AI Karar Destek - Karne ve Puanlama Ekranı",
        "evaluation_id": safe_attr(evaluation, "id", default=None),
        "period_id": safe_attr(evaluation, "period_id", default=None),
        "personnel": {"name": _person_name(evaluation)},
        "period": {"title": _period_title(evaluation)},
        "score": {"value": display_score(score), "band": band},
        "status": _evaluation_status(evaluation),
        "general_comment": _general_comment(evaluation),
        "criteria": _build_criteria_cards(evaluation),
        "supervisors": _build_supervisor_cards(evaluation),
        "process_notes": _build_process_notes(evaluation, policy),
        "recommendations": build_scorecard_recommendations(evaluation, policy),
        "policy": policy.to_dict(),
        "safeguards": [
            "Teknik ifadeler kullanıcı ekranında kurumsal Türkçe karşılıklarla gösterilir.",
            "Karar destek çıktısı idari karar yerine geçmez.",
            "Yetkisiz kullanıcıya kişi detayı açılmaz.",
            "70 altı sonuçlarda yayın kilidi ve üst onay süreci korunur.",
        ],
        "marker": "BYS360_AI_DECISION_FAZ5_SCORECARD_PANEL_OK",
    }

def build_scorecard_recommendations(evaluation: Any, policy: ScorecardUIPolicy) -> list[dict[str, str]]:
    score = score_to_float(_evaluation_score(evaluation))
    comments = _general_comment(evaluation)
    recs: list[dict[str, str]] = []
    if score is None:
        recs.append({"title": "Karne tamamlanma durumu kontrol edilsin", "body": "Nihai puan oluşmadan yayın veya personel görünürlüğü açılmamalıdır.", "severity": "info"})
    elif score < policy.low_score_limit:
        recs.append({"title": "Başkan/Üst Onay süreci takip edilsin", "body": "70 altı sonuç için onay ve personel süreç kaydı tamamlanmadan karne yayınlanmamalıdır.", "severity": "warning"})
    elif score >= policy.high_score_limit:
        recs.append({"title": "Güçlü yönler görünür kılınsın", "body": "Yüksek başarı sonucu gelişim ve örnek uygulama notuyla desteklenmelidir.", "severity": "success"})
    if comments == "Bu kayıt için genel değerlendirme metni bulunamadı.":
        recs.append({"title": "Genel değerlendirme metni eklenmeli", "body": "Karne okunabilirliği için yetkili kullanıcı tarafından anlaşılır genel görüş yazılmalıdır.", "severity": "warning"})
    if not recs:
        recs.append({"title": "Karne sunumu uygun", "body": "Kayıt mevcut karne görünüm kurallarına göre okunabilir durumda.", "severity": "info"})
    return recs

def build_scorecard_bulk_payload(evaluations: Iterable[Any], settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    policy = build_scorecard_ui_policy(settings)
    rows = list(evaluations)
    low = high = missing = 0
    status_counter: dict[str, int] = {}
    for item in rows:
        score = score_to_float(_evaluation_score(item))
        if score is None:
            missing += 1
        elif score < policy.low_score_limit:
            low += 1
        elif score >= policy.high_score_limit:
            high += 1
        label = _evaluation_status(item)
        status_counter[label] = status_counter.get(label, 0) + 1
    return {
        "ok": True,
        "module": "AI Karar Destek - Karne Toplu Görünüm Özeti",
        "summary": {"total": len(rows), "low_score_count": low, "high_score_count": high, "missing_score_count": missing, "status_distribution": status_counter},
        "recommendations": [
            {"title": "70 altı karneler onay sürecinde izlenmeli", "body": "Düşük performans karneleri Başkan/Üst Onay tamamlanmadan yayınlanmamalıdır.", "severity": "warning"} if low else {"title": "Düşük performans yayın kilidi temiz", "body": "Seçilen kayıt havuzunda 70 altı yayın riski görünmüyor.", "severity": "info"},
            {"title": "Karne dili sade tutulmalı", "body": "Kullanıcı ekranlarında teknik durum kodları yerine kurumsal Türkçe ifadeler gösterilmelidir.", "severity": "info"},
        ],
        "policy": policy.to_dict(),
        "marker": "BYS360_AI_DECISION_FAZ5_SCORECARD_BULK_OK",
    }
