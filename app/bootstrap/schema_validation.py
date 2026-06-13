from __future__ import annotations



from collections.abc import Mapping, Set as AbstractSet

from flask import Flask
from sqlalchemy import inspect

from app.extensions import db


def validate_required_schema(app: Flask, expected_schema: Mapping[str, AbstractSet[str]]) -> None:
    """Canli omurga icin beklenen tablo/kolon sozlesmesini dogrular."""
    errors: list[str] = []
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for table_name, expected_columns in expected_schema.items():
        if table_name not in existing_tables:
            errors.append(f"Tablo eksik: {table_name}")
            continue

        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing_columns = sorted(set(expected_columns) - existing_columns)
        errors.extend(f"Kolon eksik: {table_name}.{column_name}" for column_name in missing_columns)

    app.extensions["schema_check_errors"] = errors

    if not errors:
        app.logger.info("Şema doğrulaması temiz geçti. Bu güzel haber.")
        return

    for error_message in errors:
        app.logger.error("Şema kontrol notu: %s", error_message)

    if app.config.get("STRICT_SCHEMA_CHECK", False):
        raise RuntimeError("Şema doğrulama başarısız: " + " | ".join(errors))
