"""
BYS360 AI Karar Destek Faz 11 route katmanı.

BYS360_AI_DECISION_FAZ11_ROUTES_OK
"""
from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

try:
    from flask import Blueprint, jsonify, render_template, request
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz11_routes.py | line=15")
    Blueprint = None  # type: ignore
    jsonify = None  # type: ignore
    render_template = None  # type: ignore
    request = None  # type: ignore

try:
    from flask_login import current_user, login_required
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz11_routes.py | line=23")
    current_user = None  # type: ignore
    def login_required(func):  # type: ignore
        return func

try:
    from app import db
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz11_routes.py | line=30")
    db = None  # type: ignore

from app.services.ai_decision.development_guidance_integration import (
    build_development_guidance_from_db,
    persist_development_guidance_snapshot,
)


if Blueprint is not None:
    ai_decision_faz11_bp = Blueprint(
        "ai_decision_faz11",
        __name__,
        url_prefix="/decision-support/faz11",
    )
else:  # pragma: no cover
    ai_decision_faz11_bp = None  # type: ignore


def _int_arg(name: str) -> int | None:
    try:
        value = request.args.get(name) if request is not None else None
        if value in (None, ""):
            return None
        return int(value)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz11_routes.py | line=55")
        return None


def _float_arg(name: str) -> float | None:
    try:
        value = request.args.get(name) if request is not None else None
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz11_routes.py | line=65")
        return None


def _viewer_role() -> str:
    try:
        role = getattr(current_user, "role", "") or getattr(current_user, "role_name", "")
        return str(role or "Yetkili kullanıcı")
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz11_routes.py | line=73")
        return "Yetkili kullanıcı"


@ai_decision_faz11_bp.route("/health")
@login_required
def faz11_health():
    return jsonify({
        "ok": True,
        "phase": "Faz 11",
        "module": "Gelişim Önerisi ve Rehber Alanı",
        "marker": "BYS360_AI_DECISION_FAZ11_ROUTES_OK",
    })


@ai_decision_faz11_bp.route("/development-guidance")
@login_required
def faz11_development_guidance():
    evaluation_id = _int_arg("evaluation_id")
    personnel_id = _int_arg("personnel_id")
    period_id = _int_arg("period_id")
    score = _float_arg("score")
    context = build_development_guidance_from_db(
        getattr(db, "session", None),
        evaluation_id=evaluation_id,
        personnel_id=personnel_id,
        period_id=period_id,
        score=score,
        viewer_role=_viewer_role(),
    )
    persist_development_guidance_snapshot(
        getattr(db, "session", None),
        period_id=period_id,
        personnel_id=personnel_id,
        evaluation_id=evaluation_id,
        context=context,
    )
    if request is not None and request.args.get("format") == "json":
        return jsonify(context)
    return render_template("ai_decision/faz11_development_guidance.html", context=context)


@ai_decision_faz11_bp.route("/development-guidance/<int:evaluation_id>")
@login_required
def faz11_development_guidance_evaluation(evaluation_id: int):
    context = build_development_guidance_from_db(
        getattr(db, "session", None),
        evaluation_id=evaluation_id,
        viewer_role=_viewer_role(),
    )
    persist_development_guidance_snapshot(
        getattr(db, "session", None),
        period_id=None,
        personnel_id=None,
        evaluation_id=evaluation_id,
        context=context,
    )
    if request is not None and request.args.get("format") == "json":
        return jsonify(context)
    return render_template("ai_decision/faz11_development_guidance.html", context=context)
