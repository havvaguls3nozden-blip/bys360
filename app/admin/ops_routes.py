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
    if request.method == "POST":
        f = request.files.get("excel_file")
        if not f or not f.filename:
            flash("Lütfen bir Excel dosyası seçin.", "warning")
            return safe_render("excel_import.html", "<h3>Excel İçe Aktar</h3>", apply_ai_fixes=False, ai_excel_fix_panel=build_excel_fix_preview_ai_panel())

        wb = load_workbook(f, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            flash("Excel dosyası boş.", "danger")
            return safe_render("excel_import.html", "<h3>Excel İçe Aktar</h3>", apply_ai_fixes=False, ai_excel_fix_panel=build_excel_fix_preview_ai_panel())

        import_preflight = validate_personnel_import_rows_for_commit(rows)
        if not import_preflight.get("ok"):
            errors = list(import_preflight.get("errors") or [])
            warnings = list(import_preflight.get("warnings") or [])
            flash("Excel ön kontrolü başarısız. Hiçbir kayıt veritabanına yazılmadı.", "danger")
            return safe_render(
                "excel_import.html",
                "<h3>Excel İçe Aktar</h3>",
                errors=errors,
                import_preflight=import_preflight,
                import_warnings=warnings,
                apply_ai_fixes=False,
                ai_excel_fix_panel=build_excel_fix_preview_ai_panel(errors=errors, normalized_headers=import_preflight.get("canonical_headers") or []),
            )

        apply_ai_fixes = (request.form.get("apply_ai_fixes") or "").strip().lower() in {"1", "true", "on", "evet", "yes"}
        headers = [normalize_text(h) if h is not None else "" for h in rows[0]]
        normalized_headers, header_alias_count = _canonicalize_import_headers(headers, apply_ai_fixes)
        autofix_stats = {"header_alias_count": header_alias_count, "whitespace_trim_count": 0, "inferred_role_count": 0, "default_active_count": 0}
        idx = {h: i for i, h in enumerate(normalized_headers)}

        def getv(row, name, default=""):
            key = normalize_text(name)
            if key not in idx:
                return default
            value = row[idx[key]]
            if value is None:
                return default
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            if isinstance(value, int):
                return str(value)
            return str(value).strip()

        def getv_any(row, *names, default=""):
            for name in names:
                value = getv(row, name, None)
                if value is not None and str(value).strip() != "":
                    return str(value).strip()
            return default

        created = 0
        updated = 0
        skipped_admin = 0
        errors = []
        touched_users = []

        for rowno, row in enumerate(rows[1:], start=2):
            if not row or all(v is None or str(v).strip() == "" for v in row):
                continue

            sicil_no = _collapse_spaces(getv_any(row, "sicil_no", "sicil no", "sicil"), apply_ai_fixes)
            ad = _collapse_spaces(getv_any(row, "ad", "adi", "adı"), apply_ai_fixes)
            soyad = _collapse_spaces(getv_any(row, "soyad", "soyadi", "soyadı"), apply_ai_fixes)
            email = _collapse_spaces(getv_any(row, "email", "e-posta", "eposta", default="").lower(), apply_ai_fixes)
            unvan = _collapse_spaces(getv_any(row, "unvan", "ünvan"), apply_ai_fixes)
            birim = _collapse_spaces(getv_any(row, "birim"), apply_ai_fixes)
            ust_birim = _collapse_spaces(getv_any(row, "ust_birim", "ust birim", "üst birim"), apply_ai_fixes)
            raw_role = getv_any(row, "role", "rol", default="")
            inferred_role, inferred_role_label = infer_role_from_profile(raw_role=raw_role, unvan=unvan, birim=birim, ust_birim=ust_birim)
            if apply_ai_fixes and not normalize_text(raw_role) and inferred_role:
                autofix_stats["inferred_role_count"] += 1
            role = canonical_role_value(raw_role or inferred_role or "personel")
            role_label = canonical_role_label(raw_role or inferred_role_label or role)
            yonetici_sicil = _collapse_spaces(getv_any(
                row,
                "yonetici_sicil",
                "yonetici sicil",
                "yönetici sicil",
                "1. amir sicil",
                "1 amir sicil",
                "birinci amir sicil",
                "1. yönetici sicil",
                "1 yonetici sicil",
                "1. amir",
                "1 amir",
                "birinci amir",
            ), apply_ai_fixes)
            ikinci_yonetici_sicil = _collapse_spaces(getv_any(
                row,
                "ikinci_yonetici_sicil",
                "ikinci yonetici sicil",
                "ikinci yönetici sicil",
                "2. amir sicil",
                "2 amir sicil",
                "ikinci amir sicil",
                "2. yönetici sicil",
                "2 yonetici sicil",
                "2. amir",
                "2 amir",
                "ikinci amir",
            ), apply_ai_fixes)
            ucuncu_yonetici_sicil = _collapse_spaces(getv_any(
                row,
                "ucuncu_yonetici_sicil",
                "ucuncu yonetici sicil",
                "üçüncü yönetici sicil",
                "ucuncu yönetici sicil",
                "3. amir sicil",
                "3 amir sicil",
                "üçüncü amir sicil",
                "ucuncu amir sicil",
                "3. yönetici sicil",
                "3 yonetici sicil",
                "3. amir",
                "3 amir",
                "üçüncü amir",
                "ucuncu amir",
            ), apply_ai_fixes)
            personnel_category = normalize_personnel_category_label(getv_any(
                row,
                "personnel_category",
                "kategori",
                "personel kategori",
                "personel kategorisi",
                "performans kategori",
                "performans kategorisi",
                default="Diğer",
            ))  # BYS360_PHASE2_3_IMPORT_CATEGORY_READ
            is_active_source = getv_any(row, "is_active", "aktif", default="1")
            if apply_ai_fixes and not str(is_active_source or "").strip():
                autofix_stats["default_active_count"] += 1
            is_active_raw = normalize_text(is_active_source)
            is_active = is_active_raw in {"1", "true", "evet", "aktif", "yes", ""}

            if apply_ai_fixes and any("  " in str(v or "") for v in row):
                autofix_stats["whitespace_trim_count"] += 1
            if not sicil_no or not ad or not soyad or not email or not unvan or not birim:
                errors.append(f"Satır {rowno}: zorunlu alan eksik.")
                continue
            if normalize_text(role) == "admin":
                skipped_admin += 1
                continue

            unit = None
            try:
                # Birim otomatik oluşsun; bu ekrandaki en kritik işlerden biriydi.
                from app.services.hierarchy_admin_service import ensure_unit_exists_strict
                unit = ensure_unit_exists_strict(birim, ust_birim, role)
            except Exception as exc:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/admin/ops_routes.py:621)")
                errors.append(f"Satır {rowno}: birim oluşturulamadı -> {exc}")
                continue

            if not unit:
                errors.append(f"Satır {rowno}: birim çözümlenemedi -> {birim} / {ust_birim}")
                continue

            user = User.query.filter_by(sicil_no=sicil_no).first()
            if user and user.role == "admin":
                skipped_admin += 1
                continue

            resolved_ust_birim = ust_birim if ust_birim else (unit.parent.name if unit.parent else unit.name)

            try:
                if user:
                    user.ad = ad
                    user.soyad = soyad
                    user.email = email
                    user.unvan = unvan
                    user.role = role or "personel"
                    if hasattr(user, "role_label"):
                        user.role_label = role_label
                    user.organization_unit_id = unit.id
                    user.birim = birim
                    user.ust_birim = resolved_ust_birim
                    user.yonetici_sicil = yonetici_sicil or None
                    user.ikinci_yonetici_sicil = ikinci_yonetici_sicil or None
                    user.ucuncu_yonetici_sicil = ucuncu_yonetici_sicil or None
                    user.is_active = is_active
                    assign_user_performance_category(user, personnel_category, db_session=db.session)  # BYS360_PHASE2_3_IMPORT_CATEGORY_UPDATE_BINDING
                    updated += 1
                    touched_users.append(user)
                else:
                    user = User(
                        ad=ad,
                        soyad=soyad,
                        sicil_no=sicil_no,
                        email=email,
                        unvan=unvan,
                        role=role or "personel",
                        role_label=role_label,
                        organization_unit_id=unit.id,
                        birim=birim,
                        ust_birim=resolved_ust_birim,
                        yonetici_sicil=yonetici_sicil or None,
                        ikinci_yonetici_sicil=ikinci_yonetici_sicil or None,
                        ucuncu_yonetici_sicil=ucuncu_yonetici_sicil or None,
                        is_active=is_active,
                    )
                    assign_user_performance_category(user, personnel_category, db_session=db.session)  # BYS360_PHASE2_3_IMPORT_CATEGORY_CREATE_BINDING
                    user.set_password(get_default_first_login_password())
                    if hasattr(user, "must_change_password"):
                        user.must_change_password = True
                    if hasattr(user, "must_set_security_question"):
                        user.must_set_security_question = True
                    if hasattr(user, "is_first_login"):
                        user.is_first_login = True
                    db.session.add(user)
                    created += 1
                    touched_users.append(user)
            except Exception as exc:
                errors.append(f"Satır {rowno}: {exc}")

        if errors:
            db.session.rollback()
            flash("Excel içe aktarma sırasında hatalar oluştu.", "danger")
            return safe_render("excel_import.html", "<h3>Excel İçe Aktar</h3>", errors=errors, apply_ai_fixes=apply_ai_fixes, ai_excel_fix_panel=build_excel_fix_preview_ai_panel(errors=errors, normalized_headers=normalized_headers, autofix_enabled=apply_ai_fixes, applied_fixes=autofix_stats))

        db.session.flush()
        has_explicit_manager_columns = _has_explicit_manager_columns(normalized_headers)
        if has_explicit_manager_columns:
            # BYS360_IMPORT_EXPLICIT_MANAGER_CHAIN_PRESERVE_V1
            manager_sync_summary = sync_touched_users_manager_ids_from_sicils(
                touched_users,
                user_model=User,
            )
            auto_summary = {
                'updated_count': 0,
                'skipped_count': len(touched_users),
                'warnings': manager_sync_summary.get('warnings', []),
            }
        else:
            auto_summary = auto_apply_manager_chains(
                touched_users,
                fill_only_missing=False,
                commit=False,
                preserve_explicit_chain=True,
            )
            manager_sync_summary = sync_touched_users_manager_ids_from_sicils(
                touched_users,
                user_model=User,
            )
        db.session.commit()
        assignment_result = None
        from app.models import PerformancePeriod
        active_period = PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()
        if active_period:
            assignment_result = generate_assignments_for_active_period(period_id=active_period.id, actor_user_id=current_user.id)
        flash(
            f"İçe aktarma tamamlandı. Yeni: {created}, Güncellenen: {updated}, Atlanan admin: {skipped_admin}, kategori alanı işlendi, kaynak kurala göre yeniden kurulan zincir: {auto_summary.get('updated_count', 0)}",
            "success",
        )
        if has_explicit_manager_columns:
            flash('Excel içindeki yönetici sicil ve ikinci yönetici sicil alanları kaynak veri olarak korundu; amir seçili görünümü bu sicillere göre senkronlandı.', 'info')
        if assignment_result and assignment_result.get("ok"):
            flash(
                f"Aktif dönem görevleri de otomatik yenilendi. Oluşturulan/güncellenen görev: {assignment_result.get('created', 0)}, atlanan: {assignment_result.get('skipped', 0)}, gerçek uyarı: {assignment_result.get('warning_count', 0)}.",
                "success" if not assignment_result.get("warning_count") else "warning",
            )
        elif assignment_result and not assignment_result.get("ok"):
            flash(assignment_result.get("message", "Aktif dönem görevleri otomatik yenilenemedi."), "warning")
        if apply_ai_fixes and sum(int(v or 0) for v in autofix_stats.values()) > 0:
            flash(f"AI otomatik düzeltme akışı uygulandı. Başlık eşleştirme: {autofix_stats.get('header_alias_count', 0)}, metin temizliği: {autofix_stats.get('whitespace_trim_count', 0)}, rol çıkarımı: {autofix_stats.get('inferred_role_count', 0)}, varsayılan aktiflik: {autofix_stats.get('default_active_count', 0)}", "info")
        if auto_summary.get("warnings"):
            current_app.logger.warning(
                "Otomatik zincir ham uyarıları gizlendi: %s",
                " | ".join(auto_summary["warnings"][:10]),
            )
            flash(
                f"Otomatik zincir denetiminde {len(auto_summary.get('warnings', []))} kayıt için teknik not üretildi; ham liste kullanıcı ekranında gösterilmedi.",
                "info",
            )
        return redirect(url_for("main.admin_users"))

    return safe_render("excel_import.html", "<h3>Excel İçe Aktar</h3>", apply_ai_fixes=False, ai_excel_fix_panel=build_excel_fix_preview_ai_panel())


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
    user = db.session.get(User, user_id)
    if not user:
        flash("Personel kaydı bulunamadı.", "danger")
        return redirect(url_for("main.personnel_list"))

    avatar_url = url_for("static", filename="img/default-avatar.svg")
    if hasattr(user, "profile_photo") and getattr(user, "profile_photo", None):
        avatar_url = url_for("static", filename=f"uploads/{user.profile_photo}")

    role_text = ""
    if hasattr(user, "role") and (getattr(user, "role", "") or "").strip():
        role_text = user.role
    elif hasattr(user, "role_label") and (getattr(user, "role_label", "") or "").strip():
        role_text = user.role_label

    resolved_hierarchy = _resolve_personnel_profile_hierarchy(user)

    profile_data = {
        "id": user.id,
        "full_name": _profile_full_name(user),
        "ad": getattr(user, "ad", "") or "-",
        "soyad": getattr(user, "soyad", "") or "-",
        "email": getattr(user, "email", "") or "-",
        "sicil_no": getattr(user, "sicil_no", "") or "-",
        "unvan": getattr(user, "unvan", "") or "-",
        "birim": resolved_hierarchy["birim"],
        "ust_birim": resolved_hierarchy["ust_birim"],
        "org_path": resolved_hierarchy["org_path"],
        "hierarchy_state": resolved_hierarchy["hierarchy_state"],
        "role_text": role_text or "-",
        "is_active": bool(getattr(user, "is_active", False)),
        "must_change_password": bool(getattr(user, "must_change_password", False)) if hasattr(user, "must_change_password") else False,
        "must_set_security_question": bool(getattr(user, "must_set_security_question", False)) if hasattr(user, "must_set_security_question") else False,
        "is_first_login": bool(getattr(user, "is_first_login", False)) if hasattr(user, "is_first_login") else False,
        "avatar_url": avatar_url,
        "manager_1": resolved_hierarchy["manager_1"],
        "manager_2": resolved_hierarchy["manager_2"],
        "manager_3": resolved_hierarchy["manager_3"],
        "yonetici_sicil": getattr(user, "yonetici_sicil", None),
        "ikinci_yonetici_sicil": getattr(user, "ikinci_yonetici_sicil", None),
        "ucuncu_yonetici_sicil": getattr(user, "ucuncu_yonetici_sicil", None),
    }

    from app.services.hr_operations_service import build_personnel_profile_hr_context

    return safe_render(
        "personnel_profile.html",
        "<h3>Personel Profili</h3>",
        profile=profile_data,
        ai_personnel_chain_panel=build_personnel_profile_chain_ai_panel(profile_data),
        hr_context=build_personnel_profile_hr_context(user),
    )


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

