from __future__ import annotations

# BYS360_RUNTIME_PAGE_CACHE_V4



import time
from threading import RLock
from typing import Any

try:
    from flask import request, session
except Exception:  # pragma: no cover
    request = None  # type: ignore
    session = None  # type: ignore

_CACHE: dict[str, tuple[float, Any]] = {}
_LOCK = RLock()
_MAX_ITEMS = 256


def _normalize_key(key: Any) -> str:
    if isinstance(key, (tuple, list)):
        return "|".join(str(part) for part in key)
    return str(key)


def _request_allows_cache() -> bool:
    try:
        if request is not None and request.method != "GET":
            return False
        if request is not None and request.args.get("no_cache") in {"1", "true", "evet"}:
            return False
        if session is not None and session.get("_flashes"):
            return False
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return False
    return True


def bys360_get_page_cache(key: Any, ttl_seconds: int = 30) -> Any | None:
    """Kısa süreli, süreç yazmayan GET sayfaları için bellek içi güvenli cache."""
    if not _request_allows_cache():
        return None
    now = time.monotonic()
    cache_key = _normalize_key(key)
    with _LOCK:
        cached = _CACHE.get(cache_key)
        if not cached:
            return None
        expires_at, value = cached
        if expires_at < now:
            _CACHE.pop(cache_key, None)
            return None
        return value


def bys360_set_page_cache(key: Any, value: Any, ttl_seconds: int = 30) -> Any:
    if not _request_allows_cache():
        return value
    cache_key = _normalize_key(key)
    now = time.monotonic()
    with _LOCK:
        if len(_CACHE) >= _MAX_ITEMS:
            expired = [k for k, (expires_at, _v) in _CACHE.items() if expires_at < now]
            for k in expired[:64]:
                _CACHE.pop(k, None)
            if len(_CACHE) >= _MAX_ITEMS:
                for k in list(_CACHE.keys())[:64]:
                    _CACHE.pop(k, None)
        _CACHE[cache_key] = (now + max(5, int(ttl_seconds)), value)
    return value


def bys360_clear_page_cache(prefix: str | None = None) -> int:
    with _LOCK:
        if not prefix:
            count = len(_CACHE)
            _CACHE.clear()
            return count
        keys = [k for k in _CACHE if k.startswith(prefix)]
        for k in keys:
            _CACHE.pop(k, None)
        return len(keys)
