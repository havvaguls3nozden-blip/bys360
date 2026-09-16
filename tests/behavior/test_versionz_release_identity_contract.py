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

BYS360_DEFECT_AF_VERSIONZ_LOOPBACK_GATE
========================================
/versionz has no @login_required (matching /healthz and /readyz -- a
pre-existing design this fix does not change), so making it return real
source_sha/migration_head unconditionally would let ANY unauthenticated
caller on the public internet fingerprint the exact deployed commit/
migration revision. Fixed by gating just those two fields to callers
connecting from the loopback interface -- exactly what cutover_bys360_
candidate.ps1's Test-ReleaseIdentityBinding needs (it always curls
http://127.0.0.1:$AppPort directly) and nothing more; every other field
stays public, unchanged.

BYS360 PRODUCTION RELEASE-IDENTITY HOTFIX #2: the gate reads the RAW TCP
peer address from Werkzeug ProxyFix's own real environ contract --
environ["werkzeug.proxy_fix.orig"]["REMOTE_ADDR"] -- verified directly
against the installed werkzeug (3.1.8) source. A prior version of this
gate read a flat "werkzeug.proxy_fix.orig_remote_addr" key that was
REMOVED from Werkzeug in 1.0 and therefore never existed; because that
lookup always fell through to its own default (request.remote_addr --
exactly what ProxyFix REWRITES from X-Forwarded-For), the gate's claimed
resistance to a spoofed "X-Forwarded-For: 127.0.0.1" was never actually in
effect once ProxyFix was genuinely enabled, and the regression test meant
to prove otherwise passed for an unrelated reason: it enabled ProxyFix via
monkeypatch.setenv("PROXY_FIX_ENABLED", ...), which cannot affect
config.py's Config.PROXY_FIX_ENABLED (a class attribute evaluated once at
first import, not re-read afterwards) -- so ProxyFix was never actually
wrapped into that test's app at all. Tests below that need ProxyFix
genuinely active use monkeypatch.setattr(Config, "PROXY_FIX_ENABLED",
True) instead (the same pattern already established in
tests/security/test_https_scheme_and_hsts_hardening.py), so the middleware
truly runs and truly populates werkzeug.proxy_fix.orig.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from flask import request


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


def test_versionz_with_bom_prefixed_candidate_ready_json_exposes_release_identity(monkeypatch, tmp_path: Path):
    """BYS360 PRODUCTION RELEASE-IDENTITY HOTFIX #2 core RECEIPT proof: a
    real production CANDIDATE_READY.json was confirmed to start with a
    UTF-8 byte-order-mark (EF BB BF) -- prepare_bys360_candidate.ps1's old
    receipt writer used PowerShell's "-Encoding UTF8" parameter, which
    Windows PowerShell 5.1 (what production runs) writes WITH a BOM. The
    reader (encoding="utf-8-sig") must still parse this exact byte layout
    correctly, not just newly-written BOM-less receipts."""
    app = _make_app(monkeypatch)

    fake_app_dir = tmp_path / "app"
    fake_app_dir.mkdir(parents=True, exist_ok=True)
    candidate_ready = tmp_path / "CANDIDATE_READY.json"
    payload = json.dumps({
        "SOURCE_SHA": "abc123deadbeef",
        "MIGRATION_HEAD": "10858a18e9ac",
        "CANDIDATE_READY": "YES",
    }).encode("utf-8")
    candidate_ready.write_bytes(b"\xef\xbb\xbf" + payload)
    assert candidate_ready.read_bytes().startswith(b"\xef\xbb\xbf"), "test fixture itself must genuinely carry a BOM"
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


def _make_app_with_candidate_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    app = _make_app(monkeypatch)
    fake_app_dir = tmp_path / "app"
    fake_app_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "CANDIDATE_READY.json").write_text(
        json.dumps({"SOURCE_SHA": "abc123deadbeef", "MIGRATION_HEAD": "10858a18e9ac", "CANDIDATE_READY": "YES"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(app, "root_path", str(fake_app_dir))
    return app


def test_versionz_from_loopback_caller_still_exposes_release_identity(monkeypatch, tmp_path: Path):
    """Explicit positive proof, not just the implicit test-client default:
    a caller genuinely connecting from 127.0.0.1 gets the real fields --
    matching exactly what cutover_bys360_candidate.ps1's own curl call to
    http://127.0.0.1:$AppPort needs."""
    app = _make_app_with_candidate_ready(monkeypatch, tmp_path)
    response = app.test_client().get("/versionz", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["source_sha"] == "abc123deadbeef"
    assert body["migration_head"] == "10858a18e9ac"


def test_versionz_from_ipv6_loopback_caller_still_exposes_release_identity(monkeypatch, tmp_path: Path):
    """The IPv6 loopback form (::1) must be recognized exactly like the
    IPv4 one -- proves the canonical IP-parsing rewrite of the loopback
    gate didn't narrow acceptance to IPv4 only."""
    app = _make_app_with_candidate_ready(monkeypatch, tmp_path)
    response = app.test_client().get("/versionz", environ_overrides={"REMOTE_ADDR": "::1"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["source_sha"] == "abc123deadbeef"
    assert body["migration_head"] == "10858a18e9ac"


def test_versionz_from_ipv4_mapped_ipv6_loopback_caller_still_exposes_release_identity(monkeypatch, tmp_path: Path):
    """BYS360_DEFECT_Z_HOTFIX core proof: a real production cutover's own
    self-curl to http://127.0.0.1:$AppPort observed its raw socket peer as
    "::ffff:127.0.0.1" (the IPv4-mapped-IPv6 form a dual-stack Windows
    socket may legitimately report for a genuine IPv4 loopback connection),
    which the old literal {"127.0.0.1", "::1"} string-set check did not
    recognize -- silently forcing source_sha/migration_head to null even
    though the caller genuinely was loopback, and failing
    Test-ReleaseIdentityBinding for a correctly-promoted candidate."""
    app = _make_app_with_candidate_ready(monkeypatch, tmp_path)
    response = app.test_client().get("/versionz", environ_overrides={"REMOTE_ADDR": "::ffff:127.0.0.1"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["source_sha"] == "abc123deadbeef"
    assert body["migration_head"] == "10858a18e9ac"


def test_versionz_from_non_loopback_caller_gets_null_release_identity(monkeypatch, tmp_path: Path):
    """BYS360 DEFECT AF core proof: a caller connecting from a real, non-
    loopback address (simulating any public-internet or LAN caller of the
    unauthenticated /versionz endpoint) must NOT receive source_sha/
    migration_head, even though a genuine CANDIDATE_READY.json exists and
    would be returned to a loopback caller (previous test)."""
    app = _make_app_with_candidate_ready(monkeypatch, tmp_path)
    response = app.test_client().get("/versionz", environ_overrides={"REMOTE_ADDR": "203.0.113.5"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["source_sha"] is None
    assert body["migration_head"] is None
    # The rest of the endpoint's contract must be completely unaffected.
    assert body["service"] == "bys360"


def _make_app_with_genuine_proxyfix_and_candidate_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """BYS360 PRODUCTION RELEASE-IDENTITY HOTFIX #2: genuinely enables
    ProxyFix, unlike monkeypatch.setenv("PROXY_FIX_ENABLED", "true") (which
    cannot work -- see the module docstring). config.py's
    Config.PROXY_FIX_ENABLED is a class attribute evaluated once at first
    import of the config module, not re-read per request or per env
    change; monkeypatch.setattr(Config, "PROXY_FIX_ENABLED", True) is the
    only way to make a real ProxyFix instance actually wrap app.wsgi_app
    for this app instance -- the same pattern already established in
    tests/security/test_https_scheme_and_hsts_hardening.py."""
    from config import Config

    monkeypatch.setattr(Config, "PROXY_FIX_ENABLED", True)
    app = _make_app_with_candidate_ready(monkeypatch, tmp_path)
    assert app.config.get("PROXY_FIX_ENABLED") is True, "precondition: ProxyFix must genuinely be wrapped for this test to prove anything"
    return app


def test_versionz_spoofed_x_forwarded_for_loopback_does_not_bypass_the_gate(monkeypatch, tmp_path: Path):
    """The strongest AF proof: even with ProxyFix genuinely ENABLED
    (production-like) and an attacker-controlled request claiming
    "X-Forwarded-For: 127.0.0.1" while the real, raw TCP connection comes
    from a genuine external address, the gate must still return null --
    proving it reads the real werkzeug.proxy_fix.orig["REMOTE_ADDR"], not
    request.remote_addr (exactly what ProxyFix rewrites FROM that header,
    and what the previous, incorrect key name silently fell back to)."""
    app = _make_app_with_genuine_proxyfix_and_candidate_ready(monkeypatch, tmp_path)
    response = app.test_client().get(
        "/versionz",
        environ_overrides={"REMOTE_ADDR": "203.0.113.5"},
        headers={"X-Forwarded-For": "127.0.0.1"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["source_sha"] is None, "a spoofed X-Forwarded-For loopback claim must not bypass the AF gate"
    assert body["migration_head"] is None


def test_versionz_genuine_loopback_through_real_proxyfix_still_exposes_release_identity(monkeypatch, tmp_path: Path):
    """Real Werkzeug ProxyFix integration test (item 17 of the hotfix #2
    regression brief): with ProxyFix genuinely active and an X-Forwarded-For
    header present but pointing at an unrelated address, a caller whose
    RAW peer genuinely is 127.0.0.1 must still get its release identity --
    proving raw-peer trust survives an arbitrary X-Forwarded-For value
    rather than being disabled outright whenever ProxyFix is on."""
    app = _make_app_with_genuine_proxyfix_and_candidate_ready(monkeypatch, tmp_path)
    response = app.test_client().get(
        "/versionz",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
        headers={"X-Forwarded-For": "203.0.113.9"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["source_sha"] == "abc123deadbeef"
    assert body["migration_head"] == "10858a18e9ac"


def test_versionz_loopback_check_with_malformed_orig_remote_addr_fails_closed(monkeypatch, tmp_path: Path):
    """Item 18: when ProxyFix is genuinely active but the raw REMOTE_ADDR
    it captured is empty/unparseable (e.g. a misconfigured or malformed
    upstream connection), the gate must fail closed -- non-loopback,
    identity hidden -- never fall back to trusting request.remote_addr
    (which ProxyFix may already have rewritten from client-controlled
    headers)."""
    app = _make_app_with_genuine_proxyfix_and_candidate_ready(monkeypatch, tmp_path)
    response = app.test_client().get("/versionz", environ_overrides={"REMOTE_ADDR": ""})
    assert response.status_code == 200
    body = response.get_json()
    assert body["source_sha"] is None
    assert body["migration_head"] is None


def test_versionz_loopback_check_with_orig_structure_missing_remote_addr_key_fails_closed(monkeypatch, tmp_path: Path):
    """Item 19: if werkzeug.proxy_fix.orig exists but somehow lacks its own
    REMOTE_ADDR key entirely (a malformed/incomplete orig structure), the
    gate must not silently fall back to request.remote_addr -- it must
    fail closed. Exercises _bys360_request_is_from_loopback directly
    against a manually-shaped environ, since real ProxyFix always includes
    the REMOTE_ADDR key (even if empty -- see the previous test) and so
    cannot itself produce a dict missing the key outright."""
    app = _make_app_with_candidate_ready(monkeypatch, tmp_path)
    from app.routes import _bys360_request_is_from_loopback

    with app.test_request_context(
        "/versionz",
        environ_overrides={"werkzeug.proxy_fix.orig": {"wsgi.url_scheme": "https"}},
    ):
        assert _bys360_request_is_from_loopback() is False


def test_versionz_loopback_check_without_proxyfix_orig_structure_uses_remote_addr_directly(monkeypatch, tmp_path: Path):
    """Item 20: with ProxyFix genuinely absent/disabled (this app's own
    test default -- PROXY_FIX_ENABLED is False), there is no
    werkzeug.proxy_fix.orig structure in the environ at all, so
    request.remote_addr itself is the raw, unforgeable socket peer and may
    be evaluated directly."""
    app = _make_app_with_candidate_ready(monkeypatch, tmp_path)
    from app.routes import _bys360_request_is_from_loopback

    with app.test_request_context("/versionz", environ_overrides={"REMOTE_ADDR": "127.0.0.1"}):
        assert "werkzeug.proxy_fix.orig" not in request.environ
        assert _bys360_request_is_from_loopback() is True
