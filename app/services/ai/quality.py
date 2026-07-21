from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Any

from sqlalchemy import func

from app.core.datetime_utils import utc_now
from app.models import AIFeedbackLog, AIRecommendation, AIRequestLog
from app.services.ai.module_scope import (
    filter_visible_values,
    is_visible_ai_module,
    scope_visible_modules,
)

NEGATIVE_FEEDBACK_TYPES = {"not_helpful", "wrong", "unsafe"}
POSITIVE_FEEDBACK_TYPES = {"helpful", "useful", "accurate", "accepted"}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _safe_ratio(part: int, whole: int) -> int:
    if not whole:
        return 0
    return int(round((part / whole) * 100))


def _safe_avg(total: int, whole: int) -> int:
    if not whole:
        return 0
    return int(round(total / whole))


def _normalize_prompt_version(value: Any) -> str:
    text = str(value or "").strip()
    return text or "tanimsiz"


def _normalize_module_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text or "genel"


def _quality_score(*, success_rate: int, masked_rate: int, acceptance_rate: int, helpful_rate: int, backlog_penalty: int) -> int:
    score = round(
        success_rate * 0.30
        + masked_rate * 0.20
        + acceptance_rate * 0.25
        + helpful_rate * 0.25
        - backlog_penalty
    )
    return max(0, min(int(score), 100))


def _tone_from_score(score: int, *, negative_feedback: int = 0, failed_total: int = 0) -> str:
    if failed_total > 0 or negative_feedback >= 3 or score < 45:
        return "warning"
    if score < 75:
        return "calm"
    return "success"


def _ai_request_base_query(*, module_type: str = "", prompt_version: str = "", lookback_days: int = 30):
    query = scope_visible_modules(AIRequestLog.query, AIRequestLog.module_type)
    since = None
    if lookback_days:
        since = utc_now() - timedelta(days=max(int(lookback_days), 1))
        query = query.filter(AIRequestLog.created_at >= since)
    selected_module_type = str(module_type or "").strip().lower()
    selected_prompt_version = str(prompt_version or "").strip().lower()
    if selected_module_type:
        if not is_visible_ai_module(selected_module_type):
            query = query.filter(False)
        else:
            query = query.filter(func.lower(AIRequestLog.module_type) == selected_module_type)
    if selected_prompt_version:
        query = query.filter(func.lower(func.coalesce(AIRequestLog.prompt_version, "tanimsiz")) == selected_prompt_version)
    return query, since


def build_ai_quality_snapshot(*, module_type: str = "", prompt_version: str = "", lookback_days: int = 30) -> dict[str, Any]:
    query, since = _ai_request_base_query(module_type=module_type, prompt_version=prompt_version, lookback_days=lookback_days)
    request_rows = query.order_by(AIRequestLog.created_at.desc()).all()
    request_ids = [row.id for row in request_rows]

    feedback_rows = []
    recommendation_rows = []
    if request_ids:
        feedback_rows = AIFeedbackLog.query.filter(AIFeedbackLog.ai_request_log_id.in_(request_ids)).all()
        recommendation_rows = AIRecommendation.query.filter(AIRecommendation.ai_request_log_id.in_(request_ids)).all()

    total_requests = len(request_rows)
    completed_total = sum(1 for row in request_rows if str(getattr(row, "status", "")).lower() == "completed")
    failed_total = sum(1 for row in request_rows if str(getattr(row, "status", "")).lower() in {"failed", "warning"})
    visible_total = sum(1 for row in request_rows if bool(getattr(row, "was_user_visible", False)))
    masked_total = sum(1 for row in request_rows if bool(getattr(row, "was_masked", False)))
    latency_values = [int(getattr(row, "latency_ms", 0) or 0) for row in request_rows if getattr(row, "latency_ms", None) is not None]

    feedback_total = len(feedback_rows)
    negative_feedback = sum(1 for row in feedback_rows if str(getattr(row, "feedback_type", "")).lower() in NEGATIVE_FEEDBACK_TYPES)
    positive_feedback = sum(1 for row in feedback_rows if str(getattr(row, "feedback_type", "")).lower() in POSITIVE_FEEDBACK_TYPES)

    recommendation_total = len(recommendation_rows)
    accepted_recommendations = sum(1 for row in recommendation_rows if str(getattr(row, "status", "")).lower() == "accepted")
    open_recommendations = sum(1 for row in recommendation_rows if str(getattr(row, "status", "")).lower() == "open")

    success_rate = _safe_ratio(completed_total, total_requests)
    visibility_rate = _safe_ratio(visible_total, total_requests)
    masked_rate = _safe_ratio(masked_total, total_requests)
    helpful_rate = _safe_ratio(positive_feedback, feedback_total)
    acceptance_rate = _safe_ratio(accepted_recommendations, recommendation_total)
    avg_latency_ms = _safe_avg(sum(latency_values), len(latency_values)) if latency_values else 0
    backlog_penalty = min(open_recommendations * 2 + negative_feedback * 4 + failed_total * 5, 30)
    quality_score = _quality_score(
        success_rate=success_rate,
        masked_rate=masked_rate,
        acceptance_rate=acceptance_rate,
        helpful_rate=helpful_rate,
        backlog_penalty=backlog_penalty,
    )

    prompt_map: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "prompt_version": "tanimsiz",
        "request_total": 0,
        "completed_total": 0,
        "failed_total": 0,
        "visible_total": 0,
        "masked_total": 0,
        "latency_sum": 0,
        "latency_count": 0,
        "recommendation_total": 0,
        "accepted_recommendations": 0,
        "open_recommendations": 0,
        "feedback_total": 0,
        "positive_feedback": 0,
        "negative_feedback": 0,
    })
    request_prompt_lookup: dict[int, str] = {}
    for row in request_rows:
        key = _normalize_prompt_version(getattr(row, "prompt_version", None))
        payload = prompt_map[key]
        payload["prompt_version"] = key
        payload["request_total"] += 1
        request_prompt_lookup[row.id] = key
        status = str(getattr(row, "status", "")).lower()
        if status == "completed":
            payload["completed_total"] += 1
        if status in {"failed", "warning"}:
            payload["failed_total"] += 1
        if bool(getattr(row, "was_user_visible", False)):
            payload["visible_total"] += 1
        if bool(getattr(row, "was_masked", False)):
            payload["masked_total"] += 1
        latency_ms = getattr(row, "latency_ms", None)
        if latency_ms is not None:
            payload["latency_sum"] += int(latency_ms or 0)
            payload["latency_count"] += 1

    for row in recommendation_rows:
        key = request_prompt_lookup.get(getattr(row, "ai_request_log_id", None))
        if not key:
            continue
        payload = prompt_map[key]
        payload["recommendation_total"] += 1
        status = str(getattr(row, "status", "")).lower()
        if status == "accepted":
            payload["accepted_recommendations"] += 1
        if status == "open":
            payload["open_recommendations"] += 1

    for row in feedback_rows:
        key = request_prompt_lookup.get(getattr(row, "ai_request_log_id", None))
        if not key:
            continue
        payload = prompt_map[key]
        payload["feedback_total"] += 1
        feedback_type = str(getattr(row, "feedback_type", "")).lower()
        if feedback_type in NEGATIVE_FEEDBACK_TYPES:
            payload["negative_feedback"] += 1
        if feedback_type in POSITIVE_FEEDBACK_TYPES:
            payload["positive_feedback"] += 1

    prompt_rows: list[dict[str, Any]] = []
    for key, payload in prompt_map.items():
        request_total = int(payload["request_total"] or 0)
        recommendation_total = int(payload["recommendation_total"] or 0)
        feedback_total = int(payload["feedback_total"] or 0)
        success_rate_row = _safe_ratio(int(payload["completed_total"] or 0), request_total)
        masked_rate_row = _safe_ratio(int(payload["masked_total"] or 0), request_total)
        helpful_rate_row = _safe_ratio(int(payload["positive_feedback"] or 0), feedback_total)
        acceptance_rate_row = _safe_ratio(int(payload["accepted_recommendations"] or 0), recommendation_total)
        quality_score_row = _quality_score(
            success_rate=success_rate_row,
            masked_rate=masked_rate_row,
            acceptance_rate=acceptance_rate_row,
            helpful_rate=helpful_rate_row,
            backlog_penalty=min(int(payload["open_recommendations"] or 0) * 2 + int(payload["negative_feedback"] or 0) * 4 + int(payload["failed_total"] or 0) * 5, 30),
        )
        prompt_rows.append(
            {
                "prompt_version": key,
                "request_total": request_total,
                "success_rate": success_rate_row,
                "masked_rate": masked_rate_row,
                "acceptance_rate": acceptance_rate_row,
                "helpful_rate": helpful_rate_row,
                "avg_latency_ms": _safe_avg(int(payload["latency_sum"] or 0), int(payload["latency_count"] or 0)),
                "open_recommendations": int(payload["open_recommendations"] or 0),
                "negative_feedback": int(payload["negative_feedback"] or 0),
                "quality_score": quality_score_row,
                "tone": _tone_from_score(quality_score_row, negative_feedback=int(payload["negative_feedback"] or 0), failed_total=int(payload["failed_total"] or 0)),
            }
        )
    prompt_rows.sort(key=lambda item: (-int(item["quality_score"]), -int(item["request_total"]), item["prompt_version"]))

    module_map: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "module_type": "genel",
        "request_total": 0,
        "completed_total": 0,
        "failed_total": 0,
        "masked_total": 0,
        "visible_total": 0,
        "latency_sum": 0,
        "latency_count": 0,
        "recommendation_total": 0,
        "accepted_recommendations": 0,
        "open_recommendations": 0,
        "feedback_total": 0,
        "positive_feedback": 0,
        "negative_feedback": 0,
        "prompt_versions": set(),
    })
    request_module_lookup: dict[int, str] = {}
    for row in request_rows:
        key = _normalize_module_type(getattr(row, "module_type", None))
        payload = module_map[key]
        payload["module_type"] = key
        payload["request_total"] += 1
        request_module_lookup[row.id] = key
        payload["prompt_versions"].add(_normalize_prompt_version(getattr(row, "prompt_version", None)))
        status = str(getattr(row, "status", "")).lower()
        if status == "completed":
            payload["completed_total"] += 1
        if status in {"failed", "warning"}:
            payload["failed_total"] += 1
        if bool(getattr(row, "was_masked", False)):
            payload["masked_total"] += 1
        if bool(getattr(row, "was_user_visible", False)):
            payload["visible_total"] += 1
        latency_ms = getattr(row, "latency_ms", None)
        if latency_ms is not None:
            payload["latency_sum"] += int(latency_ms or 0)
            payload["latency_count"] += 1

    for row in recommendation_rows:
        key = request_module_lookup.get(getattr(row, "ai_request_log_id", None))
        if not key:
            continue
        payload = module_map[key]
        payload["recommendation_total"] += 1
        status = str(getattr(row, "status", "")).lower()
        if status == "accepted":
            payload["accepted_recommendations"] += 1
        if status == "open":
            payload["open_recommendations"] += 1

    for row in feedback_rows:
        key = request_module_lookup.get(getattr(row, "ai_request_log_id", None))
        if not key:
            continue
        payload = module_map[key]
        payload["feedback_total"] += 1
        feedback_type = str(getattr(row, "feedback_type", "")).lower()
        if feedback_type in NEGATIVE_FEEDBACK_TYPES:
            payload["negative_feedback"] += 1
        if feedback_type in POSITIVE_FEEDBACK_TYPES:
            payload["positive_feedback"] += 1

    module_rows: list[dict[str, Any]] = []
    for key, payload in module_map.items():
        if not is_visible_ai_module(key):
            continue
        request_total = int(payload["request_total"] or 0)
        recommendation_total = int(payload["recommendation_total"] or 0)
        feedback_total = int(payload["feedback_total"] or 0)
        success_rate_row = _safe_ratio(int(payload["completed_total"] or 0), request_total)
        masked_rate_row = _safe_ratio(int(payload["masked_total"] or 0), request_total)
        helpful_rate_row = _safe_ratio(int(payload["positive_feedback"] or 0), feedback_total)
        acceptance_rate_row = _safe_ratio(int(payload["accepted_recommendations"] or 0), recommendation_total)
        backlog_total = int(payload["open_recommendations"] or 0) + int(payload["negative_feedback"] or 0) + int(payload["failed_total"] or 0)
        quality_score_row = _quality_score(
            success_rate=success_rate_row,
            masked_rate=masked_rate_row,
            acceptance_rate=acceptance_rate_row,
            helpful_rate=helpful_rate_row,
            backlog_penalty=min(backlog_total * 2, 30),
        )
        module_rows.append(
            {
                "module_type": key,
                "request_total": request_total,
                "success_rate": success_rate_row,
                "masked_rate": masked_rate_row,
                "visibility_rate": _safe_ratio(int(payload["visible_total"] or 0), request_total),
                "acceptance_rate": acceptance_rate_row,
                "helpful_rate": helpful_rate_row,
                "avg_latency_ms": _safe_avg(int(payload["latency_sum"] or 0), int(payload["latency_count"] or 0)),
                "open_recommendations": int(payload["open_recommendations"] or 0),
                "negative_feedback": int(payload["negative_feedback"] or 0),
                "failed_total": int(payload["failed_total"] or 0),
                "prompt_version_total": len(payload["prompt_versions"]),
                "quality_score": quality_score_row,
                "backlog_total": backlog_total,
                "tone": _tone_from_score(quality_score_row, negative_feedback=int(payload["negative_feedback"] or 0), failed_total=int(payload["failed_total"] or 0)),
            }
        )
    module_rows.sort(key=lambda item: (-int(item["quality_score"]), -int(item["request_total"]), item["module_type"]))

    module_options = filter_visible_values(
        row[0]
        for row in AIRequestLog.query.with_entities(AIRequestLog.module_type).distinct().order_by(AIRequestLog.module_type.asc()).all()
        if row[0]
    )
    prompt_options = [
        _normalize_prompt_version(row[0])
        for row in AIRequestLog.query.with_entities(AIRequestLog.prompt_version).distinct().order_by(AIRequestLog.prompt_version.asc()).all()
    ]
    prompt_options = sorted({item for item in prompt_options if item})

    return {
        "selected_module_type": str(module_type or "").strip().lower(),
        "selected_prompt_version": str(prompt_version or "").strip().lower(),
        "selected_lookback_days": int(lookback_days or 30),
        "module_options": module_options,
        "prompt_options": prompt_options,
        "summary": {
            "request_total": total_requests,
            "quality_score": quality_score,
            "success_rate": success_rate,
            "visibility_rate": visibility_rate,
            "masked_rate": masked_rate,
            "acceptance_rate": acceptance_rate,
            "helpful_rate": helpful_rate,
            "avg_latency_ms": avg_latency_ms,
            "feedback_total": feedback_total,
            "recommendation_total": recommendation_total,
            "open_recommendations": open_recommendations,
            "negative_feedback": negative_feedback,
            "module_count": len(module_rows),
            "prompt_count": len(prompt_rows),
            "generated_at": utc_now(),
            "window_label": f"Son {int(lookback_days or 30)} gün",
            "since": since,
        },
        "module_rows": module_rows,
        "prompt_rows": prompt_rows,
        "top_prompt": prompt_rows[0] if prompt_rows else None,
        "lowest_prompt": prompt_rows[-1] if prompt_rows else None,
        "top_module": module_rows[0] if module_rows else None,
        "lowest_module": module_rows[-1] if module_rows else None,
    }