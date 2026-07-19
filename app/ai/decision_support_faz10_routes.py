"""
BYS360 AI Karar Destek Faz 10 route katmanı.

BYS360_AI_DECISION_FAZ10_ROUTES_OK
"""
from __future__ import annotations

from typing import Any, Optional
import logging
logger = logging.getLogger(__name__)

try:
    from flask import Blueprint, jsonify, render_template, request
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz10_routes.py | line=15")
    Blueprint = None  # type: ignore
    jsonify = None  # type: ignore
    render_template = None  # type: ignore
    request = None  # type: ignore

try:
    from flask_login import current_user, login_required
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz10_routes.py | line=23")
    current_user = None  # type: ignore
    def login_required(func):  # type: ignore
        return func

try:
    from app import db
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz10_routes.py | line=30")
    db = None  # type: ignore

from app.services.ai_decision.interim_feedback_integration import (
    build_interim_feedback_context,
    persist_interim_feedback_snapshot,
)


if Blueprint is not None:
    ai_decision_faz10_bp = Blueprint(
        "ai_decision_faz10",
        __name__,
        url_prefix="/decision-support/faz10",
    )
else:  # pragma: no cover
    ai_decision_faz10_bp = None  # type: ignore


def _int_arg(name: str) -> int | None:
    try:
        value = request.args.get(name) if request is not None else None
        if value in (None, ""):
            return None
        return int(value)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz10_routes.py | line=55")
        return None


def _viewer_role() -> str:
    try:
        role = getattr(current_user, "role", "") or getattr(current_user, "role_name", "")
        return str(role or "Yetkili kullanıcı")
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz10_routes.py | line=63")
        return "Yetkili kullanıcı"


@ai_decision_faz10_bp.route("/health")
@login_required
def faz10_health():
    return jsonify({
        "ok": True,
        "phase": "Faz 10",
        "module": "Performans İçi Ara Not / Geri Bildirim",
        "marker": "BYS360_AI_DECISION_FAZ10_ROUTES_OK",
    })


@ai_decision_faz10_bp.route("/interim-feedback")
@login_required
def faz10_interim_feedback():
    period_id = _int_arg("period_id")
    personnel_id = _int_arg("personnel_id")
    evaluation_id = _int_arg("evaluation_id")
    context = build_interim_feedback_context(
        getattr(db, "session", None),
        personnel_id=personnel_id,
        period_id=period_id,
        evaluation_id=evaluation_id,
        viewer_role=_viewer_role(),
    )
    persist_interim_feedback_snapshot(
        getattr(db, "session", None),
        period_id=period_id,
        personnel_id=personnel_id,
        evaluation_id=evaluation_id,
        context=context,
    )
    if request is not None and request.args.get("format") == "json":
        return jsonify(context)
    return render_template("ai_decision/faz10_interim_feedback.html", context=context)


@ai_decision_faz10_bp.route("/interim-feedback/<int:period_id>")
@login_required
def faz10_interim_feedback_period(period_id: int):
    context = build_interim_feedback_context(
        getattr(db, "session", None),
        period_id=period_id,
        viewer_role=_viewer_role(),
    )
    persist_interim_feedback_snapshot(
        getattr(db, "session", None),
        period_id=period_id,
        personnel_id=None,
        evaluation_id=None,
        context=context,
    )
    if request is not None and request.args.get("format") == "json":
        return jsonify(context)
    return render_template("ai_decision/faz10_interim_feedback.html", context=context)
