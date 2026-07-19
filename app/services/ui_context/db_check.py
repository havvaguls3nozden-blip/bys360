from __future__ import annotations

from typing import Any
from collections.abc import Iterable

from flask import current_app

from app.extensions import db
from app.models import (
    EvaluationAssignment,
    OrganizationUnit,
    PerformanceCriteria,
    PerformanceEvaluation,
    PerformanceEvaluationItem,
    PerformancePeriod,
    User,
)


TABLE_MODELS: dict[str, Any] = {
    "users": User,
    "organization_units": OrganizationUnit,
    "performance_periods": PerformancePeriod,
    "performance_criteria": PerformanceCriteria,
    "evaluation_assignments": EvaluationAssignment,
    "performance_evaluations": PerformanceEvaluation,
    "performance_evaluation_items": PerformanceEvaluationItem,
}

TABLE_LABELS: dict[str, str] = {
    "users": "Kullanıcılar",
    "organization_units": "Organizasyon Birimleri",
    "performance_periods": "Dönemler",
    "performance_criteria": "Kriterler",
    "evaluation_assignments": "Değerlendirme Görevleri",
    "performance_evaluations": "Değerlendirme Özetleri",
    "performance_evaluation_items": "Kriter Puan Satırları",
}


def _safe_model_count(model: Any) -> int:
    try:
        return int(db.session.query(model).count())
    except Exception as exc:
        current_app.logger.warning("DB kontrol sayımı başarısız. model=%s error=%s", getattr(model, "__name__", model), exc)
        try:
            db.session.rollback()
        except Exception as rollback_exc:
            current_app.logger.warning("DB kontrol rollback başarısız. model=%s error=%s", getattr(model, "__name__", model), rollback_exc)
        return 0


def _build_table_rows(table_counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in table_counts.items():
        count = int(value or 0)
        rows.append(
            {
                "key": key,
                "label": TABLE_LABELS.get(key, key.replace("_", " ").title()),
                "count": count,
                "is_populated": count > 0,
                "status_label": "Dolu" if count > 0 else "Boş",
                "status_tone": "success" if count > 0 else "muted",
            }
        )
    rows.sort(key=lambda row: (row["count"] == 0, row["label"].lower()))
    return rows


def build_db_check_context(schema_errors: Iterable[Any] | None) -> dict[str, Any]:
    rows = [str(item).strip() for item in (schema_errors or []) if str(item).strip()]
    table_counts = {key: _safe_model_count(model) for key, model in TABLE_MODELS.items()}
    table_rows = _build_table_rows(table_counts)
    db_result = "Bağlantı başarılı"
    db_result_tone = "success" if not rows else "warning"
    if not any(table_counts.values()):
        db_result = "Bağlantı var, tablolar boş veya erişim kısıtlı"
        if not rows:
            db_result_tone = "warning"

    total_records = sum(int(value or 0) for value in table_counts.values())
    populated_table_count = sum(1 for value in table_counts.values() if int(value or 0) > 0)
    empty_table_count = max(len(table_counts) - populated_table_count, 0)
    table_health_ratio = round((populated_table_count / max(len(table_counts), 1)) * 100, 1)

    return {
        "db_result": db_result,
        "db_result_tone": db_result_tone,
        "schema_errors": rows,
        "schema_check_errors": rows,
        "schema_check_error_count": len(rows),
        "table_counts": table_counts,
        "table_count_map": table_counts,
        "table_rows": table_rows,
        "non_empty_table_rows": [row for row in table_rows if row["is_populated"]],
        "empty_table_rows": [row for row in table_rows if not row["is_populated"]],
        "total_records": total_records,
        "populated_table_count": populated_table_count,
        "empty_table_count": empty_table_count,
        "table_health_ratio": table_health_ratio,
        "health_summary": {
            "table_total": len(table_rows),
            "table_health_ratio": table_health_ratio,
            "schema_error_count": len(rows),
            "is_schema_clean": len(rows) == 0,
        },
    }