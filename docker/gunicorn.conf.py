"""BYS360 Gunicorn runtime configuration.

This file keeps production process settings outside application code. Values are
controlled by environment variables so Windows/Waitress local usage can remain
unchanged while Docker/Linux deployment becomes reproducible.
"""

from __future__ import annotations

import multiprocessing
import os


def _int_env(name: str, default: int) -> int:
    try:
        value = int(str(os.getenv(name, "")).strip())
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = _int_env("WEB_CONCURRENCY", min(max(multiprocessing.cpu_count() * 2 + 1, 2), 8))
threads = _int_env("GUNICORN_THREADS", 4)
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")
timeout = _int_env("GUNICORN_TIMEOUT", 120)
graceful_timeout = _int_env("GUNICORN_GRACEFUL_TIMEOUT", 30)
keepalive = _int_env("GUNICORN_KEEPALIVE", 5)
max_requests = _int_env("GUNICORN_MAX_REQUESTS", 1000)
max_requests_jitter = _int_env("GUNICORN_MAX_REQUESTS_JITTER", 100)
preload_app = os.getenv("GUNICORN_PRELOAD_APP", "false").strip().lower() in {"1", "true", "yes", "on"}

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
capture_output = True
forwarded_allow_ips = os.getenv("GUNICORN_FORWARDED_ALLOW_IPS", "*")
proxy_allow_ips = os.getenv("GUNICORN_PROXY_ALLOW_IPS", "*")
