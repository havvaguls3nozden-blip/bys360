from __future__ import annotations

from app.core.datetime_utils import utc_now

"""Faz 9: AI öneri motoru ve risk/önceliklendirme paneli.

Bu servis yalnızca okuma yapar. Mevcut AI günlükleri, öneriler, özet cache
ve maskeleme kurallarını birlikte değerlendirerek yöneticiye öncelik sırası,
risk gerekçesi ve güvenli aksiyon notu üretir. Öneri uygulamaz, kayıt
oluşturmaz, kayıt güncellemez ve nihai idari karar vermez.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models import (
    AIFeedbackLog,
    AIRecommendation,
    AIRedactionRule,
    AIRequestLog,
    AISummaryCache,
)
from app.services.ai.module_scope import filter_visible_values, is_visible_ai_module

# Faz 9 güvenlik sözleşmesi: otomatik karar/uygulama yoktur.
AI_FINAL_DECISION_ENABLED = False
AI_AUTO_APPLY_ENABLED = False
DB_WRITE_ENABLED = False
PRIORITY_PANEL_READ_ONLY = True
HUMAN_REVIEW_REQUIRED = True
MAX_LOOKBACK_DAYS = 180
DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_LIMIT = 50
MAX_LIMIT = 250
SLOW_LATENCY_MS = 1800
NEGATIVE_FEEDBACK_TYPES = {"not_helpful", "wrong", "unsafe", "negative"}

LIVE_MODULE_ORDER = ("performance", "hr", "survey", "feedback", "communication", "support", "analysis_center", "dashboard")
MODULE_LABELS = {
    "performance": "Performans",
    "hr": "Personel / İzin",
    "survey": "Anket",
    "feedback": "Geri Bildirim / Nabız",
    "communication": "İletişim",
    "support": "Yardım Merkezi",
    "analysis_center": "Analiz Merkezi",
    "dashboard": "Dashboard",
    "general": "Genel",
    "genel": "Genel",
    "": "Genel",
}
SEVERITY_LABELS = {
    "critical": "Kritik",
    "high": "Yüksek",
    "medium": "Orta",
    "info": "Bilgi",
    "low": "Düşük",
    "warning": "Uyarı",
    "danger": "Kritik",
}
STATUS_LABELS = {
    "open": "Açık",
    "reviewed": "İncelendi",
    "accepted": "Onaylandı",
    "dismissed": "Kapatıldı",
    "completed": "Tamamlandı",
    "warning": "Uyarı",
    "failed": "Hata",
    "error": "Hata",
}
SEVERITY_WEIGHTS = {
    "critical": 48,
    "danger": 48,
    "high": 34,
    "warning": 28,
    "medium": 22,
    "info": 10,
    "low": 8,
}
STATUS_WEIGHTS = {
    "open": 18,
    "reviewed": 8,
    "accepted": 2,
    "dismissed": 0,
}


@dataclass(frozen=True)
class ModuleSignal:
    module_type: str
    request_total: int = 0
    failed_total: int = 0
    warning_total: int = 0
    unmasked_total: int = 0
    slow_total: int = 0
    latency_avg: int = 0
    negative_feedback: int = 0
    open_recommendations: int = 0
    critical_recommendations: int = 0
    active_redaction_rules: int = 0
    expired_cache_total: int = 0
    target_signal_total: int = 0


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = MAX_LOOKBACK_DAYS) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


def _clean_key(value: Any, fallback: str = "general") -> str:
    key = str(value or "").strip().lower()
    return key or fallback


def _safe_text(value: Any, limit: int = 240) -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    if len(text) > limit:
        return text[: max(limit - 1, 0)].rstrip() + "…"
    return text


def _module_label(module_type: Any) -> str:
    key = _clean_key(module_type)
    return MODULE_LABELS.get(key, key.replace("_", " ").title())


def _severity_label(value: Any) -> str:
    key = _clean_key(value, "info")
    return SEVERITY_LABELS.get(key, key.replace("_", " ").title())


def _status_label(value: Any) -> str:
    key = _clean_key(value, "open")
    return STATUS_LABELS.get(key, key.replace("_", " ").title())


def _ratio(part: int, whole: int) -> int:
    if not whole:
        return 0
    return int(round((int(part or 0) / int(whole or 1)) * 100))


def _safe_avg(values: list[int]) -> int:
    values = [int(value or 0) for value in values if value is not None]
    if not values:
        return 0
    return int(round(sum(values) / len(values)))


def _priority_label(score: int) -> str:
    if score >= 80:
        return "Kritik öncelik"
    if score >= 58:
        return "Yüksek öncelik"
    if score >= 35:
        return "Orta öncelik"
    return "İzleme"


def _priority_tone(score: int) -> str:
    if score >= 80:
        return "danger"
    if score >= 58:
        return "warning"
    if score >= 35:
        return "calm"
    return "success"


def _format_dt(value: Any) -> str:
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    return str(value)


def _visible_module_filter(query, column):
    # Canlı kapsamdan çıkarılan eski modüller Faz 9 paneline taşınmaz.
    hidden = [key for key in ("education", "strategy", "repository", "portal") if not is_visible_ai_module(key)]
    if not hidden:
        return query
    return query.filter(func.lower(func.coalesce(column, "")).notin_(hidden))


def _request_rows(since: datetime, module_type: str = "") -> list[AIRequestLog]:
    query = AIRequestLog.query.filter(AIRequestLog.created_at >= since)
    query = _visible_module_filter(query, AIRequestLog.module_type)
    if module_type:
        query = query.filter(func.lower(AIRequestLog.module_type) == module_type)
    return query.order_by(AIRequestLog.created_at.desc()).limit(5000).all()


def _recommendation_rows(
    since: datetime,
    *,
    module_type: str = "",
    status: str = "",
    severity: str = "",
    limit: int = DEFAULT_LIMIT,
) -> list[AIRecommendation]:
    query = AIRecommendation.query.filter(AIRecommendation.created_at >= since)
    query = _visible_module_filter(query, AIRecommendation.module_type)
    if module_type:
        query = query.filter(func.lower(AIRecommendation.module_type) == module_type)
    if status:
        query = query.filter(func.lower(AIRecommendation.status) == status)
    if severity:
        query = query.filter(func.lower(AIRecommendation.severity) == severity)
    return query.order_by(AIRecommendation.created_at.desc(), AIRecommendation.id.desc()).limit(limit).all()


def _negative_feedback_counter(since: datetime, module_type: str = "") -> Counter[str]:
    query = (
        db.session.query(AIRequestLog.module_type, AIFeedbackLog.feedback_type)
        .join(AIRequestLog, AIFeedbackLog.ai_request_log_id == AIRequestLog.id)
        .filter(AIFeedbackLog.created_at >= since)
    )
    query = _visible_module_filter(query, AIRequestLog.module_type)
    if module_type:
        query = query.filter(func.lower(AIRequestLog.module_type) == module_type)
    counter: Counter[str] = Counter()
    for row_module, feedback_type in query.limit(5000).all():
        if _clean_key(feedback_type) in NEGATIVE_FEEDBACK_TYPES:
            counter[_clean_key(row_module)] += 1
    return counter


def _redaction_counter(module_type: str = "") -> Counter[str]:
    query = AIRedactionRule.query.filter(AIRedactionRule.is_active.is_(True))
    query = _visible_module_filter(query, AIRedactionRule.module_type)
    if module_type:
        query = query.filter(func.lower(AIRedactionRule.module_type) == module_type)
    counter: Counter[str] = Counter()
    for row_module, count in query.with_entities(AIRedactionRule.module_type, func.count(AIRedactionRule.id)).group_by(AIRedactionRule.module_type).all():
        counter[_clean_key(row_module)] = int(count or 0)
    return counter


def _summary_cache_counter(now: datetime, module_type: str = "") -> Counter[str]:
    query = AISummaryCache.query.filter(AISummaryCache.expires_at.isnot(None), AISummaryCache.expires_at < now)
    query = _visible_module_filter(query, AISummaryCache.module_type)
    if module_type:
        query = query.filter(func.lower(AISummaryCache.module_type) == module_type)
    counter: Counter[str] = Counter()
    for row_module, count in query.with_entities(AISummaryCache.module_type, func.count(AISummaryCache.id)).group_by(AISummaryCache.module_type).all():
        counter[_clean_key(row_module)] = int(count or 0)
    return counter


def _recommendation_counter(since: datetime, module_type: str = "") -> tuple[Counter[str], Counter[str], Counter[str]]:
    query = AIRecommendation.query.filter(AIRecommendation.created_at >= since)
    query = _visible_module_filter(query, AIRecommendation.module_type)
    if module_type:
        query = query.filter(func.lower(AIRecommendation.module_type) == module_type)
    open_counter: Counter[str] = Counter()
    critical_counter: Counter[str] = Counter()
    severity_counter: Counter[str] = Counter()
    for row_module, status, severity in query.with_entities(AIRecommendation.module_type, AIRecommendation.status, AIRecommendation.severity).limit(5000).all():
        key = _clean_key(row_module)
        sev_key = _clean_key(severity, "info")
        severity_counter[sev_key] += 1
        if _clean_key(status, "open") == "open":
            open_counter[key] += 1
        if sev_key in {"critical", "danger", "high"}:
            critical_counter[key] += 1
    return open_counter, critical_counter, severity_counter


def _module_signals(request_rows: list[AIRequestLog], since: datetime, now: datetime, module_type: str = "") -> dict[str, ModuleSignal]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "request_total": 0,
            "failed_total": 0,
            "warning_total": 0,
            "unmasked_total": 0,
            "slow_total": 0,
            "latencies": [],
            "targets": set(),
        }
    )
    for row in request_rows:
        key = _clean_key(row.module_type)
        status = _clean_key(row.status, "completed")
        grouped[key]["request_total"] += 1
        if status in {"failed", "error"}:
            grouped[key]["failed_total"] += 1
        if status == "warning":
            grouped[key]["warning_total"] += 1
        if row.was_masked is False:
            grouped[key]["unmasked_total"] += 1
        if row.latency_ms is not None:
            latency = int(row.latency_ms or 0)
            grouped[key]["latencies"].append(latency)
            if latency >= SLOW_LATENCY_MS:
                grouped[key]["slow_total"] += 1
        target_key = f"{row.target_table or ''}:{row.target_id or ''}".strip(":")
        if target_key:
            grouped[key]["targets"].add(target_key)

    negative_counter = _negative_feedback_counter(since, module_type)
    redaction_counter = _redaction_counter(module_type)
    cache_counter = _summary_cache_counter(now, module_type)
    open_rec_counter, critical_rec_counter, _severity_counter = _recommendation_counter(since, module_type)

    keys = set(grouped) | set(negative_counter) | set(redaction_counter) | set(cache_counter) | set(open_rec_counter) | set(critical_rec_counter)
    if module_type:
        keys.add(module_type)
    if not keys:
        keys.update(filter_visible_values(LIVE_MODULE_ORDER))

    signals: dict[str, ModuleSignal] = {}
    for key in keys:
        values = grouped[key]
        signals[key] = ModuleSignal(
            module_type=key,
            request_total=int(values.get("request_total") or 0),
            failed_total=int(values.get("failed_total") or 0),
            warning_total=int(values.get("warning_total") or 0),
            unmasked_total=int(values.get("unmasked_total") or 0),
            slow_total=int(values.get("slow_total") or 0),
            latency_avg=_safe_avg(values.get("latencies") or []),
            negative_feedback=int(negative_counter.get(key, 0)),
            open_recommendations=int(open_rec_counter.get(key, 0)),
            critical_recommendations=int(critical_rec_counter.get(key, 0)),
            active_redaction_rules=int(redaction_counter.get(key, 0)),
            expired_cache_total=int(cache_counter.get(key, 0)),
            target_signal_total=len(values.get("targets") or []),
        )
    return signals


def _score_module(signal: ModuleSignal) -> int:
    score = 0
    score += min(signal.critical_recommendations * 18, 36)
    score += min(signal.open_recommendations * 4, 20)
    score += min(signal.failed_total * 7, 28)
    score += min(signal.warning_total * 4, 16)
    score += min(signal.unmasked_total * 10, 30)
    score += min(signal.negative_feedback * 8, 24)
    score += min(signal.slow_total * 4, 16)
    score += min(signal.expired_cache_total * 2, 12)
    if signal.request_total and signal.active_redaction_rules == 0:
        score += 14
    if signal.latency_avg >= SLOW_LATENCY_MS:
        score += 10
    return min(score, 100)


def _module_reasons(signal: ModuleSignal) -> list[str]:
    reasons: list[str] = []
    if signal.critical_recommendations:
        reasons.append(f"{signal.critical_recommendations} yüksek/kritik açık öneri")
    if signal.failed_total:
        reasons.append(f"{signal.failed_total} hata kaydı")
    if signal.unmasked_total:
        reasons.append(f"{signal.unmasked_total} maskesiz AI isteği")
    if signal.negative_feedback:
        reasons.append(f"{signal.negative_feedback} negatif geri bildirim")
    if signal.slow_total:
        reasons.append(f"{signal.slow_total} yavaş AI işlemi")
    if signal.expired_cache_total:
        reasons.append(f"{signal.expired_cache_total} süresi geçmiş özet cache")
    if signal.request_total and signal.active_redaction_rules == 0:
        reasons.append("aktif maskeleme kuralı görünmüyor")
    if not reasons:
        reasons.append("izleme sinyali düşük")
    return reasons[:4]


def _safe_action_for_module(signal: ModuleSignal) -> str:
    if signal.unmasked_total:
        return "Maskeleme kuralları ve görünürlük kapsamı yönetişim ekranında kontrol edilmeli."
    if signal.critical_recommendations:
        return "Kritik açık öneriler yönetici incelemesine alınmalı; otomatik uygulama yapılmamalı."
    if signal.failed_total:
        return "Hata mesajları ve prompt sürümü birlikte incelenmeli; gerekirse istem kalitesi güncellenmeli."
    if signal.negative_feedback:
        return "Kullanıcı geri bildirimleri okunmalı ve ilgili modülün AI çıktıları kalite panosunda gözden geçirilmeli."
    if signal.expired_cache_total:
        return "Özet cache süresi ve kaynak hash eşleşmeleri kontrol edilmeli."
    return "Düzenli izleme yeterli; insan onayı olmadan işlem yapılmaz."


def _row_priority_score(rec: AIRecommendation, signal: ModuleSignal) -> int:
    severity = _clean_key(rec.severity, "info")
    status = _clean_key(rec.status, "open")
    score = SEVERITY_WEIGHTS.get(severity, 10) + STATUS_WEIGHTS.get(status, 4)
    score += min(signal.failed_total * 4, 16)
    score += min(signal.unmasked_total * 8, 24)
    score += min(signal.negative_feedback * 6, 18)
    score += min(signal.slow_total * 2, 10)
    if signal.request_total and signal.active_redaction_rules == 0:
        score += 8
    created_at = getattr(rec, "created_at", None)
    if isinstance(created_at, datetime):
        age_days = max((utc_now() - created_at).days, 0)
        if status == "open":
            score += min(age_days, 14)
    return min(score, 100)


def _recommendation_row(rec: AIRecommendation, signal: ModuleSignal) -> dict[str, Any]:
    score = _row_priority_score(rec, signal)
    reasons = []
    severity = _clean_key(rec.severity, "info")
    status = _clean_key(rec.status, "open")
    if severity in {"critical", "danger", "high"}:
        reasons.append(f"önem derecesi: {_severity_label(severity)}")
    if status == "open":
        reasons.append("öneri açık durumda")
    reasons.extend(_module_reasons(signal))
    return {
        "id": rec.id,
        "module_type": _clean_key(rec.module_type),
        "module_label": _module_label(rec.module_type),
        "target_table": _safe_text(rec.target_table, 80),
        "target_id": rec.target_id,
        "recommendation_type": _safe_text(rec.recommendation_type, 80),
        "title": _safe_text(rec.title, 160),
        "body": _safe_text(rec.body, 320),
        "severity": severity,
        "severity_label": _severity_label(severity),
        "status": status,
        "status_label": _status_label(status),
        "score": score,
        "priority_label": _priority_label(score),
        "tone": _priority_tone(score),
        "created_at": _format_dt(getattr(rec, "created_at", None)),
        "reasons": reasons[:5],
        "safe_action": _safe_action_for_module(signal),
        "human_review_required": True,
    }


def _module_row(signal: ModuleSignal) -> dict[str, Any]:
    score = _score_module(signal)
    return {
        "module_type": signal.module_type,
        "module_label": _module_label(signal.module_type),
        "request_total": signal.request_total,
        "failed_total": signal.failed_total,
        "warning_total": signal.warning_total,
        "unmasked_total": signal.unmasked_total,
        "slow_total": signal.slow_total,
        "latency_avg": signal.latency_avg,
        "negative_feedback": signal.negative_feedback,
        "open_recommendations": signal.open_recommendations,
        "critical_recommendations": signal.critical_recommendations,
        "active_redaction_rules": signal.active_redaction_rules,
        "expired_cache_total": signal.expired_cache_total,
        "target_signal_total": signal.target_signal_total,
        "risk_score": score,
        "risk_label": _priority_label(score),
        "tone": _priority_tone(score),
        "reasons": _module_reasons(signal),
        "safe_action": _safe_action_for_module(signal),
    }


def _risk_cards(module_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals = {
        "unmasked": sum(row["unmasked_total"] for row in module_rows),
        "critical": sum(row["critical_recommendations"] for row in module_rows),
        "failed": sum(row["failed_total"] for row in module_rows),
        "negative": sum(row["negative_feedback"] for row in module_rows),
        "stale_cache": sum(row["expired_cache_total"] for row in module_rows),
        "slow": sum(row["slow_total"] for row in module_rows),
    }
    return [
        {
            "title": "KVKK / Maskeleme riski",
            "value": totals["unmasked"],
            "tone": "danger" if totals["unmasked"] else "success",
            "body": "Maskesiz görünen AI isteği varsa önce maskeleme ve görünürlük kuralı incelenir.",
        },
        {
            "title": "Kritik açık öneriler",
            "value": totals["critical"],
            "tone": "warning" if totals["critical"] else "success",
            "body": "Kritik öneriler otomatik uygulanmaz; yönetici incelemesi ve gerekçe kaydı gerekir.",
        },
        {
            "title": "Hata / uyarı yoğunluğu",
            "value": totals["failed"],
            "tone": "warning" if totals["failed"] else "success",
            "body": "Hata birikimi prompt, sağlayıcı ve hedef veri kalitesiyle birlikte okunur.",
        },
        {
            "title": "Negatif geri bildirim",
            "value": totals["negative"],
            "tone": "warning" if totals["negative"] else "success",
            "body": "Kullanıcı güvenini etkileyen sinyaller kalite panosuna taşınır.",
        },
        {
            "title": "Cache / güncellik sinyali",
            "value": totals["stale_cache"],
            "tone": "calm" if totals["stale_cache"] else "success",
            "body": "Süresi geçmiş özetler nihai karar girdisi kabul edilmez; yalnızca kontrol sinyalidir.",
        },
        {
            "title": "Yavaş işlem sinyali",
            "value": totals["slow"],
            "tone": "calm" if totals["slow"] else "success",
            "body": "Gecikme artışı kullanıcı deneyimi ve raporlama akışında önceliklendirilir.",
        },
    ]


def _generated_actions(module_rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    rows = sorted(module_rows, key=lambda row: (-int(row.get("risk_score") or 0), row.get("module_label") or ""))
    actions: list[dict[str, Any]] = []
    for row in rows:
        if int(row.get("risk_score") or 0) < 20 and len(actions) >= 3:
            continue
        actions.append(
            {
                "module_label": row["module_label"],
                "title": f"{row['module_label']} için öncelik notu",
                "score": row["risk_score"],
                "tone": row["tone"],
                "body": row["safe_action"],
                "reasons": row["reasons"],
            }
        )
        if len(actions) >= limit:
            break
    if actions:
        return actions
    return [
        {
            "module_label": "Genel",
            "title": "Düzenli izleme",
            "score": 0,
            "tone": "success",
            "body": "Kritik AI risk sinyali görünmüyor. Panel izlenmeye devam edebilir.",
            "reasons": ["veri düşük riskli"],
        }
    ]


def _module_options(request_rows: list[AIRequestLog], recommendation_rows: list[AIRecommendation]) -> list[dict[str, str]]:
    values = {getattr(row, "module_type", "") for row in request_rows}
    values.update(getattr(row, "module_type", "") for row in recommendation_rows)
    values.update(LIVE_MODULE_ORDER)
    ordered = filter_visible_values(values)
    ordered.sort(key=lambda item: (LIVE_MODULE_ORDER.index(item) if item in LIVE_MODULE_ORDER else 99, _module_label(item)))
    return [{"value": key, "label": _module_label(key)} for key in ordered]


def build_ai_recommendation_priority_snapshot(
    *,
    lookback_days: Any = DEFAULT_LOOKBACK_DAYS,
    module_type: str = "",
    status: str = "",
    severity: str = "",
    limit: Any = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Faz 9 panel payloadı. Yalnızca okuma ve bellek içi hesaplama yapar."""
    days = _safe_int(lookback_days, DEFAULT_LOOKBACK_DAYS, 1, MAX_LOOKBACK_DAYS)
    row_limit = _safe_int(limit, DEFAULT_LIMIT, 5, MAX_LIMIT)
    module_filter = _clean_key(module_type, "") if module_type else ""
    status_filter = _clean_key(status, "") if status else ""
    severity_filter = _clean_key(severity, "") if severity else ""
    now = utc_now()
    since = now - timedelta(days=days)

    requests = _request_rows(since, module_filter)
    rec_rows_raw = _recommendation_rows(
        since,
        module_type=module_filter,
        status=status_filter,
        severity=severity_filter,
        limit=row_limit,
    )
    signals = _module_signals(requests, since, now, module_filter)
    module_rows = [_module_row(signal) for signal in signals.values()]
    module_rows.sort(key=lambda row: (-int(row.get("risk_score") or 0), row.get("module_label") or ""))

    priority_rows = [
        _recommendation_row(rec, signals.get(_clean_key(rec.module_type), ModuleSignal(module_type=_clean_key(rec.module_type))))
        for rec in rec_rows_raw
    ]
    priority_rows.sort(key=lambda row: (-int(row.get("score") or 0), row.get("created_at") or ""))

    total_requests = sum(row["request_total"] for row in module_rows)
    total_open = sum(row["open_recommendations"] for row in module_rows)
    total_critical = sum(row["critical_recommendations"] for row in module_rows)
    total_unmasked = sum(row["unmasked_total"] for row in module_rows)
    highest_risk = module_rows[0] if module_rows else None
    summary_cards = [
        {
            "label": "Önceliklendirilmiş öneri",
            "value": len(priority_rows),
            "mini": f"Açık öneri toplamı {total_open}; bu panel otomatik işlem yapmaz.",
            "tone": "calm",
        },
        {
            "label": "En yüksek risk skoru",
            "value": highest_risk["risk_score"] if highest_risk else 0,
            "mini": highest_risk["module_label"] if highest_risk else "Kritik sinyal yok",
            "tone": highest_risk["tone"] if highest_risk else "success",
        },
        {
            "label": "Kritik/yüksek öneri",
            "value": total_critical,
            "mini": "Yönetici incelemesi gerektirir.",
            "tone": "warning" if total_critical else "success",
        },
        {
            "label": "KVKK maskeleme uyarısı",
            "value": total_unmasked,
            "mini": "Maskesiz istek varsa önce yönetişim kontrolü yapılır.",
            "tone": "danger" if total_unmasked else "success",
        },
        {
            "label": "AI işlem sinyali",
            "value": total_requests,
            "mini": f"Son {days} gün · canlı modül kapsamı",
            "tone": "muted",
        },
    ]

    return {
        "page_title": "AI Öneri Motoru ve Risk Önceliklendirme",
        "generated_at": now,
        "lookback_days": days,
        "filters": {
            "module_type": module_filter,
            "status": status_filter,
            "severity": severity_filter,
            "limit": row_limit,
        },
        "module_options": _module_options(requests, rec_rows_raw),
        "status_options": [{"value": key, "label": label} for key, label in STATUS_LABELS.items() if key in {"open", "reviewed", "accepted", "dismissed"}],
        "severity_options": [{"value": key, "label": label} for key, label in SEVERITY_LABELS.items() if key in {"critical", "high", "medium", "info", "low", "warning"}],
        "summary_cards": summary_cards,
        "priority_rows": priority_rows,
        "module_rows": module_rows,
        "risk_cards": _risk_cards(module_rows),
        "generated_actions": _generated_actions(module_rows),
        "safety_contract": {
            "AI_FINAL_DECISION_ENABLED": AI_FINAL_DECISION_ENABLED,
            "AI_AUTO_APPLY_ENABLED": AI_AUTO_APPLY_ENABLED,
            "DB_WRITE_ENABLED": DB_WRITE_ENABLED,
            "PRIORITY_PANEL_READ_ONLY": PRIORITY_PANEL_READ_ONLY,
            "HUMAN_REVIEW_REQUIRED": HUMAN_REVIEW_REQUIRED,
        },
    }


def export_recommendation_priority_rows(snapshot: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for row in snapshot.get("priority_rows") or []:
        rows.append(
            [
                row.get("id"),
                row.get("module_label"),
                row.get("recommendation_type"),
                row.get("title"),
                row.get("severity_label"),
                row.get("status_label"),
                row.get("score"),
                row.get("priority_label"),
                " | ".join(row.get("reasons") or []),
                row.get("safe_action"),
                row.get("created_at"),
            ]
        )
    return rows
