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
from app.services.ai.go_live import build_ai_go_live_snapshot, render_ai_go_live_markdown
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


@main_bp.route('/admin/ai-go-live-readiness')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_go_live_readiness():
    fallback = _schema_fallback('AI Canlıya Alma Hazır Oluşu')
    if fallback:
        return fallback
    snapshot = build_ai_go_live_snapshot(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    return safe_render('admin_ai_go_live_readiness.html', **snapshot)


@main_bp.route('/admin/ai-acceptance-pack')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_acceptance_pack():
    fallback = _schema_fallback('AI Kabul ve Teslim Paketi')
    if fallback:
        return fallback
    snapshot = build_ai_go_live_snapshot(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    return safe_render('admin_ai_acceptance_pack.html', **snapshot)


@main_bp.route('/admin/ai-go-live-readiness/export.md')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_go_live_readiness_export_md():
    snapshot = build_ai_go_live_snapshot(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    response = make_response(render_ai_go_live_markdown(snapshot))
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_go_live_readiness.md'
    return response


@main_bp.route('/admin/ai-go-live-readiness/export.json')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_go_live_readiness_export_json():
    snapshot = build_ai_go_live_snapshot(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    payload = dict(snapshot)
    if payload.get('generated_at'):
        payload['generated_at'] = payload['generated_at'].isoformat()
    response = make_response(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_go_live_readiness.json'
    return response


@main_bp.route('/admin/ai-acceptance-pack/export.csv')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_acceptance_pack_export_csv():
    snapshot = build_ai_go_live_snapshot(lookback_days=_safe_int(request.args.get('lookback_days'), 14))
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['bolum', 'ad', 'durum', 'detay'])
    for gate in snapshot.get('gates') or []:
        writer.writerow(['kontrol', gate.get('label'), gate.get('status'), gate.get('detail')])
    for row in snapshot.get('signoff_rows') or []:
        writer.writerow(['imza', row.get('role'), row.get('status'), row.get('note')])
    for row in snapshot.get('artifact_rows') or []:
        writer.writerow(['artefakt', row.get('name'), row.get('status'), row.get('note')])
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_acceptance_pack.csv'
    return response

@main_bp.route('/admin/analysis-center/visibility-gate')
@main_bp.route('/admin/ai-visibility-gate')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_visibility_gate():
    """Faz 10: Yetki, KVKK maskeleme ve güvenli görünürlük kapısı."""
    from flask_login import current_user
    from app.services.ai.visibility_gate import build_ai_visibility_gate_snapshot

    fallback = _schema_fallback('AI Yetki, KVKK Maskeleme ve Güvenli Görünürlük Kapısı')
    if fallback:
        return fallback
    snapshot = build_ai_visibility_gate_snapshot(
        current_user=current_user,
        lookback_days=request.args.get('lookback_days') or 30,
        module_type=request.args.get('module_type') or '',
        role_name=request.args.get('role_name') or '',
    )
    return safe_render('admin_ai_visibility_gate.html', **snapshot)


@main_bp.route('/admin/analysis-center/visibility-gate/export')
@main_bp.route('/admin/ai-visibility-gate/export')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_visibility_gate_export():
    """Faz 10 güvenli görünürlük matrisini ham AI metni olmadan CSV verir."""
    from flask_login import current_user
    from werkzeug.exceptions import Forbidden
    from app.services.ai.visibility_gate import build_ai_visibility_gate_snapshot, export_visibility_gate_rows

    snapshot = build_ai_visibility_gate_snapshot(
        current_user=current_user,
        lookback_days=request.args.get('lookback_days') or 30,
        module_type=request.args.get('module_type') or '',
        role_name=request.args.get('role_name') or '',
    )
    if not snapshot.get('current_policy', {}).get('can_export_safe_csv'):
        raise Forbidden('Bu dışa aktarım için güvenli AI export yetkiniz yok.')

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'section',
        'role_or_module',
        'scope',
        'can_view_ai_center',
        'can_export_safe_csv',
        'kvkk_masking_required',
        'raw_payload_visible',
        'request_total',
        'unmasked_total',
        'active_redaction_rules',
        'risk_label',
        'note',
    ])
    for row in export_visibility_gate_rows(snapshot):
        writer.writerow(row)
    response = make_response('\ufeff' + output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_visibility_gate_safe.csv'
    return response
