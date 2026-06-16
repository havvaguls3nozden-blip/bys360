from __future__ import annotations

from app.core.datetime_utils import utc_now
from datetime import datetime, timedelta
from math import ceil
from typing import Any

from flask import url_for

from app.models import AIFeedbackLog, AIRecommendation, AIRequestLog
from app.services.ai.localization import ai_feature_label, ai_module_label, ai_status_label, ai_target_label
from app.services.ai.quality import build_ai_quality_snapshot

NEGATIVE_FEEDBACK_TYPES = {"not_helpful", "wrong", "unsafe"}


def _safe_int(value: Any, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    if minimum is not None:
        parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def _severity_rank(value: str) -> int:
    text = str(value or "").strip().lower()
    if text == "critical":
        return 3
    if text == "warning":
        return 2
    return 1

def _determine_module_alert(row: dict[str, Any], *, module_quality_floor: int, backlog_limit: int, negative_feedback_limit: int) -> dict[str, Any] | None:
    reasons: list[str] = []
    quality_score = int(row.get("quality_score") or 0)
    backlog_total = int(row.get("backlog_total") or 0)
    negative_feedback = int(row.get("negative_feedback") or 0)
    failed_total = int(row.get("failed_total") or 0)
    request_total = int(row.get("request_total") or 0)

    if quality_score < module_quality_floor:
        reasons.append(f"Kalite skoru eşik altında ({quality_score} < {module_quality_floor}).")
    if backlog_total >= backlog_limit:
        reasons.append(f"Açık backlog yüksek ({backlog_total} ≥ {backlog_limit}).")
    if negative_feedback >= negative_feedback_limit:
        reasons.append(f"Negatif geri bildirim yükseldi ({negative_feedback} ≥ {negative_feedback_limit}).")
    failure_limit = max(2, ceil(request_total * 0.15)) if request_total else 2
    if failed_total >= failure_limit:
        reasons.append(f"Hatalı / warning istek yükü arttı ({failed_total} ≥ {failure_limit}).")

    if not reasons:
        return None

    severity = "warning"
    if quality_score < max(module_quality_floor - 15, 35) or backlog_total >= backlog_limit * 2 or failed_total >= max(failure_limit + 2, 5):
        severity = "critical"

    return {
        "kind": "module",
        "severity": severity,
        "module_type": row.get("module_type") or "genel",
        "prompt_version": "",
        "title": f"{ai_module_label(row.get('module_type') or 'genel')} modülünde AI kalite sapması var",
        "body": " ".join(reasons),
        "quality_score": quality_score,
        "backlog_total": backlog_total,
        "negative_feedback": negative_feedback,
        "failed_total": failed_total,
        "request_total": request_total,
        "href": url_for("main.admin_ai_quality_hub", module_type=row.get("module_type") or "", lookback_days=row.get("selected_lookback_days") or 30),
        "queue_href": url_for("main.admin_ai_review_queue", module_type=row.get("module_type") or "", status="open"),
    }

def _determine_prompt_alert(row: dict[str, Any], *, prompt_quality_floor: int, backlog_limit: int, negative_feedback_limit: int) -> dict[str, Any] | None:
    reasons: list[str] = []
    quality_score = int(row.get("quality_score") or 0)
    success_rate = int(row.get("success_rate") or 0)
    open_recommendations = int(row.get("open_recommendations") or 0)
    negative_feedback = int(row.get("negative_feedback") or 0)
    request_total = int(row.get("request_total") or 0)

    if quality_score < prompt_quality_floor:
        reasons.append(f"İstem kalite skoru eşik altında ({quality_score} < {prompt_quality_floor}).")
    if success_rate < 80 and request_total >= 3:
        reasons.append(f"Başarı oranı zayıf (%{success_rate}).")
    if open_recommendations >= backlog_limit:
        reasons.append(f"Bu istem ile üretilen açık öneriler yüksek ({open_recommendations} ≥ {backlog_limit}).")
    if negative_feedback >= negative_feedback_limit:
        reasons.append(f"Negatif geri bildirim arttı ({negative_feedback} ≥ {negative_feedback_limit}).")

    if not reasons:
        return None

    severity = "warning"
    if quality_score < max(prompt_quality_floor - 15, 30) or negative_feedback >= negative_feedback_limit + 2 or success_rate < 60:
        severity = "critical"

    prompt_version = str(row.get("prompt_version") or "tanimsiz")
    return {
        "kind": "prompt",
        "severity": severity,
        "module_type": "",
        "prompt_version": prompt_version,
        "title": f"{prompt_version} istem sürümü gözden geçirilmeli",
        "body": " ".join(reasons),
        "quality_score": quality_score,
        "backlog_total": open_recommendations,
        "negative_feedback": negative_feedback,
        "failed_total": 0,
        "request_total": request_total,
        "href": url_for("main.admin_ai_quality_hub", prompt_version=prompt_version, lookback_days=row.get("selected_lookback_days") or 30),
        "queue_href": url_for("main.admin_ai_review_queue", status="open"),
    }

def _recent_incidents(*, lookback_days: int, limit: int = 10) -> list[dict[str, Any]]:
    since = utc_now() - timedelta(days=max(int(lookback_days or 1), 1))
    incidents: list[dict[str, Any]] = []

    failed_rows = (
        AIRequestLog.query.filter(AIRequestLog.created_at >= since)
        .filter(AIRequestLog.status.in_(["failed", "warning"]))
        .order_by(AIRequestLog.created_at.desc(), AIRequestLog.id.desc())
        .limit(limit)
        .all()
    )
    for row in failed_rows:
        incidents.append(
            {
                "created_at": row.created_at,
                "severity": "critical" if str(row.status).lower() == "failed" else "warning",
                "title": f"{ai_module_label(row.module_type or 'genel')} · {ai_feature_label(row.feature_type or 'ai')} çağrısı {ai_status_label(row.status)}",
                "body": (row.error_message or row.response_text or "AI çağrısı beklenen kaliteye ulaşmadı.")[:220],
                "href": url_for("main.admin_ai_operations_report", module_type=row.module_type or ""),
                "kind": "request",
            }
        )

    feedback_rows = (
        AIFeedbackLog.query.filter(AIFeedbackLog.created_at >= since)
        .filter(AIFeedbackLog.feedback_type.in_(list(NEGATIVE_FEEDBACK_TYPES)))
        .order_by(AIFeedbackLog.created_at.desc(), AIFeedbackLog.id.desc())
        .limit(limit)
        .all()
    )
    for row in feedback_rows:
        request_log = getattr(row, "ai_request_log", None)
        incidents.append(
            {
                "created_at": row.created_at,
                "severity": "warning",
                "title": f"Negatif geri bildirim · {ai_module_label(getattr(request_log, 'module_type', None) or 'genel')}",
                "body": (row.feedback_note or row.feedback_type or "Olumsuz kullanıcı geri bildirimi kaydedildi.")[:220],
                "href": url_for("main.admin_ai_feedback", module_type=getattr(request_log, "module_type", "") or "", feedback_type=row.feedback_type or ""),
                "kind": "feedback",
            }
        )

    recommendation_rows = (
        AIRecommendation.query.filter(AIRecommendation.created_at >= since)
        .filter(AIRecommendation.status == "open")
        .order_by(AIRecommendation.created_at.desc(), AIRecommendation.id.desc())
        .limit(limit)
        .all()
    )
    for row in recommendation_rows:
        incidents.append(
            {
                "created_at": row.created_at,
                "severity": "info",
                "title": f"Açık öneri · {ai_module_label(row.module_type or 'genel')} / {ai_target_label(row.target_table)}",
                "body": (row.title or row.body or "AI önerisi yönetici kararı bekliyor.")[:220],
                "href": url_for("main.admin_ai_review_queue", module_type=row.module_type or "", target_table=row.target_table or "", status="open"),
                "kind": "recommendation",
            }
        )

    incidents.sort(key=lambda item: ((item.get("created_at") or datetime.min), _severity_rank(item.get("severity"))), reverse=True)
    return incidents[:limit]

def _build_actions(*, summary: dict[str, Any], module_alerts: list[dict[str, Any]], prompt_alerts: list[dict[str, Any]], backlog_limit: int, negative_feedback_limit: int) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    critical_modules = [row for row in module_alerts if row.get("severity") == "critical"]
    critical_prompts = [row for row in prompt_alerts if row.get("severity") == "critical"]

    if critical_modules:
        worst = sorted(critical_modules, key=lambda item: (int(item.get("quality_score") or 0), -int(item.get("backlog_total") or 0)))[0]
        actions.append(
            {
                "severity": "critical",
                "title": f"{ai_module_label(worst.get('module_type') or 'genel')} modülünde acil AI iyileştirmesi yapın",
                "body": "Kalite eşiği belirgin biçimde düştü. Önce operasyon raporunu açın, ardından açık öneri kuyruğunu temizleyin ve istem çıktısını gözden geçirin.",
                "href": worst.get("href"),
                "label": "Modül detayını aç",
            }
        )

    if critical_prompts:
        worst = sorted(critical_prompts, key=lambda item: (int(item.get("quality_score") or 0), -int(item.get("negative_feedback") or 0)))[0]
        actions.append(
            {
                "severity": "warning",
                "title": f"{worst.get('prompt_version') or 'tanimsiz'} istem sürümünü revize edin",
                "body": "Bu istem sürümü zayıf çıktı üretiyor veya fazla olumsuz geri bildirim topluyor. Kalite panosunda sürüm kıyasını açıp önceki sürümlerle karşılaştırın.",
                "href": worst.get("href"),
                "label": "İstem kıyasını aç",
            }
        )

    open_recommendations = int(summary.get("open_recommendations") or 0)
    if open_recommendations >= backlog_limit:
        actions.append(
            {
                "severity": "warning",
                "title": "Açık AI öneri kuyruğunu küçültün",
                "body": f"Karar bekleyen öneri sayısı {open_recommendations}. Özellikle desteklenen kayıtları toplu uygula veya kabul / ret kararıyla kapat.",
                "href": url_for("main.admin_ai_review_queue", status="open"),
                "label": "İnceleme kuyruğunu aç",
            }
        )

    negative_feedback = int(summary.get("negative_feedback") or 0)
    if negative_feedback >= negative_feedback_limit:
        actions.append(
            {
                "severity": "warning",
                "title": "Negatif kullanıcı geri bildirimlerini inceleyin",
                "body": f"Son pencerede {negative_feedback} olumsuz geri bildirim var. Hatalı özet, yetersiz öneri veya gecikme kaynaklarını ayırmak için geri bildirim günlüğünü açın.",
                "href": url_for("main.admin_ai_feedback"),
                "label": "Geri bildirimleri aç",
            }
        )

    failed_total = int(summary.get("failed_total") or 0)
    if failed_total > 0:
        actions.append(
            {
                "severity": "warning",
                "title": "Başarısız / uyarı düzeyindeki AI çağrılarını azaltın",
                "body": f"Son pencerede {failed_total} sorunlu AI çağrısı var. Sağlayıcı, istem ve hedef ekran ilişkisini operasyon raporunda kontrol edin.",
                "href": url_for("main.admin_ai_operations_report"),
                "label": "Operasyon raporunu aç",
            }
        )

    if not actions:
        actions.append(
            {
                "severity": "success",
                "title": "AI yönetişim görünümü dengeli",
                "body": "Seçili zaman penceresinde kritik eşik aşımı görünmüyor. Yine de kalite panosu ve öneri kuyruğunu periyodik takip edin.",
                "href": url_for("main.admin_ai_quality_hub"),
                "label": "Kalite panosunu aç",
            }
        )

    return actions[:6]

def build_ai_governance_snapshot(*, module_type: str = "", prompt_version: str = "", lookback_days: int = 30, module_quality_floor: int = 65, prompt_quality_floor: int = 60, backlog_limit: int = 8, negative_feedback_limit: int = 3) -> dict[str, Any]:
    lookback_days = _safe_int(lookback_days, 30, minimum=1, maximum=180)
    module_quality_floor = _safe_int(module_quality_floor, 65, minimum=20, maximum=95)
    prompt_quality_floor = _safe_int(prompt_quality_floor, 60, minimum=20, maximum=95)
    backlog_limit = _safe_int(backlog_limit, 8, minimum=1, maximum=200)
    negative_feedback_limit = _safe_int(negative_feedback_limit, 3, minimum=1, maximum=50)

    snapshot = build_ai_quality_snapshot(
        module_type=module_type,
        prompt_version=prompt_version,
        lookback_days=lookback_days,
    )
    module_rows = [dict(row, selected_lookback_days=lookback_days) for row in (snapshot.get("module_rows") or [])]
    prompt_rows = [dict(row, selected_lookback_days=lookback_days) for row in (snapshot.get("prompt_rows") or [])]

    module_alerts = [
        alert
        for row in module_rows
        for alert in [_determine_module_alert(
            row,
            module_quality_floor=module_quality_floor,
            backlog_limit=backlog_limit,
            negative_feedback_limit=negative_feedback_limit,
        )]
        if alert
    ]
    prompt_alerts = [
        alert
        for row in prompt_rows
        for alert in [_determine_prompt_alert(
            row,
            prompt_quality_floor=prompt_quality_floor,
            backlog_limit=backlog_limit,
            negative_feedback_limit=negative_feedback_limit,
        )]
        if alert
    ]

    all_alerts = sorted(module_alerts + prompt_alerts, key=lambda item: (_severity_rank(item.get("severity")), -(int(item.get("request_total") or 0))), reverse=True)
    critical_alerts = [row for row in all_alerts if row.get("severity") == "critical"]
    warning_alerts = [row for row in all_alerts if row.get("severity") == "warning"]

    summary = dict(snapshot.get("summary") or {})
    governance_score = max(0, min(100, int(summary.get("quality_score") or 0) - len(critical_alerts) * 8 - len(warning_alerts) * 3))
    summary.update(
        {
            "governance_score": governance_score,
            "critical_alert_total": len(critical_alerts),
            "warning_alert_total": len(warning_alerts),
            "module_alert_total": len(module_alerts),
            "prompt_alert_total": len(prompt_alerts),
            "lookback_days": lookback_days,
            "module_quality_floor": module_quality_floor,
            "prompt_quality_floor": prompt_quality_floor,
            "backlog_limit": backlog_limit,
            "negative_feedback_limit": negative_feedback_limit,
            "failed_total": sum(int(row.get("failed_total") or 0) for row in module_rows),
        }
    )

    actions = _build_actions(
        summary=summary,
        module_alerts=module_alerts,
        prompt_alerts=prompt_alerts,
        backlog_limit=backlog_limit,
        negative_feedback_limit=negative_feedback_limit,
    )
    incidents = _recent_incidents(lookback_days=lookback_days, limit=12)

    return {
        **snapshot,
        "summary": summary,
        "module_alerts": module_alerts,
        "prompt_alerts": prompt_alerts,
        "all_alerts": all_alerts,
        "actions": actions,
        "recent_incidents": incidents,
        "selected_module_type": str(module_type or "").strip().lower(),
        "selected_prompt_version": str(prompt_version or "").strip(),
        "selected_lookback_days": lookback_days,
        "selected_module_quality_floor": module_quality_floor,
        "selected_prompt_quality_floor": prompt_quality_floor,
        "selected_backlog_limit": backlog_limit,
        "selected_negative_feedback_limit": negative_feedback_limit,
    }