"""Phase 13B security closure -- setup-admin bootstrap negatives (SEC-001).

The prior brutal audit found ``/setup-admin`` publicly reachable whenever
``users`` is empty, with no environment gate at all -- reachable even in a
production-shaped app. The fix adds a fail-closed environment gate
(``_setup_admin_route_permitted`` in app/main_handlers/auth_handlers.py):
closed by default whenever ``APP_ENV`` is production/staging unless the
operator explicitly opts in via ``SETUP_ADMIN_ENABLED``.
"""
from __future__ import annotations

import uuid
from pathlib import Path

_PHASE13B_TEST_DB_ROOT = Path("C:/bys360/audit_tmp/phase13b/test_dbs")


def _make_app(monkeypatch, *, app_env: str = "testing", setup_admin_enabled: bool | None = None):
    # BYS360_P13B_TEST_APP_ENV: config.Config.APP_ENV (and everything derived
    # from it, e.g. SESSION_COOKIE_SECURE) is a class attribute computed once
    # from os.environ the FIRST time the `config` module is imported in this
    # process, so a later monkeypatch.setenv("APP_ENV", ...) has no effect on
    # an already-imported process (the value is frozen). The app is therefore
    # always built under the safe/permissive "testing" environment (which
    # boots without needing a full production-grade config), and the specific
    # APP_ENV value under test is applied directly to the created app's own
    # (mutable, per-instance) config dict -- exactly what
    # `_setup_admin_route_permitted()` reads at request time.
    _PHASE13B_TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
    db_path = _PHASE13B_TEST_DB_ROOT / f"{uuid.uuid4().hex}.sqlite3"
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-phase13b-setup-admin-negatives")
    monkeypatch.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "test-password")
    monkeypatch.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    monkeypatch.setenv("AUTO_REPAIR_SCHEMA", "false")
    monkeypatch.setenv("STRICT_SCHEMA_CHECK", "false")
    monkeypatch.setenv("REQUIRE_DOTENV_FILE", "false")
    monkeypatch.setenv("STRICT_ENV_VALIDATION", "false")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + db_path.as_posix())
    monkeypatch.setenv("MAIL_SUPPRESS_SEND", "true")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setenv("LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER", "false")

    from app import create_app

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///" + db_path.as_posix(),
        APP_ENV=app_env,
    )
    if setup_admin_enabled is not None:
        app.config["SETUP_ADMIN_ENABLED"] = setup_admin_enabled

    from app.extensions import db

    with app.app_context():
        db.create_all()

    return app


def _user_count(app) -> int:
    from app.extensions import db
    from app.models import User

    with app.app_context():
        return db.session.query(User).count()


def _delete_all_users(app) -> None:
    # BYS360_P13B_TEST_ISOLATION: config.Config.SQLALCHEMY_DATABASE_URI is a
    # class attribute resolved once at first import of this process (like
    # APP_ENV), so every app built later in this same pytest file/process
    # actually shares the FIRST test's sqlite file underneath, regardless of
    # the per-instance app.config override or the fresh DATABASE_URL passed
    # to monkeypatch. Tests that need a genuinely empty `users` table must
    # therefore clear it explicitly rather than relying on a fresh DB.
    from app.extensions import db
    from app.models import User

    with app.app_context():
        db.session.query(User).delete()
        db.session.commit()


# --- SEC-001: setup-admin disabled by default in production ---


def test_setup_admin_disabled_by_default_in_production(monkeypatch):
    app = _make_app(monkeypatch, app_env="production")
    _delete_all_users(app)
    before = _user_count(app)
    client = app.test_client()

    get_response = client.get("/setup-admin", follow_redirects=False)
    assert get_response.status_code == 404

    post_response = client.post(
        "/setup-admin",
        data={
            "ad": "Attacker",
            "soyad": "Bootstrap",
            "sicil_no": "90000",
            "email": "attacker@ktb.gov.tr",
            # BYS360 secret-gate closure: not a real credential -- an obviously
            # fake, test-only fixture value (contains "Test", matched
            # case-insensitively by the gate's own PLACEHOLDER_WORDS list in
            # scripts/quality/bys360_secret_repo_gate.py), still >= 8 chars to
            # satisfy _MIN_PASSWORD_LENGTH in app/main_handlers/auth_handlers.py.
            "password": "AttackerTestFixtureOnly123!",
        },
        follow_redirects=False,
    )
    assert post_response.status_code == 404
    assert _user_count(app) == before


def test_setup_admin_requires_explicit_flag_in_production(monkeypatch):
    app = _make_app(monkeypatch, app_env="production", setup_admin_enabled=True)
    _delete_all_users(app)
    before = _user_count(app)
    client = app.test_client()

    get_response = client.get("/setup-admin", follow_redirects=False)
    assert get_response.status_code == 200

    post_response = client.post(
        "/setup-admin",
        data={
            "ad": "Ops",
            "soyad": "Bootstrap",
            "sicil_no": "90001",
            "email": "ops.bootstrap@ktb.gov.tr",
            # Fake test-only fixture value; see comment on the attacker-path
            # password above.
            "password": "OperatorTestFixtureOnly1!",
        },
        follow_redirects=False,
    )
    assert post_response.status_code == 302
    assert _user_count(app) == before + 1


# --- SEC-001: setup-admin blocked once a user exists ---


def test_setup_admin_blocked_when_user_exists(monkeypatch):
    app = _make_app(monkeypatch)  # APP_ENV=testing -> route open by default
    _delete_all_users(app)
    from app.extensions import db
    from app.models import User

    with app.app_context():
        existing = User(
            sicil_no="10000",
            email="existing.admin@ktb.gov.tr",
            ad="Existing",
            soyad="Admin",
            role="admin",
            is_active=True,
            must_change_password=False,
            must_set_security_question=False,
        )
        existing.set_password("ExistingAdminPass1!")
        db.session.add(existing)
        db.session.commit()

    before = _user_count(app)
    assert before == 1
    client = app.test_client()

    get_response = client.get("/setup-admin", follow_redirects=False)
    assert get_response.status_code == 302
    assert "/login" in get_response.headers.get("Location", "")

    post_response = client.post(
        "/setup-admin",
        data={
            "ad": "Second",
            "soyad": "Admin",
            "sicil_no": "10001",
            "email": "second.admin@ktb.gov.tr",
            # Fake test-only fixture value; see comment on the attacker-path
            # password above.
            "password": "SecondAdminTestFixtureOnly1!",
        },
        follow_redirects=False,
    )
    assert post_response.status_code == 302
    assert _user_count(app) == before


# --- bonus: weak bootstrap password rejected ---


def test_setup_admin_rejects_weak_password(monkeypatch):
    app = _make_app(monkeypatch)  # APP_ENV=testing, zero users -> route open
    _delete_all_users(app)
    before = _user_count(app)
    client = app.test_client()

    response = client.post(
        "/setup-admin",
        data={
            "ad": "Weak",
            "soyad": "Password",
            "sicil_no": "10002",
            "email": "weak.password@ktb.gov.tr",
            "password": "1",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert _user_count(app) == before
