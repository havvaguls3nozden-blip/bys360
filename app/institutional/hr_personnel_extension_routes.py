from __future__ import annotations

import logging
from datetime import date
from typing import Any

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import inspect

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import (
    PersonnelAssetAssignment,
    PersonnelChecklistReview,
    PersonnelChecklistTemplateItem,
    PersonnelDocument,
    PersonnelDocumentReminderLog,
    User,
)
from app.route_registry import main_bp
from app.route_support import (
    consume_form_token,
    issue_form_token,
    manager_required,
    menu_key_required,
    safe_db_rollback,
    safe_render,
)

from .hr_personnel_operations_routes import (
    _current_scope_bundle,
    _full_name,
    _normalize_text,
    _parse_date,
    _redirect_operations,
    _require_user_in_scope,
    _safe_int,
)

logger = logging.getLogger(__name__)

ASSET_STATUS_LABELS = {
    "assigned": "Zimmette",
    "returned": "Teslim Alındı",
    "lost": "Kayıp / Eksik",
    "repair": "Bakım / Servis",
}

CHECKLIST_STATUS_LABELS = {
    "pending": "Bekliyor",
    "approved": "Onaylandı",
    "revision": "Revizyon İstendi",
    "rejected": "Reddedildi",
}

REMINDER_TYPE_LABELS = {
    "manual": "Manuel",
    "critical": "Kritik",
    "soon": "Yaklaşan",
    "expired": "Süresi Dolan",
}

REMINDER_LOG_STATUS_LABELS = {
    "queued": "Kuyrukta",
    "sent": "Gönderildi",
    "delivered": "İletildi",
    "failed": "Başarısız",
}

DEFAULT_CHECKLIST_ITEMS = [
    {"code": "kimlik_bilgisi", "label": "Kimlik ve temel profil kontrolü", "category": "ozluk", "description": "Ad, soyad, sicil, e-posta ve birim bilgileri doğrulandı.", "sort_order": 10},
    {"code": "atama_yazisi", "label": "Atama / görevlendirme yazısı", "category": "gorev", "description": "Aktif görev veya son atama yazısı dosyada mevcut.", "sort_order": 20},
    {"code": "ozluk_evrak", "label": "Zorunlu özlük evrak tamlığı", "category": "ozluk", "description": "Zorunlu evrak listesi güncel ve eksiksiz.", "sort_order": 30},
    {"code": "teslim_zimmet", "label": "Zimmet ve teslim kaydı", "category": "zimmet", "description": "Üzerindeki cihaz / demirbaş kayıtları kontrol edildi.", "sort_order": 40},
    {"code": "gecerlilik_takibi", "label": "Belge geçerlilik takibi", "category": "uyari", "description": "Süresi yaklaşan belge ve sertifikalar için aksiyon alındı.", "sort_order": 50},
]


def _table_exists(table_name: str) -> bool:
    try:
        return table_name in set(inspect(db.engine).get_table_names())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_personnel_extension_routes.py:68")
        return False


def _asset_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return ASSET_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _checklist_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return CHECKLIST_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _reminder_type_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return REMINDER_TYPE_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _reminder_log_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return REMINDER_LOG_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _ensure_checklist_seed() -> None:
    if not _table_exists("personnel_checklist_template_items"):
        return
    if PersonnelChecklistTemplateItem.query.count() > 0:
        return
    for item in DEFAULT_CHECKLIST_ITEMS:
        db.session.add(PersonnelChecklistTemplateItem(**item, is_required=True, is_active=True))
    db.session.commit()


def _asset_in_scope(asset_id: int | None, scope_user_ids: set[int]) -> PersonnelAssetAssignment:
    if not asset_id:
        raise ValueError("Zimmet kaydı bulunamadı.")
    row = PersonnelAssetAssignment.query.filter(
        PersonnelAssetAssignment.id == int(asset_id),
        PersonnelAssetAssignment.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Zimmet kaydı bu kapsam içinde bulunamadı.")
    return row


def _review_in_scope(review_id: int | None, scope_user_ids: set[int]) -> PersonnelChecklistReview:
    if not review_id:
        raise ValueError("Checklist kaydı bulunamadı.")
    row = PersonnelChecklistReview.query.filter(
        PersonnelChecklistReview.id == int(review_id),
        PersonnelChecklistReview.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Checklist kaydı bu kapsam içinde bulunamadı.")
    return row


def _document_in_scope(document_id: int | None, scope_user_ids: set[int]) -> PersonnelDocument:
    if not document_id:
        raise ValueError("Belge kaydı bulunamadı.")
    row = PersonnelDocument.query.filter(
        PersonnelDocument.id == int(document_id),
        PersonnelDocument.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Belge kaydı bu kapsam içinde bulunamadı.")
    return row


def _selected_user(scope_users: list[User], scope_user_ids: set[int]) -> User | None:
    selected_user_id = _safe_int(request.args.get("user_id"))
    if selected_user_id and selected_user_id in scope_user_ids:
        return db.session.get(User, int(selected_user_id))
    return scope_users[0] if scope_users else None


def _base_context():
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    selected_scope_mode = (hr_scope or {}).get("scope_mode") or "personal"
    selected_user = _selected_user(scope_users, scope_user_ids)
    return hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user


def _scope_user_options(scope_users: list[User]) -> list[dict[str, object]]:
    rows = []
    for user in scope_users:
        rows.append({
            "id": int(user.id),
            "full_name": _full_name(user),
            "unit_name": (getattr(user, "birim", None) or getattr(user, "ust_birim", None) or "-").strip() or "-",
        })
    return rows


@main_bp.route("/hr-management/personnel-operations/assets")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_assets_center():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user = _base_context()
    if not _table_exists("personnel_asset_assignments"):
        return safe_render("hr_personnel_assets_center.html", assets_ready=False, hr_scope=hr_scope, selected_scope_mode=selected_scope_mode, scope_user_options=_scope_user_options(scope_users), selected_user=None)

    selected_asset = None
    edit_asset_id = _safe_int(request.args.get("edit_asset_id"))
    if edit_asset_id:
        selected_asset = _asset_in_scope(edit_asset_id, scope_user_ids)
        selected_user = db.session.get(User, int(selected_asset.user_id)) or selected_user

    selected_rows = []
    due_rows = []
    summary = {"assigned": 0, "returned": 0, "overdue": 0, "tracked": 0}
    if scope_user_ids:
        rows = PersonnelAssetAssignment.query.filter(PersonnelAssetAssignment.user_id.in_(list(scope_user_ids))).order_by(PersonnelAssetAssignment.assigned_date.desc(), PersonnelAssetAssignment.id.desc()).all()
        today = date.today()
        for row in rows:
            summary["tracked"] += 1
            status = (row.status or "assigned").strip().lower()
            if status == "returned":
                summary["returned"] += 1
            else:
                summary["assigned"] += 1
            is_overdue = bool(row.due_return_date and status != "returned" and row.due_return_date < today)
            payload = {
                "id": int(row.id),
                "user_id": int(row.user_id),
                "user_name": _full_name(getattr(row, "user", None)),
                "asset_category": row.asset_category or "demirbas",
                "asset_name": row.asset_name or "Demirbaş",
                "asset_code": row.asset_code or "-",
                "serial_no": row.serial_no or "-",
                "status": status,
                "status_label": _asset_status_label(status),
                "assigned_date": row.assigned_date,
                "due_return_date": row.due_return_date,
                "returned_date": row.returned_date,
                "note": row.note or "",
                "is_overdue": is_overdue,
            }
            if is_overdue:
                summary["overdue"] += 1
                due_rows.append(payload)
            if selected_user and int(row.user_id) == int(selected_user.id):
                selected_rows.append(payload)

    return safe_render(
        "hr_personnel_assets_center.html",
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        assets_ready=True,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        selected_asset=selected_asset,
        selected_asset_rows=selected_rows,
        due_asset_rows=due_rows[:12],
        asset_summary=summary,
        asset_form_token=issue_form_token("hr_personnel_asset_save", scope="hr_personnel_operations"),
        asset_delete_token=issue_form_token("hr_personnel_asset_delete", scope="hr_personnel_operations"),
        asset_return_token=issue_form_token("hr_personnel_asset_return", scope="hr_personnel_operations"),
        asset_status_options=list(ASSET_STATUS_LABELS.items()),
    )


@main_bp.route("/hr-management/personnel-operations/assets/save", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_asset_save():
    if not consume_form_token("hr_personnel_asset_save", request.form.get("form_token"), scope="hr_personnel_operations"):
        flash("Form oturumu doğrulanamadı. Lütfen tekrar deneyin.", "warning")
        return _redirect_operations(user_id=_safe_int(request.form.get("user_id")))
    hr_scope, _, scope_user_ids, _, _ = _base_context()
    try:
        if not _table_exists("personnel_asset_assignments"):
            raise ValueError("Zimmet tablosu henüz hazır değil.")
        user = _require_user_in_scope(_safe_int(request.form.get("user_id")), scope_user_ids)
        row_id = _safe_int(request.form.get("asset_id"))
        row = _asset_in_scope(row_id, scope_user_ids) if row_id else PersonnelAssetAssignment(user_id=user.id, assigned_by_id=getattr(current_user, "id", None))
        asset_name = _normalize_text(request.form.get("asset_name"), 255)
        if not asset_name:
            raise ValueError("Demirbaş / zimmet adı zorunludur.")
        assigned_date = _parse_date(request.form.get("assigned_date")) or date.today()
        row.user_id = int(user.id)
        row.asset_category = _normalize_text(request.form.get("asset_category"), 50) or "demirbas"
        row.asset_name = asset_name
        row.asset_code = _normalize_text(request.form.get("asset_code"), 120) or None
        row.serial_no = _normalize_text(request.form.get("serial_no"), 120) or None
        row.status = _normalize_text(request.form.get("status"), 30).lower() or "assigned"
        row.assigned_date = assigned_date
        row.due_return_date = _parse_date(request.form.get("due_return_date"))
        row.returned_date = _parse_date(request.form.get("returned_date"))
        row.received_by_id = _safe_int(request.form.get("received_by_id")) or getattr(current_user, "id", None)
        row.note = (request.form.get("note") or "").strip() or None
        db.session.add(row)
        db.session.commit()
        flash("Zimmet / teslim kaydı kaydedildi.", "success")
        return redirect(url_for("main.hr_personnel_assets_center", scope=(request.form.get("scope") or "").strip() or None, user_id=user.id))
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
        return redirect(url_for("main.hr_personnel_assets_center", scope=(request.form.get("scope") or "").strip() or None, user_id=_safe_int(request.form.get("user_id")) or None))


@main_bp.route("/hr-management/personnel-operations/assets/<int:asset_id>/return", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_asset_return(asset_id: int):
    if not consume_form_token("hr_personnel_asset_return", request.form.get("form_token"), scope="hr_personnel_operations"):
        flash("Form oturumu doğrulanamadı. Lütfen tekrar deneyin.", "warning")
        return redirect(url_for("main.hr_personnel_assets_center", scope=(request.form.get("scope") or "").strip() or None, user_id=_safe_int(request.form.get("user_id")) or None))
    _, _, scope_user_ids, _, _ = _base_context()
    try:
        row = _asset_in_scope(asset_id, scope_user_ids)
        row.status = "returned"
        row.returned_date = _parse_date(request.form.get("returned_date")) or date.today()
        db.session.add(row)
        db.session.commit()
        flash("Zimmet kaydı teslim alındı olarak işlendi.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
    return redirect(url_for("main.hr_personnel_assets_center", scope=(request.form.get("scope") or "").strip() or None, user_id=_safe_int(request.form.get("user_id")) or None))


@main_bp.route("/hr-management/personnel-operations/assets/<int:asset_id>/delete", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_asset_delete(asset_id: int):
    if not consume_form_token("hr_personnel_asset_delete", request.form.get("form_token"), scope="hr_personnel_operations"):
        flash("Form oturumu doğrulanamadı. Lütfen tekrar deneyin.", "warning")
        return redirect(url_for("main.hr_personnel_assets_center", scope=(request.form.get("scope") or "").strip() or None, user_id=_safe_int(request.form.get("user_id")) or None))
    _, _, scope_user_ids, _, _ = _base_context()
    try:
        row = _asset_in_scope(asset_id, scope_user_ids)
        db.session.delete(row)
        db.session.commit()
        flash("Zimmet kaydı silindi.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
    return redirect(url_for("main.hr_personnel_assets_center", scope=(request.form.get("scope") or "").strip() or None, user_id=_safe_int(request.form.get("user_id")) or None))


@main_bp.route("/hr-management/personnel-operations/checklists")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_checklist_center():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user = _base_context()
    if not (_table_exists("personnel_checklist_template_items") and _table_exists("personnel_checklist_reviews")):
        return safe_render("hr_personnel_checklist_center.html", checklist_ready=False, hr_scope=hr_scope, selected_scope_mode=selected_scope_mode, scope_user_options=_scope_user_options(scope_users), selected_user=None)
    _ensure_checklist_seed()
    template_rows = PersonnelChecklistTemplateItem.query.filter_by(is_active=True).order_by(PersonnelChecklistTemplateItem.sort_order.asc(), PersonnelChecklistTemplateItem.id.asc()).all()
    review_map = {}
    if selected_user:
        for row in PersonnelChecklistReview.query.filter_by(user_id=selected_user.id).all():
            review_map[int(row.template_item_id)] = row
    selected_review = None
    edit_review_id = _safe_int(request.args.get("edit_review_id"))
    if edit_review_id:
        selected_review = _review_in_scope(edit_review_id, scope_user_ids)
        selected_user = db.session.get(User, int(selected_review.user_id)) or selected_user
        review_map[int(selected_review.template_item_id)] = selected_review

    selected_rows = []
    approved = 0
    pending = 0
    rejected = 0
    for item in template_rows:
        review = review_map.get(int(item.id))
        status = (getattr(review, "status", None) or "pending").strip().lower()
        if status == "approved":
            approved += 1
        elif status == "rejected":
            rejected += 1
        else:
            pending += 1
        selected_rows.append({
            "template_id": int(item.id),
            "template_code": item.code,
            "label": item.label,
            "category": item.category,
            "description": item.description or "",
            "review_id": int(review.id) if review else None,
            "status": status,
            "status_label": _checklist_status_label(status),
            "checked_at": getattr(review, "checked_at", None),
            "expiry_date": getattr(review, "expiry_date", None),
            "note": getattr(review, "note", None) or "",
            "checked_by_name": _full_name(getattr(review, "checked_by", None)) if review else "-",
        })

    team_rows: list[dict[str, Any]] = []
    if scope_user_ids and template_rows:
        template_count = len(template_rows)
        for user in scope_users:
            user_reviews = PersonnelChecklistReview.query.filter_by(user_id=user.id).all()
            review_by_template = {int(r.template_item_id): r for r in user_reviews}
            approved_count = sum(1 for item in template_rows if (getattr(review_by_template.get(int(item.id)), "status", None) or "pending") == "approved")
            pending_count = template_count - approved_count
            team_rows.append({
                "user_id": int(user.id),
                "user_name": _full_name(user),
                "unit_name": (getattr(user, "birim", None) or getattr(user, "ust_birim", None) or "-").strip() or "-",
                "approved_count": approved_count,
                "pending_count": pending_count,
                "ratio": 100 if template_count == 0 else int(round((approved_count / template_count) * 100)),
            })
        team_rows.sort(key=lambda row: (row["ratio"], row["user_name"].lower()))

    return safe_render(
        "hr_personnel_checklist_center.html",
        checklist_ready=True,
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        selected_review=selected_review,
        checklist_rows=selected_rows,
        checklist_team_rows=team_rows[:14],
        checklist_summary={"approved": approved, "pending": pending, "rejected": rejected, "tracked": len(template_rows)},
        checklist_form_token=issue_form_token("hr_personnel_checklist_save", scope="hr_personnel_operations"),
        checklist_delete_token=issue_form_token("hr_personnel_checklist_delete", scope="hr_personnel_operations"),
        checklist_status_options=list(CHECKLIST_STATUS_LABELS.items()),
    )


@main_bp.route("/hr-management/personnel-operations/checklists/save", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_checklist_save():
    if not consume_form_token("hr_personnel_checklist_save", request.form.get("form_token"), scope="hr_personnel_operations"):
        flash("Form oturumu doğrulanamadı. Lütfen tekrar deneyin.", "warning")
        return redirect(url_for("main.hr_personnel_checklist_center", scope=(request.form.get("scope") or "").strip() or None, user_id=_safe_int(request.form.get("user_id")) or None))
    _, _, scope_user_ids, _, _ = _base_context()
    try:
        if not (_table_exists("personnel_checklist_template_items") and _table_exists("personnel_checklist_reviews")):
            raise ValueError("Checklist tabloları henüz hazır değil.")
        user = _require_user_in_scope(_safe_int(request.form.get("user_id")), scope_user_ids)
        template_id = _safe_int(request.form.get("template_item_id"))
        template = db.session.get(PersonnelChecklistTemplateItem, int(template_id or 0))
        if not template:
            raise ValueError("Checklist maddesi bulunamadı.")
        row_id = _safe_int(request.form.get("review_id"))
        row = _review_in_scope(row_id, scope_user_ids) if row_id else PersonnelChecklistReview(user_id=user.id, template_item_id=template.id)
        row.user_id = int(user.id)
        row.template_item_id = int(template.id)
        row.status = _normalize_text(request.form.get("status"), 30).lower() or "pending"
        row.checked_at = utc_now()
        row.checked_by_id = getattr(current_user, "id", None)
        row.expiry_date = _parse_date(request.form.get("expiry_date"))
        row.note = (request.form.get("note") or "").strip() or None
        db.session.add(row)
        db.session.commit()
        flash("Checklist kaydı güncellendi.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
    return redirect(url_for("main.hr_personnel_checklist_center", scope=(request.form.get("scope") or "").strip() or None, user_id=_safe_int(request.form.get("user_id")) or None))


@main_bp.route("/hr-management/personnel-operations/checklists/<int:review_id>/delete", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_checklist_delete(review_id: int):
    if not consume_form_token("hr_personnel_checklist_delete", request.form.get("form_token"), scope="hr_personnel_operations"):
        flash("Form oturumu doğrulanamadı. Lütfen tekrar deneyin.", "warning")
        return redirect(url_for("main.hr_personnel_checklist_center", scope=(request.form.get("scope") or "").strip() or None, user_id=_safe_int(request.form.get("user_id")) or None))
    _, _, scope_user_ids, _, _ = _base_context()
    try:
        row = _review_in_scope(review_id, scope_user_ids)
        db.session.delete(row)
        db.session.commit()
        flash("Checklist kaydı silindi.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
    return redirect(url_for("main.hr_personnel_checklist_center", scope=(request.form.get("scope") or "").strip() or None, user_id=_safe_int(request.form.get("user_id")) or None))


@main_bp.route("/hr-management/personnel-operations/reminders")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_reminder_center():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user = _base_context()
    if not (_table_exists("personnel_documents") and _table_exists("personnel_document_reminder_logs")):
        return safe_render("hr_personnel_reminder_center.html", reminders_ready=False, hr_scope=hr_scope, selected_scope_mode=selected_scope_mode, scope_user_options=_scope_user_options(scope_users), selected_user=selected_user)

    severity_filter = (request.args.get("severity") or "all").strip().lower() or "all"
    today = date.today()
    candidate_rows = []
    summary = {"tracked": 0, "expired": 0, "critical": 0, "soon": 0}
    if scope_user_ids:
        docs = PersonnelDocument.query.filter(PersonnelDocument.user_id.in_(list(scope_user_ids))).order_by(PersonnelDocument.expiry_date.asc().nullslast(), PersonnelDocument.id.desc()).all()
        for row in docs:
            expiry_date = getattr(row, "expiry_date", None)
            if not expiry_date:
                continue
            summary["tracked"] += 1
            days_left = (expiry_date - today).days
            if days_left < 0:
                severity = "expired"
            elif days_left <= 15:
                severity = "critical"
            elif days_left <= 45:
                severity = "soon"
            else:
                continue
            summary[severity] += 1
            payload = {
                "document_id": int(row.id),
                "user_id": int(row.user_id),
                "user_name": _full_name(getattr(row, "user", None)),
                "title": row.title or "Belge",
                "category": (getattr(row, "category", None) or "ozluk").replace("_", " ").title(),
                "expiry_date": expiry_date,
                "days_left": days_left,
                "severity": severity,
                "severity_label": _reminder_type_label(severity),
            }
            candidate_rows.append(payload)
    candidate_rows.sort(key=lambda row: (row["days_left"], row["user_name"].lower(), row["title"].lower()))
    if severity_filter in {"expired", "critical", "soon"}:
        candidate_rows = [row for row in candidate_rows if row["severity"] == severity_filter]

    log_rows = []
    if scope_user_ids:
        logs = PersonnelDocumentReminderLog.query.filter(PersonnelDocumentReminderLog.user_id.in_(list(scope_user_ids))).order_by(PersonnelDocumentReminderLog.created_at.desc(), PersonnelDocumentReminderLog.id.desc()).limit(24).all()
        for row in logs:
            log_rows.append({
                "user_name": _full_name(getattr(row, "user", None)),
                "document_title": getattr(getattr(row, "document", None), "title", None) or "Belge",
                "reminder_type": row.reminder_type or "manual",
                "reminder_type_label": _reminder_type_label(row.reminder_type),
                "status": row.status or "queued",
                "status_label": _reminder_log_status_label(row.status or "queued"),
                "due_date": row.due_date,
                "created_at": row.created_at,
            })

    return safe_render(
        "hr_personnel_reminder_center.html",
        reminders_ready=True,
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        severity_filter=severity_filter,
        reminder_summary=summary,
        reminder_candidate_rows=candidate_rows,
        reminder_log_rows=log_rows,
        reminder_run_token=issue_form_token("hr_personnel_reminder_run", scope="hr_personnel_operations"),
        reminder_bulk_token=issue_form_token("hr_personnel_reminder_bulk", scope="hr_personnel_operations"),
    )


@main_bp.route("/hr-management/personnel-operations/reminders/run", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_reminder_run():
    if not consume_form_token("hr_personnel_reminder_run", request.form.get("form_token"), scope="hr_personnel_operations"):
        flash("Form oturumu doğrulanamadı. Lütfen tekrar deneyin.", "warning")
        return redirect(url_for("main.hr_personnel_reminder_center", scope=(request.form.get("scope") or "").strip() or None, severity=(request.form.get("severity") or "all").strip() or None))
    _, _, scope_user_ids, _, _ = _base_context()
    try:
        if not (_table_exists("personnel_documents") and _table_exists("personnel_document_reminder_logs")):
            raise ValueError("Hatırlatma tabloları henüz hazır değil.")
        document = _document_in_scope(_safe_int(request.form.get("document_id")), scope_user_ids)
        reminder_type = _normalize_text(request.form.get("reminder_type"), 30).lower() or "manual"
        row = PersonnelDocumentReminderLog(
            user_id=document.user_id,
            document_id=document.id,
            reminder_type=reminder_type,
            channel="in_app",
            status="queued",
            due_date=getattr(document, "expiry_date", None),
            reminder_text=(request.form.get("reminder_text") or "").strip() or None,
            triggered_by_id=getattr(current_user, "id", None),
            triggered_at=utc_now(),
        )
        db.session.add(row)
        db.session.commit()
        flash("Belge yenileme hatırlatması kuyruğa alındı.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
    return redirect(url_for("main.hr_personnel_reminder_center", scope=(request.form.get("scope") or "").strip() or None, severity=(request.form.get("severity") or "all").strip() or None))


@main_bp.route("/hr-management/personnel-operations/reminders/bulk", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_reminder_bulk():
    if not consume_form_token("hr_personnel_reminder_bulk", request.form.get("form_token"), scope="hr_personnel_operations"):
        flash("Form oturumu doğrulanamadı. Lütfen tekrar deneyin.", "warning")
        return redirect(url_for("main.hr_personnel_reminder_center", scope=(request.form.get("scope") or "").strip() or None, severity=(request.form.get("severity") or "all").strip() or None))
    _, _, scope_user_ids, _, _ = _base_context()
    try:
        if not (_table_exists("personnel_documents") and _table_exists("personnel_document_reminder_logs")):
            raise ValueError("Hatırlatma tabloları henüz hazır değil.")
        severity = (request.form.get("severity") or "soon").strip().lower() or "soon"
        today = date.today()
        docs = PersonnelDocument.query.filter(PersonnelDocument.user_id.in_(list(scope_user_ids))).all()
        created = 0
        for document in docs:
            if not getattr(document, "expiry_date", None):
                continue
            days_left = (document.expiry_date - today).days
            if severity == "expired" and days_left >= 0:
                continue
            if severity == "critical" and not (0 <= days_left <= 15):
                continue
            if severity == "soon" and not (0 <= days_left <= 45):
                continue
            db.session.add(PersonnelDocumentReminderLog(
                user_id=document.user_id,
                document_id=document.id,
                reminder_type=severity,
                channel="in_app",
                status="queued",
                due_date=document.expiry_date,
                reminder_text=(request.form.get("reminder_text") or "").strip() or None,
                triggered_by_id=getattr(current_user, "id", None),
                triggered_at=utc_now(),
            ))
            created += 1
        db.session.commit()
        flash(f"Toplu hatırlatma kaydı oluşturuldu: {created}", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
    return redirect(url_for("main.hr_personnel_reminder_center", scope=(request.form.get("scope") or "").strip() or None, severity=(request.form.get("severity") or "all").strip() or None))
