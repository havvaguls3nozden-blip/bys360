from __future__ import annotations

import hmac
import logging
import uuid
from pathlib import Path

from flask import (
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import safe_join

from app.extensions import csrf, db
from app.models.announcement_popup_models import Announcement
from app.route_registry import main_bp
from app.route_support import (
    consume_form_token,
    issue_form_token,
    menu_key_required,
    safe_db_rollback,
    safe_render,
)
from app.services.announcement_popup_service import (
    ANNOUNCEMENT_TYPES,
    MEDIA_TYPES,
    SHOW_RULES,
    TARGET_SCOPES,
    acknowledge_announcement,
    announcement_media_root,
    apply_payload_to_announcement,
    build_announcement_acceptance_summary,
    commit_runtime_change,
    count_target_users,
    dismiss_announcement,
    export_announcement_report_csv,
    find_pending_announcement_for_user,
    get_announcement_form_options,
    list_announcement_report_rows,
    normalize_announcement_form,
    process_announcement_media_upload,
    record_announcement_seen,
    safe_media_subpath,
    serialize_runtime_announcement,
    summarize_announcement_reads,
    validate_announcement_payload,
)

logger = logging.getLogger(__name__)

"""BYS360 Duyuru Yönetimi - Video destekli pop-up Faz 5 route'ları."""


def _announcement_form_context(announcement: Announcement | None = None, *, payload: dict | None = None):
    options = get_announcement_form_options()
    form_token = issue_form_token("announcement_popup_form", scope=str(current_user.id))
    data = payload or {}
    return {
        "announcement": announcement,
        "form_token": form_token,
        "announcement_types": options.announcement_types,
        "show_rules": options.show_rules,
        "target_scopes": options.target_scopes,
        "media_types": options.media_types,
        "roles": options.roles,
        "units": options.units,
        "form_data": data,
    }


def _runtime_token_key() -> str:
    # BYS360_V59_3_POPUP_RUNTIME_ANON_SAFE
    try:
        user_id = getattr(current_user, "id", None) if getattr(current_user, "is_authenticated", False) else None
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/announcement_popup_routes.py | line=68")
        user_id = None
    return f"form_token:announcement_popup_runtime:{user_id or 'anonymous'}"


def _get_runtime_token() -> str:
    """Duyuru pop-up işlemleri için sayfa yenilemelerinde bozulmayan oturum tokenı.

    Önceki sürüm tek kullanımlık token tükettiği için, kullanıcı dashboard/anasayfa
    arasında gezdiğinde veya popup açıkken yeni sayfa render edildiğinde Okudum/Daha
    sonra işlemleri gereksiz şekilde güvenlik hatasına düşebiliyordu. Bu token yine
    kullanıcı oturumuna bağlıdır; ancak runtime aksiyonlarında tüketilmez.
    """
    key = _runtime_token_key()
    token = session.get(key)
    if not token:
        token = uuid.uuid4().hex
        session[key] = token
        session.modified = True
    return str(token)


@main_bp.app_context_processor
def announcement_popup_runtime_context():
    if not current_user.is_authenticated:
        return {"announcement_popup_runtime_token": ""}
    return {"announcement_popup_runtime_token": _get_runtime_token()}


def _consume_runtime_token() -> bool:
    submitted = request.form.get("runtime_token") or request.headers.get("X-BYS360-Announcement-Token")
    expected = session.get(_runtime_token_key())
    if not submitted or not expected:
        return False
    return hmac.compare_digest(str(submitted), str(expected))


def _parse_list_filters():
    q = " ".join((request.args.get("q") or "").split())[:120]
    status = (request.args.get("status") or "all").strip().lower()
    if status not in {"all", "active", "inactive", "required"}:
        status = "all"
    return q, status


def _parse_report_filters():
    q = " ".join((request.args.get("q") or "").split())[:120]
    status = (request.args.get("status") or "all").strip().lower()
    allowed = {"all", "acknowledged", "dismissed", "seen", "not_seen", "pending"}
    if status not in allowed:
        status = "all"
    return q, status


def _filter_report_rows(rows: list[dict], q: str, status: str) -> list[dict]:
    filtered = rows
    if status == "pending":
        filtered = [row for row in filtered if row.get("is_pending")]
    elif status != "all":
        filtered = [row for row in filtered if row.get("status_key") == status]

    if q:
        needle = q.lower()
        def matches(row: dict) -> bool:
            haystack = " ".join(str(row.get(key) or "") for key in (
                "full_name", "sicil_no", "email", "role", "unit_name", "status_label"
            )).lower()
            return needle in haystack
        filtered = [row for row in filtered if matches(row)]
    return filtered


def _normalize_payload_with_upload(announcement: Announcement | None = None) -> tuple[dict, list[str]]:
    payload = normalize_announcement_form(request.form)
    errors: list[str] = []
    try:
        process_announcement_media_upload(payload, request.files.get("media_file"), existing=announcement)
    except ValueError as exc:
        errors.append(str(exc))
    errors.extend(validate_announcement_payload(payload))
    return payload, errors


@main_bp.route("/announcements/popup/manage")
@main_bp.route("/announcements/popup")
@main_bp.route("/announcements/manage")
@login_required
@menu_key_required("announcements")
def announcement_popup_manage():
    q, status = _parse_list_filters()
    query = Announcement.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Announcement.title.ilike(like), Announcement.body.ilike(like)))
    if status == "active":
        query = query.filter(Announcement.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(Announcement.is_active.is_(False))
    elif status == "required":
        query = query.filter(Announcement.is_required.is_(True))

    rows = query.order_by(Announcement.updated_at.desc().nullslast(), Announcement.id.desc()).limit(200).all()
    row_summaries = {row.id: summarize_announcement_reads(row) for row in rows}
    counts = {
        "total": Announcement.query.count(),
        "active": Announcement.query.filter(Announcement.is_active.is_(True)).count(),
        "required": Announcement.query.filter(Announcement.is_required.is_(True)).count(),
        "video": Announcement.query.filter(Announcement.media_type.in_(["youtube", "vimeo", "dailymotion", "upload_video"])).count(),
    }
    return safe_render(
        "communication/announcement_popup_manage.html",
        "<h3>Duyuru Yönetimi</h3>",
        rows=rows,
        row_summaries=row_summaries,
        counts=counts,
        q=q,
        status=status,
        announcement_types=ANNOUNCEMENT_TYPES,
        show_rules=SHOW_RULES,
        target_scopes=TARGET_SCOPES,
        media_types=MEDIA_TYPES,
    )


@main_bp.route("/announcements/popup/new", methods=["GET", "POST"])
@main_bp.route("/announcements/manage/new", methods=["GET", "POST"])
@login_required
@menu_key_required("announcements")
def announcement_popup_new():
    if request.method == "POST":
        if not consume_form_token("announcement_popup_form", request.form.get("form_token"), scope=str(current_user.id)):
            flash("Form güvenlik doğrulaması başarısız. Lütfen yeniden deneyin.", "danger")
            return redirect(url_for("main.announcement_popup_new"))
        payload, errors = _normalize_payload_with_upload()
        if errors:
            for error in errors:
                flash(error, "warning")
            return safe_render(
                "communication/announcement_popup_form.html",
                "<h3>Yeni Duyuru</h3>",
                mode="new",
                **_announcement_form_context(payload=payload),
            )
        try:
            announcement = Announcement()
            apply_payload_to_announcement(announcement, payload, actor_id=current_user.id)
            db.session.add(announcement)
            db.session.commit()
            flash("Duyuru kaydı oluşturuldu. Video destekli pop-up akışı aktif.", "success")
            return redirect(url_for("main.announcement_popup_manage"))
        except SQLAlchemyError as exc:
            logger.exception("Duyuru kaydı oluşturulurken veritabanı hatası: %s", exc)
            safe_db_rollback()
            flash("Duyuru kaydı oluşturulamadı.", "danger")

    return safe_render(
        "communication/announcement_popup_form.html",
        "<h3>Yeni Duyuru</h3>",
        mode="new",
        **_announcement_form_context(),
    )


@main_bp.route("/announcements/popup/<int:announcement_id>/edit", methods=["GET", "POST"])
@main_bp.route("/announcements/manage/<int:announcement_id>/edit", methods=["GET", "POST"])
@login_required
@menu_key_required("announcements")
def announcement_popup_edit(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    if request.method == "POST":
        if not consume_form_token("announcement_popup_form", request.form.get("form_token"), scope=str(current_user.id)):
            flash("Form güvenlik doğrulaması başarısız. Lütfen yeniden deneyin.", "danger")
            return redirect(url_for("main.announcement_popup_edit", announcement_id=announcement.id))
        payload, errors = _normalize_payload_with_upload(announcement)
        if errors:
            for error in errors:
                flash(error, "warning")
            return safe_render(
                "communication/announcement_popup_form.html",
                "<h3>Duyuru Düzenle</h3>",
                mode="edit",
                **_announcement_form_context(announcement=announcement, payload=payload),
            )
        try:
            apply_payload_to_announcement(announcement, payload, actor_id=current_user.id)
            db.session.commit()
            flash("Duyuru kaydı güncellendi.", "success")
            return redirect(url_for("main.announcement_popup_manage"))
        except SQLAlchemyError as exc:
            logger.exception("Duyuru kaydı güncellenirken veritabanı hatası: %s", exc)
            safe_db_rollback()
            flash("Duyuru kaydı güncellenemedi.", "danger")

    return safe_render(
        "communication/announcement_popup_form.html",
        "<h3>Duyuru Düzenle</h3>",
        mode="edit",
        **_announcement_form_context(announcement=announcement),
    )


@main_bp.route("/announcements/popup/<int:announcement_id>/toggle", methods=["POST"])
@main_bp.route("/announcements/manage/<int:announcement_id>/toggle", methods=["POST"])
@login_required
@menu_key_required("announcements")
def announcement_popup_toggle(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    try:
        announcement.is_active = not bool(announcement.is_active)
        announcement.updated_by = current_user.id
        db.session.commit()
        flash("Duyuru durumu güncellendi.", "success")
    except SQLAlchemyError as exc:
        logger.exception("Duyuru durumu güncellenirken veritabanı hatası: %s", exc)
        safe_db_rollback()
        flash("Duyuru durumu güncellenemedi.", "danger")
    return redirect(url_for("main.announcement_popup_manage"))


@main_bp.route("/announcements/popup/<int:announcement_id>/target-count")
@main_bp.route("/announcements/manage/<int:announcement_id>/target-count")
@login_required
@menu_key_required("announcements")
def announcement_popup_target_count(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    flash(f"Bu duyurunun hedef kullanıcı sayısı: {count_target_users(announcement)}", "info")
    return redirect(url_for("main.announcement_popup_manage"))


@main_bp.route("/announcements/popup/<int:announcement_id>/report")
@main_bp.route("/announcements/manage/<int:announcement_id>/report")
@login_required
@menu_key_required("announcements")
def announcement_popup_report(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    q, status = _parse_report_filters()
    all_rows = list_announcement_report_rows(announcement)
    rows = _filter_report_rows(all_rows, q, status)
    summary = build_announcement_acceptance_summary(announcement, rows=all_rows)
    status_options = {
        "all": "Tüm kayıtlar",
        "acknowledged": "Okudu",
        "dismissed": "Kapattı",
        "seen": "Gördü",
        "not_seen": "Henüz görmedi",
        "pending": "Onay bekliyor",
    }
    return safe_render(
        "communication/announcement_popup_report.html",
        "<h3>Duyuru Okunma Raporu</h3>",
        announcement=announcement,
        summary=summary,
        rows=rows,
        all_row_count=len(all_rows),
        filtered_row_count=len(rows),
        q=q,
        status=status,
        status_options=status_options,
    )


@main_bp.route("/announcements/popup/<int:announcement_id>/report.csv")
@main_bp.route("/announcements/manage/<int:announcement_id>/report.csv")
@login_required
@menu_key_required("announcements")
def announcement_popup_report_csv(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    csv_body = export_announcement_report_csv(announcement)
    filename = f"bys360_duyuru_{announcement.id}_okunma_raporu.csv"
    return Response(
        csv_body,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@main_bp.route("/announcements/popup/media/<path:filename>")
@login_required
def announcement_popup_media(filename: str):
    clean_name = safe_media_subpath(filename)
    if not clean_name:
        abort(404)
    root = announcement_media_root()
    full_path = safe_join(str(root), clean_name)
    if not full_path or not Path(full_path).is_file():
        abort(404)
    return send_from_directory(str(root), clean_name, as_attachment=False, conditional=True)


@main_bp.route("/announcements/popup/runtime/pending")
@login_required
def announcement_popup_runtime_pending():
    # BYS360_V59_3_POPUP_RUNTIME_PUBLIC_GUARD
    if not getattr(current_user, "is_authenticated", False):
        return jsonify({"ok": True, "has_pending": False, "runtime_token": _get_runtime_token()})
    announcement = find_pending_announcement_for_user(current_user)
    if not announcement:
        return jsonify({"ok": True, "has_pending": False, "runtime_token": _get_runtime_token()})
    try:
        record_announcement_seen(announcement, current_user, request)
        commit_runtime_change()
    except SQLAlchemyError:
        return jsonify({"ok": False, "has_pending": False, "message": "Duyuru okundu kaydı yazılamadı."}), 500
    return jsonify({
        "ok": True,
        "has_pending": True,
        "runtime_token": _get_runtime_token(),
        "announcement": serialize_runtime_announcement(announcement),
    })


@main_bp.route("/announcements/popup/<int:announcement_id>/acknowledge", methods=["POST"])
@csrf.exempt
@login_required
def announcement_popup_acknowledge(announcement_id: int):
    if not _consume_runtime_token():
        return jsonify({"ok": False, "message": "Duyuru güvenlik doğrulaması başarısız."}), 400
    announcement = Announcement.query.get_or_404(announcement_id)
    try:
        acknowledge_announcement(announcement, current_user, request)
        commit_runtime_change()
    except SQLAlchemyError:
        return jsonify({"ok": False, "message": "Okundu kaydı yazılamadı."}), 500
    return jsonify({"ok": True, "message": "Duyuru okundu olarak işaretlendi."})


@main_bp.route("/announcements/popup/<int:announcement_id>/dismiss", methods=["POST"])
@csrf.exempt
@login_required
def announcement_popup_dismiss(announcement_id: int):
    if not _consume_runtime_token():
        return jsonify({"ok": False, "message": "Duyuru güvenlik doğrulaması başarısız."}), 400
    announcement = Announcement.query.get_or_404(announcement_id)
    try:
        dismiss_announcement(announcement, current_user, request)
        commit_runtime_change()
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    except SQLAlchemyError:
        return jsonify({"ok": False, "message": "Kapatma kaydı yazılamadı."}), 500
    return jsonify({"ok": True, "message": "Duyuru kapatıldı."})
