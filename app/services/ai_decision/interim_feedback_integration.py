"""
BYS360 AI Karar Destek Faz 10 entegrasyon servisi.

Dönem içi notları, geri bildirim kayıtlarını ve performans değerlendirme
bağlamını karar destek özetine dönüştürür. Veritabanı modeli farklı canlı
sürümlerde değişebileceği için sorgular toleranslı tutulmuştur.

BYS360_AI_DECISION_FAZ10_INTEGRATION_OK
"""
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from app.services.ai_decision.interim_feedback_policy import build_interim_feedback_decision_support

logger = logging.getLogger(__name__)

try:  # pragma: no cover - canlı projede vardır
    from sqlalchemy import text
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/services/ai_decision/interim_feedback_integration.py | line=21")
    text = None  # type: ignore


INTERIM_NOTE_TABLE_CANDIDATES = (
    "performance_interim_notes",
    "performance_period_notes",
    "feedback_action_plans",
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
            rows.append(dict(row))
    return rows


def _table_exists(db_session: Any, table_name: str) -> bool:
    # BYS360 DEFECT AL: raw PostgreSQL-only information_schema/current_schema()
    # query replaced with SQLAlchemy's inspect(), which is dialect-neutral by
    # construction.
    try:
        from sqlalchemy import inspect
        return bool(inspect(db_session.get_bind()).has_table(table_name))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/ai_decision/interim_feedback_integration.py | line=55")
        return False


def fetch_interim_notes(
    db_session: Any,
    *,
    personnel_id: int | None = None,
    period_id: int | None = None,
    evaluation_id: int | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Canlı şemaya göre bulunabilen ara not tablosundan kayıt döndürür."""
    if text is None or db_session is None:
        return []

    table_name = next((t for t in INTERIM_NOTE_TABLE_CANDIDATES if _table_exists(db_session, t)), None)
    if not table_name:
        return []

    # Sütun adları canlı sürümler arasında değişebildiği için en yaygın alanlar
    # güvenli aliaslarla okunur.
    column_map_sql = {
        "performance_interim_notes": """
            SELECT
                id,
                COALESCE(note_type, category, 'general_observation') AS note_type,
                COALESCE(note_text, description, summary, '') AS note_text,
                personnel_id,
                period_id,
                evaluation_id,
                created_at
            FROM performance_interim_notes
            WHERE (:personnel_id IS NULL OR personnel_id = :personnel_id)
              AND (:period_id IS NULL OR period_id = :period_id)
              AND (:evaluation_id IS NULL OR evaluation_id = :evaluation_id)
            ORDER BY created_at DESC NULLS LAST, id DESC
            LIMIT :limit
        """,
        "performance_period_notes": """
            SELECT
                id,
                COALESCE(note_type, category, 'general_observation') AS note_type,
                COALESCE(note_text, description, summary, '') AS note_text,
                personnel_id,
                period_id,
                NULL::integer AS evaluation_id,
                created_at
            FROM performance_period_notes
            WHERE (:personnel_id IS NULL OR personnel_id = :personnel_id)
              AND (:period_id IS NULL OR period_id = :period_id)
            ORDER BY created_at DESC NULLS LAST, id DESC
            LIMIT :limit
        """,
        "feedback_action_plans": """
            SELECT
                id,
                'feedback' AS note_type,
                COALESCE(action_title, title, description, '') AS note_text,
                user_id AS personnel_id,
                period_id,
                evaluation_id,
                created_at
            FROM feedback_action_plans
            WHERE (:personnel_id IS NULL OR user_id = :personnel_id)
              AND (:period_id IS NULL OR period_id = :period_id)
              AND (:evaluation_id IS NULL OR evaluation_id = :evaluation_id)
            ORDER BY created_at DESC NULLS LAST, id DESC
            LIMIT :limit
        """,
    }

    try:
        result = db_session.execute(text(column_map_sql[table_name]), {
            "personnel_id": personnel_id,
            "period_id": period_id,
            "evaluation_id": evaluation_id,
            "limit": limit,
        })
        return _rows_as_dicts(result)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/ai_decision/interim_feedback_integration.py | line=135")
        return []


def build_interim_feedback_context(
    db_session: Any,
    *,
    personnel_id: int | None = None,
    period_id: int | None = None,
    evaluation_id: int | None = None,
    viewer_role: str = "",
) -> dict[str, Any]:
    notes = fetch_interim_notes(
        db_session,
        personnel_id=personnel_id,
        period_id=period_id,
        evaluation_id=evaluation_id,
    )
    return build_interim_feedback_decision_support(notes, viewer_role=viewer_role)


def persist_interim_feedback_snapshot(
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
            INSERT INTO ai_decision_interim_feedback_snapshots
                (period_id, personnel_id, evaluation_id, total_notes, positive_total,
                 negative_total, development_need_total, balance_label)
            VALUES
                (:period_id, :personnel_id, :evaluation_id, :total_notes, :positive_total,
                 :negative_total, :development_need_total, :balance_label)
        """), {
            "period_id": period_id,
            "personnel_id": personnel_id,
            "evaluation_id": evaluation_id,
            "total_notes": int(summary.get("total_notes") or 0),
            "positive_total": int(summary.get("positive_total") or 0),
            "negative_total": int(summary.get("negative_total") or 0),
            "development_need_total": int(summary.get("development_need_total") or 0),
            "balance_label": str(summary.get("balance_label") or ""),
        })
        db_session.commit()
        return True
    except Exception:
        try:
            db_session.rollback()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai_decision/interim_feedback_integration.py")
        return False
