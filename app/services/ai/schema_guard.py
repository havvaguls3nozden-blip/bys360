from __future__ import annotations

from typing import Any

from flask import current_app
from sqlalchemy import inspect

from app.extensions import db

AI_EXPECTED_SCHEMA: dict[str, set[str]] = {
    "ai_request_logs": {
        "module_type",
        "feature_type",
        "target_table",
        "target_id",
        "user_id",
        "request_text",
        "response_text",
        "provider_name",
        "model_name",
        "prompt_version",
        "status",
        "latency_ms",
        "token_in",
        "token_out",
        "was_masked",
        "was_user_visible",
        "error_message",
        "created_at",
        "updated_at",
    },
    "ai_recommendations": {
        "module_type",
        "target_table",
        "target_id",
        "recommendation_type",
        "title",
        "body",
        "severity",
        "status",
        "ai_request_log_id",
        "reviewed_by_user_id",
        "reviewed_at",
        "created_by_id",
        "updated_by_id",
        "created_at",
        "updated_at",
    },
    "ai_feedback_logs": {
        "ai_request_log_id",
        "user_id",
        "feedback_type",
        "feedback_note",
        "created_at",
        "updated_at",
    },
    "ai_redaction_rules": {
        "module_type",
        "field_name",
        "redaction_type",
        "replacement_text",
        "is_active",
        "created_by_id",
        "updated_by_id",
        "created_at",
        "updated_at",
    },
    "ai_summary_cache": {
        "module_type",
        "target_table",
        "target_id",
        "summary_kind",
        "summary_text",
        "source_hash",
        "expires_at",
        "created_at",
        "updated_at",
    },
}


def get_ai_schema_status() -> dict[str, Any]:
    cached_errors = list(current_app.extensions.get("schema_check_errors") or [])
    ai_table_names = tuple(AI_EXPECTED_SCHEMA.keys())
    ai_errors = [message for message in cached_errors if any(table_name in str(message) for table_name in ai_table_names)]

    status: dict[str, Any] = {
        "ready": True,
        "error_count": 0,
        "missing_tables": [],
        "missing_columns": [],
        "errors": [],
        "message": "AI şema hazırlığı tamam görünüyor.",
        "migration_hint": "flask --app run.py db upgrade",
        "auto_repair_hint": "AUTO_REPAIR_SCHEMA=true ile tek açılışlık güvenli onarım denenebilir.",
    }

    if ai_errors:
        missing_tables = sorted({str(message).split(": ", 1)[1] for message in ai_errors if str(message).startswith("Tablo eksik: ")})
        missing_columns = sorted({str(message).split(": ", 1)[1] for message in ai_errors if str(message).startswith("Kolon eksik: ")})
        status.update(
            {
                "ready": False,
                "error_count": len(ai_errors),
                "missing_tables": missing_tables,
                "missing_columns": missing_columns,
                "errors": ai_errors,
                "message": "AI yönetim tabloları eksik veya kısmi görünüyor. Önce migration / şema onarımı tamamlanmalı.",
            }
        )
        return status

    try:
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        missing_tables: list[str] = []
        missing_columns: list[str] = []
        for table_name, expected_columns in AI_EXPECTED_SCHEMA.items():
            if table_name not in existing_tables:
                missing_tables.append(table_name)
                continue
            column_names = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name in sorted(expected_columns - column_names):
                missing_columns.append(f"{table_name}.{column_name}")
        if missing_tables or missing_columns:
            status.update(
                {
                    "ready": False,
                    "error_count": len(missing_tables) + len(missing_columns),
                    "missing_tables": missing_tables,
                    "missing_columns": missing_columns,
                    "errors": [*[f"Tablo eksik: {name}" for name in missing_tables], *[f"Kolon eksik: {name}" for name in missing_columns]],
                    "message": "AI şema kontrolünde eksik tablo/kolon bulundu. AI ekranları korumalı modda çalıştırılıyor.",
                }
            )
    except Exception as exc:  # pragma: no cover
        try:
            db.session.rollback()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/schema_guard.py")
        status.update(
            {
                "ready": False,
                "error_count": 1,
                "errors": [str(exc)],
                "message": "AI şema durumu okunurken veritabanı hatası oluştu. AI ekranları korumalı moda alındı.",
            }
        )
    return status


def ai_schema_ready() -> bool:
    return bool(get_ai_schema_status().get("ready"))