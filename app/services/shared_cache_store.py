from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import suppress
from copy import deepcopy
from pathlib import Path
from typing import Any

from flask import current_app, has_app_context

"""Shared JSON cache adapter for BYS360.

Redis is used when configured.  If Redis is missing or temporarily unavailable,
workers on the same server share a locked JSON file.  Memory is only the final
fallback for local development.
"""

_MEMORY_CACHE: dict[str, tuple[float, Any]] = {}
_REDIS_CLIENT: Any | None = None
_REDIS_CLIENT_KEY: str | None = None


def _cfg(name: str, default: Any = None) -> Any:
    if has_app_context():
        return current_app.config.get(name, default)
    return os.getenv(name, default)


def backend_name() -> str:
    raw = str(_cfg("CACHE_BACKEND", "") or "").strip().lower()
    if raw:
        return raw
    return "redis" if str(_cfg("CACHE_REDIS_URL", "") or _cfg("REDIS_URL", "") or "").strip() else "file"


def _key_prefix() -> str:
    return str(_cfg("CACHE_KEY_PREFIX", "bys360") or "bys360").strip().strip(":") or "bys360"


def _redis_url() -> str:
    return str(_cfg("CACHE_REDIS_URL", "") or _cfg("REDIS_URL", "") or "").strip()


def _redis_client() -> Any | None:
    global _REDIS_CLIENT, _REDIS_CLIENT_KEY
    if backend_name() != "redis":
        return None
    url = _redis_url()
    if not url:
        return None
    if _REDIS_CLIENT is not None and url == _REDIS_CLIENT_KEY:
        return _REDIS_CLIENT
    try:
        import redis  # type: ignore
        client = redis.Redis.from_url(
            url,
            socket_connect_timeout=float(_cfg("REDIS_CONNECT_TIMEOUT", 1.0) or 1.0),
            socket_timeout=float(_cfg("REDIS_SOCKET_TIMEOUT", 1.0) or 1.0),
            decode_responses=True,
        )
        client.ping()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None
    _REDIS_CLIENT = client
    _REDIS_CLIENT_KEY = url
    return client


def _full_key(key: str) -> str:
    return f"{_key_prefix()}:cache:{key}"


def _safe_file_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8", "ignore")).hexdigest()


def _file_path() -> Path:
    configured = str(_cfg("CACHE_FILE", "") or "").strip()
    if configured:
        return Path(configured)
    return Path(str(_cfg("LOG_FOLDER", "logs") or "logs")) / "shared_cache.json"


def _read_file(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_file(path: Path, payload: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def _lock(path: Path, timeout_seconds: float = 1.5) -> Path | None:
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii", "ignore"))
            os.close(fd)
            return lock_path
        except FileExistsError:
            with suppress(OSError):
                if time.time() - lock_path.stat().st_mtime > 10:
                    lock_path.unlink(missing_ok=True)
                    continue
            time.sleep(0.03)
        except OSError:
            return None
    return None


def _with_file(mutator):
    path = _file_path()
    lock_path = _lock(path)
    if lock_path is None:
        return None
    try:
        payload = _read_file(path)
        now = time.time()
        for key, row in list(payload.items()):
            if isinstance(row, dict) and float(row.get("expires_at") or 0) <= now:
                payload.pop(key, None)
        result = mutator(payload)
        _write_file(path, payload)
        return result
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None
    finally:
        with suppress(OSError):
            lock_path.unlink(missing_ok=True)


def get_json(key: str) -> Any | None:
    raw_key = str(key or "").strip()
    if not raw_key:
        return None
    client = _redis_client()
    if client is not None:
        try:
            raw = client.get(_full_key(raw_key))
            return json.loads(raw) if raw else None
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/shared_cache_store.py")
    file_key = _safe_file_key(raw_key)
    result = _with_file(lambda payload: deepcopy(payload.get(file_key, {}).get("value")) if isinstance(payload.get(file_key), dict) else None)
    if result is not None:
        return result
    row = _MEMORY_CACHE.get(raw_key)
    if not row:
        return None
    expires_at, value = row
    if expires_at and expires_at <= time.monotonic():
        _MEMORY_CACHE.pop(raw_key, None)
        return None
    return deepcopy(value)


def set_json(key: str, value: Any, ttl_seconds: int = 60) -> bool:
    raw_key = str(key or "").strip()
    if not raw_key:
        return False
    ttl = max(1, int(ttl_seconds or 60))
    client = _redis_client()
    if client is not None:
        try:
            client.setex(_full_key(raw_key), ttl, json.dumps(value, ensure_ascii=False, default=str))
            return True
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/shared_cache_store.py")
    file_key = _safe_file_key(raw_key)
    def mutator(payload):
        payload[file_key] = {"key": raw_key, "expires_at": time.time() + ttl, "value": deepcopy(value)}
        return True
    if _with_file(mutator):
        return True
    _MEMORY_CACHE[raw_key] = (time.monotonic() + ttl, deepcopy(value))
    return True


def delete_prefix(prefix: str) -> int:
    raw_prefix = str(prefix or "").strip()
    if not raw_prefix:
        return 0
    removed = 0
    client = _redis_client()
    if client is not None:
        redis_prefix = _full_key(raw_prefix)
        try:
            cursor = 0
            while True:
                cursor, keys = client.scan(cursor=cursor, match=f"{redis_prefix}*", count=250)
                if keys:
                    removed += int(client.delete(*keys))
                if cursor == 0:
                    break
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/shared_cache_store.py")
    def mutator(payload):
        count = 0
        for file_key, row in list(payload.items()):
            if isinstance(row, dict) and str(row.get("key") or "").startswith(raw_prefix):
                payload.pop(file_key, None)
                count += 1
        return count
    file_removed = _with_file(mutator)
    if isinstance(file_removed, int):
        removed += file_removed
    for key in list(_MEMORY_CACHE.keys()):
        if key.startswith(raw_prefix):
            _MEMORY_CACHE.pop(key, None)
            removed += 1
    return removed


__all__ = ["backend_name", "get_json", "set_json", "delete_prefix"]
