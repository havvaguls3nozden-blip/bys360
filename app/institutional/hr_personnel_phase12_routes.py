from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_CHILD_IMPORT
# STATUS_SOURCE: app.institutional.routes LOADED_CHILD_ROUTE_MODULES
import logging
from collections import defaultdict
from datetime import date
from typing import Any

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import inspect

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import PersonnelHandoverItem, PersonnelHandoverRecord, PersonnelLifecycleCase, User
from app.route_registry import main_bp
from app.route_support import (
    consume_form_token,
    issue_form_token,
    manager_required,
    menu_key_required,
    safe_db_rollback,
    safe_render,
)

from .hr_personnel_extension_routes import (
    _base_context,
    _full_name,
    _normalize_text,
    _parse_date,
    _safe_int,
    _scope_user_options,
)

logger = logging.getLogger(__name__)

OPERATION_TYPE_LABELS = {
    "offboarding": "Ayrılış Devir Teslimi",
    "onboarding": "İşe Başlatma Teslimi",
    "unit_change": "Birim Devir / Teslim",
    "return_to_work": "İşe Dönüş Hazırlığı",
}
HANDOVER_STATUS_LABELS = {
    "draft": "Taslak",
    "in_progress": "İşlemde",
    "waiting": "Beklemede",
    "completed": "Tamamlandı",
    "cancelled": "İptal",
}
ITEM_STATUS_LABELS = {
    "pending": "Bekliyor",
    "in_progress": "İşlemde",
    "completed": "Tamamlandı",
    "waived": "Muaf",
}


def _table_exists(table_name: str) -> bool:
    try:
        return table_name in set(inspect(db.engine).get_table_names())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_personnel_phase12_routes.py:48")
        return False


def _operation_type_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return OPERATION_TYPE_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _handover_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return HANDOVER_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _item_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return ITEM_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _handover_in_scope(handover_id: int | None, scope_user_ids: set[int]) -> PersonnelHandoverRecord:
    if not handover_id:
        raise ValueError("Devir teslim kaydı bulunamadı.")
    row = PersonnelHandoverRecord.query.filter(
        PersonnelHandoverRecord.id == int(handover_id),
        PersonnelHandoverRecord.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Devir teslim kaydı bu kapsam içinde bulunamadı.")
    return row


def _handover_item_in_scope(item_id: int | None, scope_user_ids: set[int]) -> PersonnelHandoverItem:
    if not item_id:
        raise ValueError("Devir teslim satırı bulunamadı.")
    row = (
        PersonnelHandoverItem.query
        .join(PersonnelHandoverRecord, PersonnelHandoverRecord.id == PersonnelHandoverItem.handover_id)
        .filter(
            PersonnelHandoverItem.id == int(item_id),
            PersonnelHandoverRecord.user_id.in_(list(scope_user_ids)),
        )
        .first()
    )
    if not row:
        raise ValueError("Devir teslim satırı bu kapsam içinde bulunamadı.")
    return row


def _redirect_handover(handover_id: int | None = None, user_id: int | None = None, scope_mode: str | None = None):
    params: dict[str, Any] = {}
    scope_value = (scope_mode or request.form.get("scope") or request.args.get("scope") or "").strip()
    if scope_value:
        params["scope"] = scope_value
    if handover_id:
        params["handover_id"] = int(handover_id)
    if user_id:
        params["user_id"] = int(user_id)
    return redirect(url_for("main.hr_personnel_handover_center", **params))


def _progress(record: PersonnelHandoverRecord) -> int:
    items = list(record.items.order_by(PersonnelHandoverItem.id.asc()).all()) if getattr(record, "items", None) is not None else []
    required_items = [item for item in items if bool(item.is_required)] or items
    if not required_items:
        return 0
    done = sum(1 for item in required_items if (item.status or "").strip().lower() in {"completed", "waived"})
    return int(round((done / len(required_items)) * 100)) if required_items else 0


@main_bp.route("/hr-management/personnel-operations/handover-center")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_handover_center():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user = _base_context()
    handover_ready = all(_table_exists(name) for name in ["personnel_handover_records", "personnel_handover_items"])
    selected_handover = None
    handover_rows: list[dict[str, object]] = []
    item_rows: list[dict[str, object]] = []
    summary = {"open": 0, "completed": 0, "critical": 0, "items": 0}
    if handover_ready and scope_user_ids:
        edit_handover_id = _safe_int(request.args.get("handover_id"))
        if edit_handover_id:
            selected_handover = _handover_in_scope(edit_handover_id, scope_user_ids)
            selected_user = db.session.get(User, int(selected_handover.user_id)) or selected_user
        q = PersonnelHandoverRecord.query.filter(PersonnelHandoverRecord.user_id.in_(list(scope_user_ids)))
        if selected_user:
            q = q.filter(PersonnelHandoverRecord.user_id == int(selected_user.id))
        rows = q.order_by(PersonnelHandoverRecord.created_at.desc(), PersonnelHandoverRecord.id.desc()).all()
        today = date.today()
        for row in rows:
            items = row.items.order_by(PersonnelHandoverItem.id.asc()).all()
            summary["items"] += len(items)
            status = (row.status or "draft").strip().lower()
            if status == "completed":
                summary["completed"] += 1
            else:
                summary["open"] += 1
                if row.due_date and row.due_date < today:
                    summary["critical"] += 1
            handover_rows.append({
                "id": int(row.id),
                "title": row.title,
                "user_name": _full_name(getattr(row, "user", None)),
                "operation_type_label": _operation_type_label(row.operation_type),
                "status": status,
                "status_label": _handover_status_label(status),
                "planned_date": row.planned_date,
                "due_date": row.due_date,
                "progress": _progress(row),
                "item_count": len(items),
                "required_count": sum(1 for item in items if bool(item.is_required)),
            })
        if selected_handover is not None:
            for item in selected_handover.items.order_by(PersonnelHandoverItem.id.asc()).all():
                item_rows.append({
                    "id": int(item.id),
                    "title": item.title,
                    "category": item.category or "genel",
                    "status": item.status or "pending",
                    "status_label": _item_status_label(item.status),
                    "responsible_name": _full_name(getattr(item, "responsible_user", None)),
                    "due_date": item.due_date,
                    "note": item.note or "",
                    "evidence_note": item.evidence_note or "",
                    "is_required": bool(item.is_required),
                })
    available_cases = []
    if handover_ready and selected_user:
        case_rows = PersonnelLifecycleCase.query.filter_by(user_id=int(selected_user.id)).order_by(PersonnelLifecycleCase.created_at.desc()).all()
        available_cases = [{
            "id": int(row.id),
            "title": row.title,
            "lifecycle_type": (row.lifecycle_type or "").strip().lower(),
        } for row in case_rows]
    return safe_render(
        "hr_personnel_handover_center.html",
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        handover_ready=handover_ready,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        selected_handover=selected_handover,
        handover_rows=handover_rows,
        handover_item_rows=item_rows,
        handover_summary=summary,
        available_cases=available_cases,
        handover_form_token=issue_form_token("hr_personnel_handover_save", scope="hr_personnel_phase12"),
        handover_item_form_token=issue_form_token("hr_personnel_handover_item_save", scope="hr_personnel_phase12"),
        handover_item_status_token=issue_form_token("hr_personnel_handover_item_status", scope="hr_personnel_phase12"),
    )


@main_bp.route("/hr-management/personnel-operations/handover-center/save", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_handover_save():
    _hr_scope, _scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    if not _table_exists("personnel_handover_records"):
        flash("Devir teslim tabloları henüz hazır değil.", "warning")
        return _redirect_handover(scope_mode=selected_scope_mode)
    try:
        submitted_token = (request.form.get("form_token") or "").strip()
        if not consume_form_token("hr_personnel_handover_save", submitted_token, scope="hr_personnel_phase12"):
            raise ValueError("Form güvenlik anahtarı doğrulanamadı.")
        user_id = _safe_int(request.form.get("user_id"))
        if not user_id or user_id not in scope_user_ids:
            raise ValueError("Seçilen personel bu kapsam içinde görünmüyor.")
        edit_id = _safe_int(request.form.get("handover_id"))
        row = _handover_in_scope(edit_id, scope_user_ids) if edit_id else PersonnelHandoverRecord(user_id=int(user_id), created_by_id=getattr(current_user, "id", None))
        row.organization_unit_id = getattr(db.session.get(User, int(user_id)), "organization_unit_id", None)
        lifecycle_case_id = _safe_int(request.form.get("lifecycle_case_id"))
        if lifecycle_case_id:
            lifecycle_case = PersonnelLifecycleCase.query.filter(
                PersonnelLifecycleCase.id == int(lifecycle_case_id),
                PersonnelLifecycleCase.user_id == int(user_id),
            ).first()
            if not lifecycle_case:
                raise ValueError("Seçilen yaşam döngüsü vakası bu personel için bulunamadı.")
            row.lifecycle_case_id = int(lifecycle_case.id)
        else:
            row.lifecycle_case_id = None
        row.operation_type = _normalize_text(request.form.get("operation_type") or "offboarding", 30).lower() or "offboarding"
        row.title = _normalize_text(request.form.get("title"), 255) or "Devir teslim kaydı"
        row.status = _normalize_text(request.form.get("status") or "draft", 30).lower() or "draft"
        row.planned_date = _parse_date(request.form.get("planned_date"))
        row.due_date = _parse_date(request.form.get("due_date"))
        row.handover_no = _normalize_text(request.form.get("handover_no"), 120) or None
        row.note = (request.form.get("note") or "").strip() or None
        row.approved_by_id = _safe_int(request.form.get("approved_by_id")) or getattr(current_user, "id", None)
        if row.status == "completed" and not row.completed_at:
            row.completed_at = utc_now()
        elif row.status != "completed":
            row.completed_at = None
        db.session.add(row)
        db.session.commit()
        flash("Devir teslim kaydı kaydedildi.", "success")
        return _redirect_handover(handover_id=row.id, user_id=user_id, scope_mode=selected_scope_mode)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
        return _redirect_handover(user_id=_safe_int(request.form.get("user_id")), scope_mode=selected_scope_mode)


@main_bp.route("/hr-management/personnel-operations/handover-center/item/save", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_handover_item_save():
    _hr_scope, _scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    if not _table_exists("personnel_handover_items"):
        flash("Devir teslim satır tabloları henüz hazır değil.", "warning")
        return _redirect_handover(scope_mode=selected_scope_mode)
    try:
        submitted_token = (request.form.get("form_token") or "").strip()
        if not consume_form_token("hr_personnel_handover_item_save", submitted_token, scope="hr_personnel_phase12"):
            raise ValueError("Form güvenlik anahtarı doğrulanamadı.")
        handover = _handover_in_scope(_safe_int(request.form.get("handover_id")), scope_user_ids)
        row = PersonnelHandoverItem(handover_id=int(handover.id), created_by_id=getattr(current_user, "id", None))
        row.responsible_user_id = _safe_int(request.form.get("responsible_user_id"))
        row.category = _normalize_text(request.form.get("category") or "genel", 50).lower() or "genel"
        row.title = _normalize_text(request.form.get("title"), 255) or "Devir teslim satırı"
        row.status = _normalize_text(request.form.get("status") or "pending", 30).lower() or "pending"
        row.due_date = _parse_date(request.form.get("due_date"))
        row.is_required = str(request.form.get("is_required") or "1").strip().lower() in {"1", "true", "on", "yes", "evet"}
        row.note = (request.form.get("note") or "").strip() or None
        row.evidence_note = (request.form.get("evidence_note") or "").strip() or None
        if row.status in {"completed", "waived"}:
            row.completed_at = utc_now()
        db.session.add(row)
        db.session.commit()
        flash("Devir teslim satırı eklendi.", "success")
        return _redirect_handover(handover_id=handover.id, user_id=handover.user_id, scope_mode=selected_scope_mode)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
        return _redirect_handover(handover_id=_safe_int(request.form.get("handover_id")), scope_mode=selected_scope_mode)


@main_bp.route("/hr-management/personnel-operations/handover-center/item/status", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_handover_item_status():
    _hr_scope, _scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    try:
        submitted_token = (request.form.get("form_token") or "").strip()
        if not consume_form_token("hr_personnel_handover_item_status", submitted_token, scope="hr_personnel_phase12"):
            raise ValueError("Form güvenlik anahtarı doğrulanamadı.")
        row = _handover_item_in_scope(_safe_int(request.form.get("item_id")), scope_user_ids)
        row.status = _normalize_text(request.form.get("status") or "pending", 30).lower() or "pending"
        row.evidence_note = (request.form.get("evidence_note") or "").strip() or row.evidence_note
        row.completed_at = utc_now() if row.status in {"completed", "waived"} else None
        db.session.add(row)
        db.session.commit()
        flash("Devir teslim satırı güncellendi.", "success")
        return _redirect_handover(handover_id=row.handover_id, user_id=getattr(row.handover, "user_id", None), scope_mode=selected_scope_mode)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
        return _redirect_handover(scope_mode=selected_scope_mode)


@main_bp.route("/hr-management/personnel-operations/clearance-board")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_clearance_board():
    hr_scope, _scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    board_ready = all(_table_exists(name) for name in ["personnel_handover_records", "personnel_handover_items"])
    summary = {"total": 0, "completed": 0, "critical": 0, "items": 0}
    board_rows = []
    type_totals: defaultdict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "completed": 0})
    if board_ready and scope_user_ids:
        rows = (
            PersonnelHandoverRecord.query
            .filter(PersonnelHandoverRecord.user_id.in_(list(scope_user_ids)))
            .order_by(PersonnelHandoverRecord.due_date.asc().nullslast(), PersonnelHandoverRecord.id.desc())
            .all()
        )
        today = date.today()
        for row in rows:
            items = row.items.order_by(PersonnelHandoverItem.id.asc()).all()
            required_items = [item for item in items if bool(item.is_required)] or items
            completed_items = sum(1 for item in required_items if (item.status or "").strip().lower() in {"completed", "waived"})
            pending_items = max(0, len(required_items) - completed_items)
            progress = int(round((completed_items / len(required_items)) * 100)) if required_items else 0
            is_critical = bool(row.due_date and row.due_date < today and pending_items > 0 and (row.status or "").strip().lower() != "completed")
            summary["total"] += 1
            summary["items"] += len(items)
            if (row.status or "").strip().lower() == "completed":
                summary["completed"] += 1
            if is_critical:
                summary["critical"] += 1
            op_key = (row.operation_type or "offboarding").strip().lower() or "offboarding"
            type_totals[op_key]["total"] += 1
            if (row.status or "").strip().lower() == "completed":
                type_totals[op_key]["completed"] += 1
            board_rows.append({
                "id": int(row.id),
                "title": row.title,
                "user_name": _full_name(getattr(row, "user", None)),
                "operation_type_label": _operation_type_label(row.operation_type),
                "status_label": _handover_status_label(row.status),
                "status": (row.status or "draft").strip().lower(),
                "due_date": row.due_date,
                "progress": progress,
                "required_total": len(required_items),
                "completed_total": completed_items,
                "pending_total": pending_items,
                "critical": is_critical,
            })
    return safe_render(
        "hr_personnel_clearance_board.html",
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        board_ready=board_ready,
        clearance_summary=summary,
        clearance_rows=board_rows,
        type_totals=dict(type_totals),
        operation_type_labels=OPERATION_TYPE_LABELS,
    )
