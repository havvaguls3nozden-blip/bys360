"""Operational admin helper functions extracted from ops_routes.py.

This module intentionally contains helper logic only. Route decorators stay in ops_routes.py.
"""
from __future__ import annotations

from app.services.safe_user_delete_service import safe_delete_user_by_id
from app.core.datetime_utils import utc_now
from datetime import datetime
from io import BytesIO
from flask import current_app, flash, redirect, request, send_file, url_for
from flask_login import current_user, login_required
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import EmployeeOrgAssignmentHistory, OrganizationUnit, PerformancePeriod, User
from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_db_rollback, safe_render, ensure_boolean_toggle, normalize_int_list
from app.services.hierarchy_admin_service import normalize_text, reset_all_personnel_and_related_data
from app.services.auto_hierarchy_service import auto_apply_manager_chains, infer_role_from_profile
from app.services.personnel_sync_service import canonical_role_label, canonical_role_value
from app.services.personnel.categories import assign_user_performance_category, normalize_personnel_category_label
from app.services.performance_service import generate_assignments_for_active_period, is_single_manager_case
from app.services.ai import build_personnel_profile_chain_ai_panel, build_excel_fix_preview_ai_panel, build_import_health_priority_ai_panel, build_import_health_simulation_ai_panel
from app.services.personnel.import_manager_chain_sync import sync_touched_users_manager_ids_from_sicils
from app.services.personnel.excel_import_guard import validate_personnel_import_rows_for_commit
from app.services.profile_photo_service import (
    delete_profile_photo_file as _delete_profile_photo_file,
    save_profile_photo as _save_profile_photo,
)

IMPORT_HEADER_ALIASES = {
    'kategori': 'personnel_category',
    'personel kategori': 'personnel_category',
    'personel kategorisi': 'personnel_category',
    'performans kategori': 'personnel_category',
    'performans kategorisi': 'personnel_category',
    'performance category': 'personnel_category',
    'performance_category': 'personnel_category',
    'personnel_category': 'personnel_category',
    'sicil no': 'sicil_no',
    'sicil': 'sicil_no',
    'e posta': 'email',
    'eposta': 'email',
    'mail': 'email',
    'ünvan': 'unvan',
    'ust birim': 'ust_birim',
    'üst birim': 'ust_birim',
    'rol': 'role',
    'yonetici sicil': 'yonetici_sicil',
    'yönetici sicil': 'yonetici_sicil',
    '1 amir': 'yonetici_sicil',
    '1. amir': 'yonetici_sicil',
    'ikinci yonetici sicil': 'ikinci_yonetici_sicil',
    'ikinci yönetici sicil': 'ikinci_yonetici_sicil',
    '2 amir': 'ikinci_yonetici_sicil',
    '2. amir': 'ikinci_yonetici_sicil',
    'ucuncu yonetici sicil': 'ucuncu_yonetici_sicil',
    'üçüncü yönetici sicil': 'ucuncu_yonetici_sicil',
    '3 amir': 'ucuncu_yonetici_sicil',
    '3. amir': 'ucuncu_yonetici_sicil',
    'aktif': 'is_active',
}

def _profile_full_name(user_obj) -> str:
    if not user_obj:
        return ""
    full_name = (getattr(user_obj, "full_name", None) or getattr(user_obj, "full_name_cache", None) or "").strip()
    if full_name:
        return full_name
    return f"{getattr(user_obj, 'ad', '') or ''} {getattr(user_obj, 'soyad', '') or ''}".strip()

def _safe_text(value: object, default: str = "-") -> str:
    text_value = (str(value).strip() if value is not None else "")
    return text_value or default

def _resolve_user_by_sicil(sicil_no: str | None):
    normalized = (sicil_no or "").strip()
    if not normalized:
        return None
    return User.query.filter_by(sicil_no=normalized).first()

def _build_org_path(unit: OrganizationUnit | None) -> str:
    if not unit:
        return "-"
    parts = []
    current = unit
    seen = set()
    while current and current.id not in seen:
        seen.add(current.id)
        parts.append((current.name or "").strip())
        current = current.parent
    parts = [part for part in reversed(parts) if part]
    return " > ".join(parts) if parts else "-"

def _serialize_manager_card(manager, fallback_unit: str = "-") -> dict | None:
    if not manager:
        return None
    unit_name = (getattr(manager, "birim", None) or "").strip() or fallback_unit or "-"
    return {
        "id": getattr(manager, "id", None),
        "full_name": _profile_full_name(manager) or "-",
        "ad": getattr(manager, "ad", None) or "",
        "soyad": getattr(manager, "soyad", None) or "",
        "unvan": _safe_text(getattr(manager, "unvan", None)),
        "birim": _safe_text(unit_name),
        "sicil_no": _safe_text(getattr(manager, "sicil_no", None)),
    }

def _resolve_personnel_profile_hierarchy(user):
    current_assignment = (
        EmployeeOrgAssignmentHistory.query
        .filter_by(employee_id=user.id, is_current=True)
        .order_by(EmployeeOrgAssignmentHistory.start_date.desc(), EmployeeOrgAssignmentHistory.id.desc())
        .first()
    )

    org_unit = getattr(user, "organization_unit", None)
    birim = (getattr(user, "birim", None) or "").strip()
    if not birim and current_assignment:
        birim = (getattr(current_assignment, "unit_name_snapshot", None) or "").strip()
    if not birim and org_unit:
        birim = (getattr(org_unit, "name", None) or "").strip()

    ust_birim = (getattr(user, "ust_birim", None) or "").strip()
    if not ust_birim and current_assignment:
        ust_birim = (getattr(current_assignment, "parent_unit_name_snapshot", None) or "").strip()
    if not ust_birim and org_unit and getattr(org_unit, "parent", None):
        ust_birim = (getattr(org_unit.parent, "name", None) or "").strip()

    org_path = ""
    if current_assignment and (getattr(current_assignment, "org_path_snapshot", None) or "").strip():
        org_path = current_assignment.org_path_snapshot.strip()
    elif org_unit:
        org_path = _build_org_path(org_unit)

    manager_1 = None
    manager_2 = None
    manager_3 = None

    direct_manager_1_id = getattr(user, "manager_1_id", None)
    direct_manager_2_id = getattr(user, "manager_2_id", None)
    direct_manager_3_id = getattr(user, "manager_3_id", None)

    if direct_manager_1_id:
        manager_1 = db.session.get(User, direct_manager_1_id)
    if direct_manager_2_id:
        manager_2 = db.session.get(User, direct_manager_2_id)
    if direct_manager_3_id:
        manager_3 = db.session.get(User, direct_manager_3_id)

    if not manager_1:
        manager_1 = _resolve_user_by_sicil(getattr(user, "yonetici_sicil", None))
    if not manager_2:
        manager_2 = _resolve_user_by_sicil(getattr(user, "ikinci_yonetici_sicil", None))
    if not manager_3:
        manager_3 = _resolve_user_by_sicil(getattr(user, "ucuncu_yonetici_sicil", None))

    if current_assignment:
        if not manager_1:
            manager_1 = getattr(current_assignment, "manager_1_user", None) or _resolve_user_by_sicil(getattr(current_assignment, "manager_1_sicil_snapshot", None))
        if not manager_2:
            manager_2 = getattr(current_assignment, "manager_2_user", None) or _resolve_user_by_sicil(getattr(current_assignment, "manager_2_sicil_snapshot", None))
        if not manager_3:
            manager_3 = getattr(current_assignment, "manager_3_user", None) or _resolve_user_by_sicil(getattr(current_assignment, "manager_3_sicil_snapshot", None))

    hierarchy_state = "Tanımlı" if any([manager_1, manager_2, manager_3]) else "Tanımlı değil"

    return {
        "birim": _safe_text(birim),
        "ust_birim": _safe_text(ust_birim),
        "org_path": _safe_text(org_path),
        "hierarchy_state": hierarchy_state,
        "manager_1": _serialize_manager_card(manager_1, fallback_unit=birim),
        "manager_2": _serialize_manager_card(manager_2, fallback_unit=birim),
        "manager_3": _serialize_manager_card(manager_3, fallback_unit=birim),
    }

def _canonicalize_import_headers(headers: list[str], apply_ai_fixes: bool) -> tuple[list[str], int]:
    if not apply_ai_fixes:
        return list(headers), 0
    normalized = []
    alias_count = 0
    for header in headers:
        mapped = IMPORT_HEADER_ALIASES.get(header, header)
        if mapped != header:
            alias_count += 1
        normalized.append(mapped)
    return normalized, alias_count

def _collapse_spaces(value: str, apply_ai_fixes: bool) -> str:
    value = str(value or '').strip()
    return ' '.join(value.split()) if apply_ai_fixes else value

def _has_explicit_manager_columns(headers: list[str] | tuple[str, ...]) -> bool:
    # BYS360_IMPORT_EXPLICIT_MANAGER_CHAIN_PRESERVE_V1
    # Ops import akışında başlıklar bazen canonical, bazen normalize edilmiş gelir.
    # İki biçimi de kabul ederek Excel'deki amir zincirini otomatik motorun ezmesini engeller.
    manager_headers = {
        "yonetici_sicil",
        "yonetici sicil",
        "yönetici sicil",
        "1. amir sicil",
        "1 amir sicil",
        "1. amir",
        "1 amir",
        "ikinci_yonetici_sicil",
        "ikinci yonetici sicil",
        "ikinci yönetici sicil",
        "2. amir sicil",
        "2 amir sicil",
        "2. amir",
        "2 amir",
        "ucuncu_yonetici_sicil",
        "ucuncu yonetici sicil",
        "üçüncü yönetici sicil",
        "3. amir sicil",
        "3 amir sicil",
        "3. amir",
        "3 amir",
    }
    normalized = {normalize_text(header) for header in headers if str(header or "").strip()}
    return bool(normalized.intersection({normalize_text(item) for item in manager_headers}))

def get_default_first_login_password() -> str:
    import os
    import secrets
    try:
        configured = current_app.config.get("BYS360_DEFAULT_FIRST_LOGIN_PASSWORD") or current_app.config.get("DEFAULT_FIRST_LOGIN_PASSWORD")
    except Exception:
        configured = None
    return str(configured or os.environ.get("BYS360_DEFAULT_FIRST_LOGIN_PASSWORD") or os.environ.get("DEFAULT_FIRST_LOGIN_PASSWORD") or secrets.token_urlsafe(18))
