from __future__ import annotations

# Faz 2 V5: publish.policy uygulama açılışında visibility_guard import etmez.
# Bu değerler visibility_guard ile aynı tutulur; fonksiyonlar ihtiyaç anında lazy proxy ile çağrılır.


PUBLISHABLE_FINAL_STATUSES = {"tamamlandi", "tamamlandı", "completed", "published"}
PRIVILEGED_SCORECARD_ROLES = {
    "admin",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "koordinator",
    "birim_sorumlusu",
}


def _phase2_visibility_guard():
    from app.services.performance import visibility_guard as _guard
    return _guard


def _build_visibility_lock_hint(*args, **kwargs):
    return _phase2_visibility_guard().build_visibility_lock_hint(*args, **kwargs)


def can_employee_view_evaluation(*args, **kwargs):
    return _phase2_visibility_guard().can_employee_view_evaluation(*args, **kwargs)


def get_evaluation_visibility_state(*args, **kwargs):
    return _phase2_visibility_guard().get_evaluation_visibility_state(*args, **kwargs)


def is_evaluation_publish_exempt(*args, **kwargs):
    return _phase2_visibility_guard().is_evaluation_publish_exempt(*args, **kwargs)


def is_evaluation_publishable(*args, **kwargs):
    return _phase2_visibility_guard().is_evaluation_publishable(*args, **kwargs)


from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from typing import Any, Optional

from app.extensions import db
from app.models import PerformanceEvaluation, PerformancePeriod


def get_publish_timestamp(evaluation: PerformanceEvaluation | None) -> datetime | None:
    if not evaluation:
        return None
    return getattr(evaluation, "published_to_employee_at", None) or getattr(evaluation, "published_at", None)


def summarize_skip_reasons(rows: Iterable[dict[str, Any]] | None) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for row in rows or []:
        reason = str((row or {}).get("reason") or "Belirtilmeyen neden").strip() or "Belirtilmeyen neden"
        counter[reason] += 1
    return sorted(counter.items(), key=lambda item: (-item[1], item[0].lower()))


def get_period(period_id: int | None = None) -> PerformancePeriod | None:
    try:
        if period_id:
            return db.session.get(PerformancePeriod, int(period_id))
    except (TypeError, ValueError):
        return None
    return (
        PerformancePeriod.query
        .filter_by(is_active=True)
        .order_by(PerformancePeriod.id.desc())
        .first()
    )
