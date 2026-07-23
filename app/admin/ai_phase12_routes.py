# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_REQUIRED
# STATUS_SOURCE: app.admin.route_manifest REQUIRED_ROUTE_MODULES
"""BYS360 AI Faz 12 — final canlı sertleştirme route katmanı.

Amaç:
    AI Karar Destek Merkezi için final canlı sertleştirme, kalite kapısı,
    CSV dışa aktarma ve kapanış raporu ekranlarını sağlar.

Kaldırma/taşıma koşulu:
    Canlı pilot stabil hale geldiğinde bu dosya `ai_final_hardening_routes.py`
    gibi kalıcı ve anlamlı bir route adına taşınabilir. Taşıma yapılana kadar
    faz sözlüğü ve gate testleri bu dosyayı açıkça belgelemelidir.

Bağımlılıklar:
    - app.route_registry.main_bp
    - app.route_support.admin_required, menu_key_required, safe_render
    - app.services.ai.schema_guard.get_ai_schema_status
    - app.services.ai.final_live_hardening servis ailesi
"""
from __future__ import annotations

import csv
import io

from flask import make_response, request
from flask_login import current_user, login_required
from werkzeug.exceptions import Forbidden

from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_render
from app.services.ai.schema_guard import get_ai_schema_status


def _safe_int(value: str | None, default: int = 30) -> int:
    try:
        return max(int(value or default), 1)
    except (TypeError, ValueError):
        return default


def _schema_fallback(page_title: str):
    schema_status = get_ai_schema_status()
    if schema_status.get("ready"):
        return None
    return safe_render(
        "admin_ai_schema_not_ready.html",
        page_title=page_title,
        selected_module_type="",
        ai_schema_status=schema_status,
        module_options=[],
    )


# ---------------------------------------------------------------------------
# Faz 12 — Final canlı sertleştirme, kalite kapısı ve kapanış raporu
# ---------------------------------------------------------------------------
@main_bp.route('/admin/analysis-center/final-live-hardening')
@main_bp.route('/admin/ai-final-live-hardening')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_final_live_hardening():
    """Faz 12: final canlı sertleştirme, kalite kapısı ve kapanış raporu."""
    from app.services.ai.final_live_hardening import build_ai_final_live_hardening_snapshot

    fallback = _schema_fallback('AI Final Canlı Sertleştirme')
    if fallback:
        return fallback
    snapshot = build_ai_final_live_hardening_snapshot(
        current_user=current_user,
        lookback_days=_safe_int(request.args.get('lookback_days'), 30),
    )
    return safe_render('admin_ai_final_live_hardening.html', **snapshot)


@main_bp.route('/admin/analysis-center/final-live-hardening/export.csv')
@main_bp.route('/admin/ai-final-live-hardening/export.csv')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_final_live_hardening_export_csv():
    """Faz 12 güvenli CSV kapanış raporu: ham AI metni ve kişisel veri içermez."""
    from app.services.ai.final_live_hardening import (
        EXPORT_COLUMNS,
        build_ai_final_live_hardening_export_rows,
        build_ai_final_live_hardening_snapshot,
    )

    snapshot = build_ai_final_live_hardening_snapshot(
        current_user=current_user,
        lookback_days=_safe_int(request.args.get('lookback_days'), 30),
    )
    if not snapshot.get('visibility_policy', {}).get('can_export_safe_csv', True):
        raise Forbidden('Bu dışa aktarım için güvenli AI export yetkiniz yok.')
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(EXPORT_COLUMNS)
    for row in build_ai_final_live_hardening_export_rows(snapshot):
        writer.writerow(row)
    response = make_response('\ufeff' + output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_final_live_hardening_safe.csv'
    return response


@main_bp.route('/admin/analysis-center/final-live-hardening/export.json')
@main_bp.route('/admin/ai-final-live-hardening/export.json')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_final_live_hardening_export_json():
    """Faz 12 güvenli JSON kapanış raporu: yalnız özet, metrik ve kalite kapısı."""
    from app.services.ai.final_live_hardening import (
        build_ai_final_live_hardening_snapshot,
        dumps_safe_json,
    )

    snapshot = build_ai_final_live_hardening_snapshot(
        current_user=current_user,
        lookback_days=_safe_int(request.args.get('lookback_days'), 30),
    )
    if not snapshot.get('visibility_policy', {}).get('can_export_safe_csv', True):
        raise Forbidden('Bu dışa aktarım için güvenli AI export yetkiniz yok.')
    response = make_response(dumps_safe_json(snapshot))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_final_live_hardening_safe.json'
    return response


@main_bp.route('/admin/analysis-center/final-live-hardening/export.md')
@main_bp.route('/admin/ai-final-live-hardening/export.md')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_final_live_hardening_export_md():
    """Faz 12 güvenli Markdown kapanış raporu."""
    from app.services.ai.final_live_hardening import (
        build_ai_final_live_hardening_snapshot,
        render_ai_final_live_hardening_markdown,
    )

    snapshot = build_ai_final_live_hardening_snapshot(
        current_user=current_user,
        lookback_days=_safe_int(request.args.get('lookback_days'), 30),
    )
    if not snapshot.get('visibility_policy', {}).get('can_export_safe_csv', True):
        raise Forbidden('Bu dışa aktarım için güvenli AI export yetkiniz yok.')
    response = make_response(render_ai_final_live_hardening_markdown(snapshot))
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_final_live_hardening_safe.md'
    return response
