"""
BYS360 AI Karar Destek Faz 11 entegrasyon servisi.

Karne, dönem içi not, geçmiş puan ve mevcut gelişim önerisi verilerini
karar destek rehber alanına dönüştürür. Canlı şema farklılıklarına karşı
toleranslı sorgular kullanır.

BYS360_AI_DECISION_FAZ11_INTEGRATION_OK
"""
from __future__ import annotations

from typing import Any
from collections.abc import Mapping, Sequence

from app.services.ai_decision.development_guidance_policy import build_development_guidance_context

try:  # pragma: no cover - canlı projede vardır
    from sqlalchemy import text
except Exception:  # pragma: no cover
    text = None  # type: ignore


RECOMMENDATION_TABLE_CANDIDATES = (
    "performance_development_recommendations",
    "performance_guidance_recommendations",
    "feedback_action_plans",
    "ai_recommendations",
)


def _rows_as_dicts(result: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if result is None:
        return rows
    for row in result:
        if hasattr(row, "_mapping"):
            rows.append(dict(row._mapping))
        elif isinstance(row, Mapping):
            rows.append(dict(row))
        else:
            try:
                rows.append(dict(row))
            except Exception:
                rows.append({})
    return rows


def _table_exists(db_session: Any, table_name: str) -> bool:
    if text is None or db_session is None:
        return False
    try:
        result = db_session.execute(text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_name = :table_name LIMIT 1"
        ), {"table_name": table_name}).scalar()
        return bool(result)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return False


def fetch_evaluation_summary(db_session: Any, evaluation_id: int | None = None) -> dict[str, Any]:
    if text is None or db_session is None or not evaluation_id:
        return {}
    if not _table_exists(db_session, "performance_evaluations"):
        return {}
    try:
        result = db_session.execute(text("""
            SELECT
                id,
                COALESCE(personnel_id, user_id, employee_id) AS personnel_id,
                period_id,
                COALESCE(final_score, total_score, score, calculated_score) AS score,
                COALESCE(general_comment, comment, evaluator_comment, '') AS general_comment,
                created_at
            FROM performance_evaluations
            WHERE id = :evaluation_id
            LIMIT 1
        """), {"evaluation_id": evaluation_id})
        rows = _rows_as_dicts(result)
        return rows[0] if rows else {}
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return {}


def fetch_criteria_results(db_session: Any, evaluation_id: int | None = None) -> list[dict[str, Any]]:
    if text is None or db_session is None or not evaluation_id:
        return []
    if not _table_exists(db_session, "performance_evaluation_items"):
        return []
    try:
        result = db_session.execute(text("""
            SELECT
                i.id,
                COALESCE(c.name, c.title, i.criterion_name, 'Değerlendirme kriteri') AS criterion_name,
                COALESCE(i.score, i.point, i.value, i.score_value) AS score
            FROM performance_evaluation_items i
            LEFT JOIN performance_criteria c ON c.id = i.criterion_id
            WHERE i.evaluation_id = :evaluation_id
            ORDER BY i.id ASC
            LIMIT 100
        """), {"evaluation_id": evaluation_id})
        return _rows_as_dicts(result)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return []


def fetch_previous_scores(
    db_session: Any,
    *,
    personnel_id: int | None = None,
    current_evaluation_id: int | None = None,
    limit: int = 6,
) -> list[float]:
    if text is None or db_session is None or not personnel_id:
        return []
    scores: list[float] = []
    try:
        if _table_exists(db_session, "performance_archived_results"):
            result = db_session.execute(text("""
                SELECT score AS score
                FROM performance_archived_results
                WHERE personnel_id = :personnel_id
                ORDER BY year ASC NULLS LAST, period_id ASC NULLS LAST, id ASC
                LIMIT :limit
            """), {"personnel_id": personnel_id, "limit": limit})
            for row in _rows_as_dicts(result):
                try:
                    scores.append(float(row.get("score")))
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai_decision/development_guidance_integration.py")
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai_decision/development_guidance_integration.py")
    try:
        if _table_exists(db_session, "performance_evaluations"):
            result = db_session.execute(text("""
                SELECT COALESCE(final_score, total_score, score, calculated_score) AS score
                FROM performance_evaluations
                WHERE COALESCE(personnel_id, user_id, employee_id) = :personnel_id
                  AND (:current_evaluation_id IS NULL OR id <> :current_evaluation_id)
                ORDER BY created_at ASC NULLS LAST, id ASC
                LIMIT :limit
            """), {"personnel_id": personnel_id, "current_evaluation_id": current_evaluation_id, "limit": limit})
            for row in _rows_as_dicts(result):
                try:
                    scores.append(float(row.get("score")))
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai_decision/development_guidance_integration.py")
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai_decision/development_guidance_integration.py")
    return scores[-limit:]


def fetch_existing_recommendations(
    db_session: Any,
    *,
    personnel_id: int | None = None,
    period_id: int | None = None,
    evaluation_id: int | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    if text is None or db_session is None:
        return []
    table_name = next((t for t in RECOMMENDATION_TABLE_CANDIDATES if _table_exists(db_session, t)), None)
    if not table_name:
        return []
    queries = {
        "performance_development_recommendations": """
            SELECT id, recommendation_text AS text, created_at
            FROM performance_development_recommendations
            WHERE (:personnel_id IS NULL OR personnel_id = :personnel_id)
              AND (:period_id IS NULL OR period_id = :period_id)
              AND (:evaluation_id IS NULL OR evaluation_id = :evaluation_id)
            ORDER BY created_at DESC NULLS LAST, id DESC
            LIMIT :limit
        """,
        "performance_guidance_recommendations": """
            SELECT id, guidance_text AS text, created_at
            FROM performance_guidance_recommendations
            WHERE (:personnel_id IS NULL OR personnel_id = :personnel_id)
              AND (:period_id IS NULL OR period_id = :period_id)
              AND (:evaluation_id IS NULL OR evaluation_id = :evaluation_id)
            ORDER BY created_at DESC NULLS LAST, id DESC
            LIMIT :limit
        """,
        "feedback_action_plans": """
            SELECT id, COALESCE(action_title, title, description, '') AS text, created_at
            FROM feedback_action_plans
            WHERE (:personnel_id IS NULL OR user_id = :personnel_id)
              AND (:period_id IS NULL OR period_id = :period_id)
              AND (:evaluation_id IS NULL OR evaluation_id = :evaluation_id)
            ORDER BY created_at DESC NULLS LAST, id DESC
            LIMIT :limit
        """,
        "ai_recommendations": """
            SELECT id, COALESCE(recommendation_text, content, summary, '') AS text, created_at
            FROM ai_recommendations
            WHERE (:personnel_id IS NULL OR personnel_id = :personnel_id)
              AND (:period_id IS NULL OR period_id = :period_id)
              AND (:evaluation_id IS NULL OR evaluation_id = :evaluation_id)
            ORDER BY created_at DESC NULLS LAST, id DESC
            LIMIT :limit
        """,
    }
    try:
        result = db_session.execute(text(queries[table_name]), {
            "personnel_id": personnel_id,
            "period_id": period_id,
            "evaluation_id": evaluation_id,
            "limit": limit,
        })
        return _rows_as_dicts(result)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return []


def fetch_interim_summary(
    db_session: Any,
    *,
    personnel_id: int | None = None,
    period_id: int | None = None,
    evaluation_id: int | None = None,
) -> dict[str, Any]:
    if text is None or db_session is None:
        return {}
    if _table_exists(db_session, "ai_decision_interim_feedback_snapshots"):
        try:
            result = db_session.execute(text("""
                SELECT total_notes, positive_total, negative_total, development_need_total, balance_label
                FROM ai_decision_interim_feedback_snapshots
                WHERE (:personnel_id IS NULL OR personnel_id = :personnel_id)
                  AND (:period_id IS NULL OR period_id = :period_id)
                  AND (:evaluation_id IS NULL OR evaluation_id = :evaluation_id)
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            """), {
                "personnel_id": personnel_id,
                "period_id": period_id,
                "evaluation_id": evaluation_id,
            })
            rows = _rows_as_dicts(result)
            if rows:
                row = rows[0]
                return {
                    "total_notes": row.get("total_notes") or 0,
                    "positive_total": row.get("positive_total") or 0,
                    "negative_total": row.get("negative_total") or 0,
                    "development_need_total": row.get("development_need_total") or 0,
                    "balance_label": row.get("balance_label") or "",
                }
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
            return {}
    return {}


def build_development_guidance_from_db(
    db_session: Any,
    *,
    evaluation_id: int | None = None,
    personnel_id: int | None = None,
    period_id: int | None = None,
    score: float | None = None,
    viewer_role: str = "",
) -> dict[str, Any]:
    evaluation = fetch_evaluation_summary(db_session, evaluation_id)
    personnel_id = personnel_id or evaluation.get("personnel_id")
    period_id = period_id or evaluation.get("period_id")
    score = score if score is not None else evaluation.get("score")
    criteria = fetch_criteria_results(db_session, evaluation_id)
    previous_scores = fetch_previous_scores(
        db_session,
        personnel_id=personnel_id,
        current_evaluation_id=evaluation_id,
    )
    interim_summary = fetch_interim_summary(
        db_session,
        personnel_id=personnel_id,
        period_id=period_id,
        evaluation_id=evaluation_id,
    )
    existing = fetch_existing_recommendations(
        db_session,
        personnel_id=personnel_id,
        period_id=period_id,
        evaluation_id=evaluation_id,
    )
    return build_development_guidance_context(
        score=score,
        previous_scores=previous_scores,
        interim_summary=interim_summary,
        criteria_results=criteria,
        general_comment=evaluation.get("general_comment"),
        existing_recommendations=existing,
        viewer_role=viewer_role,
    )


def persist_development_guidance_snapshot(
    db_session: Any,
    *,
    period_id: int | None,
    personnel_id: int | None,
    evaluation_id: int | None,
    context: Mapping[str, Any],
) -> bool:
    if text is None or db_session is None:
        return False
    try:
        summary = context.get("summary", {}) if isinstance(context, Mapping) else {}
        db_session.execute(text("""
            INSERT INTO ai_decision_development_guidance_snapshots
                (period_id, personnel_id, evaluation_id, score_value, score_band,
                 recommendation_count, priority_label, safe_summary)
            VALUES
                (:period_id, :personnel_id, :evaluation_id, :score_value, :score_band,
                 :recommendation_count, :priority_label, :safe_summary)
        """), {
            "period_id": period_id,
            "personnel_id": personnel_id,
            "evaluation_id": evaluation_id,
            "score_value": summary.get("score"),
            "score_band": str(summary.get("score_band") or ""),
            "recommendation_count": int(context.get("recommendation_count") or 0),
            "priority_label": _highest_priority(context.get("cards") or []),
            "safe_summary": str(context.get("safe_visibility_note") or "")[:500],
        })
        db_session.commit()
        return True
    except Exception:
        try:
            db_session.rollback()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai_decision/development_guidance_integration.py")
        return False


def _highest_priority(cards: Sequence[Mapping[str, Any]]) -> str:
    order = {"critical": 4, "high": 3, "normal": 2, "low": 1}
    best = "low"
    for card in cards or []:
        priority = str(card.get("priority") or "low")
        if order.get(priority, 0) > order.get(best, 0):
            best = priority
    return best
