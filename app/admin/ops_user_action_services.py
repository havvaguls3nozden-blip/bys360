"""Operational admin user action services extracted from ops_routes.py.

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
from .ops_performance_services import performance_hierarchy_bulk_assign_impl

def ensure_not_self_target(actor_id, target_id, entity_label="kayıt"):
    if actor_id is not None and target_id is not None and str(actor_id) == str(target_id):
        raise ValueError(f"Kendi {entity_label} kaydınız üzerinde bu işlem yapılamaz.")

def admin_users_bulk_delete_impl():
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

def admin_user_change_photo_impl(user_id: int):
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

def admin_user_archive_impl(user_id: int):
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

def admin_users_bulk_archive_impl():
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

def admin_user_delete_impl(user_id: int):
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

def admin_users_bulk_passive_impl():
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

def admin_user_toggle_active_impl(user_id: int):
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

def admin_users_reset_all_impl():
    try:
        reset_all_personnel_and_related_data()
        db.session.commit()
        flash("Personel, hiyerarşi ve ilişkili performans verileri tamamen sıfırlandı.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Sıfırlama işlemi sırasında hata oluştu: {exc}", "danger")

    return redirect(url_for("main.admin_users"))
