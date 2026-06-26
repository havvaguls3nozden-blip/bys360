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
# Phase4J V38C effective_menu ROLE constants facade imports
from app.services.settings.effective_menu_parts.role_constants import (
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS,
)



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
# Phase4J V37C effective_menu PHASE3 constants facade imports
from app.services.settings.effective_menu_parts.phase3_constants import (
    PHASE3_2_GENERAL_VISIBLE_KEYS,
    PHASE3_2_MANAGER_VISIBLE_KEYS,
    PHASE3_2_MENU_VISIBILITY_MARKER,
    PHASE3_2_PERFORMANCE_MENU_POLICY,
    PHASE3_2_PERSONNEL_VISIBLE_KEYS,
    PHASE3_PERFORMANCE_MENU_POLICY,
)





# BYS360_PHASE3_2_MENU_VISIBILITY_BEGIN
# Faz 3.2 — Performans menü görünürlüğü son güvenlik katmanı.
# Menüde görünmemesi gereken kullanıcı, ilgili performans menüsünü hiç görmez.
# Backend veri kilidi Faz 3.3 içinde ayrıca uygulanacaktır.








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

# Phase4J V39C2 effective_menu build core alias-aware facade import
from app.services.settings.effective_menu_parts.build_context import (
    build_menu_visibility_map as _BYS360_BUILD_MENU_VISIBILITY_MAP_CORE_V39C2,
)

# Phase4J V39D: expose split core under original name during legacy wrapper registration
build_menu_visibility_map = _BYS360_BUILD_MENU_VISIBILITY_MAP_CORE_V39C2


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
# Phase4J V44C effective_menu daily weather policy block facade call
from app.services.settings.effective_menu_parts.block_context import (
    apply_daily_weather_policy_block,
)
apply_daily_weather_policy_block(globals(), logging=logging)
# BYS360_DAILY_WEATHER_MAIL_EXEC_EFFECTIVE_MENU_V1_0_7_END

# BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK_BEGIN
# Yönetici Özeti modülü ve alt sekmeleri yalnızca Sistem Yöneticisi / teknik admin rollerinde görünür.
# Bu son katman, rol matrisi/kişi bazlı eski açık kayıtlar veya önceki force-visible blokları tarafından ezilmesin diye
# build_menu_visibility_map fonksiyonunun çıktısını en sonda temizler.








# BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK_END

# BYS360_PERFORMANCE_V2_1_3C_EFFECTIVE_MENU_FORCE_BEGIN
# Personel Kategori Atama sekmesi base.html'de sabit Jinja ile render edilir.
# Bu son karar katmanı, admin/sistem yöneticisi rolünde ilgili menu_map anahtarını açık tutar.
# Phase4J V40C effective_menu V213C wrapper block facade call
from app.services.settings.effective_menu_parts.build_wrapper_context import (
    apply_v213c_category_menu_wrapper,
)
build_menu_visibility_map = apply_v213c_category_menu_wrapper(
    build_menu_visibility_map,
    logging=logging,
    normalize_role_name=normalize_role_name,
    is_removed_menu_key=is_removed_menu_key,
)
# BYS360_PERFORMANCE_V2_1_3C_EFFECTIVE_MENU_FORCE_END

# BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_EFFECTIVE_MENU_BEGIN
# Phase4J V43C effective_menu V214 final wrapper block facade call
from app.services.settings.effective_menu_parts.build_wrapper_context import (
    apply_v214_category_scope_wrapper,
)
build_menu_visibility_map = apply_v214_category_scope_wrapper(
    build_menu_visibility_map,
    logging=logging,
    normalize_role_name=normalize_role_name,
    is_removed_menu_key=is_removed_menu_key,
)
# BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_EFFECTIVE_MENU_END

# BYS360_PERFORMANCE_V2_1_5_CATEGORY_PERIOD_SCOPE_EFFECTIVE_MENU_BEGIN
# Phase4J V41C effective_menu V215 wrapper block facade call
from app.services.settings.effective_menu_parts.build_wrapper_context import (
    apply_v215_category_period_scope_wrapper,
)
build_menu_visibility_map = apply_v215_category_period_scope_wrapper(
    build_menu_visibility_map,
    logging=logging,
    normalize_role_name=normalize_role_name,
    is_removed_menu_key=is_removed_menu_key,
)
# BYS360_PERFORMANCE_V2_1_5_CATEGORY_PERIOD_SCOPE_EFFECTIVE_MENU_END

# BYS360_PERFORMANCE_V2_1_6_CATEGORY_PERIOD_INTEGRATION_EFFECTIVE_MENU_BEGIN
# Phase4J V42C effective_menu V216 wrapper block facade call
from app.services.settings.effective_menu_parts.build_wrapper_context import (
    apply_v216_category_period_integration_wrapper,
)
build_menu_visibility_map = apply_v216_category_period_integration_wrapper(
    build_menu_visibility_map,
    logging=logging,
    normalize_role_name=normalize_role_name,
    is_removed_menu_key=is_removed_menu_key,
)
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
