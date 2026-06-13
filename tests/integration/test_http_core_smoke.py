from __future__ import annotations
import pytest



# BYS360_SPRINT2_LEGACY_INTEGRATION_SCOPE_V8
pytestmark = [pytest.mark.legacy_integration, pytest.mark.realdb]
def _make_app(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "test-password")
    monkeypatch.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    from app import create_app

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return app


def test_healthz_returns_json(monkeypatch):
    app = _make_app(monkeypatch)
    response = app.test_client().get("/healthz")
    assert response.status_code == 200
    assert response.get_json()["service"] == "bys360"


def test_personel_analizi_route_is_protected_not_missing(monkeypatch):
    app = _make_app(monkeypatch)
    response = app.test_client().get("/performance/personel-analizi")
    assert response.status_code in {302, 401, 403}
    assert response.status_code != 404


def test_core_health_route_is_protected_not_missing(monkeypatch):
    app = _make_app(monkeypatch)
    response = app.test_client().get("/performance/core-health")
    assert response.status_code in {302, 401, 403}
    assert response.status_code != 404
