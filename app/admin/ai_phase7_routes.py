from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_REQUIRED
# STATUS_SOURCE: app.admin.route_manifest REQUIRED_ROUTE_MODULES




import csv
import io

from flask import current_app, flash, make_response, request
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_render
from app.services.ai.governance import build_ai_governance_snapshot
from app.services.ai.governance_settings import get_governance_thresholds
from app.services.ai.schema_guard import get_ai_schema_status


def _safe_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


@main_bp.route('/admin/ai-governance-hub')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_governance_hub():
    schema_status = get_ai_schema_status()
    if not schema_status.get('ready'):
        return safe_render(
            'admin_ai_schema_not_ready.html',
            page_title='AI Yönetişim Merkezi',
            selected_module_type=(request.args.get('module_type') or '').strip().lower(),
            ai_schema_status=schema_status,
            module_options=[],
        )
    thresholds = get_governance_thresholds()
    snapshot = build_ai_governance_snapshot(
        module_type=request.args.get('module_type') or '',
        prompt_version=request.args.get('prompt_version') or '',
        lookback_days=_safe_int(request.args.get('lookback_days'), thresholds['default_lookback_days'], 1, 180),
        module_quality_floor=_safe_int(request.args.get('module_quality_floor'), thresholds['module_quality_floor'], 20, 95),
        prompt_quality_floor=_safe_int(request.args.get('prompt_quality_floor'), thresholds['prompt_quality_floor'], 20, 95),
        backlog_limit=_safe_int(request.args.get('backlog_limit'), thresholds['backlog_limit'], 1, 200),
        negative_feedback_limit=_safe_int(request.args.get('negative_feedback_limit'), thresholds['negative_feedback_limit'], 1, 50),
    )
    snapshot['configured_thresholds'] = thresholds
    return safe_render('admin_ai_governance_hub.html', **snapshot)


@main_bp.route('/admin/ai-governance-hub/export')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_governance_hub_export():
    thresholds = get_governance_thresholds()
    snapshot = build_ai_governance_snapshot(
        module_type=request.args.get('module_type') or '',
        prompt_version=request.args.get('prompt_version') or '',
        lookback_days=_safe_int(request.args.get('lookback_days'), thresholds['default_lookback_days'], 1, 180),
        module_quality_floor=_safe_int(request.args.get('module_quality_floor'), thresholds['module_quality_floor'], 20, 95),
        prompt_quality_floor=_safe_int(request.args.get('prompt_quality_floor'), thresholds['prompt_quality_floor'], 20, 95),
        backlog_limit=_safe_int(request.args.get('backlog_limit'), thresholds['backlog_limit'], 1, 200),
        negative_feedback_limit=_safe_int(request.args.get('negative_feedback_limit'), thresholds['negative_feedback_limit'], 1, 50),
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['section', 'severity', 'kind', 'module_type', 'prompt_version', 'title', 'body', 'quality_score', 'request_total', 'backlog_total', 'negative_feedback', 'failed_total'])
    for row in snapshot.get('all_alerts') or []:
        writer.writerow([
            'alert',
            row.get('severity'),
            row.get('kind'),
            row.get('module_type'),
            row.get('prompt_version'),
            row.get('title'),
            row.get('body'),
            row.get('quality_score'),
            row.get('request_total'),
            row.get('backlog_total'),
            row.get('negative_feedback'),
            row.get('failed_total'),
        ])
    for row in snapshot.get('actions') or []:
        writer.writerow([
            'action',
            row.get('severity'),
            '',
            '',
            '',
            row.get('title'),
            row.get('body'),
            '',
            '',
            '',
            '',
            '',
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_governance_hub.csv'
    return response


@main_bp.route('/admin/analysis-center/excel-preview', methods=['GET', 'POST'])
@main_bp.route('/admin/ai-excel-preview', methods=['GET', 'POST'])
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_analysis_center_excel_preview():
    """Faz 7: gerçek içe aktarım yapmadan güvenli Excel/CSV önizleme."""
    from app.services.ai.excel_preview import (
        ExcelPreviewValidationError,
        build_empty_excel_preview_context,
        build_safe_excel_preview,
    )

    context = build_empty_excel_preview_context()
    context.update(
        {
            'page_title': 'Analiz Merkezi Excel Önizleme',
            'selected_module_type': 'analysis_center',
            'request_method': request.method,
        }
    )
    if request.method == 'POST':
        uploaded_file = request.files.get('analysis_file')
        try:
            preview = build_safe_excel_preview(
                uploaded_file,
                sample_limit=request.form.get('sample_limit') or context.get('default_sample_limit'),
                scan_limit=request.form.get('scan_limit') or context.get('default_scan_limit'),
                sheet_name=request.form.get('sheet_name') or '',
            )
            context['preview'] = preview.to_dict()
            flash('Dosya güvenli şekilde analiz edildi. Gerçek içe aktarım yapılmadı.', 'success')
        except ExcelPreviewValidationError as exc:
            flash(str(exc), 'danger')
        except Exception as exc:  # pragma: no cover - canlı koruma
            current_app.logger.exception('Faz 7 Excel önizleme hatası: %s', exc)
            flash('Dosya önizleme sırasında beklenmeyen bir hata oluştu; veri kaydedilmedi.', 'danger')
    return safe_render('admin_analysis_excel_preview.html', **context)
