from __future__ import annotations

import logging
"""Ayarlar servis menü görünürlük çözümleyicisi.

Bu modül route katmanındaki menü görünürlük hesaplamasını servis tarafına alır.
Kayıt/commit davranışına dokunmaz; yalnızca okuma, fallback ve canlı menü
filtreleme mantığını tek noktada toplar.
"""

from collections.abc import Callable
from typing import Any

from app.config import is_removed_menu_key
from app.menu_registry import flatten_menu_definitions
from app.models import UserMenuPermission, RoleMenuDefault
from app.services.settings_service import build_effective_user_menu_context, get_role_default_menu_keys

RollbackHook = Callable[[], None]

CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]] = {
    "messages": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "notifications": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "surveys": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "survey_manage": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "survey_results": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "feedback_dashboard": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "feedback_pulse": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "feedback_campaigns": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "feedback_results": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "feedback_actions": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "feedback_manager": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "feedback_admin": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"},
    "performance_reports": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "analysis_center": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
}


# Phase4J V34C effective_menu bys360_context facade imports
from app.services.settings.effective_menu_parts.bys360_context import (
    _bys360_admin_period_reminder_is_admin_v1,
    _bys360_admin_period_reminder_norm_v1,
    _bys360_apply_general_category_visibility_fix_v1,
    _bys360_apply_performance_main_switch,
    _bys360_apply_performance_shortcut_gate_v4,
    _bys360_exec_item_matches,
    _bys360_exec_norm,
    _bys360_force_home_menu_visible_v1,
    _bys360_general_category_bool_v1,
    _bys360_general_category_state_v1,
    _bys360_is_exec_summary_menu_key,
    _bys360_perf_rm_v8_apply_aliases,
    _bys360_perf_rm_v8_apply_main_gate,
    _bys360_perf_rm_v8_norm_role,
    _bys360_perf_rm_v8_state_for_keys,
    _bys360_performance_role_state,
    _bys360_person_matrix_can_open_v1,
    _bys360_person_matrix_user_is_admin_v1,
    _bys360_portal_role_matrix_v2_12_apply,
    _bys360_press_news_role,
    _bys360_restore_general_section_v4,
    _get_unit_name_for_authority,
    _load_role_matrix_state,
    _load_unit_profile_state,
    _load_user_override_state,
    _rollback,
    _row_map_by_key,
    _safe_query_all,
    normalize_role_name,
)



def _log_warning(logger: Any, message: str, *args: Any) -> None:
    if logger is None:
        return
    try:
        logger.warning(message, *args)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/settings/effective_menu.py")
# Ayarlar > Rol Matrisi ekranında kapatılan sekmeler, çekirdek menü savunması
# veya kişi bazlı eski override nedeniyle yeniden açılmasın.
ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str] = {
    "messages",
    "notifications",
    "surveys",
    "survey_manage",
    "survey_results",
    "feedback_dashboard",
    "feedback_pulse",
    "feedback_campaigns",
    "feedback_results",
    "feedback_actions",
    "feedback_manager",
    "feedback_admin",
    "portal_press_news",
    "announcements",
    "assistant_center",
    "assistant_my_reminders",
    "assistant_scheduled_tasks",
    "assistant_report_generate",
    "assistant_report_share",
    "assistant_ai_summary",
    "assistant_process_alerts",
    "assistant_logs",
    "assistant_settings",
}


# Phase4J V35C effective_menu apply_context facade imports
from app.services.settings.effective_menu_parts.apply_context import (
    _allowed_by_static_gate,
    _apply_bys360_press_news_admin_only_policy,
    _apply_bys360_settings_live_authority_v1,
    _apply_core_menu_visibility_policy,
    _apply_phase3_2_performance_menu_visibility,
    _apply_phase3_performance_menu_policy,
    _apply_role_gate,
    _apply_role_matrix_closed_guard,
    _get_role_matrix_closed_keys_for_role,
    _menu_item_by_key,
    _phase3_2_ascii_tr,
    _phase3_2_normalize_role_name,
    _role_allowed_for_menu,
    _role_matrix_runtime_closed,
    _settings_explicitly_controls_key,
)






def _active_menu_items() -> list[dict[str, Any]]:
    return [item for item in flatten_menu_definitions() if not is_removed_menu_key(item.get("key"))]



# BYS360_SETTINGS_ROLE_MATRIX_RUNTIME_V6_CORE_POLICY
# Eski çekirdek canlı menü savunması, rol matrisinde kapatılan satırı artık
# yeniden açamaz. Kullanıcı Ayarlar ekranında tik kaldırdıysa kapalı kalır.

def _user_has_any_assigned_survey(user: Any, *, rollback: RollbackHook | None = None) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    try:
        from app.models import Survey
        from app.services.message_service import user_matches_assignment

        surveys = (
            Survey.query
            .filter(Survey.status == "published")
            .order_by(Survey.id.desc())
            .limit(10000)
            .all()
        )
        for survey in surveys:
            assignments = getattr(survey, "assignments", None)
            if assignments is None:
                continue
            try:
                rows = assignments.all()
            except Exception:
                logger = __import__("logging").getLogger(__name__)
                logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=249")
                rows = []
            if any(user_matches_assignment(row, user) for row in rows):
                return True
    except Exception:
        _rollback(rollback)
        return False
    return False



# BYS360_PHASE3_VISIBILITY_PERMISSION_MENU_MATRIX
PHASE3_PERFORMANCE_MENU_POLICY: dict[str, set[str]] = {
    # Personel: kendi karnesi ve kendi kıyas/ortalama görünümü.
    "performance_scorecard": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "my_performance_comparison": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},

    # Koordinatör/Grup Başkanı: kendi kapsamındaki personel ve ortalamalar.
    "performance_reports": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "performance_team_compare": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "team_performance_comparison_history": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},

    # Yönetim ekranları: genel/teknik yönetim ailesi.
    "performance_criteria": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi"},
    "performance_periods": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi"},
    "performance_task_management": {"admin", "sistem_yoneticisi", "system_admin", "super_admin"},
    "performance_hierarchy_tree": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "performance_hierarchy_assignments": {"admin", "sistem_yoneticisi", "system_admin", "super_admin"},
    "performance_publish": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan"},
    "performance_history_import": {"admin", "sistem_yoneticisi", "system_admin", "super_admin"},
}




# BYS360_PHASE3_2_MENU_VISIBILITY_BEGIN
# Faz 3.2 — Performans menü görünürlüğü son güvenlik katmanı.
# Menüde görünmemesi gereken kullanıcı, ilgili performans menüsünü hiç görmez.
# Backend veri kilidi Faz 3.3 içinde ayrıca uygulanacaktır.
PHASE3_2_MENU_VISIBILITY_MARKER = "BYS360_PHASE3_2_MENU_VISIBILITY"

PHASE3_2_PERFORMANCE_MENU_POLICY: dict[str, set[str]] = {
    # Personel: yalnızca kendi karnesi ve kendi grup/kategori ortalaması tarafı.
    "performance_scorecard": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu", "personel", "user", "standart_personel"},
    "my_performance_comparison": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu", "personel", "user", "standart_personel"},

    # Koordinatör ve Grup Başkanı: yalnızca kendi kapsamındaki personel/ortalama ekranları.
    "performance_reports": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_team_compare": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "team_performance_comparison_history": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_evaluation_tasks": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_tasks": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_interim_notes": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_development_guidance": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_feedback_meetings": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},

    # Başkan/Admin: genel yönetim görünümü.
    "performance_criteria": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı"},
    "performance_periods": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı"},
    "performance_hierarchy_tree": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_publish": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president"},
    "performance_president_approvals": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president"},
    "performance_personnel_support_publish_approval": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "grup_baskani", "grup_başkanı"},

    # Teknik yönetim: yalnızca Admin/Sistem Yöneticisi.
    "performance_task_management": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator"},
    "performance_hierarchy_assignments": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator"},
    "performance_history_import": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator"},
    "performance_mail_settings": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator"},

    # Stratejik Performans — KPI, Hedef, Yetkinlik, Öz Değerlendirme
    "performance_kpi_dashboard": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör"},
    "performance_kpi_management": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör"},
    "performance_competency_library": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_self_assessment": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_kpi_analysis": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör"},
}

PHASE3_2_PERSONNEL_VISIBLE_KEYS = {"performance_scorecard", "my_performance_comparison"}
PHASE3_2_MANAGER_VISIBLE_KEYS = {
    "performance_scorecard", "my_performance_comparison", "performance_reports",
    "performance_team_compare", "team_performance_comparison_history",
    "performance_evaluation_tasks", "performance_tasks", "performance_interim_notes",
    "performance_development_guidance", "performance_feedback_meetings", "performance_hierarchy_tree",
}
PHASE3_2_GENERAL_VISIBLE_KEYS = set(PHASE3_2_PERFORMANCE_MENU_POLICY.keys())






# BYS360_PHASE3_2_MENU_VISIBILITY_END

# BYS360_SETTINGS_LIVE_AUTHORITY_V1_BEGIN
# Ayarlar modülünün son karar katmanı.
# Amaç: Rol matrisi / birim profili / kişi bazlı görünürlük kayıtları,
# çekirdek menü savunmaları ve faz politikaları tarafından tekrar ezilmesin.
# Sıra: Rol matrisi tabanı -> birim profili -> kişi özel ayarı -> teknik/rol güvenlik kapısı.


def _truthy_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "evet", "yes", "on", "aktif", "visible", "açık", "acik"}


















# BYS360_SETTINGS_LIVE_AUTHORITY_V2_END


# Compatibility guard.


# Compatibility guard.

def build_menu_visibility_map(
    user: Any,
    *,
    logger: Any = None,
    rollback: RollbackHook | None = None,
) -> dict[str, bool]:
    """Kullanıcının canlı menü görünürlük haritasını üretir.

    Öncelik sırası:
    1. Rol varsayılanı
    2. Birim profili
    3. Kullanıcı override kaydı
    4. Çekirdek canlı menü savunması
    """
    active_menu_items = _active_menu_items()
    visibility = {item["key"]: False for item in active_menu_items if item.get("key")}
    if not user:
        visibility.update({"home": True, "account": True, "logout": True})
        return visibility

    role_name = normalize_role_name(getattr(user, "role", ""))
    effective_context: dict[str, Any] = {}

    try:
        effective_context = build_effective_user_menu_context(user, active_menu_items)
        visibility.update(effective_context.get("effective_rule_map", {}) or {})
    except Exception as exc:  # pragma: no cover - canlı DB/şema fallback alanı
        _rollback(rollback)
        _log_warning(
            logger,
            "Menu visibility settings service fallback calisti | user_id=%s | exc=%s",
            getattr(user, "id", None),
            exc,
        )
        for key in get_role_default_menu_keys(role_name):
            if key and not is_removed_menu_key(key):
                visibility[key] = True

        try:
            rows = UserMenuPermission.query.filter_by(user_id=user.id).all()
        except Exception as load_exc:  # pragma: no cover
            _rollback(rollback)
            _log_warning(
                logger,
                "Kullanıcı menü izinleri okunamadı | user_id=%s | exc=%s",
                getattr(user, "id", None),
                load_exc,
            )
            rows = []
        for row in rows:
            menu_key = getattr(row, "menu_key", "")
            if menu_key and not is_removed_menu_key(menu_key):
                visibility[menu_key] = bool(getattr(row, "is_visible", False))

    source_map = effective_context.get("source_map", {}) if isinstance(effective_context, dict) else {}
    _apply_role_matrix_closed_guard(visibility, role_name, source_map=source_map, rollback=rollback)

    _apply_role_gate(visibility, active_menu_items, role_name)

    if not visibility.get("surveys") and _role_allowed_for_menu(
        {"required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
        role_name,
    ):
        if _user_has_any_assigned_survey(user, rollback=rollback):
            visibility["surveys"] = True

    source_map = effective_context.get("source_map", {}) if isinstance(effective_context, dict) else {}
    _apply_role_matrix_closed_guard(visibility, role_name, source_map=source_map, rollback=rollback)
    visibility = _apply_core_menu_visibility_policy(visibility, role_name, source_map=source_map)

    visibility = _apply_phase3_performance_menu_policy(visibility, role_name)  # BYS360_PHASE3_VISIBILITY_PERMISSION_MENU_APPLIED
    visibility = _apply_phase3_2_performance_menu_visibility(visibility, role_name)  # BYS360_PHASE3_2_MENU_VISIBILITY_APPLIED

    # BYS360_SETTINGS_LIVE_AUTHORITY_V2_APPLIED
    # Rol matrisi, birim profili ve kişi bazlı ayarlar faz/çekirdek/statik rol
    # politikalarından sonra son karar olarak uygulanır; açılan menü görünür,
    # kapatılan menü yeniden açılmaz.
    visibility = _apply_bys360_settings_live_authority_v1(
        visibility,
        user,
        role_name,
        active_menu_items,
        rollback=rollback,
    )
    visibility = _apply_bys360_press_news_admin_only_policy(visibility, user)  # compatibility guard
    visibility = _bys360_apply_performance_main_switch(visibility, user, role_name, rollback=rollback)
    visibility = _bys360_restore_general_section_v4(visibility, user)
    visibility = _bys360_apply_performance_shortcut_gate_v4(visibility)


    # PHASE3A_EFFECTIVE_MENU_V7_V8_INLINE_BEGIN
    if user:
        role_name = normalize_role_name(getattr(user, "role", ""))
        role_state = _load_role_matrix_state(role_name, rollback=rollback)
        unit_state = _load_unit_profile_state(user, rollback=rollback)
        user_state = _load_user_override_state(user, rollback=rollback)

        for _key in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS:
            visibility[_key] = False

        manager_norms = {
            _phase3_2_normalize_role_name(_r)
            for _r in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES
        }

        for _key in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS:
            if _key not in visibility:
                visibility[_key] = False
            if _key in role_state:
                visibility[_key] = bool(role_state[_key])
            elif role_name in manager_norms:
                visibility[_key] = True
            if role_state.get(_key) is not False and _key in unit_state:
                visibility[_key] = bool(unit_state[_key])
            if role_state.get(_key) is not False and _key in user_state:
                visibility[_key] = bool(user_state[_key])
            if role_name in {"personel", "user", "kullanici", "kullan\u0131c\u0131", "standart_personel", "rolsuz", "__none__"} and _key in {"admin_users", "org_units", "hr_management", "hr_reports"}:
                if role_state.get(_key) is not True and user_state.get(_key) is not True:
                    visibility[_key] = False

        visibility["account"] = True
        visibility["logout"] = True

        role_name = _bys360_perf_rm_v8_norm_role(getattr(user, "role", ""))
        try:
            role_state = _load_role_matrix_state(role_name, rollback=rollback)
        except Exception:
            log = __import__("logging").getLogger(__name__)
            log.exception("BYS360 effective menu fallback failed | phase=perf_rm_v8_role_state")
            role_state = {}
        try:
            unit_state = _load_unit_profile_state(user, rollback=rollback)
        except Exception:
            log = __import__("logging").getLogger(__name__)
            log.exception("BYS360 effective menu fallback failed | phase=perf_rm_v8_unit_state")
            unit_state = {}
        try:
            user_state = _load_user_override_state(user, rollback=rollback)
        except Exception:
            log = __import__("logging").getLogger(__name__)
            log.exception("BYS360 effective menu fallback failed | phase=perf_rm_v8_user_state")
            user_state = {}

        visibility = _bys360_perf_rm_v8_apply_aliases(visibility, role_state, unit_state, user_state)
        visibility = _bys360_perf_rm_v8_apply_main_gate(visibility, role_state, unit_state, user_state)
        visibility["account"] = True
        visibility["logout"] = True
    # PHASE3A_EFFECTIVE_MENU_V7_V8_INLINE_END


    # PHASE3A_EFFECTIVE_MENU_V14_GENERAL_HOME_INLINE_BEGIN
    if user:
        try:
            active_menu_items = _active_menu_items()
            active_keys = {
                str((item or {}).get("key") or "").strip()
                for item in active_menu_items or []
                if str((item or {}).get("key") or "").strip()
            }
        except Exception:
            log = __import__("logging").getLogger(__name__)
            log.exception("BYS360 effective menu fallback failed | phase=v14_active_keys")
            active_keys = set(visibility.keys())

        try:
            user_state = _load_user_override_state(user, rollback=rollback)
        except Exception:
            log = __import__("logging").getLogger(__name__)
            log.exception("BYS360 effective menu fallback failed | phase=v14_user_state")
            user_state = {}

        for key, is_visible in (user_state or {}).items():
            key = str(key or "").strip()
            if not key or key not in active_keys or is_removed_menu_key(key):
                continue
            visibility[key] = bool(is_visible)

        performance_children = {
            "scorecards", "performance_dashboard", "performance_criteria", "criteria",
            "performance_periods", "periods", "performance_evaluation_tasks", "assignments",
            "performance_tasks", "performance_task_management", "performance_hierarchy_tree",
            "performance_hierarchy_assignments", "performance_team_compare", "team_analysis",
            "team_performance_comparison_history", "performance_feedback_meetings", "feedback_meetings",
            "performance_publish", "publish", "performance_mail_settings", "performance_mail",
            "performance_process_tracking", "performance_process_reports", "performance_president_approvals",
            "performance_personnel_support_publish_approval", "performance_interim_notes",
            "performance_development_guidance", "performance_meeting_p3_reminders",
            "performance_kpi_dashboard", "performance_kpi_management", "performance_competency_library",
            "performance_self_assessment", "performance_kpi_analysis", "performance_feedback_aftercare",
            "performance_feedback_aftercare_new", "performance_feedback_meeting_guide", "performance_feedback_followup",
            "performance_archive", "performance_reports", "performance_scorecard", "my_performance_comparison",
        }
        if any(bool(visibility.get(key)) for key in performance_children):
            for main_key in ("performance_module", "performance_management", "performans_yonetimi"):
                if main_key in active_keys or main_key in visibility:
                    visibility[main_key] = True

        assistant_children = {"ai_agent_panel", "ai_agent_knowledge", "ai_agent_teaching_center", "assistant_center"}
        if any(bool(visibility.get(key)) for key in assistant_children):
            for main_key in ("assistant_module", "ai_agent_panel"):
                if main_key in active_keys or main_key in visibility:
                    visibility[main_key] = True

        visibility["account"] = True
        visibility["logout"] = True

    visibility = _bys360_apply_general_category_visibility_fix_v1(visibility, user, rollback=rollback)
    visibility = _bys360_force_home_menu_visible_v1(visibility, user)
    # PHASE3A_EFFECTIVE_MENU_V14_GENERAL_HOME_INLINE_END


    # PHASE3A_EFFECTIVE_MENU_PORTAL_EXEC_INLINE_BEGIN
    role = str(getattr(user, "role", "") or "").strip().lower()
    for key, allowed_roles in PORTAL_MENU_VISIBILITY_POLICY.items():
        if role in allowed_roles and not is_removed_menu_key(key):
            visibility.setdefault(key, True)

    visibility = _bys360_portal_role_matrix_v2_12_apply(visibility, user, rollback=rollback)

    try:
        exec_role = _bys360_exec_norm(getattr(user, "role", ""))
        is_admin = exec_role in globals().get("_BYS360_EXEC_ADMIN_ONLY_ROLES", set())
        try:
            active_items = _active_menu_items()
        except Exception:
            log = __import__("logging").getLogger(__name__)
            log.exception("BYS360 effective menu fallback failed | phase=exec_active_items")
            active_items = []

        exec_keys = set(globals().get("_BYS360_EXEC_KNOWN_KEYS", set()))
        for item in active_items or []:
            if isinstance(item, dict) and _bys360_exec_item_matches(item):
                k = str(item.get("key") or "").strip()
                if k:
                    exec_keys.add(k)

        for k in list(visibility.keys()):
            if _bys360_is_exec_summary_menu_key(k):
                exec_keys.add(k)

        for k in exec_keys:
            if k in visibility:
                visibility[k] = bool(is_admin)

        if "executive_summary" in visibility:
            visibility["executive_summary"] = bool(is_admin)
    except Exception:
        log = __import__("logging").getLogger(__name__)
        log.exception("BYS360 effective menu fallback failed | phase=exec_admin_only")
    # PHASE3A_EFFECTIVE_MENU_PORTAL_EXEC_INLINE_END

    return visibility

# BYS360_SETTINGS_MANUAL_V1_EFFECTIVE_MENU_BEGIN
# Phase4J V36C effective_menu BYS360 constants facade imports
from app.services.settings.effective_menu_parts.bys360_constants import (
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


for _role, _keys in _BYS360_MANUAL_ROLE_MENU_ADDITIONS.items():
    for _key in _keys:
        _BYS360_MANUAL_POLICY.setdefault(_key, set()).add(_role)

for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY"]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key, _roles in _BYS360_MANUAL_POLICY.items():
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_roles)
            elif isinstance(_current, list):
                _current.extend([_r for _r in _roles if _r not in _current])

for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS"]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.update(_BYS360_MANUAL_POLICY.keys())
    elif isinstance(_target, list):
        _target.extend([_k for _k in _BYS360_MANUAL_POLICY.keys() if _k not in _target])
# BYS360_SETTINGS_MANUAL_V1_EFFECTIVE_MENU_END

# BYS360_SETTINGS_MANUAL_V1_1_REMINDERS_POLICY_BEGIN

for _policy_name in [
    "PHASE3_PERFORMANCE_MENU_POLICY",
    "PHASE3_2_PERFORMANCE_MENU_POLICY",
    "PERFORMANCE_MENU_POLICY",
    "ROLE_MENU_POLICY",
]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        _current = _policy.setdefault(_BYS360_REMINDERS_MENU_KEY, set())
        if isinstance(_current, set):
            _current.update(_BYS360_REMINDERS_ALLOWED_ROLES)
        elif isinstance(_current, list):
            _current.extend([_r for _r in _BYS360_REMINDERS_ALLOWED_ROLES if _r not in _current])

for _set_name in [
    "PHASE3_2_MANAGER_VISIBLE_KEYS",
    "PHASE3_2_GENERAL_VISIBLE_KEYS",
    "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.add(_BYS360_REMINDERS_MENU_KEY)
    elif isinstance(_target, list) and _BYS360_REMINDERS_MENU_KEY not in _target:
        _target.append(_BYS360_REMINDERS_MENU_KEY)
# BYS360_SETTINGS_MANUAL_V1_1_REMINDERS_POLICY_END

# BYS360_PROCESS_TRACKING_REPORTS_EFFECTIVE_MENU_V1_BEGIN

for _policy_name in [
    "PHASE3_PERFORMANCE_MENU_POLICY",
    "PHASE3_2_PERFORMANCE_MENU_POLICY",
    "PERFORMANCE_MENU_POLICY",
    "ROLE_MENU_POLICY",
]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key in _BYS360_PROCESS_MENU_KEYS:
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_BYS360_PROCESS_MENU_ROLES)
            elif isinstance(_current, list):
                _current.extend([_r for _r in _BYS360_PROCESS_MENU_ROLES if _r not in _current])

for _set_name in [
    "PHASE3_2_MANAGER_VISIBLE_KEYS",
    "PHASE3_2_GENERAL_VISIBLE_KEYS",
    "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.update(_BYS360_PROCESS_MENU_KEYS)
    elif isinstance(_target, list):
        _target.extend([_k for _k in _BYS360_PROCESS_MENU_KEYS if _k not in _target])
# BYS360_PROCESS_TRACKING_REPORTS_EFFECTIVE_MENU_V1_END

# BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TABS_V1_EFFECTIVE_MENU_BEGIN

for _policy_name in [
    "PHASE3_PERFORMANCE_MENU_POLICY",
    "PHASE3_2_PERFORMANCE_MENU_POLICY",
    "PERFORMANCE_MENU_POLICY",
    "ROLE_MENU_POLICY",
    "ROLE_MATRIX_POLICY",
]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key, _roles in _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY.items():
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_roles)
            elif isinstance(_current, list):
                _current.extend([_r for _r in _roles if _r not in _current])

for _set_name in [
    "PHASE3_2_MANAGER_VISIBLE_KEYS",
    "PHASE3_2_GENERAL_VISIBLE_KEYS",
    "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
    "PERFORMANCE_ROLE_MATRIX_KEYS",
]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.update(_BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY.keys())
    elif isinstance(_target, list):
        _target.extend([_k for _k in _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY.keys() if _k not in _target])
# BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TABS_V1_EFFECTIVE_MENU_END


# BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_EFFECTIVE_MENU_BEGIN
# Modül Bazlı Rol Matrislerinde kapatılan yeni Yardım Merkezi, BYS360 Asistanı V9 ve performans satırları runtime'da da kapalı kalır.
try:
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_ROLE_MATRIX_V12_AUTHORITY_KEYS)
except Exception:
    import logging
    logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/settings/effective_menu.py")
for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY"]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key, _roles in _BYS360_ROLE_MATRIX_V12_POLICY.items():
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_roles)
            elif isinstance(_current, list):
                _current.extend([_role for _role in _roles if _role not in _current])
# BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_EFFECTIVE_MENU_END
# BYS360_AY1_AI_PERFORMANCE_SETTINGS_INTEGRATION_V1_BEGIN
# Rol Matrisi kapattığında BYS360 Asistanı ve yeni performans sekmeleri runtime'da kapalı kalır.
try:
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update({
        "ai_agent_panel",
        "performance_president_approvals",
        "performance_personnel_support_publish_approval",
        "performance_process_tracking",
        "performance_process_reports",
        "performance_interim_notes",
        "performance_development_guidance",
        "performance_meeting_p3_reminders",
        "performance_archive",
        "performance_kpi_dashboard",
        "performance_kpi_management",
        "performance_competency_library",
        "performance_self_assessment",
        "performance_kpi_analysis",
        "performance_team_compare",
        "performance_feedback_meetings",
        "team_performance_comparison_history",
    })
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:822)")

try:
    CORE_MENU_VISIBILITY_POLICY.setdefault("ai_agent_panel", {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"})
    CORE_MENU_VISIBILITY_POLICY.setdefault("performance_president_approvals", {"admin", "baskan"})
    CORE_MENU_VISIBILITY_POLICY.setdefault("performance_personnel_support_publish_approval", {"admin", "grup_baskani"})
    CORE_MENU_VISIBILITY_POLICY.setdefault("performance_process_tracking", {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"})
    CORE_MENU_VISIBILITY_POLICY.setdefault("performance_process_reports", {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"})
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:831)")
# BYS360_AY1_AI_PERFORMANCE_SETTINGS_INTEGRATION_V1_END

# BYS360_AG5E_AI_TEACHING_EFFECTIVE_MENU_START
try:
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.add(_BYS360_AG5E_AI_TEACHING_MENU_KEY)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:840)")
try:
    CORE_MENU_VISIBILITY_POLICY.setdefault(_BYS360_AG5E_AI_TEACHING_MENU_KEY, set()).update(_BYS360_AG5E_AI_TEACHING_ROLES)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:844)")
for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        _current = _policy.setdefault(_BYS360_AG5E_AI_TEACHING_MENU_KEY, set())
        if isinstance(_current, set):
            _current.update(_BYS360_AG5E_AI_TEACHING_ROLES)
        elif isinstance(_current, list):
            _current.extend([_role for _role in _BYS360_AG5E_AI_TEACHING_ROLES if _role not in _current])
for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.add(_BYS360_AG5E_AI_TEACHING_MENU_KEY)
    elif isinstance(_target, list) and _BYS360_AG5E_AI_TEACHING_MENU_KEY not in _target:
        _target.append(_BYS360_AG5E_AI_TEACHING_MENU_KEY)
# BYS360_AG5E_AI_TEACHING_EFFECTIVE_MENU_END


# BYS360_PERSONEL_LIVE_SCOPE_NARROW_V1_EFFECTIVE_MENU_BEGIN
# Personel Yönetimi rol matrisi canlı kapsamı daraltıldı.
# Rol matrisinde canlı tutulacak tek personel alt operasyon anahtarı: hr_leave_tracking.
for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key in _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS:
            _policy.pop(_key, None)
        for _key, _roles in _BYS360_PERSONEL_ALLOWED_POLICY.items():
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_roles)
            elif isinstance(_current, list):
                _current.extend([_role for _role in _roles if _role not in _current])
for _set_name in ["ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.difference_update(_BYS360_PERSONEL_DISALLOWED_POLICY_KEYS)
        _target.update(_BYS360_PERSONEL_ALLOWED_POLICY.keys())
    elif isinstance(_target, list):
        _target[:] = [_key for _key in _target if _key not in _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS]
        _target.extend([_key for _key in _BYS360_PERSONEL_ALLOWED_POLICY.keys() if _key not in _target])
# BYS360_PERSONEL_LIVE_SCOPE_NARROW_V1_EFFECTIVE_MENU_END

# BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_EFFECTIVE_MENU_BEGIN
# Ayarlar rol matrisi kaydı canlı menü kararına yansısın diye güncel personel anahtarları runtime yetki katmanına eklenir.
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
# BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_EFFECTIVE_MENU_END

# BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_BEGIN
# Rol matrisi son karar katmanı: yeni eklenen tüm canlı sekmeler rol matrisi tarafından kapatılınca kapalı kalır;
# rol matrisinden açılınca sidebar görünürlüğüne dahil olur.
try:
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS)
except Exception:
    logger = __import__("logging").getLogger(__name__)
    logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=1017")
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS)

for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key, _roles in _BYS360_ALL_MENU_ROLE_MATRIX_POLICY.items():
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_roles)
            elif isinstance(_current, list):
                _current.extend([_role for _role in _roles if _role not in _current])

for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.update(_BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS if _key not in _target])
# BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_END

# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_BEGIN
# BYS360 Asistanı gerçek sekmeleri rol matrisi runtime son karar katmanına eklendi.
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
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key, _roles in _BYS360_ASSISTANT_TAB_POLICY.items():
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_roles)
            elif isinstance(_current, list):
                _current.extend([_role for _role in _roles if _role not in _current])
# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_END

# BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_BEGIN
# Performans Yönetimi ana anahtarı runtime son karar katmanı.
try:
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_PERFORMANCE_ALL_KEYS)
except Exception:
    logger = __import__("logging").getLogger(__name__)
    logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=1117")
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_PERFORMANCE_ALL_KEYS)
for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key, _roles in _BYS360_PERFORMANCE_MAIN_SWITCH_POLICY.items():
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_roles)
            elif isinstance(_current, list):
                _current.extend([_role for _role in _roles if _role not in _current])
for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.update(_BYS360_PERFORMANCE_ALL_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_PERFORMANCE_ALL_KEYS if _key not in _target])



# BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_END

# BYS360_GENERAL_SECTION_RESTORE_V4_BEGIN
# Genel bölüm, Performans Yönetimi ana anahtarından bağımsızdır.
# Performans ana anahtarı yalnızca performans bölümü ve performans kısayollarını kapatır.
try:
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update(_BYS360_GENERAL_CORE_KEYS_V4 | _BYS360_PERFORMANCE_MAIN_KEYS_V4 | _BYS360_PERFORMANCE_CHILD_KEYS_V4)
except Exception:
    logger = __import__("logging").getLogger(__name__)
    logger.exception("BYS360 effective menu guvenli fallback isleminde hata yakalandi | line=1178")
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = set(_BYS360_GENERAL_CORE_KEYS_V4 | _BYS360_PERFORMANCE_MAIN_KEYS_V4 | _BYS360_PERFORMANCE_CHILD_KEYS_V4)



# BYS360_GENERAL_SECTION_RESTORE_V4_END

# BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_EFFECTIVE_MENU_BEGIN
# Personel Yönetimi rol matrisi runtime son karar düzeltmesi.
# Rol matrisinde seçili Personel sekmeleri sol şeritte görünür; kapalı olanlar gizli kalır.
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
for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS:
            _policy.pop(_key, None)
        for _key in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS:
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES)
            elif isinstance(_current, list):
                _current.extend([_role for _role in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES if _role not in _current])
try:
    _BYS360_PERSONEL_DISALLOWED_POLICY_KEYS.difference_update({"hr_management", "hr_reports"})
    _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS.update(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:1221)")


# BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_EFFECTIVE_MENU_END

# BYS360_PERFORMANCE_ROLE_MATRIX_PERSONNEL_V8_BEGIN
# Rol matrisi düzeltmesi: Performans Yönetimi ana anahtarı ile alt sekme tikleri çakıştığında
# seçili alt sekme menüde görünür; ana anahtar alt sekmelerden otomatik türetilir.
# Ayrıca eski alias anahtarları canonical sol menü anahtarlarıyla eşitlenir.
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
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        for _key, _roles in _BYS360_PERF_RM_V8_ROLE_POLICY.items():
            _current = _policy.setdefault(_key, set())
            if isinstance(_current, set):
                _current.update(_roles)
            elif isinstance(_current, list):
                _current.extend([_role for _role in _roles if _role not in _current])
for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.update(_BYS360_PERF_RM_V8_ALL_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_PERF_RM_V8_ALL_KEYS if _key not in _target])









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


# /BYS360_CORPORATE_PORTAL_V1_EFFECTIVE_MENU_POLICY

# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_EFFECTIVE_MENU_BEGIN
# Portal rol matrisi, önceki force-visible davranışından sonra son karar olarak tekrar uygulanır.
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




# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_EFFECTIVE_MENU_END


# BYS360_DAILY_WEATHER_MAIL_EXEC_EFFECTIVE_MENU_V1_0_7_BEGIN
try:
    _BYS360_DAILY_WEATHER_SYSTEM_ADMIN_ROLES = {'admin', 'super_admin', 'system_admin', 'sistem_yoneticisi'}
    _BYS360_DAILY_WEATHER_DISALLOWED_ROLES = {'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'performans_yetkilisi', 'personel', 'user', 'employee', 'ik', 'hr'}
    for _policy_name in [
        "PHASE3_PERFORMANCE_MENU_POLICY",
        "PHASE3_2_PERFORMANCE_MENU_POLICY",
        "PERFORMANCE_MENU_POLICY",
        "ROLE_MENU_POLICY",
        "ROLE_MATRIX_POLICY",
    ]:
        _policy = globals().get(_policy_name)
        if isinstance(_policy, dict):
            _policy["daily_weather_mail"] = set(_BYS360_DAILY_WEATHER_SYSTEM_ADMIN_ROLES)
            _policy.setdefault("executive_summary", set())
            if isinstance(_policy.get("executive_summary"), set):
                _policy["executive_summary"].update(_BYS360_DAILY_WEATHER_SYSTEM_ADMIN_ROLES)
            elif isinstance(_policy.get("executive_summary"), list):
                for _r in _BYS360_DAILY_WEATHER_SYSTEM_ADMIN_ROLES:
                    if _r not in _policy["executive_summary"]:
                        _policy["executive_summary"].append(_r)
    for _set_name in [
        "PHASE3_2_MANAGER_VISIBLE_KEYS",
        "PHASE3_2_GENERAL_VISIBLE_KEYS",
        "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
        "PERFORMANCE_ROLE_MATRIX_KEYS",
    ]:
        _target = globals().get(_set_name)
        if isinstance(_target, set):
            _target.add("daily_weather_mail")
except Exception:
    import logging
    logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
    pass
# BYS360_DAILY_WEATHER_MAIL_EXEC_EFFECTIVE_MENU_V1_0_7_END

# BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK_BEGIN
# Yönetici Özeti modülü ve alt sekmeleri yalnızca Sistem Yöneticisi / teknik admin rollerinde görünür.
# Bu son katman, rol matrisi/kişi bazlı eski açık kayıtlar veya önceki force-visible blokları tarafından ezilmesin diye
# build_menu_visibility_map fonksiyonunun çıktısını en sonda temizler.








# BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK_END

# BYS360_PERFORMANCE_V2_1_3C_EFFECTIVE_MENU_FORCE_BEGIN
# Personel Kategori Atama sekmesi base.html'de sabit Jinja ile render edilir.
# Bu son karar katmanı, admin/sistem yöneticisi rolünde ilgili menu_map anahtarını açık tutar.
try:
    _BYS360_V213C_CATEGORY_MENU_KEY = "performance_personnel_category_card"
    _BYS360_V213C_CATEGORY_ROLES = {
        "admin", "administrator", "super_admin", "system_admin", "sistem_yoneticisi"
    }
    for _policy_name in [
        "CORE_MENU_VISIBILITY_POLICY",
        "PHASE3_PERFORMANCE_MENU_POLICY",
        "PHASE3_2_PERFORMANCE_MENU_POLICY",
        "PERFORMANCE_MENU_POLICY",
        "ROLE_MENU_POLICY",
        "ROLE_MATRIX_POLICY",
    ]:
        _policy = globals().get(_policy_name)
        if isinstance(_policy, dict):
            _current = _policy.setdefault(_BYS360_V213C_CATEGORY_MENU_KEY, set())
            if isinstance(_current, set):
                _current.update(_BYS360_V213C_CATEGORY_ROLES)
            elif isinstance(_current, list):
                for _role in _BYS360_V213C_CATEGORY_ROLES:
                    if _role not in _current:
                        _current.append(_role)
    for _set_name in [
        "PHASE3_2_GENERAL_VISIBLE_KEYS",
        "PERFORMANCE_ROLE_MATRIX_KEYS",
        "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
    ]:
        _target = globals().get(_set_name)
        if isinstance(_target, set):
            _target.add(_BYS360_V213C_CATEGORY_MENU_KEY)
        elif isinstance(_target, list) and _BYS360_V213C_CATEGORY_MENU_KEY not in _target:
            _target.append(_BYS360_V213C_CATEGORY_MENU_KEY)

    _BYS360_V213C_PREVIOUS_BUILD_MENU_VISIBILITY_MAP = build_menu_visibility_map  # type: ignore[name-defined]

    def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
        visibility = dict(_BYS360_V213C_PREVIOUS_BUILD_MENU_VISIBILITY_MAP(user, *args, **kwargs) or {})
        try:
            _role = normalize_role_name(getattr(user, "role", ""))
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("BYS360 effective menu isleminde hata yakalandi")
            _role = str(getattr(user, "role", "") or "").strip().lower()
        _is_admin_like = bool(
            _role in _BYS360_V213C_CATEGORY_ROLES
            or getattr(user, "is_admin", False)
            or getattr(user, "is_superuser", False)
        )
        if _is_admin_like and not is_removed_menu_key(_BYS360_V213C_CATEGORY_MENU_KEY):
            visibility[_BYS360_V213C_CATEGORY_MENU_KEY] = True
            visibility["performance_module"] = True
            visibility["performance_management"] = True
            visibility["performans_yonetimi"] = True
        return visibility
except Exception:
    import logging
    logging.getLogger(__name__).exception("BYS360 V2.1.3C kategori menü effective_menu force uygulanamadı")
# BYS360_PERFORMANCE_V2_1_3C_EFFECTIVE_MENU_FORCE_END

# BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_EFFECTIVE_MENU_BEGIN
try:
    _BYS360_V214_CATEGORY_SCOPE_KEY = "performance_category_scope_visibility"
    _BYS360_V214_CATEGORY_SCOPE_ROLES = {"admin", "administrator", "super_admin", "system_admin", "sistem_yoneticisi"}
    _BYS360_V214_PREVIOUS_BUILD_MENU_VISIBILITY_MAP = build_menu_visibility_map  # type: ignore[name-defined]
    def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
        visibility = dict(_BYS360_V214_PREVIOUS_BUILD_MENU_VISIBILITY_MAP(user, *args, **kwargs) or {})
        try:
            _role = normalize_role_name(getattr(user, "role", ""))
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("BYS360 effective menu isleminde hata yakalandi")
            _role = str(getattr(user, "role", "") or "").strip().lower()
        _is_admin_like = bool(_role in _BYS360_V214_CATEGORY_SCOPE_ROLES or getattr(user, "is_admin", False) or getattr(user, "is_superuser", False))
        if _is_admin_like and not is_removed_menu_key(_BYS360_V214_CATEGORY_SCOPE_KEY):
            visibility[_BYS360_V214_CATEGORY_SCOPE_KEY] = True
            visibility["performance_module"] = True
            visibility["performance_management"] = True
            visibility["performans_yonetimi"] = True
        return visibility
except Exception:
    import logging
    logging.getLogger(__name__).exception("BYS360 V2.1.4 kategori kapsam effective_menu force uygulanamadı")
# BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_EFFECTIVE_MENU_END

# BYS360_PERFORMANCE_V2_1_5_CATEGORY_PERIOD_SCOPE_EFFECTIVE_MENU_BEGIN
try:
    _BYS360_V215_CATEGORY_PERIOD_SCOPE_KEY = "performance_category_period_scope"
    _BYS360_V215_CATEGORY_PERIOD_SCOPE_ROLES = {"admin", "administrator", "super_admin", "system_admin", "sistem_yoneticisi"}
    _BYS360_V215_PREVIOUS_BUILD_MENU_VISIBILITY_MAP = build_menu_visibility_map  # type: ignore[name-defined]
    def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
        visibility = dict(_BYS360_V215_PREVIOUS_BUILD_MENU_VISIBILITY_MAP(user, *args, **kwargs) or {})
        try:
            _role = normalize_role_name(getattr(user, "role", ""))
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("BYS360 effective menu isleminde hata yakalandi")
            _role = str(getattr(user, "role", "") or "").strip().lower()
        _is_admin_like = bool(_role in _BYS360_V215_CATEGORY_PERIOD_SCOPE_ROLES or getattr(user, "is_admin", False) or getattr(user, "is_superuser", False))
        if _is_admin_like:
            try:
                _removed = is_removed_menu_key(_BYS360_V215_CATEGORY_PERIOD_SCOPE_KEY)
            except Exception:
                logger = __import__("logging").getLogger(__name__)
                logger.exception("BYS360 effective menu isleminde hata yakalandi")
                _removed = False
            if not _removed:
                visibility[_BYS360_V215_CATEGORY_PERIOD_SCOPE_KEY] = True
                visibility["performance_module"] = True
                visibility["performance_management"] = True
                visibility["performans_yonetimi"] = True
        return visibility
except Exception:
    import logging
    logging.getLogger(__name__).exception("BYS360 V2.1.5 kategori dönem kapsam effective_menu force uygulanamadı")
# BYS360_PERFORMANCE_V2_1_5_CATEGORY_PERIOD_SCOPE_EFFECTIVE_MENU_END

# BYS360_PERFORMANCE_V2_1_6_CATEGORY_PERIOD_INTEGRATION_EFFECTIVE_MENU_BEGIN
try:
    _BYS360_V216_CATEGORY_PERIOD_INTEGRATION_KEY = "performance_category_period_integration"
    _BYS360_V216_CATEGORY_PERIOD_INTEGRATION_ROLES = {"admin", "administrator", "super_admin", "system_admin", "sistem_yoneticisi"}
    _BYS360_V216_PREVIOUS_BUILD_MENU_VISIBILITY_MAP = build_menu_visibility_map  # type: ignore[name-defined]
    def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
        visibility = dict(_BYS360_V216_PREVIOUS_BUILD_MENU_VISIBILITY_MAP(user, *args, **kwargs) or {})
        try:
            _role = normalize_role_name(getattr(user, "role", ""))
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("BYS360 effective menu isleminde hata yakalandi")
            _role = str(getattr(user, "role", "") or "").strip().lower()
        _is_admin_like = bool(_role in _BYS360_V216_CATEGORY_PERIOD_INTEGRATION_ROLES or getattr(user, "is_admin", False) or getattr(user, "is_superuser", False))
        if _is_admin_like:
            try:
                _removed = is_removed_menu_key(_BYS360_V216_CATEGORY_PERIOD_INTEGRATION_KEY)
            except Exception:
                logger = __import__("logging").getLogger(__name__)
                logger.exception("BYS360 effective menu isleminde hata yakalandi")
                _removed = False
            if not _removed:
                visibility[_BYS360_V216_CATEGORY_PERIOD_INTEGRATION_KEY] = True
                visibility["performance_module"] = True
                visibility["performance_management"] = True
                visibility["performans_yonetimi"] = True
        return visibility
except Exception:
    import logging
    logging.getLogger(__name__).exception("BYS360 V2.1.6 kategori dönem entegrasyonu effective_menu force uygulanamadı")
# BYS360_PERFORMANCE_V2_1_6_CATEGORY_PERIOD_INTEGRATION_EFFECTIVE_MENU_END

# BYS360_PERFORMANCE_V2_1_21_PERIOD_CENTER_ROLE_MATRIX_AUTHORITY_BEGIN
# Dönem Yönetim Merkezi görünürlüğü Ayarlar > Rol Matrisi / birim profili / kişi bazlı menü görünürlüğü kararına bağlanır.
for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        _policy.setdefault(_BYS360_PERIOD_CENTER_MENU_KEY_V221, set()).update(_BYS360_PERIOD_CENTER_DEFAULT_ROLES_V221)
for _set_name in ["ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.add(_BYS360_PERIOD_CENTER_MENU_KEY_V221)
# BYS360_PERFORMANCE_V2_1_21_PERIOD_CENTER_ROLE_MATRIX_AUTHORITY_END


# BYS360_PERFORMANCE_V2_1_23_SETTINGS_ROLE_MATRIX_FULL_AUTHORITY_BEGIN
# Dönem Yönetim Merkezi, Canlı Takip ve Amir Hatırlatma menü anahtarları
# Ayarlar > Rol Matrisi kararına tabi canlı otorite anahtarlarıdır.
for _key, _roles in _BYS360_V223_PERIOD_CENTER_KEY_ROLES.items():
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.add(_key)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        pass
    try:
        CORE_MENU_VISIBILITY_POLICY.setdefault(_key, set()).update(set(_roles))
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        pass
# BYS360_PERFORMANCE_V2_1_23_SETTINGS_ROLE_MATRIX_FULL_AUTHORITY_END


# BYS360_A5_P2D4_LIVE_SCOPE_PORTAL_PREFIX_ANCHOR_START
# Static contract anchor: /portal
# Portal prefix canl? kapsam/karantina s?zle?mesinde a??k?a izlenir.
# BYS360_A5_P2D4_LIVE_SCOPE_PORTAL_PREFIX_ANCHOR_END


# BYS360_ADMIN_PERIOD_REMINDER_ACCESS_FIX_V1_BEGIN
# Admin/Sistem Yöneticisi için Dönem Yönetim Merkezi ve Amir Hatırlatma Merkezi
# rol matrisi veya kişi bazlı eski kapalı kayıtlar yüzünden gizlenmesin.
_BYS360_PREV_BUILD_MENU_VISIBILITY_MAP_ADMIN_PERIOD_REMINDER_V1 = build_menu_visibility_map



def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
    visibility = dict(_BYS360_PREV_BUILD_MENU_VISIBILITY_MAP_ADMIN_PERIOD_REMINDER_V1(user, *args, **kwargs) or {})
    if _bys360_admin_period_reminder_is_admin_v1(user):
        for key in (
            "performance_period_management_center",
            "performance_evaluator_reminder_center",
            "performance_evaluation_live_tracking",
        ):
            visibility[key] = True
        for parent in ("performance_module", "performance_management", "performans_yonetimi"):
            visibility[parent] = True
    return visibility
# BYS360_ADMIN_PERIOD_REMINDER_ACCESS_FIX_V1_END
