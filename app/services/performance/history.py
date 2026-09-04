from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models import PerformanceEvaluation, PerformanceEvaluationHistory

ACTION_LABELS = {
    "SAVED_BY_LEVEL_1": "1. amir taslağı kaydetti",
    "SAVED_BY_LEVEL_2": "2. amir taslağı kaydetti",
    "COMPLETED_BY_LEVEL_1": "1. amir değerlendirmeyi tamamladı",
    "COMPLETED_BY_LEVEL_3": "3. amir değerlendirmeyi tamamladı",
    "SUBMITTED_TO_LEVEL_1": "2. amir değerlendirmeyi 1. amire gönderdi",
    "WITHDRAWN": "2. amir gönderimi geri çekti",
    "RETURNED_BY_LEVEL_1": "1. amir değerlendirmeyi 2. amire iade etti",
}

STATUS_LABELS = {
    "bekliyor_3_amir": "3. amir bekleniyor",
    "tamamlandi_3_amir": "3. amir tamamladı",
    "taslak_1_amir": "2. amir taslak aşamasında",
    "gonderildi_2_amir": "1. amire gönderildi",
    "goruldu_2_amir": "1. amir görüntüledi",
    "iade_1_amir": "2. amire iade edildi",
    "yeniden_gonderildi_2_amir": "Yeniden 1. amire gönderildi",
    "tamamlandi_2_amir": "1. amir tamamladı",
    "geri_cekildi_1_amir": "Gönderim geri çekildi",
}

ACTOR_LEVEL_LABELS = {
    1: "1. Amir",
    2: "2. Amir",
    3: "3. Amir",
}


def build_score_snapshot(evaluation: PerformanceEvaluation) -> dict[str, Any]:
    return {
        "level_1_total_100": float(getattr(evaluation, "level_1_total_100", 0) or 0),
        "level_2_total_100": float(getattr(evaluation, "level_2_total_100", 0) or 0),
        "level_3_total_100": float(getattr(evaluation, "level_3_total_100", 0) or 0),
        "final_total_100": float(getattr(evaluation, "final_total_100", 0) or 0),
        "workflow_status": getattr(evaluation, "workflow_status", None),
        "status": getattr(evaluation, "status", None),
    }


def humanize_workflow_status(status: str | None) -> str:
    clean = (status or "").strip()
    if not clean:
        return "-"
    return STATUS_LABELS.get(clean, "Süreç Durumu")

def humanize_action_type(action_type: str | None) -> str:
    clean = (action_type or "").strip()
    if not clean:
        return "-"
    return ACTION_LABELS.get(clean, "Süreç işlemi")

def humanize_actor_level(level: int | None) -> str:
    if level is None:
        return "-"
    return ACTOR_LEVEL_LABELS.get(level, f"Seviye {level}")

def log_evaluation_action(
    evaluation: PerformanceEvaluation,
    *,
    action_type: str,
    actor_user_id: int | None = None,
    actor_level: int | None = None,
    from_status: str | None = None,
    to_status: str | None = None,
    note: str = "",
) -> PerformanceEvaluationHistory:
    row = PerformanceEvaluationHistory(
        evaluation_id=evaluation.id,
        actor_user_id=actor_user_id,
        actor_level=actor_level,
        action_type=action_type,
        from_status=from_status,
        to_status=to_status,
        note=(note or "").strip() or None,
        score_snapshot=build_score_snapshot(evaluation),
    )
    db.session.add(row)
    db.session.flush()
    return row

def build_history_rows(evaluation_id: int):
    rows = (
        PerformanceEvaluationHistory.query
        .filter_by(evaluation_id=evaluation_id)
        .order_by(PerformanceEvaluationHistory.created_at.desc(), PerformanceEvaluationHistory.id.desc())
        .all()
    )
    for row in rows:
        actor_name = "-"
        if getattr(row, "actor", None):
            actor_name = getattr(row.actor, "full_name", None) or getattr(row.actor, "name", None) or getattr(row.actor, "email", None) or "-"
        snap = row.score_snapshot or {}
        row.action_label = humanize_action_type(getattr(row, "action_type", None))
        row.actor_level_label = humanize_actor_level(getattr(row, "actor_level", None))
        row.actor_name_label = actor_name
        row.from_status_label = humanize_workflow_status(getattr(row, "from_status", None))
        row.to_status_label = humanize_workflow_status(getattr(row, "to_status", None))
        row.score_summary = {"level_1": float(snap.get("level_1_total_100", 0) or 0), "level_2": float(snap.get("level_2_total_100", 0) or 0), "level_3": float(snap.get("level_3_total_100", 0) or 0), "final": float(snap.get("final_total_100", 0) or 0)}
    return rows

def build_history_summary(history_rows) -> dict[str, Any]:
    action_counts: dict[str, int] = {}
    actor_counts: dict[str, int] = {}
    for row in history_rows:
        action_label = getattr(row, "action_label", None) or humanize_action_type(getattr(row, "action_type", None))
        action_counts[action_label] = action_counts.get(action_label, 0) + 1
        actor_label = getattr(row, "actor_level_label", None) or humanize_actor_level(getattr(row, "actor_level", None))
        actor_counts[actor_label] = actor_counts.get(actor_label, 0) + 1

    latest = history_rows[0] if history_rows else None
    return {
        "total_events": len(history_rows),
        "latest_action": getattr(latest, "action_label", None) if latest else "-",
        "latest_actor": getattr(latest, "actor_level_label", None) if latest else "-",
        "latest_date": getattr(latest, "created_at", None) if latest else None,
        "action_counts": action_counts,
        "actor_counts": actor_counts,
    }

def get_evaluation_history(evaluation_id: int):
    return build_history_rows(evaluation_id)


__all__ = [
    "ACTION_LABELS",
    "STATUS_LABELS",
    "ACTOR_LEVEL_LABELS",
    "build_score_snapshot",
    "humanize_workflow_status",
    "humanize_action_type",
    "humanize_actor_level",
    "log_evaluation_action",
    "build_history_rows",
    "build_history_summary",
    "get_evaluation_history",
]