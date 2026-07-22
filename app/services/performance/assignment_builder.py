
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

def prevent_duplicate_assignment(existing_keys, key):
    return key not in existing_keys

def build_assignment_key(period_id, employee_id, evaluator_id, level):
    return f"{period_id}-{employee_id}-{evaluator_id}-{level}"

def sync_evaluation_summary(evaluation, evaluator_id, level):
    if level == 1:
        evaluation["level_1_evaluator_id"] = evaluator_id
    elif level == 2:
        evaluation["level_2_evaluator_id"] = evaluator_id
    elif level == 3:
        evaluation["level_3_evaluator_id"] = evaluator_id
    return evaluation

def build_assignments(period_id:int, chains:list[dict[str,Any]]):
    assignments = []
    existing_keys = set()

    for c in chains:
        emp = c["employee_id"]

        for level in [3,2,1]:
            evaluator = c.get(f"manager_{level}_id")
            if not evaluator:
                continue
            if level == 3:
                # BYS360_PHASE4_THIRD_SUPERVISOR_LEGACY_TASK_GUARD
                try:
                    from app.services.performance.third_supervisor_policy import (
                        should_create_third_supervisor_task,
                    )
                    if not should_create_third_supervisor_task(evaluator_id=evaluator):
                        continue
                except Exception:
                    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                    import logging
                    logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/assignment_builder.py")
            key = build_assignment_key(period_id, emp, evaluator, level)
            if not prevent_duplicate_assignment(existing_keys, key):
                continue

            existing_keys.add(key)

            assignments.append({
                "period_id": period_id,
                "employee_id": emp,
                "evaluator_id": evaluator,
                "manager_level": level,
                "status": "bekliyor",
                "created_at": datetime.now()
            })

    return assignments