from __future__ import annotations

import logging
from typing import Any

from app.extensions import db
from app.models import User
from app.api.mobile.routes import _full_name, _item
from app.api.mobile.services.performance_base_helpers import _label, _period_name
from app.api.mobile.services.performance_query_helpers import _score_value


logger = logging.getLogger(__name__)


def _safe_get_user(user_id: Any):
    try:
        if user_id is None:
            return None
        return db.session.get(User, user_id)
    except Exception:
        logger.exception("BYS360 mobil performans item yardımcısında kullanıcı okunamadı.")
        try:
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 mobil performans item yardımcısında rollback tamamlanamadı.")
        return None


def _assignment_item(assignment: Any) -> dict[str, Any]:
    employee = getattr(assignment, "employee", None)
    evaluator = getattr(assignment, "evaluator", None) or getattr(assignment, "manager", None)
    period = getattr(assignment, "period", None)
    completed = getattr(assignment, "completed_at", None)
    status = _label(getattr(assignment, "status", None))
    level = getattr(assignment, "manager_level", None) or getattr(assignment, "supervisor_level", None) or "-"
    evaluator_text = _full_name(evaluator) if evaluator else "Değerlendirici bilgisi"
    return _item(getattr(assignment, "id", ""), _full_name(employee), _period_name(period), status, f"{level}. amir / {evaluator_text}" if str(level) != "-" else evaluator_text, "Tamamlandı" if completed else "İşlem bekliyor", 100 if completed else 40)


def _scorecard_item(row: Any) -> dict[str, Any]:
    employee = getattr(row, "employee", None) or _safe_get_user(getattr(row, "employee_id", None))
    period = getattr(row, "period", None)
    score = _score_value(row)
    status = "Yayınlandı" if getattr(row, "is_published", False) else _label(getattr(row, "status", None), "Kontrol Bekliyor")
    return _item(getattr(row, "id", ""), _full_name(employee), _period_name(period), status, "70 altı takip" if 0 < score < 70 else "Karne", f"{score}/100" if score else "", score if score else 35)
