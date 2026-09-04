from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Any

from flask import jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import text

from app.extensions import db
from app.route_registry import main_bp
from app.route_support import safe_db_rollback
from app.services.ai_decision.historical_archive_integration import (
    build_archive_summary_payload,
    build_person_archive_payload,
)

logger = logging.getLogger(__name__)

"""BYS360 AI Karar Destek Faz 7 route ekleri.

Geçmiş yıl karne ve puan arşivini karar destek merkezi üzerinden güvenli
JSON çıktılarıyla sunar.

BYS360_AI_DECISION_FAZ7_ROUTES
"""

ResponseBuilder = Callable[..., dict[str, Any]]


def _run_faz7_json(builder: ResponseBuilder, *args: Any) -> tuple[Any, int]:
    try:
        payload = builder(*args)
        return jsonify(payload), 200
    except PermissionError as exc:
        safe_db_rollback()
        return jsonify({"ok": False, "error": str(exc) or "Bu sayfaya erişim yetkiniz bulunmamaktadır."}), 403
    except LookupError as exc:
        logger.exception("BYS360 AI karar destek: beklenmeyen LookupError | exc=%s", exc)
        safe_db_rollback()
        return jsonify({"ok": False, "error": "Kayıt bulunamadı."}), 404
    except ValueError as exc:
        logger.exception("BYS360 AI karar destek: beklenmeyen ValueError | exc=%s", exc)
        safe_db_rollback()
        return jsonify({"ok": False, "error": "Geçersiz istek parametresi."}), 400
    except Exception as exc:  # pragma: no cover
        logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz7_routes.py | line=43 | exc=%s", exc)
        safe_db_rollback()
        return jsonify({"ok": False, "error": "Geçmiş karne karar destek kontrolünde beklenmeyen bir hata oluştu."}), 500


def _load_settings() -> dict[str, Any]:
    rows = db.session.execute(
        text(
            """
            SELECT setting_key, value_text
              FROM module_settings
             WHERE module_key = 'ai_decision'
               AND setting_key IN (
                'faz7_low_score_limit', 'faz7_high_score_limit',
                'faz7_detail_for_personnel_only', 'faz7_manager_summary_only'
               )
            """
        )
    ).mappings().all()
    return {row["setting_key"]: row["value_text"] for row in rows}


def _limit(default: int = 250) -> int:
    try:
        value = int(request.args.get("limit", default))
        return max(1, min(value, 1000))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/ai/decision_support_faz7_routes.py | line=69")
        return default


def _archive_rows(limit: int = 250) -> Sequence[Any]:
    return db.session.execute(
        text(
            """
            SELECT id, user_id, personnel_id, registry_no, personnel_name,
                   period_year, period_title, score_value, score_label,
                   general_comment, source_document, created_at
              FROM performance_archived_results
             WHERE COALESCE(visibility_status, 'active') <> 'deleted'
             ORDER BY period_year DESC NULLS LAST, created_at DESC NULLS LAST, id DESC
             LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()


def _person_archive_rows(user_id: int, limit: int = 100) -> Sequence[Any]:
    return db.session.execute(
        text(
            """
            SELECT id, user_id, personnel_id, registry_no, personnel_name,
                   period_year, period_title, score_value, score_label,
                   general_comment, source_document, created_at
              FROM performance_archived_results
             WHERE COALESCE(visibility_status, 'active') <> 'deleted'
               AND COALESCE(user_id, personnel_id) = :user_id
             ORDER BY period_year DESC NULLS LAST, created_at DESC NULLS LAST, id DESC
             LIMIT :limit
            """
        ),
        {"user_id": user_id, "limit": limit},
    ).mappings().all()


@main_bp.route("/ai/decision-support/faz7/health")
@login_required
def ai_decision_faz7_health():
    return jsonify({
        "ok": True,
        "phase": "Faz 7",
        "module": "AI Karar Destek Merkezi",
        "scope": "Geçmiş Yıl Karne ve Puan Arşivi",
        "marker": "BYS360_AI_DECISION_FAZ7_HEALTH_OK",
    })


@main_bp.route("/ai/decision-support/performance/archive/summary")
@login_required
def ai_decision_faz7_archive_summary():
    rows = _archive_rows(_limit())
    settings = _load_settings()
    return _run_faz7_json(build_archive_summary_payload, rows, current_user, settings)


@main_bp.route("/ai/decision-support/performance/archive/user/<int:user_id>")
@login_required
def ai_decision_faz7_person_archive(user_id: int):
    rows = _person_archive_rows(user_id, _limit(100))
    settings = _load_settings()
    return _run_faz7_json(build_person_archive_payload, rows, current_user, user_id, settings)
