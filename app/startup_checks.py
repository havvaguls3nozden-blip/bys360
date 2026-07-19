
"""BYS360 startup ve schema guard yardimcilari.

Maintenance Faz 2.4 kapsaminda app/__init__.py icindeki baslangic on kosullari
ve schema guard akisi daha okunur bir modüle tasinir. Davranis degismez;
mevcut log metinleri ve production/staging korumalari korunur.
"""
from __future__ import annotations

from pathlib import Path
from collections.abc import Callable
import os
import sys

from flask import Flask

from app.extensions import db
from app.schema_guard import repair_runtime_schema, should_auto_repair_schema

SchemaValidator = Callable[[Flask], None]


def is_schema_migration_command() -> bool:
    """Alembic/Flask migration komutlarinda boot-time schema kontrolunu atla."""
    env_flag = (os.getenv("FLASK_SKIP_SCHEMA_VALIDATION") or "").strip().lower()
    if env_flag in {"1", "true", "yes", "on"}:
        return True

    argv = " ".join(sys.argv).strip().lower()
    if not argv:
        return False

    migration_markers = (
        " flask db ",
        "alembic ",
        " db upgrade",
        " db downgrade",
        " db stamp",
        " db migrate",
        " db revision",
        " db check",
        " db heads",
        " db current",
        " db history",
    )
    argv_padded = f" {argv} "
    return any(marker in argv_padded for marker in migration_markers)


def should_run_schema_validation_on_boot(app: Flask) -> bool:
    """Boot sirasinda schema dogrulamasi calismali mi?"""
    if is_schema_migration_command():
        app.logger.info("Schema validation boot sırasında pas geçildi: migration komutu algılandı.")
        return False

    if app.config.get("TESTING"):
        app.logger.info("Schema validation test modunda pas geçildi.")
        return False

    dialect_name = (getattr(getattr(db.engine, "dialect", None), "name", "") or "").lower()
    if dialect_name == "sqlite":
        app.logger.info("Schema validation SQLite duman/test ortamında pas geçildi.")
        return False

    return True


def validate_runtime_prerequisites(app: Flask) -> None:
    """Uygulama acilisindan once temel ortam kosullarini dogrula."""
    dotenv_path = Path(app.config.get("DOTENV_PATH") or ".env")
    require_dotenv = bool(app.config.get("REQUIRE_DOTENV_FILE", False))
    strict_env_validation = bool(app.config.get("STRICT_ENV_VALIDATION", False))

    runtime_errors: list[str] = []

    if require_dotenv and not dotenv_path.exists():
        runtime_errors.append(f".env dosyasi bulunamadi: {dotenv_path}")

    database_uri = (app.config.get("SQLALCHEMY_DATABASE_URI") or "").strip()
    if strict_env_validation and (not database_uri or "CHANGE_ME" in database_uri or database_uri == "sqlite:///:memory:"):
        runtime_errors.append("DATABASE_URL tanimli degil ya da guvensiz varsayilan deger kullaniyor.")

    if runtime_errors:
        raise RuntimeError("Runtime preflight basarisiz: " + " | ".join(runtime_errors))


def run_schema_guard_bootstrap(app: Flask, validate_required_schema: SchemaValidator) -> None:
    """Mevcut schema guard boot akisini app factory disina al."""
    if should_run_schema_validation_on_boot(app):
        auto_repair_schema = bool(app.config.get("AUTO_REPAIR_SCHEMA", False))
        if auto_repair_schema and should_auto_repair_schema():
            if app.config.get("APP_ENV") in {"production", "staging"}:
                app.logger.warning("AUTO_REPAIR_SCHEMA acik. Canli ortamda migration sonrasi gecici kullanim disinda onerilmez.")
            repair_runtime_schema(app)
        else:
            app.logger.info("Schema guard DDL modu pas gecildi. Beklenen akis: once migration, sonra uygulama acilisi.")
        validate_required_schema(app)
    else:
        app.extensions["schema_check_errors"] = []


__all__ = [
    "is_schema_migration_command",
    "should_run_schema_validation_on_boot",
    "validate_runtime_prerequisites",
    "run_schema_guard_bootstrap",
]
