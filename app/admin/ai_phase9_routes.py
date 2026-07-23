from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_REQUIRED
# STATUS_SOURCE: app.admin.route_manifest REQUIRED_ROUTE_MODULES
import csv
import io
import json

from flask import make_response, request
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_render
from app.services.ai.executive_reporting import (
    build_ai_executive_brief,
    render_ai_executive_markdown,
)
from app.services.ai.schema_guard import get_ai_schema_status


def _safe_int(value: str | None, default: int = 14) -> int:
    try:
        return max(int(value or default), 1)
    except (TypeError, ValueError):
        return default


def _schema_fallback(page_title: str):
    schema_status = get_ai_schema_status()
    if schema_status.get('ready'):
        return None
    return safe_render(
        'admin_ai_schema_not_ready.html',
        page_title=page_title,
        selected_module_type='',
        ai_schema_status=schema_status,
        module_options=[],
    )


@main_bp.route('/admin/ai-executive-brief')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_executive_brief():
    fallback = _schema_fallback('AI Yönetici Özeti')
    if fallback:
        return fallback
    snapshot = build_ai_executive_brief(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    return safe_render('admin_ai_executive_brief.html', **snapshot)


@main_bp.route('/admin/ai-share-export-hub')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_share_export_hub():
    fallback = _schema_fallback('AI Paylaşım ve Dışa Aktarma')
    if fallback:
        return fallback
    snapshot = build_ai_executive_brief(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    return safe_render('admin_ai_share_export_hub.html', **snapshot)


@main_bp.route('/admin/ai-executive-brief/export.md')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_executive_brief_export_md():
    snapshot = build_ai_executive_brief(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    response = make_response(render_ai_executive_markdown(snapshot))
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_executive_brief.md'
    return response


@main_bp.route('/admin/ai-executive-brief/export.json')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_executive_brief_export_json():
    snapshot = build_ai_executive_brief(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    payload = dict(snapshot)
    if payload.get('generated_at'):
        payload['generated_at'] = payload['generated_at'].isoformat()
    exec_summary = dict(payload.get('executive_summary') or {})
    if exec_summary.get('generated_at'):
        exec_summary['generated_at'] = exec_summary['generated_at'].isoformat()
    payload['executive_summary'] = exec_summary
    response = make_response(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_executive_brief.json'
    return response


@main_bp.route('/admin/ai-share-export-hub/export.csv')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_share_export_hub_export_csv():
    snapshot = build_ai_executive_brief(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['section', 'title', 'body', 'metric_1', 'metric_2', 'metric_3'])
    for row in snapshot.get('highlights') or []:
        writer.writerow(['highlight', row.get('title'), row.get('body'), '', '', ''])
    for row in snapshot.get('alerts') or []:
        writer.writerow(['alert', row.get('title'), row.get('body'), row.get('severity'), row.get('quality_score'), row.get('negative_feedback')])
    for row in snapshot.get('actions') or []:
        writer.writerow(['action', row.get('title'), row.get('body'), row.get('severity'), '', ''])
    for row in snapshot.get('module_rows') or []:
        writer.writerow(['module', row.get('module_type'), row.get('risk_level'), row.get('quality_score'), row.get('success_rate'), row.get('backlog_total')])
    for row in snapshot.get('prompt_rows') or []:
        writer.writerow(['prompt', row.get('prompt_version'), row.get('stability'), row.get('quality_score'), row.get('success_rate'), row.get('open_recommendations')])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_share_export_pack.csv'
    return response

@main_bp.route('/admin/analysis-center/recommendation-priority')
@main_bp.route('/admin/ai-recommendation-priority')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_recommendation_priority():
    """Faz 9: AI öneri motoru ve risk/önceliklendirme paneli."""
    from app.services.ai.recommendation_priority import build_ai_recommendation_priority_snapshot

    fallback = _schema_fallback('AI Öneri Motoru ve Risk Önceliklendirme')
    if fallback:
        return fallback
    snapshot = build_ai_recommendation_priority_snapshot(
        lookback_days=request.args.get('lookback_days') or 30,
        module_type=request.args.get('module_type') or '',
        status=request.args.get('status') or '',
        severity=request.args.get('severity') or '',
        limit=request.args.get('limit') or 50,
    )
    return safe_render('admin_analysis_recommendation_priority.html', **snapshot)


@main_bp.route('/admin/analysis-center/recommendation-priority/export')
@main_bp.route('/admin/ai-recommendation-priority/export')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_recommendation_priority_export():
    """Faz 9 öneri önceliklendirme çıktısını salt-okunur CSV olarak verir."""
    from app.services.ai.recommendation_priority import (
        build_ai_recommendation_priority_snapshot,
        export_recommendation_priority_rows,
    )

    fallback = _schema_fallback('AI Öneri Motoru ve Risk Önceliklendirme')
    if fallback:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['message'])
        writer.writerow(['AI şema hazır olmadığı için Faz 9 dışa aktarımı üretilemedi.'])
    else:
        snapshot = build_ai_recommendation_priority_snapshot(
            lookback_days=request.args.get('lookback_days') or 30,
            module_type=request.args.get('module_type') or '',
            status=request.args.get('status') or '',
            severity=request.args.get('severity') or '',
            limit=request.args.get('limit') or 250,
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'recommendation_id',
            'module',
            'recommendation_type',
            'title',
            'severity',
            'status',
            'priority_score',
            'priority_label',
            'reasons',
            'safe_action',
            'created_at',
        ])
        for row in export_recommendation_priority_rows(snapshot):
            writer.writerow(row)
    response = make_response('\ufeff' + output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_recommendation_priority.csv'
    return response
