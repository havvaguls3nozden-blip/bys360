"""
BYS360 asenkron iş kuyruğu adaptörü.

Amaç:
- Mail, rapor, AI özet, sağlık snapshot ve ağır analizleri HTTP isteği içinde çalıştırmamak.
- Redis/RQ varsa gerçek kuyruğa almak.
- Geliştirme ortamında Redis yoksa kontrollü inline veya skipped davranmak.

Bu dosya Flask uygulama açılışını zorlamaz; import edildiğinde Redis'e bağlanmaz.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import importlib
import logging
import os
from typing import Any
from collections.abc import Callable, Mapping

logger = logging.getLogger(__name__)


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        value = int(str(os.getenv(name, "")).strip())
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _str_env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or default).strip()


@dataclass(slots=True)
class AsyncJobResult:
    ok: bool
    backend: str
    queued: bool = False
    inline: bool = False
    skipped: bool = False
    job_id: str | None = None
    queue_name: str | None = None
    message: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AsyncQueueUnavailable(RuntimeError):
    """Gerçek asenkron kuyruk isteniyor ama altyapı hazır değil."""


def async_tasks_enabled() -> bool:
    return _bool_env("ASYNC_TASKS_ENABLED", False)


def get_async_backend() -> str:
    configured = _str_env("ASYNC_TASK_BACKEND", "").lower()
    if configured:
        return configured
    if _str_env("ASYNC_TASK_REDIS_URL") or _str_env("REDIS_URL"):
        return "rq"
    return "inline"


def get_default_queue_name() -> str:
    return _str_env("ASYNC_TASK_QUEUE_DEFAULT", "bys360-default") or "bys360-default"


def get_redis_url() -> str:
    return _str_env("ASYNC_TASK_REDIS_URL") or _str_env("REDIS_URL")


def import_callable(path: str | Callable[..., Any]) -> Callable[..., Any]:
    if callable(path):
        return path
    if not isinstance(path, str) or "." not in path:
        raise ValueError("Görev yolu 'paket.modul.fonksiyon' biçiminde olmalıdır.")
    module_name, func_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)
    if not callable(func):
        raise TypeError(f"Görev çağrılabilir değil: {path}")
    return func


def _enqueue_rq(
    func_path: str | Callable[..., Any],
    *,
    args: tuple[Any, ...],
    kwargs: Mapping[str, Any],
    queue_name: str,
    timeout: int,
    result_ttl: int,
) -> AsyncJobResult:
    redis_url = get_redis_url()
    if not redis_url:
        raise AsyncQueueUnavailable("ASYNC_TASK_REDIS_URL veya REDIS_URL tanımlı değil.")

    try:
        from redis import Redis
        from rq import Queue
    except Exception as exc:  # pragma: no cover - opsiyonel bağımlılık
        raise AsyncQueueUnavailable(f"RQ/Redis bağımlılığı yüklenemedi: {exc}") from exc

    connection = Redis.from_url(
        redis_url,
        socket_connect_timeout=float(os.getenv("REDIS_CONNECT_TIMEOUT", "1.0") or 1.0),
        socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT", "1.0") or 1.0),
        decode_responses=False,
    )
    queue = Queue(queue_name, connection=connection, default_timeout=timeout)
    func = import_callable(func_path)
    job = queue.enqueue_call(
        func=func,
        args=args,
        kwargs=dict(kwargs),
        timeout=timeout,
        result_ttl=result_ttl,
        failure_ttl=_int_env("ASYNC_TASK_FAILURE_TTL_SECONDS", 86400),
    )
    return AsyncJobResult(
        ok=True,
        backend="rq",
        queued=True,
        job_id=str(job.id),
        queue_name=queue_name,
        message="Görev RQ kuyruğuna alındı.",
    )


def enqueue_job(
    func_path: str | Callable[..., Any],
    *args: Any,
    queue_name: str | None = None,
    timeout: int | None = None,
    result_ttl: int | None = None,
    allow_inline_fallback: bool | None = None,
    **kwargs: Any,
) -> AsyncJobResult:
    """Görevi kuyrukla.

    ASYNC_TASKS_ENABLED=false ise, geliştirme ve test ortamında güvenli şekilde inline çalışabilir.
    Production'da inline fallback kapatılarak altyapı eksikliği açıkça görünür hale getirilebilir.
    """
    backend = get_async_backend()
    queue = queue_name or get_default_queue_name()
    timeout_value = timeout or _int_env("ASYNC_TASK_TIMEOUT_SECONDS", 900)
    result_ttl_value = result_ttl or _int_env("ASYNC_TASK_RESULT_TTL_SECONDS", 3600)
    inline_fallback = _bool_env("ASYNC_TASK_INLINE_FALLBACK", True)
    if allow_inline_fallback is not None:
        inline_fallback = bool(allow_inline_fallback)

    if not async_tasks_enabled() and backend not in {"rq", "redis"}:
        if inline_fallback:
            func = import_callable(func_path)
            func(*args, **kwargs)
            return AsyncJobResult(ok=True, backend="inline", inline=True, message="ASYNC_TASKS_ENABLED kapalı; görev inline çalıştı.")
        return AsyncJobResult(ok=True, backend="disabled", skipped=True, message="Asenkron görev altyapısı kapalı; görev atlandı.")

    try:
        if backend in {"rq", "redis"}:
            return _enqueue_rq(
                func_path,
                args=args,
                kwargs=kwargs,
                queue_name=queue,
                timeout=timeout_value,
                result_ttl=result_ttl_value,
            )
        if backend == "inline":
            func = import_callable(func_path)
            func(*args, **kwargs)
            return AsyncJobResult(ok=True, backend="inline", inline=True, message="Görev inline çalıştı.")
        return AsyncJobResult(ok=False, backend=backend, error=f"Bilinmeyen async backend: {backend}")
    except Exception as exc:
        logger.exception("Asenkron görev kuyruğa alınamadı: %s", func_path)
        if inline_fallback:
            func = import_callable(func_path)
            func(*args, **kwargs)
            return AsyncJobResult(ok=True, backend="inline-fallback", inline=True, message="Kuyruk kullanılamadı; görev inline fallback ile çalıştı.", error=str(exc))
        return AsyncJobResult(ok=False, backend=backend, error=str(exc))


def queue_health() -> dict[str, Any]:
    backend = get_async_backend()
    payload: dict[str, Any] = {
        "enabled": async_tasks_enabled(),
        "backend": backend,
        "queue_name": get_default_queue_name(),
        "redis_configured": bool(get_redis_url()),
    }
    if backend in {"rq", "redis"} and get_redis_url():
        try:
            from redis import Redis
            redis_client = Redis.from_url(get_redis_url(), socket_connect_timeout=1.0, socket_timeout=1.0)
            payload["redis_ping"] = bool(redis_client.ping())
        except Exception as exc:  # pragma: no cover - canlı ortamda anlamlı
            logger.exception("BYS360 V6C guarded exception | file=app/services/async_job_queue.py | line=206")
            payload["redis_ping"] = False
            payload["error"] = str(exc)
    return payload
