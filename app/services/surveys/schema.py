"""Anket canlı şema uyumluluğu yardımcıları.

DB erişimi fonksiyon içinde ve savunmacı yapılır. Bu sayede modül import'u canlı
uygulama context'i gerektirmez.
"""
from __future__ import annotations

from functools import lru_cache
import logging
logger = logging.getLogger(__name__)


@lru_cache(maxsize=64)
def table_columns(table_name: str) -> frozenset[str]:
    try:
        from sqlalchemy import inspect as sa_inspect
        from app.extensions import db

        cols = {str(col.get("name") or "").strip() for col in sa_inspect(db.engine).get_columns(table_name)}
        return frozenset(col for col in cols if col)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/schema.py | line=21")
        return frozenset()


def has_table_columns(table_name: str, *columns: str) -> bool:
    available = table_columns(table_name)
    return all(column in available for column in columns)


def survey_response_phase2_ready() -> bool:
    return has_table_columns("survey_responses", "started_at", "last_saved_at", "progress_percent")


def survey_question_phase2_ready() -> bool:
    if not has_table_columns(
        "survey_questions",
        "helper_text",
        "logic_mode",
        "logic_source_question_id",
        "logic_operator",
        "logic_value",
    ):
        return False
    try:
        from app.models import SurveyQuestion

        mapped = set(getattr(SurveyQuestion, "__mapper__").attrs.keys())
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/schema.py | line=48")
        return False
    return {
        "helper_text",
        "logic_mode",
        "logic_source_question_id",
        "logic_operator",
        "logic_value",
    }.issubset(mapped)


def clear_schema_cache() -> None:
    table_columns.cache_clear()
