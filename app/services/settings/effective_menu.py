from __future__ import annotations



# BYS360_SCORE10_F821_PERIOD_CENTER_IMPORT_V3
try:
    from app.services.settings.effective_menu_parts.bys360_constants import (
        _BYS360_PERIOD_CENTER_DEFAULT_ROLES_V221,
        _BYS360_PERIOD_CENTER_MENU_KEY_V221,
        _BYS360_V223_PERIOD_CENTER_KEY_ROLES,
    )
except Exception:
    _BYS360_PERIOD_CENTER_MENU_KEY_V221 = "performance_period_center"
    _BYS360_PERIOD_CENTER_DEFAULT_ROLES_V221 = {
        "admin",
        "sistem_yoneticisi",
        "baskan",
        "baskan_yardimcisi",
        "grup_baskani",
    }
    _BYS360_V223_PERIOD_CENTER_KEY_ROLES = {
        _BYS360_PERIOD_CENTER_MENU_KEY_V221: set(_BYS360_PERIOD_CENTER_DEFAULT_ROLES_V221)
    }
from app.services.settings.effective_menu_parts.bys360_constants import (
    _BYS360_PERIOD_CENTER_DEFAULT_ROLES_V221,
    _BYS360_PERIOD_CENTER_MENU_KEY_V221,
    _BYS360_V223_PERIOD_CENTER_KEY_ROLES,
)
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

# Phase4J V47C effective_menu core policy constant facade import
from app.services.settings.effective_menu_parts.core_policy_constants import (
    CORE_MENU_VISIBILITY_POLICY,
)


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

# Phase4J V45C effective_menu user assigned survey function facade import
from app.services.settings.effective_menu_parts.user_context import (
    _user_has_any_assigned_survey,
)



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


# Phase4J EFFECTIVE_MENU_FACADE_V1 runtime policy blocks
from app.services.settings.effective_menu_parts.runtime_policy_context import (
    apply_runtime_policy_blocks,
)

apply_runtime_policy_blocks(globals(), logging=logging)

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
# Phase4J V51C effective_menu period center block facade call
from app.services.settings.effective_menu_parts.block_context import (
    apply_period_center_key_roles_block,
)
apply_period_center_key_roles_block(
    CORE_MENU_VISIBILITY_POLICY,
    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS,
    _BYS360_V223_PERIOD_CENTER_KEY_ROLES,
    logging,
)
# BYS360_PERFORMANCE_V2_1_23_SETTINGS_ROLE_MATRIX_FULL_AUTHORITY_END


# BYS360_A5_P2D4_LIVE_SCOPE_PORTAL_PREFIX_ANCHOR_START
# Static contract anchor: /portal
# Portal prefix canl? kapsam/karantina s?zle?mesinde a??k?a izlenir.
# BYS360_A5_P2D4_LIVE_SCOPE_PORTAL_PREFIX_ANCHOR_END


# BYS360_ADMIN_PERIOD_REMINDER_ACCESS_FIX_V1_BEGIN
# Admin/Sistem Yöneticisi için Dönem Yönetim Merkezi ve Amir Hatırlatma Merkezi
# rol matrisi veya kişi bazlı eski kapalı kayıtlar yüzünden gizlenmesin.
_BYS360_PREV_BUILD_MENU_VISIBILITY_MAP_ADMIN_PERIOD_REMINDER_V1 = build_menu_visibility_map



# Phase4J V52C effective_menu public build function facade assignment
from app.services.settings.effective_menu_parts.public_build_context import (
    apply_admin_period_reminder_public_build_wrapper,
)
build_menu_visibility_map = apply_admin_period_reminder_public_build_wrapper(
    _BYS360_PREV_BUILD_MENU_VISIBILITY_MAP_ADMIN_PERIOD_REMINDER_V1,
    _bys360_admin_period_reminder_is_admin_v1,
)
# BYS360_ADMIN_PERIOD_REMINDER_ACCESS_FIX_V1_END


