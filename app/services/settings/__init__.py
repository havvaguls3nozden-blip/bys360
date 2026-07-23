from . import menu_profile_access
from .validation_defaults import build_settings_defaults_snapshot, normalize_module_setting_definitions, normalize_system_setting_definitions, validate_settings_catalog_contract
from .value_codec import normalize_bool, value_to_python, value_to_storage
from .foundation_access import build_settings_foundation_context_handler, ensure_settings_phase1_seeded_handler, iter_live_module_setting_definitions
"""BYS360 Ayarlar servis alt paketleri."""

from .catalog import MODULE_SETTING_DEFINITIONS, SYSTEM_SETTING_DEFINITIONS
from .change_logs import (
    create_settings_change_log,
    deserialize_settings_state,
    list_recent_settings_change_logs,
    serialize_settings_state,
)
from .diagnostics import build_settings_diagnostics_context
from .effective_menu import build_menu_visibility_map
from .final_hardening import (
    assert_settings_final_hardening_contract,
    build_settings_final_hardening_report,
    get_settings_final_release_checklist,
)
from .form_pipeline import (
    save_module_settings_from_form_handler,
    save_system_settings_from_form_handler,
)
from .menu_permissions import (
    build_complete_visibility_map,
    filter_live_menu_keys,
    filter_live_menu_rows,
    snapshot_module_settings_state,
    snapshot_role_menu_state,
    snapshot_system_settings_state,
    snapshot_unit_menu_state,
    snapshot_user_override_state,
)
from .quality_gate import (
    build_settings_refactor_quality_snapshot,
    build_settings_template_guard_context,
    get_settings_refactor_phase_sequence,
)
from .rollback_handler import rollback_settings_change_handler
from .ui_panel import build_settings_ui_diagnostics_panel

__all__ = [
    "menu_profile_access",
    "validate_settings_catalog_contract",
    "normalize_system_setting_definitions",
    "normalize_module_setting_definitions",
    "build_settings_defaults_snapshot",
    "iter_live_module_setting_definitions",
    "ensure_settings_phase1_seeded_handler",
    "build_settings_foundation_context_handler",
    "value_to_storage",
    "value_to_python",
    "normalize_bool",
    "MODULE_SETTING_DEFINITIONS",
    "SYSTEM_SETTING_DEFINITIONS",
    "assert_settings_final_hardening_contract",
    "build_complete_visibility_map",
    "build_menu_visibility_map",
    "build_settings_diagnostics_context",
    "build_settings_final_hardening_report",
    "build_settings_refactor_quality_snapshot",
    "build_settings_template_guard_context",
    "build_settings_ui_diagnostics_panel",
    "create_settings_change_log",
    "deserialize_settings_state",
    "filter_live_menu_keys",
    "filter_live_menu_rows",
    "get_settings_final_release_checklist",
    "get_settings_refactor_phase_sequence",
    "list_recent_settings_change_logs",
    "rollback_settings_change_handler",
    "save_module_settings_from_form_handler",
    "save_system_settings_from_form_handler",
    "serialize_settings_state",
    "snapshot_module_settings_state",
    "snapshot_role_menu_state",
    "snapshot_system_settings_state",
    "snapshot_unit_menu_state",
    "snapshot_user_override_state",
    "MenuPermissionRule",
    "SettingDefinition",
    "SettingValue",
    "SettingsAuditFinding",
    "build_definition",
    "group_definitions",
    "index_definitions",
    "normalize_menu_key",
    "normalize_setting_key",
    "to_bool",
]

# ---------------------------------------------------------------------------
# Faz 1 public contract compatibility exports
# ---------------------------------------------------------------------------
from .contracts import (
    MenuPermissionRule,
    SettingChange,
    SettingDefinition,
    SettingValue,
    SettingsAuditFinding,
)
from .definitions import build_definition, group_definitions, index_definitions
from .serialization import (
    mask_sensitive_value,
    normalize_menu_key,
    normalize_setting_key,
    to_bool,
)


def build_change_payload(change: SettingChange) -> dict:
    """Ayar de?i?ikli?i denetim/log ??kt?s? i?in g?venli payload ?retir."""
    changed_at = getattr(change, "changed_at", None)
    return {
        "key": change.key,
        "old_value": mask_sensitive_value(change.key, change.old_value),
        "new_value": mask_sensitive_value(change.key, change.new_value),
        "actor_id": change.actor_id,
        "operation": change.operation,
        "reason": change.reason,
        "changed_at": changed_at.isoformat() if changed_at else None,
        "meta": dict(change.meta or {}),
    }


for _name in [
    "MenuPermissionRule",
    "SettingChange",
    "SettingDefinition",
    "SettingValue",
    "SettingsAuditFinding",
    "build_definition",
    "build_change_payload",
    "group_definitions",
    "index_definitions",
    "mask_sensitive_value",
    "normalize_menu_key",
    "normalize_setting_key",
    "to_bool",
]:
    if _name not in __all__:  # pragma: no branch
        __all__.append(_name)
