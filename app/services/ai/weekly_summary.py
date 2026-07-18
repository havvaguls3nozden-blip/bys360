from __future__ import annotations

from app.core.datetime_utils import utc_now
from typing import Any

from app.services.ai.governance import build_ai_governance_snapshot
from app.services.ai.governance_settings import get_governance_thresholds, get_weekly_summary_settings
from app.services.ai.quality import build_ai_quality_snapshot
from app.services.ai.localization import ai_module_label


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = 365) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


def build_ai_weekly_summary(*, lookback_days: int | None = None) -> dict[str, Any]:
    thresholds = get_governance_thresholds()
    summary_settings = get_weekly_summary_settings()
    lookback = _safe_int(lookback_days, int(summary_settings.get("lookback_days") or 7), 1, 60)
    top_limit = _safe_int(summary_settings.get("top_limit"), 5, 1, 20)

    quality_snapshot = build_ai_quality_snapshot(lookback_days=lookback)
    governance_snapshot = build_ai_governance_snapshot(
        lookback_days=lookback,
        module_quality_floor=thresholds["module_quality_floor"],
        prompt_quality_floor=thresholds["prompt_quality_floor"],
        backlog_limit=thresholds["backlog_limit"],
        negative_feedback_limit=thresholds["negative_feedback_limit"],
    )

    summary = quality_snapshot.get("summary") or {}
    module_rows = list(quality_snapshot.get("module_rows") or [])[:top_limit]
    prompt_rows = list(quality_snapshot.get("prompt_rows") or [])[:top_limit]
    actions = list(governance_snapshot.get("actions") or [])[:top_limit]
    alerts = list(governance_snapshot.get("all_alerts") or [])[:top_limit]
    incidents = list(governance_snapshot.get("incidents") or [])[:top_limit]

    highlights: list[dict[str, str]] = []
    highlights.append({
        "title": "Karar destek kalite skoru",
        "body": f"Son {lookback} günde genel kalite skoru %{summary.get('quality_score') or 0}. Açık öneri {summary.get('open_recommendations') or 0}, negatif geri bildirim {summary.get('negative_feedback') or 0}.",
    })
    if module_rows:
        best_module = sorted(module_rows, key=lambda row: (-int(row.get("quality_score") or 0), row.get("module_type") or ""))[0]
        highlights.append({
            "title": f"Öne çıkan modül: {ai_module_label(best_module.get('module_type') or 'genel')}",
            "body": f"Kalite skoru %{best_module.get('quality_score') or 0}. Başarı oranı %{best_module.get('success_rate') or 0}, açık iş yükü {best_module.get('backlog_total') or 0}.",
        })
    if alerts:
        first_alert = alerts[0]
        highlights.append({
            "title": f"Öncelikli risk: {first_alert.get('title') or 'Karar destek kalite sapması'}",
            "body": str(first_alert.get('body') or '')[:220],
        })
    if not alerts:
        highlights.append({
            "title": "Kritik risk görünmüyor",
            "body": "Bu pencerede kalite eşiğini aşan belirgin alarm oluşmadı. Yine de modül ve istem bazlı eğilimleri haftalık olarak izlemeye devam edin.",
        })

    return {
        "page_title": "Karar Destek Haftalık Yönetici Özeti",
        "page_kicker": "Yönetici özeti",
        "page_subtitle": "Kalite, istem, modül ve aksiyon görünümünü tek sayfada özetler",
        "generated_at": utc_now(),
        "lookback_days": lookback,
        "thresholds": thresholds,
        "summary": summary,
        "module_rows": module_rows,
        "prompt_rows": prompt_rows,
        "actions": actions,
        "alerts": alerts,
        "incidents": incidents,
        "highlights": highlights,
        "weekly_settings": summary_settings,
    }