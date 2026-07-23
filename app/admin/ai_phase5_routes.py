from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_REQUIRED
# STATUS_SOURCE: app.admin.route_manifest REQUIRED_ROUTE_MODULES
import csv
import io
import logging

from flask import flash, make_response, redirect, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_db_rollback, safe_render
from app.services.ai.admin_queue import build_review_queue_snapshot
from app.services.ai.audit import mark_recommendation
from app.services.ai.recommendation_actions import bulk_apply_recommendations

logger = logging.getLogger(__name__)


def _safe_ids(values: list[str]) -> list[int]:
    result: list[int] = []
    seen: set[int] = set()
    for item in values:
        try:
            value = int(item)
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/admin/ai_phase5_routes.py:26)")
            continue
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _current_filters() -> dict[str, str]:
    return {
        'module_type': (request.values.get('module_type') or '').strip().lower(),
        'target_table': (request.values.get('target_table') or '').strip(),
        'status': (request.values.get('status') or '').strip().lower(),
        'severity': (request.values.get('severity') or '').strip().lower(),
        'page': str(request.values.get('page') or '1'),
    }


@main_bp.route('/admin/ai-review-queue')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_review_queue():
    snapshot = build_review_queue_snapshot(
        module_type=request.args.get('module_type'),
        target_table=request.args.get('target_table'),
        status=request.args.get('status') or 'open',
        severity=request.args.get('severity'),
        page=request.args.get('page') or 1,
        per_page=20,
    )
    return safe_render('admin_ai_review_queue.html', **snapshot)


@main_bp.route('/admin/ai-review-queue/export')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_review_queue_export():
    snapshot = build_review_queue_snapshot(
        module_type=request.args.get('module_type'),
        target_table=request.args.get('target_table'),
        status=request.args.get('status') or 'open',
        severity=request.args.get('severity'),
        page=1,
        per_page=500,
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'created_at', 'module_type', 'target_table', 'target_id', 'recommendation_type', 'title', 'severity', 'status', 'is_supported'])
    for row in snapshot.get('rows') or []:
        writer.writerow([
            row.get('id'),
            row.get('created_at').isoformat() if row.get('created_at') else '',
            row.get('module_type'),
            row.get('target_table'),
            row.get('target_id'),
            row.get('recommendation_type'),
            row.get('title'),
            row.get('severity'),
            row.get('status'),
            'evet' if row.get('is_supported') else 'hayir',
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_review_queue.csv'
    return response


@main_bp.route('/admin/ai-review-queue/bulk', methods=['POST'])
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_review_queue_bulk():
    action = (request.form.get('bulk_action') or '').strip().lower()
    filters = _current_filters()
    recommendation_ids = _safe_ids(request.form.getlist('recommendation_ids'))
    redirect_url = url_for('main.admin_ai_review_queue', **filters)

    if not action:
        flash('Toplu işlem seçimi yapılmadı.', 'warning')
        return redirect(redirect_url)
    if not recommendation_ids:
        flash('Toplu işlem için en az bir öneri seçin.', 'warning')
        return redirect(redirect_url)

    try:
        if action in {'accepted', 'rejected', 'dismissed'}:
            for rid in recommendation_ids:
                mark_recommendation(rid, status=action, reviewed_by_user_id=getattr(current_user, 'id', None))
            db.session.commit()
            flash(f'{len(recommendation_ids)} AI önerisi için durum güncellendi: {action}.', 'success')
        elif action == 'apply':
            result = bulk_apply_recommendations(recommendation_ids, acting_user=current_user)
            db.session.commit()
            flash(
                f"AI toplu uygulama tamamlandı. Uygulanan: {result.get('applied', 0)} · Atlanan: {result.get('skipped', 0)} · Destek dışı: {result.get('unsupported', 0)}.",
                'success' if not result.get('errors') else 'warning',
            )
            if result.get('errors'):
                flash(' | '.join(result['errors'][:3]), 'warning')
        else:
            flash('Desteklenmeyen toplu AI işlemi seçildi.', 'warning')
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(f'AI toplu işleminde hata oluştu: {exc}', 'danger')
    return redirect(redirect_url)