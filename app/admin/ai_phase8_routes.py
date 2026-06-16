from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_REQUIRED
# STATUS_SOURCE: app.admin.route_manifest REQUIRED_ROUTE_MODULES

import csv
import io

from flask import flash, make_response, redirect, request, url_for
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_render
from app.services.ai.governance_settings import get_ai_governance_settings, save_ai_governance_settings
from app.services.ai.schema_guard import get_ai_schema_status
from app.services.ai.weekly_summary import build_ai_weekly_summary
from app.services.ai.notification_priority import build_ai_notification_priority_snapshot, export_ai_notification_priority_rows


def _safe_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


@main_bp.route('/admin/ai-governance-settings', methods=['GET', 'POST'])
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_governance_settings():
    schema_status = get_ai_schema_status()
    if not schema_status.get('ready'):
        return safe_render(
            'admin_ai_schema_not_ready.html',
            page_title='AI Yönetişim Ayarları',
            selected_module_type='',
            ai_schema_status=schema_status,
            module_options=[],
        )

    if request.method == 'POST':
        payload = {
            'module_quality_floor': _safe_int(request.form.get('module_quality_floor'), 65, 20, 95),
            'prompt_quality_floor': _safe_int(request.form.get('prompt_quality_floor'), 60, 20, 95),
            'backlog_limit': _safe_int(request.form.get('backlog_limit'), 8, 1, 200),
            'negative_feedback_limit': _safe_int(request.form.get('negative_feedback_limit'), 3, 1, 50),
            'default_lookback_days': _safe_int(request.form.get('default_lookback_days'), 30, 1, 180),
            'weekly_summary': {
                'lookback_days': _safe_int(request.form.get('weekly_lookback_days'), 7, 1, 60),
                'top_limit': _safe_int(request.form.get('weekly_top_limit'), 5, 1, 20),
                'show_prompt_breakdown': bool(request.form.get('show_prompt_breakdown')),
                'show_module_breakdown': bool(request.form.get('show_module_breakdown')),
                'include_actions': bool(request.form.get('include_actions')),
            },
        }
        save_ai_governance_settings(payload)
        flash('AI yönetişim ayarları güncellendi.', 'success')
        return redirect(url_for('main.admin_ai_governance_settings'))

    settings = get_ai_governance_settings()
    return safe_render('admin_ai_governance_settings.html', settings=settings)


@main_bp.route('/admin/ai-weekly-summary')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_weekly_summary():
    schema_status = get_ai_schema_status()
    if not schema_status.get('ready'):
        return safe_render(
            'admin_ai_schema_not_ready.html',
            page_title='AI Haftalık Yönetici Özeti',
            selected_module_type='',
            ai_schema_status=schema_status,
            module_options=[],
        )
    snapshot = build_ai_weekly_summary(lookback_days=_safe_int(request.args.get('lookback_days'), 7, 1, 60))
    return safe_render('admin_ai_weekly_summary.html', **snapshot)


@main_bp.route('/admin/ai-weekly-summary/export')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_weekly_summary_export():
    snapshot = build_ai_weekly_summary(lookback_days=_safe_int(request.args.get('lookback_days'), 7, 1, 60))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['section', 'title', 'body', 'module_type', 'prompt_version', 'quality_score', 'backlog_total', 'negative_feedback'])
    for row in snapshot.get('highlights') or []:
        writer.writerow(['highlight', row.get('title'), row.get('body'), '', '', '', '', ''])
    for row in snapshot.get('alerts') or []:
        writer.writerow(['alert', row.get('title'), row.get('body'), row.get('module_type'), row.get('prompt_version'), row.get('quality_score'), row.get('backlog_total'), row.get('negative_feedback')])
    for row in snapshot.get('actions') or []:
        writer.writerow(['action', row.get('title'), row.get('body'), '', '', '', '', ''])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_weekly_summary.csv'
    return response


@main_bp.route('/admin/ai-notification-priority')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_notification_priority():
    snapshot = build_ai_notification_priority_snapshot(
        lookback_days=_safe_int(request.args.get('lookback_days'), 7, 1, 90),
        priority=request.args.get('priority') or '',
        notification_type=request.args.get('notification_type') or '',
        unread_only=bool(request.args.get('unread_only')),
        limit=_safe_int(request.args.get('limit'), 40, 5, 200),
    )
    return safe_render('admin_ai_notification_priority.html', **snapshot)


@main_bp.route('/admin/ai-notification-priority/export')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_notification_priority_export():
    snapshot = build_ai_notification_priority_snapshot(
        lookback_days=_safe_int(request.args.get('lookback_days'), 7, 1, 90),
        priority=request.args.get('priority') or '',
        notification_type=request.args.get('notification_type') or '',
        unread_only=bool(request.args.get('unread_only')),
        limit=_safe_int(request.args.get('limit'), 200, 5, 500),
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'created_at', 'priority', 'notification_type', 'title', 'is_read', 'reason'])
    for row in export_ai_notification_priority_rows(snapshot):
        writer.writerow([
            row.get('id'),
            row.get('created_at'),
            row.get('priority'),
            row.get('notification_type'),
            row.get('title'),
            row.get('is_read'),
            row.get('reason'),
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_notification_priority.csv'
    return response

@main_bp.route('/admin/analysis-center/visual-reports')
@main_bp.route('/admin/ai-visual-reports')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_visual_reports():
    """Faz 8: AI karar destek verilerini grafik ve rapor kartı olarak gösterir."""
    from app.services.ai.visual_reports import build_ai_visual_report_snapshot

    schema_status = get_ai_schema_status()
    if not schema_status.get('ready'):
        return safe_render(
            'admin_ai_schema_not_ready.html',
            page_title='AI Görselleştirme ve Rapor Kartları',
            selected_module_type=(request.args.get('module_type') or '').strip().lower(),
            ai_schema_status=schema_status,
            module_options=[],
        )
    snapshot = build_ai_visual_report_snapshot(
        lookback_days=request.args.get('lookback_days') or 30,
        module_type=request.args.get('module_type') or '',
    )
    return safe_render('admin_analysis_visual_reports.html', **snapshot)


@main_bp.route('/admin/analysis-center/visual-reports/export')
@main_bp.route('/admin/ai-visual-reports/export')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_visual_reports_export():
    """Faz 8 rapor kartlarını salt-okunur CSV olarak dışa verir."""
    from app.services.ai.visual_reports import build_ai_visual_report_snapshot, export_visual_report_rows

    snapshot = build_ai_visual_report_snapshot(
        lookback_days=request.args.get('lookback_days') or 30,
        module_type=request.args.get('module_type') or '',
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'module_type',
        'label',
        'request_total',
        'success_rate',
        'masked_rate',
        'open_recommendations',
        'critical_recommendations',
        'negative_feedback',
        'avg_latency_ms',
        'signal_score',
        'tone',
        'note',
    ])
    for row in export_visual_report_rows(snapshot):
        writer.writerow(row)
    response = make_response('\ufeff' + output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_visual_report_cards.csv'
    return response

