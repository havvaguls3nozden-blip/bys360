from __future__ import annotations

from typing import Any


def apply_runtime_policy_blocks(ns: dict[str, Any], *, logging: Any) -> None:
    """Apply effective_menu runtime policy blocks to caller globals.

    This module keeps app.services.settings.effective_menu as a small facade while
    preserving the original import-time policy mutation order. The caller passes
    its globals() mapping as ns.
    """
    CORE_MENU_VISIBILITY_POLICY = ns["CORE_MENU_VISIBILITY_POLICY"]
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = ns["ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS"]
    PHASE3_PERFORMANCE_MENU_POLICY = ns.get("PHASE3_PERFORMANCE_MENU_POLICY")
    PHASE3_2_PERFORMANCE_MENU_POLICY = ns.get("PHASE3_2_PERFORMANCE_MENU_POLICY")
    PHASE3_2_MANAGER_VISIBLE_KEYS = ns.get("PHASE3_2_MANAGER_VISIBLE_KEYS")
    PHASE3_2_GENERAL_VISIBLE_KEYS = ns.get("PHASE3_2_GENERAL_VISIBLE_KEYS")
    PERFORMANCE_ROLE_MATRIX_KEYS = ns.get("PERFORMANCE_ROLE_MATRIX_KEYS")

    # BYS360_SETTINGS_MANUAL_V1_EFFECTIVE_MENU_BEGIN
    # Phase4J V36C effective_menu BYS360 constants facade imports
    from app.services.settings.effective_menu_parts.bys360_constants import (  # noqa: F401, I001 - some names kept for parity; semantic fault-injection scenarios in tests/services/test_settings_campaign2_wave3_phase4dv.py target these by object identity, not source line
        _BYS360_AG5E_AI_TEACHING_MENU_KEY,
        _BYS360_AG5E_AI_TEACHING_ROLES,
        _BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS,
        _BYS360_ALL_MENU_ROLE_MATRIX_POLICY,
        _BYS360_ASSISTANT_TAB_AUTHORITY_KEYS,
        _BYS360_ASSISTANT_TAB_POLICY,
        _BYS360_EXEC_ADMIN_ONLY_ROLES,
        _BYS360_EXEC_KNOWN_KEYS,
        _BYS360_EXEC_URL_MARKERS,
        _BYS360_GENERAL_CATEGORY_CHILD_KEYS_V1,
        _BYS360_GENERAL_CATEGORY_SECTION_KEYS_V1,
        _BYS360_GENERAL_CORE_KEYS_V4,
        _BYS360_MANUAL_POLICY,
        _BYS360_MANUAL_ROLE_MENU_ADDITIONS,
        _BYS360_PERFORMANCE_ALL_KEYS,
        _BYS360_PERFORMANCE_CHILD_KEYS,
        _BYS360_PERFORMANCE_CHILD_KEYS_V4,
        _BYS360_PERFORMANCE_GENERAL_SHORTCUT_KEYS_V4,
        _BYS360_PERFORMANCE_MAIN_KEYS,
        _BYS360_PERFORMANCE_MAIN_KEYS_V4,
        _BYS360_PERFORMANCE_MAIN_SWITCH_POLICY,
        _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY,
        _BYS360_PERF_RM_V8_ALIAS_GROUPS,
        _BYS360_PERF_RM_V8_ALL_AUTH_ROLES,
        _BYS360_PERF_RM_V8_ALL_KEYS,
        _BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS,
        _BYS360_PERF_RM_V8_CHILD_KEYS,
        _BYS360_PERF_RM_V8_MAIN_KEYS,
        _BYS360_PERF_RM_V8_MANAGER_ROLES,
        _BYS360_PERF_RM_V8_ROLE_POLICY,
        _BYS360_PERIOD_CENTER_DEFAULT_ROLES_V221,
        _BYS360_PERIOD_CENTER_MENU_KEY_V221,
        _BYS360_PERSONEL_ALLOWED_POLICY,
        _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS,
        _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS,
        _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_MANAGER_ROLES,
        _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS,
        _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES,
        _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS,
        _BYS360_PROCESS_MENU_KEYS,
        _BYS360_PROCESS_MENU_ROLES,
        _BYS360_REMINDERS_ALLOWED_ROLES,
        _BYS360_REMINDERS_MENU_KEY,
        _BYS360_ROLE_MATRIX_V12_AUTHORITY_KEYS,
        _BYS360_ROLE_MATRIX_V12_POLICY,
        _BYS360_V223_PERIOD_CENTER_KEY_ROLES,
    )


    _apply_manual_role_menu_policy(ns, _BYS360_MANUAL_ROLE_MENU_ADDITIONS, _BYS360_MANUAL_POLICY)
    # BYS360_SETTINGS_MANUAL_V1_EFFECTIVE_MENU_END

    # BYS360_SETTINGS_MANUAL_V1_1_REMINDERS_POLICY_BEGIN

    # Phase4J V50C effective_menu reminders menu block facade call
    from app.services.settings.effective_menu_parts.block_context import (
        apply_reminders_menu_policy_block,
    )
    apply_reminders_menu_policy_block(
        ns,
        _BYS360_REMINDERS_MENU_KEY,
        _BYS360_REMINDERS_ALLOWED_ROLES,
    )

    # Phase4J V56C effective_menu reminders key sets block facade call
    from app.services.settings.effective_menu_parts.block_context import (
        apply_reminders_menu_key_sets_block,
    )
    apply_reminders_menu_key_sets_block(
        ns,
        _BYS360_REMINDERS_MENU_KEY,
    )
    # BYS360_SETTINGS_MANUAL_V1_1_REMINDERS_POLICY_END

    # BYS360_PROCESS_TRACKING_REPORTS_EFFECTIVE_MENU_V1_BEGIN

    # Phase4J V49C effective_menu process menu block facade call
    from app.services.settings.effective_menu_parts.block_context import (
        apply_process_menu_policy_block,
    )
    apply_process_menu_policy_block(
        ns,
        _BYS360_PROCESS_MENU_KEYS,
        _BYS360_PROCESS_MENU_ROLES,
    )

    _apply_process_menu_authority_keys(ns, _BYS360_PROCESS_MENU_KEYS)
    # BYS360_PROCESS_TRACKING_REPORTS_EFFECTIVE_MENU_V1_END

    # BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TABS_V1_EFFECTIVE_MENU_BEGIN

    # Phase4J V48C effective_menu performance role matrix new tab block facade call
    from app.services.settings.effective_menu_parts.block_context import (
        apply_performance_role_matrix_new_tab_policy_block,
    )
    apply_performance_role_matrix_new_tab_policy_block(
        ns,
        _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY,
    )

    # Phase4J V53C effective_menu new tab sets block facade call
    from app.services.settings.effective_menu_parts.block_context import (
        apply_performance_role_matrix_new_tab_sets_block,
    )
    apply_performance_role_matrix_new_tab_sets_block(
        ns,
        _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY,
    )
    # BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TABS_V1_EFFECTIVE_MENU_END


    # BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_EFFECTIVE_MENU_BEGIN
    # Modül Bazlı Rol Matrislerinde kapatılan yeni Yardım Merkezi, BYS360 Asistanı V9 ve performans satırları runtime'da da kapalı kalır.
    _apply_role_matrix_v12_block(ns, ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, _BYS360_ROLE_MATRIX_V12_AUTHORITY_KEYS, _BYS360_ROLE_MATRIX_V12_POLICY)
    # BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_EFFECTIVE_MENU_END
    # BYS360_AY1_AI_PERFORMANCE_SETTINGS_INTEGRATION_V1_BEGIN
    # Rol Matrisi kapattığında BYS360 Asistanı ve yeni performans sekmeleri runtime'da kapalı kalır.
    # Phase4J V46C effective_menu role matrix authority keys block facade call
    from app.services.settings.effective_menu_parts.block_context import (
        apply_role_matrix_runtime_authority_keys_block,
    )
    apply_role_matrix_runtime_authority_keys_block(ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS)

    _apply_ay1_ai_performance_core_visibility_fallback(CORE_MENU_VISIBILITY_POLICY)
    # BYS360_AY1_AI_PERFORMANCE_SETTINGS_INTEGRATION_V1_END

    # BYS360_AG5E_AI_TEACHING_EFFECTIVE_MENU_START
    _apply_ag5e_ai_teaching_block(ns, ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, CORE_MENU_VISIBILITY_POLICY, _BYS360_AG5E_AI_TEACHING_MENU_KEY, _BYS360_AG5E_AI_TEACHING_ROLES)
    # BYS360_AG5E_AI_TEACHING_EFFECTIVE_MENU_END


    # BYS360_PERSONEL_LIVE_SCOPE_NARROW_V1_EFFECTIVE_MENU_BEGIN
    # Personel Yönetimi rol matrisi canlı kapsamı daraltıldı.
    # Rol matrisinde canlı tutulacak tek personel alt operasyon anahtarı: hr_leave_tracking.
    # Phase4J V54C effective_menu personel policy block facade call
    from app.services.settings.effective_menu_parts.block_context import (
        apply_personel_allowed_policy_block,
    )
    apply_personel_allowed_policy_block(
        ns,
        _BYS360_PERSONEL_ALLOWED_POLICY,
        _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS,
    )
    _apply_personel_live_scope_authority_keys(ns, _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS, _BYS360_PERSONEL_ALLOWED_POLICY)
    # BYS360_PERSONEL_LIVE_SCOPE_NARROW_V1_EFFECTIVE_MENU_END

    # BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_EFFECTIVE_MENU_BEGIN
    # Ayarlar rol matrisi kaydı canlı menü kararına yansısın diye güncel personel anahtarları runtime yetki katmanına eklenir.
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = _apply_personel_current_scope_authority(
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, CORE_MENU_VISIBILITY_POLICY,
        _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS, _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_MANAGER_ROLES,
    )
    # BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_EFFECTIVE_MENU_END

    # BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_BEGIN
    # Rol matrisi son karar katmanı: yeni eklenen tüm canlı sekmeler rol matrisi tarafından kapatılınca kapalı kalır;
    # rol matrisinden açılınca sidebar görünürlüğüne dahil olur.
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = _apply_all_menu_role_matrix_block(
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, ns, _BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS, _BYS360_ALL_MENU_ROLE_MATRIX_POLICY,
    )
    # BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_END

    # BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_BEGIN
    # BYS360 Asistanı gerçek sekmeleri rol matrisi runtime son karar katmanına eklendi.
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = _apply_assistant_tab_role_matrix_block(
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, CORE_MENU_VISIBILITY_POLICY, ns, _BYS360_ASSISTANT_TAB_AUTHORITY_KEYS, _BYS360_ASSISTANT_TAB_POLICY,
    )
    # BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_END

    # BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_BEGIN
    # Performans Yönetimi ana anahtarı runtime son karar katmanı.
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = _apply_performance_main_switch_role_matrix_block(
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, ns, _BYS360_PERFORMANCE_ALL_KEYS, _BYS360_PERFORMANCE_MAIN_SWITCH_POLICY,
    )
    # BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_END

    # BYS360_GENERAL_SECTION_RESTORE_V4_BEGIN
    # Genel bölüm, Performans Yönetimi ana anahtarından bağımsızdır.
    # Performans ana anahtarı yalnızca performans bölümü ve performans kısayollarını kapatır.
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = _apply_general_section_restore_v4_authority(
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, _BYS360_GENERAL_CORE_KEYS_V4, _BYS360_PERFORMANCE_MAIN_KEYS_V4, _BYS360_PERFORMANCE_CHILD_KEYS_V4,
    )
    # BYS360_GENERAL_SECTION_RESTORE_V4_END

    # BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_EFFECTIVE_MENU_BEGIN
    # Personel Yönetimi rol matrisi runtime son karar düzeltmesi.
    # Rol matrisinde seçili Personel sekmeleri sol şeritte görünür; kapalı olanlar gizli kalır.
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = _apply_personel_v7_authority_and_core_fallback(
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, CORE_MENU_VISIBILITY_POLICY,
        _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS, _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES, _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS,
    )
    # Phase4J V55C effective_menu personel role matrix visibility v7 block facade call
    from app.services.settings.effective_menu_parts.block_context import (
        apply_personel_role_matrix_visibility_v7_block,
    )
    apply_personel_role_matrix_visibility_v7_block(
        ns,
        _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS,
        _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES,
        _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS,
    )
    _apply_personel_v7_constant_narrowing(
        _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS, _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS, _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS,
    )
    # BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_EFFECTIVE_MENU_END

    # BYS360_PERFORMANCE_ROLE_MATRIX_PERSONNEL_V8_BEGIN
    # Rol matrisi düzeltmesi: Performans Yönetimi ana anahtarı ile alt sekme tikleri çakıştığında
    # seçili alt sekme menüde görünür; ana anahtar alt sekmelerden otomatik türetilir.
    # Ayrıca eski alias anahtarları canonical sol menü anahtarlarıyla eşitlenir.
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = _apply_perf_rm_v8_personnel_block(
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, CORE_MENU_VISIBILITY_POLICY, ns, _BYS360_PERF_RM_V8_ALL_KEYS, _BYS360_PERF_RM_V8_ROLE_POLICY,
    )
    # BYS360_PERFORMANCE_ROLE_MATRIX_PERSONNEL_V8_END


    # BYS360_PERSON_BASED_ROLE_MATRIX_V1_BEGIN
    # Personel bazlı rol matrisi nihai görünürlük katmanı.
    # Amaç: Unvan/rol varsayılanı ana politika olarak kalsın; ancak kurum içi
    # istisnalar kişi bazlı, audit log'lu ve kontrollü biçimde yönetilebilsin.
    # Bu blok mevcut UserMenuPermission tablosunu kullanır; şema değiştirmez.





    # BYS360_PERSON_BASED_ROLE_MATRIX_V1_END

    # BYS360_PERSONNEL_FEATURE_MATRIX_V1_4_FINAL_USER_OVERRIDE_RUNTIME

    # BYS360_GENERAL_CATEGORY_VISIBILITY_FIX_V1_BEGIN
    # Genel kategorisi icin son karar duzeltmesi.
    # Sorun: Rol matrisinde Genel alt sekmeleri acik olsa bile eski DB kaydi
    # general_section=false kaldiginda sol menude Genel basligi tamamen gizlenebiliyordu.
    # Kural: Genel altinda acik en az bir canli sekme varsa kategori basligi gorunur.







    # BYS360_GENERAL_CATEGORY_VISIBILITY_FIX_V1_END

    # BYS360_HOME_MENU_ALWAYS_VISIBLE_V1_BEGIN
    # Anasayfa ve çekirdek kullanıcı bağlantıları her kullanıcı için güvenli giriş kapısıdır.
    # Kişi/rol bazlı menü ayarları alt özellikleri kapatabilir; ancak Anasayfa kaybolmaz.

    # BYS360_HOME_MENU_ALWAYS_VISIBLE_V1_END

    # BYS360_CORPORATE_PORTAL_V1_EFFECTIVE_MENU_POLICY
    PORTAL_MENU_VISIBILITY_POLICY = _apply_corporate_portal_policy(CORE_MENU_VISIBILITY_POLICY, ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS)


    # /BYS360_CORPORATE_PORTAL_V1_EFFECTIVE_MENU_POLICY

    # BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_EFFECTIVE_MENU_BEGIN
    # Portal rol matrisi, önceki force-visible davranışından sonra son karar olarak tekrar uygulanır.
    PORTAL_ROLE_MATRIX_V2_12_KEYS, PORTAL_ROLE_MATRIX_V2_12_DEFAULTS = _apply_portal_role_matrix_v2_12_policy(ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS)




    # BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_EFFECTIVE_MENU_END


    # BYS360_DAILY_WEATHER_MAIL_EXEC_EFFECTIVE_MENU_V1_0_7_BEGIN
    # Phase4J V44C effective_menu daily weather policy block facade call
    from app.services.settings.effective_menu_parts.block_context import (
        apply_daily_weather_policy_block,
    )
    apply_daily_weather_policy_block(ns, logging=logging)
    # BYS360_DAILY_WEATHER_MAIL_EXEC_EFFECTIVE_MENU_V1_0_7_END

    # BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK_BEGIN
    # Yönetici Özeti modülü ve alt sekmeleri yalnızca Sistem Yöneticisi / teknik admin rollerinde görünür.
    # Bu son katman, rol matrisi/kişi bazlı eski açık kayıtlar veya önceki force-visible blokları tarafından ezilmesin diye
    # build_menu_visibility_map fonksiyonunun çıktısını en sonda temizler.








    # BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK_END


    for _name, _value in list(locals().items()):
        if _name.startswith("_BYS360_") or _name in {
            "CORE_MENU_VISIBILITY_POLICY",
            "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
            "PORTAL_MENU_VISIBILITY_POLICY",
            "PORTAL_ROLE_MATRIX_V2_12_KEYS",
            "PORTAL_ROLE_MATRIX_V2_12_DEFAULTS",
        }:
            ns[_name] = _value


def _apply_manual_role_menu_policy(
    ns: dict[str, Any],
    _BYS360_MANUAL_ROLE_MENU_ADDITIONS: dict[str, list[str]],
    _BYS360_MANUAL_POLICY: dict[str, set[str]],
) -> None:
    """BYS360_SETTINGS_MANUAL_V1_EFFECTIVE_MENU block, lifted verbatim."""
    for _role, _keys in _BYS360_MANUAL_ROLE_MENU_ADDITIONS.items():
        for _key in _keys:
            _BYS360_MANUAL_POLICY.setdefault(_key, set()).add(_role)

    for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY"]:
        _policy = ns.get(_policy_name)
        if isinstance(_policy, dict):
            for _key, _roles in _BYS360_MANUAL_POLICY.items():
                _current = _policy.setdefault(_key, set())
                if isinstance(_current, set):
                    _current.update(_roles)
                elif isinstance(_current, list):
                    _current.extend([_r for _r in _roles if _r not in _current])

    for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS"]:
        _target = ns.get(_set_name)
        if isinstance(_target, set):
            _target.update(_BYS360_MANUAL_POLICY.keys())
        elif isinstance(_target, list):
            _target.extend([_k for _k in _BYS360_MANUAL_POLICY if _k not in _target])


def _apply_process_menu_authority_keys(
    ns: dict[str, Any],
    _BYS360_PROCESS_MENU_KEYS: list[str],
) -> None:
    """BYS360_PROCESS_TRACKING_REPORTS_EFFECTIVE_MENU_V1 authority-keys tail, lifted verbatim."""
    for _set_name in [
        "PHASE3_2_MANAGER_VISIBLE_KEYS",
        "PHASE3_2_GENERAL_VISIBLE_KEYS",
        "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
    ]:
        _target = ns.get(_set_name)
        if isinstance(_target, set):
            _target.update(_BYS360_PROCESS_MENU_KEYS)
        elif isinstance(_target, list):
            _target.extend([_k for _k in _BYS360_PROCESS_MENU_KEYS if _k not in _target])


def _apply_ay1_ai_performance_core_visibility_fallback(
    CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]],
) -> None:
    """BYS360_AY1_AI_PERFORMANCE_SETTINGS_INTEGRATION_V1 CORE_MENU_VISIBILITY_POLICY
    portion, lifted verbatim. Catch-and-log only, no reassignment -- partial-apply
    risk (a mid-sequence setdefault failure leaves earlier setdefaults already
    applied) is preserved exactly as before."""
    try:
        CORE_MENU_VISIBILITY_POLICY.setdefault("ai_agent_panel", {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"})
        CORE_MENU_VISIBILITY_POLICY.setdefault("performance_president_approvals", {"admin", "baskan"})
        CORE_MENU_VISIBILITY_POLICY.setdefault("performance_personnel_support_publish_approval", {"admin", "grup_baskani"})
        CORE_MENU_VISIBILITY_POLICY.setdefault("performance_process_tracking", {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"})
        CORE_MENU_VISIBILITY_POLICY.setdefault("performance_process_reports", {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"})
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:831)")


def _apply_personel_live_scope_authority_keys(
    ns: dict[str, Any],
    _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS: set[str],
    _BYS360_PERSONEL_ALLOWED_POLICY: dict[str, set[str]],
) -> None:
    """BYS360_PERSONEL_LIVE_SCOPE_NARROW_V1 authority/visibility-set tail,
    lifted verbatim. Block 8 of the Block 8/9->14 order contract: reads
    _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS at its pre-mutation value -- must
    run before Block 14 mutates that same constant."""
    for _set_name in ["ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
        _target = ns.get(_set_name)
        if isinstance(_target, set):
            _target.difference_update(_BYS360_PERSONEL_DISALLOWED_POLICY_KEYS)
            _target.update(_BYS360_PERSONEL_ALLOWED_POLICY.keys())
        elif isinstance(_target, list):
            _target[:] = [_key for _key in _target if _key not in _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS]
            _target.extend([_key for _key in _BYS360_PERSONEL_ALLOWED_POLICY if _key not in _target])


def _apply_role_matrix_v12_block(
    ns: dict[str, Any],
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
    _BYS360_ROLE_MATRIX_V12_AUTHORITY_KEYS: set[str],
    _BYS360_ROLE_MATRIX_V12_POLICY: dict[str, set[str]],
) -> None:
    """BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_EFFECTIVE_MENU block, lifted
    verbatim. Catch-and-log only; no reassignment fallback for this block."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_ROLE_MATRIX_V12_AUTHORITY_KEYS)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/settings/effective_menu.py")
    for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY"]:
        _policy = ns.get(_policy_name)
        if isinstance(_policy, dict):
            for _key, _roles in _BYS360_ROLE_MATRIX_V12_POLICY.items():
                _current = _policy.setdefault(_key, set())
                if isinstance(_current, set):
                    _current.update(_roles)
                elif isinstance(_current, list):
                    _current.extend([_role for _role in _roles if _role not in _current])


def _apply_ag5e_ai_teaching_block(
    ns: dict[str, Any],
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
    CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]],
    _BYS360_AG5E_AI_TEACHING_MENU_KEY: str,
    _BYS360_AG5E_AI_TEACHING_ROLES: set[str],
) -> None:
    """BYS360_AG5E_AI_TEACHING_EFFECTIVE_MENU block, lifted verbatim. The
    guarded .add() (try/except) and the later unguarded .add() inside the
    closing set-loop both target the same key -- this redundancy is
    intentional/pre-existing (see test_runtime_authority_ag5e_add_redundant_unguarded_readd)
    and must not be de-duplicated."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.add(_BYS360_AG5E_AI_TEACHING_MENU_KEY)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:840)")
    try:
        CORE_MENU_VISIBILITY_POLICY.setdefault(_BYS360_AG5E_AI_TEACHING_MENU_KEY, set()).update(_BYS360_AG5E_AI_TEACHING_ROLES)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:844)")
    for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
        _policy = ns.get(_policy_name)
        if isinstance(_policy, dict):
            _current = _policy.setdefault(_BYS360_AG5E_AI_TEACHING_MENU_KEY, set())
            if isinstance(_current, set):
                _current.update(_BYS360_AG5E_AI_TEACHING_ROLES)
            elif isinstance(_current, list):
                _current.extend([_role for _role in _BYS360_AG5E_AI_TEACHING_ROLES if _role not in _current])
    for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
        _target = ns.get(_set_name)
        if isinstance(_target, set):
            _target.add(_BYS360_AG5E_AI_TEACHING_MENU_KEY)
        elif isinstance(_target, list) and _BYS360_AG5E_AI_TEACHING_MENU_KEY not in _target:
            _target.append(_BYS360_AG5E_AI_TEACHING_MENU_KEY)


def _apply_corporate_portal_policy(
    CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]],
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
) -> dict[str, set[str]]:
    """BYS360_CORPORATE_PORTAL_V1_EFFECTIVE_MENU_POLICY block, lifted verbatim.
    Returns PORTAL_MENU_VISIBILITY_POLICY so the caller can rebind its own
    local of that name -- required for the final ns sync loop's explicit
    allowlist to pick it up. CORE_MENU_VISIBILITY_POLICY.update(...) here is a
    wholesale per-key value REPLACE, not the setdefault+union merge every
    other block uses -- preserved exactly, not normalized to merge semantics."""
    PORTAL_MENU_VISIBILITY_POLICY = {
        "portal_feed": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
        "portal_profiles": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
        "portal_groups": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
        "portal_moderation": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"},
    }
    CORE_MENU_VISIBILITY_POLICY.update(PORTAL_MENU_VISIBILITY_POLICY)
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(PORTAL_MENU_VISIBILITY_POLICY.keys())
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        pass
    return PORTAL_MENU_VISIBILITY_POLICY


def _apply_portal_role_matrix_v2_12_policy(
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
) -> tuple[set[str], dict[str, set[str]]]:
    """BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_EFFECTIVE_MENU block, lifted
    verbatim. Returns (PORTAL_ROLE_MATRIX_V2_12_KEYS, PORTAL_ROLE_MATRIX_V2_12_DEFAULTS)
    so the caller can rebind its own locals of those names -- required for the
    final ns sync loop's explicit allowlist to pick them up."""
    PORTAL_ROLE_MATRIX_V2_12_KEYS = {
        "portal_feed", "portal_people", "portal_profiles", "portal_post_create", "portal_wall_post",
        "portal_post_interact", "portal_post_report", "portal_post_delete", "portal_groups",
        "portal_group_create", "portal_moderation",
    }
    PORTAL_ROLE_MATRIX_V2_12_DEFAULTS = {
        "admin": PORTAL_ROLE_MATRIX_V2_12_KEYS,
        "baskan": PORTAL_ROLE_MATRIX_V2_12_KEYS,
        "baskan_yardimcisi": PORTAL_ROLE_MATRIX_V2_12_KEYS,
        "grup_baskani": PORTAL_ROLE_MATRIX_V2_12_KEYS,
        "mali_musavir": PORTAL_ROLE_MATRIX_V2_12_KEYS,
        "koordinator": PORTAL_ROLE_MATRIX_V2_12_KEYS - {"portal_moderation"},
        "birim_sorumlusu": PORTAL_ROLE_MATRIX_V2_12_KEYS - {"portal_moderation"},
        "personel": PORTAL_ROLE_MATRIX_V2_12_KEYS - {"portal_group_create", "portal_moderation"},
    }
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(PORTAL_ROLE_MATRIX_V2_12_KEYS)
    except Exception:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("BYS360 effective menu isleminde hata yakalandi")
        __import__("logging").getLogger(__name__).exception("BYS360 portal rol matrisi authority anahtarları eklenemedi")
    return PORTAL_ROLE_MATRIX_V2_12_KEYS, PORTAL_ROLE_MATRIX_V2_12_DEFAULTS


def _apply_personel_current_scope_authority(
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
    CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]],
    _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS: set[str],
    _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_MANAGER_ROLES: set[str],
) -> set[str]:
    """BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_EFFECTIVE_MENU block,
    lifted verbatim. Block 9 of the Block 8/9->14 order contract: reads
    _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS at its pre-mutation
    value -- must run before Block 14 mutates that same constant. On
    failure, rebinds to a brand-new set object; returns it so the caller can
    rethread the (possibly new) object into subsequent blocks, since a
    callee cannot rebind a caller's local variable through a parameter."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS)
    except Exception:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=943")
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS)
    try:
        for _key in _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS:
            CORE_MENU_VISIBILITY_POLICY.setdefault(_key, set()).update(_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_MANAGER_ROLES)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:918)")
    return ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS


def _apply_all_menu_role_matrix_block(
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
    ns: dict[str, Any],
    _BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS: set[str],
    _BYS360_ALL_MENU_ROLE_MATRIX_POLICY: dict[str, set[str]],
) -> set[str]:
    """BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1 block, lifted verbatim.
    The closing set-loop deliberately reads ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS
    back out of ns (not the parameter above) -- this preserves a pre-existing
    staleness quirk: ns["ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS"] is never resynced
    until the function's final sync-to-ns loop, so if an earlier block's
    fallback already rebound the local variable, this loop still mutates the
    older, pre-rebind object. Changing this to read the parameter instead
    would be a silent behavior change."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS)
    except Exception:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=1017")
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS)

    for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
        _policy = ns.get(_policy_name)
        if isinstance(_policy, dict):
            for _key, _roles in _BYS360_ALL_MENU_ROLE_MATRIX_POLICY.items():
                _current = _policy.setdefault(_key, set())
                if isinstance(_current, set):
                    _current.update(_roles)
                elif isinstance(_current, list):
                    _current.extend([_role for _role in _roles if _role not in _current])

    for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
        _target = ns.get(_set_name)
        if isinstance(_target, set):
            _target.update(_BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS)
        elif isinstance(_target, list):
            _target.extend([_key for _key in _BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS if _key not in _target])
    return ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS


def _apply_assistant_tab_role_matrix_block(
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
    CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]],
    ns: dict[str, Any],
    _BYS360_ASSISTANT_TAB_AUTHORITY_KEYS: set[str],
    _BYS360_ASSISTANT_TAB_POLICY: dict[str, set[str]],
) -> set[str]:
    """BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2 block, lifted verbatim."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_ASSISTANT_TAB_AUTHORITY_KEYS)
    except Exception:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=1050")
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_ASSISTANT_TAB_AUTHORITY_KEYS)
    try:
        for _key, _roles in _BYS360_ASSISTANT_TAB_POLICY.items():
            CORE_MENU_VISIBILITY_POLICY.setdefault(_key, set()).update(_roles)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:1025)")
    for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
        _policy = ns.get(_policy_name)
        if isinstance(_policy, dict):
            for _key, _roles in _BYS360_ASSISTANT_TAB_POLICY.items():
                _current = _policy.setdefault(_key, set())
                if isinstance(_current, set):
                    _current.update(_roles)
                elif isinstance(_current, list):
                    _current.extend([_role for _role in _roles if _role not in _current])
    return ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS


def _apply_performance_main_switch_role_matrix_block(
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
    ns: dict[str, Any],
    _BYS360_PERFORMANCE_ALL_KEYS: set[str],
    _BYS360_PERFORMANCE_MAIN_SWITCH_POLICY: dict[str, set[str]],
) -> set[str]:
    """BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3 block, lifted verbatim.
    Same ns-vs-parameter staleness note as _apply_all_menu_role_matrix_block
    applies to the closing set-loop below."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_PERFORMANCE_ALL_KEYS)
    except Exception:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=1117")
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_PERFORMANCE_ALL_KEYS)
    for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
        _policy = ns.get(_policy_name)
        if isinstance(_policy, dict):
            for _key, _roles in _BYS360_PERFORMANCE_MAIN_SWITCH_POLICY.items():
                _current = _policy.setdefault(_key, set())
                if isinstance(_current, set):
                    _current.update(_roles)
                elif isinstance(_current, list):
                    _current.extend([_role for _role in _roles if _role not in _current])
    for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
        _target = ns.get(_set_name)
        if isinstance(_target, set):
            _target.update(_BYS360_PERFORMANCE_ALL_KEYS)
        elif isinstance(_target, list):
            _target.extend([_key for _key in _BYS360_PERFORMANCE_ALL_KEYS if _key not in _target])
    return ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS


def _apply_general_section_restore_v4_authority(
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
    _BYS360_GENERAL_CORE_KEYS_V4: set[str],
    _BYS360_PERFORMANCE_MAIN_KEYS_V4: set[str],
    _BYS360_PERFORMANCE_CHILD_KEYS_V4: set[str],
) -> set[str]:
    """BYS360_GENERAL_SECTION_RESTORE_V4 block, lifted verbatim."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_GENERAL_CORE_KEYS_V4 | _BYS360_PERFORMANCE_MAIN_KEYS_V4 | _BYS360_PERFORMANCE_CHILD_KEYS_V4)
    except Exception:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=1178")
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_GENERAL_CORE_KEYS_V4 | _BYS360_PERFORMANCE_MAIN_KEYS_V4 | _BYS360_PERFORMANCE_CHILD_KEYS_V4)
    return ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS


def _apply_personel_v7_authority_and_core_fallback(
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
    CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]],
    _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS: set[str],
    _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES: set[str],
    _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS: set[str],
) -> set[str]:
    """BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7 block's RMRAK/CMVP portion
    (pre-delegate-call), lifted verbatim. This is the landing site of the
    Block 8/9->14 order contract, but this specific helper only covers the
    RMRAK/CMVP sub-steps -- the existing delegate call
    (apply_personel_role_matrix_visibility_v7_block) and the constant-mutation
    sub-step (see _apply_personel_v7_constant_narrowing) remain separate,
    sequential steps in the orchestrator, in the exact same order as before."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS)
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.difference_update(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS)
    except Exception:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=1230")
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS)
    try:
        for _key in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS:
            CORE_MENU_VISIBILITY_POLICY.setdefault(_key, set()).update(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES)
        for _key in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS:
            CORE_MENU_VISIBILITY_POLICY.pop(_key, None)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:1205)")
    return ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS


def _apply_personel_v7_constant_narrowing(
    _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS: set[str],
    _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS: set[str],
    _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS: set[str],
) -> None:
    """BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7 block's constant-mutation
    sub-step, lifted verbatim. This is Block 14 of the Block 8/9->14 order
    contract: mutates the same two module-level constants that Blocks 8 and 9
    read at their pre-mutation values, so it must run after those reads (see
    test_personel_scope_block8_9_run_before_v7_block14_mutates_constants).
    Single try/except with two statements: if the first raises, the second
    never executes -- this partial-apply behavior is preserved exactly
    (see test_runtime_constant_mutation_fallback_semantic)."""
    try:
        _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS.difference_update({"hr_management", "hr_reports"})
        _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS.update(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:1221)")


def _apply_perf_rm_v8_personnel_block(
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str],
    CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]],
    ns: dict[str, Any],
    _BYS360_PERF_RM_V8_ALL_KEYS: set[str],
    _BYS360_PERF_RM_V8_ROLE_POLICY: dict[str, set[str]],
) -> set[str]:
    """BYS360_PERFORMANCE_ROLE_MATRIX_PERSONNEL_V8 block, lifted verbatim.
    Last of the 7 RMRAK reassignment sites; same ns-vs-parameter staleness
    note applies to the closing set-loop below."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_PERF_RM_V8_ALL_KEYS)
    except Exception:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=1388")
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_PERF_RM_V8_ALL_KEYS)
    try:
        for _key, _roles in _BYS360_PERF_RM_V8_ROLE_POLICY.items():
            CORE_MENU_VISIBILITY_POLICY.setdefault(_key, set()).update(_roles)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:1361)")
    for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
        _policy = ns.get(_policy_name)
        if isinstance(_policy, dict):
            for _key, _roles in _BYS360_PERF_RM_V8_ROLE_POLICY.items():
                _current = _policy.setdefault(_key, set())
                if isinstance(_current, set):
                    _current.update(_roles)
                elif isinstance(_current, list):
                    _current.extend([_role for _role in _roles if _role not in _current])
    for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
        _target = ns.get(_set_name)
        if isinstance(_target, set):
            _target.update(_BYS360_PERF_RM_V8_ALL_KEYS)
        elif isinstance(_target, list):
            _target.extend([_key for _key in _BYS360_PERF_RM_V8_ALL_KEYS if _key not in _target])
    return ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS
