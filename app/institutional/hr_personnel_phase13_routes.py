from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_CHILD_IMPORT
# STATUS_SOURCE: app.institutional.routes LOADED_CHILD_ROUTE_MODULES
import logging
from hashlib import sha256
from typing import Any

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import inspect

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import (
    PersonnelApprovalStation,
    PersonnelDigitalHandoverDocument,
    PersonnelExitRiskAssessment,
    PersonnelHandoverRecord,
    PersonnelLifecycleCase,
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

from .hr_personnel_extension_routes import (
    _base_context,
    _full_name,
    _normalize_text,
    _parse_date,
    _safe_int,
    _scope_user_options,
)

logger = logging.getLogger(__name__)

APPROVAL_STATUS_LABELS = {
    "pending": "Bekliyor",
    "approved": "Onaylandı",
    "revision": "Revizyon",
    "rejected": "Reddedildi",
}
DOC_STATUS_LABELS = {
    "draft": "Taslak",
    "signed": "İmzalandı",
    "approved": "Onaylandı",
    "archived": "Arşivlendi",
}
RISK_LEVEL_LABELS = {
    "dusuk": "Düşük",
    "orta": "Orta",
    "yuksek": "Yüksek",
    "kritik": "Kritik",
}
DOCUMENT_TYPE_LABELS = {
    "devir_teslim": "Devir teslim",
    "ilisik_kesme": "İlişik kesme",
    "teslim_tutanagi": "Teslim tutanağı",
}


def _table_exists(table_name: str) -> bool:
    try:
        return table_name in set(inspect(db.engine).get_table_names())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_personnel_phase13_routes.py:54")
        return False


def _approval_in_scope(station_id: int | None, scope_user_ids: set[int]) -> PersonnelApprovalStation:
    if not station_id:
        raise ValueError("Onay istasyonu kaydı bulunamadı.")
    row = PersonnelApprovalStation.query.filter(
        PersonnelApprovalStation.id == int(station_id),
        PersonnelApprovalStation.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Onay istasyonu bu kapsam içinde bulunamadı.")
    return row


def _document_in_scope(document_id: int | None, scope_user_ids: set[int]) -> PersonnelDigitalHandoverDocument:
    if not document_id:
        raise ValueError("Dijital tutanak kaydı bulunamadı.")
    row = PersonnelDigitalHandoverDocument.query.filter(
        PersonnelDigitalHandoverDocument.id == int(document_id),
        PersonnelDigitalHandoverDocument.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Dijital tutanak bu kapsam içinde bulunamadı.")
    return row


def _risk_in_scope(assessment_id: int | None, scope_user_ids: set[int]) -> PersonnelExitRiskAssessment:
    if not assessment_id:
        raise ValueError("Risk değerlendirmesi bulunamadı.")
    row = PersonnelExitRiskAssessment.query.filter(
        PersonnelExitRiskAssessment.id == int(assessment_id),
        PersonnelExitRiskAssessment.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Risk değerlendirmesi bu kapsam içinde bulunamadı.")
    return row


def _approval_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return APPROVAL_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _doc_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return DOC_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _risk_level_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return RISK_LEVEL_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _document_type_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return DOCUMENT_TYPE_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _calculate_risk_level(score: int) -> str:
    if score >= 75:
        return "kritik"
    if score >= 50:
        return "yuksek"
    if score >= 25:
        return "orta"
    return "dusuk"


def _redirect_phase13(endpoint: str, user_id: int | None = None, scope_mode: str | None = None, **kwargs):
    params: dict[str, Any] = {}
    scope_value = (scope_mode or request.form.get("scope") or request.args.get("scope") or "").strip()
    if scope_value:
        params["scope"] = scope_value
    if user_id:
        params["user_id"] = int(user_id)
    for key, value in kwargs.items():
        if value:
            params[key] = value
    return redirect(url_for(endpoint, **params))


@main_bp.route("/hr-management/personnel-operations/approval-stations")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_approval_station_center():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user = _base_context()
    ready = _table_exists("personnel_approval_stations")
    selected_station = None
    summary = {"pending": 0, "approved": 0, "revision": 0, "rejected": 0}
    station_rows: list[dict[str, object]] = []
    available_cases: list[dict[str, object]] = []
    available_handovers: list[dict[str, object]] = []
    if ready and scope_user_ids:
        edit_station_id = _safe_int(request.args.get("station_id"))
        if edit_station_id:
            selected_station = _approval_in_scope(edit_station_id, scope_user_ids)
            selected_user = db.session.get(User, int(selected_station.user_id)) or selected_user
        q = PersonnelApprovalStation.query.filter(PersonnelApprovalStation.user_id.in_(list(scope_user_ids)))
        if selected_user:
            q = q.filter(PersonnelApprovalStation.user_id == int(selected_user.id))
            available_cases = [
                {"id": int(row.id), "title": row.title}
                for row in PersonnelLifecycleCase.query.filter_by(user_id=int(selected_user.id)).order_by(PersonnelLifecycleCase.created_at.desc()).all()
            ]
            available_handovers = [
                {"id": int(row.id), "title": row.title}
                for row in PersonnelHandoverRecord.query.filter_by(user_id=int(selected_user.id)).order_by(PersonnelHandoverRecord.created_at.desc()).all()
            ]
        for row in q.order_by(PersonnelApprovalStation.station_order.asc(), PersonnelApprovalStation.id.desc()).all():
            status = (row.status or "pending").strip().lower()
            summary[status] = summary.get(status, 0) + 1
            station_rows.append({
                "id": int(row.id),
                "user_name": _full_name(getattr(row, "user", None)),
                "station_name": row.station_name,
                "module_name": row.module_name or "clearance",
                "station_order": row.station_order,
                "role_label": row.role_label or "-",
                "assigned_name": _full_name(getattr(row, "assigned_user", None)),
                "status": status,
                "status_label": _approval_status_label(status),
                "due_date": row.due_date,
                "decision_note": row.decision_note or "",
            })
    return safe_render(
        "hr_personnel_approval_station_center.html",
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        ready=ready,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        selected_station=selected_station,
        station_rows=station_rows,
        available_cases=available_cases,
        available_handovers=available_handovers,
        approval_summary=summary,
        approval_form_token=issue_form_token("hr_personnel_approval_station_save", scope="hr_personnel_phase13"),
        approval_status_token=issue_form_token("hr_personnel_approval_station_decide", scope="hr_personnel_phase13"),
    )


@main_bp.route("/hr-management/personnel-operations/approval-stations/save", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_approval_station_save():
    _hr_scope, _scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    if not _table_exists("personnel_approval_stations"):
        flash("Onay istasyonu tabloları henüz hazır değil.", "warning")
        return _redirect_phase13("main.hr_personnel_approval_station_center", scope_mode=selected_scope_mode)
    try:
        submitted_token = (request.form.get("form_token") or "").strip()
        if not consume_form_token("hr_personnel_approval_station_save", submitted_token, scope="hr_personnel_phase13"):
            raise ValueError("Form güvenlik anahtarı doğrulanamadı.")
        user_id = _safe_int(request.form.get("user_id"))
        if not user_id or user_id not in scope_user_ids:
            raise ValueError("Seçilen personel bu kapsam içinde görünmüyor.")
        edit_id = _safe_int(request.form.get("station_id"))
        row = _approval_in_scope(edit_id, scope_user_ids) if edit_id else PersonnelApprovalStation(user_id=int(user_id))
        row.lifecycle_case_id = _safe_int(request.form.get("lifecycle_case_id")) or None
        row.handover_id = _safe_int(request.form.get("handover_id")) or None
        row.assigned_user_id = _safe_int(request.form.get("assigned_user_id")) or None
        row.module_name = _normalize_text(request.form.get("module_name") or "clearance", 50).lower() or "clearance"
        row.station_order = _safe_int(request.form.get("station_order")) or 1
        row.station_name = _normalize_text(request.form.get("station_name"), 255) or "Onay istasyonu"
        row.role_label = _normalize_text(request.form.get("role_label"), 120) or None
        row.status = _normalize_text(request.form.get("status") or "pending", 30).lower() or "pending"
        row.due_date = _parse_date(request.form.get("due_date"))
        row.decision_note = (request.form.get("decision_note") or "").strip() or None
        db.session.add(row)
        db.session.commit()
        flash("Onay istasyonu kaydedildi.", "success")
        return _redirect_phase13("main.hr_personnel_approval_station_center", user_id=user_id, scope_mode=selected_scope_mode, station_id=row.id)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
        return _redirect_phase13("main.hr_personnel_approval_station_center", user_id=_safe_int(request.form.get("user_id")), scope_mode=selected_scope_mode)


@main_bp.route("/hr-management/personnel-operations/approval-stations/decide", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_approval_station_decide():
    _hr_scope, _scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    try:
        submitted_token = (request.form.get("form_token") or "").strip()
        if not consume_form_token("hr_personnel_approval_station_decide", submitted_token, scope="hr_personnel_phase13"):
            raise ValueError("Form güvenlik anahtarı doğrulanamadı.")
        row = _approval_in_scope(_safe_int(request.form.get("station_id")), scope_user_ids)
        row.status = _normalize_text(request.form.get("status") or "pending", 30).lower() or "pending"
        row.decision_note = (request.form.get("decision_note") or "").strip() or None
        row.acted_by_id = getattr(current_user, "id", None)
        row.decision_at = utc_now()
        db.session.add(row)
        db.session.commit()
        flash("Onay istasyonu güncellendi.", "success")
        return _redirect_phase13("main.hr_personnel_approval_station_center", user_id=int(row.user_id), scope_mode=selected_scope_mode, station_id=row.id)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
        return _redirect_phase13("main.hr_personnel_approval_station_center", scope_mode=selected_scope_mode)


@main_bp.route("/hr-management/personnel-operations/digital-handover-documents")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_digital_handover_documents():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user = _base_context()
    ready = _table_exists("personnel_digital_handover_documents")
    selected_document = None
    summary = {"draft": 0, "signed": 0, "approved": 0, "archived": 0}
    document_rows: list[dict[str, object]] = []
    available_cases: list[dict[str, object]] = []
    available_handovers: list[dict[str, object]] = []
    if ready and scope_user_ids:
        edit_document_id = _safe_int(request.args.get("document_id"))
        if edit_document_id:
            selected_document = _document_in_scope(edit_document_id, scope_user_ids)
            selected_user = db.session.get(User, int(selected_document.user_id)) or selected_user
        q = PersonnelDigitalHandoverDocument.query.filter(PersonnelDigitalHandoverDocument.user_id.in_(list(scope_user_ids)))
        if selected_user:
            q = q.filter(PersonnelDigitalHandoverDocument.user_id == int(selected_user.id))
            available_cases = [
                {"id": int(row.id), "title": row.title}
                for row in PersonnelLifecycleCase.query.filter_by(user_id=int(selected_user.id)).order_by(PersonnelLifecycleCase.created_at.desc()).all()
            ]
            available_handovers = [
                {"id": int(row.id), "title": row.title}
                for row in PersonnelHandoverRecord.query.filter_by(user_id=int(selected_user.id)).order_by(PersonnelHandoverRecord.created_at.desc()).all()
            ]
        for row in q.order_by(PersonnelDigitalHandoverDocument.created_at.desc(), PersonnelDigitalHandoverDocument.id.desc()).all():
            status = (row.status or "draft").strip().lower()
            summary[status] = summary.get(status, 0) + 1
            document_rows.append({
                "id": int(row.id),
                "user_name": _full_name(getattr(row, "user", None)),
                "title": row.title,
                "document_type": row.document_type or "devir_teslim",
                "document_type_label": _document_type_label(row.document_type or "devir_teslim"),
                "document_no": row.document_no or "-",
                "status": status,
                "status_label": _doc_status_label(status),
                "hash_value": row.hash_value or "-",
                "signed_at": row.signed_at,
                "approved_at": row.approved_at,
            })
    return safe_render(
        "hr_personnel_digital_handover_documents.html",
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        ready=ready,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        selected_document=selected_document,
        document_rows=document_rows,
        available_cases=available_cases,
        available_handovers=available_handovers,
        document_summary=summary,
        document_form_token=issue_form_token("hr_personnel_digital_document_save", scope="hr_personnel_phase13"),
        document_status_token=issue_form_token("hr_personnel_digital_document_status", scope="hr_personnel_phase13"),
    )


@main_bp.route("/hr-management/personnel-operations/digital-handover-documents/save", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_digital_document_save():
    _hr_scope, _scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    if not _table_exists("personnel_digital_handover_documents"):
        flash("Dijital tutanak tabloları henüz hazır değil.", "warning")
        return _redirect_phase13("main.hr_personnel_digital_handover_documents", scope_mode=selected_scope_mode)
    try:
        submitted_token = (request.form.get("form_token") or "").strip()
        if not consume_form_token("hr_personnel_digital_document_save", submitted_token, scope="hr_personnel_phase13"):
            raise ValueError("Form güvenlik anahtarı doğrulanamadı.")
        user_id = _safe_int(request.form.get("user_id"))
        if not user_id or user_id not in scope_user_ids:
            raise ValueError("Seçilen personel bu kapsam içinde görünmüyor.")
        edit_id = _safe_int(request.form.get("document_id"))
        row = _document_in_scope(edit_id, scope_user_ids) if edit_id else PersonnelDigitalHandoverDocument(user_id=int(user_id), created_by_id=getattr(current_user, "id", None))
        row.lifecycle_case_id = _safe_int(request.form.get("lifecycle_case_id")) or None
        row.handover_id = _safe_int(request.form.get("handover_id")) or None
        row.document_type = _normalize_text(request.form.get("document_type") or "devir_teslim", 50).lower() or "devir_teslim"
        row.title = _normalize_text(request.form.get("title"), 255) or "Dijital teslim tutanağı"
        row.document_no = _normalize_text(request.form.get("document_no"), 120) or None
        row.status = _normalize_text(request.form.get("status") or "draft", 30).lower() or "draft"
        row.summary = (request.form.get("summary") or "").strip() or None
        row.content_text = (request.form.get("content_text") or "").strip() or None
        hash_source = f"{row.user_id}|{row.title}|{row.document_no or '-'}|{row.content_text or '-'}|{row.status}"
        row.hash_value = sha256(hash_source.encode("utf-8")).hexdigest()[:24]
        db.session.add(row)
        db.session.commit()
        flash("Dijital tutanak kaydedildi.", "success")
        return _redirect_phase13("main.hr_personnel_digital_handover_documents", user_id=user_id, scope_mode=selected_scope_mode, document_id=row.id)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
        return _redirect_phase13("main.hr_personnel_digital_handover_documents", user_id=_safe_int(request.form.get("user_id")), scope_mode=selected_scope_mode)


@main_bp.route("/hr-management/personnel-operations/digital-handover-documents/status", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_digital_document_status():
    _hr_scope, _scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    try:
        submitted_token = (request.form.get("form_token") or "").strip()
        if not consume_form_token("hr_personnel_digital_document_status", submitted_token, scope="hr_personnel_phase13"):
            raise ValueError("Form güvenlik anahtarı doğrulanamadı.")
        row = _document_in_scope(_safe_int(request.form.get("document_id")), scope_user_ids)
        action = _normalize_text(request.form.get("action") or "save", 20).lower() or "save"
        if action == "sign":
            row.status = "signed"
            row.signed_by_id = getattr(current_user, "id", None)
            row.signed_at = utc_now()
        elif action == "approve":
            row.status = "approved"
            row.approved_by_id = getattr(current_user, "id", None)
            row.approved_at = utc_now()
        elif action == "archive":
            row.status = "archived"
        db.session.add(row)
        db.session.commit()
        flash("Dijital tutanak durumu güncellendi.", "success")
        return _redirect_phase13("main.hr_personnel_digital_handover_documents", user_id=int(row.user_id), scope_mode=selected_scope_mode, document_id=row.id)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
        return _redirect_phase13("main.hr_personnel_digital_handover_documents", scope_mode=selected_scope_mode)


@main_bp.route("/hr-management/personnel-operations/exit-risk-center")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_exit_risk_center():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user = _base_context()
    ready = _table_exists("personnel_exit_risk_assessments")
    selected_assessment = None
    summary = {"dusuk": 0, "orta": 0, "yuksek": 0, "kritik": 0}
    risk_rows: list[dict[str, object]] = []
    available_cases: list[dict[str, object]] = []
    if ready and scope_user_ids:
        edit_assessment_id = _safe_int(request.args.get("assessment_id"))
        if edit_assessment_id:
            selected_assessment = _risk_in_scope(edit_assessment_id, scope_user_ids)
            selected_assessment.risk_level_label = _risk_level_label(selected_assessment.risk_level)
            selected_user = db.session.get(User, int(selected_assessment.user_id)) or selected_user
        q = PersonnelExitRiskAssessment.query.filter(PersonnelExitRiskAssessment.user_id.in_(list(scope_user_ids)))
        if selected_user:
            q = q.filter(PersonnelExitRiskAssessment.user_id == int(selected_user.id))
            available_cases = [
                {"id": int(row.id), "title": row.title}
                for row in PersonnelLifecycleCase.query.filter_by(user_id=int(selected_user.id)).order_by(PersonnelLifecycleCase.created_at.desc()).all()
            ]
        for row in q.order_by(PersonnelExitRiskAssessment.assessed_at.desc().nullslast(), PersonnelExitRiskAssessment.id.desc()).all():
            level = (row.risk_level or "dusuk").strip().lower()
            summary[level] = summary.get(level, 0) + 1
            risk_rows.append({
                "id": int(row.id),
                "user_name": _full_name(getattr(row, "user", None)),
                "risk_score": int(row.risk_score or 0),
                "risk_level": level,
                "risk_level_label": _risk_level_label(level),
                "assessed_at": row.assessed_at,
                "knowledge_loss_risk": int(row.knowledge_loss_risk or 0),
                "asset_risk": int(row.asset_risk or 0),
                "access_risk": int(row.access_risk or 0),
                "process_risk": int(row.process_risk or 0),
            })
    return safe_render(
        "hr_personnel_exit_risk_center.html",
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        ready=ready,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        selected_assessment=selected_assessment,
        risk_rows=risk_rows,
        available_cases=available_cases,
        risk_summary=summary,
        risk_form_token=issue_form_token("hr_personnel_exit_risk_save", scope="hr_personnel_phase13"),
    )


@main_bp.route("/hr-management/personnel-operations/exit-risk-center/save", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_exit_risk_save():
    _hr_scope, _scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    if not _table_exists("personnel_exit_risk_assessments"):
        flash("Ayrılış risk tabloları henüz hazır değil.", "warning")
        return _redirect_phase13("main.hr_personnel_exit_risk_center", scope_mode=selected_scope_mode)
    try:
        submitted_token = (request.form.get("form_token") or "").strip()
        if not consume_form_token("hr_personnel_exit_risk_save", submitted_token, scope="hr_personnel_phase13"):
            raise ValueError("Form güvenlik anahtarı doğrulanamadı.")
        user_id = _safe_int(request.form.get("user_id"))
        if not user_id or user_id not in scope_user_ids:
            raise ValueError("Seçilen personel bu kapsam içinde görünmüyor.")
        edit_id = _safe_int(request.form.get("assessment_id"))
        row = _risk_in_scope(edit_id, scope_user_ids) if edit_id else PersonnelExitRiskAssessment(user_id=int(user_id))
        row.lifecycle_case_id = _safe_int(request.form.get("lifecycle_case_id")) or None
        row.knowledge_loss_risk = max(0, min(25, _safe_int(request.form.get("knowledge_loss_risk")) or 0))
        row.asset_risk = max(0, min(25, _safe_int(request.form.get("asset_risk")) or 0))
        row.access_risk = max(0, min(25, _safe_int(request.form.get("access_risk")) or 0))
        row.process_risk = max(0, min(25, _safe_int(request.form.get("process_risk")) or 0))
        row.risk_score = row.knowledge_loss_risk + row.asset_risk + row.access_risk + row.process_risk
        row.risk_level = _calculate_risk_level(int(row.risk_score))
        row.note = (request.form.get("note") or "").strip() or None
        row.mitigation_plan = (request.form.get("mitigation_plan") or "").strip() or None
        row.assessed_by_id = getattr(current_user, "id", None)
        row.assessed_at = utc_now()
        db.session.add(row)
        db.session.commit()
        flash("Ayrılış risk değerlendirmesi kaydedildi.", "success")
        return _redirect_phase13("main.hr_personnel_exit_risk_center", user_id=user_id, scope_mode=selected_scope_mode, assessment_id=row.id)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash("İşlem sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.", "danger")
        return _redirect_phase13("main.hr_personnel_exit_risk_center", user_id=_safe_int(request.form.get("user_id")), scope_mode=selected_scope_mode)
