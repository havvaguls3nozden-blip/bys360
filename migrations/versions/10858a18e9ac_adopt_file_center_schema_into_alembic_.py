"""Adopt File Center schema into Alembic migrations.

Revision ID: 10858a18e9ac
Revises: e0efcd07abf7
Create Date: 2026-08-24 22:45:29.120615

BYS360's File Center ("Dosya Merkezi", app/file_center/{routes,services,
mail_service,settings_service,maintenance_service,permissions}.py) has 19
tables (app/models/file_center_models.py, confirmed by direct count of
``__tablename__`` occurrences -- an earlier handover-documentation pass had
mis-stated this as 15; that count is corrected here, since a migration
touching all of them is the moment that number has to actually be right).
None of the 19 tables were ever created by a normal Alembic migration.
Historically they were bootstrapped once via an archived, one-off script
(scripts/archive/pre_handover_20260708/local/create_file_center_tables_local_v1.py,
a plain ``db.create_all()`` call scoped to the File Center model imports).
A fresh environment relying solely on ``flask db upgrade`` would not get
these tables -- this migration closes that transferability gap.

Two real-world starting states have to be handled safely by the SAME
migration, since this repository's Alembic history has no reliable way to
know in advance which one a given target database is in:

  A) Fresh database: none of the 19 tables exist. This migration creates
     all of them with the exact schema app/models/file_center_models.py
     declares (columns, types, nullability, defaults, primary keys, foreign
     keys, and the handful of unique/indexed columns the application
     depends on for correctness -- token_hash uniqueness on guest links and
     requests, session_token uniqueness on chunk-upload sessions, etc.).

  B) Legacy/live-style database: the tables already exist (created by the
     archived bootstrap script at some point in the past, exactly as
     production is). This migration must ADOPT them into Alembic ownership
     without touching a single row, without dropping and recreating
     anything, and without silently accepting a table whose shape doesn't
     actually match what the application code reads and writes.

Compatibility contract for the adopt path (mirrors the project's own
existing precedent, migrations/versions/29fee38a97e1_adopt_performance_
development_.py, which adopts a different self-healed table the same way):
for each existing table, this migration checks that every column name the
model expects is present, and that the primary key column matches. It does
NOT attempt byte-for-byte type/length/constraint equality -- SQLite and
PostgreSQL reflect column types differently (e.g. SQLite has no native
VARCHAR(n) length enforcement, and unique-constraint reflection on SQLite
does not reliably expose a queryable name for constraints created via bare
``UNIQUE`` column modifiers), so a stricter check would be fragile and
prone to false failures on a database that is, in every way the
application actually cares about, compatible. Column-name-set-plus-primary-
key is the same minimum compatibility contract the 29fee38a97e1 precedent
already established for this project; this migration follows it rather
than inventing a new, unproven policy. Unlike that precedent (which only
logs a warning on a mismatch), THIS migration treats a missing required
column or a wrong primary key as a hard failure: File Center is a much
larger surface (19 tables, guest-facing token/password auth, real file
data) than a single internally-consumed recommendations table, and a
silently-adopted, subtly-broken table would fail in confusing ways at
request time instead of at migration time. See SchemaAdoptionError below.

Downgrade policy: intentionally a no-op for every table, matching this
project's own established convention for adopted, potentially data-bearing
tables (see 29fee38a97e1's downgrade docstring for the identical
reasoning). File Center tables can hold real uploaded-file metadata,
active guest share links, and audit/download logs; a destructive downgrade
that dropped them could erase institutional data with no way back. This is
not a special policy invented for this migration -- it is the same policy
the project already uses.
"""
from __future__ import annotations

import logging

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "10858a18e9ac"
down_revision = "e0efcd07abf7"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


class SchemaAdoptionError(RuntimeError):
    """Raised when a pre-existing File Center table's schema does not meet
    this migration's minimum compatibility contract (missing required
    column, or wrong primary key). Fails the migration closed instead of
    silently adopting a table the application cannot actually use
    correctly."""


def _ts_columns() -> list[sa.Column]:
    """Fresh sa.Column instances for TimestampMixin's created_at/updated_at
    (app/models/base.py) -- Column objects cannot be reused across
    multiple op.create_table() calls, so this must return new ones each
    time. No server_default is set, matching the model exactly: the model
    only declares a Python-side default (default=utc_now), never a
    server_default, and every write path in this codebase goes through the
    SQLAlchemy ORM (which applies that Python-side default before issuing
    the INSERT) -- adding a server_default here would diverge from what
    db.create_all() actually produced historically."""
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    ]


def _table_exists(bind: sa.engine.Connection, table_name: str) -> bool:
    return table_name in sa.inspect(bind).get_table_names()


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _table_exists(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def _pk_columns(bind: sa.engine.Connection, table_name: str) -> set[str]:
    pk = sa.inspect(bind).get_pk_constraint(table_name)
    return set(pk.get("constrained_columns") or [])


def _adopt_or_create(
    bind: sa.engine.Connection,
    table_name: str,
    create_fn,
    expected_columns: set[str],
    expected_pk: set[str],
) -> None:
    if not _table_exists(bind, table_name):
        create_fn()
        logger.info("File Center adoption: created table '%s' (did not exist).", table_name)
        return

    existing_columns = _column_names(bind, table_name)
    missing = expected_columns - existing_columns
    if missing:
        raise SchemaAdoptionError(
            f"File Center schema adoption FAILED for existing table '{table_name}': "
            f"missing required column(s) {sorted(missing)}. This table already exists "
            f"(most likely created by the historical scripts/archive/pre_handover_20260708/"
            f"local/create_file_center_tables_local_v1.py db.create_all() bootstrap) but its "
            f"current schema does not match what app/models/file_center_models.py expects. "
            f"Refusing to silently adopt a table the application cannot use correctly -- "
            f"inspect and fix the table's schema (or restore from a known-good backup) and "
            f"re-run `flask db upgrade`."
        )

    existing_pk = _pk_columns(bind, table_name)
    if existing_pk != expected_pk:
        raise SchemaAdoptionError(
            f"File Center schema adoption FAILED for existing table '{table_name}': "
            f"primary key column(s) {sorted(existing_pk)} do not match the expected "
            f"{sorted(expected_pk)}."
        )

    logger.info(
        "File Center adoption: adopted pre-existing table '%s' into Alembic ownership "
        "(schema compatible with app/models/file_center_models.py, no changes made).",
        table_name,
    )


# ---------------------------------------------------------------------------
# Table creation functions -- one per model in app/models/file_center_models.py,
# in FK-dependency order (a table is only created after every table it
# references). Column shape (type/nullable/default/unique/index) mirrors the
# model file exactly.
# ---------------------------------------------------------------------------


def _create_file_storage_folders() -> None:
    op.create_table(
        "file_storage_folders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("file_storage_folders.id"), nullable=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_storage_items() -> None:
    op.create_table(
        "file_storage_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("folder_id", sa.Integer(), sa.ForeignKey("file_storage_folders.id"), nullable=True, index=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("stored_filename", sa.String(length=500), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("extension", sa.String(length=40), nullable=True, index=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False, index=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'ready'"), index=True),
        sa.Column("scan_status", sa.String(length=40), nullable=False, server_default=sa.text("'pending'"), index=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_transfers() -> None:
    op.create_table(
        "file_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'draft'"), index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True, index=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_transfer_items() -> None:
    op.create_table(
        "file_transfer_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("file_transfers.id"), nullable=False, index=True),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_storage_items.id"), nullable=False, index=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_transfer_recipients() -> None:
    op.create_table(
        "file_transfer_recipients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("file_transfers.id"), nullable=False, index=True),
        sa.Column("recipient_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("recipient_email", sa.String(length=255), nullable=True, index=True),
        sa.Column("recipient_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'pending'"), index=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_share_links() -> None:
    op.create_table(
        "file_share_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_storage_items.id"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column("public_token", sa.String(length=255), nullable=True, index=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("max_downloads", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true(), index=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("last_downloaded_at", sa.DateTime(), nullable=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_requests() -> None:
    op.create_table(
        "file_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("recipient_name", sa.String(length=255), nullable=True),
        sa.Column("recipient_email", sa.String(length=255), nullable=True, index=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column("public_token", sa.String(length=255), nullable=True, index=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("max_file_gb", sa.Float(), nullable=False, server_default=sa.text("5")),
        sa.Column("allowed_extensions", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'open'"), index=True),
        sa.Column("upload_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_upload_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_request_uploads() -> None:
    op.create_table(
        "file_request_uploads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("file_requests.id"), nullable=False, index=True),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_storage_items.id"), nullable=False, index=True),
        sa.Column("guest_name", sa.String(length=255), nullable=True),
        sa.Column("guest_email", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'uploaded'"), index=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_download_logs() -> None:
    op.create_table(
        "file_download_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_storage_items.id"), nullable=False, index=True),
        sa.Column("share_link_id", sa.Integer(), sa.ForeignKey("file_share_links.id"), nullable=True, index=True),
        sa.Column("downloaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("guest_label", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'success'"), index=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_access_logs() -> None:
    op.create_table(
        "file_access_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_storage_items.id"), nullable=True, index=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("action", sa.String(length=80), nullable=False, index=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_quota_usage() -> None:
    op.create_table(
        "file_quota_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True, index=True),
        sa.Column("used_bytes", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_security_scans() -> None:
    op.create_table(
        "file_security_scans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_storage_items.id"), nullable=False, index=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'pending'"), index=True),
        sa.Column("scanner", sa.String(length=120), nullable=True),
        sa.Column("result_message", sa.Text(), nullable=True),
        sa.Column("scanned_at", sa.DateTime(), nullable=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_audit_logs() -> None:
    op.create_table(
        "file_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("file_storage_items.id"), nullable=True, index=True),
        sa.Column("action", sa.String(length=80), nullable=False, index=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_quota_policies() -> None:
    op.create_table(
        "file_quota_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scope_type", sa.String(length=40), nullable=False, server_default=sa.text("'global'"), index=True),
        sa.Column("scope_value", sa.String(length=255), nullable=True, index=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("max_storage_gb", sa.Float(), nullable=False, server_default=sa.text("25")),
        sa.Column("max_single_file_gb", sa.Float(), nullable=False, server_default=sa.text("5")),
        sa.Column("max_transfer_gb", sa.Float(), nullable=False, server_default=sa.text("20")),
        sa.Column("warning_threshold_percent", sa.Integer(), nullable=False, server_default=sa.text("80")),
        sa.Column("hard_stop_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true(), index=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_upload_sessions() -> None:
    op.create_table(
        "file_upload_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("session_token", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("total_size_bytes", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("chunk_size_bytes", sa.Integer(), nullable=False, server_default=sa.text("10485760")),
        sa.Column("total_chunks", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("received_chunks", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("received_bytes", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("sha256_hash", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'prepared'"), index=True),
        sa.Column("temp_dir", sa.Text(), nullable=True),
        sa.Column("finalized_file_id", sa.Integer(), sa.ForeignKey("file_storage_items.id"), nullable=True, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True, index=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_upload_chunks() -> None:
    op.create_table(
        "file_upload_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("file_upload_sessions.id"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False, index=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("sha256_hash", sa.String(length=64), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'prepared'"), index=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_center_mail_logs() -> None:
    op.create_table(
        "file_center_mail_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("file_requests.id"), nullable=True, index=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("recipient_email", sa.String(length=255), nullable=False, index=True),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("purpose", sa.String(length=80), nullable=False, server_default=sa.text("'request_invitation'"), index=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'pending'"), index=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("smtp_host", sa.String(length=255), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_center_role_permissions() -> None:
    op.create_table(
        "file_center_role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role_key", sa.String(length=120), nullable=False, unique=True, index=True),
        sa.Column("role_label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("can_use", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_upload_files", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_download_files", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_create_guest_links", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_create_guest_upload_requests", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_view_transfers", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_view_requests", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_use_chunk_upload", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_view_logs", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_manage_security", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_manage_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_manage_maintenance", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_manage_settings", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_manage_quota_policy", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_manage_role_matrix", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true(), index=True),
        sa.Column("updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


def _create_file_center_settings() -> None:
    op.create_table(
        "file_center_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=120), nullable=False, unique=True, index=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("value_type", sa.String(length=40), nullable=False, server_default=sa.text("'string'")),
        sa.Column("group_key", sa.String(length=80), nullable=False, server_default=sa.text("'general'"), index=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true(), index=True),
        sa.Column("updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        *_ts_columns(),
        sqlite_autoincrement=True,
    )


# ---------------------------------------------------------------------------
# (table_name, create_fn, expected_columns, expected_pk) in dependency order.
# expected_columns mirrors each model class's real attribute set exactly
# (including created_at/updated_at from TimestampMixin).
# ---------------------------------------------------------------------------

_TABLES: list[tuple[str, object, set[str], set[str]]] = [
    (
        "file_storage_folders",
        _create_file_storage_folders,
        {"id", "owner_user_id", "parent_id", "name", "is_deleted", "created_at", "updated_at"},
        {"id"},
    ),
    (
        "file_storage_items",
        _create_file_storage_items,
        {
            "id", "owner_user_id", "folder_id", "original_filename", "stored_filename",
            "storage_path", "content_type", "extension", "size_bytes", "sha256_hash",
            "status", "scan_status", "is_deleted", "deleted_at", "deleted_by_user_id",
            "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_transfers",
        _create_file_transfers,
        {"id", "owner_user_id", "title", "message", "status", "expires_at", "created_at", "updated_at"},
        {"id"},
    ),
    (
        "file_transfer_items",
        _create_file_transfer_items,
        {"id", "transfer_id", "file_id", "created_at", "updated_at"},
        {"id"},
    ),
    (
        "file_transfer_recipients",
        _create_file_transfer_recipients,
        {
            "id", "transfer_id", "recipient_user_id", "recipient_email", "recipient_name",
            "status", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_share_links",
        _create_file_share_links,
        {
            "id", "file_id", "token_hash", "public_token", "password_hash", "expires_at",
            "max_downloads", "download_count", "is_active", "created_by_user_id",
            "revoked_at", "revoked_by_user_id", "last_downloaded_at", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_requests",
        _create_file_requests,
        {
            "id", "owner_user_id", "title", "description", "recipient_name", "recipient_email",
            "token_hash", "public_token", "password_hash", "expires_at", "max_file_gb",
            "allowed_extensions", "status", "upload_count", "last_upload_at", "closed_at",
            "revoked_at", "revoked_by_user_id", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_request_uploads",
        _create_file_request_uploads,
        {
            "id", "request_id", "file_id", "guest_name", "guest_email", "ip_address",
            "user_agent", "status", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_download_logs",
        _create_file_download_logs,
        {
            "id", "file_id", "share_link_id", "downloaded_by_user_id", "guest_label",
            "ip_address", "user_agent", "status", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_access_logs",
        _create_file_access_logs,
        {
            "id", "file_id", "actor_user_id", "action", "ip_address", "user_agent",
            "detail", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_quota_usage",
        _create_file_quota_usage,
        {"id", "user_id", "used_bytes", "file_count", "created_at", "updated_at"},
        {"id"},
    ),
    (
        "file_security_scans",
        _create_file_security_scans,
        {
            "id", "file_id", "status", "scanner", "result_message", "scanned_at",
            "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_audit_logs",
        _create_file_audit_logs,
        {
            "id", "actor_user_id", "file_id", "action", "message", "ip_address",
            "user_agent", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_quota_policies",
        _create_file_quota_policies,
        {
            "id", "scope_type", "scope_value", "label", "max_storage_gb", "max_single_file_gb",
            "max_transfer_gb", "warning_threshold_percent", "hard_stop_enabled", "is_active",
            "created_by_user_id", "notes", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_upload_sessions",
        _create_file_upload_sessions,
        {
            "id", "owner_user_id", "session_token", "original_filename", "total_size_bytes",
            "chunk_size_bytes", "total_chunks", "received_chunks", "received_bytes",
            "sha256_hash", "status", "temp_dir", "finalized_file_id", "expires_at",
            "cancelled_at", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_upload_chunks",
        _create_file_upload_chunks,
        {
            "id", "session_id", "chunk_index", "size_bytes", "sha256_hash", "storage_path",
            "status", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_center_mail_logs",
        _create_file_center_mail_logs,
        {
            "id", "request_id", "actor_user_id", "recipient_email", "subject", "body",
            "purpose", "status", "error_message", "smtp_host", "sent_at", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_center_role_permissions",
        _create_file_center_role_permissions,
        {
            "id", "role_key", "role_label", "description", "can_use", "can_upload_files",
            "can_download_files", "can_create_guest_links", "can_create_guest_upload_requests",
            "can_view_transfers", "can_view_requests", "can_use_chunk_upload", "can_view_logs",
            "can_manage_security", "can_manage_admin", "can_manage_maintenance",
            "can_manage_settings", "can_manage_quota_policy", "can_manage_role_matrix",
            "is_active", "updated_by_user_id", "created_at", "updated_at",
        },
        {"id"},
    ),
    (
        "file_center_settings",
        _create_file_center_settings,
        {
            "id", "key", "value", "value_type", "group_key", "label", "description",
            "is_active", "updated_by_user_id", "created_at", "updated_at",
        },
        {"id"},
    ),
]


def upgrade() -> None:
    bind = op.get_bind()
    for table_name, create_fn, expected_columns, expected_pk in _TABLES:
        _adopt_or_create(bind, table_name, create_fn, expected_columns, expected_pk)


def downgrade() -> None:
    """Intentional no-op for every File Center table.

    See the module docstring's "Downgrade policy" section: this mirrors the
    project's own established convention (29fee38a97e1) for adopted tables
    that may already hold real institutional data. A destructive downgrade
    (dropping all 19 tables) is not implemented here.
    """
