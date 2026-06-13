from __future__ import annotations


import logging

from app.core.datetime_utils import utc_now
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy import desc

from app.models import (
    AssignmentCoverageLog,
    EvaluationPublishLog,
    FeedbackMeeting,
    FeedbackRequest,
    MailLog,
)
from app.services.performance.common import get_period
from app.services.performance.go_live_service import build_performance_go_live_center
from app.services.performance.health_report import build_performance_task_health_report
from app.services.performance.orchestration import build_performance_service_snapshot
from app.services.performance.preflight import build_task_management_preflight_report
from app.services.performance.publish_guard import build_publish_preflight_report
from app.services.performance_v2.reporting_workspace import (
    build_period_scorecard_context,
    build_publish_workspace_context,
)
logger = logging.getLogger(__name__)


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0


def _clean_text(value: Any, default: str = '-') -> str:
    text = str(value or '').strip()
    return text or default


def _safe_name(user: Any) -> str:
    if not user:
        return '-'
    return (
        getattr(user, 'full_name', None)
        or f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}".strip()
        or getattr(user, 'email', None)
        or '-'
    )


def _coerce_scope_ids(values: Iterable[Any] | None) -> list[int]:
    result: list[int] = []
    for value in values or []:
        try:
            as_int = int(value)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/ops_center.py:56)")
            continue
        if as_int > 0 and as_int not in result:
            result.append(as_int)
    return result


def _collect_feedback_data(period, scope_user_ids: Iterable[int] | None) -> tuple[list[Any], list[Any]]:
    if not period:
        return [], []
    employee_ids = _coerce_scope_ids(scope_user_ids)
    request_query = FeedbackRequest.query.filter_by(period_id=period.id)
    meeting_query = FeedbackMeeting.query
    if employee_ids:
        request_query = request_query.filter(FeedbackRequest.employee_id.in_(employee_ids))
        meeting_query = meeting_query.filter(FeedbackMeeting.employee_id.in_(employee_ids))
    requests_list = request_query.order_by(FeedbackRequest.requested_at.desc(), FeedbackRequest.id.desc()).all()
    meetings = meeting_query.order_by(FeedbackMeeting.created_at.desc(), FeedbackMeeting.id.desc()).all()
    return requests_list, meetings


def _build_assignment_log_rows(period, scope_user_ids: Iterable[int] | None, limit: int = 8) -> list[dict[str, Any]]:
    if not period:
        return []
    employee_ids = _coerce_scope_ids(scope_user_ids)
    query = AssignmentCoverageLog.query.filter_by(period_id=period.id)
    if employee_ids:
        query = query.filter(AssignmentCoverageLog.employee_id.in_(employee_ids))
    rows = query.order_by(desc(AssignmentCoverageLog.created_at), desc(AssignmentCoverageLog.id)).limit(max(int(limit or 0), 1)).all()
    payload: list[dict[str, Any]] = []
    for row in rows:
        payload.append({
            'created_at': getattr(row, 'created_at', None),
            'severity': _clean_text(getattr(row, 'severity', None), 'warning').lower(),
            'event_type': _clean_text(getattr(row, 'event_type', None)),
            'event_scope': _clean_text(getattr(row, 'event_scope', None)),
            'employee_name': _safe_name(getattr(row, 'employee', None)),
            'manager_level': getattr(row, 'manager_level', None),
            'reason': _clean_text(getattr(row, 'reason', None)),
            'acting_evaluator_name': _safe_name(getattr(row, 'acting_evaluator', None)),
            'original_evaluator_name': _safe_name(getattr(row, 'original_evaluator', None)),
            'run_key': _clean_text(getattr(row, 'run_key', None), '-'),
        })
    return payload


def _build_publish_log_rows(period, scope_user_ids: Iterable[int] | None, limit: int = 8) -> list[dict[str, Any]]:
    if not period:
        return []
    employee_ids = _coerce_scope_ids(scope_user_ids)
    query = EvaluationPublishLog.query.filter_by(period_id=period.id)
    if employee_ids:
        query = query.filter(EvaluationPublishLog.employee_id.in_(employee_ids))
    rows = query.order_by(desc(EvaluationPublishLog.acted_at), desc(EvaluationPublishLog.id)).limit(max(int(limit or 0), 1)).all()
    payload: list[dict[str, Any]] = []
    for row in rows:
        payload.append({
            'acted_at': getattr(row, 'acted_at', None),
            'action': _clean_text(getattr(row, 'action', None)),
            'employee_name': _safe_name(getattr(row, 'employee', None)),
            'actor_name': _safe_name(getattr(row, 'acted_by', None)),
        })
    return payload


def _build_mail_log_rows(period, scope_user_ids: Iterable[int] | None, limit: int = 8) -> list[dict[str, Any]]:
    if not period:
        return []
    employee_ids = _coerce_scope_ids(scope_user_ids)
    query = MailLog.query.filter_by(related_period_id=period.id)
    if employee_ids:
        query = query.filter(MailLog.related_user_id.in_(employee_ids))
    rows = query.order_by(desc(MailLog.sent_at), desc(MailLog.id)).limit(max(int(limit or 0), 1)).all()
    payload: list[dict[str, Any]] = []
    for row in rows:
        payload.append({
            'sent_at': getattr(row, 'sent_at', None),
            'mail_type': _clean_text(getattr(row, 'mail_type', None)),
            'recipient_email': _clean_text(getattr(row, 'recipient_email', None)),
            'is_success': bool(getattr(row, 'is_success', False)),
            'error_message': _clean_text(getattr(row, 'error_message', None), ''),
            'subject': _clean_text(getattr(row, 'subject', None)),
        })
    return payload


def _merge_signal_rows(source_label: str, rows: Iterable[dict[str, Any]] | None, tone: str) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for row in rows or []:
        merged.append({
            'source': source_label,
            'tone': tone,
            'title': _clean_text(row.get('title')),
            'detail': _clean_text(row.get('detail')),
            'action': _clean_text(row.get('action'), ''),
        })
    return merged


def _build_readiness_summary(*, go_live_score: int, task_score: int, publish_score: int, blocker_count: int, warning_count: int) -> dict[str, Any]:
    base_score = round((go_live_score + task_score + publish_score) / 3) if any([go_live_score, task_score, publish_score]) else 0
    if blocker_count > 0:
        readiness_score = min(base_score, 69)
        readiness_label = 'Blokaj var'
        readiness_tone = 'critical'
    elif warning_count > 0:
        readiness_score = min(max(base_score, 70), 89)
        readiness_label = 'Kontrollü ilerleyin'
        readiness_tone = 'watch'
    else:
        readiness_score = max(base_score, 90)
        readiness_label = 'Operasyon hazır'
        readiness_tone = 'ok'
    return {
        'base_score': base_score,
        'readiness_score': readiness_score,
        'readiness_label': readiness_label,
        'readiness_tone': readiness_tone,
    }


def build_performance_operations_snapshot(*, period=None, viewer=None, scope_user_ids: Iterable[int] | None = None, now: datetime | None = None) -> dict[str, Any]:
    """Operasyon merkezinin tek çağrıda besleneceği birleşik görünümü kurar.

    Bu snapshot; görev ön kontrolü, yayın ön kontrolü, canlıya hazırlık merkezi,
    geri bildirim verileri, sağlık raporu ve son log akışlarını aynı sözleşmede
    toplar. Amaç; dashboard route'larının ayrı ayrı servis birleştirmesi yapmadan
    hazır kart, uyarı ve log blokları alabilmesidir.
    """
    period = period or get_period()
    scope_ids = _coerce_scope_ids(scope_user_ids)
    scorecard = build_period_scorecard_context(period, viewer=viewer, allowed_employee_ids=scope_ids or None)
    publish_summary = build_publish_workspace_context(period, viewer=viewer, allowed_employee_ids=scope_ids or None)
    task_preflight = build_task_management_preflight_report(period, scope_ids or None)
    health_report = build_performance_task_health_report(period, scope_ids or None)
    publish_preflight = build_publish_preflight_report(period=period, scorecard=scorecard, publish_summary=publish_summary)
    requests_list, meetings = _collect_feedback_data(period, scope_ids or None)
    go_live = build_performance_go_live_center(
        active_period=period,
        requests_list=requests_list,
        meetings=meetings,
        now=now or utc_now(),
    )

    blocker_rows = (
        _merge_signal_rows('Görev ön kontrolü', task_preflight.get('blockers'), 'critical')
        + _merge_signal_rows('Yayın ön kontrolü', publish_preflight.get('blockers'), 'critical')
        + _merge_signal_rows('Canlı merkezi', go_live.get('blockers'), 'critical')
    )
    warning_rows = (
        _merge_signal_rows('Görev ön kontrolü', task_preflight.get('warnings'), 'watch')
        + _merge_signal_rows('Yayın ön kontrolü', publish_preflight.get('warnings'), 'watch')
        + _merge_signal_rows('Canlı merkezi', go_live.get('warnings'), 'watch')
    )

    readiness = _build_readiness_summary(
        go_live_score=_safe_int((go_live.get('cards') or {}).get('release_score')),
        task_score=_safe_int(task_preflight.get('readiness_score')),
        publish_score=_safe_int(publish_preflight.get('readiness_score')),
        blocker_count=len(blocker_rows),
        warning_count=len(warning_rows),
    )

    health_summary = health_report.get('summary') or {}
    cards = {
        'readiness_score': readiness['readiness_score'],
        'task_blockers': len(task_preflight.get('blockers') or []),
        'publish_blockers': len(publish_preflight.get('blockers') or []),
        'critical_health': (
            _safe_int(health_summary.get('duplicate_level_count'))
            + _safe_int(health_summary.get('mismatch_count'))
            + _safe_int(health_summary.get('orphan_evaluation_count'))
            + _safe_int(health_summary.get('orphan_assignment_count'))
            + _safe_int(health_summary.get('uncovered_count'))
        ),
        'critical_feedback_requests': _safe_int((go_live.get('cards') or {}).get('critical_feedback_requests')),
        'recent_log_events': (
            len(_build_assignment_log_rows(period, scope_ids or None, 6))
            + len(_build_publish_log_rows(period, scope_ids or None, 6))
            + len(_build_mail_log_rows(period, scope_ids or None, 6))
        ),
    }

    assignment_logs = _build_assignment_log_rows(period, scope_ids or None, 10)
    publish_logs = _build_publish_log_rows(period, scope_ids or None, 10)
    mail_logs = _build_mail_log_rows(period, scope_ids or None, 10)
    service_snapshot = build_performance_service_snapshot(
        period_id=getattr(period, 'id', None),
        manager_id=getattr(viewer, 'id', None),
        employee_ids=scope_ids or None,
    )

    return {
        'generated_at': now or utc_now(),
        'period': period,
        'cards': cards,
        'readiness_label': readiness['readiness_label'],
        'readiness_tone': readiness['readiness_tone'],
        'task_preflight': task_preflight,
        'publish_preflight': publish_preflight,
        'go_live': go_live,
        'health_report': health_report,
        'scorecard': scorecard,
        'publish_summary': publish_summary,
        'blocker_rows': blocker_rows,
        'warning_rows': warning_rows,
        'assignment_logs': assignment_logs,
        'publish_logs': publish_logs,
        'mail_logs': mail_logs,
        'service_snapshot': service_snapshot,
        'shortcut_counts': [
            {'label': 'Görev ön kontrol', 'value': len(task_preflight.get('blockers') or []) + len(task_preflight.get('warnings') or [])},
            {'label': 'Yayın ön kontrol', 'value': len(publish_preflight.get('blockers') or []) + len(publish_preflight.get('warnings') or [])},
            {'label': 'Sağlık kritik', 'value': cards['critical_health']},
            {'label': 'Kritik talep', 'value': cards['critical_feedback_requests']},
        ],
    }