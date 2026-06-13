from __future__ import annotations



import os
import time
from typing import Any

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


def _db_status() -> tuple[bool, str]:
    try:
        from sqlalchemy import text
        try:
            from app.extensions import db  # type: ignore
        except Exception:
            from extensions import db  # type: ignore
        db.session.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:  # pragma: no cover - canlı ortam bağımlılığı
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/core/healthcheck.py:23")
        return False, f"{type(exc).__name__}: {exc}"


def _redis_status() -> tuple[bool | None, str]:
    url = os.environ.get("REDIS_URL") or os.environ.get("CACHE_REDIS_URL")
    if not url:
        return None, "not_configured"
    try:
        import redis  # type: ignore
        client = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        return bool(client.ping()), "ok"
    except Exception as exc:  # pragma: no cover - canlı ortam bağımlılığı
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/core/healthcheck.py:35")
        return False, f"{type(exc).__name__}: {exc}"


@health_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "BYS360"}), 200


@health_bp.route("/health/deep")
def health_deep():
    db_ok, db_message = _db_status()
    redis_ok, redis_message = _redis_status()
    checks: dict[str, Any] = {
        "db": {"ok": db_ok, "message": db_message},
        "redis": {"ok": redis_ok, "message": redis_message},
    }
    overall_ok = db_ok and (redis_ok is not False)
    return jsonify({
        "status": "ok" if overall_ok else "degraded",
        "service": "BYS360",
        "timestamp": int(time.time()),
        "checks": checks,
        "marker": "BYS360_CLAUDE_ROADMAP_PHASE5_HEALTHCHECK_SYNTAX_OK",
    }), 200 if overall_ok else 503
