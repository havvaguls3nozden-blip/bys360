from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_OPTIONAL
# STATUS_SOURCE: app.communication.route_manifest OPTIONAL_ROUTE_MODULES
import json
import logging
from io import BytesIO

from flask import Response, flash, redirect, request, send_file, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import consume_form_token, issue_form_token, menu_key_required, safe_render
from app.services.communication_phase9b_service import (
    build_phase9b_markdown,
    phase9b_payload,
    phase9b_transition_center_snapshot,
    record_phase9b_decision,
    record_phase9b_gate,
)

logger = logging.getLogger(__name__)


@main_bp.route('/communication/faz9b')
@login_required
@menu_key_required('reports')
def communication_phase9b_dashboard():
    payload = phase9b_transition_center_snapshot()
    gate_token = issue_form_token('communication_phase9b_gate', scope=str(current_user.id))
    decision_token = issue_form_token('communication_phase9b_decision', scope=str(current_user.id))
    return safe_render(
        'communication/phase9b_dashboard.html',
        payload=payload,
        gate_token=gate_token,
        decision_token=decision_token,
    )


@main_bp.route('/communication/faz9b/transition-center')
@login_required
@menu_key_required('settings')
def communication_phase9b_transition_center():
    payload = phase9b_transition_center_snapshot()
    gate_token = issue_form_token('communication_phase9b_gate', scope=str(current_user.id))
    decision_token = issue_form_token('communication_phase9b_decision', scope=str(current_user.id))
    return safe_render(
        'communication/phase9b_transition_center.html',
        payload=payload,
        gate_token=gate_token,
        decision_token=decision_token,
    )


@main_bp.route('/communication/faz9b/gate', methods=['POST'])
@login_required
@menu_key_required('settings')
def communication_phase9b_gate_create():
    submitted = request.form.get('gate_token')
    if not consume_form_token('communication_phase9b_gate', submitted, scope=str(current_user.id)):
        flash('Faz 9B kapı formu geçersiz veya süresi dolmuş.', 'danger')
        return redirect(url_for('main.communication_phase9b_transition_center'))

    gate_key = (request.form.get('gate_key') or '').strip()
    status = (request.form.get('status') or 'pending').strip().lower()
    note = (request.form.get('note') or '').strip()
    try:
        record_phase9b_gate(current_user, gate_key, status, note)
        flash('Faz 9B kapı kaydı oluşturuldu.', 'success')
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/phase9b_routes.py | line=70 | exc=%s", exc)
        flash('Kapı kaydı oluşturulamadı.', 'danger')
    return redirect(url_for('main.communication_phase9b_transition_center'))


@main_bp.route('/communication/faz9b/decision', methods=['POST'])
@login_required
@menu_key_required('settings')
def communication_phase9b_decision_create():
    submitted = request.form.get('decision_token')
    if not consume_form_token('communication_phase9b_decision', submitted, scope=str(current_user.id)):
        flash('Faz 9B karar formu geçersiz veya süresi dolmuş.', 'danger')
        return redirect(url_for('main.communication_phase9b_transition_center'))

    decision = (request.form.get('decision') or '').strip()
    note = (request.form.get('note') or '').strip()
    try:
        record_phase9b_decision(current_user, decision, note)
        flash('Faz 9B karar kaydı oluşturuldu.', 'success')
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/phase9b_routes.py | line=89 | exc=%s", exc)
        flash('Karar kaydı oluşturulamadı.', 'danger')
    return redirect(url_for('main.communication_phase9b_transition_center'))


@main_bp.route('/communication/faz9b/export/md')
@login_required
@menu_key_required('reports')
def communication_phase9b_export_md():
    return Response(
        build_phase9b_markdown(),
        mimetype='text/markdown; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=communication_phase9b_data_security.md'},
    )


@main_bp.route('/communication/faz9b/export/json')
@login_required
@menu_key_required('reports')
def communication_phase9b_export_json():
    payload = json.dumps(phase9b_payload(), ensure_ascii=False, indent=2, default=str)
    data = BytesIO(payload.encode('utf-8'))
    data.seek(0)
    return send_file(
        data,
        as_attachment=True,
        download_name='communication_phase9b_data_security.json',
        mimetype='application/json',
    )
