# -*- coding: utf-8 -*-
"""BYS360 API ve ağır işlem rate limit altyapısı.

flask-limiter yoksa uygulamayı kırmadan devreden çıkar.
Varsayılanlar .env üzerinden değiştirilebilir:
- RATELIMIT_DEFAULT="200 per minute"
- RATELIMIT_STORAGE_URI="redis://redis:6379/1"
"""
from __future__ import annotations

import os
from typing import Any


def _storage_uri() -> str:
    return os.getenv("RATELIMIT_STORAGE_URI") or os.getenv("REDIS_URL") or "memory://"


def _default_limit() -> str:
    return os.getenv("RATELIMIT_DEFAULT", "200 per minute")


def init_api_rate_limit(app: Any) -> None:
    enabled = os.getenv("ENABLE_API_RATE_LIMIT", "true").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        app.logger.info("BYS360 API rate limit kapalı")
        return
    try:
        from flask import jsonify
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
    except Exception as exc:  # pragma: no cover
        app.logger.warning("flask-limiter bulunamadı; API rate limit pasif: %s", exc)
        return

    if getattr(app, "_bys360_rate_limit_ready", False):
        return

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[_default_limit()],
        storage_uri=_storage_uri(),
        headers_enabled=True,
    )

    @app.errorhandler(429)
    def _bys360_rate_limit_exceeded(error):
        response = jsonify({
            "ok": False,
            "message": "Çok kısa sürede çok fazla işlem yapıldı. Lütfen biraz sonra tekrar deneyin.",
        })
        response.status_code = 429
        response.headers.setdefault("Retry-After", "60")
        return response

    app.extensions["bys360_limiter"] = limiter
    app._bys360_rate_limit_ready = True
    app.logger.info("BYS360 API rate limit aktif")
