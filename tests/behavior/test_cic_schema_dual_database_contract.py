"""BYS360_DEFECT_AJ_CIC_SCHEMA_DUAL_DATABASE_CONTRACT

Regression contract for Defect AJ's CIC (Corporate Information Center)
candidates, triaged and mechanically proven independently rather than
assumed:

  - app/services/cic/celebration_service.py::ensure_celebration_schema()
    CLASSIFICATION: DUPLICATE_HELPER_ALREADY_SAFE. This function already
    dialect-branches correctly (``if dialect == "postgresql": ...ADD
    COLUMN IF NOT EXISTS... else: ...plain ADD COLUMN...``) -- the
    "ADD COLUMN IF NOT EXISTS" string a repo-wide grep found here is
    genuinely unreachable under SQLite (the ``else`` branch runs instead).
    Proven below against a real legacy-shaped SQLite ``users`` table
    missing all three target columns -- not assumed from the source text.

  - app/services/cic/cic_context.py::_cic_v45_ensure_schema()
    CLASSIFICATION: AJ_CONFIRMED_DEFECT. This function's Python-level
    existence guards (``if "birth_date" not in cols: ...``) were already
    correct, but each guarded ALTER statement's own SQL string still
    contained the literal "ADD COLUMN IF NOT EXISTS" keywords -- a SQLite
    PARSE-TIME syntax error (``near "EXISTS": syntax error``) that fires
    regardless of whether the Python guard correctly determined the
    column was missing. Mechanically reproduced against a real legacy
    SQLite ``users`` table before the fix: the function silently added
    NONE of the three columns (the broad ``except Exception: ...log...
    pass`` swallowed the error, so callers had no way to know the repair
    failed). Fixed by dropping the redundant "IF NOT EXISTS" keywords
    (the Python guard already prevents the duplicate-column case those
    keywords existed for).

Both functions are exercised here against a deliberately legacy-shaped
``users`` table (created via raw DDL, NOT db.create_all()) that lacks
birth_date/hire_date/celebration_opt_out entirely -- db.create_all() would
otherwise create them from the current User model's own column
declarations, masking whether the ADD COLUMN path is genuinely exercised.
"""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy.pool import StaticPool

_TMP_DB_DIR = r"C:\bys360_pytest_tmp_defect_aj_cic"


def _make_app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-defect-aj-cic-contract")
    monkeypatch.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "defect-aj-cic-first-login-test-pw")
    monkeypatch.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    monkeypatch.setenv("AUTO_REPAIR_SCHEMA", "false")
    monkeypatch.setenv("STRICT_SCHEMA_CHECK", "false")
    monkeypatch.setenv("REQUIRE_DOTENV_FILE", "false")
    monkeypatch.setenv("STRICT_ENV_VALIDATION", "false")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setenv("MAIL_SUPPRESS_SEND", "true")

    os.makedirs(_TMP_DB_DIR, exist_ok=True)
    db_path = os.path.join(_TMP_DB_DIR, f"defect_aj_cic_{uuid.uuid4().hex}.sqlite3")
    db_uri = "sqlite:///" + db_path.replace("\\", "/")
    monkeypatch.setenv("DATABASE_URL", db_uri)

    from app import create_app
    from config import Config

    monkeypatch.setattr(Config, "APP_ENV", "testing")
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", db_uri)
    monkeypatch.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})

    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_ENGINE_OPTIONS={
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        },
    )
    return flask_app


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    flask_app = _make_app(monkeypatch)
    with flask_app.app_context():
        from sqlalchemy import event

        from app.extensions import db

        @event.listens_for(db.engine, "connect")
        def _disable_pysqlite_implicit_begin(dbapi_connection, connection_record):  # noqa: ARG001
            dbapi_connection.isolation_level = None

        @event.listens_for(db.engine, "begin")
        def _explicit_begin(conn):
            conn.exec_driver_sql("BEGIN")

        db.create_all()
        # Replace the model-driven 'users' table with a deliberately
        # legacy-shaped one lacking birth_date/hire_date/
        # celebration_opt_out entirely, so both functions' ADD COLUMN
        # paths are genuinely exercised rather than skipped as no-ops.
        db.session.execute(db.text("DROP TABLE users"))
        db.session.execute(db.text("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255))"))
        db.session.commit()
    yield flask_app


def _cols(db, table_name: str) -> set[str]:
    from sqlalchemy import inspect
    return {c["name"] for c in inspect(db.engine).get_columns(table_name)}


def test_celebration_service_already_safely_adds_missing_columns_on_sqlite(app) -> None:
    """DUPLICATE_HELPER_ALREADY_SAFE, mechanically proven: on a legacy
    users table genuinely missing all three columns, this pre-existing,
    already dialect-branched helper adds them correctly under SQLite."""
    from app.extensions import db
    from app.services.cic.celebration_service import ensure_celebration_schema

    with app.app_context():
        result = ensure_celebration_schema()
        assert result["ok"] is True
        assert set(result["added"]) == {"birth_date", "hire_date", "celebration_opt_out"}
        cols = _cols(db, "users")
        assert {"birth_date", "hire_date", "celebration_opt_out"} <= cols


def test_celebration_service_is_idempotent_on_second_invocation(app) -> None:
    from app.services.cic.celebration_service import ensure_celebration_schema

    with app.app_context():
        ensure_celebration_schema()
        second = ensure_celebration_schema()
        assert second["ok"] is True
        assert second["added"] == []  # nothing left to add -- already idempotent by design


def test_cic_context_ensure_schema_adds_missing_columns_on_sqlite(app) -> None:
    """AJ_CONFIRMED_DEFECT closure: on the same legacy users table, this
    function must now actually add the columns instead of silently
    swallowing a SQLite syntax error."""
    from app.extensions import db
    from app.services.cic.cic_context import _cic_v45_ensure_schema

    with app.app_context():
        _cic_v45_ensure_schema()  # must not raise
        cols = _cols(db, "users")
        assert {"birth_date", "hire_date", "celebration_opt_out"} <= cols


def test_cic_context_ensure_schema_is_idempotent_on_second_invocation(app) -> None:
    from app.extensions import db
    from app.services.cic.cic_context import _cic_v45_ensure_schema

    with app.app_context():
        _cic_v45_ensure_schema()
        _cic_v45_ensure_schema()  # must not raise a second time (duplicate-column guard)
        cols = _cols(db, "users")
        assert {"birth_date", "hire_date", "celebration_opt_out"} <= cols
