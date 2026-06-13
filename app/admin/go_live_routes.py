from __future__ import annotations



import json
from io import BytesIO

from flask import Response, send_file
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import admin_required, safe_render
from app.services.go_live_readiness_service import build_go_live_readiness_context


@main_bp.route('/admin/go-live-readiness', endpoint='admin_go_live_readiness')
@login_required
@admin_required
def admin_go_live_readiness():
    context = build_go_live_readiness_context()
    return safe_render(
        'admin_go_live_readiness.html',
        '<h3>Canlıya Hazırlık Merkezi</h3>',
        **context,
    )


@main_bp.route('/admin/go-live-readiness/export/json', endpoint='admin_go_live_readiness_export_json')
@login_required
@admin_required
def admin_go_live_readiness_export_json():
    context = build_go_live_readiness_context()
    payload = json.dumps(context, ensure_ascii=False, default=str, indent=2)
    data = BytesIO(payload.encode('utf-8'))
    data.seek(0)
    return send_file(
        data,
        as_attachment=True,
        download_name='bys360_go_live_readiness.json',
        mimetype='application/json',
    )


@main_bp.route('/admin/go-live-readiness/export/md', endpoint='admin_go_live_readiness_export_md')
@login_required
@admin_required
def admin_go_live_readiness_export_md():
    context = build_go_live_readiness_context()
    lines = [
        '# BYS360 Canlıya Hazırlık Özeti',
        '',
        f"- Üretim zamanı: {context.get('generated_at')}",
        f"- Hazırlık skoru: {context.get('readiness_score')}",
        f"- Kapanış kararı: {context.get('rollout_decision')}",
        '',
        '## Kapılar',
        '',
    ]
    for gate in context.get('gates') or []:
        lines.append(f"- [{gate.get('status')}] {gate.get('label')} — {gate.get('detail')} ({gate.get('owner')})")

    lines.extend(['', '## Güvenlik Özeti', ''])
    security = context.get('security_report') or {}
    lines.append(f"- Kritik: {security.get('critical_count', 0)}")
    lines.append(f"- Uyarı: {security.get('warning_count', 0)}")
    lines.append(f"- Bilgi: {security.get('info_count', 0)}")

    lines.extend(['', '## Ortam Önerileri', ''])
    for key, value in (context.get('env_suggestions') or {}).items():
        lines.append(f"- {key} = {value}")

    return Response('\n'.join(lines) + '\n', mimetype='text/markdown; charset=utf-8')