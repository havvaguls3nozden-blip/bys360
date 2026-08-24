from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "10858a18e9ac_adopt_file_center_schema_into_alembic_.py"
)

FILE_CENTER_TABLES = {
    "file_storage_folders",
    "file_storage_items",
    "file_transfers",
    "file_transfer_items",
    "file_transfer_recipients",
    "file_share_links",
    "file_requests",
    "file_request_uploads",
    "file_download_logs",
    "file_access_logs",
    "file_quota_usage",
    "file_security_scans",
    "file_audit_logs",
    "file_quota_policies",
    "file_upload_sessions",
    "file_upload_chunks",
    "file_center_mail_logs",
    "file_center_role_permissions",
    "file_center_settings",
}


def _load_migration() -> Any:
    # op/upgrade/downgrade are dynamically defined by whichever versions/*.py
    # file is loaded, and `op` is reassigned below before each call -- no
    # fixed static contract to type against (matches the established pattern
    # in tests/migrations/test_phase60b_development_recommendations_adoption_migration.py).
    spec = importlib.util.spec_from_file_location("file_center_schema_adoption", MIGRATION_PATH)
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


def _expected_columns(module: Any) -> dict[str, set[str]]:
    return {name: cols for name, _create_fn, cols, _pk in module._TABLES}


def test_creates_all_19_tables_on_empty_database() -> None:
    """Fresh-database scenario: none of the 19 File Center tables exist yet.
    The migration must create every one of them with the exact column set
    app/models/file_center_models.py declares."""
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection_op = Operations(MigrationContext.configure(connection))
        module.op = connection_op
        module.upgrade()

        existing_tables = set(sa.inspect(connection).get_table_names())
        missing_tables = FILE_CENTER_TABLES - existing_tables
        assert not missing_tables, f"Tables not created: {sorted(missing_tables)}"
        assert existing_tables >= FILE_CENTER_TABLES

        expected = _expected_columns(module)
        for table_name, expected_cols in expected.items():
            actual_cols = _column_names(connection, table_name)
            assert actual_cols == expected_cols, (
                f"{table_name}: column mismatch. "
                f"missing={expected_cols - actual_cols} extra={actual_cols - expected_cols}"
            )


def test_table_count_is_exactly_19_not_15() -> None:
    """Regression guard for a real miscount made earlier this session (an
    agent report and, transitively, the canonical handover docs, stated
    File Center had 15 tables -- direct grep of __tablename__ occurrences in
    app/models/file_center_models.py shows 19). This migration's own table
    list is the ground truth for what actually gets created."""
    module = _load_migration()
    assert len(module._TABLES) == 19
    assert {name for name, *_ in module._TABLES} == FILE_CENTER_TABLES


def _create_legacy_bootstrapped_schema(connection: sa.Connection) -> None:
    """Mirrors what the archived scripts/archive/pre_handover_20260708/local/
    create_file_center_tables_local_v1.py db.create_all() bootstrap would
    have produced: every File Center table, correctly shaped, already
    present before Alembic ever knew about them."""
    module = _load_migration()
    for _table_name, create_fn, _cols, _pk in module._TABLES:
        module.op = Operations(MigrationContext.configure(connection))
        create_fn()


def test_adopts_preexisting_legacy_schema_without_losing_data() -> None:
    """Legacy/live-style database scenario: all 19 tables already exist
    (simulating the historical bootstrap), one of them holds a real row.
    The migration must adopt them -- no drop, no recreate, no duplicate
    tables, and the pre-existing row must survive byte-for-byte."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_legacy_bootstrapped_schema(connection)

        connection.execute(
            sa.text(
                """
                INSERT INTO file_storage_items
                    (id, owner_user_id, original_filename, stored_filename, storage_path,
                     content_type, extension, size_bytes, sha256_hash, status, scan_status,
                     is_deleted, created_at, updated_at)
                VALUES
                    (1, 42, 'preexisting_legacy_file.pdf', 'legacy_stored_123.pdf',
                     '/fake/legacy/path/legacy_stored_123.pdf', 'application/pdf', '.pdf',
                     12345, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                     'ready', 'clean', 0, '2026-01-01 00:00:00', '2026-01-01 00:00:00')
                """
            )
        )

        tables_before = set(sa.inspect(connection).get_table_names())
        file_center_tables_before = {t for t in tables_before if t in FILE_CENTER_TABLES}
        assert len(file_center_tables_before) == 19

        _run_upgrade(connection)

        tables_after = set(sa.inspect(connection).get_table_names())
        file_center_tables_after = {t for t in tables_after if t in FILE_CENTER_TABLES}
        assert file_center_tables_after == file_center_tables_before, (
            "File Center table set changed across adoption -- must be identical "
            "(no table dropped, none duplicated under a different name)."
        )
        assert len(file_center_tables_after) == 19

        row = connection.execute(
            sa.text(
                """
                SELECT owner_user_id, original_filename, stored_filename, sha256_hash, size_bytes
                FROM file_storage_items WHERE id = 1
                """
            )
        ).mappings().one()
        assert dict(row) == {
            "owner_user_id": 42,
            "original_filename": "preexisting_legacy_file.pdf",
            "stored_filename": "legacy_stored_123.pdf",
            "sha256_hash": "a" * 64,
            "size_bytes": 12345,
        }


def test_upgrade_is_idempotent_on_already_adopted_schema() -> None:
    """Running the migration a second time against a database it already
    adopted must not error, duplicate tables, or lose data -- mirrors
    test_phase60b's idempotency check for the same reason: Alembic itself
    prevents replaying an already-applied revision in normal operation, but
    the upgrade() function's own logic should not silently assume it is
    only ever called once."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        _run_upgrade(connection)

        existing_tables = set(sa.inspect(connection).get_table_names())
        assert existing_tables >= FILE_CENTER_TABLES
        file_center_tables = {t for t in existing_tables if t in FILE_CENTER_TABLES}
        assert len(file_center_tables) == 19


def test_downgrade_is_non_destructive() -> None:
    """Downgrade must be a no-op: File Center tables can hold real
    institutional data (uploaded-file metadata, active guest links, audit
    logs), and this project's own established convention for adopted tables
    (migrations/versions/29fee38a97e1) is a non-destructive no-op downgrade,
    not a DROP TABLE."""
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        connection.execute(
            sa.text(
                """
                INSERT INTO file_center_settings (id, key, value_type, group_key, label,
                                                    is_active, created_at, updated_at)
                VALUES (1, 'storage_root_note', 'string', 'general', 'Test',
                        1, '2026-01-01 00:00:00', '2026-01-01 00:00:00')
                """
            )
        )

        _run_downgrade(connection)

        existing_tables = set(sa.inspect(connection).get_table_names())
        assert existing_tables >= FILE_CENTER_TABLES, "Downgrade must not drop any File Center table."
        value = connection.execute(
            sa.text("SELECT key FROM file_center_settings WHERE id = 1")
        ).scalar_one()
        assert value == "storage_root_note"


def test_negative_schema_mismatch_fails_closed() -> None:
    """A pre-existing table with a missing required column (here:
    file_share_links without token_hash, the column guest-link lookup
    security depends on) must make the migration FAIL, not silently adopt
    a table the application cannot use correctly. This is the deliberate
    behavioral difference from this project's 29fee38a97e1 precedent (which
    only logs a warning): File Center is a much larger, guest-facing
    surface, so a schema drift here should stop the deploy, not degrade
    silently at request time."""
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        for table_name, create_fn, _cols, _pk in module._TABLES:
            if table_name == "file_share_links":
                continue
            module.op = Operations(MigrationContext.configure(connection))
            create_fn()

        # Intentionally broken: missing token_hash (and other columns) --
        # exactly the kind of drift a corrupted/partial legacy bootstrap
        # could leave behind.
        connection.execute(
            sa.text(
                """
                CREATE TABLE file_share_links (
                    id INTEGER PRIMARY KEY,
                    file_id INTEGER NOT NULL,
                    password_hash VARCHAR(255),
                    expires_at DATETIME NOT NULL,
                    max_downloads INTEGER NOT NULL DEFAULT 5,
                    download_count INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_by_user_id INTEGER NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )

        # Deliberately reuse this same `module` object (not the generic
        # _run_upgrade() helper, which loads its own fresh module instance
        # internally) -- pytest.raises() checks exception *class identity*,
        # and a second importlib exec of the same file produces a
        # structurally-identical but distinct SchemaAdoptionError class.
        module.op = Operations(MigrationContext.configure(connection))
        with pytest.raises(module.SchemaAdoptionError, match="token_hash"):
            module.upgrade()

        # No partial mutation: the other 18 tables are untouched, and the
        # broken table was not silently patched.
        existing_tables = set(sa.inspect(connection).get_table_names())
        assert len(existing_tables & FILE_CENTER_TABLES) == 19
        assert "token_hash" not in _column_names(connection, "file_share_links")


def test_negative_schema_mismatch_wrong_primary_key_fails_closed() -> None:
    """A pre-existing table whose primary key does not match the model
    (here: file_center_settings with no primary key declared at all) must
    also fail closed."""
    module = _load_migration()
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        for table_name, create_fn, _cols, _pk in module._TABLES:
            if table_name == "file_center_settings":
                continue
            module.op = Operations(MigrationContext.configure(connection))
            create_fn()

        connection.execute(
            sa.text(
                """
                CREATE TABLE file_center_settings (
                    id INTEGER,
                    key VARCHAR(120) NOT NULL,
                    value TEXT,
                    value_type VARCHAR(40) NOT NULL DEFAULT 'string',
                    group_key VARCHAR(80) NOT NULL DEFAULT 'general',
                    label VARCHAR(255) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    updated_by_user_id INTEGER,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )

        module.op = Operations(MigrationContext.configure(connection))
        with pytest.raises(module.SchemaAdoptionError, match="primary key"):
            module.upgrade()
