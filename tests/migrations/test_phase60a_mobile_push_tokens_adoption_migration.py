from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "b704bd9d68c0_adopt_mobile_push_tokens_table_into_.py"
)

REQUIRED_COLUMNS = {
    "id",
    "user_id",
    "token",
    "platform",
    "device_id",
    "app_version",
    "device_label",
    "is_active",
    "last_seen_at",
    "created_at",
    "updated_at",
}


def _load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("phase60a_mobile_push_tokens_adoption", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_upgrade(connection: sa.Connection) -> None:
    module = _load_migration()
    module.op = Operations(MigrationContext.configure(connection))
    module.upgrade()


def _run_downgrade(connection: sa.Connection) -> None:
    module = _load_migration()
    module.op = Operations(MigrationContext.configure(connection))
    module.downgrade()


def _column_names(connection: sa.Connection, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(connection).get_columns(table_name)}


def _indexes_by_name(connection: sa.Connection, table_name: str) -> dict[str, dict]:
    return {index["name"]: index for index in sa.inspect(connection).get_indexes(table_name)}


def _create_legacy_self_healed_table(connection: sa.Connection) -> None:
    # Mirrors the exact SQLite DDL app/api/mobile/domains/push_notifications.py's
    # _ensure_mobile_push_token_table() runs at request time.
    connection.execute(
        sa.text(
            """
            CREATE TABLE mobile_push_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token VARCHAR(512) NOT NULL,
                platform VARCHAR(30),
                device_id VARCHAR(120),
                app_version VARCHAR(60),
                device_label VARCHAR(180),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def test_phase60a_creates_complete_schema_on_empty_database() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)

        assert "mobile_push_tokens" in sa.inspect(connection).get_table_names()
        assert _column_names(connection, "mobile_push_tokens") >= REQUIRED_COLUMNS

        indexes = _indexes_by_name(connection, "mobile_push_tokens")
        assert "ix_mobile_push_tokens_user_active" in indexes
        assert "ix_mobile_push_tokens_token" in indexes
        assert bool(indexes["ix_mobile_push_tokens_token"]["unique"]) is True


def test_phase60a_adopts_preexisting_self_healed_table_without_losing_rows() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_legacy_self_healed_table(connection)
        connection.execute(
            sa.text(
                """
                INSERT INTO mobile_push_tokens (id, user_id, token, platform)
                VALUES (1, 7, 'token-abc', 'android')
                """
            )
        )

        _run_upgrade(connection)

        row = connection.execute(
            sa.text("SELECT user_id, token, platform FROM mobile_push_tokens WHERE id = 1")
        ).mappings().one()
        assert dict(row) == {"user_id": 7, "token": "token-abc", "platform": "android"}

        indexes = _indexes_by_name(connection, "mobile_push_tokens")
        assert "ix_mobile_push_tokens_user_active" in indexes
        assert "ix_mobile_push_tokens_token" in indexes
        assert bool(indexes["ix_mobile_push_tokens_token"]["unique"]) is True


def test_phase60a_skips_unique_index_when_duplicate_tokens_exist() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_legacy_self_healed_table(connection)
        connection.execute(
            sa.text(
                """
                INSERT INTO mobile_push_tokens (id, user_id, token, platform)
                VALUES (1, 7, 'dup-token', 'android'), (2, 8, 'dup-token', 'ios')
                """
            )
        )

        _run_upgrade(connection)

        count = connection.execute(
            sa.text("SELECT COUNT(*) FROM mobile_push_tokens")
        ).scalar_one()
        assert count == 2

        indexes = _indexes_by_name(connection, "mobile_push_tokens")
        assert "ix_mobile_push_tokens_token" in indexes
        assert bool(indexes["ix_mobile_push_tokens_token"]["unique"]) is False
        assert "ix_mobile_push_tokens_user_active" in indexes


def test_phase60a_upgrade_is_idempotent() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        _run_upgrade(connection)

        assert "mobile_push_tokens" in sa.inspect(connection).get_table_names()
        assert _column_names(connection, "mobile_push_tokens") >= REQUIRED_COLUMNS


def test_phase60a_downgrade_is_non_destructive_for_adopted_table() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        connection.execute(
            sa.text(
                """
                INSERT INTO mobile_push_tokens (id, user_id, token, platform)
                VALUES (1, 7, 'Korunacak-token', 'android')
                """
            )
        )

        _run_downgrade(connection)

        assert "mobile_push_tokens" in sa.inspect(connection).get_table_names()
        token = connection.execute(
            sa.text("SELECT token FROM mobile_push_tokens WHERE id = 1")
        ).scalar_one()
        assert token == "Korunacak-token"
