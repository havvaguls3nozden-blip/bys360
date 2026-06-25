from __future__ import annotations

from app.services.safe_user_delete_service import safe_delete_user_by_id
from app.core.datetime_utils import utc_now
"""Admin operasyon route ailesi.

Bu dosya admin toplu işlemleri, personel profil/aksiyonları ve
hiyerarşi yardımcı rotalarını modüler yapı altında toplar.
"""

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
from .ops_personnel_services import download_personnel_template_impl
from .ops_personnel_services import personnel_profile_impl
from .ops_performance_services import performance_hierarchy_bulk_assign_impl
from .ops_user_action_services import admin_users_bulk_delete_impl, admin_user_change_photo_impl, admin_user_archive_impl, admin_users_bulk_archive_impl, admin_user_delete_impl, admin_users_bulk_passive_impl, admin_user_toggle_active_impl, admin_users_reset_all_impl

LEGACY_SHIM = False
LEGACY_RUNTIME_STATUS = "active_modular_main_blueprint_routes"
LEGACY_ROUTE_FAMILY = "admin_bulk_ops_and_personnel_actions"
LEGACY_NOTE = (
    "Admin toplu işlemleri, personel profil/aksiyonları ve hiyerarşi "
    "yardımcı rotaları app.admin.ops_routes altında çalışır."
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





@main_bp.route("/admin/users/<int:user_id>/photo", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_user_change_photo(user_id: int):
    return admin_user_change_photo_impl(user_id)


@main_bp.route("/admin/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_user_toggle_active(user_id: int):
    return admin_user_toggle_active_impl(user_id)


@main_bp.route("/admin/users/<int:user_id>/archive", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_user_archive(user_id: int):
    return admin_user_archive_impl(user_id)


@main_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_user_delete(user_id: int):
    return admin_user_delete_impl(user_id)


@main_bp.route("/admin/users/bulk-delete", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_users_bulk_delete():
    return admin_users_bulk_delete_impl()


@main_bp.route("/admin/users/bulk-archive", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_users_bulk_archive():
    return admin_users_bulk_archive_impl()


@main_bp.route("/admin/users/bulk-passive", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_users_bulk_passive():
    return admin_users_bulk_passive_impl()


@main_bp.route("/admin/users/import", methods=["GET", "POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_user_import():
    return admin_user_import_impl()


@main_bp.route("/admin/import-health-report")
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_import_health_report():
    return admin_import_health_report_impl()


@main_bp.route("/admin/users/reset-all", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_users_reset_all():
    return admin_users_reset_all_impl()


@main_bp.route("/performance/hierarchy-settings/bulk-assign", methods=["POST"])
@login_required
@admin_required
def performance_hierarchy_bulk_assign():
    return performance_hierarchy_bulk_assign_impl()


@main_bp.route("/personnel/template/download")
@login_required
@admin_required
@menu_key_required("admin_users")
def download_personnel_template():
    return download_personnel_template_impl()


@main_bp.route("/personnel/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def personnel_toggle_active(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("Personel kaydı bulunamadı.", "danger")
        return redirect(url_for("main.personnel_list"))

    try:
        if hasattr(user, "is_active"):
            user.is_active = not bool(user.is_active)
            db.session.commit()
            flash("Personel aktiflik durumu güncellendi.", "success")
        else:
            flash("Bu kullanıcı modelinde aktiflik alanı bulunamadı.", "warning")
    except Exception as exc:
        db.session.rollback()
        flash(f"Durum güncelleme sırasında hata oluştu: {exc}", "danger")

    return redirect(url_for("main.personnel_list"))


@main_bp.route("/personnel/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def personnel_delete(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("Personel kaydı bulunamadı.", "danger")
        return redirect(url_for("main.personnel_list"))

    try:
        safe_delete_user_by_id(getattr(user, "id", user), commit=False)
        db.session.commit()
        flash("Personel kaydı silindi.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Silme işlemi sırasında hata oluştu: {exc}", "danger")

    return redirect(url_for("main.personnel_list"))


@main_bp.route("/personnel/<int:user_id>/profile")
@login_required
@admin_required
@menu_key_required("admin_users")
def personnel_profile(user_id: int):
    return personnel_profile_impl(user_id)


__all__ = [
    "LEGACY_SHIM",
    "LEGACY_RUNTIME_STATUS",
    "LEGACY_ROUTE_FAMILY",
    "LEGACY_NOTE",
    "admin_user_change_photo",
    "admin_user_toggle_active",
    "admin_user_archive",
    "admin_user_delete",
    "admin_users_bulk_delete",
    "admin_users_bulk_archive",
    "admin_users_bulk_passive",
    "admin_user_import",
    "admin_import_health_report",
    "admin_users_reset_all",
    "performance_hierarchy_bulk_assign",
    "download_personnel_template",
    "personnel_toggle_active",
    "personnel_delete",
    "personnel_profile",
]

# BYS360_PERFORMANCE_COMPLETION_PHASE2_IMPORT_CATEGORY_MARKER
# Toplu personel import tarafında kategori/personel kategorisi sütunları desteklenir.
try:
    from app.services.performance.phase2_category_center import normalize_category_label as _phase2_normalize_category_label
except Exception:
    def _phase2_normalize_category_label(value):
        return str(value or "Diğer").strip() or "Diğer"


# Compatibility guard.
def ensure_not_self_target(actor_id, target_id, entity_label="kayıt"):
    if actor_id is not None and target_id is not None and str(actor_id) == str(target_id):
        raise ValueError(f"Kendi {entity_label} kaydınız üzerinde bu işlem yapılamaz.")

