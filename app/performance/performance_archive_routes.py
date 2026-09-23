from __future__ import annotations

import logging
from io import BytesIO

from flask import flash, redirect, request, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.performance_archive_models import PerformanceArchivedResult
from app.route_registry import main_bp
from app.route_support import render_access_denied, safe_render
from app.services.performance.archive_service import (
    apply_archive_search_filters,
    archive_visibility_context,
    archive_year_options_for_user,
    build_archive_excel_template_bytes,
    build_archive_query_for_user,
    build_archive_summary,
    can_manage_archive,
    can_view_archived_result,
    create_manual_archive_result,
    display_name,
    import_archive_results_from_excel,
    manual_entry_employee_options,
)
from app.services.runtime_page_cache_v4 import (  # BYS360_RUNTIME_PAGE_CACHE_V4
    bys360_get_page_cache,
    bys360_set_page_cache,
)

"""BYS360 Faz 7.5 — Geçmiş Karne Arşivi yönetici görünürlüğü route ailesi.

Faz 7.5 kapsamı:
- Personel yalnızca kendi geçmiş karne arşivini görür.
- Yönetici yalnızca kendi yetki kapsamındaki geçmişi görür.
- Detay sayfası doğrudan URL ile kapsam dışına açılmaz.
- Excel ve manuel giriş yetkili kullanıcılarla sınırlı kalır.
"""
logger = logging.getLogger(__name__)

# BYS360_PHASE7_4_PERFORMANCE_ARCHIVE_PERSONNEL_VISIBILITY_ROUTES
# BYS360_PHASE7_5_PERFORMANCE_ARCHIVE_MANAGER_VISIBILITY_ROUTES


def _visible_archive_query():
    query = build_archive_query_for_user(current_user).options(
        joinedload(PerformanceArchivedResult.employee),  # type: ignore[arg-type]
        joinedload(PerformanceArchivedResult.created_by),  # type: ignore[arg-type]
    )
    return query


@main_bp.route("/performance/archive", methods=["GET"])
@main_bp.route("/performans/gecmis-karne-arsivi", methods=["GET"])
@login_required
def performance_archive():
    # BYS360_RUNTIME_ARCHIVE_HOME_CACHE_V4B_archive
    _bys360_archive_cache_key = (
        'performance_archive_v4b',
        getattr(current_user, 'id', 0),
        getattr(current_user, 'role', ''),
        request.full_path,
    )
    _bys360_archive_cached_response = bys360_get_page_cache(_bys360_archive_cache_key, ttl_seconds=30)
    if _bys360_archive_cached_response is not None:
        return _bys360_archive_cached_response
    q = (request.args.get("q") or "").strip()
    year = request.args.get("year", type=int)
    query = apply_archive_search_filters(_visible_archive_query(), q=q, year=year)
    rows = query.order_by(
        PerformanceArchivedResult.result_year.desc(),
        PerformanceArchivedResult.period_label.desc(),
        PerformanceArchivedResult.created_at.desc(),
        PerformanceArchivedResult.id.desc(),
    ).limit(500).all()
    return bys360_set_page_cache(_bys360_archive_cache_key, safe_render(
        "performance/archive/index.html",
        "<h3>Geçmiş Karne Arşivi</h3>",
        rows=rows,
        summary=build_archive_summary(rows),
        years=archive_year_options_for_user(current_user),
        selected_year=year,
        q=q,
        can_manage_archive=can_manage_archive(current_user),
        visibility_context=archive_visibility_context(current_user),
        display_name=display_name,
    ), ttl_seconds=30)


@main_bp.route("/performance/archive/import", methods=["GET", "POST"])
@main_bp.route("/performans/gecmis-karne-arsivi/excel", methods=["GET", "POST"])
@login_required
def performance_archive_import():
    """Excel yükleme Geçmiş Karne Arşivi içinde tek merkezde çalışır."""
    if not can_manage_archive(current_user):
        return render_access_denied("Geçmiş karne arşivine Excel yükleme yetkiniz bulunmamaktadır.")

    result = None
    if request.method == "POST":
        upload = request.files.get("archive_excel")
        if not upload or not upload.filename:
            flash("Lütfen .xlsx formatında bir Excel dosyası seçin.", "warning")
        else:
            try:
                result = import_archive_results_from_excel(upload, actor=current_user)
                if result.get("created", 0):
                    flash(f"Excel aktarımı tamamlandı. {result.get('created', 0)} kayıt arşive eklendi.", "success")
                if result.get("skipped", 0):
                    flash(f"{result.get('skipped', 0)} satır atlandı. Ayrıntılar ekranda gösteriliyor.", "warning")
                for warning in result.get("schema_warnings", []) or []:
                    flash(warning, "warning")
                if not result.get("created", 0) and not result.get("skipped", 0):
                    flash("Excel dosyasında aktarılacak satır bulunamadı.", "info")
            except Exception as exc:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı. | exc=%s", exc)
                db.session.rollback()
                flash("Excel aktarımı yapılamadı.", "danger")

    return safe_render(
        "performance/archive/import.html",
        "<h3>Geçmiş Karne Excel Yükleme</h3>",
        result=result,
    )


@main_bp.route("/performance/archive/import/template", methods=["GET"])
@main_bp.route("/performans/gecmis-karne-arsivi/excel-sablon", methods=["GET"])
@login_required
def performance_archive_import_template():
    if not can_manage_archive(current_user):
        return render_access_denied("Geçmiş karne arşivi Excel şablonu indirme yetkiniz bulunmamaktadır.")
    data = build_archive_excel_template_bytes()
    return send_file(
        BytesIO(data),
        as_attachment=True,
        download_name="bys360_gecmis_karne_arsivi_sablon.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# BYS360_PHASE7_6_TEMPLATE_ENDPOINT_ALIAS_V2
@main_bp.route("/performance/archive/template", methods=["GET"])
@main_bp.route("/performans/gecmis-karne-arsivi/sablon", methods=["GET"])
@login_required
def performance_archive_template():
    # Faz 7.6 final gate için Excel şablonu endpoint alias'ı.
    # Faz 7.3 endpointi performance_archive_import_template olarak korunur.
    return performance_archive_import_template()

@main_bp.route("/performance/archive/<int:result_id>", methods=["GET"])
@main_bp.route("/performans/gecmis-karne-arsivi/<int:result_id>", methods=["GET"])
@login_required
def performance_archive_detail(result_id: int):
    result = PerformanceArchivedResult.query.options(
        joinedload(PerformanceArchivedResult.employee),  # type: ignore[arg-type]
        joinedload(PerformanceArchivedResult.created_by),  # type: ignore[arg-type]
    ).get_or_404(result_id)
    if not can_view_archived_result(current_user, result):
        return render_access_denied()
    return safe_render(
        "performance/archive/detail.html",
        "<h3>Geçmiş Karne Detayı</h3>",
        result=result,
        display_name=display_name,
        can_manage_archive=can_manage_archive(current_user),
        visibility_context=archive_visibility_context(current_user),
    )


@main_bp.route("/performance/archive/new", methods=["GET", "POST"])
@main_bp.route("/performans/gecmis-karne-arsivi/yeni", methods=["GET", "POST"])
@login_required
def performance_archive_new():
    if not can_manage_archive(current_user):
        return render_access_denied("Geçmiş karne arşivine manuel kayıt ekleme yetkiniz bulunmamaktadır.")

    employees = manual_entry_employee_options(current_user)
    if request.method == "GET":
        return safe_render(
            "performance/archive/form.html",
            "<h3>Geçmiş Puan Ekle</h3>",
            employees=employees,
            display_name=display_name,
        )

    try:
        result = create_manual_archive_result(
            actor=current_user,
            employee_id=request.form.get("employee_id"),
            result_year=request.form.get("result_year"),
            period_label=request.form.get("period_label"),
            score=request.form.get("score"),
            description=request.form.get("description"),
            source_document=request.form.get("source_document"),
            source_document_name=request.form.get("source_document_name") or request.form.get("source_document"),
        )
        flash("Geçmiş performans puanı arşive eklendi.", "success")
        return redirect(url_for("main.performance_archive_detail", result_id=result.id))
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı. | exc=%s", exc)
        db.session.rollback()
        flash("Kayıt eklenemedi.", "danger")
        return safe_render(
            "performance/archive/form.html",
            "<h3>Geçmiş Puan Ekle</h3>",
            employees=employees,
            display_name=display_name,
        )
