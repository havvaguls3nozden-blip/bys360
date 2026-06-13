from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_REQUIRED
# STATUS_SOURCE: app.admin.route_manifest REQUIRED_ROUTE_MODULES



import csv
import io

from flask import make_response, request
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_render
from app.services.ai.quality import build_ai_quality_snapshot
from app.services.ai.schema_guard import get_ai_schema_status



def _safe_int(value: str | None, default: int = 30) -> int:
    try:
        return max(int(value or default), 1)
    except (TypeError, ValueError):
        return default


@main_bp.route('/admin/ai-quality-hub')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_quality_hub():
    schema_status = get_ai_schema_status()
    if not schema_status.get('ready'):
        return safe_render(
            'admin_ai_schema_not_ready.html',
            page_title='AI Kalite Panosu',
            selected_module_type=(request.args.get('module_type') or '').strip().lower(),
            ai_schema_status=schema_status,
            module_options=[],
        )
    snapshot = build_ai_quality_snapshot(
        module_type=request.args.get('module_type') or '',
        prompt_version=request.args.get('prompt_version') or '',
        lookback_days=_safe_int(request.args.get('lookback_days'), 30),
    )
    return safe_render('admin_ai_quality_hub.html', **snapshot)


@main_bp.route('/admin/ai-quality-hub/export')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_quality_hub_export():
    snapshot = build_ai_quality_snapshot(
        module_type=request.args.get('module_type') or '',
        prompt_version=request.args.get('prompt_version') or '',
        lookback_days=_safe_int(request.args.get('lookback_days'), 30),
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'section', 'key', 'request_total', 'quality_score', 'success_rate', 'masked_rate',
        'acceptance_rate', 'helpful_rate', 'avg_latency_ms', 'open_recommendations', 'negative_feedback'
    ])
    for row in snapshot.get('module_rows') or []:
        writer.writerow([
            'module', row.get('module_type'), row.get('request_total'), row.get('quality_score'),
            row.get('success_rate'), row.get('masked_rate'), row.get('acceptance_rate'),
            row.get('helpful_rate'), row.get('avg_latency_ms'), row.get('open_recommendations'),
            row.get('negative_feedback'),
        ])
    for row in snapshot.get('prompt_rows') or []:
        writer.writerow([
            'prompt', row.get('prompt_version'), row.get('request_total'), row.get('quality_score'),
            row.get('success_rate'), row.get('masked_rate'), row.get('acceptance_rate'),
            row.get('helpful_rate'), row.get('avg_latency_ms'), row.get('open_recommendations'),
            row.get('negative_feedback'),
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_quality_hub.csv'
    return response