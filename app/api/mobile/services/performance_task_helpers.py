from __future__ import annotations

import logging
from datetime import datetime as _v2822_datetime
from datetime import UTC
from typing import Any

from app.api.mobile.routes import _full_name, _has_global_scope, _item
from app.api.mobile.services.performance_base_helpers import _date_text, _label, _period_name
from app.extensions import db
from app.models import EvaluationAssignment, PerformancePeriod, User

logger = logging.getLogger(__name__)

_DONE = {"tamamlandi", "tamamlandı", "completed", "done", "closed", "kapandi", "kapandı", "yayınlandı", "published"}


def _task_helpers_rollback_quietly() -> None:
    try:
        db.session.rollback()
    except Exception:
        logger.exception("BYS360 mobil performans görev yardımcısında rollback tamamlanamadı.")


def _safe_get_model(model, object_id):
    try:
        if object_id is None:
            return None
        return db.session.get(model, object_id)
    except Exception:
        logger.exception("BYS360 mobil performans görev yardımcısında kayıt okunamadı.")
        _task_helpers_rollback_quietly()
        return None


def _v2822_now():
    try:
        return _v2822_datetime.now(UTC).replace(tzinfo=None)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _v2822_datetime.utcnow()


def _v2822_due_label(row: Any) -> tuple[str, int, str]:
    completed = getattr(row, 'completed_at', None)
    if completed:
        return 'Tamamlandı', 100, 'green'
    due = getattr(row, 'due_date', None)
    if due:
        try:
            hours = ((due.replace(tzinfo=None) if getattr(due, 'tzinfo', None) else due) - _v2822_now()).total_seconds() / 3600
            if hours < 0:
                return 'Gecikti', 25, 'yellow'
            if hours <= 24:
                return 'Bugün Son Gün', 55, 'yellow'
            if hours <= 72:
                return 'Süresi Yaklaşıyor', 65, 'blue'
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/performance_routes.py:553)")
    return _label(getattr(row, 'status', None), 'Değerlendirme Bekliyor'), 40, 'red'


def _v2822_unit_name(user: Any) -> str:
    if not user:
        return 'Birim bilgisi'
    for name in ('birim', 'unit_name', 'organization_unit_name', 'ust_birim'):
        value = getattr(user, name, None)
        if value:
            return str(value)
    org = getattr(user, 'organization_unit', None)
    if org:
        return str(getattr(org, 'name', None) or getattr(org, 'title', None) or 'Birim bilgisi')
    return 'Birim bilgisi'


def _v2822_sicil(user: Any) -> str:
    if not user:
        return '-'
    for name in ('sicil_no', 'registration_no', 'employee_no', 'sicil'):
        value = getattr(user, name, None)
        if value:
            return str(value)
    return '-'


def _v2822_level_label(level: Any) -> str:
    try:
        n = int(level or 0)
    except (TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        n = 0
    if n == 3:
        return '3. Amir'
    if n == 2:
        return '2. Amir'
    if n == 1:
        return '1. Amir'
    return 'Amir'


def _v2822_assignment_card(row: Any) -> dict[str, Any]:
    employee = getattr(row, 'employee', None) or _safe_get_model(User, getattr(row, 'employee_id', None))
    period = getattr(row, 'period', None) or _safe_get_model(PerformancePeriod, getattr(row, 'period_id', None))
    status, progress, _tone = _v2822_due_label(row)
    due = _date_text(getattr(row, 'due_date', None))
    meta_parts = [_v2822_level_label(getattr(row, 'manager_level', None)), _v2822_unit_name(employee)]
    if due:
        meta_parts.append(f'Son tarih {due}')
    return _item(getattr(row, 'id', ''), _full_name(employee), _period_name(period), status, ' / '.join(part for part in meta_parts if part), f'Sicil: {_v2822_sicil(employee)}', progress)


def _v2822_can_view_assignment(user: User, row: Any) -> bool:
    if not row:
        return False
    if _has_global_scope(user):
        return True
    return int(getattr(row, 'evaluator_id', 0) or 0) == int(getattr(user, 'id', 0) or 0)


def _v2822_assignment_query(user: User):
    q = EvaluationAssignment.query
    if _has_global_scope(user):
        return q
    return q.filter(EvaluationAssignment.evaluator_id == user.id)


def _v2822_open_query(user: User):
    q = _v2822_assignment_query(user)
    try:
        return q.filter(~EvaluationAssignment.status.in_(list(_DONE)), EvaluationAssignment.completed_at.is_(None))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _task_helpers_rollback_quietly()
        return q
