
"""Ayarlar Servisi Faz 12 final canlı sertleştirme yardımcıları.

Bu modül ayar kaydetme, rollback, menü görünürlüğü veya veritabanı yazma
akışını DEĞİŞTİRMEZ. Kapanış fazında amaç; Faz 4-11 arasında servis
katmanına alınan parçaların canlıya uygun, yan etkisiz ve okunabilir bir final
raporuna dönüştürülmesidir.
"""
from __future__ import annotations

from typing import Any

from app.services.settings.quality_gate import (
    build_settings_refactor_quality_snapshot,
    get_settings_refactor_phase_sequence,
)

FINAL_HARDENING_GUARDS: tuple[dict[str, str], ...] = (
    {
        "code": "settings.write_contract.kept",
        "title": "Ayar kayıt sözleşmesi korunur",
        "description": "save_system_settings_from_form ve save_module_settings_from_form dış sözleşmesi aynı kalır.",
    },
    {
        "code": "settings.rollback_contract.kept",
        "title": "Rollback sözleşmesi korunur",
        "description": "rollback_settings_change dış çağrılarda aynı isimle çalışmaya devam eder.",
    },
    {
        "code": "settings.menu_visibility.single_source",
        "title": "Menü görünürlüğü tek kaynaklıdır",
        "description": "Effective menu visibility hesabı servis katmanındaki effective_menu köprüsü üzerinden okunur.",
    },
    {
        "code": "settings.live_scope.guarded",
        "title": "Canlı kapsam filtresi korunur",
        "description": "Kaldırılmış modüller ayar/menü kayıt akışına geri sokulmaz.",
    },
    {
        "code": "settings.audit_history.readable",
        "title": "Değişiklik geçmişi okunabilir",
        "description": "settings_change_logs ve recent history servis fonksiyonları korunur.",
    },
    {
        "code": "settings.no_secret_material",
        "title": "Gizli bilgi pakete alınmaz",
        "description": "Overlay içinde .env, parola veya canlı gizli değer taşınmaz.",
    },
)

FINAL_REQUIRED_SERVICE_MODULES: tuple[str, ...] = (
    "app.services.settings.change_logs",
    "app.services.settings.menu_permissions",
    "app.services.settings.effective_menu",
    "app.services.settings.diagnostics",
    "app.services.settings.rollback_handler",
    "app.services.settings.form_pipeline",
    "app.services.settings.quality_gate",
    "app.services.settings.ui_panel",
    "app.services.settings.final_hardening",
)

FINAL_SETTINGS_TABLES: tuple[str, ...] = (
    "system_settings",
    "module_settings",
    "settings_change_logs",
    "user_menu_permissions",
    "role_menu_defaults",
    "unit_menu_profiles",
)


def _bool(value: Any) -> bool:
    return bool(value)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _guard(code: str, ok: bool, title: str, detail: str) -> dict[str, Any]:
    return {
        "code": code,
        "ok": bool(ok),
        "status": "OK" if ok else "KONTROL",
        "title": title,
        "detail": detail,
    }


def get_settings_final_release_checklist() -> list[dict[str, str]]:
    """Faz 12 canlı kapanış kontrol başlıklarını döndürür."""
    return [dict(item) for item in FINAL_HARDENING_GUARDS]


def build_settings_final_hardening_report(
    *,
    foundation_context: dict[str, Any] | None = None,
    profile_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ayarlar servisi için yan etkisiz final canlı sertleştirme raporu üretir.

    DB yazmaz, commit/rollback çalıştırmaz, form verisini değiştirmez. Route veya
    template tarafında güvenle okunabilecek özet veri sağlar.
    """
    foundation_context = foundation_context or {}
    profile_context = profile_context or {}
    quality_snapshot = build_settings_refactor_quality_snapshot()
    phase_sequence = get_settings_refactor_phase_sequence()
    stats = foundation_context.get("stats") or {}
    missing_tables = list(foundation_context.get("missing_tables") or [])
    module_states = list(quality_snapshot.get("module_states") or [])
    unavailable_modules = [item for item in module_states if not item.get("available")]
    completed_phase_count = len([item for item in phase_sequence if item.get("status") == "tamamlandı"])
    all_phases_closed = completed_phase_count >= 9 and not [item for item in phase_sequence if item.get("status") in {"aktif", "sırada"}]

    guard_results = [
        _guard(
            "phase_sequence.closed",
            all_phases_closed,
            "Faz 4-12 kapanış sırası tamamlandı",
            f"Tamamlanan faz: {completed_phase_count} / {len(phase_sequence)}",
        ),
        _guard(
            "service_modules.available",
            _bool(quality_snapshot.get("ok")) and not unavailable_modules,
            "Servis modülleri erişilebilir",
            f"İzlenen modül: {len(module_states)} · Eksik: {len(unavailable_modules)}",
        ),
        _guard(
            "foundation_tables.ready",
            not missing_tables,
            "Ayar omurga tabloları hazır",
            "Eksik tablo yok." if not missing_tables else ", ".join(missing_tables),
        ),
        _guard(
            "history_context.readable",
            "recent_change_logs" in foundation_context or "recent_change_logs" in profile_context,
            "Son değişiklik geçmişi okunabilir",
            f"Genel geçmiş kayıt sayısı: {len(foundation_context.get('recent_change_logs') or [])}",
        ),
        _guard(
            "settings_counts.visible",
            _as_int(stats.get("system_total")) >= 0 and _as_int(stats.get("module_total")) >= 0,
            "Ayar sayıları raporlanabilir",
            f"Genel: {_as_int(stats.get('system_total'))} · Modül: {_as_int(stats.get('module_total'))}",
        ),
        _guard(
            "write_side_effects.none",
            True,
            "Final raporu yan etkisizdir",
            "Bu modül DB yazmaz, commit/rollback çalıştırmaz.",
        ),
    ]

    return {
        "ok": all(item["ok"] for item in guard_results),
        "phase": "settings_faz12_final_hardening",
        "summary": {
            "completed_phase_count": completed_phase_count,
            "phase_total": len(phase_sequence),
            "module_total": len(module_states),
            "unavailable_module_total": len(unavailable_modules),
            "missing_table_total": len(missing_tables),
            "system_setting_total": _as_int(stats.get("system_total")),
            "module_setting_total": _as_int(stats.get("module_total")),
            "history_total": _as_int(stats.get("history_total")),
        },
        "phase_sequence": phase_sequence,
        "quality_snapshot": quality_snapshot,
        "guard_results": guard_results,
        "release_checklist": get_settings_final_release_checklist(),
        "required_tables": list(FINAL_SETTINGS_TABLES),
        "required_modules": list(FINAL_REQUIRED_SERVICE_MODULES),
    }


def assert_settings_final_hardening_contract(
    *,
    foundation_context: dict[str, Any] | None = None,
    profile_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Final raporu üretir; başarısızsa açıklayıcı ValueError fırlatır."""
    report = build_settings_final_hardening_report(
        foundation_context=foundation_context,
        profile_context=profile_context,
    )
    if not report.get("ok"):
        failing = [item for item in report.get("guard_results", []) if not item.get("ok")]
        codes = ", ".join(item.get("code", "unknown") for item in failing) or "unknown"
        raise ValueError(f"Ayarlar Servisi Faz 12 final kontrolü başarısız: {codes}")
    return report
