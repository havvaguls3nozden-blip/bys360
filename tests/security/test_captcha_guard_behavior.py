"""BYS360 TD-016 coverage-gap closure: app/security/captcha_guard.py.

This module was previously at 0.0% line / 0.0% branch coverage despite being
the brute-force login defense: it decides when a simple arithmetic captcha
must be shown, tracking failed logins per client key via the shared,
multi-worker-safe app/security/rate_limit_store.py, with an in-process
_FAILED_LOGIN_CACHE fallback when the shared store is unavailable.

These are real behavioural tests, run inside a genuine Flask app/request
context via the shared `app` fixture from tests/conftest.py (same
create_app()-based pattern used throughout tests/security/). Each test
points SECURITY_RATE_LIMIT_FILE at a fresh tmp_path so the shared store never
leaks state across tests, and an autouse fixture clears the module-level
_FAILED_LOGIN_CACHE dict before/after every test for the same reason.

A dedicated test (test_shared_store_write_failure_falls_back_to_inprocess_
cache_not_silently_disabled) specifically targets the SECURITY FAIL-OPEN
question this task asked to investigate: does a shared-store failure ever
silently bypass/disable captcha enforcement, instead of degrading to the
equally-enforcing in-process fallback? See that test and the final report
for the conclusion.
"""
from __future__ import annotations

import pytest

from app.security import captcha_guard as cg, rate_limit_store as rls


@pytest.fixture(autouse=True)
def _clear_inprocess_failed_login_cache():
    cg._FAILED_LOGIN_CACHE.clear()
    yield
    cg._FAILED_LOGIN_CACHE.clear()


def _configure_shared_store(app, monkeypatch, tmp_path, **overrides):
    store_path = tmp_path / "security_rate_limits.json"
    config = {
        "SECURITY_RATE_LIMIT_BACKEND": "file",
        "SECURITY_RATE_LIMIT_SHARED": True,
        "SECURITY_RATE_LIMIT_FILE": str(store_path),
        "SECURITY_RATE_LIMIT_REDIS_URL": "",
        "REDIS_URL": "",
        "CACHE_REDIS_URL": "",
        "CAPTCHA_ENABLED": True,
        "LOGIN_MAX_FAILS_BEFORE_CAPTCHA": 3,
    }
    config.update(overrides)
    for key, value in config.items():
        monkeypatch.setitem(app.config, key, value)
    return store_path


def _make_client_key(app, ip="203.0.113.10", ua="pytest-agent"):
    with app.test_request_context("/login", headers={"X-Forwarded-For": ip, "User-Agent": ua}):
        return cg.get_client_key()


# ---------------------------------------------------------------------------
# get_client_key()
# ---------------------------------------------------------------------------


def test_get_client_key_prefers_first_x_forwarded_for_entry(app):
    with app.test_request_context(
        "/login", headers={"X-Forwarded-For": "203.0.113.5, 10.0.0.1"}
    ):
        key = cg.get_client_key()
    assert key.startswith("203.0.113.5|")


def test_get_client_key_falls_back_to_remote_addr_without_forwarded_header(app):
    with app.test_request_context("/login", environ_base={"REMOTE_ADDR": "192.0.2.77"}):
        key = cg.get_client_key()
    assert key.startswith("192.0.2.77|")


def test_get_client_key_truncates_user_agent_to_120_chars(app):
    long_ua = "A" * 500
    with app.test_request_context("/login", headers={"User-Agent": long_ua}):
        key = cg.get_client_key()
    _, _, ua_part = key.partition("|")
    assert len(ua_part) == 120


def test_different_client_keys_are_isolated(app, monkeypatch, tmp_path):
    _configure_shared_store(app, monkeypatch, tmp_path, LOGIN_MAX_FAILS_BEFORE_CAPTCHA=2)
    key_a = _make_client_key(app, ip="203.0.113.10", ua="agent-A")
    key_b = _make_client_key(app, ip="198.51.100.20", ua="agent-B")
    assert key_a != key_b
    with app.app_context():
        cg.record_failed_login_attempt(key_a)
        cg.record_failed_login_attempt(key_a)
        assert cg.is_captcha_required(key_a) is True
        assert cg.is_captcha_required(key_b) is False


# ---------------------------------------------------------------------------
# is_captcha_required() -- CAPTCHA_ENABLED short-circuit + threshold boundary
# ---------------------------------------------------------------------------


def test_is_captcha_required_false_when_disabled_regardless_of_failure_count(
    app, monkeypatch, tmp_path
):
    """`return enabled and int(shared[0]) >= _threshold()` -- `enabled` must
    short-circuit to False even when the failure count is far past
    threshold."""
    _configure_shared_store(
        app, monkeypatch, tmp_path, CAPTCHA_ENABLED=False, LOGIN_MAX_FAILS_BEFORE_CAPTCHA=1
    )
    client_key = _make_client_key(app)
    with app.app_context():
        for _ in range(5):
            cg.record_failed_login_attempt(client_key)
        assert cg.is_captcha_required(client_key) is False


def test_failure_count_below_threshold_not_required(app, monkeypatch, tmp_path):
    _configure_shared_store(app, monkeypatch, tmp_path, LOGIN_MAX_FAILS_BEFORE_CAPTCHA=3)
    client_key = _make_client_key(app)
    with app.app_context():
        cg.record_failed_login_attempt(client_key)
        cg.record_failed_login_attempt(client_key)
        assert cg.is_captcha_required(client_key) is False


def test_failure_count_exactly_at_threshold_is_required(app, monkeypatch, tmp_path):
    """Boundary per source: `int(shared[0]) >= _threshold()` uses `>=`, so a
    count that equals the threshold already requires the captcha."""
    _configure_shared_store(app, monkeypatch, tmp_path, LOGIN_MAX_FAILS_BEFORE_CAPTCHA=3)
    client_key = _make_client_key(app)
    with app.app_context():
        for _ in range(3):
            cg.record_failed_login_attempt(client_key)
        assert cg.is_captcha_required(client_key) is True


def test_failure_count_one_below_threshold_still_not_required(app, monkeypatch, tmp_path):
    _configure_shared_store(app, monkeypatch, tmp_path, LOGIN_MAX_FAILS_BEFORE_CAPTCHA=3)
    client_key = _make_client_key(app)
    with app.app_context():
        cg.record_failed_login_attempt(client_key)
        cg.record_failed_login_attempt(client_key)
        assert cg.is_captcha_required(client_key) is False


# ---------------------------------------------------------------------------
# record_failed_login_attempt() -- shared store vs in-process fallback
# ---------------------------------------------------------------------------


def test_record_failed_login_attempt_uses_shared_store_when_available(app, monkeypatch, tmp_path):
    store_path = _configure_shared_store(app, monkeypatch, tmp_path)
    client_key = _make_client_key(app)
    with app.app_context():
        count = cg.record_failed_login_attempt(client_key)
        shared = rls.read_bucket_count(f"captcha:{client_key}", 30 * 60)
    assert count == 1
    assert shared is not None
    assert shared[0] == 1
    assert store_path.exists()
    # the shared store handled it, so the in-process cache must be untouched
    assert cg._FAILED_LOGIN_CACHE == {}


def test_record_failed_login_attempt_falls_back_to_inprocess_cache_when_shared_disabled(
    app, monkeypatch, tmp_path
):
    _configure_shared_store(app, monkeypatch, tmp_path, SECURITY_RATE_LIMIT_BACKEND="off")
    client_key = _make_client_key(app)
    with app.app_context():
        count1 = cg.record_failed_login_attempt(client_key)
        count2 = cg.record_failed_login_attempt(client_key)
    assert (count1, count2) == (1, 2)
    assert len(cg._FAILED_LOGIN_CACHE.get(client_key, [])) == 2


def test_is_captcha_required_uses_inprocess_fallback_when_shared_disabled(
    app, monkeypatch, tmp_path
):
    _configure_shared_store(
        app,
        monkeypatch,
        tmp_path,
        SECURITY_RATE_LIMIT_BACKEND="off",
        LOGIN_MAX_FAILS_BEFORE_CAPTCHA=2,
    )
    client_key = _make_client_key(app)
    with app.app_context():
        cg.record_failed_login_attempt(client_key)
        assert cg.is_captcha_required(client_key) is False
        cg.record_failed_login_attempt(client_key)
        assert cg.is_captcha_required(client_key) is True


# ---------------------------------------------------------------------------
# clear_failed_login_attempts() -- resets both the shared bucket AND the
# in-process cache
# ---------------------------------------------------------------------------


def test_clear_failed_login_attempts_resets_shared_store_bucket(app, monkeypatch, tmp_path):
    _configure_shared_store(app, monkeypatch, tmp_path)
    client_key = _make_client_key(app)
    with app.app_context():
        cg.record_failed_login_attempt(client_key)
        cg.record_failed_login_attempt(client_key)
        cg.clear_failed_login_attempts(client_key)
        shared = rls.read_bucket_count(f"captcha:{client_key}", 30 * 60)
    assert shared == (0, 0)


def test_clear_failed_login_attempts_resets_inprocess_cache(app, monkeypatch, tmp_path):
    _configure_shared_store(app, monkeypatch, tmp_path, SECURITY_RATE_LIMIT_BACKEND="off")
    client_key = _make_client_key(app)
    with app.app_context():
        cg.record_failed_login_attempt(client_key)
        assert client_key in cg._FAILED_LOGIN_CACHE
        cg.clear_failed_login_attempts(client_key)
    assert client_key not in cg._FAILED_LOGIN_CACHE


def test_clear_failed_login_attempts_always_pops_inprocess_cache_even_when_shared_enabled(
    app, monkeypatch, tmp_path
):
    """clear_failed_login_attempts() unconditionally does both
    `_shared_clear_buckets(...)` AND `_FAILED_LOGIN_CACHE.pop(client_key,
    None)` -- verify the in-process side is cleared even for a key that was
    only ever recorded in the shared store (simulating a worker restart that
    left a stale in-process entry)."""
    _configure_shared_store(app, monkeypatch, tmp_path)
    client_key = _make_client_key(app)
    with app.app_context():
        cg.record_failed_login_attempt(client_key)  # goes to shared store only
        from app.core.datetime_utils import utc_now

        cg._FAILED_LOGIN_CACHE[client_key] = [utc_now()]  # simulate stale local state
        cg.clear_failed_login_attempts(client_key)
        shared = rls.read_bucket_count(f"captcha:{client_key}", 30 * 60)
    assert shared == (0, 0)
    assert client_key not in cg._FAILED_LOGIN_CACHE


# ---------------------------------------------------------------------------
# verify_simple_captcha() / generate_simple_captcha()
# ---------------------------------------------------------------------------


def test_verify_simple_captcha_correct_answer_with_whitespace_is_true():
    assert cg.verify_simple_captcha("  7  ", "7") is True


def test_verify_simple_captcha_incorrect_answer_is_false():
    assert cg.verify_simple_captcha("8", "7") is False


def test_verify_simple_captcha_missing_or_none_answer_is_false():
    # The signature declares `str`, but the real body (`str(answer or "")`)
    # tolerates None at runtime -- real call sites may pass a possibly-None
    # form value, so this is a legitimate behavioral case, not a type error.
    assert cg.verify_simple_captcha(None, "7") is False  # type: ignore[arg-type]
    assert cg.verify_simple_captcha("", "7") is False


def test_verify_simple_captcha_missing_expected_is_false():
    assert cg.verify_simple_captcha("7", None) is False  # type: ignore[arg-type]


def test_generate_simple_captcha_is_internally_consistent():
    for _ in range(25):
        question, expected = cg.generate_simple_captcha()
        left, _, right = question.partition(" + ")
        b_str, _, _tail = right.partition(" = ?")
        a, b = int(left), int(b_str)
        assert 1 <= a <= 9
        assert 1 <= b <= 9
        assert expected == str(a + b)
        assert cg.verify_simple_captcha(expected, expected) is True


# ---------------------------------------------------------------------------
# SECURITY FAIL-OPEN investigation
# ---------------------------------------------------------------------------


def test_shared_store_write_failure_falls_back_to_inprocess_cache_not_silently_disabled(
    app, monkeypatch, tmp_path
):
    """Security regression guard for the fail-open question this task asked
    to investigate.

    Scenario: the shared, file-backed rate-limit store is *enabled* but
    cannot actually be written (simulated here by pointing
    SECURITY_RATE_LIMIT_FILE at a path that is already an existing
    directory, so app/security/rate_limit_store.py's `_write_payload()` ->
    `os.replace(tmp, path)` raises OSError, caught by `_with_payload()`'s
    broad `except Exception` and turned into a `None` return -- a real,
    unmocked failure of the exact code path record_bucket_hit()/
    read_bucket_count() run through).

    Expected (and verified) behaviour: captcha_guard.record_failed_login_
    attempt() / is_captcha_required() must still enforce, via the
    in-process _FAILED_LOGIN_CACHE fallback -- NOT silently stop counting
    failed logins and NOT silently report "captcha not required" just
    because the shared store happens to be broken.
    """
    broken_store_path = tmp_path / "ratelimits_as_directory"
    broken_store_path.mkdir()
    _configure_shared_store(
        app,
        monkeypatch,
        tmp_path,
        SECURITY_RATE_LIMIT_FILE=str(broken_store_path),
        LOGIN_MAX_FAILS_BEFORE_CAPTCHA=2,
    )
    client_key = _make_client_key(app, ip="203.0.113.99")
    with app.app_context():
        # Prove the shared store really is broken (enabled, but every write
        # fails), not merely disabled by config.
        assert rls.shared_store_enabled() is True
        assert rls.record_bucket_hit(f"captcha:{client_key}", window_seconds=1800, limit=2) is None

        count1 = cg.record_failed_login_attempt(client_key)
        count2 = cg.record_failed_login_attempt(client_key)
        required = cg.is_captcha_required(client_key)

    assert (count1, count2) == (1, 2)
    assert required is True, (
        "FAIL-OPEN: a shared-store write failure must not silently bypass "
        "captcha enforcement -- it must degrade to the in-process cache "
        "fallback instead."
    )
    assert client_key in cg._FAILED_LOGIN_CACHE
