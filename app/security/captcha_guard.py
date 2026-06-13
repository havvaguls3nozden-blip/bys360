from __future__ import annotations


import logging

from app.core.datetime_utils import utc_now
import random
from datetime import datetime, timedelta
from flask import current_app, request

from app.security.rate_limit_store import (
    clear_buckets as _shared_clear_buckets,
    read_bucket_count as _shared_read_bucket_count,
    record_bucket_hit as _shared_record_bucket_hit,
)
logger = logging.getLogger(__name__)

_FAILED_LOGIN_CACHE: dict[str, list[datetime]] = {}


def _threshold() -> int:
    try:
        return int(current_app.config.get("LOGIN_MAX_FAILS_BEFORE_CAPTCHA", 3))
    except Exception as exc:
        logger.exception("BYS360 critical exception captured in app/security/captcha_guard.py", exc_info=exc)
        return 3


def get_client_key() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    ip = forwarded or request.remote_addr or "unknown"
    ua = (request.headers.get("User-Agent") or "")[:120]
    return f"{ip}|{ua}"


def _prune(client_key: str, window_minutes: int = 30) -> list[datetime]:
    now = utc_now()
    window_start = now - timedelta(minutes=window_minutes)
    rows = [ts for ts in _FAILED_LOGIN_CACHE.get(client_key, []) if ts >= window_start]
    _FAILED_LOGIN_CACHE[client_key] = rows
    return rows


def record_failed_login_attempt(client_key: str) -> int:
    shared = _shared_record_bucket_hit(
        f"captcha:{client_key}",
        window_seconds=30 * 60,
        limit=max(_threshold(), 1),
    )
    if shared is not None:
        return int(shared[0])

    rows = _prune(client_key)
    rows.append(utc_now())
    _FAILED_LOGIN_CACHE[client_key] = rows
    return len(rows)


def clear_failed_login_attempts(client_key: str) -> None:
    _shared_clear_buckets((f"captcha:{client_key}",))
    _FAILED_LOGIN_CACHE.pop(client_key, None)


def is_captcha_required(client_key: str) -> bool:
    shared = _shared_read_bucket_count(f"captcha:{client_key}", 30 * 60)
    enabled = bool(current_app.config.get("CAPTCHA_ENABLED", True))
    if shared is not None:
        return enabled and int(shared[0]) >= _threshold()

    rows = _prune(client_key)
    return enabled and len(rows) >= _threshold()


def generate_simple_captcha() -> tuple[str, str]:
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    question = f"{a} + {b} = ?"
    return question, str(a + b)


def verify_simple_captcha(answer: str, expected: str) -> bool:
    return str(answer or "").strip() == str(expected or "").strip()