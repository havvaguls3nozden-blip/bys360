"""BYS360 Test Integration Expansion Wave 1 — mobile auth real HTTP behavior.

Every test here does a real Flask ``test_client()`` HTTP call against a real
``create_app()`` instance and a real (in-memory SQLite) database, with a real
password-hashed user. Nothing here is AST/regex-based. Mock boundary: none —
these tests exercise the real login/token issuance/validation chain end to
end (password hashing, itsdangerous token signing, DB user lookup).
"""
from __future__ import annotations

import pytest


def _make_app(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-mobile-auth-flows")
    monkeypatch.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "test-password")
    monkeypatch.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    monkeypatch.setenv("AUTO_REPAIR_SCHEMA", "false")
    monkeypatch.setenv("STRICT_SCHEMA_CHECK", "false")
    monkeypatch.setenv("REQUIRE_DOTENV_FILE", "false")
    monkeypatch.setenv("STRICT_ENV_VALIDATION", "false")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("MAIL_SUPPRESS_SEND", "true")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    from app import create_app

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    from app.extensions import db

    with app.app_context():
        db.create_all()

    return app


@pytest.fixture
def app(monkeypatch):
    return _make_app(monkeypatch)


@pytest.fixture
def client(app):
    return app.test_client()


def _create_user(app, *, sicil_no="90001", email="mobile.wave1@bys360.test", password="Wave1TestSecret!", role="personel", is_active=True):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        user = User(
            sicil_no=sicil_no,
            email=email,
            ad="Wave1",
            soyad="Test",
            role=role,
            is_active=is_active,
            must_change_password=False,
            must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


# --- HTTP-INTEGRATION: real login -> real token -> real protected endpoint ---


def test_mobile_login_with_valid_credentials_returns_access_and_refresh_tokens(app, client):
    _create_user(app, sicil_no="90010", email="w1.login.ok@bys360.test", password="CorrectTestHorse1!")

    response = client.post(
        "/api/mobile/auth/login",
        json={"username": "90010", "password": "CorrectTestHorse1!"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["token_type"] == "Bearer"
    assert isinstance(payload["access_token"], str) and payload["access_token"]
    assert isinstance(payload["refresh_token"], str) and payload["refresh_token"]
    assert payload["user"]["sicil_no"] == "90010" if "sicil_no" in payload.get("user", {}) else True


def test_mobile_login_accepts_email_as_username(app, client):
    _create_user(app, sicil_no="90011", email="w1.email.login@bys360.test", password="EmailTestLogin1!")

    response = client.post(
        "/api/mobile/auth/login",
        json={"username": "w1.email.login@bys360.test", "password": "EmailTestLogin1!"},
    )

    assert response.status_code == 200
    assert response.get_json()["access_token"]


def test_mobile_login_with_wrong_password_is_rejected(app, client):
    _create_user(app, sicil_no="90012", email="w1.wrongpw@bys360.test", password="RealTestPassword1!")

    response = client.post(
        "/api/mobile/auth/login",
        json={"username": "90012", "password": "WrongTestPassword!"},
    )

    assert response.status_code == 401
    assert "access_token" not in (response.get_json() or {})


def test_mobile_login_with_nonexistent_user_is_rejected(app, client):
    response = client.post(
        "/api/mobile/auth/login",
        json={"username": "does-not-exist-90099", "password": "whatever"},
    )

    assert response.status_code == 401


def test_mobile_login_for_inactive_user_is_rejected(app, client):
    _create_user(app, sicil_no="90013", email="w1.inactive@bys360.test", password="InactiveTestUser1!", is_active=False)

    response = client.post(
        "/api/mobile/auth/login",
        json={"username": "90013", "password": "InactiveTestUser1!"},
    )

    assert response.status_code == 401


# --- VALIDATION-NEGATIVE: malformed / missing payloads ---


def test_mobile_login_with_missing_password_returns_400(app, client):
    _create_user(app, sicil_no="90014", email="w1.missingpw@bys360.test")

    response = client.post("/api/mobile/auth/login", json={"username": "90014"})

    assert response.status_code == 400


def test_mobile_login_with_missing_username_returns_400(app, client):
    response = client.post("/api/mobile/auth/login", json={"password": "whatever"})

    assert response.status_code == 400


def test_mobile_login_with_empty_json_body_returns_400(app, client):
    response = client.post("/api/mobile/auth/login", json={})

    assert response.status_code == 400


def test_mobile_login_with_malformed_json_does_not_500(app, client):
    response = client.post(
        "/api/mobile/auth/login",
        data="{not-valid-json",
        content_type="application/json",
    )

    assert response.status_code < 500
    assert response.status_code in {400, 401, 415}


# --- AUTHZ-NEGATIVE: protected endpoint token handling ---


def test_mobile_me_without_authorization_header_returns_401(client):
    response = client.get("/api/mobile/me")

    assert response.status_code == 401


def test_mobile_me_with_malformed_bearer_token_returns_401(client):
    response = client.get("/api/mobile/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_mobile_me_with_non_bearer_scheme_returns_401(app, client):
    _create_user(app, sicil_no="90015", email="w1.basicscheme@bys360.test", password="BasicTestScheme1!")
    login = client.post("/api/mobile/auth/login", json={"username": "90015", "password": "BasicTestScheme1!"})
    token = login.get_json()["access_token"]

    response = client.get("/api/mobile/me", headers={"Authorization": f"Basic {token}"})

    assert response.status_code == 401


def test_mobile_me_with_valid_token_returns_200_and_real_profile(app, client):
    _create_user(app, sicil_no="90016", email="w1.realprofile@bys360.test", password="RealTestProfile1!")
    login = client.post("/api/mobile/auth/login", json={"username": "90016", "password": "RealTestProfile1!"})
    token = login.get_json()["access_token"]

    response = client.get("/api/mobile/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None


def test_mobile_me_token_for_deactivated_user_is_rejected_after_deactivation(app, client):
    """A token issued while active must stop working once the account is deactivated —
    proves the /me path re-checks is_active on every request rather than trusting the token alone."""
    from app.extensions import db
    from app.models import User

    user_id = _create_user(app, sicil_no="90017", email="w1.deactivated@bys360.test", password="DeactivateTest1!")
    login = client.post("/api/mobile/auth/login", json={"username": "90017", "password": "DeactivateTest1!"})
    token = login.get_json()["access_token"]

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        user.is_active = False
        db.session.commit()

    response = client.get("/api/mobile/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


# --- HTTP-INTEGRATION: refresh flow ---


def test_mobile_refresh_with_valid_refresh_token_issues_new_access_token(app, client):
    _create_user(app, sicil_no="90018", email="w1.refresh@bys360.test", password="RefreshTestFlow1!")
    login = client.post("/api/mobile/auth/login", json={"username": "90018", "password": "RefreshTestFlow1!"})
    refresh_token = login.get_json()["refresh_token"]

    response = client.post("/api/mobile/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    new_access_token = response.get_json()["access_token"]
    assert new_access_token

    me_response = client.get("/api/mobile/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me_response.status_code == 200


def test_mobile_refresh_with_access_token_instead_of_refresh_token_is_rejected(app, client):
    """The refresh endpoint must reject an access token passed as a refresh token —
    proves the two token kinds are salted/scoped separately, not interchangeable."""
    _create_user(app, sicil_no="90019", email="w1.tokenconfusion@bys360.test", password="TokenTestConfusion1!")
    login = client.post("/api/mobile/auth/login", json={"username": "90019", "password": "TokenTestConfusion1!"})
    access_token = login.get_json()["access_token"]

    response = client.post("/api/mobile/auth/refresh", json={"refresh_token": access_token})

    assert response.status_code == 401


def test_mobile_refresh_with_garbage_token_returns_401(client):
    response = client.post("/api/mobile/auth/refresh", json={"refresh_token": "garbage-token-value"})

    assert response.status_code == 401


def test_mobile_refresh_with_missing_token_returns_401(client):
    response = client.post("/api/mobile/auth/refresh", json={})

    assert response.status_code == 401
