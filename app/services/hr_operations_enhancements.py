from __future__ import annotations

from datetime import date
from typing import Any

from flask import request
from sqlalchemy import inspect

from app.extensions import db
from app.models import PersonnelDocument, PersonnelPositionHistory, User
from app.route_support import issue_form_token

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

POSITION_ASSIGNMENT_TYPE_LABELS = {
    "atama": "Atama",
    "gorevlendirme": "Görevlendirme",
    "vekalet": "Vekâlet",
    "terfi": "Terfi",
    "unvan_degisim": "Unvan Değişikliği",
    "rotasyon": "Rotasyon",
    "diger": "Diğer",
}

APPOINTMENT_KIND_LABELS = {
    "asil": "Asil",
    "vekil": "Vekil",
    "gecici": "Geçici",
    "gorevlendirme": "Görevlendirme",
}


def _table_exists(table_name: str) -> bool:
    try:
        return table_name in set(inspect(db.engine).get_table_names())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/hr_operations_enhancements.py:47")
        return False


def _safe_int(value: Any) -> int | None:
    try:
        raw = str(value or "").strip()
        return int(raw) if raw else None
    except (TypeError, ValueError):
        return None


def _full_name(user: Any) -> str:
    if not user:
        return "-"
    full_name = (getattr(user, "full_name", None) or getattr(user, "full_name_cache", None) or "").strip()
    if full_name:
        return full_name
    return f"{(getattr(user, 'ad', '') or '').strip()} {(getattr(user, 'soyad', '') or '').strip()}".strip() or "-"


def _label(mapping: dict[str, str], value: str | None) -> str:
    raw = (value or "").strip().lower()
    return mapping.get(raw, raw.replace("_", " ").title() if raw else "-")


def _manager_from_sicil(user: Any, attr_name: str) -> str:
    sicil = (getattr(user, attr_name, None) or "").strip()
    if not sicil:
        return "-"
    manager = User.query.filter_by(sicil_no=sicil).first()
    return _full_name(manager)


def _position_rows_for_user(user_id: int) -> list[dict[str, Any]]:
    if not _table_exists("personnel_position_histories"):
        return []
    rows = (
        PersonnelPositionHistory.query
        .filter_by(user_id=user_id)
        .order_by(PersonnelPositionHistory.is_current.desc(), PersonnelPositionHistory.start_date.desc().nullslast(), PersonnelPositionHistory.id.desc())
        .all()
    )
    payload: list[dict[str, Any]] = []
    for row in rows:
        payload.append({
            "id": int(row.id),
            "position_title": row.position_title or "-",
            "position_grade": row.position_grade or "-",
            "assignment_type": row.assignment_type or "atama",
            "assignment_type_label": _label(POSITION_ASSIGNMENT_TYPE_LABELS, row.assignment_type),
            "appointment_kind": row.appointment_kind or "",
            "appointment_kind_label": _label(APPOINTMENT_KIND_LABELS, row.appointment_kind),
            "decision_no": row.decision_no or "-",
            "start_date": row.start_date,
            "end_date": row.end_date,
            "reason": row.reason or "-",
            "is_current": bool(row.is_current),
            "unit_name": row.unit_name_snapshot or getattr(getattr(row, "organization_unit", None), "name", None) or "-",
            "parent_unit_name": row.parent_unit_name_snapshot or "-",
            "manager_name": _full_name(getattr(row, "manager_user", None)),
        })
    return payload


def _validity_rows_from_documents(doc_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    summary = {"expired": 0, "critical": 0, "soon": 0, "ok": 0}
    for row in doc_rows:
        days_left = row.get("days_left")
        expiry_date = row.get("expiry_date")
        if expiry_date is None or days_left is None:
            continue
        severity = "ok"
        if days_left < 0:
            severity = "expired"
        elif days_left <= 15:
            severity = "critical"
        elif days_left <= 45:
            severity = "soon"
        summary[severity] += 1
        if severity == "ok":
            continue
        rows.append({
            **row,
            "severity": severity,
            "severity_label": {"expired": "Süresi doldu", "critical": "Kritik", "soon": "Yaklaşıyor"}[severity],
        })
    rows.sort(key=lambda item: (item.get("days_left", 999999), str(item.get("title") or "").lower()))
    return rows, summary


def build_hr_personnel_overlay_context(hr_scope: dict[str, Any] | None, scope_users: list[User], base_payload: dict[str, Any]) -> dict[str, Any]:
    selected_user = base_payload.get("selected_user")
    selected_user_id = base_payload.get("selected_user_id")
    scope_user_ids = {int(getattr(user, "id", 0)) for user in scope_users if getattr(user, "id", None) is not None}

    position_ready = _table_exists("personnel_position_histories")
    selected_position = None
    selected_position_rows: list[dict[str, Any]] = []
    if selected_user and position_ready:
        selected_position_rows = _position_rows_for_user(int(selected_user_id))
        edit_position_id = _safe_int(request.args.get("edit_position_id"))
        if edit_position_id:
            selected_position = PersonnelPositionHistory.query.filter(
                PersonnelPositionHistory.id == int(edit_position_id),
                PersonnelPositionHistory.user_id.in_(list(scope_user_ids)),
            ).first()

    selected_document_validity_rows, selected_validity_summary = _validity_rows_from_documents(base_payload.get("selected_document_rows") or [])
    profile_header = None
    if selected_user:
        profile_header = {
            "sicil_no": (getattr(selected_user, "sicil_no", None) or "-").strip() or "-",
            "email": (getattr(selected_user, "email", None) or "-").strip() or "-",
            "unvan": (getattr(selected_user, "unvan", None) or "-").strip() or "-",
            "birim": (getattr(selected_user, "birim", None) or getattr(selected_user, "ust_birim", None) or "-").strip() or "-",
            "ust_birim": (getattr(selected_user, "ust_birim", None) or "-").strip() or "-",
            "manager_1_name": _manager_from_sicil(selected_user, "yonetici_sicil"),
            "manager_2_name": _manager_from_sicil(selected_user, "ikinci_yonetici_sicil"),
            "manager_3_name": _manager_from_sicil(selected_user, "ucuncu_yonetici_sicil"),
            "position_count": len(selected_position_rows),
            "validity_alert_count": len(selected_document_validity_rows),
            "current_position_title": selected_position_rows[0]["position_title"] if selected_position_rows else ((getattr(selected_user, "unvan", None) or "-").strip() or "-"),
        }

    return {
        "position_ready": position_ready,
        "selected_position": selected_position,
        "selected_position_rows": selected_position_rows,
        "selected_document_validity_rows": selected_document_validity_rows,
        "selected_validity_summary": selected_validity_summary,
        "selected_profile_header": profile_header,
        "position_assignment_type_options": list(POSITION_ASSIGNMENT_TYPE_LABELS.items()),
        "position_appointment_kind_options": list(APPOINTMENT_KIND_LABELS.items()),
        "position_form_token": issue_form_token("hr_personnel_position_save", scope="hr_personnel_operations"),
        "position_delete_token": issue_form_token("hr_personnel_position_delete", scope="hr_personnel_operations"),
    }


def build_hr_document_validity_center_context(hr_scope: dict[str, Any] | None, scope_users: list[User]) -> dict[str, Any]:
    selected_scope_mode = (hr_scope or {}).get("scope_mode") or "personal"
    scope_user_ids = [int(getattr(user, "id", 0)) for user in scope_users if getattr(user, "id", None) is not None]
    rows: list[dict[str, Any]] = []
    summary = {"expired": 0, "critical": 0, "soon": 0, "tracked": 0}
    severity_filter = (request.args.get("severity") or "all").strip().lower() or "all"

    if _table_exists("personnel_documents") and scope_user_ids:
        docs = (
            PersonnelDocument.query
            .filter(PersonnelDocument.user_id.in_(scope_user_ids))
            .order_by(PersonnelDocument.expiry_date.asc().nullslast(), PersonnelDocument.id.desc())
            .all()
        )
        today = date.today()
        for row in docs:
            if not getattr(row, "expiry_date", None):
                continue
            summary["tracked"] += 1
            days_left = (row.expiry_date - today).days
            severity = None
            if days_left < 0:
                severity = "expired"
            elif days_left <= 15:
                severity = "critical"
            elif days_left <= 45:
                severity = "soon"
            if not severity:
                continue
            summary[severity] += 1
            payload = {
                "id": int(row.id),
                "user_id": int(row.user_id),
                "user_name": _full_name(getattr(row, "user", None)),
                "title": getattr(row, "title", None) or "Belge",
                "category": (getattr(row, "category", None) or "ozluk").replace("_", " ").title(),
                "issue_date": getattr(row, "issue_date", None),
                "expiry_date": getattr(row, "expiry_date", None),
                "days_left": days_left,
                "severity": severity,
                "severity_label": {"expired": "Süresi doldu", "critical": "Kritik 15 gün", "soon": "45 gün içinde"}[severity],
                "is_confidential": bool(getattr(row, "is_confidential", False)),
            }
            rows.append(payload)

    rows.sort(key=lambda item: (item.get("days_left", 999999), str(item.get("user_name") or "").lower(), str(item.get("title") or "").lower()))
    if severity_filter in {"expired", "critical", "soon"}:
        rows = [row for row in rows if row.get("severity") == severity_filter]

    return {
        "hr_scope": hr_scope,
        "selected_scope_mode": selected_scope_mode,
        "scope_label": (hr_scope or {}).get("scope_label") or "Kapsam",
        "scope_user_count": len(scope_users),
        "validity_rows": rows,
        "validity_summary": summary,
        "severity_filter": severity_filter,
    }
