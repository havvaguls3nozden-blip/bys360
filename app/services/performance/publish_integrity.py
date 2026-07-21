from __future__ import annotations

from typing import Any

from app.models import PerformanceEvaluation, PerformanceEvaluationItem
from app.services.performance.common import get_period_level_3_flags
from app.services.performance.policy_flags import (
    is_level_2_comment_required_when_level_1_score_is_three,
)


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _level_label(level: int) -> str:
    return {1: "1. amir", 2: "2. amir", 3: "3. amir"}.get(int(level or 0), f"{level}. amir")


def _requires_general_comment(level_total_100: float, raw_scores: list[float]) -> bool:
    if float(level_total_100 or 0) < 70 or float(level_total_100 or 0) > 90:
        return True
    return any(float(score) in {1.0, 5.0} for score in raw_scores or [])


def _level_items(evaluation_id: int, manager_level: int) -> list[PerformanceEvaluationItem]:
    rows = (
        PerformanceEvaluationItem.query
        .filter_by(evaluation_id=evaluation_id, manager_level=manager_level)
        .order_by(PerformanceEvaluationItem.criteria_id.asc(), PerformanceEvaluationItem.id.desc())
        .all()
    )
    latest_by_criteria: dict[int, PerformanceEvaluationItem] = {}
    for row in rows:
        criteria_id = int(getattr(row, "criteria_id", 0) or 0)
        if criteria_id and criteria_id not in latest_by_criteria:
            latest_by_criteria[criteria_id] = row
    return [latest_by_criteria[key] for key in sorted(latest_by_criteria)]


def _level_1_has_any_three(evaluation: PerformanceEvaluation) -> bool:
    return any(
        (_safe_float(getattr(item, "score", None)) == 3.0)
        for item in _level_items(evaluation.id, 1)
    )


def find_level_integrity_issues(
    evaluation: PerformanceEvaluation | None,
    manager_level: int,
    period: Any | None = None,
) -> list[str]:
    if not evaluation:
        return ["Değerlendirme kaydı bulunamadı."]

    period = period or getattr(evaluation, "period", None)
    level_3_flags = get_period_level_3_flags(period)
    level = int(manager_level or 0)
    issues: list[str] = []

    if not bool(getattr(evaluation, f"level_{level}_completed", False)):
        return issues

    level_label = _level_label(level)
    general_comment = _safe_str(getattr(evaluation, f"level_{level}_general_comment", None))

    if level == 3 and level_3_flags.get("enabled") and not level_3_flags.get("scoring_enabled"):
        if not general_comment:
            issues.append("3. amir üst görüşü zorunlu fakat boş.")
        return issues

    items = _level_items(evaluation.id, level)
    if not items:
        issues.append(f"{level_label} kriter puanları eksik.")
        return issues

    raw_scores: list[float] = []
    missing_score = False

    for item in items:
        raw_score = _safe_float(getattr(item, "score", None))
        comment = _safe_str(getattr(item, "comment", None))
        criteria_name = _safe_str(getattr(getattr(item, "criteria", None), "name", None)) or "Bu kriter"

        if raw_score is None:
            missing_score = True
            continue

        raw_scores.append(raw_score)
        if raw_score in {1.0, 5.0} and not comment:
            issues.append(f"{level_label} · {criteria_name} için açıklama zorunludur.")

    if missing_score:
        issues.append(f"{level_label} tüm kriterleri puanlamadan tamamlanmış görünüyor.")

    level_total = float(getattr(evaluation, f"level_{level}_total_100", 0) or 0)
    if _requires_general_comment(level_total, raw_scores) and not general_comment:
        issues.append(f"{level_label} genel görüşü zorunlu fakat boş.")

    if (
        level == 2
        and is_level_2_comment_required_when_level_1_score_is_three()
        and _level_1_has_any_three(evaluation)
        and not general_comment
    ):
        issues.append("2. amir genel görüşü zorunlu; 1. amirde 3 puan bulunan kriter var.")

    deduped: list[str] = []
    seen: set[str] = set()
    for issue in issues:
        key = _safe_str(issue)
        if not key or key in seen:
            continue
        deduped.append(key)
        seen.add(key)
    return deduped


def find_evaluation_integrity_issues(evaluation: PerformanceEvaluation | None, period: Any | None = None) -> list[str]:
    if not evaluation:
        return ["Değerlendirme kaydı bulunamadı."]

    period = period or getattr(evaluation, "period", None)
    get_period_level_3_flags(period)
    issues: list[str] = []

    for level in (1, 2, 3):
        issues.extend(find_level_integrity_issues(evaluation, manager_level=level, period=period))

    deduped: list[str] = []
    seen: set[str] = set()
    for issue in issues:
        key = _safe_str(issue)
        if not key or key in seen:
            continue
        deduped.append(key)
        seen.add(key)
    return deduped


def first_evaluation_integrity_issue(evaluation: PerformanceEvaluation | None, period: Any | None = None) -> str:
    issues = find_evaluation_integrity_issues(evaluation, period=period)
    return issues[0] if issues else ""


__all__ = [
    "find_evaluation_integrity_issues",
    "find_level_integrity_issues",
    "first_evaluation_integrity_issue",
]


# BYS360_A5_P2D3_PUBLISH_PREFLIGHT_LOCK_ANCHOR_START
# Static contract anchor: 2026-04-18-publish-preflight-lock-v1
PUBLISH_PREFLIGHT_LOCK_CONTRACT_ID = "2026-04-18-publish-preflight-lock-v1"
# BYS360_A5_P2D3_PUBLISH_PREFLIGHT_LOCK_ANCHOR_END

