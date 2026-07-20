"""Anket liste/sonuç ekranları için küçük metrik yardımcıları."""
from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Iterable
from typing import Any

from .contracts import SurveyMetricSummary

logger = logging.getLogger(__name__)


def empty_survey_counts() -> dict[str, int]:
    """Kullanıcı anket listesi için canlı route sayaç sözleşmesi."""
    return {"all": 0, "active": 0, "completed": 0, "upcoming": 0, "expired": 0}


def completion_percent(completed: int, assigned: int) -> int:
    try:
        completed_i = int(completed or 0)
        assigned_i = int(assigned or 0)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/metrics.py | line=21")
        return 0
    if assigned_i <= 0:
        return 0
    return int(round((completed_i / assigned_i) * 100))


def status_counts(rows: Iterable[Any]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    total = 0
    for row in rows or []:
        status = str(getattr(row, "status", "") or "draft").strip() or "draft"
        counter[status] += 1
        total += 1
    summary = SurveyMetricSummary(
        total_surveys=total,
        draft=counter.get("draft", 0),
        published=counter.get("published", 0),
        closed=counter.get("closed", 0),
        archived=counter.get("archived", 0),
    )
    return summary.as_dict()


def answer_value_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()
