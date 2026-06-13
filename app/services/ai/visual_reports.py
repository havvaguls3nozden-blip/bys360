from __future__ import annotations



from app.core.datetime_utils import utc_now
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models import AIFeedbackLog, AIRecommendation, AIRequestLog, AIRedactionRule, AISummaryCache

# Faz 8 sabit sözleşmesi: bu servis yalnızca okuma ve görselleştirme verisi üretir.
GERCEK_ICE_AKTARIM_YOK = True
DB_WRITE_ENABLED = False
VISUAL_REPORT_READ_ONLY = True
DEFAULT_LOOKBACK_DAYS = 30
MAX_LOOKBACK_DAYS = 180
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
    "genel": "Genel",
    "general": "Genel",
    "": "Genel",
}
STATUS_LABELS = {
    "completed": "Tamamlandı",
    "success": "Başarılı",
    "warning": "Uyarı",
    "failed": "Hata",
    "error": "Hata",
    "open": "Açık",
    "reviewed": "İncelendi",
    "accepted": "Onaylandı",
    "dismissed": "Kapatıldı",
    "unknown": "Belirsiz",
}
FEEDBACK_NEGATIVE_TYPES = {"not_helpful", "wrong", "unsafe", "negative"}


@dataclass(frozen=True)
class _ModuleMetrics:
    module_type: str
    request_total: int
    success_total: int
    warning_total: int
    failed_total: int
    masked_total: int
    unmasked_total: int
    open_recommendations: int
    critical_recommendations: int
    negative_feedback: int
    avg_latency_ms: int


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = MAX_LOOKBACK_DAYS) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


def _clean_key(value: Any, fallback: str = "genel") -> str:
    key = str(value or "").strip().lower()
    return key or fallback


def _label_module(module_type: str | None) -> str:
    key = _clean_key(module_type)
    return MODULE_LABELS.get(key, key.replace("_", " ").title())


def _label_status(status: str | None) -> str:
    key = _clean_key(status, "unknown")
    return STATUS_LABELS.get(key, key.replace("_", " ").title())


def _ratio(part: int, whole: int) -> int:
    if not whole:
        return 0
    return int(round((part / whole) * 100))


def _tone_from_score(score: int) -> str:
    if score >= 80:
        return "success"
    if score >= 55:
        return "warning"
    return "danger"


def _bar_rows(counter: Counter[str], *, labels: dict[str, str] | None = None, limit: int = 8) -> list[dict[str, Any]]:
    labels = labels or {}
    items = counter.most_common(limit)
    max_value = max([count for _, count in items] or [1])
    rows: list[dict[str, Any]] = []
    for key, value in items:
        width = _ratio(int(value or 0), max_value)
        rows.append(
            {
                "key": key,
                "label": labels.get(key, _label_module(key)),
                "value": int(value or 0),
                "width": max(width, 4 if value else 0),
            }
        )
    return rows


def _date_range(days: int) -> list[datetime.date]:
    today = utc_now().date()
    start = today - timedelta(days=max(days - 1, 0))
    return [start + timedelta(days=offset) for offset in range(days)]


def _safe_avg(values: list[int]) -> int:
    values = [int(value or 0) for value in values if value is not None]
    if not values:
        return 0
    return int(round(sum(values) / len(values)))


def _read_request_rows(since: datetime, module_type: str = "") -> list[AIRequestLog]:
    query = AIRequestLog.query.filter(AIRequestLog.created_at >= since)
    if module_type:
        query = query.filter(func.lower(AIRequestLog.module_type) == module_type)
    return query.order_by(AIRequestLog.created_at.asc()).limit(5000).all()


def _recommendation_counter(since: datetime, module_type: str = "") -> Counter[str]:
    query = AIRecommendation.query.filter(AIRecommendation.created_at >= since)
    if module_type:
        query = query.filter(func.lower(AIRecommendation.module_type) == module_type)
    rows = query.with_entities(AIRecommendation.module_type, AIRecommendation.status, AIRecommendation.severity).all()
    counter: Counter[str] = Counter()
    for row_module, row_status, row_severity in rows:
        key = _clean_key(row_module)
        status = _clean_key(row_status)
        severity = _clean_key(row_severity)
        counter[f"module::{key}"] += 1
        if status == "open":
            counter[f"open::{key}"] += 1
        if severity in {"critical", "high", "danger"}:
            counter[f"critical::{key}"] += 1
    return counter


def _negative_feedback_counter(since: datetime, module_type: str = "") -> Counter[str]:
    query = (
        db.session.query(AIRequestLog.module_type, AIFeedbackLog.feedback_type)
        .join(AIRequestLog, AIFeedbackLog.ai_request_log_id == AIRequestLog.id)
        .filter(AIFeedbackLog.created_at >= since)
    )
    if module_type:
        query = query.filter(func.lower(AIRequestLog.module_type) == module_type)
    counter: Counter[str] = Counter()
    for row_module, feedback_type in query.all():
        if _clean_key(feedback_type) in FEEDBACK_NEGATIVE_TYPES:
            counter[_clean_key(row_module)] += 1
    return counter


def _module_metrics(request_rows: list[AIRequestLog], since: datetime, module_type: str = "") -> list[_ModuleMetrics]:
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "request_total": 0,
        "success_total": 0,
        "warning_total": 0,
        "failed_total": 0,
        "masked_total": 0,
        "unmasked_total": 0,
        "latencies": [],
    })
    for row in request_rows:
        key = _clean_key(row.module_type)
        status = _clean_key(row.status, "unknown")
        grouped[key]["request_total"] += 1
        if status in {"completed", "success"}:
            grouped[key]["success_total"] += 1
        elif status == "warning":
            grouped[key]["warning_total"] += 1
        elif status in {"failed", "error"}:
            grouped[key]["failed_total"] += 1
        if row.was_masked is True:
            grouped[key]["masked_total"] += 1
        elif row.was_masked is False:
            grouped[key]["unmasked_total"] += 1
        if row.latency_ms is not None:
            grouped[key]["latencies"].append(int(row.latency_ms or 0))

    rec_counter = _recommendation_counter(since, module_type)
    negative_counter = _negative_feedback_counter(since, module_type)
    for raw_key in list(rec_counter):
        if raw_key.startswith("module::"):
            grouped[raw_key.split("::", 1)[1]]["request_total"] += 0
    for key in negative_counter:
        grouped[key]["request_total"] += 0

    metrics: list[_ModuleMetrics] = []
    ordered_keys = sorted(grouped, key=lambda item: (-int(grouped[item]["request_total"]), _label_module(item)))
    for key in ordered_keys:
        values = grouped[key]
        metrics.append(
            _ModuleMetrics(
                module_type=key,
                request_total=int(values["request_total"] or 0),
                success_total=int(values["success_total"] or 0),
                warning_total=int(values["warning_total"] or 0),
                failed_total=int(values["failed_total"] or 0),
                masked_total=int(values["masked_total"] or 0),
                unmasked_total=int(values["unmasked_total"] or 0),
                open_recommendations=int(rec_counter.get(f"open::{key}", 0)),
                critical_recommendations=int(rec_counter.get(f"critical::{key}", 0)),
                negative_feedback=int(negative_counter.get(key, 0)),
                avg_latency_ms=_safe_avg(values["latencies"]),
            )
        )
    return metrics


def _latency_buckets(request_rows: list[AIRequestLog]) -> Counter[str]:
    buckets: Counter[str] = Counter({"0-500 ms": 0, "500-1500 ms": 0, "1500-3000 ms": 0, "3000+ ms": 0})
    for row in request_rows:
        latency = int(row.latency_ms or 0)
        if latency <= 500:
            buckets["0-500 ms"] += 1
        elif latency <= 1500:
            buckets["500-1500 ms"] += 1
        elif latency <= 3000:
            buckets["1500-3000 ms"] += 1
        else:
            buckets["3000+ ms"] += 1
    return buckets


def _daily_trend_rows(request_rows: list[AIRequestLog], days: int) -> list[dict[str, Any]]:
    date_counts: Counter[str] = Counter()
    fail_counts: Counter[str] = Counter()
    for row in request_rows:
        label = row.created_at.date().isoformat() if row.created_at else utc_now().date().isoformat()
        date_counts[label] += 1
        if _clean_key(row.status) in {"failed", "error", "warning"}:
            fail_counts[label] += 1
    all_days = _date_range(days)
    max_value = max([date_counts.get(day.isoformat(), 0) for day in all_days] or [1]) or 1
    trend: list[dict[str, Any]] = []
    for day in all_days:
        key = day.isoformat()
        value = int(date_counts.get(key, 0))
        trend.append(
            {
                "date": key,
                "label": day.strftime("%d.%m"),
                "value": value,
                "risk_value": int(fail_counts.get(key, 0)),
                "height": max(_ratio(value, max_value), 3 if value else 0),
            }
        )
    return trend


def _report_cards(metrics: list[_ModuleMetrics]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in metrics[:10]:
        success_rate = _ratio(row.success_total, row.request_total)
        masked_rate = _ratio(row.masked_total, row.request_total)
        risk_penalty = min(60, row.failed_total * 12 + row.warning_total * 6 + row.open_recommendations * 5 + row.negative_feedback * 10 + row.unmasked_total * 8)
        signal_score = max(0, min(100, 72 + success_rate // 5 + masked_rate // 8 - risk_penalty))
        cards.append(
            {
                "module_type": row.module_type,
                "label": _label_module(row.module_type),
                "request_total": row.request_total,
                "success_rate": success_rate,
                "masked_rate": masked_rate,
                "open_recommendations": row.open_recommendations,
                "critical_recommendations": row.critical_recommendations,
                "negative_feedback": row.negative_feedback,
                "avg_latency_ms": row.avg_latency_ms,
                "signal_score": signal_score,
                "tone": _tone_from_score(signal_score),
                "note": _module_note(row, signal_score),
            }
        )
    if not cards:
        cards.append(
            {
                "module_type": "genel",
                "label": "Veri bekleniyor",
                "request_total": 0,
                "success_rate": 0,
                "masked_rate": 0,
                "open_recommendations": 0,
                "critical_recommendations": 0,
                "negative_feedback": 0,
                "avg_latency_ms": 0,
                "signal_score": 0,
                "tone": "muted",
                "note": "Seçilen aralıkta AI işlem kaydı bulunmadı. Ekran veri yazmaz; kayıt oluştukça kartlar otomatik dolar.",
            }
        )
    return cards


def _module_note(row: _ModuleMetrics, score: int) -> str:
    if row.unmasked_total:
        return "Maskesiz AI kaydı var; KVKK görünürlük kapısında öncelikli incelenmeli."
    if row.failed_total or row.warning_total:
        return "Hata/uyarı yoğunluğu var; işlem günlükleri ve istem sürümü birlikte okunmalı."
    if row.open_recommendations:
        return "Açık öneriler birikmeden yönetici kararıyla kapatılmalı."
    if score >= 80:
        return "Operasyon sinyali dengeli; izleme periyodu korunabilir."
    return "Kayıt sayısı veya kalite sinyali sınırlı; yönetsel takip önerilir."


def _risk_cards(request_rows: list[AIRequestLog], metrics: list[_ModuleMetrics]) -> list[dict[str, Any]]:
    total = len(request_rows)
    failed = sum(1 for row in request_rows if _clean_key(row.status) in {"failed", "error", "warning"})
    unmasked = sum(1 for row in request_rows if row.was_masked is False)
    slow = sum(1 for row in request_rows if int(row.latency_ms or 0) > 3000)
    open_recommendations = sum(row.open_recommendations for row in metrics)
    negative_feedback = sum(row.negative_feedback for row in metrics)
    active_rules = AIRedactionRule.query.filter(AIRedactionRule.is_active.is_(True)).count()
    cache_total = AISummaryCache.query.count()

    cards = [
        {
            "label": "KVKK maskeleme",
            "value": f"%{_ratio(total - unmasked, total)}",
            "tone": "success" if unmasked == 0 else "danger",
            "body": f"Maskesiz kayıt: {unmasked}. Aktif redaction kuralı: {active_rules}.",
        },
        {
            "label": "Hata / uyarı baskısı",
            "value": str(failed),
            "tone": "success" if failed == 0 else "warning",
            "body": f"Seçilen aralıkta {total} AI işleminden {failed} kayıt hata/uyarı sinyali taşıyor.",
        },
        {
            "label": "Açık öneri yükü",
            "value": str(open_recommendations),
            "tone": "success" if open_recommendations == 0 else "warning",
            "body": "Açık öneriler karar defterine bağlanmadan bekletilmemeli.",
        },
        {
            "label": "Yavaş işlem sinyali",
            "value": str(slow),
            "tone": "success" if slow == 0 else "warning",
            "body": "3000 ms üzerindeki AI işlemleri kullanıcı algısında yavaşlık oluşturabilir.",
        },
        {
            "label": "Negatif geri bildirim",
            "value": str(negative_feedback),
            "tone": "success" if negative_feedback == 0 else "danger",
            "body": "Yanlış, yararsız veya güvenli değil işaretleri istem kalitesi için okunur.",
        },
        {
            "label": "Özet cache",
            "value": str(cache_total),
            "tone": "success" if cache_total else "muted",
            "body": "Cache kayıtları özet üretiminin tekrar maliyetini azaltmak için izlenir.",
        },
    ]
    return cards


def _executive_notes(metrics: list[_ModuleMetrics], risk_cards: list[dict[str, Any]]) -> list[str]:
    danger_cards = [card for card in risk_cards if card.get("tone") == "danger"]
    warning_cards = [card for card in risk_cards if card.get("tone") == "warning"]
    busiest = max(metrics, key=lambda row: row.request_total, default=None)
    notes: list[str] = []
    if busiest and busiest.request_total:
        notes.append(f"En yoğun AI görünürlüğü {_label_module(busiest.module_type)} alanında: {busiest.request_total} işlem.")
    else:
        notes.append("Seçilen aralıkta henüz yoğun AI işlem verisi yok; pano veri oluştuğunda otomatik dolacaktır.")
    if danger_cards:
        notes.append("Kritik güvenlik/kalite sinyali var: " + ", ".join(card["label"] for card in danger_cards[:3]) + ".")
    elif warning_cards:
        notes.append("Uyarı düzeyinde takip gereken başlıklar var: " + ", ".join(card["label"] for card in warning_cards[:3]) + ".")
    else:
        notes.append("KVKK, hata ve öneri yükü tarafında kritik baskı görünmüyor.")
    notes.append("Bu ekran yalnızca okuma ve görselleştirme yapar; Excel ya da canlı veride gerçek içe aktarım/DB yazımı yapmaz.")
    return notes


def build_ai_visual_report_snapshot(*, lookback_days: Any = DEFAULT_LOOKBACK_DAYS, module_type: str = "") -> dict[str, Any]:
    days = _safe_int(lookback_days, DEFAULT_LOOKBACK_DAYS, 1, MAX_LOOKBACK_DAYS)
    selected_module = _clean_key(module_type, "") if module_type else ""
    since = utc_now() - timedelta(days=days)
    request_rows = _read_request_rows(since, selected_module)
    metrics = _module_metrics(request_rows, since, selected_module)

    module_counter = Counter(_clean_key(row.module_type) for row in request_rows)
    status_counter = Counter(_clean_key(row.status, "unknown") for row in request_rows)
    feature_counter = Counter(_clean_key(row.feature_type, "genel") for row in request_rows)
    latency_counter = _latency_buckets(request_rows)
    report_cards = _report_cards(metrics)
    risk_cards = _risk_cards(request_rows, metrics)

    total = len(request_rows)
    failed = sum(1 for row in request_rows if _clean_key(row.status) in {"failed", "error", "warning"})
    masked = sum(1 for row in request_rows if row.was_masked is True)
    unmasked = sum(1 for row in request_rows if row.was_masked is False)
    avg_latency = _safe_avg([int(row.latency_ms or 0) for row in request_rows if row.latency_ms is not None])
    open_rec_total = sum(row.open_recommendations for row in metrics)
    critical_rec_total = sum(row.critical_recommendations for row in metrics)
    negative_feedback_total = sum(row.negative_feedback for row in metrics)

    module_options = [
        {"value": key, "label": _label_module(key)}
        for key in sorted(set(LIVE_MODULE_ORDER) | set(module_counter.keys()), key=lambda item: _label_module(item))
    ]

    return {
        "page_title": "AI Görselleştirme ve Rapor Kartları",
        "selected_module_type": selected_module,
        "lookback_days": days,
        "module_options": module_options,
        "summary": {
            "request_total": total,
            "success_total": total - failed,
            "failed_or_warning_total": failed,
            "masked_rate": _ratio(masked, total),
            "unmasked_total": unmasked,
            "avg_latency_ms": avg_latency,
            "open_recommendations": open_rec_total,
            "critical_recommendations": critical_rec_total,
            "negative_feedback": negative_feedback_total,
            "report_card_count": len(report_cards),
        },
        "charts": {
            "module_distribution": _bar_rows(module_counter, limit=10),
            "status_distribution": _bar_rows(status_counter, labels={key: _label_status(key) for key in status_counter}, limit=8),
            "feature_distribution": _bar_rows(feature_counter, labels={key: key.replace("_", " ").title() for key in feature_counter}, limit=8),
            "latency_distribution": _bar_rows(latency_counter, labels={key: key for key in latency_counter}, limit=4),
            "daily_trend": _daily_trend_rows(request_rows, min(days, 45)),
        },
        "report_cards": report_cards,
        "risk_cards": risk_cards,
        "executive_notes": _executive_notes(metrics, risk_cards),
        "safety_notes": [
            "Bu ekran AI log, öneri, geri bildirim ve özet cache kayıtlarını yalnızca okur.",
            "Grafikler gerçek içe aktarım yapmaz; Excel/CSV verisini veritabanına yazmaz.",
            "KVKK açısından maskesiz kayıtlar ayrı risk kartı olarak görünür.",
            "Rapor kartları yönetsel karar desteğidir; nihai idari karar yerine geçmez.",
        ],
        "generated_at": utc_now(),
        "read_only_contract": {
            "GERCEK_ICE_AKTARIM_YOK": GERCEK_ICE_AKTARIM_YOK,
            "DB_WRITE_ENABLED": DB_WRITE_ENABLED,
            "VISUAL_REPORT_READ_ONLY": VISUAL_REPORT_READ_ONLY,
        },
    }


def export_visual_report_rows(snapshot: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for card in snapshot.get("report_cards") or []:
        rows.append(
            [
                card.get("module_type"),
                card.get("label"),
                card.get("request_total"),
                card.get("success_rate"),
                card.get("masked_rate"),
                card.get("open_recommendations"),
                card.get("critical_recommendations"),
                card.get("negative_feedback"),
                card.get("avg_latency_ms"),
                card.get("signal_score"),
                card.get("tone"),
                card.get("note"),
            ]
        )
    return rows
