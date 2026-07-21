from __future__ import annotations

import logging

"""Performans değerlendirmesinde 'kimde kaldı / en son kim puanladı' özeti."""

from typing import Any

from app.models import EvaluationAssignment, PerformanceLowScoreProcess
from app.services.performance.low_score_process_service import (
    humanize_process_status,
    is_low_score_evaluation,
)

logger = logging.getLogger(__name__)

DONE_STATUSES = {"tamamlandi", "tamamlandı", "completed", "submitted"}


def _safe_name(user: Any | None) -> str:
    if not user:
        return "-"
    return getattr(user, "full_name", None) or f"{getattr(user, 'ad', '') or ''} {getattr(user, 'soyad', '') or ''}".strip() or "-"


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_done_assignment(assignment: Any | None) -> bool:
    if not assignment:
        return False
    return bool(getattr(assignment, "completed_at", None)) or _status(getattr(assignment, "status", "")) in DONE_STATUSES


def _level_label(level: int | None) -> str:
    return {1: "1. Amir", 2: "2. Amir", 3: "3. Amir"}.get(level, "Süreç")


def _assignments(evaluation: Any | None) -> list[Any]:
    if not evaluation:
        return []
    try:
        return EvaluationAssignment.query.filter_by(
            period_id=getattr(evaluation, "period_id", None),
            employee_id=getattr(evaluation, "employee_id", None),
        ).order_by(EvaluationAssignment.manager_level.desc()).all()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return []


def _assignment_for_level(assignments: list[Any], level: int) -> Any | None:
    for assignment in assignments:
        try:
            if int(getattr(assignment, "manager_level", 0) or 0) == level:
                return assignment
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/evaluation_flow_status_service.py:50)")
            continue
    return None


def _expected_levels(evaluation: Any | None) -> list[int]:
    if not evaluation:
        return []
    levels: list[int] = []
    if getattr(evaluation, "level_3_evaluator_id", None):
        levels.append(3)
    if getattr(evaluation, "level_2_evaluator_id", None):
        levels.append(2)
    if getattr(evaluation, "level_1_evaluator_id", None):
        levels.append(1)
    return levels or [1]


def _completed_flag(evaluation: Any | None, level: int) -> bool:
    return bool(getattr(evaluation, f"level_{level}_completed", False))


def _evaluator(evaluation: Any | None, level: int) -> Any | None:
    return getattr(evaluation, f"level_{level}_evaluator", None)


def _level_score(evaluation: Any | None, level: int) -> float | None:
    value = getattr(evaluation, f"level_{level}_total_100", None)
    try:
        return round(float(value), 2)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def build_evaluation_flow_status(evaluation: Any | None) -> dict[str, Any]:
    if not evaluation:
        return {"summary": "Değerlendirme yok", "tone": "locked", "current_owner": "-", "last_scorer": "-", "steps": []}

    assignments = _assignments(evaluation)
    expected_levels = _expected_levels(evaluation)
    steps: list[dict[str, Any]] = []
    current_owner = "Yayın / İK kontrol"
    current_owner_level = None

    for level in expected_levels:
        assignment = _assignment_for_level(assignments, level)
        evaluator = _evaluator(evaluation, level) or getattr(assignment, "evaluator", None)
        done = _completed_flag(evaluation, level) or _is_done_assignment(assignment)
        # BYS360_PHASE4_THIRD_SUPERVISOR_STATUS_LANGUAGE
        if done:
            status_label = "Tamamlandı"
        elif level == 3:
            try:
                from app.services.performance.third_supervisor_policy import (
                    third_supervisor_assignment_waiting_label,
                )
                status_label = third_supervisor_assignment_waiting_label(evaluation)
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                status_label = "Yorum/Görüş Bekliyor"
        else:
            status_label = "Bekliyor"
        if not done and current_owner_level is None:
            current_owner_level = level
            current_owner = _safe_name(evaluator)
        steps.append({
            "level": level,
            "label": _level_label(level),
            "owner": _safe_name(evaluator),
            "status": status_label,
            "done": done,
            "score": _level_score(evaluation, level),
            "completed_at": getattr(assignment, "completed_at", None) if assignment else None,
        })

    completed_assignments = [a for a in assignments if _is_done_assignment(a)]
    completed_assignments.sort(key=lambda a: getattr(a, "completed_at", None) or getattr(a, "updated_at", None) or getattr(a, "created_at", None), reverse=True)
    last_assignment = completed_assignments[0] if completed_assignments else None
    last_scorer = _safe_name(getattr(last_assignment, "evaluator", None)) if last_assignment else "Henüz yok"
    last_level = int(getattr(last_assignment, "manager_level", 0) or 0) if last_assignment else None
    last_scored_at = getattr(last_assignment, "completed_at", None) if last_assignment else None

    low_score_process = None
    if is_low_score_evaluation(evaluation):
        try:
            low_score_process = PerformanceLowScoreProcess.query.filter_by(evaluation_id=getattr(evaluation, "id", None)).first()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            low_score_process = None

    if current_owner_level is None:
        if low_score_process and not low_score_process.is_finalized_for_publish:
            current_owner = getattr(low_score_process, "current_owner_label", None) or "İK/Admin / Başkan"
            summary = humanize_process_status(low_score_process)
            tone = "critical"
        elif bool(getattr(evaluation, "is_published_to_employee", False)):
            current_owner = "Tamamlandı"
            summary = "Personele açık"
            tone = "published"
        else:
            current_owner = "Yayın Merkezi"
            summary = "Yayın bekliyor"
            tone = "watch"
    else:
        summary = f"{_level_label(current_owner_level)} bekliyor"
        tone = "watch"

    return {
        "summary": summary,
        "tone": tone,
        "current_owner": current_owner,
        "current_owner_level": current_owner_level,
        "last_scorer": last_scorer,
        "last_level": _level_label(last_level) if last_level else "-",
        "last_scored_at": last_scored_at,
        "steps": steps,
        "low_score_process": low_score_process,
        "has_low_score_process": bool(low_score_process),
    }

# BYS360_PHASE4_THIRD_SUPERVISOR_STATUS_LANGUAGE
# BYS360_PHASE4_3_FLOW_STATUS_LANGUAGE
# BYS360_PHASE4_3_FLOW_SUMMARY_LANGUAGE
# Final gate uyum notu: 3. amir statü dili third_supervisor_pending_status_label ile yönetilir.
# Varsayılan yorum modu etiketi: Yorum/Görüş Bekliyor
