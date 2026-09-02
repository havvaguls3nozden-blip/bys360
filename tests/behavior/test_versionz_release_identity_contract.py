"""BYS360_DEFECT_Z_VERSIONZ_RELEASE_IDENTITY_CONTRACT

Regression contract for the minimal, justified application-source change
inside Defect Z (cutover process/release identity binding).

Root cause this closes: every promoted candidate release lives at the exact
same fixed path (C:\\bys360\\project). PID/process/path metadata -- which
scripts/windows/cutover_bys360_candidate.ps1's Test-ProcessBinding uses to
prove a FRESH, BYS360-owned process is listening -- is therefore identical
across every version ever promoted and can never, by itself, prove WHICH
release's code that process actually has loaded. GET /versionz already
existed as the app's own "what version am I" surface but returned no release
identity at all before this fix.

Fix: GET /versionz now also reads the running process's own bundled
CANDIDATE_READY.json (the same file cutover_bys360_candidate.ps1 itself
writes/verifies) and exposes its SOURCE_SHA/MIGRATION_HEAD. The cutover
script's new Test-ReleaseIdentityBinding function calls this endpoint after
promotion and compares the response against the candidate identity it
intended to promote -- failing closed on any mismatch. This is a pure
additive change: all four pre-existing /versionz fields (service, app_env,
route_count, schema_error_count) and the entire /readyz endpoint are
unchanged, confirmed here as a non-regression guard.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _make_app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-defect-z-versionz-contract")
    monkeypatch.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "defect-z-first-login-test-pw")
    monkeypatch.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setenv("MAIL_SUPPRESS_SEND", "true")
    from app import create_app

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return app


def test_versionz_without_candidate_ready_json_returns_none_release_identity(monkeypatch):
    """Local/dev environments (or any tree not managed by the candidate/
    cutover pipeline) have no CANDIDATE_READY.json -- the endpoint must
    degrade gracefully (null fields), not error."""
    app = _make_app(monkeypatch)
    client = app.test_client()

    response = client.get("/versionz")
    assert response.status_code == 200
    body = response.get_json()
    assert body["service"] == "bys360"
    assert body["source_sha"] is None
    assert body["migration_head"] is None


def test_versionz_with_candidate_ready_json_exposes_release_identity(monkeypatch, tmp_path: Path):
    app = _make_app(monkeypatch)

    fake_app_dir = tmp_path / "app"
    fake_app_dir.mkdir(parents=True, exist_ok=True)
    candidate_ready = tmp_path / "CANDIDATE_READY.json"
    candidate_ready.write_text(
        json.dumps({
            "SOURCE_SHA": "abc123deadbeef",
            "MIGRATION_HEAD": "10858a18e9ac",
            "CANDIDATE_READY": "YES",
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(app, "root_path", str(fake_app_dir))

    response = app.test_client().get("/versionz")
    assert response.status_code == 200
    body = response.get_json()
    assert body["source_sha"] == "abc123deadbeef"
    assert body["migration_head"] == "10858a18e9ac"


def test_versionz_with_malformed_candidate_ready_json_degrades_to_none_not_500(monkeypatch, tmp_path: Path):
    app = _make_app(monkeypatch)

    fake_app_dir = tmp_path / "app"
    fake_app_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "CANDIDATE_READY.json").write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(app, "root_path", str(fake_app_dir))

    response = app.test_client().get("/versionz")
    assert response.status_code == 200
    body = response.get_json()
    assert body["source_sha"] is None
    assert body["migration_head"] is None


def test_versionz_pre_existing_fields_unchanged(monkeypatch):
    app = _make_app(monkeypatch)
    response = app.test_client().get("/versionz")
    assert response.status_code == 200
    body = response.get_json()
    assert body["service"] == "bys360"
    assert "app_env" in body
    assert isinstance(body["route_count"], int)
    assert isinstance(body["schema_error_count"], int)


def test_readyz_contract_unchanged_by_this_fix(monkeypatch):
    app = _make_app(monkeypatch)
    response = app.test_client().get("/readyz")
    assert response.status_code in (200, 503)
    body = response.get_json()
    assert body["service"] == "bys360"
    assert body["status"] in ("ready", "degraded")
    assert "schema_error_count" in body
    assert "source_sha" not in body, "release identity belongs only on /versionz, not /readyz"
