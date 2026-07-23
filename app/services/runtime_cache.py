from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from threading import RLock
from typing import Any

try:
    from flask import current_app, has_app_context
except Exception:  # pragma: no cover
    current_app = None

    def has_app_context() -> bool:
        return False

try:
    import redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore

"""BYS360 runtime cache servisi.

Faz 4 ile Redis destekli hale getirildi. Redis yoksa veya bağlantı kurulamazsa
uygulama düşmez; mevcut bellek içi cache davranışı devam eder.
"""

# BYS360_MAINTENANCE_ROADMAP_PHASE4_SCALABILITY_PERFORMANCE_RUNTIME_CACHE
_CACHE: dict[str, tuple[float, Any]] = {}
_LOCK = RLock()
_REDIS_CLIENT: Any = None
_REDIS_CLIENT_READY = False
_REDIS_LAST_ERROR_AT = 0.0


def _config_value(name: str, default: Any = None) -> Any:
    if has_app_context() and current_app is not None:
        try:
            return current_app.config.get(name, os.getenv(name, default))
        except Exception:
            return os.getenv(name, default)
    return os.getenv(name, default)


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(str(value or '').strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _redis_url() -> str:
    return str(_config_value('CACHE_REDIS_URL', os.getenv('REDIS_URL', '')) or '').strip()


def _backend() -> str:
    backend = str(_config_value('RUNTIME_CACHE_BACKEND', 'redis' if _redis_url() else 'memory') or 'memory').strip().lower()
    if backend not in {'redis', 'memory', 'off'}:
        backend = 'memory'
    return backend


def _client():
    global _REDIS_CLIENT, _REDIS_CLIENT_READY, _REDIS_LAST_ERROR_AT
    if _backend() != 'redis' or redis is None:
        return None
    url = _redis_url()
    if not url:
        return None
    now = time.time()
    if _REDIS_CLIENT is not None and _REDIS_CLIENT_READY:
        return _REDIS_CLIENT
    if _REDIS_LAST_ERROR_AT and now - _REDIS_LAST_ERROR_AT < 15:
        return None
    try:
        _REDIS_CLIENT = redis.Redis.from_url(url, decode_responses=True, socket_timeout=1.0, socket_connect_timeout=1.0)
        _REDIS_CLIENT.ping()
        _REDIS_CLIENT_READY = True
        return _REDIS_CLIENT
    except Exception:
        _REDIS_LAST_ERROR_AT = now
        _REDIS_CLIENT_READY = False
        _REDIS_CLIENT = None
        return None


def _safe_key(key: str) -> str:
    raw = str(key or '').strip()
    if not raw:
        raw = 'empty'
    prefix = str(_config_value('CACHE_KEY_PREFIX', 'bys360') or 'bys360').strip() or 'bys360'
    if raw.startswith(prefix + ':'):
        return raw
    return f'{prefix}:{raw}'


def get(key: str, default: Any = None) -> Any:
    if _backend() == 'off':
        return default
    safe_key = _safe_key(key)
    client = _client()
    if client is not None:
        try:
            raw = client.get(safe_key)
            if raw is None:
                return default
            return json.loads(raw)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/runtime_cache.py")
    now = time.time()
    with _LOCK:
        row = _CACHE.get(safe_key)
        if not row:
            return default
        expires_at, value = row
        if expires_at and expires_at < now:
            _CACHE.pop(safe_key, None)
            return default
        return value


def set(key: str, value: Any, ttl_seconds: int = 30) -> Any:
    if _backend() == 'off':
        return value
    ttl = max(_positive_int(ttl_seconds, _positive_int(_config_value('CACHE_DEFAULT_TTL', 30), 30)), 1)
    safe_key = _safe_key(key)
    client = _client()
    if client is not None:
        try:
            client.setex(safe_key, ttl, json.dumps(value, ensure_ascii=False, default=str))
            return value
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/runtime_cache.py")
    expires_at = time.time() + ttl if ttl else 0
    with _LOCK:
        _CACHE[safe_key] = (expires_at, value)
    return value


def get_or_set(key: str, factory: Callable[[], Any], ttl_seconds: int = 30) -> Any:
    marker = object()
    cached = get(key, default=marker)
    if cached is not marker:
        return cached
    value = factory()
    set(key, value, ttl_seconds=ttl_seconds)
    return value


def invalidate(key: str) -> None:
    safe_key = _safe_key(key)
    client = _client()
    if client is not None:
        try:
            client.delete(safe_key)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/runtime_cache.py")
    with _LOCK:
        _CACHE.pop(safe_key, None)


def invalidate_prefix(prefix: str) -> None:
    raw_prefix = _safe_key(prefix).rstrip('*')
    client = _client()
    if client is not None:
        try:
            cursor = 0
            pattern = f'{raw_prefix}*'
            while True:
                cursor, keys = client.scan(cursor=cursor, match=pattern, count=250)
                if keys:
                    client.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/runtime_cache.py")
    with _LOCK:
        for key in [row for row in _CACHE if str(row).startswith(raw_prefix)]:
            _CACHE.pop(key, None)


def cache_status() -> dict[str, Any]:
    client = _client()
    return {
        'backend': _backend(),
        'redis_configured': bool(_redis_url()),
        'redis_connected': bool(client is not None),
        'memory_entries': len(_CACHE),
    }
