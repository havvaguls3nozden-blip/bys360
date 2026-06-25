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
    user = db.session.get(User, user_id)
    if not user:
        flash("Kullanıcı bulunamadı.", "danger")
        return redirect(url_for("main.admin_users"))

    try:
        remove_photo = (request.form.get("remove_profile_photo") or "").strip().lower() in {"1", "true", "on", "evet", "yes"}

        if remove_photo:
            _delete_profile_photo_file(user.profile_photo_path)
            user.profile_photo_path = None
            user.profile_photo_updated_at = utc_now()
            db.session.commit()
            flash("Profil fotoğrafı kaldırıldı.", "success")
            return redirect(url_for("main.admin_user_edit", user_id=user.id))

        photo = request.files.get("profile_photo")
        if not photo or not getattr(photo, "filename", ""):
            flash("Lütfen bir fotoğraf seçin.", "warning")
            return redirect(url_for("main.admin_user_edit", user_id=user.id))

        _save_profile_photo(photo, user)
        db.session.commit()
        flash("Profil fotoğrafı güncellendi.", "success")
        return redirect(url_for("main.admin_user_edit", user_id=user.id))

    except Exception as exc:
        db.session.rollback()
        flash(f"Profil fotoğrafı güncellenirken hata oluştu: {exc}", "danger")
        return redirect(url_for("main.admin_user_edit", user_id=user.id))


@main_bp.route("/admin/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_user_toggle_active(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("Kullanıcı bulunamadı.", "danger")
        return redirect(url_for("main.admin_users"))
    try:
        ensure_not_self_target(actor_id=current_user.id, target_id=user.id, entity_label="kullanıcı")
        user.is_active = ensure_boolean_toggle(current_value=getattr(user, "is_active", False), entity_label="Kullanıcı", requested_state=request.form.get("target_state"))
        db.session.commit()
        flash("Kullanıcı durumu güncellendi.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        db.session.rollback()
        flash(f"Kullanıcı durumu güncellenirken hata oluştu: {exc}", "danger")
    return redirect(url_for("main.admin_users"))


@main_bp.route("/admin/users/<int:user_id>/archive", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_user_archive(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("Kullanıcı bulunamadı.", "danger")
        return redirect(url_for("main.admin_users"))

    try:
        ensure_not_self_target(actor_id=current_user.id, target_id=user.id, entity_label="kullanıcı")
        if bool(getattr(user, "is_archived", False)) and not bool(getattr(user, "is_active", True)):
            flash("Kullanıcı zaten arşivde.", "warning")
            return redirect(url_for("main.admin_users"))
        user.is_active = False
        if hasattr(user, "is_archived"):
            user.is_archived = True
        if hasattr(user, "archived_at") and not getattr(user, "archived_at", None):
            user.archived_at = utc_now()
        db.session.commit()
        flash("Kullanıcı arşive alındı.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        db.session.rollback()
        flash(f"Arşivleme sırasında hata oluştu: {exc}", "danger")
    return redirect(url_for("main.admin_users"))


@main_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_user_delete(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("Kullanıcı bulunamadı.", "danger")
        return redirect(url_for("main.admin_users"))
    if user.id == current_user.id:
        flash("Kendi hesabınızı silemezsiniz.", "warning")
        return redirect(url_for("main.admin_users"))

    try:
        safe_delete_user_by_id(getattr(user, "id", user), commit=False)
        db.session.commit()
        flash("Kullanıcı silindi.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Bu kullanıcı ilişkili kayıtlar nedeniyle silinemedi.", "danger")
    except Exception as exc:
        db.session.rollback()
        flash(f"Bu kullanıcı silinemedi: {exc}", "danger")
    return redirect(url_for("main.admin_users"))


@main_bp.route("/admin/users/bulk-delete", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_users_bulk_delete():
    ids = normalize_int_list(request.form.getlist("user_ids"))
    if not ids:
        flash("Lütfen en az bir personel seçin.", "warning")
        return redirect(url_for("main.admin_users"))

    deleted_count = 0
    blocked_count = 0

    for user_id in ids:
        user = db.session.get(User, user_id)
        if not user:
            continue
        if user.id == current_user.id:
            blocked_count += 1
            continue

        try:
            safe_delete_user_by_id(getattr(user, "id", user), commit=False)
            db.session.commit()
            deleted_count += 1
        except IntegrityError:
            db.session.rollback()
            blocked_count += 1
        except Exception:
            db.session.rollback()
            blocked_count += 1

    if blocked_count > 0:
        flash(
            f"Toplu silme tamamlandı. Silinen: {deleted_count}, silinemeyen: {blocked_count}. "
            f"Silinemeyen kayıtlar ilişkili veri içeriyor olabilir.",
            "warning",
        )
    else:
        flash(f"Toplu silme tamamlandı. Silinen kayıt: {deleted_count}", "success")

    return redirect(url_for("main.admin_users"))


@main_bp.route("/admin/users/bulk-archive", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_users_bulk_archive():
    ids = normalize_int_list(request.form.getlist("user_ids"))
    if not ids:
        flash("Lütfen en az bir personel seçin.", "warning")
        return redirect(url_for("main.admin_users"))

    updated = 0
    for user_id in ids:
        user = db.session.get(User, user_id)
        if not user or user.id == current_user.id:
            continue
        if bool(getattr(user, "is_archived", False)) and not bool(getattr(user, "is_active", True)):
            continue
        user.is_active = False
        if hasattr(user, "is_archived"):
            user.is_archived = True
        if hasattr(user, "archived_at") and not getattr(user, "archived_at", None):
            user.archived_at = utc_now()
        updated += 1

    db.session.commit()
    flash(f"Toplu arşivleme tamamlandı. Güncellenen kayıt: {updated}", "success")
    return redirect(url_for("main.admin_users"))


@main_bp.route("/admin/users/bulk-passive", methods=["POST"])
@login_required
@admin_required
@menu_key_required("admin_users")
def admin_users_bulk_passive():
    ids = normalize_int_list(request.form.getlist("user_ids"))
    if not ids:
        flash("Lütfen en az bir personel seçin.", "warning")
        return redirect(url_for("main.admin_users"))

    updated = 0
    for user_id in ids:
        user = db.session.get(User, user_id)
        if not user or user.id == current_user.id:
            continue
        if not bool(getattr(user, "is_active", False)):
            continue
        user.is_active = False
        updated += 1

    db.session.commit()
    flash(f"Toplu pasif yapma tamamlandı. Güncellenen kayıt: {updated}", "success")
    return redirect(url_for("main.admin_users"))


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
    try:
        reset_all_personnel_and_related_data()
        db.session.commit()
        flash("Personel, hiyerarşi ve ilişkili performans verileri tamamen sıfırlandı.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Sıfırlama işlemi sırasında hata oluştu: {exc}", "danger")

    return redirect(url_for("main.admin_users"))


@main_bp.route("/performance/hierarchy-settings/bulk-assign", methods=["POST"])
@login_required
@admin_required
def performance_hierarchy_bulk_assign():
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

