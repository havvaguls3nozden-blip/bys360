from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Any

from flask import current_app, request

_BUCKETS: dict[str, list[float]] = defaultdict(list)
_LOG_COOLDOWNS: dict[str, float] = {}
_LOCK = Lock()

_EXACT_PROBE_PATHS = {
    '/.env',
    '/.git/config',
    '/xmlrpc.php',
    '/wp-login.php',
    '/wp-admin',
    '/phpmyadmin',
    '/pma',
    '/adminer.php',
    '/server-status',
    '/hnap1/',
}

_PROBE_PATH_PREFIXES = (
    '/.git/',
    '/.svn/',
    '/cgi-bin/',
    '/vendor/phpunit/',
    '/phpmyadmin/',
    '/pma/',
    '/boaform/',
    '/actuator/',
    '/solr/',
    '/_ignition/',
)

_MUTATING_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}


@dataclass(slots=True, frozen=True)
class GuardDecision:
    kind: str
    client_ip: str
    path: str
    method: str
    blocked: bool
    retry_after_seconds: int
    count: int
    limit: int
    should_log: bool
    bucket: str


@dataclass(slots=True, frozen=True)
class AuthThrottleState:
    allowed: bool
    retry_after_seconds: int
    ip_count: int
    ip_limit: int
    identity_count: int
    identity_limit: int


def _truthy(value: Any, default: bool = False) -> bool:
    if value in {None, ''}:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def get_client_ip() -> str:
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip() or 'unknown'
    real_ip = request.headers.get('X-Real-IP', '').strip()
    if real_ip:
        return real_ip
    return request.remote_addr or 'unknown'


def _normalize_identity(value: str | None) -> str:
    return str(value or '').strip().lower() or 'unknown'


def _prune_bucket(bucket: str, window_seconds: int, now: float | None = None) -> list[float]:
    now = now or time.time()
    cutoff = now - max(1, int(window_seconds))
    rows = [ts for ts in _BUCKETS.get(bucket, []) if ts >= cutoff]
    _BUCKETS[bucket] = rows
    return rows


def _record_hit(bucket: str, *, window_seconds: int, limit: int) -> tuple[int, bool, int]:
    now = time.time()
    with _LOCK:
        rows = _prune_bucket(bucket, window_seconds, now)
        rows.append(now)
        _BUCKETS[bucket] = rows
        blocked = len(rows) > max(1, int(limit))
        retry_after = 0
        if blocked and rows:
            retry_after = max(1, int(window_seconds - (now - rows[0])))
        return len(rows), blocked, retry_after


def _should_log(bucket: str, cooldown_seconds: int) -> bool:
    now = time.time()
    with _LOCK:
        last_seen = float(_LOG_COOLDOWNS.get(bucket, 0.0) or 0.0)
        if now - last_seen < max(1, int(cooldown_seconds)):
            return False
        _LOG_COOLDOWNS[bucket] = now
        return True


def _looks_like_probe_path(path: str) -> bool:
    normalized = str(path or '/').strip().lower() or '/'
    if normalized in _EXACT_PROBE_PATHS:
        return True
    return any(normalized.startswith(prefix) for prefix in _PROBE_PATH_PREFIXES)


def inspect_incoming_request() -> GuardDecision | None:
    if not _truthy(current_app.config.get('REQUEST_GUARD_ENABLED', True), True):
        return None

    method = str(request.method or 'GET').upper()
    path = str(request.path or '/').strip() or '/'
    client_ip = get_client_ip()
    cooldown_seconds = int(current_app.config.get('SECURITY_LOG_COOLDOWN_SECONDS', 300) or 300)

    if path == '/' and method in _MUTATING_METHODS:
        limit = int(current_app.config.get('ROOT_POST_BURST_LIMIT', 8) or 8)
        window_seconds = int(current_app.config.get('ROOT_POST_WINDOW_SECONDS', 60) or 60)
        bucket = f'root_mutation:{client_ip}'
        count, blocked, retry_after = _record_hit(bucket, window_seconds=window_seconds, limit=limit)
        return GuardDecision(
            kind='root_mutation',
            client_ip=client_ip,
            path=path,
            method=method,
            blocked=blocked,
            retry_after_seconds=retry_after,
            count=count,
            limit=limit,
            should_log=_should_log(bucket, cooldown_seconds),
            bucket=bucket,
        )

    if _looks_like_probe_path(path):
        limit = int(current_app.config.get('SUSPICIOUS_PROBE_BURST_LIMIT', 20) or 20)
        window_seconds = int(current_app.config.get('SUSPICIOUS_PROBE_WINDOW_SECONDS', 120) or 120)
        bucket = f'suspicious_probe:{client_ip}'
        count, blocked, retry_after = _record_hit(bucket, window_seconds=window_seconds, limit=limit)
        return GuardDecision(
            kind='suspicious_probe',
            client_ip=client_ip,
            path=path,
            method=method,
            blocked=blocked,
            retry_after_seconds=retry_after,
            count=count,
            limit=limit,
            should_log=_should_log(bucket, cooldown_seconds),
            bucket=bucket,
        )

    return None


def _read_bucket_count(bucket: str, window_seconds: int) -> tuple[int, int]:
    now = time.time()
    with _LOCK:
        rows = _prune_bucket(bucket, window_seconds, now)
        if not rows:
            return 0, 0
        retry_after = max(1, int(window_seconds - (now - rows[0])))
        return len(rows), retry_after


def get_auth_throttle_state(client_ip: str, identity: str | None) -> AuthThrottleState:
    if not _truthy(current_app.config.get('LOGIN_THROTTLE_ENABLED', True), True):
        return AuthThrottleState(True, 0, 0, 0, 0, 0)

    window_seconds = int(current_app.config.get('LOGIN_LOCKOUT_MINUTES', 15) or 15) * 60
    ip_limit = int(current_app.config.get('LOGIN_IP_MAX_ATTEMPTS', 12) or 12)
    identity_limit = int(current_app.config.get('LOGIN_IDENTITY_MAX_ATTEMPTS', 6) or 6)

    ip_bucket = f'auth_ip:{client_ip}'
    identity_bucket = f'auth_ident:{_normalize_identity(identity)}'

    ip_count, ip_retry = _read_bucket_count(ip_bucket, window_seconds)
    identity_count, identity_retry = _read_bucket_count(identity_bucket, window_seconds)
    retry_after = max(ip_retry, identity_retry)
    allowed = ip_count < ip_limit and identity_count < identity_limit
    return AuthThrottleState(allowed, retry_after, ip_count, ip_limit, identity_count, identity_limit)


def record_auth_failure(client_ip: str, identity: str | None) -> AuthThrottleState:
    if not _truthy(current_app.config.get('LOGIN_THROTTLE_ENABLED', True), True):
        return AuthThrottleState(True, 0, 0, 0, 0, 0)

    window_seconds = int(current_app.config.get('LOGIN_LOCKOUT_MINUTES', 15) or 15) * 60
    ip_limit = int(current_app.config.get('LOGIN_IP_MAX_ATTEMPTS', 12) or 12)
    identity_limit = int(current_app.config.get('LOGIN_IDENTITY_MAX_ATTEMPTS', 6) or 6)

    ip_bucket = f'auth_ip:{client_ip}'
    identity_bucket = f'auth_ident:{_normalize_identity(identity)}'

    ip_count, _ip_blocked, ip_retry = _record_hit(ip_bucket, window_seconds=window_seconds, limit=ip_limit)
    identity_count, _identity_blocked, identity_retry = _record_hit(identity_bucket, window_seconds=window_seconds, limit=identity_limit)

    retry_after = max(ip_retry, identity_retry)
    allowed = ip_count < ip_limit and identity_count < identity_limit
    return AuthThrottleState(allowed, retry_after, ip_count, ip_limit, identity_count, identity_limit)


def clear_auth_failures(client_ip: str, identity: str | None) -> None:
    identity_bucket = f'auth_ident:{_normalize_identity(identity)}'
    ip_bucket = f'auth_ip:{client_ip}'
    with _LOCK:
        _BUCKETS.pop(ip_bucket, None)
        _BUCKETS.pop(identity_bucket, None)


def should_log_auth_throttle(client_ip: str, identity: str | None) -> bool:
    cooldown_seconds = int(current_app.config.get('SECURITY_LOG_COOLDOWN_SECONDS', 300) or 300)
    masked_identity = mask_identity(identity)
    return _should_log(f'auth_throttle:{client_ip}:{masked_identity}', cooldown_seconds)


def mask_identity(identity: str | None) -> str:
    raw = _normalize_identity(identity)
    if raw in {'', 'unknown'}:
        return 'unknown'
    if '@' in raw:
        user, domain = raw.split('@', 1)
        if len(user) <= 2:
            masked_user = user[:1] + '*'
        else:
            masked_user = user[:2] + '*' * max(1, len(user) - 2)
        return f'{masked_user}@{domain}'
    if len(raw) <= 3:
        return raw[:1] + '*' * max(1, len(raw) - 1)
    return raw[:3] + '*' * max(1, len(raw) - 3)
