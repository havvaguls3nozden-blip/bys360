from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from flask import abort, flash, redirect, request, send_file, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.route_registry import main_bp
from app.route_support import manager_required, safe_db_rollback, safe_render
from app.services.publication_service import (
    archive_publication_issue,
    build_publication_library_context,
    get_publication_issue_or_404,
    get_publication_page_count,
    permanent_delete_publication_issue,
    publication_renderer_available,
    publication_type_label,
    render_publication_page_image,
    toggle_featured_publication,
    update_publication_status,
    upload_publication_issue,
)

logger = logging.getLogger(__name__)


def _parse_date(value: str | None):
    raw = (value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/institutional/publication_routes.py:34)")
            continue
    raise ValueError("Yayın tarihi geçerli değil.")


@main_bp.route("/publications")
@login_required
def publication_library():
    can_manage = current_user.role in ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"]
    year_raw = (request.args.get("year") or "").strip()
    try:
        selected_year = int(year_raw) if year_raw else None
    except ValueError:
        selected_year = None
    context = build_publication_library_context(
        q=request.args.get("q"),
        publication_type=request.args.get("publication_type"),
        selected_year=selected_year,
        status_filter=request.args.get("status"),
        can_manage=can_manage,
    )
    return safe_render(
        "publications/library.html",
        "<h3>Kurumsal yayınlar sayfası yüklenemedi</h3>",
        **context,
    )


@main_bp.route("/publications/upload", methods=["POST"])
@login_required
@manager_required
def publication_upload():
    file_storage = request.files.get("publication_file")
    if not file_storage or not getattr(file_storage, "filename", ""):
        flash("Bir PDF dosyası seçmelisiniz.", "warning")
        return redirect(url_for("main.publication_library"))
    try:
        upload_publication_issue(
            file_storage=file_storage,
            title=(request.form.get("title") or "").strip(),
            subtitle=(request.form.get("subtitle") or "").strip() or None,
            summary=(request.form.get("summary") or "").strip() or None,
            publication_type=request.form.get("publication_type"),
            issue_no=(request.form.get("issue_no") or "").strip() or None,
            publication_period=(request.form.get("publication_period") or "").strip() or None,
            publication_date=_parse_date(request.form.get("publication_date")),
            allow_download=str(request.form.get("allow_download") or "1").strip().lower() in {"1", "true", "on", "yes", "evet"},
            is_featured=str(request.form.get("is_featured") or "").strip().lower() in {"1", "true", "on", "yes", "evet"},
            status=request.form.get("status"),
            uploaded_by_id=current_user.id,
        )
        db.session.commit()
        flash("Kurumsal yayın eklendi.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(f"Kurumsal yayın yüklenemedi: {exc}", "danger")
    return redirect(url_for("main.publication_library"))


@main_bp.route("/publications/<int:publication_id>")
@login_required
def publication_view(publication_id: int):
    can_manage = current_user.role in ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"]
    row = get_publication_issue_or_404(publication_id, include_archived=can_manage)
    return safe_render(
        "publications/viewer.html",
        "<h3>Kurumsal yayın görüntüleyicisi yüklenemedi</h3>",
        publication=row,
        can_manage_publications=can_manage,
        type_label=publication_type_label(row.publication_type),
        inline_pdf_url=url_for("main.publication_inline_pdf", publication_id=row.id),
        page_count=get_publication_page_count(row),
        renderer_available=publication_renderer_available(),
        page_image_template=url_for("main.publication_page_image", publication_id=row.id, page_token="__PAGE__"),
    )


@main_bp.route("/publications/<int:publication_id>/file")
@login_required
def publication_inline_pdf(publication_id: int):
    can_manage = current_user.role in ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"]
    row = get_publication_issue_or_404(publication_id, include_archived=can_manage)
    abs_path = Path(row.storage_path or "")
    if not abs_path.is_file():
        abort(404)
    return send_file(abs_path, mimetype=row.mime_type or "application/pdf", as_attachment=False, download_name=row.original_filename)


@main_bp.route("/publications/<int:publication_id>/pages/<page_token>.png")
@login_required
def publication_page_image(publication_id: int, page_token: str):
    can_manage = current_user.role in ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"]
    row = get_publication_issue_or_404(publication_id, include_archived=can_manage)
    try:
        page_number = int(str(page_token).strip())
    except Exception:
        abort(404)
    width_raw = (request.args.get("w") or "1400").strip()
    try:
        width = int(width_raw)
    except ValueError:
        width = 1400
    try:
        png_path = render_publication_page_image(publication=row, page_number=page_number, width=width)
    except IndexError:
        abort(404)
    except FileNotFoundError:
        abort(404)
    except RuntimeError as exc:
        abort(503, description=str(exc))
    return send_file(png_path, mimetype="image/png", as_attachment=False, download_name=png_path.name)


@main_bp.route("/publications/<int:publication_id>/download")
@login_required
def publication_download(publication_id: int):
    can_manage = current_user.role in ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"]
    row = get_publication_issue_or_404(publication_id, include_archived=can_manage)
    if not row.allow_download:
        abort(403)
    abs_path = Path(row.storage_path or "")
    if not abs_path.is_file():
        abort(404)
    return send_file(abs_path, mimetype=row.mime_type or "application/pdf", as_attachment=True, download_name=row.original_filename)


@main_bp.route("/publications/<int:publication_id>/feature", methods=["POST"])
@login_required
@manager_required
def publication_toggle_featured(publication_id: int):
    try:
        row = toggle_featured_publication(publication_id=publication_id, user_id=current_user.id)
        db.session.commit()
        flash("Öne çıkan yayın durumu güncellendi.", "success")
        return redirect(url_for("main.publication_view", publication_id=row.id))
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(f"İşlem tamamlanamadı: {exc}", "danger")
        return redirect(url_for("main.publication_library"))


@main_bp.route("/publications/<int:publication_id>/status", methods=["POST"])
@login_required
@manager_required
def publication_set_status(publication_id: int):
    try:
        row = update_publication_status(
            publication_id=publication_id,
            status=request.form.get("status") or "published",
            user_id=current_user.id,
        )
        db.session.commit()
        flash("Yayın durumu güncellendi.", "success")
        return redirect(url_for("main.publication_view", publication_id=row.id))
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(f"Durum güncellenemedi: {exc}", "danger")
        return redirect(url_for("main.publication_library"))


@main_bp.route("/publications/<int:publication_id>/archive", methods=["POST"])
@login_required
@manager_required
def publication_archive(publication_id: int):
    try:
        archive_publication_issue(publication_id=publication_id, user_id=current_user.id)
        db.session.commit()
        flash("Yayın arşive alındı.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(f"Arşivleme yapılamadı: {exc}", "danger")
    return redirect(url_for("main.publication_library"))

@main_bp.route("/publications/<int:publication_id>/delete", methods=["POST"])
@login_required
@manager_required
def publication_delete(publication_id: int):
    try:
        payload = permanent_delete_publication_issue(publication_id=publication_id, user_id=current_user.id)
        db.session.commit()
        flash(f"Yayın kalıcı olarak silindi: {payload.get('title')}", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(f"Yayın silinemedi: {exc}", "danger")
    return redirect(url_for("main.publication_library"))