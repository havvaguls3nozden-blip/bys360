"""Operational admin personnel services extracted from ops_routes.py.

Route decorators stay in ops_routes.py. This module contains implementation bodies.
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
from .ops_health_services import admin_import_health_report_impl
from .ops_import_services import admin_user_import_impl

def download_personnel_template_impl():
    wb = Workbook()
    ws = wb.active
    ws.title = "Personel Şablonu"

    headers = [
        "Sicil No",
        "Ad",
        "Soyad",
        "E-Posta",
        "Unvan",
        "Birim",
        "Üst Birim",
        "Rol (opsiyonel)",
        "Yönetici Sicil (opsiyonel)",
        "İkinci Yönetici Sicil (opsiyonel)",
        "Üçüncü Yönetici Sicil (opsiyonel)",
    ]
    ws.append(headers)

    example_rows = [
        ["1001", "Ahmet", "Yılmaz", "ahmet.yilmaz@ktb.gov.tr", "Personel", "Eğitim ve Performans Çalışma Grubu", "Personel ve Destek Hizmetleri Grup Başkanlığı", "personel", "", "", ""],
        ["1002", "Ayşe", "Demir", "ayse.demir@ktb.gov.tr", "Koordinatör", "Eğitim ve Performans Çalışma Grubu", "Personel ve Destek Hizmetleri Grup Başkanlığı", "koordinator", "", "", ""],
    ]
    for row in example_rows:
        ws.append(row)

    header_fill = PatternFill("solid", fgColor="8B0000")
    header_font = Font(color="FFFFFF", bold=True)
    thin = Side(style="thin", color="D1D5DB")

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
            cell.alignment = Alignment(vertical="center", wrap_text=True)

    widths = {
        "A": 16,
        "B": 18,
        "C": 18,
        "D": 30,
        "E": 24,
        "F": 34,
        "G": 34,
        "H": 20,
        "I": 20,
        "J": 24,
        "K": 24,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="bys360_personel_sablonu.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
