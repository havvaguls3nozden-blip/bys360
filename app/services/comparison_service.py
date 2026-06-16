from __future__ import annotations

from types import SimpleNamespace

from app.extensions import db
from app.models import (
    PerformanceCriteria,
    PerformanceEvaluation,
    PerformanceEvaluationItem,
    PerformancePeriod,
    PerformanceResultSnapshot,
)


def _object_id(value):
    """User nesnesi ya da ham id geldiğinde güvenli biçimde id döndürür."""
    return getattr(value, "id", value)


def safe_float(value, default=0.0):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return float(default)


def comparison_band(score):
    score = safe_float(score)
    if score < 70:
        return "low"
    if score > 90:
        return "high"
    return "mid"


def snapshot_payload_map(snapshot):
    payload = getattr(snapshot, "payload_json", None) or {}
    rows = payload.get("criteria", []) if isinstance(payload, dict) else []
    mapped = {}
    for item in rows:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        mapped[name] = {
            "name": name,
            "criteria_code": item.get("criteria_code"),
            "weight": safe_float(item.get("weight")),
            "score": safe_float(item.get("visible_final_score")),
            "level_1_score": item.get("level_1_score"),
            "level_2_score": item.get("level_2_score"),
            "level_3_score": item.get("level_3_score"),
            "description": item.get("description"),
        }
    return mapped


def compare_two_snapshots(old_snapshot, new_snapshot):
    old_map = snapshot_payload_map(old_snapshot) if old_snapshot else {}
    new_map = snapshot_payload_map(new_snapshot) if new_snapshot else {}

    names = sorted(set(old_map.keys()) | set(new_map.keys()))
    rows = []
    for name in names:
        old_score = safe_float(old_map.get(name, {}).get("score"))
        new_score = safe_float(new_map.get(name, {}).get("score"))
        diff = round(new_score - old_score, 2)
        rows.append(
            {
                "name": name,
                "old_score": old_score,
                "new_score": new_score,
                "diff": diff,
                "band": comparison_band(new_score),
                "description": new_map.get(name, {}).get("description")
                or old_map.get(name, {}).get("description"),
            }
        )

    rows.sort(key=lambda x: x["name"])
    return rows


def build_change_summary(criteria_rows):
    if not criteria_rows:
        return {"best": None, "worst": None}

    sorted_rows = sorted(criteria_rows, key=lambda x: x["diff"], reverse=True)
    best = sorted_rows[0]
    worst = sorted_rows[-1]

    if best["diff"] == 0:
        best = None
    if worst["diff"] == 0:
        worst = None

    return {"best": best, "worst": worst}


def _build_payload_from_evaluation(evaluation: PerformanceEvaluation) -> dict:
    items = (
        PerformanceEvaluationItem.query
        .join(PerformanceCriteria, PerformanceCriteria.id == PerformanceEvaluationItem.criteria_id)
        .filter(PerformanceEvaluationItem.evaluation_id == evaluation.id)
        .order_by(PerformanceCriteria.sort_order.asc(), PerformanceCriteria.id.asc(), PerformanceEvaluationItem.manager_level.asc())
        .all()
    )

    grouped = {}
    for item in items:
        criteria = item.criteria
        if not criteria:
            continue
        row = grouped.setdefault(
            criteria.id,
            {
                "criteria_id": criteria.id,
                "criteria_code": getattr(criteria, "criteria_code", None),
                "name": getattr(criteria, "name", "") or "",
                "description": getattr(criteria, "description", None),
                "weight": safe_float(getattr(criteria, "weight", 0)),
                "sort_order": int(getattr(criteria, "sort_order", 0) or 0),
                "level_1_score": None,
                "level_2_score": None,
                "level_3_score": None,
                "visible_final_score": None,
            },
        )
        score_100 = safe_float(getattr(item, "score_100", 0))
        if not score_100 and getattr(item, "score", None) not in (None, ""):
            try:
                bounded = min(5.0, max(1.0, float(item.score)))
                score_100 = round(((bounded - 1.0) / 4.0) * 100.0, 2)
            except (TypeError, ValueError):
                score_100 = 0.0
        if item.manager_level == 1:
            row["level_1_score"] = score_100
        elif item.manager_level == 2:
            row["level_2_score"] = score_100
        elif item.manager_level == 3:
            row["level_3_score"] = score_100

    for row in grouped.values():
        if row["level_2_score"] is not None:
            row["visible_final_score"] = row["level_2_score"]
        elif row["level_1_score"] is not None:
            row["visible_final_score"] = row["level_1_score"]
        elif row["level_3_score"] is not None:
            row["visible_final_score"] = row["level_3_score"]
        else:
            row["visible_final_score"] = 0

    criteria_rows = sorted(grouped.values(), key=lambda x: (x["sort_order"], x["criteria_id"]))
    return {
        "period_id": evaluation.period_id,
        "evaluation_id": evaluation.id,
        "status": getattr(evaluation, "status", None),
        "criteria": criteria_rows,
    }


def _build_snapshot_like_from_evaluation(period: PerformancePeriod, evaluation: PerformanceEvaluation):
    return SimpleNamespace(
        id=f"eval-{evaluation.id}",
        period_id=period.id,
        evaluation_id=evaluation.id,
        employee_id=evaluation.employee_id,
        final_total_100=safe_float(getattr(evaluation, "final_total_100", 0)),
        ranking_in_unit=None,
        ranking_in_scope=None,
        payload_json=_build_payload_from_evaluation(evaluation),
        published_at=getattr(evaluation, "published_to_employee_at", None),
    )


def _dedupe_period_rows(period_rows):
    seen_period_ids = set()
    periods = []
    snapshots_by_period = {}
    normalized_rows = []

    for period, snapshot in period_rows:
        if not period or not getattr(period, "id", None):
            continue
        if period.id in seen_period_ids:
            continue
        seen_period_ids.add(period.id)
        periods.append(period)
        snapshots_by_period[period.id] = snapshot
        normalized_rows.append((period, snapshot))

    return periods, snapshots_by_period, normalized_rows


def _snapshot_rows_for_employee(employee_id: int):
    return (
        db.session.query(PerformancePeriod, PerformanceResultSnapshot)
        .join(PerformanceResultSnapshot, PerformanceResultSnapshot.period_id == PerformancePeriod.id)
        .filter(
            PerformanceResultSnapshot.employee_id == employee_id,
            PerformanceResultSnapshot.is_current.is_(True),
        )
        .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
        .all()
    )


def _published_evaluation_rows_for_employee(employee_id: int):
    return (
        db.session.query(PerformancePeriod, PerformanceEvaluation)
        .join(PerformanceEvaluation, PerformanceEvaluation.period_id == PerformancePeriod.id)
        .filter(
            PerformanceEvaluation.employee_id == employee_id,
            PerformanceEvaluation.is_published_to_employee.is_(True),
        )
        .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
        .all()
    )


def snapshot_period_options_for_user(employee_id):
    employee_id = _object_id(employee_id)
    if not employee_id:
        return [], {}, []

    snapshot_rows = _snapshot_rows_for_employee(employee_id)
    if snapshot_rows:
        return _dedupe_period_rows(snapshot_rows)

    evaluation_rows = _published_evaluation_rows_for_employee(employee_id)
    if not evaluation_rows:
        return [], {}, []

    fallback_rows = []
    for period, evaluation in evaluation_rows:
        fallback_rows.append((period, _build_snapshot_like_from_evaluation(period, evaluation)))

    return _dedupe_period_rows(fallback_rows)
