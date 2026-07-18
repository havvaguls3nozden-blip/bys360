"""Operational admin performance services extracted from ops_routes.py.

Route decorators stay in ops_routes.py. This module contains implementation bodies.
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
from .ops_health_services import admin_import_health_report_impl
from .ops_import_services import admin_user_import_impl
from .ops_personnel_services import download_personnel_template_impl
from .ops_personnel_services import personnel_profile_impl

def performance_hierarchy_bulk_assign_impl():
    ust_birim = (request.form.get("ust_birim") or "").strip()
    birim = (request.form.get("birim") or "").strip()
    role = (request.form.get("role") or "").strip()

    yonetici_sicil = (request.form.get("bulk_yonetici_sicil") or "").strip() or None
    ikinci_yonetici_sicil = (request.form.get("bulk_ikinci_yonetici_sicil") or "").strip() or None
    ucuncu_yonetici_sicil = (request.form.get("bulk_ucuncu_yonetici_sicil") or "").strip() or None
    level_3_enabled = request.form.get("bulk_level_3_enabled") == "on"

    query = User.query.filter(User.role != "admin")
    if ust_birim:
        query = query.filter(User.ust_birim == ust_birim)
    if birim:
        query = query.filter(User.birim == birim)
    if role:
        query = query.filter(User.role == role)

    users = query.all()
    if not users:
        flash("Toplu atama için uygun personel bulunamadı.", "warning")
        return redirect(url_for("main.performance_hierarchy_settings"))

    updated_count = 0
    for user_obj in users:
        # Rol/ünvan anahtar kelimesine göre otomatik daraltma yapılmaz.
        # Tek amir istisnası yalnızca gerçekten başkana doğrudan bağlı ve
        # sadece başkanın puan verdiği personelde, alanlar o şekilde boş
        # bırakıldıysa oluşur.
        user_obj.yonetici_sicil = yonetici_sicil
        user_obj.ikinci_yonetici_sicil = ikinci_yonetici_sicil
        user_obj.ucuncu_yonetici_sicil = ucuncu_yonetici_sicil if level_3_enabled else None
        updated_count += 1

    db.session.commit()

    active_period = PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()
    assignment_result = None
    if active_period:
        assignment_result = generate_assignments_for_active_period(period_id=active_period.id, actor_user_id=current_user.id)

    flash(f"Toplu hiyerarşi ataması tamamlandı. Güncellenen personel: {updated_count}", "success")
    if assignment_result and assignment_result.get("ok"):
        flash("Aktif dönem görevleri toplu hiyerarşi ataması sonrası yeniden senkronlandı.", "success")
    elif assignment_result and not assignment_result.get("ok"):
        flash(assignment_result.get("message", "Aktif dönem görevleri yeniden senkronlanamadı."), "warning")
    return redirect(url_for("main.performance_hierarchy_settings"))
