from __future__ import annotations

from app.main_handlers.account_communication_helpers import (
    utc_now,
    datetime,
    io,
    json,
    re,
    flash,
    redirect,
    request,
    send_file,
    url_for,
    current_user,
    db,
    flatten_settings_menu_definitions,
    get_grouped_menu_definitions,
    SECURITY_QUESTION_CHOICES,
    SystemSetting,
    User,
    UserMenuPermission,
    safe_render,
    _delete_profile_photo_file,
    _save_profile_photo,
    build_effective_user_menu_context,
    build_settings_foundation_context,
    build_settings_profile_context,
    build_settings_ui_diagnostics_panel,
    clear_user_menu_overrides,
    ensure_settings_phase1_seeded,
    get_role_default_menu_keys,
    get_unit_profile_menu_keys,
    save_module_settings_from_form,
    save_role_menu_defaults,
    save_system_settings_from_form,
    save_unit_menu_profile,
    save_user_menu_overrides,
    rollback_settings_change,
    enforce_first_login_security_flow_redirect,
    logging,
    logger,
    COMMUNICATION_POLICY_ROLE_OPTIONS,
    _build_communication_policy_items,
    _build_communication_role_matrix,
    SUPPORT_HELP_ROLE_MATRIX_ITEMS,
    PERFORMANCE_ROLE_MATRIX_V12_ITEMS,
    ASSISTANT_ROLE_MATRIX_ITEMS,
    ASSISTANT_ROLE_MATRIX_KEYS,
    ASSISTANT_ROLE_MATRIX_RECOMMENDED,
    ROLE_MATRIX_POLICY_CONFIGS,
    get_assistant_role_matrix_recommended_keys,
    _role_matrix_policy_config_map,
    _find_menu_item_by_key,
    _build_role_matrix_group,
    _build_settings_role_matrix_groups,
    _get_role_matrix_policy_items_or_raise,
    _role_matrix_form_field_name,
    _collect_role_matrix_visible_keys_from_form,
    enforce_first_login_security_flow,
    ASSISTANT_POLICY_ROLE_OPTIONS,
    ASSISTANT_DEFAULT_VISIBLE_ROLES,
    ASSISTANT_ROLE_MATRIX_ROWS,
    _assistant_visible_roles_from_settings,
    _build_assistant_role_matrix,
    _upsert_assistant_module_setting,
    save_assistant_role_matrix_from_form,
    reset_assistant_role_matrix_defaults,
    PERSONNEL_ROLE_MATRIX_CURRENT_SCOPE_ITEMS,
    _PERSONNEL_ROLE_MATRIX_CURRENT_SCOPE_KEYS,
    _BYS360_PREVIOUS_EXTEND_FLAT_MENU_ITEMS_FOR_ASSISTANT,
    _BYS360_BASE_ROLE_MATRIX_POLICY_CONFIGS,
    _BYS360_PERSONNEL_POLICY_CONFIG,
    _BYS360_PREVIOUS_BUILD_ROLE_MATRIX_POLICY_ITEMS,
    _build_role_matrix_policy_items,
    _BYS360_ALL_MENU_ROLE_MATRIX_ITEMS,
    _BYS360_ALL_MENU_ROLE_MATRIX_ITEM_BY_KEY,
    _BYS360_ASSISTANT_TAB_ROLE_MATRIX_ITEMS,
    _BYS360_ASSISTANT_TAB_RECOMMENDED,
    _BYS360_PERFORMANCE_MAIN_SWITCH_ITEM,
    _bys360_clean_general_role_matrix_performance_text_v5,
    _BYS360_PREVIOUS_EXTEND_FLAT_MENU_ITEMS_ALL_FEATURES_V1,
    _bys360_role_matrix_all_feature_items_v1,
    PORTAL_ROLE_MATRIX_V2_12_ITEMS,
    _PORTAL_ROLE_MATRIX_V2_12_CONFIG,
    _BYS360_PERFORMANCE_PERIOD_CENTER_POLICY_ITEMS_V2_1_23B,
    _bys360_merge_performance_period_center_policy_items_v2_1_23b,
    _BYS360_PREVIOUS_EXTEND_FLAT_MENU_ITEMS_V2_1_23B,
    extend_flat_menu_items_with_assistant_role_matrix_items,
)
from app.main_handlers.account_settings_helpers import account, settings_page  # noqa: F401

# Hesap güvenliği ve profil fotoğrafı işlemleri burada kalır; hesap/ayar ekranları
# account_settings_helpers üzerinden geriye dönük uyumla dışa aktarılır.

def account_change_photo():
    next_url = (request.form.get("next") or "").strip()
    redirect_target = next_url if next_url.startswith("/") and not next_url.startswith("//") else url_for("main.account")

    try:
        remove_photo = (request.form.get("remove_profile_photo") or "").strip().lower() in {"1", "true", "on", "evet", "yes"}

        if remove_photo:
            _delete_profile_photo_file(current_user.profile_photo_path)
            current_user.profile_photo_path = None
            current_user.profile_photo_updated_at = utc_now()
            db.session.commit()
            flash("Profil fotoğrafınız kaldırıldı.", "success")
            return redirect(redirect_target)

        photo = request.files.get("profile_photo")
        if not photo or not getattr(photo, "filename", ""):
            flash("Lütfen bir fotoğraf seçin.", "warning")
            return redirect(redirect_target)

        _save_profile_photo(photo, current_user)
        db.session.commit()
        flash("Profil fotoğrafınız güncellendi.", "success")
        return redirect(redirect_target)

    except Exception as exc:
        db.session.rollback()
        flash(f"Profil fotoğrafı güncellenirken hata oluştu: {exc}", "danger")
        return redirect(redirect_target)


def account_security_setup():
    if request.method == "POST":
        question = (request.form.get("security_question") or "").strip()
        answer = (request.form.get("security_answer") or "").strip()
        if not question or not answer:
            flash("Gizli soru ve cevap zorunludur.", "warning")
            return safe_render(
                "account_security_setup.html",
                "<h3>Gizli soru</h3>",
                security_questions=SECURITY_QUESTION_CHOICES,
            )
        current_user.security_question = question
        current_user.set_security_answer(answer)
        current_user.must_set_security_question = False
        db.session.commit()
        if getattr(current_user, "must_change_password", False):
            flash("Şimdi şifrenizi değiştirmeniz gerekiyor.", "warning")
            return redirect(url_for("main.account_change_password"))
        flash("Gizli soru kaydedildi.", "success")
        return redirect(url_for("main.account"))

    return safe_render(
        "account_security_setup.html",
        "<h3>Gizli soru</h3>",
        security_questions=SECURITY_QUESTION_CHOICES,
    )


def account_change_password():
    force_password_change = bool(getattr(current_user, "must_change_password", False))
    password_min_length = 8

    if request.method == "POST":
        current_password = (request.form.get("current_password") or "").strip()
        new_password = (request.form.get("new_password") or "").strip()
        new_password_repeat = (request.form.get("new_password_repeat") or "").strip()

        if not current_user.check_password(current_password):
            flash("Mevcut şifre yanlış.", "danger")
            return safe_render(
                "account_change_password.html",
                "<h3>Şifre değiştir</h3>",
                force_password_change=force_password_change,
                password_min_length=password_min_length,
            )

        if len(new_password) < password_min_length:
            flash(f"Yeni şifre en az {password_min_length} karakter olmalıdır.", "warning")
            return safe_render(
                "account_change_password.html",
                "<h3>Şifre değiştir</h3>",
                force_password_change=force_password_change,
                password_min_length=password_min_length,
            )

        if new_password != new_password_repeat:
            flash("Yeni şifreler eşleşmiyor.", "warning")
            return safe_render(
                "account_change_password.html",
                "<h3>Şifre değiştir</h3>",
                force_password_change=force_password_change,
                password_min_length=password_min_length,
            )

        if current_user.check_password(new_password):
            flash("Yeni şifre mevcut şifre ile aynı olamaz.", "warning")
            return safe_render(
                "account_change_password.html",
                "<h3>Şifre değiştir</h3>",
                force_password_change=force_password_change,
                password_min_length=password_min_length,
            )

        current_user.set_password(new_password)
        current_user.must_change_password = False
        current_user.is_first_login = False
        db.session.commit()

        flash("Şifreniz güncellendi.", "success")
        return redirect(url_for("main.account"))

    return safe_render(
        "account_change_password.html",
        "<h3>Şifre değiştir</h3>",
        force_password_change=force_password_change,
        password_min_length=password_min_length,
    )


__all__ = [
    "account",
    "settings_page",
    "enforce_first_login_security_flow",
    "account_change_photo",
    "account_security_setup",
    "account_change_password",
]
