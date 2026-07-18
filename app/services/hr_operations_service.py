from __future__ import annotations

# --- BYS360 third-manager Excel import compatibility patch ---
THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]

from datetime import date
from typing import Any

from flask import request
from sqlalchemy import inspect

from app.extensions import db
from app.models import (
    AttendanceException,
    DelegationAssignment,
    EmployeeOrgAssignmentHistory,
    LeaveBalance,
    PerformanceEvaluation,
    PersonnelDocument,
    PersonnelDocumentCategory,
    PersonnelDocumentUploadBatch,
    PersonnelLeave,
    PersonnelProcessNote,
    PersonnelStatusHistory,
    User,
)
from app.route_support import issue_form_token


DEFAULT_DOCUMENT_CATEGORIES = [
    {
        "code": "ozluk",
        "label": "Özlük",
        "description": "Temel kimlik, göreve başlama ve personel dosyası evrakları.",
        "is_required": True,
        "validity_days": None,
        "sort_order": 10,
    },
    {
        "code": "gorevlendirme",
        "label": "Görevlendirme",
        "description": "Geçici görev, vekâlet ve görev yazıları.",
        "is_required": False,
        "validity_days": 365,
        "sort_order": 20,
    },
    {
        "code": "sertifika",
        "label": "Sertifika",
        "description": "Eğitim, yetkinlik ve sertifika kanıtları.",
        "is_required": False,
        "validity_days": None,
        "sort_order": 30,
    },
    {
        "code": "izin",
        "label": "İzin / Onay",
        "description": "İzin, sağlık raporu ve onay belgeleri.",
        "is_required": False,
        "validity_days": 180,
        "sort_order": 40,
    },
    {
        "code": "disiplin",
        "label": "Disiplin",
        "description": "Soruşturma, savunma ve disiplin karar evrakları.",
        "is_required": False,
        "validity_days": None,
        "sort_order": 50,
    },
    {
        "code": "odul",
        "label": "Ödül",
        "description": "Takdir, teşekkür ve ödül belgeleri.",
        "is_required": False,
        "validity_days": None,
        "sort_order": 60,
    },
    {
        "code": "diger",
        "label": "Diğer",
        "description": "Sınıflanmayan veya destekleyici personel dokümanları.",
        "is_required": False,
        "validity_days": None,
        "sort_order": 90,
    },
]

DOCUMENT_STATUS_LABELS = {
    "aktif": "Aktif",
    "arsiv": "Arşiv",
    "pasif": "Pasif",
    "iptal": "İptal",
}

NOTE_TYPE_LABELS = {
    "ozluk": "Özlük",
    "hatirlatma": "Hatırlatma",
    "uyum": "Uyum",
    "disiplin": "Disiplin",
    "odul": "Ödül",
    "izin": "İzin",
    "diger": "Diğer",
}

NOTE_PRIORITY_LABELS = {
    "normal": "Normal",
    "high": "Yüksek",
    "critical": "Kritik",
}

NOTE_STATUS_LABELS = {
    "open": "Açık",
    "in_progress": "İşlemde",
    "closed": "Kapalı",
}

STATUS_EVENT_LABELS = {
    "durum": "Durum",
    "atama": "Atama",
    "unvan": "Unvan",
    "birim": "Birim",
    "gorevlendirme": "Görevlendirme",
    "vekalet": "Vekâlet",
    "izin": "İzin",
    "diger": "Diğer",
}


def _table_exists(table_name: str) -> bool:
    try:
        return table_name in set(inspect(db.engine).get_table_names())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/hr_operations_service.py:144")
        return False


def _full_name(user: Any) -> str:
    if not user:
        return "-"
    value = (getattr(user, "full_name", None) or getattr(user, "full_name_cache", None) or "").strip()
    if value:
        return value
    return f"{getattr(user, 'ad', '') or ''} {getattr(user, 'soyad', '') or ''}".strip() or "-"


def _unit_name(user: Any) -> str:
    return (getattr(user, "birim", None) or getattr(user, "ust_birim", None) or "Belirsiz birim").strip()


def _role_label(user: Any) -> str:
    return (getattr(user, "role_label", None) or getattr(user, "role", None) or "-").strip()


def _profile_missing_fields(user: Any) -> list[str]:
    checks = [
        ("Ad", bool((getattr(user, "ad", "") or "").strip())),
        ("Soyad", bool((getattr(user, "soyad", "") or "").strip())),
        ("Sicil No", bool((getattr(user, "sicil_no", "") or "").strip())),
        ("E-posta", bool((getattr(user, "email", "") or "").strip())),
        ("Unvan", bool((getattr(user, "unvan", "") or "").strip())),
        ("Birim", bool((getattr(user, "birim", "") or "").strip())),
        ("Üst Birim", bool((getattr(user, "ust_birim", "") or "").strip())),
        ("1. Amir", bool((getattr(user, "yonetici_sicil", "") or "").strip()) or (getattr(user, "role", "") or "").strip().lower() in {"admin", "baskan"}),
    ]
    return [label for label, ok in checks if not ok]


def _profile_score(user: Any) -> int:
    checks = [
        bool((getattr(user, "ad", "") or "").strip()),
        bool((getattr(user, "soyad", "") or "").strip()),
        bool((getattr(user, "sicil_no", "") or "").strip()),
        bool((getattr(user, "email", "") or "").strip()),
        bool((getattr(user, "unvan", "") or "").strip()),
        bool((getattr(user, "birim", "") or "").strip()),
        bool((getattr(user, "ust_birim", "") or "").strip()),
        bool((getattr(user, "yonetici_sicil", "") or "").strip()) or (getattr(user, "role", "") or "").strip().lower() in {"admin", "baskan"},
    ]
    return int(round((sum(1 for item in checks if item) / len(checks)) * 100)) if checks else 0


def _performance_map(user_ids: list[int]) -> dict[int, Any]:
    if not user_ids:
        return {}
    rows = (
        PerformanceEvaluation.query
        .filter(PerformanceEvaluation.employee_id.in_(user_ids))
        .order_by(PerformanceEvaluation.period_id.desc(), PerformanceEvaluation.id.desc())
        .all()
    )
    mapping: dict[int, Any] = {}
    for row in rows:
        mapping.setdefault(int(row.employee_id), row)
    return mapping


def _leave_balance_risk_count(user_id: int) -> int:
    if not _table_exists("leave_balances"):
        return 0
    count = 0
    rows = LeaveBalance.query.filter_by(user_id=user_id).all()
    for row in rows:
        remaining = round(float(row.total_days or 0) + float(row.carried_over_days or 0) - float(row.used_days or 0), 2)
        if remaining <= 3:
            count += 1
    return count


def _safe_int(value: Any) -> int | None:
    try:
        raw = str(value or "").strip()
        if not raw:
            return None
        return int(raw)
    except (TypeError, ValueError):
        return None


def _selected_user(scope_users: list[User]) -> User | None:
    if not scope_users:
        return None
    wanted_id = _safe_int(request.args.get("user_id"))
    by_id = {int(user.id): user for user in scope_users if getattr(user, "id", None) is not None}
    if wanted_id and wanted_id in by_id:
        return by_id[wanted_id]
    return next((user for user in scope_users if getattr(user, "id", None) is not None), None)


def _selected_entity(scope_user_ids: list[int], model: Any, arg_name: str) -> Any | None:
    entity_id = _safe_int(request.args.get(arg_name))
    if not entity_id or not _table_exists(getattr(model, "__tablename__", "")):
        return None
    try:
        entity = model.query.filter(model.id == entity_id, model.user_id.in_(scope_user_ids)).first()
        return entity
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/hr_operations_service.py:247")
        return None


def _default_category_map() -> dict[str, dict[str, Any]]:
    return {row["code"]: dict(row) for row in DEFAULT_DOCUMENT_CATEGORIES}


def _category_catalog() -> list[dict[str, Any]]:
    defaults = _default_category_map()
    if _table_exists("personnel_document_categories"):
        try:
            rows = (
                PersonnelDocumentCategory.query
                .filter_by(is_active=True)
                .order_by(PersonnelDocumentCategory.sort_order.asc(), PersonnelDocumentCategory.label.asc())
                .all()
            )
            if rows:
                payload = []
                for row in rows:
                    payload.append({
                        "code": (getattr(row, "code", None) or "").strip().lower(),
                        "label": getattr(row, "label", None) or getattr(row, "code", None) or "Belge",
                        "description": getattr(row, "description", None) or "",
                        "is_required": bool(getattr(row, "is_required", False)),
                        "validity_days": getattr(row, "validity_days", None),
                        "sort_order": int(getattr(row, "sort_order", 0) or 0),
                    })
                return payload
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/hr_operations_service.py")
    return sorted(defaults.values(), key=lambda item: (int(item.get("sort_order") or 0), str(item.get("label") or "").lower()))


def _document_label(value: str | None, category_map: dict[str, dict[str, Any]] | None = None) -> str:
    raw = (value or "").strip().lower()
    mapping = category_map or _default_category_map()
    if raw in mapping:
        return str(mapping[raw].get("label") or raw)
    return raw.replace("_", " ").title() if raw else "-"


def _document_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return DOCUMENT_STATUS_LABELS.get(raw, raw.replace("_", " ").title() if raw else "-")


def _note_type_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return NOTE_TYPE_LABELS.get(raw, raw.replace("_", " ").title() if raw else "-")


def _note_priority_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return NOTE_PRIORITY_LABELS.get(raw, raw.replace("_", " ").title() if raw else "-")


def _note_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return NOTE_STATUS_LABELS.get(raw, raw.replace("_", " ").title() if raw else "-")


def _status_event_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return STATUS_EVENT_LABELS.get(raw, raw.replace("_", " ").title() if raw else "-")


def _build_selected_timeline(selected_user_id: int, category_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    timeline_rows: list[dict[str, Any]] = []

    if _table_exists("personnel_documents"):
        rows = PersonnelDocument.query.filter_by(user_id=selected_user_id).order_by(PersonnelDocument.created_at.desc(), PersonnelDocument.id.desc()).limit(12).all()
        for row in rows:
            event_date = getattr(row, "issue_date", None) or getattr(row, "created_at", None)
            timeline_rows.append({
                "date": event_date,
                "kind": "document",
                "kind_label": "Belge",
                "title": getattr(row, "title", None) or "Belge",
                "subtitle": _document_label(getattr(row, "category", None), category_map),
                "detail": getattr(row, "original_filename", None) or getattr(row, "description", None) or "Belge kaydı oluşturuldu.",
                "tone": "good" if (getattr(row, "status", None) or "aktif") == "aktif" else "soft",
            })

    if _table_exists("personnel_process_notes"):
        rows = PersonnelProcessNote.query.filter_by(user_id=selected_user_id).order_by(PersonnelProcessNote.updated_at.desc(), PersonnelProcessNote.id.desc()).limit(12).all()
        for row in rows:
            event_date = getattr(row, "resolved_at", None) or getattr(row, "due_date", None) or getattr(row, "updated_at", None)
            priority = (getattr(row, "priority", None) or "normal").lower()
            timeline_rows.append({
                "date": event_date,
                "kind": "note",
                "kind_label": "İşlem notu",
                "title": getattr(row, "subject", None) or "İşlem notu",
                "subtitle": _note_type_label(getattr(row, "note_type", None)),
                "detail": getattr(row, "note", None) or "İşlem notu kaydedildi.",
                "tone": "bad" if priority == "critical" else ("warn" if priority == "high" else "soft"),
            })

    if _table_exists("personnel_status_history"):
        rows = PersonnelStatusHistory.query.filter_by(user_id=selected_user_id).order_by(PersonnelStatusHistory.event_date.desc(), PersonnelStatusHistory.id.desc()).limit(12).all()
        for row in rows:
            timeline_rows.append({
                "date": getattr(row, "event_date", None) or getattr(row, "created_at", None),
                "kind": "status",
                "kind_label": "Durum",
                "title": getattr(row, "summary", None) or "Durum kaydı",
                "subtitle": _status_event_label(getattr(row, "event_type", None)),
                "detail": getattr(row, "description", None) or getattr(row, "new_value", None) or "Durum geçmişi güncellendi.",
                "tone": "soft",
            })

    history_rows = (
        EmployeeOrgAssignmentHistory.query
        .filter_by(employee_id=selected_user_id)
        .order_by(EmployeeOrgAssignmentHistory.start_date.desc(), EmployeeOrgAssignmentHistory.id.desc())
        .limit(8)
        .all()
    )
    for row in history_rows:
        timeline_rows.append({
            "date": getattr(row, "start_date", None) or getattr(row, "created_at", None),
            "kind": "movement",
            "kind_label": "Hareket",
            "title": getattr(row, "assignment_type", None) or "Atama hareketi",
            "subtitle": getattr(row, "unit_name_snapshot", None) or "Birim kaydı",
            "detail": getattr(row, "reason", None) or getattr(row, "parent_unit_name_snapshot", None) or "Organizasyon hareketi işlendi.",
            "tone": "good" if bool(getattr(row, "is_current", False)) else "soft",
        })

    if _table_exists("personnel_leaves"):
        rows = PersonnelLeave.query.filter_by(user_id=selected_user_id).order_by(PersonnelLeave.start_date.desc(), PersonnelLeave.id.desc()).limit(6).all()
        for row in rows:
            timeline_rows.append({
                "date": getattr(row, "start_date", None) or getattr(row, "created_at", None),
                "kind": "leave",
                "kind_label": "İzin",
                "title": getattr(row, "leave_type", None) or "İzin",
                "subtitle": getattr(row, "status", None) or "onaylandi",
                "detail": getattr(row, "description", None) or "İzin kaydı işlendi.",
                "tone": "warn",
            })

    if _table_exists("attendance_exceptions"):
        rows = AttendanceException.query.filter_by(user_id=selected_user_id).order_by(AttendanceException.record_date.desc(), AttendanceException.id.desc()).limit(6).all()
        for row in rows:
            timeline_rows.append({
                "date": getattr(row, "record_date", None) or getattr(row, "created_at", None),
                "kind": "attendance",
                "kind_label": "Devamsızlık",
                "title": getattr(row, "exception_type", None) or "İstisna kaydı",
                "subtitle": getattr(row, "status", None) or "onaylandi",
                "detail": getattr(row, "description", None) or "Devamsızlık istisnası işlendi.",
                "tone": "warn",
            })

    if _table_exists("delegation_assignments"):
        rows = DelegationAssignment.query.filter(DelegationAssignment.delegate_user_id == selected_user_id).order_by(DelegationAssignment.start_date.desc(), DelegationAssignment.id.desc()).limit(6).all()
        for row in rows:
            timeline_rows.append({
                "date": getattr(row, "start_date", None) or getattr(row, "created_at", None),
                "kind": "delegation",
                "kind_label": "Vekâlet",
                "title": "Üstlenilen vekâlet",
                "subtitle": _full_name(getattr(row, "delegator", None)),
                "detail": getattr(row, "note", None) or getattr(row, "scope_type", None) or "Vekâlet kaydı işlendi.",
                "tone": "good",
            })

    timeline_rows.sort(key=lambda item: item.get("date") or date.min, reverse=True)
    return timeline_rows[:24]


def build_hr_personnel_operations_context(hr_scope: dict[str, Any] | None, scope_users: list[User], active_period: Any | None = None) -> dict[str, Any]:
    selected_scope_mode = (hr_scope or {}).get("scope_mode") or "personal"
    scope_users = scope_users or []
    scope_user_ids = [int(user.id) for user in scope_users if getattr(user, "id", None)]
    perf_map = _performance_map(scope_user_ids)
    category_catalog = _category_catalog()
    category_map = {row["code"]: row for row in category_catalog}
    required_codes = {row["code"] for row in category_catalog if row.get("is_required")}

    documents_ready = _table_exists("personnel_documents")
    notes_ready = _table_exists("personnel_process_notes")
    status_ready = _table_exists("personnel_status_history")
    batch_ready = _table_exists("personnel_document_upload_batches")

    document_counts: dict[int, int] = {}
    confidential_counts: dict[int, int] = {}
    category_counts: dict[str, int] = {row["code"]: 0 for row in category_catalog}
    user_category_map: dict[int, set[str]] = {}
    expiring_document_rows: list[dict[str, Any]] = []
    recent_batch_rows: list[dict[str, Any]] = []
    if documents_ready and scope_user_ids:
        docs = PersonnelDocument.query.filter(PersonnelDocument.user_id.in_(scope_user_ids)).order_by(PersonnelDocument.expiry_date.asc().nullslast(), PersonnelDocument.id.desc()).all()
        today = date.today()
        for row in docs:
            uid = int(row.user_id)
            category_code = (getattr(row, "category", None) or "ozluk").strip().lower()
            document_counts[uid] = document_counts.get(uid, 0) + 1
            category_counts[category_code] = category_counts.get(category_code, 0) + 1
            user_category_map.setdefault(uid, set()).add(category_code)
            if bool(getattr(row, "is_confidential", False)):
                confidential_counts[uid] = confidential_counts.get(uid, 0) + 1
            if getattr(row, "expiry_date", None):
                days_left = (row.expiry_date - today).days
                if days_left <= 45:
                    expiring_document_rows.append({
                        "user_name": _full_name(getattr(row, "user", None)),
                        "title": getattr(row, "title", None) or "Belge",
                        "category": _document_label(category_code, category_map),
                        "expiry_date": row.expiry_date,
                        "days_left": days_left,
                        "status": _document_status_label(getattr(row, "status", None)),
                    })
        if batch_ready:
            batches = (
                PersonnelDocumentUploadBatch.query
                .filter(PersonnelDocumentUploadBatch.user_id.in_(scope_user_ids))
                .order_by(PersonnelDocumentUploadBatch.created_at.desc(), PersonnelDocumentUploadBatch.id.desc())
                .limit(12)
                .all()
            )
            for row in batches:
                recent_batch_rows.append({
                    "user_name": _full_name(getattr(row, "user", None)),
                    "category_label": _document_label(getattr(row, "category_code", None), category_map),
                    "source_name": getattr(row, "source_name", None) or "Toplu yükleme",
                    "total_file_count": int(getattr(row, "total_file_count", 0) or 0),
                    "success_count": int(getattr(row, "success_count", 0) or 0),
                    "status": getattr(row, "status", None) or "tamamlandi",
                    "created_at": getattr(row, "created_at", None),
                })

    note_counts: dict[int, int] = {}
    overdue_note_count = 0
    open_note_rows: list[dict[str, Any]] = []
    if notes_ready and scope_user_ids:
        notes = PersonnelProcessNote.query.filter(PersonnelProcessNote.user_id.in_(scope_user_ids)).order_by(PersonnelProcessNote.due_date.asc().nullslast(), PersonnelProcessNote.id.desc()).all()
        today = date.today()
        for row in notes:
            uid = int(row.user_id)
            note_counts[uid] = note_counts.get(uid, 0) + 1
            if (getattr(row, "status", "open") or "open") != "closed":
                if getattr(row, "due_date", None) and row.due_date < today:
                    overdue_note_count += 1
                open_note_rows.append({
                    "user_name": _full_name(getattr(row, "user", None)),
                    "subject": getattr(row, "subject", None) or "İşlem notu",
                    "priority": _note_priority_label(getattr(row, "priority", None)),
                    "status": _note_status_label(getattr(row, "status", None)),
                    "due_date": getattr(row, "due_date", None),
                })

    status_rows: list[dict[str, Any]] = []
    if status_ready and scope_user_ids:
        rows = PersonnelStatusHistory.query.filter(PersonnelStatusHistory.user_id.in_(scope_user_ids)).order_by(PersonnelStatusHistory.event_date.desc(), PersonnelStatusHistory.id.desc()).limit(30).all()
        for row in rows:
            status_rows.append({
                "user_name": _full_name(getattr(row, "user", None)),
                "event_type": _status_event_label(getattr(row, "event_type", None)),
                "summary": getattr(row, "summary", None) or "-",
                "event_date": getattr(row, "event_date", None),
                "new_value": getattr(row, "new_value", None) or "-",
                "unit_name": getattr(getattr(row, "organization_unit", None), "name", None) or "-",
            })

    movement_rows: list[dict[str, Any]] = []
    if scope_user_ids:
        history_rows = (
            EmployeeOrgAssignmentHistory.query
            .filter(EmployeeOrgAssignmentHistory.employee_id.in_(scope_user_ids))
            .order_by(EmployeeOrgAssignmentHistory.start_date.desc(), EmployeeOrgAssignmentHistory.id.desc())
            .limit(40)
            .all()
        )
        for row in history_rows:
            movement_rows.append({
                "user_name": _full_name(getattr(row, "employee", None)),
                "unit_name": getattr(row, "unit_name_snapshot", None) or "-",
                "parent_unit_name": getattr(row, "parent_unit_name_snapshot", None) or "-",
                "assignment_type": getattr(row, "assignment_type", None) or "-",
                "reason": getattr(row, "reason", None) or "-",
                "start_date": getattr(row, "start_date", None),
                "end_date": getattr(row, "end_date", None),
                "is_current": bool(getattr(row, "is_current", False)),
            })

    category_rows: list[dict[str, Any]] = []
    for row in category_catalog:
        category_rows.append({
            **row,
            "document_count": category_counts.get(row["code"], 0),
        })

    dossier_rows: list[dict[str, Any]] = []
    missing_profile_count = 0
    dossier_gap_count = 0
    for user in scope_users:
        uid = int(user.id)
        missing = _profile_missing_fields(user)
        profile_score = _profile_score(user)
        if missing:
            missing_profile_count += 1
        doc_count = document_counts.get(uid, 0)
        note_count = note_counts.get(uid, 0)
        movement_count = sum(1 for row in movement_rows if row["user_name"] == _full_name(user))
        leave_risk = _leave_balance_risk_count(uid)
        last_score = float(getattr(perf_map.get(uid), "final_total_100", 0) or 0)
        existing_codes = user_category_map.get(uid, set())
        missing_required = sorted(required_codes - existing_codes)
        required_ratio = 100 if not required_codes else int(round(((len(required_codes) - len(missing_required)) / len(required_codes)) * 100))
        gap_reasons = []
        if missing:
            gap_reasons.append("Özlük alanı eksik")
        if doc_count == 0 and documents_ready:
            gap_reasons.append("Belge kaydı yok")
        if missing_required:
            gap_reasons.append("Zorunlu evrak eksik")
        if movement_count == 0:
            gap_reasons.append("Atama geçmişi yok")
        if leave_risk:
            gap_reasons.append("İzin bakiyesi kritik")
        if gap_reasons:
            dossier_gap_count += 1
        dossier_rows.append({
            "user_id": uid,
            "user_name": _full_name(user),
            "unit_name": _unit_name(user),
            "role_label": _role_label(user),
            "profile_score": profile_score,
            "missing_fields": missing,
            "document_count": doc_count,
            "confidential_count": confidential_counts.get(uid, 0),
            "note_count": note_count,
            "movement_count": movement_count,
            "leave_risk_count": leave_risk,
            "performance_score": last_score,
            "gap_reasons": gap_reasons,
            "required_ratio": required_ratio,
            "missing_required_labels": [_document_label(code, category_map) for code in missing_required],
        })

    dossier_rows.sort(key=lambda row: (0 if row["gap_reasons"] else 1, row["profile_score"], row["required_ratio"], row["document_count"], row["user_name"].lower()))
    expiring_document_rows.sort(key=lambda row: (row["days_left"], row["user_name"].lower()))
    open_note_rows.sort(key=lambda row: (0 if row["priority"] in {"Kritik", "Yüksek"} else 1, row["due_date"] or date.max, row["user_name"].lower()))

    action_rows: list[dict[str, Any]] = []
    if missing_profile_count:
        action_rows.append({"title": "Özlük profili eksik kayıtlar", "detail": "Birim, unvan ve amir zinciri eksikleri personel ana kartında kapanmalı.", "count": missing_profile_count, "tone": "critical", "priority": 1})
    missing_required_total = sum(1 for row in dossier_rows if row["missing_required_labels"])
    if missing_required_total:
        action_rows.append({"title": "Zorunlu evrakı eksik personel var", "detail": "Kategori kataloğundaki zorunlu evraklar personel bazında tamamlanmalı.", "count": missing_required_total, "tone": "critical", "priority": 2})
    if documents_ready and expiring_document_rows:
        action_rows.append({"title": "Süresi yaklaşan personel belgeleri", "detail": "Yetki, görevlendirme veya süreli evrakların yenilenmesi planlanmalı.", "count": len(expiring_document_rows), "tone": "watch", "priority": 3})
    if notes_ready and overdue_note_count:
        action_rows.append({"title": "Geciken işlem notları", "detail": "Açık aksiyonlar tamamlanmadan özlük akışı sağlıklı ilerlemez.", "count": overdue_note_count, "tone": "watch", "priority": 4})
    if not documents_ready or not notes_ready or not status_ready:
        missing_modules = []
        if not documents_ready:
            missing_modules.append("belge")
        if not notes_ready:
            missing_modules.append("süreç notu")
        if not status_ready:
            missing_modules.append("durum geçmişi")
        action_rows.append({"title": "Yeni Personel omurga tabloları bekliyor", "detail": f"{', '.join(missing_modules).title()} tabloları migration sonrası aktifleşecek.", "count": len(missing_modules), "tone": "watch", "priority": 5})
    action_rows.sort(key=lambda row: (int(row.get("priority") or 99), -int(row.get("count") or 0)))

    selected_user = _selected_user(scope_users)
    selected_document = _selected_entity(scope_user_ids, PersonnelDocument, "edit_document_id") if documents_ready else None
    selected_note = _selected_entity(scope_user_ids, PersonnelProcessNote, "edit_note_id") if notes_ready else None
    selected_status = _selected_entity(scope_user_ids, PersonnelStatusHistory, "edit_status_id") if status_ready else None

    selected_document_rows: list[dict[str, Any]] = []
    selected_note_rows: list[dict[str, Any]] = []
    selected_status_rows: list[dict[str, Any]] = []
    selected_movement_rows: list[dict[str, Any]] = []
    selected_timeline_rows: list[dict[str, Any]] = []
    selected_user_summary: dict[str, Any] | None = None
    if selected_user:
        selected_user_id = int(selected_user.id)
        selected_existing_codes = user_category_map.get(selected_user_id, set())
        selected_missing_required = sorted(required_codes - selected_existing_codes)
        selected_required_ratio = 100 if not required_codes else int(round(((len(required_codes) - len(selected_missing_required)) / len(required_codes)) * 100))
        selected_user_summary = {
            "user_id": selected_user_id,
            "full_name": _full_name(selected_user),
            "unit_name": _unit_name(selected_user),
            "role_label": _role_label(selected_user),
            "profile_score": _profile_score(selected_user),
            "missing_fields": _profile_missing_fields(selected_user),
            "performance_score": float(getattr(perf_map.get(selected_user_id), "final_total_100", 0) or 0),
            "document_count": document_counts.get(selected_user_id, 0),
            "note_count": note_counts.get(selected_user_id, 0),
            "status_count": sum(1 for row in status_rows if row["user_name"] == _full_name(selected_user)),
            "movement_count": sum(1 for row in movement_rows if row["user_name"] == _full_name(selected_user)),
            "confidential_count": confidential_counts.get(selected_user_id, 0),
            "required_ratio": selected_required_ratio,
            "missing_required_labels": [_document_label(code, category_map) for code in selected_missing_required],
        }
        if documents_ready:
            rows = PersonnelDocument.query.filter_by(user_id=selected_user_id).order_by(PersonnelDocument.expiry_date.asc().nullslast(), PersonnelDocument.id.desc()).limit(20).all()
            today = date.today()
            for row in rows:
                days_left = None
                if getattr(row, "expiry_date", None):
                    days_left = (row.expiry_date - today).days
                selected_document_rows.append({
                    "id": int(row.id),
                    "title": getattr(row, "title", None) or "Belge",
                    "category": getattr(row, "category", None) or "ozluk",
                    "category_label": _document_label(getattr(row, "category", None), category_map),
                    "document_no": getattr(row, "document_no", None) or "-",
                    "status": getattr(row, "status", None) or "aktif",
                    "status_label": _document_status_label(getattr(row, "status", None)),
                    "issue_date": getattr(row, "issue_date", None),
                    "expiry_date": getattr(row, "expiry_date", None),
                    "days_left": days_left,
                    "is_confidential": bool(getattr(row, "is_confidential", False)),
                    "original_filename": getattr(row, "original_filename", None) or "-",
                    "description": getattr(row, "description", None) or "",
                })
        if notes_ready:
            rows = PersonnelProcessNote.query.filter_by(user_id=selected_user_id).order_by(PersonnelProcessNote.due_date.asc().nullslast(), PersonnelProcessNote.id.desc()).limit(20).all()
            for row in rows:
                selected_note_rows.append({
                    "id": int(row.id),
                    "subject": getattr(row, "subject", None) or "İşlem notu",
                    "note_type": getattr(row, "note_type", None) or "ozluk",
                    "note_type_label": _note_type_label(getattr(row, "note_type", None)),
                    "priority": getattr(row, "priority", None) or "normal",
                    "priority_label": _note_priority_label(getattr(row, "priority", None)),
                    "status": getattr(row, "status", None) or "open",
                    "status_label": _note_status_label(getattr(row, "status", None)),
                    "due_date": getattr(row, "due_date", None),
                    "resolved_at": getattr(row, "resolved_at", None),
                    "is_private": bool(getattr(row, "is_private", True)),
                    "note": getattr(row, "note", None) or "",
                    "created_by_name": _full_name(getattr(row, "created_by", None)),
                })
        if status_ready:
            rows = PersonnelStatusHistory.query.filter_by(user_id=selected_user_id).order_by(PersonnelStatusHistory.event_date.desc(), PersonnelStatusHistory.id.desc()).limit(20).all()
            for row in rows:
                selected_status_rows.append({
                    "id": int(row.id),
                    "event_type": getattr(row, "event_type", None) or "durum",
                    "event_type_label": _status_event_label(getattr(row, "event_type", None)),
                    "event_date": getattr(row, "event_date", None),
                    "effective_start_date": getattr(row, "effective_start_date", None),
                    "effective_end_date": getattr(row, "effective_end_date", None),
                    "summary": getattr(row, "summary", None) or "-",
                    "previous_value": getattr(row, "previous_value", None) or "",
                    "new_value": getattr(row, "new_value", None) or "",
                    "description": getattr(row, "description", None) or "",
                    "unit_name": getattr(getattr(row, "organization_unit", None), "name", None) or selected_user_summary["unit_name"],
                })
        rows = (
            EmployeeOrgAssignmentHistory.query
            .filter_by(employee_id=selected_user_id)
            .order_by(EmployeeOrgAssignmentHistory.start_date.desc(), EmployeeOrgAssignmentHistory.id.desc())
            .limit(12)
            .all()
        )
        for row in rows:
            selected_movement_rows.append({
                "unit_name": getattr(row, "unit_name_snapshot", None) or "-",
                "parent_unit_name": getattr(row, "parent_unit_name_snapshot", None) or "-",
                "assignment_type": getattr(row, "assignment_type", None) or "-",
                "reason": getattr(row, "reason", None) or "-",
                "start_date": getattr(row, "start_date", None),
                "end_date": getattr(row, "end_date", None),
                "is_current": bool(getattr(row, "is_current", False)),
            })
        selected_timeline_rows = _build_selected_timeline(selected_user_id, category_map)

    return {
        "hr_scope": hr_scope,
        "selected_scope_mode": selected_scope_mode,
        "scope_label": (hr_scope or {}).get("scope_label") or "Kapsam",
        "active_period": active_period,
        "scope_user_count": len(scope_users),
        "missing_profile_count": missing_profile_count,
        "dossier_gap_count": dossier_gap_count,
        "document_count": sum(document_counts.values()),
        "open_note_count": len(open_note_rows),
        "overdue_note_count": overdue_note_count,
        "movement_count": len(movement_rows),
        "documents_ready": documents_ready,
        "notes_ready": notes_ready,
        "status_ready": status_ready,
        "batch_ready": batch_ready,
        "action_rows": action_rows,
        "dossier_rows": dossier_rows[:18],
        "movement_rows": movement_rows[:18],
        "expiring_document_rows": expiring_document_rows[:12],
        "open_note_rows": open_note_rows[:12],
        "status_rows": status_rows[:12],
        "category_rows": category_rows,
        "recent_batch_rows": recent_batch_rows,
        "selected_user": selected_user,
        "selected_user_summary": selected_user_summary,
        "selected_user_id": int(selected_user.id) if selected_user else None,
        "selected_document": selected_document,
        "selected_note": selected_note,
        "selected_status": selected_status,
        "selected_document_rows": selected_document_rows,
        "selected_note_rows": selected_note_rows,
        "selected_status_rows": selected_status_rows,
        "selected_movement_rows": selected_movement_rows,
        "selected_timeline_rows": selected_timeline_rows,
        "scope_user_options": [
            {
                "id": int(user.id),
                "full_name": _full_name(user),
                "unit_name": _unit_name(user),
                "role_label": _role_label(user),
            }
            for user in scope_users
        ],
        "document_category_options": category_rows,
        "document_status_options": list(DOCUMENT_STATUS_LABELS.items()),
        "note_type_options": list(NOTE_TYPE_LABELS.items()),
        "note_priority_options": list(NOTE_PRIORITY_LABELS.items()),
        "note_status_options": list(NOTE_STATUS_LABELS.items()),
        "status_event_options": list(STATUS_EVENT_LABELS.items()),
        "document_form_token": issue_form_token("hr_personnel_document_save", scope="hr_personnel_operations"),
        "document_delete_token": issue_form_token("hr_personnel_document_delete", scope="hr_personnel_operations"),
        "bulk_document_form_token": issue_form_token("hr_personnel_document_bulk_upload", scope="hr_personnel_operations"),
        "note_form_token": issue_form_token("hr_personnel_note_save", scope="hr_personnel_operations"),
        "note_delete_token": issue_form_token("hr_personnel_note_delete", scope="hr_personnel_operations"),
        "note_close_token": issue_form_token("hr_personnel_note_close", scope="hr_personnel_operations"),
        "status_form_token": issue_form_token("hr_personnel_status_save", scope="hr_personnel_operations"),
        "status_delete_token": issue_form_token("hr_personnel_status_delete", scope="hr_personnel_operations"),
    }


def build_personnel_profile_hr_context(user: User | None) -> dict[str, Any]:
    if not user:
        return {"enabled": False}

    category_catalog = _category_catalog()
    category_map = {row["code"]: row for row in category_catalog}
    required_codes = {row["code"] for row in category_catalog if row.get("is_required")}
    documents_ready = _table_exists("personnel_documents")
    notes_ready = _table_exists("personnel_process_notes")
    status_ready = _table_exists("personnel_status_history")

    document_rows = []
    existing_codes: set[str] = set()
    if documents_ready:
        rows = PersonnelDocument.query.filter_by(user_id=user.id).order_by(PersonnelDocument.expiry_date.asc().nullslast(), PersonnelDocument.id.desc()).limit(8).all()
        for row in rows:
            code = (getattr(row, "category", None) or "ozluk").strip().lower()
            existing_codes.add(code)
            document_rows.append({
                "title": getattr(row, "title", None) or "Belge",
                "category": _document_label(code, category_map),
                "status": _document_status_label(getattr(row, "status", None)),
                "expiry_date": getattr(row, "expiry_date", None),
                "is_confidential": bool(getattr(row, "is_confidential", False)),
            })

    note_rows = []
    if notes_ready:
        rows = PersonnelProcessNote.query.filter_by(user_id=user.id).order_by(PersonnelProcessNote.due_date.asc().nullslast(), PersonnelProcessNote.id.desc()).limit(8).all()
        for row in rows:
            note_rows.append({
                "subject": getattr(row, "subject", None) or "İşlem notu",
                "priority": _note_priority_label(getattr(row, "priority", None)),
                "status": _note_status_label(getattr(row, "status", None)),
                "due_date": getattr(row, "due_date", None),
            })

    status_rows = []
    if status_ready:
        rows = PersonnelStatusHistory.query.filter_by(user_id=user.id).order_by(PersonnelStatusHistory.event_date.desc(), PersonnelStatusHistory.id.desc()).limit(8).all()
        for row in rows:
            status_rows.append({
                "summary": getattr(row, "summary", None) or "-",
                "event_type": _status_event_label(getattr(row, "event_type", None)),
                "event_date": getattr(row, "event_date", None),
                "new_value": getattr(row, "new_value", None) or "-",
            })

    movement_rows = []
    history_rows = (
        EmployeeOrgAssignmentHistory.query
        .filter_by(employee_id=user.id)
        .order_by(EmployeeOrgAssignmentHistory.start_date.desc(), EmployeeOrgAssignmentHistory.id.desc())
        .limit(8)
        .all()
    )
    for row in history_rows:
        movement_rows.append({
            "unit_name": getattr(row, "unit_name_snapshot", None) or "-",
            "parent_unit_name": getattr(row, "parent_unit_name_snapshot", None) or "-",
            "assignment_type": getattr(row, "assignment_type", None) or "-",
            "reason": getattr(row, "reason", None) or "-",
            "start_date": getattr(row, "start_date", None),
            "end_date": getattr(row, "end_date", None),
            "is_current": bool(getattr(row, "is_current", False)),
        })

    latest_leave = PersonnelLeave.query.filter_by(user_id=user.id).order_by(PersonnelLeave.start_date.desc(), PersonnelLeave.id.desc()).first() if _table_exists("personnel_leaves") else None
    latest_attendance = AttendanceException.query.filter_by(user_id=user.id).order_by(AttendanceException.record_date.desc(), AttendanceException.id.desc()).first() if _table_exists("attendance_exceptions") else None
    latest_delegation = DelegationAssignment.query.filter(DelegationAssignment.delegate_user_id == user.id).order_by(DelegationAssignment.start_date.desc(), DelegationAssignment.id.desc()).first() if _table_exists("delegation_assignments") else None
    missing_required = sorted(required_codes - existing_codes)
    required_ratio = 100 if not required_codes else int(round(((len(required_codes) - len(missing_required)) / len(required_codes)) * 100))

    return {
        "enabled": True,
        "documents_ready": documents_ready,
        "notes_ready": notes_ready,
        "status_ready": status_ready,
        "summary": {
            "profile_score": _profile_score(user),
            "missing_fields": _profile_missing_fields(user),
            "document_count": len(document_rows),
            "note_count": len(note_rows),
            "movement_count": len(movement_rows),
            "status_count": len(status_rows),
            "required_ratio": required_ratio,
            "missing_required_labels": [_document_label(code, category_map) for code in missing_required],
        },
        "document_rows": document_rows,
        "note_rows": note_rows,
        "status_rows": status_rows,
        "movement_rows": movement_rows,
        "latest_leave": latest_leave,
        "latest_attendance": latest_attendance,
        "latest_delegation": latest_delegation,
        "operations_url": f"/hr-management/personnel-operations?user_id={int(user.id)}",
    }
