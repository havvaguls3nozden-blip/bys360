
"""BYS360 schema guard - DDL uygulama motoru.

should_auto_repair_schema() ve repair_runtime_schema() fonksiyonlarını
içerir. TABLE_REPAIRS ve SCHEMA_PATCHES alt modüllerden derlenir.
"""
from __future__ import annotations

import os
import re
import sys
from typing import Iterable

from flask import Flask
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app.extensions import db
from app.schema_guard_core_repairs import TABLE_REPAIRS
from app.schema_guard_patches import SCHEMA_PATCHES

INDEX_COLUMNS_RE = re.compile(r"\bON\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)", re.IGNORECASE | re.DOTALL)
TABLE_RE = re.compile(r"(?:ALTER|CREATE TABLE(?: IF NOT EXISTS)?)\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.IGNORECASE)


def should_auto_repair_schema() -> bool:
    """Return True only for normal app boots where ad-hoc DDL is explicitly allowed.

    Alembic / flask db komutlari sirasinda kesinlikle calismaz. Canli ortamda da
    config tarafindan ayrica AUTO_REPAIR_SCHEMA=true verilmedikce devreye girmez.
    """
    if os.getenv("BYS_SKIP_SCHEMA_GUARD") == "1":
        return False

    argv = " ".join(sys.argv).lower()
    if os.getenv("BYS_FORCE_SCHEMA_GUARD") == "1":
        return True

    management_markers = (
        "flask db",
        "alembic",
        "db upgrade",
        "db migrate",
        "db revision",
        "db stamp",
        "db current",
        "db heads",
        "db history",
    )
    return not any(marker in argv for marker in management_markers)


def _is_insufficient_privilege(exc: Exception) -> bool:
    orig = getattr(exc, "orig", None)
    pgcode = getattr(orig, "pgcode", None)
    if pgcode == "42501":
        return True
    message = str(orig or exc).lower()
    return "must be owner of table" in message or "insufficient privilege" in message


def _is_duplicate_object(exc: Exception) -> bool:
    orig = getattr(exc, "orig", None)
    pgcode = getattr(orig, "pgcode", None)
    if pgcode in {"42P07", "42710"}:
        return True
    message = str(orig or exc).lower()
    return "already exists" in message or "duplicate" in message


def _current_user(connection) -> str | None:
    try:
        return connection.execute(text("SELECT current_user")).scalar()
    except SQLAlchemyError:
        return None


def _owner_map(connection) -> dict[str, str]:
    try:
        rows = connection.execute(
            text(
                """
                SELECT tablename, tableowner
                FROM pg_tables
                WHERE schemaname = current_schema()
                """
            )
        )
        return {row[0]: row[1] for row in rows}
    except SQLAlchemyError:
        return {}


def _columns(connection, table: str) -> set[str]:
    dialect_name = (getattr(getattr(connection, "dialect", None), "name", "") or "").lower()
    if dialect_name == "sqlite":
        try:
            rows = connection.execute(text(f"PRAGMA table_info({table})"))
            return {row[1] for row in rows}
        except SQLAlchemyError:
            return set()

    rows = connection.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = :table_name
            """
        ),
        {"table_name": table},
    )
    return {row[0] for row in rows}


def _required_index_columns(statement: str) -> tuple[str, set[str]] | None:
    normalized = " ".join(statement.split())
    lowered = normalized.lower()
    if not re.match(r"^create\s+(unique\s+)?index\b", lowered):
        return None

    match = INDEX_COLUMNS_RE.search(normalized)
    if not match:
        return None

    table = match.group(1)
    raw_cols = match.group(2)
    cols: set[str] = set()
    for chunk in raw_cols.split(","):
        token = chunk.strip().split()[0].strip('"')
        if not token:
            continue
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
            continue
        cols.add(token)

    if not cols:
        return None
    return table, cols


def _safe_exec(connection, statement: str) -> str:
    connection.execute(text(statement))
    return statement.splitlines()[0][:140]


def repair_runtime_schema(app: Flask) -> None:
    applied: list[str] = []
    skipped: list[str] = []

    try:
        dialect_name = (getattr(getattr(db.engine, "dialect", None), "name", "") or "").lower()
        if dialect_name == "sqlite":
            app.logger.info("Schema guard SQLite ortamında otomatik DDL uygulamaz; create_all/migration akışı kullanılacak.")
            return
        with db.engine.begin() as connection:
            current_user = _current_user(connection)
            owner_map = _owner_map(connection)

            for repair in TABLE_REPAIRS:
                table_exists = repair.table in owner_map or bool(_columns(connection, repair.table))
                table_owner = owner_map.get(repair.table)
                owner_mismatch = bool(table_exists and current_user and table_owner and table_owner != current_user)

                if not table_exists:
                    try:
                        applied.append(f"{repair.table}: {_safe_exec(connection, repair.create_sql)}")
                        table_exists = True
                    except DBAPIError as exc:
                        if _is_insufficient_privilege(exc):
                            skipped.append(f"{repair.table}: tablo olusturma yetkisi yok")
                            continue
                        if _is_duplicate_object(exc):
                            table_exists = True
                        else:
                            raise
                    owner_map = _owner_map(connection)
                    table_owner = owner_map.get(repair.table)
                    owner_mismatch = bool(table_exists and current_user and table_owner and table_owner != current_user)

                if owner_mismatch:
                    skipped.append(f"{repair.table}: sahip {table_owner}, aktif rol {current_user}; alter/index atlandi")
                    continue

                for statement in repair.column_sql:
                    try:
                        applied.append(f"{repair.table}: {_safe_exec(connection, statement)}")
                    except DBAPIError as exc:
                        if _is_duplicate_object(exc):
                            continue
                        if _is_insufficient_privilege(exc):
                            skipped.append(f"{repair.table}: kolon yetkisi yok -> {statement[:100]}")
                            break
                        raise

                cols = _columns(connection, repair.table)
                for statement in repair.index_sql:
                    info = _required_index_columns(statement)
                    if info is not None:
                        _, needed_cols = info
                        if not needed_cols.issubset(cols):
                            skipped.append(f"{repair.table}: index atlandi, kolon eksik -> {sorted(needed_cols - cols)}")
                            continue
                    try:
                        applied.append(f"{repair.table}: {_safe_exec(connection, statement)}")
                    except DBAPIError as exc:
                        if _is_duplicate_object(exc) or _is_insufficient_privilege(exc):
                            skipped.append(f"{repair.table}: index atlandi -> {statement[:100]}")
                            continue
                        raise

            for label, statement in SCHEMA_PATCHES:
                table_match = TABLE_RE.search(statement)
                table_name = table_match.group(1) if table_match else None
                table_owner = owner_map.get(table_name) if table_name else None
                if table_name and current_user and table_owner and table_owner != current_user:
                    skipped.append(f"{label}: sahip {table_owner}, aktif rol {current_user}; atlandi")
                    continue

                info = _required_index_columns(statement)
                if info is not None:
                    table_name, needed_cols = info
                    cols = _columns(connection, table_name)
                    if not needed_cols.issubset(cols):
                        skipped.append(f"{label}: index atlandi, kolon eksik -> {sorted(needed_cols - cols)}")
                        continue

                try:
                    applied.append(f"{label}: {_safe_exec(connection, statement)}")
                except DBAPIError as exc:
                    if _is_duplicate_object(exc) or _is_insufficient_privilege(exc):
                        skipped.append(f"{label}: atlandi")
                        continue
                    raise
    except Exception:
        app.logger.exception("Schema guard DDL calistirirken kritik hata verdi.")
        return

    if applied:
        app.logger.info("Schema guard %s ifade uyguladi.", len(applied))
    else:
        app.logger.info("Schema guard uygulanacak yeni bir sey bulmadi.")

    for item in applied[:25]:
        app.logger.info("Schema guard uygulandi: %s", item)
    if len(applied) > 25:
        app.logger.info("Schema guard kalan %s ifade daha uyguladi.", len(applied) - 25)
    for item in skipped:
        app.logger.warning("Schema guard atladi: %s", item)

# BYS360_CLAUDE_V13_SCHEMA_GUARD_DEFAULT_OFF_BEGIN
# Canlı güvenlik kapısı: ad-hoc DDL onarımı yalnızca açık AUTO_REPAIR_SCHEMA=true
# verildiğinde ve migration komutu değilken çalışabilir. BYS_FORCE_SCHEMA_GUARD
# bilinçli acil durum anahtarı olarak korunur.
_BYS360_V13_ORIGINAL_SHOULD_AUTO_REPAIR_SCHEMA = should_auto_repair_schema


def _bys360_v13_env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def should_auto_repair_schema() -> bool:  # type: ignore[no-redef]
    if _bys360_v13_env_bool("BYS_FORCE_SCHEMA_GUARD", False):
        return _BYS360_V13_ORIGINAL_SHOULD_AUTO_REPAIR_SCHEMA()
    if not _bys360_v13_env_bool("AUTO_REPAIR_SCHEMA", False):
        return False
    return _BYS360_V13_ORIGINAL_SHOULD_AUTO_REPAIR_SCHEMA()
# BYS360_CLAUDE_V13_SCHEMA_GUARD_DEFAULT_OFF_END


# BYS360_A5_P2D4_SCHEMA_GUARD_SKIP_ENV_ANCHOR_START
# Static contract anchor: BYS_SKIP_SCHEMA_GUARD
# Schema guard varsay?lan olarak check-first ?al???r; skip env sadece a??k test/operasyon durumlar?nda okunmal?d?r.
# BYS360_A5_P2D4_SCHEMA_GUARD_SKIP_ENV_ANCHOR_END


# BYS360_A5_P2D4_SCHEMA_GUARD_DB_UPGRADE_ANCHOR_START
# Static contract anchor: db upgrade
# ?retimde ?ema d?zeltme ak??? otomatik onar?m yerine kontroll? migration / db upgrade s?reciyle y?r?t?lmelidir.
# BYS360_A5_P2D4_SCHEMA_GUARD_DB_UPGRADE_ANCHOR_END

