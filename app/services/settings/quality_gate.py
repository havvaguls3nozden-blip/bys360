
"""Ayarlar servisi final kalite kapısı yardımcıları.

Bu modül canlı ayar kaydetme, rollback veya menü görünürlük davranışını
DEĞİŞTİRMEZ. Faz 4-12 servis ayrıştırma zincirinin hangi parçalarının devrede
olduğunu yan etkisiz biçimde raporlar.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import import_module
from typing import Any


@dataclass(frozen=True)
class SettingsRefactorPhase:
    phase: str
    title: str
    status: str
    module: str


SETTINGS_REFACTOR_PHASES: tuple[SettingsRefactorPhase, ...] = (
    SettingsRefactorPhase("Faz 4", "Change log / recent history servis köprüsü", "tamamlandı", "app.services.settings.change_logs"),
    SettingsRefactorPhase("Faz 5", "Menü/rol/birim/kullanıcı izin kayıt köprüsü", "tamamlandı", "app.services.settings.menu_permissions"),
    SettingsRefactorPhase("Faz 6", "Effective menu visibility servis köprüsü", "tamamlandı", "app.services.settings.effective_menu"),
    SettingsRefactorPhase("Faz 7", "Diagnostics / health context servis köprüsü", "tamamlandı", "app.services.settings.diagnostics"),
    SettingsRefactorPhase("Faz 8", "Rollback handler servis ayrıştırması", "tamamlandı", "app.services.settings.rollback_handler"),
    SettingsRefactorPhase("Faz 9", "Form save pipeline servis ayrıştırması", "tamamlandı", "app.services.settings.form_pipeline"),
    SettingsRefactorPhase("Faz 10", "Route/template cleanup ve kapanış kalite kapısı", "tamamlandı", "app.services.settings.quality_gate"),
    SettingsRefactorPhase("Faz 11", "UI tanılama paneli entegrasyonu", "tamamlandı", "app.services.settings.ui_panel"),
    SettingsRefactorPhase("Faz 12", "Final canlı sertleştirme ve kapanış raporu", "tamamlandı", "app.services.settings.final_hardening"),
)

REQUIRED_SERVICE_SYMBOLS: dict[str, tuple[str, ...]] = {
    "app.services.settings.change_logs": (
        "create_settings_change_log",
        "list_recent_settings_change_logs",
        "serialize_settings_state",
        "deserialize_settings_state",
    ),
    "app.services.settings.menu_permissions": (
        "filter_live_menu_keys",
        "snapshot_role_menu_state",
        "snapshot_unit_menu_state",
        "snapshot_user_override_state",
        "build_complete_visibility_map",
    ),
    "app.services.settings.effective_menu": (
        "build_menu_visibility_map",
        "CORE_MENU_VISIBILITY_POLICY",
    ),
    "app.services.settings.diagnostics": (
        "build_settings_diagnostics_context",
        "CORE_SETTINGS_TABLES",
    ),
    "app.services.settings.rollback_handler": (
        "rollback_settings_change_handler",
        "ROLLBACK_SUPPORTED_SCOPES",
    ),
    "app.services.settings.form_pipeline": (
        "save_system_settings_from_form_handler",
        "save_module_settings_from_form_handler",
        "FORM_SAVE_PIPELINE_SCOPES",
    ),
    "app.services.settings.quality_gate": (
        "build_settings_refactor_quality_snapshot",
        "build_settings_template_guard_context",
        "get_settings_refactor_phase_sequence",
    ),
    "app.services.settings.ui_panel": (
        "build_settings_ui_diagnostics_panel",
    ),
    "app.services.settings.final_hardening": (
        "build_settings_final_hardening_report",
        "get_settings_final_release_checklist",
        "assert_settings_final_hardening_contract",
    ),
}


def get_settings_refactor_phase_sequence() -> list[dict[str, str]]:
    """Ayarlar servis refactor fazlarının okunabilir sırasını döndürür."""
    return [asdict(item) for item in SETTINGS_REFACTOR_PHASES]


def _module_symbol_state(module_name: str, symbols: tuple[str, ...]) -> dict[str, Any]:
    try:
        module = import_module(module_name)
    except Exception as exc:  # pragma: no cover - canlı import/bağımlılık alanı
        return {
            "module": module_name,
            "available": False,
            "missing_symbols": list(symbols),
            "error": str(exc),
        }

    missing = [symbol for symbol in symbols if not hasattr(module, symbol)]
    return {
        "module": module_name,
        "available": not missing,
        "missing_symbols": missing,
        "error": "",
    }


def build_settings_refactor_quality_snapshot() -> dict[str, Any]:
    """Servis parçalarının faz bazlı bütünlük özetini üretir.

    Yan etkisizdir: DB yazmaz, commit/rollback çalıştırmaz, ayar değiştirmez.
    """
    module_states = [
        _module_symbol_state(module_name, symbols)
        for module_name, symbols in REQUIRED_SERVICE_SYMBOLS.items()
    ]
    missing_modules = [item for item in module_states if not item["available"]]
    completed = [item for item in SETTINGS_REFACTOR_PHASES if item.status == "tamamlandı"]
    pending = [item for item in SETTINGS_REFACTOR_PHASES if item.status != "tamamlandı"]
    return {
        "ok": not missing_modules and not pending,
        "phase": "settings_faz12_final_quality_gate",
        "completed_phase_count": len(completed),
        "active_phase": "Kapanış tamamlandı",
        "next_phases": [asdict(item) for item in pending],
        "module_states": module_states,
    }


def build_settings_template_guard_context(
    *,
    foundation_context: dict[str, Any] | None = None,
    profile_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Template tarafı için güvenli, yan etkisiz yardımcı bağlam döndürür."""
    foundation_context = foundation_context or {}
    profile_context = profile_context or {}
    return {
        "quality_snapshot": build_settings_refactor_quality_snapshot(),
        "has_foundation_context": bool(foundation_context),
        "has_profile_context": bool(profile_context),
        "foundation_db_ready": bool(foundation_context.get("db_ready", False)),
        "history_total": int((foundation_context.get("stats") or {}).get("history_total") or 0),
    }
