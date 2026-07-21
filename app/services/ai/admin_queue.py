from __future__ import annotations

from math import ceil
from typing import Any

from sqlalchemy import func

from app.models import AIRecommendation
from app.services.ai.module_scope import (
    filter_visible_values,
    is_visible_ai_module,
    scope_visible_modules,
)
from app.services.ai.recommendation_actions import is_recommendation_supported


def _safe_int(value: Any, default: int = 1, minimum: int = 1, maximum: int | None = None) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def build_review_queue_snapshot(*, module_type: str = '', target_table: str = '', status: str = 'open', severity: str = '', page: int = 1, per_page: int = 20) -> dict[str, Any]:
    page = _safe_int(page, default=1)
    per_page = _safe_int(per_page, default=20, maximum=100)

    query = AIRecommendation.query
    selected_module_type = (module_type or '').strip().lower()
    selected_target_table = (target_table or '').strip()
    selected_status = (status or '').strip().lower()
    selected_severity = (severity or '').strip().lower()

    if selected_module_type:
        if not is_visible_ai_module(selected_module_type):
            query = query.filter(False)
        else:
            query = query.filter(func.lower(AIRecommendation.module_type) == selected_module_type)
    else:
        query = scope_visible_modules(query, AIRecommendation.module_type)
    if selected_target_table:
        query = query.filter(AIRecommendation.target_table == selected_target_table)
    if selected_status:
        query = query.filter(func.lower(AIRecommendation.status) == selected_status)
    if selected_severity:
        query = query.filter(func.lower(func.coalesce(AIRecommendation.severity, 'info')) == selected_severity)

    total = query.count()
    pages = max(ceil(total / per_page), 1)
    page = min(page, pages)
    rows = (
        query.order_by(AIRecommendation.created_at.desc(), AIRecommendation.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    module_options = filter_visible_values(
        row[0] for row in AIRecommendation.query.with_entities(AIRecommendation.module_type).distinct().order_by(AIRecommendation.module_type.asc()).all() if row[0]
    )
    target_table_options = [
        row[0] for row in AIRecommendation.query.with_entities(AIRecommendation.target_table).distinct().order_by(AIRecommendation.target_table.asc()).all() if row[0]
    ]
    severity_options = [
        row[0] for row in AIRecommendation.query.with_entities(AIRecommendation.severity).distinct().order_by(AIRecommendation.severity.asc()).all() if row[0]
    ]
    status_options = ['open', 'accepted', 'rejected', 'dismissed']

    row_payloads = []
    supported_count = 0
    for row in rows:
        supported = is_recommendation_supported(row)
        if supported:
            supported_count += 1
        row_payloads.append(
            {
                'id': row.id,
                'created_at': row.created_at,
                'module_type': row.module_type,
                'target_table': row.target_table,
                'target_id': row.target_id,
                'recommendation_type': row.recommendation_type,
                'title': row.title,
                'body': row.body,
                'severity': row.severity or 'info',
                'status': row.status,
                'reviewed_at': row.reviewed_at,
                'reviewed_by_user': getattr(row, 'reviewed_by_user', None),
                'is_supported': supported,
            }
        )

    open_total = AIRecommendation.query.filter(func.lower(AIRecommendation.status) == 'open').count()
    filtered_open_count = sum(1 for row in row_payloads if str(row.get('status') or '').lower() == 'open')
    filtered_supported_open = sum(1 for row in row_payloads if str(row.get('status') or '').lower() == 'open' and row.get('is_supported'))

    return {
        'rows': row_payloads,
        'module_options': module_options,
        'target_table_options': target_table_options,
        'severity_options': severity_options,
        'status_options': status_options,
        'selected_module_type': selected_module_type,
        'selected_target_table': selected_target_table,
        'selected_status': selected_status,
        'selected_severity': selected_severity,
        'summary': {
            'filtered_total': total,
            'global_open_total': open_total,
            'page_supported_total': supported_count,
            'page_filtered_open_total': filtered_open_count,
            'page_supported_open_total': filtered_supported_open,
        },
        'pagination': {
            'page': page,
            'pages': pages,
            'per_page': per_page,
            'total': total,
            'has_prev': page > 1,
            'has_next': page < pages,
            'prev_num': page - 1,
            'next_num': page + 1,
        },
    }