from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_REQUIRED
# STATUS_SOURCE: app.admin.route_manifest REQUIRED_ROUTE_MODULES

import csv
import io
import json

from flask import make_response, request
from flask_login import current_user, login_required
from werkzeug.exceptions import Forbidden

from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_render
from app.services.ai.history_compare import (
    build_ai_decision_history_snapshot,
    build_ai_management_pack,
    build_ai_prompt_compare_snapshot,
    render_ai_management_pack_markdown,
)
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


@main_bp.route("/admin/ai-decision-history")
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_decision_history():
    fallback = _schema_fallback("AI Karar Geçmişi")
    if fallback:
        return fallback
    snapshot = build_ai_decision_history_snapshot(
        lookback_days=_safe_int(request.args.get("lookback_days"), 30),
        module_type=request.args.get("module_type", ""),
        feature_type=request.args.get("feature_type", ""),
        status=request.args.get("status", ""),
        page=_safe_int(request.args.get("page"), 1),
        per_page=_safe_int(request.args.get("per_page"), 20),
    )
    return safe_render("admin_ai_decision_history.html", **snapshot)


@main_bp.route("/admin/ai-prompt-compare")
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_prompt_compare():
    fallback = _schema_fallback("AI İstem Sürüm Karşılaştırması")
    if fallback:
        return fallback
    snapshot = build_ai_prompt_compare_snapshot(
        lookback_days=_safe_int(request.args.get("lookback_days"), 30),
        module_type=request.args.get("module_type", ""),
        feature_type=request.args.get("feature_type", ""),
    )
    return safe_render("admin_ai_prompt_compare.html", **snapshot)


@main_bp.route("/admin/ai-management-pack")
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_management_pack():
    fallback = _schema_fallback("AI Yönetici Rapor Paketi")
    if fallback:
        return fallback
    snapshot = build_ai_management_pack(lookback_days=_safe_int(request.args.get("lookback_days"), 30))
    return safe_render("admin_ai_management_pack.html", **snapshot)


@main_bp.route("/admin/ai-decision-history/export.csv")
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_decision_history_export_csv():
    snapshot = build_ai_decision_history_snapshot(
        lookback_days=_safe_int(request.args.get("lookback_days"), 30),
        module_type=request.args.get("module_type", ""),
        feature_type=request.args.get("feature_type", ""),
        status=request.args.get("status", ""),
        page=1,
        per_page=200,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "tarih",
        "modul",
        "ozellik",
        "hedef",
        "hedef_id",
        "istem_surumu",
        "durum",
        "gecikme_ms",
        "geri_bildirim",
        "negatif_geri_bildirim",
        "acik_oneri",
    ])
    for row in snapshot.get("rows") or []:
        created_at = row.get("created_at")
        writer.writerow([
            created_at.isoformat() if created_at else "",
            row.get("module_type"),
            row.get("feature_type"),
            row.get("target_table"),
            row.get("target_id"),
            row.get("prompt_version"),
            row.get("status"),
            row.get("latency_ms"),
            row.get("feedback_total"),
            row.get("feedback_negative"),
            row.get("open_recommendations"),
        ])
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=ai_decision_history.csv"
    return response


@main_bp.route("/admin/ai-prompt-compare/export.csv")
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_prompt_compare_export_csv():
    snapshot = build_ai_prompt_compare_snapshot(
        lookback_days=_safe_int(request.args.get("lookback_days"), 30),
        module_type=request.args.get("module_type", ""),
        feature_type=request.args.get("feature_type", ""),
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "modul",
        "ozellik",
        "istem_surumu",
        "istek_sayisi",
        "basari_orani",
        "kalite_skoru",
        "stabilite",
        "ortalama_gecikme_ms",
        "acik_oneri",
        "onceki_surum",
        "delta_kalite",
    ])
    for row in snapshot.get("rows") or []:
        writer.writerow([
            row.get("module_type"),
            row.get("feature_type"),
            row.get("prompt_version"),
            row.get("request_total"),
            row.get("success_rate"),
            row.get("quality_score"),
            row.get("stability"),
            row.get("avg_latency_ms"),
            row.get("open_recommendations"),
            row.get("previous_version"),
            row.get("delta_quality"),
        ])
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=ai_prompt_compare.csv"
    return response


@main_bp.route("/admin/ai-management-pack/export.md")
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_management_pack_export_md():
    snapshot = build_ai_management_pack(lookback_days=_safe_int(request.args.get("lookback_days"), 30))
    response = make_response(render_ai_management_pack_markdown(snapshot))
    response.headers["Content-Type"] = "text/markdown; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=ai_management_pack.md"
    return response


@main_bp.route("/admin/ai-management-pack/export.json")
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_management_pack_export_json():
    snapshot = build_ai_management_pack(lookback_days=_safe_int(request.args.get("lookback_days"), 30))
    response = make_response(json.dumps(snapshot, ensure_ascii=False, indent=2, default=str))
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=ai_management_pack.json"
    return response


# ---------------------------------------------------------------------------
# Faz 11 — UI profesyonelleştirme, yönetici ekranları ve güvenli rapor export
# ---------------------------------------------------------------------------
@main_bp.route('/admin/analysis-center/executive-report')
@main_bp.route('/admin/ai-executive-report')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_executive_report():
    """Faz 11: Yönetici ekranı, profesyonel rapor kartları ve güvenli export merkezi."""
    from app.services.ai.executive_report_exports import build_ai_executive_report_snapshot

    fallback = _schema_fallback('AI Yönetici Rapor ve Export Merkezi')
    if fallback:
        return fallback
    snapshot = build_ai_executive_report_snapshot(
        current_user=current_user,
        lookback_days=request.args.get('lookback_days') or 30,
        module_type=request.args.get('module_type') or '',
    )
    return safe_render('admin_ai_executive_report.html', **snapshot)


@main_bp.route('/admin/analysis-center/executive-report/export.csv')
@main_bp.route('/admin/ai-executive-report/export.csv')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_executive_report_export_csv():
    """Faz 11 güvenli CSV export: ham AI metni ve kişisel veri içermez."""
    from app.services.ai.executive_report_exports import EXPORT_COLUMNS, build_ai_executive_report_export_rows, build_ai_executive_report_snapshot

    snapshot = build_ai_executive_report_snapshot(
        current_user=current_user,
        lookback_days=request.args.get('lookback_days') or 30,
        module_type=request.args.get('module_type') or '',
    )
    if not snapshot.get('visibility_policy', {}).get('can_export_safe_csv'):
        raise Forbidden('Bu dışa aktarım için güvenli AI export yetkiniz yok.')
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(EXPORT_COLUMNS)
    for row in build_ai_executive_report_export_rows(snapshot):
        writer.writerow(row)
    response = make_response('\ufeff' + output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_executive_report_safe.csv'
    return response


@main_bp.route('/admin/analysis-center/executive-report/export.json')
@main_bp.route('/admin/ai-executive-report/export.json')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_executive_report_export_json():
    """Faz 11 güvenli JSON export: sadece özet, metrik ve aksiyon satırları."""
    from app.services.ai.executive_report_exports import build_ai_executive_report_snapshot, dumps_safe_json

    snapshot = build_ai_executive_report_snapshot(
        current_user=current_user,
        lookback_days=request.args.get('lookback_days') or 30,
        module_type=request.args.get('module_type') or '',
    )
    if not snapshot.get('visibility_policy', {}).get('can_export_safe_csv'):
        raise Forbidden('Bu dışa aktarım için güvenli AI export yetkiniz yok.')
    response = make_response(dumps_safe_json(snapshot))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_executive_report_safe.json'
    return response


@main_bp.route('/admin/analysis-center/executive-report/export.md')
@main_bp.route('/admin/ai-executive-report/export.md')
@login_required
@admin_required
@menu_key_required('ai_center')
def admin_ai_executive_report_export_md():
    """Faz 11 güvenli Markdown export: yönetici rapor metni."""
    from app.services.ai.executive_report_exports import build_ai_executive_report_snapshot, render_ai_executive_report_markdown

    snapshot = build_ai_executive_report_snapshot(
        current_user=current_user,
        lookback_days=request.args.get('lookback_days') or 30,
        module_type=request.args.get('module_type') or '',
    )
    if not snapshot.get('visibility_policy', {}).get('can_export_safe_csv'):
        raise Forbidden('Bu dışa aktarım için güvenli AI export yetkiniz yok.')
    response = make_response(render_ai_executive_report_markdown(snapshot))
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=ai_executive_report_safe.md'
    return response

