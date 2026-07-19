from __future__ import annotations

import logging

"""Performans servis katmanını tek merkezden okuyan güvenli orkestrasyon yardımcıları.

Bu fazın amacı yeni iş kuralı icat etmek değil; mevcut modüler servisleri
aynı sözleşmede birleştirip operasyon ekranlarının zincir sağlığı, görev üretimi
ve ekip kıyas durumunu tek bakışta okuyabilmesini sağlamaktır.
"""

from collections import Counter
from typing import Any, Iterable

from app.models import EvaluationAssignment, PerformanceEvaluation

from .assignments import (
    build_assignment_log_summary,
    generate_assignments_for_active_period,
    get_latest_assignment_generation_logs,
)
from .common import get_active_period, get_period
from .hierarchy import analyze_hierarchy_rows, build_assignment_rows
from .reporting import build_team_compare_rows

logger = logging.getLogger(__name__)


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0.0


def _safe_str(value: Any) -> str:
    return str(value or '').strip()


def _selected_period(period_id: int | None = None):
    return get_period(period_id) or get_active_period()


def _scope_rows(rows: Iterable[dict[str, Any]], employee_ids: Iterable[int] | None = None) -> list[dict[str, Any]]:
    allowed = {int(v) for v in (employee_ids or []) if str(v).isdigit()}
    if not allowed:
        return list(rows or [])
    result: list[dict[str, Any]] = []
    for row in rows or []:
        employee_id = row.get('employee_id')
        try:
            employee_id = int(employee_id)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/orchestration.py:55)")
            continue
        if employee_id in allowed:
            result.append(row)
    return result


def build_chain_health_snapshot(*, employee_ids: Iterable[int] | None = None) -> dict[str, Any]:
    rows = _scope_rows(analyze_hierarchy_rows(), employee_ids)
    assignment_rows = _scope_rows(build_assignment_rows(), employee_ids)

    issue_rows = [row for row in rows if list(row.get('issues') or [])]
    info_rows = [row for row in rows if not row.get('issues') and list(row.get('info_notes') or [])]
    single_manager_rows = [row for row in rows if bool(row.get('is_single_manager_case'))]
    level_3_rows = [row for row in rows if bool(row.get('has_level_3'))]

    unit_counter: Counter[tuple[str, str]] = Counter()
    for row in issue_rows:
        user = row.get('user')
        ust_birim = _safe_str(getattr(user, 'ust_birim', None)) or 'Belirsiz üst birim'
        birim = _safe_str(getattr(user, 'birim', None)) or 'Belirsiz birim'
        unit_counter[(ust_birim, birim)] += 1

    top_issue_units = [
        {
            'ust_birim': key[0],
            'birim': key[1],
            'issue_count': value,
        }
        for key, value in unit_counter.most_common(8)
    ]

    estimated_assignments = 0
    for row in assignment_rows:
        chain = row.get('chain') or {}
        for level_key in ('manager_1', 'manager_2', 'manager_3'):
            if _safe_str(chain.get(level_key)):
                estimated_assignments += 1

    sample_rows = []
    for row in issue_rows[:10]:
        chain = row.get('chain')
        sample_rows.append(
            {
                'employee_name': row.get('employee_name') or '-',
                'issues': list(row.get('issues') or []),
                'manager_1_name': getattr(chain, 'manager_1_name', '') if chain else '',
                'manager_2_name': getattr(chain, 'manager_2_name', '') if chain else '',
                'manager_3_name': getattr(chain, 'manager_3_name', '') if chain else '',
            }
        )

    return {
        'user_count': len(rows),
        'issue_count': len(issue_rows),
        'info_count': len(info_rows),
        'single_manager_count': len(single_manager_rows),
        'level_3_count': len(level_3_rows),
        'estimated_assignment_count': estimated_assignments,
        'top_issue_units': top_issue_units,
        'sample_issue_rows': sample_rows,
    }


def build_team_compare_snapshot(*, period_id: int | None = None, manager_id: int | None = None) -> dict[str, Any]:
    rows = build_team_compare_rows(period_id=period_id, manager_id=manager_id)
    if not rows:
        return {
            'row_count': 0,
            'average_score': 0.0,
            'low_count': 0,
            'high_count': 0,
            'completed_count': 0,
            'sample_rows': [],
        }

    scores = [_safe_float(row.get('score')) for row in rows]
    low_count = sum(1 for value in scores if value < 70)
    high_count = sum(1 for value in scores if value > 90)
    completed_count = sum(1 for row in rows if _safe_str(row.get('status')) in {'tamamlandi', 'yayinlandi'})

    return {
        'row_count': len(rows),
        'average_score': round(sum(scores) / len(scores), 2) if scores else 0.0,
        'low_count': low_count,
        'high_count': high_count,
        'completed_count': completed_count,
        'sample_rows': rows[:10],
    }


def build_assignment_generation_snapshot(*, period_id: int | None = None, employee_ids: Iterable[int] | None = None) -> dict[str, Any]:
    period = _selected_period(period_id)
    logs = get_latest_assignment_generation_logs(getattr(period, 'id', None), limit=200, employee_ids=employee_ids)
    rows = list(logs.get('rows') or [])
    summary = build_assignment_log_summary(rows)
    return {
        'period': period,
        'run_key': logs.get('run_key'),
        'created_at': logs.get('created_at'),
        'summary': summary,
        'rows': rows[:15],
    }


def run_assignment_generation_with_snapshot(*, period_id: int | None = None, actor_user_id: int | None = None) -> dict[str, Any]:
    result = generate_assignments_for_active_period(period_id=period_id, actor_user_id=actor_user_id)
    snapshot = build_assignment_generation_snapshot(period_id=period_id)
    return {
        'result': result,
        'snapshot': snapshot,
    }


def build_performance_service_snapshot(*, period_id: int | None = None, manager_id: int | None = None, employee_ids: Iterable[int] | None = None) -> dict[str, Any]:
    period = _selected_period(period_id)
    chain_health = build_chain_health_snapshot(employee_ids=employee_ids)
    team_compare = build_team_compare_snapshot(period_id=getattr(period, 'id', None), manager_id=manager_id)
    assignment_generation = build_assignment_generation_snapshot(period_id=getattr(period, 'id', None), employee_ids=employee_ids)

    assignment_count = 0
    evaluation_count = 0
    period_id_value = getattr(period, 'id', None)
    try:
        if period_id_value:
            assignment_count = EvaluationAssignment.query.filter_by(period_id=period_id_value).count()
            evaluation_count = PerformanceEvaluation.query.filter_by(period_id=period_id_value).count()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        assignment_count = 0
        evaluation_count = 0

    return {
        'period': period,
        'chain_health': chain_health,
        'team_compare': team_compare,
        'assignment_generation': assignment_generation,
        'cards': {
            'chain_issue_count': chain_health.get('issue_count', 0),
            'chain_info_count': chain_health.get('info_count', 0),
            'estimated_assignment_count': chain_health.get('estimated_assignment_count', 0),
            'current_assignment_count': assignment_count,
            'evaluation_count': evaluation_count,
            'team_compare_row_count': team_compare.get('row_count', 0),
        },
    }


__all__ = [
    'build_assignment_generation_snapshot',
    'build_chain_health_snapshot',
    'build_performance_service_snapshot',
    'build_team_compare_snapshot',
    'run_assignment_generation_with_snapshot',
]