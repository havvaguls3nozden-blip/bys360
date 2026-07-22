
"""Performans yayın helper ailesi."""
from __future__ import annotations

from sqlalchemy import or_

from app.models import PerformanceEvaluation
from app.services.publish_service import get_publish_timestamp, is_evaluation_publishable


def _evaluation_published_at(evaluation):
    return get_publish_timestamp(evaluation)


def _build_publish_stats(scoped_query):
    return {
        "total": scoped_query.count(),
        "completed": scoped_query.filter(PerformanceEvaluation.status == "tamamlandi").count(),
        "published": scoped_query.filter(PerformanceEvaluation.is_published_to_employee.is_(True)).count(),
        "unpublished": scoped_query.filter(
            or_(
                PerformanceEvaluation.is_published_to_employee.is_(False),
                PerformanceEvaluation.is_published_to_employee.is_(None),
            )
        ).count(),
    }


def _build_publish_rows(selected_period, evaluations):
    rows = []
    for evaluation in evaluations:
        employee = evaluation.employee
        employee_name = "-"
        if employee:
            employee_name = employee.full_name or f"{employee.ad or ''} {employee.soyad or ''}".strip() or "-"

        is_completed = (evaluation.status or "") == "tamamlandi"
        is_published = bool(getattr(evaluation, "is_published_to_employee", False))
        publishable, publish_reason = is_evaluation_publishable(selected_period, evaluation)
        ready_to_publish = publishable and not is_published
        blocked = not publishable and not is_published

        rows.append(
            {
                "evaluation": evaluation,
                "employee_name": employee_name,
                "sicil_no": employee.sicil_no if employee and employee.sicil_no else "-",
                "birim": employee.birim if employee and employee.birim else "-",
                "ust_birim": employee.ust_birim if employee and employee.ust_birim else "-",
                "unvan": employee.unvan if employee and employee.unvan else "-",
                "final_score": float(evaluation.final_total_100 or 0),
                "is_completed": is_completed,
                "is_published": is_published,
                "ready_to_publish": ready_to_publish,
                "blocked": blocked,
                "publish_reason": publish_reason,
                "published_at": _evaluation_published_at(evaluation),
            }
        )
    return rows


def _build_filtered_publish_stats(evaluation_rows):
    return {
        "filtered_total": len(evaluation_rows),
        "filtered_completed": sum(1 for row in evaluation_rows if row["is_completed"]),
        "filtered_published": sum(1 for row in evaluation_rows if row["is_published"]),
        "filtered_unpublished": sum(1 for row in evaluation_rows if not row["is_published"]),
        "ready_to_publish": sum(1 for row in evaluation_rows if row["ready_to_publish"]),
        "blocked_count": sum(1 for row in evaluation_rows if row["blocked"]),
    }


def _filter_publish_logs(logs, log_actor: str = "", log_employee: str = ""):
    rows = list(logs or [])
    if log_actor:
        actor_lower = log_actor.lower()
        rows = [
            log
            for log in rows
            if log.actor and actor_lower in ((log.actor.full_name or f"{log.actor.ad or ''} {log.actor.soyad or ''}".strip() or "").lower())
        ]
    if log_employee:
        employee_lower = log_employee.lower()
        rows = [
            log
            for log in rows
            if log.employee and employee_lower in ((log.employee.full_name or f"{log.employee.ad or ''} {log.employee.soyad or ''}".strip() or "").lower())
        ]
    return rows


__all__ = [
    "_build_filtered_publish_stats",
    "_build_publish_rows",
    "_build_publish_stats",
    "_evaluation_published_at",
    "_filter_publish_logs",
]