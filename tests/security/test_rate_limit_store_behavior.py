"""BYS360 TD-016 coverage-gap closure: app/security/rate_limit_store.py.

This module was previously at 0.0% line / 0.0% branch coverage despite being
a multi-worker-safe rate-limit bucket store used by app/security/
captcha_guard.py (and potentially other guards) to share hit counters across
Gunicorn/Waitress worker processes.

These are real behavioural tests against the actual file-backed JSON store
(no Redis server required -- SECURITY_RATE_LIMIT_BACKEND defaults to "file"),
run inside a genuine Flask app context via the shared `app` fixture from
tests/conftest.py (create_app()-based, same pattern used throughout
tests/security/, e.g. test_https_scheme_and_hsts_hardening.py). Each test
points SECURITY_RATE_LIMIT_FILE at a fresh tmp_path so tests never share
state and never touch a real LOG_FOLDER.

A dedicated Redis-unreachable test proves the documented fallback: when
SECURITY_RATE_LIMIT_BACKEND="redis" is configured but no server answers,
_redis_client()'s `except Exception` branch must swallow the connection
failure and record_bucket_hit()/read_bucket_count() must silently continue
via the file-backed path -- not crash, not return a false "not rate limited"
signal because of an unrelated infra failure.
"""
from __future__ import annotations

import json
import time

import pytest

from app.security import rate_limit_store as rls


def _configure_file_backend(app, monkeypatch, tmp_path, **overrides):
    """Point the module at an isolated, per-test file-backed store.

    Mirrors the config keys config.py actually wires
    (SECURITY_RATE_LIMIT_BACKEND / _SHARED / _FILE / _REDIS_URL --
    see config.py lines ~625-628) rather than inventing new ones.
    """
    store_path = tmp_path / "security_rate_limits.json"
    config = {
        "SECURITY_RATE_LIMIT_BACKEND": "file",
        "SECURITY_RATE_LIMIT_SHARED": True,
        "SECURITY_RATE_LIMIT_FILE": str(store_path),
        "SECURITY_RATE_LIMIT_REDIS_URL": "",
        "REDIS_URL": "",
        "CACHE_REDIS_URL": "",
    }
    config.update(overrides)
    for key, value in config.items():
        monkeypatch.setitem(app.config, key, value)
    return store_path


# ---------------------------------------------------------------------------
# Basic hit accounting
# ---------------------------------------------------------------------------


def test_first_hit_on_fresh_bucket_not_blocked_count_one(app, monkeypatch, tmp_path):
    _configure_file_backend(app, monkeypatch, tmp_path)
    with app.app_context():
        result = rls.record_bucket_hit("bucket:first", window_seconds=60, limit=5)
    assert result == (1, False, 0)


def test_repeated_hits_accumulate_count_correctly(app, monkeypatch, tmp_path):
    _configure_file_backend(app, monkeypatch, tmp_path)
    counts: list[int] = []
    with app.app_context():
        for _ in range(4):
            result = rls.record_bucket_hit("bucket:repeat", window_seconds=60, limit=100)
            assert result is not None
            counts.append(result[0])
    assert counts == [1, 2, 3, 4]


def test_hit_count_below_limit_is_not_blocked(app, monkeypatch, tmp_path):
    _configure_file_backend(app, monkeypatch, tmp_path)
    with app.app_context():
        result = None
        for _ in range(2):
            result = rls.record_bucket_hit("bucket:below-limit", window_seconds=60, limit=5)
    assert result is not None
    assert result[0] == 2
    assert result[1] is False
    assert result[2] == 0


def test_hit_count_exactly_at_limit_is_not_blocked(app, monkeypatch, tmp_path):
    """Boundary per source: `blocked = len(rows) > max(1, int(limit))`.

    A count that equals the configured limit is NOT yet blocked -- only a
    count that exceeds it is. Do not assume `>=` without reading the source.
    """
    _configure_file_backend(app, monkeypatch, tmp_path)
    limit = 3
    with app.app_context():
        result = None
        for _ in range(limit):
            result = rls.record_bucket_hit("bucket:at-limit", window_seconds=60, limit=limit)
    assert result is not None
    assert result[0] == limit
    assert result[1] is False
    assert result[2] == 0


def test_hit_count_over_limit_is_blocked_with_retry_after(app, monkeypatch, tmp_path):
    _configure_file_backend(app, monkeypatch, tmp_path)
    limit = 3
    with app.app_context():
        result = None
        for _ in range(limit + 1):
            result = rls.record_bucket_hit("bucket:over-limit", window_seconds=60, limit=limit)
    assert result is not None
    assert result[0] == limit + 1
    assert result[1] is True
    assert result[2] >= 1


def test_limit_zero_floors_to_one_first_hit_allowed_second_blocked(app, monkeypatch, tmp_path):
    """`max(1, int(limit))` floors limit=0 (or negative) to 1, so the first
    hit is still allowed and only the second one blocks."""
    _configure_file_backend(app, monkeypatch, tmp_path)
    with app.app_context():
        first = rls.record_bucket_hit("bucket:zero-limit", window_seconds=60, limit=0)
        second = rls.record_bucket_hit("bucket:zero-limit", window_seconds=60, limit=0)
    assert first == (1, False, 0)
    assert second is not None
    assert second[0] == 2
    assert second[1] is True


# ---------------------------------------------------------------------------
# Window expiry
# ---------------------------------------------------------------------------


def test_window_expiry_old_entries_excluded_from_current_window(app, monkeypatch, tmp_path):
    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    bucket = "bucket:expired-only"
    hashed = rls._hash_bucket(bucket)
    old_ts = time.time() - 999  # far outside any short test window
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps({hashed: [old_ts]}), encoding="utf-8")
    with app.app_context():
        result = rls.read_bucket_count(bucket, window_seconds=5)
    assert result == (0, 0)


def test_window_expiry_then_new_hit_starts_a_fresh_count(app, monkeypatch, tmp_path):
    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    bucket = "bucket:expired-then-hit"
    hashed = rls._hash_bucket(bucket)
    old_ts = time.time() - 999
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps({hashed: [old_ts, old_ts]}), encoding="utf-8")
    with app.app_context():
        result = rls.record_bucket_hit(bucket, window_seconds=5, limit=10)
    # both stale rows must be pruned before the new hit is appended
    assert result == (1, False, 0)


# ---------------------------------------------------------------------------
# clear_buckets / isolation
# ---------------------------------------------------------------------------


def test_clear_buckets_removes_state(app, monkeypatch, tmp_path):
    _configure_file_backend(app, monkeypatch, tmp_path)
    bucket = "bucket:to-clear"
    with app.app_context():
        rls.record_bucket_hit(bucket, window_seconds=60, limit=10)
        rls.record_bucket_hit(bucket, window_seconds=60, limit=10)
        before = rls.read_bucket_count(bucket, window_seconds=60)
        cleared = rls.clear_buckets([bucket])
        after = rls.read_bucket_count(bucket, window_seconds=60)
    assert before is not None
    assert before[0] == 2
    assert cleared is True
    assert after == (0, 0)


def test_different_bucket_keys_are_isolated(app, monkeypatch, tmp_path):
    _configure_file_backend(app, monkeypatch, tmp_path)
    with app.app_context():
        for _ in range(3):
            rls.record_bucket_hit("bucket:A", window_seconds=60, limit=10)
        rls.record_bucket_hit("bucket:B", window_seconds=60, limit=10)
        count_a = rls.read_bucket_count("bucket:A", 60)
        count_b = rls.read_bucket_count("bucket:B", 60)
    assert count_a is not None
    assert count_b is not None
    assert count_a[0] == 3
    assert count_b[0] == 1


# ---------------------------------------------------------------------------
# shared_store_enabled() / disabled-store graceful None behaviour
# ---------------------------------------------------------------------------


def test_shared_store_enabled_by_default(app, monkeypatch, tmp_path):
    _configure_file_backend(app, monkeypatch, tmp_path)
    with app.app_context():
        assert rls.shared_store_enabled() is True


@pytest.mark.parametrize("backend_value", ["off", "memory", "local", "0", "false"])
def test_shared_store_enabled_false_when_backend_explicitly_disabled(
    app, monkeypatch, tmp_path, backend_value
):
    _configure_file_backend(app, monkeypatch, tmp_path, SECURITY_RATE_LIMIT_BACKEND=backend_value)
    with app.app_context():
        assert rls.shared_store_enabled() is False
        assert rls.record_bucket_hit("bucket:disabled", window_seconds=60, limit=5) is None
        assert rls.read_bucket_count("bucket:disabled", 60) is None
        assert rls._with_payload(lambda payload: True) is None


def test_shared_store_enabled_false_when_shared_flag_explicitly_off(app, monkeypatch, tmp_path):
    _configure_file_backend(app, monkeypatch, tmp_path, SECURITY_RATE_LIMIT_SHARED=False)
    with app.app_context():
        assert rls.shared_store_enabled() is False
        assert rls.record_bucket_hit("bucket:disabled-shared-flag", window_seconds=60, limit=5) is None


def test_shared_store_shared_flag_none_falls_back_to_safe_default_true(app, monkeypatch, tmp_path):
    """_truthy()'s `value in {None, ""}` branch: an explicitly None/empty
    SECURITY_RATE_LIMIT_SHARED value must fall back to the safe default
    (True), not be silently treated as falsy/disabled."""
    _configure_file_backend(app, monkeypatch, tmp_path, SECURITY_RATE_LIMIT_SHARED=None)
    with app.app_context():
        assert rls.shared_store_enabled() is True


def test_store_path_falls_back_to_log_folder_when_file_not_configured(app, monkeypatch, tmp_path):
    """When SECURITY_RATE_LIMIT_FILE is unset/blank, _store_path() must fall
    back to `<LOG_FOLDER>/security_rate_limits.json`, per the module
    docstring's documented contract."""
    monkeypatch.setitem(app.config, "SECURITY_RATE_LIMIT_BACKEND", "file")
    monkeypatch.setitem(app.config, "SECURITY_RATE_LIMIT_SHARED", True)
    monkeypatch.setitem(app.config, "SECURITY_RATE_LIMIT_FILE", "")
    monkeypatch.setitem(app.config, "LOG_FOLDER", str(tmp_path))
    with app.app_context():
        resolved = rls._store_path()
    assert resolved == tmp_path / "security_rate_limits.json"


# ---------------------------------------------------------------------------
# Malformed / corrupt JSON on disk
# ---------------------------------------------------------------------------


def test_read_payload_malformed_json_returns_empty_dict_not_crash(app, monkeypatch, tmp_path):
    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text("{not valid json!!", encoding="utf-8")
    with app.app_context():
        payload = rls._read_payload(store_path)
    assert payload == {}


def test_record_bucket_hit_self_heals_a_corrupt_store_file(app, monkeypatch, tmp_path):
    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text("]] this is not json [[", encoding="utf-8")
    with app.app_context():
        result = rls.record_bucket_hit("bucket:corrupt-file", window_seconds=60, limit=5)
    assert result == (1, False, 0)
    # the corrupt file must have been overwritten with valid JSON
    payload = json.loads(store_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)


def test_read_payload_non_dict_json_returns_empty_dict(app, monkeypatch, tmp_path):
    """A JSON array (valid JSON, wrong shape) must also be rejected safely,
    not just outright-invalid JSON text."""
    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with app.app_context():
        payload = rls._read_payload(store_path)
    assert payload == {}


def test_read_payload_skips_keys_whose_value_is_not_a_list(app, monkeypatch, tmp_path):
    """A payload entry whose value is not a list at all (e.g. a string or a
    nested object, from a hand-edited or otherwise corrupted store file)
    must be skipped for that key, not crash the whole read."""
    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    good_hashed = rls._hash_bucket("bucket:good")
    bad_hashed = rls._hash_bucket("bucket:bad-shape")
    now = time.time()
    store_path.write_text(
        json.dumps({good_hashed: [now], bad_hashed: "not-a-list"}), encoding="utf-8"
    )
    with app.app_context():
        payload = rls._read_payload(store_path)
    assert payload[good_hashed] == [now]
    assert bad_hashed not in payload


def test_read_payload_drops_non_numeric_entries_but_keeps_valid_rows(app, monkeypatch, tmp_path):
    """_read_payload coerces each row to float and silently drops entries
    that cannot be coerced, instead of discarding the whole bucket."""
    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    hashed = rls._hash_bucket("bucket:mixed")
    now = time.time()
    store_path.write_text(
        json.dumps({hashed: [now, "not-a-number", None, now - 1]}), encoding="utf-8"
    )
    with app.app_context():
        payload = rls._read_payload(store_path)
    assert payload[hashed] == [now, now - 1]


# ---------------------------------------------------------------------------
# Redis configured but unreachable -> graceful fallback to file store
# ---------------------------------------------------------------------------


def test_redis_client_unreachable_returns_none(app, monkeypatch, tmp_path):
    pytest.importorskip("redis")
    _configure_file_backend(
        app,
        monkeypatch,
        tmp_path,
        SECURITY_RATE_LIMIT_BACKEND="redis",
        SECURITY_RATE_LIMIT_REDIS_URL="redis://127.0.0.1:6399/0",
        REDIS_CONNECT_TIMEOUT=0.2,
        REDIS_SOCKET_TIMEOUT=0.2,
    )
    with app.app_context():
        client = rls._redis_client()
    assert client is None


def test_redis_backend_unreachable_falls_back_to_file_store(app, monkeypatch, tmp_path):
    pytest.importorskip("redis")
    store_path = _configure_file_backend(
        app,
        monkeypatch,
        tmp_path,
        SECURITY_RATE_LIMIT_BACKEND="redis",
        SECURITY_RATE_LIMIT_REDIS_URL="redis://127.0.0.1:6399/0",
        REDIS_CONNECT_TIMEOUT=0.2,
        REDIS_SOCKET_TIMEOUT=0.2,
    )
    with app.app_context():
        result = rls.record_bucket_hit("bucket:redis-fallback", window_seconds=60, limit=5)
        readback = rls.read_bucket_count("bucket:redis-fallback", 60)
    assert result == (1, False, 0)
    assert readback is not None
    assert readback[0] == 1
    assert store_path.exists()  # proves the fallback actually persisted to disk


def test_acquire_lock_times_out_and_returns_none_when_lock_held_by_another_process(
    app, monkeypatch, tmp_path
):
    """A fresh (not stale) .lock file already present means some other
    process/worker currently holds it -- _acquire_lock must keep retrying
    (FileExistsError branch) until its deadline, then give up with None
    rather than blocking forever or silently corrupting the store."""
    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    lock_path = store_path.with_suffix(store_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("held-by-another-worker", encoding="utf-8")
    try:
        with app.app_context():
            result = rls._acquire_lock(store_path, timeout_seconds=0.2)
        assert result is None
    finally:
        lock_path.unlink(missing_ok=True)


def test_acquire_lock_recovers_a_stale_lock_left_by_a_crashed_process(app, monkeypatch, tmp_path):
    """A .lock file older than 10 seconds is treated as abandoned (e.g. a
    worker crashed while holding it) -- _acquire_lock must remove it and
    successfully acquire a fresh lock instead of deadlocking forever."""
    import os as _os

    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    lock_path = store_path.with_suffix(store_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("stale-lock-from-crashed-worker", encoding="utf-8")
    stale_mtime = time.time() - 30  # well past the 10-second staleness cutoff
    _os.utime(lock_path, (stale_mtime, stale_mtime))
    try:
        with app.app_context():
            acquired = rls._acquire_lock(store_path, timeout_seconds=1.5)
        assert acquired == lock_path
        assert lock_path.exists()
        # confirm it is genuinely a fresh lock (recreated, not the stale text)
        assert lock_path.read_text(encoding="utf-8") != "stale-lock-from-crashed-worker"
    finally:
        lock_path.unlink(missing_ok=True)


def test_with_payload_returns_none_when_lock_cannot_be_acquired_in_time(app, monkeypatch, tmp_path):
    """End-to-end: when another process holds a fresh (non-stale) .lock file,
    _with_payload() (and therefore record_bucket_hit()) must give up
    gracefully with None once _acquire_lock()'s default deadline passes,
    rather than blocking forever or raising. This is the real caller-facing
    path a lock-timeout takes (as opposed to calling _acquire_lock()
    directly), so it is worth the ~1.5s default-timeout runtime cost."""
    store_path = _configure_file_backend(app, monkeypatch, tmp_path)
    lock_path = store_path.with_suffix(store_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("held-by-another-worker", encoding="utf-8")
    try:
        with app.app_context():
            result = rls.record_bucket_hit("bucket:lock-contended", window_seconds=60, limit=5)
        assert result is None
    finally:
        lock_path.unlink(missing_ok=True)


def test_redis_backend_without_url_configured_never_attempts_redis(app, monkeypatch, tmp_path):
    """backend='redis' with no URL anywhere must short-circuit to None
    before ever importing/constructing a redis client, then still work via
    the file-backed fallback."""
    _configure_file_backend(
        app,
        monkeypatch,
        tmp_path,
        SECURITY_RATE_LIMIT_BACKEND="redis",
        SECURITY_RATE_LIMIT_REDIS_URL="",
        REDIS_URL="",
        CACHE_REDIS_URL="",
    )
    with app.app_context():
        assert rls._redis_client() is None
        result = rls.record_bucket_hit("bucket:no-redis-url", window_seconds=60, limit=5)
    assert result == (1, False, 0)
