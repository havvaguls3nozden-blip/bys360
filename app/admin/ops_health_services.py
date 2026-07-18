"""Operational admin import health service extracted from ops_routes.py.

Route decorators stay in ops_routes.py. This module contains the heavy implementation body.
"""
from __future__ import annotations

from app.services.safe_user_delete_service import safe_delete_user_by_id
from app.core.datetime_utils import utc_now
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
from .ops_helpers import (
    _profile_full_name,
    _safe_text,
    _resolve_user_by_sicil,
    _build_org_path,
    _serialize_manager_card,
    _resolve_personnel_profile_hierarchy,
    _canonicalize_import_headers,
    _collapse_spaces,
    _has_explicit_manager_columns,
    get_default_first_login_password,
)

def admin_import_health_report_impl():
    """İçe aktarım sağlık raporunu veritabanı bağımsız şekilde üret.

    Önceki sürüm PostgreSQL'e özgü STRING_AGG, ::text ve BTRIM kullandığı için
    test/staging gibi SQLite ortamlarında 500 üretiyordu. Bu sürüm aynı raporu
    ORM ile derleyip hem SQLite hem PostgreSQL üzerinde güvenli şekilde çalıştırır.
    """

    units = (
        OrganizationUnit.query
        .order_by(OrganizationUnit.name.asc(), OrganizationUnit.id.asc())
        .all()
    )
    users = (
        User.query
        .filter(User.role != "admin", User.is_active.is_(True))
        .order_by(User.birim.asc(), User.ad.asc(), User.soyad.asc(), User.id.asc())
        .all()
    )

    unit_by_id = {unit.id: unit for unit in units}
    users_by_unit_id = {}
    for user in users:
        users_by_unit_id.setdefault(user.organization_unit_id, []).append(user)

    duplicate_buckets = {}
    for unit in units:
        parent = unit_by_id.get(unit.parent_id)
        key = (
            (unit.name or "").strip(),
            (unit.unit_type or "").strip(),
            ((parent.name if parent else "-") or "-").strip(),
        )
        duplicate_buckets.setdefault(key, []).append(unit)

    duplicate_units = []
    for (unit_name, unit_type, parent_name), bucket in duplicate_buckets.items():
        if len(bucket) <= 1:
            continue
        duplicate_units.append({
            "unit_name": unit_name,
            "unit_type": unit_type,
            "parent_name": parent_name or "-",
            "duplicate_count": len(bucket),
            "unit_ids": ", ".join(str(item.id) for item in bucket),
        })
    duplicate_units.sort(key=lambda row: (-int(row["duplicate_count"]), row["unit_name"].lower(), row["unit_ids"]))

    empty_workgroups = []
    for unit in units:
        if (unit.unit_type or "") != "calisma_grubu":
            continue
        parent = unit_by_id.get(unit.parent_id)
        personnel = users_by_unit_id.get(unit.id, [])
        if personnel:
            continue
        empty_workgroups.append({
            "id": unit.id,
            "unit_name": unit.name,
            "parent_name": (parent.name if parent else "-") or "-",
            "personnel_count": 0,
        })
    empty_workgroups.sort(key=lambda row: ((row["unit_name"] or "").lower(), int(row["id"])))

    unbound_users = []
    for user in users:
        if user.organization_unit_id is not None:
            continue
        unbound_users.append({
            "id": user.id,
            "ad": user.ad,
            "soyad": user.soyad,
            "sicil_no": user.sicil_no,
            "role": user.role,
            "birim": user.birim,
            "ust_birim": user.ust_birim,
        })

    mismatched_users = []
    incomplete_manager_chain = []
    for user in users:
        if user.organization_unit_id is not None:
            unit = unit_by_id.get(user.organization_unit_id)
            parent = unit_by_id.get(unit.parent_id) if unit else None
            user_birim = (user.birim or "").strip()
            user_ust_birim = (user.ust_birim or "").strip()
            unit_name = ((unit.name if unit else "") or "").strip()
            parent_name = ((parent.name if parent else "") or "").strip()
            if user_birim != unit_name or user_ust_birim != parent_name:
                mismatched_users.append({
                    "id": user.id,
                    "ad": user.ad,
                    "soyad": user.soyad,
                    "sicil_no": user.sicil_no,
                    "role": user.role,
                    "birim": user.birim,
                    "ust_birim": user.ust_birim,
                    "organization_unit_id": user.organization_unit_id,
                    "linked_unit": unit.name if unit else None,
                    "linked_parent": parent.name if parent else None,
                })

        required_missing = not (user.yonetici_sicil or "").strip()
        optional_fields = [
            (user.ikinci_yonetici_sicil or "").strip(),
            (user.ucuncu_yonetici_sicil or "").strip(),
        ]
        if required_missing or any(not value for value in optional_fields):
            incomplete_manager_chain.append({
                "id": user.id,
                "ad": user.ad,
                "soyad": user.soyad,
                "sicil_no": user.sicil_no,
                "role": user.role,
                "birim": user.birim,
                "yonetici_sicil": user.yonetici_sicil,
                "ikinci_yonetici_sicil": user.ikinci_yonetici_sicil,
                "ucuncu_yonetici_sicil": user.ucuncu_yonetici_sicil,
            })

    stats = {
        "duplicate_unit_count": len(duplicate_units),
        "empty_workgroup_count": len(empty_workgroups),
        "unbound_user_count": len(unbound_users),
        "mismatched_user_count": len(mismatched_users),
        "incomplete_manager_chain_count": len(incomplete_manager_chain),
        # eski şablon anahtarları için uyumluluk
        "duplicate_units": len(duplicate_units),
        "empty_workgroups": len(empty_workgroups),
        "unbound_users": len(unbound_users),
        "mismatched_users": len(mismatched_users),
        "incomplete_manager_chain": len(incomplete_manager_chain),
    }

    bindable_users = sum(1 for row in unbound_users if (row.get("birim") or "").strip() and (row.get("ust_birim") or "").strip())
    syncable_users = len(mismatched_users)
    duplicate_review_units = len(duplicate_units)
    chain_review_users = len(incomplete_manager_chain)
    simulation = {
        "bindable_users": bindable_users,
        "syncable_users": syncable_users,
        "duplicate_review_units": duplicate_review_units,
        "chain_review_users": chain_review_users,
        "triggered": request.method == "POST",
    }
    if request.method == "POST":
        flash(
            f"AI düzeltme simülasyonu çalıştı: {bindable_users} bağlama adayı, {syncable_users} senkron adayı, {chain_review_users} manuel zincir incelemesi.",
            "info",
        )

    return safe_render(
        "admin_import_health_report.html",
        "<h3>İçe Aktarım Sağlık Raporu</h3>",
        duplicate_units=duplicate_units,
        empty_workgroups=empty_workgroups,
        unbound_users=unbound_users,
        mismatched_users=mismatched_users,
        incomplete_manager_chain=incomplete_manager_chain,
        stats=stats,
        summary=stats,
        ai_import_health_panel=build_import_health_priority_ai_panel(
            stats=stats,
            duplicate_units=duplicate_units,
            unbound_users=unbound_users,
            mismatched_users=mismatched_users,
            incomplete_manager_chain=incomplete_manager_chain,
            empty_workgroups=empty_workgroups,
        ),
        ai_import_simulation_panel=build_import_health_simulation_ai_panel(
            stats=stats,
            simulation=simulation,
        ),
        ai_import_simulation=simulation,
    )
