from __future__ import annotations


import logging

"""Multi-worker rate-limit store for BYS360 security guards.

The old in-memory bucket dictionaries were safe for a single process, but
Gunicorn/Waitress deployments can run more than one worker.  This module keeps
the same lightweight behaviour while allowing all workers on the same server to
share counters through a small JSON file under LOG_FOLDER.

No database migration is required.  If the file store cannot be used for any
reason, callers can continue with their in-process fallback.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Callable, Iterable

from flask import current_app
logger = logging.getLogger(__name__)

_REDIS_CLIENT = None
_REDIS_CLIENT_KEY: str | None = None


def _redis_url() -> str:
    return str(current_app.config.get("SECURITY_RATE_LIMIT_REDIS_URL", "") or current_app.config.get("REDIS_URL", "") or current_app.config.get("CACHE_REDIS_URL", "") or "").strip()


def _redis_client():
    global _REDIS_CLIENT, _REDIS_CLIENT_KEY
    backend = str(current_app.config.get("SECURITY_RATE_LIMIT_BACKEND", "file") or "file").strip().lower()
    if backend != "redis":
        return None
    url = _redis_url()
    if not url:
        return None
    if _REDIS_CLIENT is not None and _REDIS_CLIENT_KEY == url:
        return _REDIS_CLIENT
    try:
        import redis  # type: ignore
        client = redis.Redis.from_url(url, socket_connect_timeout=float(current_app.config.get("REDIS_CONNECT_TIMEOUT", 1.0) or 1.0), socket_timeout=float(current_app.config.get("REDIS_SOCKET_TIMEOUT", 1.0) or 1.0), decode_responses=True)
        client.ping()
    except Exception as exc:
        logger.exception("BYS360 critical exception captured in app/security/rate_limit_store.py", exc_info=exc)
        return None
    _REDIS_CLIENT = client
    _REDIS_CLIENT_KEY = url
    return client


def _redis_rate_key(bucket: str) -> str:
    prefix = str(current_app.config.get("CACHE_KEY_PREFIX", "bys360") or "bys360").strip().strip(":") or "bys360"
    return f"{prefix}:rate:{_hash_bucket(bucket)}"


def _truthy(value: object, default: bool = False) -> bool:
    if value in {None, ""}:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "file", "shared"}


def shared_store_enabled() -> bool:
    backend = str(current_app.config.get("SECURITY_RATE_LIMIT_BACKEND", "file") or "file").strip().lower()
    if backend in {"0", "false", "off", "memory", "local"}:
        return False
    return _truthy(current_app.config.get("SECURITY_RATE_LIMIT_SHARED", True), True)


def _store_path() -> Path:
    configured = str(current_app.config.get("SECURITY_RATE_LIMIT_FILE", "") or "").strip()
    if configured:
        return Path(configured)
    log_folder = Path(str(current_app.config.get("LOG_FOLDER", "logs") or "logs"))
    return log_folder / "security_rate_limits.json"


def _hash_bucket(bucket: str) -> str:
    return hashlib.sha256(str(bucket or "").encode("utf-8", "ignore")).hexdigest()


def _read_payload(path: Path) -> dict[str, list[float]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    except Exception as exc:
        logger.exception("BYS360 critical exception captured in app/security/rate_limit_store.py", exc_info=exc)
        return {}
    if not isinstance(payload, dict):
        return {}
    clean: dict[str, list[float]] = {}
    for key, values in payload.items():
        if not isinstance(values, list):
            continue
        rows: list[float] = []
        for value in values:
            try:
                rows.append(float(value))
            except (TypeError, ValueError):
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/security/rate_limit_store.py:99)")
                continue
        clean[str(key)] = rows
    return clean


def _write_payload(path: Path, payload: dict[str, list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def _acquire_lock(path: Path, timeout_seconds: float = 1.5) -> Path | None:
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max(0.1, float(timeout_seconds))
    while time.time() < deadline:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii", "ignore"))
            os.close(fd)
            return lock_path
        except FileExistsError:
            try:
                if time.time() - lock_path.stat().st_mtime > 10:
                    lock_path.unlink(missing_ok=True)
                    continue
            except OSError:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/security/rate_limit_store.py)")
            time.sleep(0.03)
        except OSError:
            return None
    return None


def _with_payload(mutator: Callable[[dict[str, list[float]]], object]) -> object | None:
    if not shared_store_enabled():
        return None
    path = _store_path()
    lock_path = _acquire_lock(path)
    if lock_path is None:
        return None
    try:
        payload = _read_payload(path)
        result = mutator(payload)
        _write_payload(path, payload)
        return result
    except Exception as exc:
        logger.exception("BYS360 critical exception captured in app/security/rate_limit_store.py", exc_info=exc)
        return None
    finally:
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/security/rate_limit_store.py)")


def read_bucket_count(bucket: str, window_seconds: int) -> tuple[int, int] | None:
    now = time.time()
    cutoff = now - max(1, int(window_seconds))

    client = _redis_client()
    if client is not None:
        try:
            key = _redis_rate_key(bucket)
            client.zremrangebyscore(key, 0, cutoff)
            count = int(client.zcard(key) or 0)
            if not count:
                return 0, 0
            oldest = client.zrange(key, 0, 0, withscores=True)
            first_score = float(oldest[0][1]) if oldest else now
            retry_after = max(1, int(max(1, int(window_seconds)) - (now - first_score)))
            client.expire(key, max(1, int(window_seconds)))
            return count, retry_after
        except Exception as exc:
            logger.exception("BYS360 critical exception captured in app/security/rate_limit_store.py", exc_info=exc)
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/security/rate_limit_store.py)")

    hashed = _hash_bucket(bucket)

    def mutator(payload: dict[str, list[float]]) -> tuple[int, int]:
        rows = [ts for ts in payload.get(hashed, []) if ts >= cutoff]
        payload[hashed] = rows
        if not rows:
            return 0, 0
        retry_after = max(1, int(max(1, int(window_seconds)) - (now - rows[0])))
        return len(rows), retry_after

    result = _with_payload(mutator)
    return result if isinstance(result, tuple) else None


def record_bucket_hit(bucket: str, *, window_seconds: int, limit: int) -> tuple[int, bool, int] | None:
    now = time.time()
    cutoff = now - max(1, int(window_seconds))

    client = _redis_client()
    if client is not None:
        try:
            key = _redis_rate_key(bucket)
            member = f"{now:.6f}:{os.getpid()}"
            pipe = client.pipeline()
            pipe.zremrangebyscore(key, 0, cutoff)
            pipe.zadd(key, {member: now})
            pipe.zcard(key)
            pipe.zrange(key, 0, 0, withscores=True)
            pipe.expire(key, max(1, int(window_seconds)))
            result = pipe.execute()
            count = int(result[2] or 0)
            oldest = result[3] or []
            first_score = float(oldest[0][1]) if oldest else now
            blocked = count > max(1, int(limit))
            retry_after = max(1, int(max(1, int(window_seconds)) - (now - first_score))) if blocked else 0
            return count, blocked, retry_after
        except Exception as exc:
            logger.exception("BYS360 critical exception captured in app/security/rate_limit_store.py", exc_info=exc)
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/security/rate_limit_store.py)")

    hashed = _hash_bucket(bucket)

    def mutator(payload: dict[str, list[float]]) -> tuple[int, bool, int]:
        rows = [ts for ts in payload.get(hashed, []) if ts >= cutoff]
        rows.append(now)
        payload[hashed] = rows
        blocked = len(rows) > max(1, int(limit))
        retry_after = 0
        if blocked and rows:
            retry_after = max(1, int(max(1, int(window_seconds)) - (now - rows[0])))
        return len(rows), blocked, retry_after

    result = _with_payload(mutator)
    return result if isinstance(result, tuple) else None


def clear_buckets(buckets: Iterable[str]) -> bool:
    bucket_list = list(buckets)
    cleared = False
    client = _redis_client()
    if client is not None:
        try:
            keys = [_redis_rate_key(bucket) for bucket in bucket_list]
            if keys:
                cleared = bool(client.delete(*keys)) or cleared
        except Exception as exc:
            logger.exception("BYS360 critical exception captured in app/security/rate_limit_store.py", exc_info=exc)
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/security/rate_limit_store.py)")

    hashed_keys = {_hash_bucket(bucket) for bucket in bucket_list}

    def mutator(payload: dict[str, list[float]]) -> bool:
        for key in hashed_keys:
            payload.pop(key, None)
        return True

    return bool(_with_payload(mutator)) or cleared
