from __future__ import annotations

import logging

"""BYS360 AI Karar Destek Faz 6 düşük performans onay entegrasyonu.

Performans değerlendirme kaydını güvenli karar destek süreci özetine dönüştürür.
Bu çıktı idari karar değildir; Başkan/Üst Onay ve yayın kilidi gerekliliklerini
yetkili kullanıcıya görünür kılar.

BYS360_AI_DECISION_FAZ6_LOW_PERFORMANCE_INTEGRATION
"""

from datetime import date, datetime
from typing import Any, Iterable, Mapping

from .low_performance_approval_policy import (
    LowPerformanceApprovalPolicy,
    build_low_performance_policy,
    display_score,
    low_score_level,
    normalize_process_label,
    safe_attr,
    score_requires_upper_approval,
    score_to_float,
)

logger = logging.getLogger(__name__)


def _person_name(evaluation: Any) -> str:
    person = safe_attr(evaluation, "user", "employee", "personnel", default=None)
    full = safe_attr(person, "full_name", "name", "display_name", default=None)
    if full:
        return str(full)
    first = safe_attr(person, "first_name", "ad", default="")
    last = safe_attr(person, "last_name", "soyad", default="")
    return f"{first} {last}".strip() or "Personel"


def _user_id(evaluation: Any) -> Any:
    return safe_attr(evaluation, "user_id", "personnel_id", "employee_id", default=None)


def _period_title(evaluation: Any) -> str:
    period = safe_attr(evaluation, "period", default=None)
    title = safe_attr(period, "title", "name", "period_name", default=None)
    if title:
        return str(title)
    return str(safe_attr(evaluation, "period_title", "period_name", default="Dönem Bilgisi Yok"))


def _period_year(evaluation: Any) -> int | None:
    period = safe_attr(evaluation, "period", default=None)
    for source in (evaluation, period):
        year = safe_attr(source, "year", "period_year", default=None)
        if year not in (None, ""):
            try:
                return int(year)
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                import logging
                logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai_decision/low_performance_approval_integration.py")
        start = safe_attr(source, "start_date", "date_start", default=None)
        if start:
            if isinstance(start, (date, datetime)):
                return int(start.year)
            try:
                return int(str(start)[:4])
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                import logging
                logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai_decision/low_performance_approval_integration.py")
    return None


def _evaluation_score(evaluation: Any) -> Any:
    return safe_attr(
        evaluation,
        "final_score",
        "weighted_score",
        "score",
        "overall_score",
        "average_score",
        "result_score",
        default=None,
    )


def _general_comment(evaluation: Any) -> str:
    text = safe_attr(
        evaluation,
        "general_comment",
        "comment",
        "summary",
        "result_note",
        "manager_comment",
        default=None,
    )
    if text is None or str(text).strip() == "":
        return "Genel değerlendirme metni bulunamadı."
    return str(text).strip()


def _status(evaluation: Any) -> str:
    return normalize_process_label(
        safe_attr(evaluation, "status", "state", "result_status", "publish_status", default=None)
    )


def _approval_completed(evaluation: Any) -> bool:
    raw = str(
        safe_attr(
            evaluation,
            "president_approval_status",
            "upper_approval_status",
            "low_score_approval_status",
            "approval_status",
            default="",
        )
    ).strip().lower()
    if raw in {"approved", "approved_by_president", "approved_by_upper", "onaylandı", "onaylandi"}:
        return True
    marker = safe_attr(evaluation, "president_approved_at", "upper_approved_at", default=None)
    return marker not in (None, "")


def _build_timeline(
    requires_approval: bool,
    approval_completed: bool,
    level: Mapping[str, str],
    policy: LowPerformanceApprovalPolicy,
) -> list[dict[str, str]]:
    if not requires_approval:
        return [
            {"title": "Değerlendirme sonucu", "body": "Bu kayıt düşük performans üst onay sürecine girmiyor.", "tone": "info"},
            {"title": "Yayın hazırlığı", "body": "Genel yayın kuralları tamamlandığında personele açılabilir.", "tone": "success"},
        ]
    items = [
        {"title": "Düşük performans tespiti", "body": "Nihai puan 70 altı olduğu için özel süreç başlatılmalıdır.", "tone": "warning"},
        {"title": "Başkan/Üst Onay", "body": "Kayıt doğrudan Başkan/Üst Onay ekranında izlenmelidir.", "tone": "warning"},
    ]
    if policy.require_low_score_general_comment:
        items.append({"title": "Gerekçeli genel görüş", "body": "70 altı sonuç için ayrıntılı genel görüş bulunmalıdır.", "tone": "warning"})
    items.append({"title": level.get("label", "Düşük Performans Kaydı"), "body": level.get("action", "Personel süreç kaydı oluşturulmalıdır."), "tone": "warning"})
    if approval_completed:
        items.append({"title": "Onay durumu", "body": "Başkan/Üst Onay tamamlanmış görünüyor; yayın öncesi kurumsal kontrol sürdürülmelidir.", "tone": "success"})
    else:
        items.append({"title": "Yayın kilidi", "body": "Onay tamamlanmadan karne personele yayınlanmış sonuç sayılmamalıdır.", "tone": "danger"})
    return items


def build_low_performance_approval_payload(
    evaluation: Any,
    prior_low_count_same_year: int = 0,
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    policy = build_low_performance_policy(settings)
    score = _evaluation_score(evaluation)
    numeric = score_to_float(score)
    requires_approval = score_requires_upper_approval(score, policy)
    approval_completed = _approval_completed(evaluation)
    level = low_score_level(prior_low_count_same_year)
    publish_locked = bool(requires_approval and policy.lock_publish_until_upper_approval and not approval_completed)

    if numeric is None:
        headline = "Nihai puan henüz oluşmadı"
        status_label = "Süreç Kontrolü Bekliyor"
        decision = "Puan oluşmadan düşük performans süreci üretilemez."
        tone = "neutral"
    elif requires_approval:
        headline = "Başkan/Üst Onay gerektiren düşük performans"
        status_label = "Başkan/Üst Onay Bekliyor" if not approval_completed else "Başkan/Üst Onay Tamamlandı"
        decision = "Onay ve personel süreç kaydı tamamlanmadan karne personele açılmamalıdır."
        tone = "danger" if publish_locked else "warning"
    else:
        headline = "Düşük performans üst onayı gerekmiyor"
        status_label = "Genel Yayın Kontrolüne Uygun"
        decision = "Bu kayıt 70 altı özel onay kapsamına girmiyor."
        tone = "success"

    return {
        "ok": True,
        "module": "AI Karar Destek - Düşük Performans ve Üst Onay",
        "evaluation_id": safe_attr(evaluation, "id", default=None),
        "personnel": {"id": _user_id(evaluation), "name": _person_name(evaluation)},
        "period": {"id": safe_attr(evaluation, "period_id", default=None), "title": _period_title(evaluation), "year": _period_year(evaluation)},
        "score": {"value": display_score(score), "numeric": numeric},
        "current_status": _status(evaluation),
        "process": {
            "headline": headline,
            "status_label": status_label,
            "requires_upper_approval": requires_approval,
            "approval_completed": approval_completed,
            "publish_locked": publish_locked,
            "repeat_level": level,
            "decision_note": decision,
            "tone": tone,
        },
        "general_comment": _general_comment(evaluation),
        "timeline": _build_timeline(requires_approval, approval_completed, level, policy),
        "safeguards": [
            "70 altı sonuçlar Başkan/Üst Onay tamamlanmadan personele yayınlanmış sonuç sayılmaz.",
            "Sistem otomatik işten çıkarma işlemi yapmaz; yalnızca süreç sinyali üretir.",
            "İK/Admin ara onay kapısı değildir; takip ve yayın hazırlığı rolünde izler.",
            "Karar destek çıktısı nihai idari karar yerine geçmez.",
        ],
        "policy": policy.to_dict(),
        "marker": "BYS360_AI_DECISION_FAZ6_LOW_PERFORMANCE_PAYLOAD_OK",
    }


def build_low_performance_bulk_summary(
    evaluations: Iterable[Any],
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    policy = build_low_performance_policy(settings)
    total = low = locked = approved = missing = 0
    rows: list[dict[str, Any]] = []
    for evaluation in evaluations:
        total += 1
        score = _evaluation_score(evaluation)
        numeric = score_to_float(score)
        if numeric is None:
            missing += 1
        requires = score_requires_upper_approval(score, policy)
        completed = _approval_completed(evaluation)
        if requires:
            low += 1
            if completed:
                approved += 1
            else:
                locked += 1
        rows.append({
            "evaluation_id": safe_attr(evaluation, "id", default=None),
            "personnel": _person_name(evaluation),
            "period": _period_title(evaluation),
            "score": display_score(score),
            "requires_upper_approval": requires,
            "publish_locked": bool(requires and not completed),
            "status": "Başkan/Üst Onay Tamamlandı" if completed and requires else ("Başkan/Üst Onay Bekliyor" if requires else "Genel Süreç"),
        })
    return {
        "ok": True,
        "module": "AI Karar Destek - Düşük Performans Toplu Süreç Özeti",
        "summary": {
            "total": total,
            "low_score_count": low,
            "publish_locked_count": locked,
            "upper_approval_completed_count": approved,
            "missing_score_count": missing,
        },
        "rows": rows[:100],
        "recommendations": [
            {"title": "Yayın kilitleri izlenmeli", "body": "Onay bekleyen 70 altı karneler personele açılmamalıdır.", "severity": "danger"} if locked else {"title": "Düşük performans yayın kilidi temiz", "body": "Seçilen kayıt havuzunda açık yayın kilidi görünmüyor.", "severity": "success"},
            {"title": "Süreç kaydı korunmalı", "body": "İlk ve tekrarlayan düşük performans kayıtları personel geçmişiyle ilişkilendirilmelidir.", "severity": "info"},
        ],
        "policy": policy.to_dict(),
        "marker": "BYS360_AI_DECISION_FAZ6_LOW_PERFORMANCE_BULK_OK",
    }
