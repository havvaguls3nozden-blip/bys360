
"""Ayarlar Servisi Faz 11 UI tanılama paneli yardımcıları.

Bu modül ayar kaydetme, rollback veya menü izin davranışını değiştirmez.
Ayarlar ekranında gösterilecek küçük tanılama paneli için, mevcut servis
özetlerini yan etkisiz ve template dostu bir sözlüğe dönüştürür.
"""
from __future__ import annotations

from typing import Any

from app.services.settings.quality_gate import (
    build_settings_refactor_quality_snapshot,
    get_settings_refactor_phase_sequence,
)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _truth_label(flag: bool, *, yes: str = "Hazır", no: str = "Kontrol gerekli") -> str:
    return yes if flag else no


def _status_class(status: str) -> str:
    normalized = (status or "").strip().lower()
    if normalized in {"tamamlandı", "tamamlandi", "aktif", "hazır", "hazir"}:
        return "ok"
    if normalized in {"sırada", "sirada", "bekliyor", "planlandı", "planlandi"}:
        return "pending"
    return "warn"


def build_settings_ui_diagnostics_panel(
    *,
    foundation_context: dict[str, Any] | None = None,
    profile_context: dict[str, Any] | None = None,
    selected_user: Any | None = None,
) -> dict[str, Any]:
    """Ayarlar template'i için Faz 11 tanılama paneli bağlamını üretir.

    Yan etkisizdir: DB yazmaz, commit/rollback çalıştırmaz, form verisini
    değiştirmez. Elindeki contextleri toparlayıp okunabilir kartlara çevirir.
    """
    foundation_context = foundation_context or {}
    profile_context = profile_context or {}
    stats = foundation_context.get("stats") or {}
    missing_tables = list(foundation_context.get("missing_tables") or [])
    db_ready = bool(foundation_context.get("db_ready", not missing_tables))

    quality_snapshot = build_settings_refactor_quality_snapshot()
    phase_sequence = get_settings_refactor_phase_sequence()
    module_states = list(quality_snapshot.get("module_states") or [])
    problem_modules = [item for item in module_states if not item.get("available")]

    if selected_user:
        recent_logs = list(profile_context.get("recent_change_logs") or [])
        history_scope_label = "Seçili kullanıcı geçmişi"
    else:
        recent_logs = list(foundation_context.get("recent_change_logs") or [])
        history_scope_label = "Genel ayar geçmişi"

    completed_phases = [phase for phase in phase_sequence if phase.get("status") == "tamamlandı"]
    active_phase = next((phase for phase in phase_sequence if phase.get("status") == "aktif"), None)
    next_phases = [phase for phase in phase_sequence if phase.get("status") == "sırada"]

    service_ok = bool(quality_snapshot.get("ok")) and not problem_modules
    panel_ok = service_ok and db_ready

    health_cards = [
        {
            "label": "Servis Kalite Kapısı",
            "value": _truth_label(service_ok, yes="Temiz", no="Eksik var"),
            "state": "ok" if service_ok else "warn",
            "help": f"İzlenen servis modülü: {len(module_states)} · Eksik: {len(problem_modules)}",
        },
        {
            "label": "Veritabanı Omurgası",
            "value": _truth_label(db_ready, yes="Hazır", no="Eksik tablo"),
            "state": "ok" if db_ready else "warn",
            "help": "Eksik tablo yok." if db_ready else ", ".join(missing_tables),
        },
        {
            "label": "Ayar Kayıtları",
            "value": str(_as_int(stats.get("system_total")) + _as_int(stats.get("module_total"))),
            "state": "ok",
            "help": f"Genel: {_as_int(stats.get('system_total'))} · Modül: {_as_int(stats.get('module_total'))}",
        },
        {
            "label": history_scope_label,
            "value": str(len(recent_logs)),
            "state": "ok" if recent_logs else "pending",
            "help": "Son değişiklik kayıtları panelde okunabilir." if recent_logs else "Henüz görüntülenecek geçmiş kaydı yok.",
        },
    ]

    return {
        "ok": panel_ok,
        "service_ok": service_ok,
        "db_ready": db_ready,
        "quality_snapshot": quality_snapshot,
        "module_states": module_states,
        "problem_modules": problem_modules,
        "missing_tables": missing_tables,
        "health_cards": health_cards,
        "phase_sequence": [
            {
                **phase,
                "status_class": _status_class(str(phase.get("status") or "")),
            }
            for phase in phase_sequence
        ],
        "completed_phase_count": len(completed_phases),
        "active_phase": active_phase or {},
        "next_phases": next_phases,
        "next_phase_label": (next_phases[0].get("phase") if next_phases else "Kapanış"),
        "summary": {
            "system_total": _as_int(stats.get("system_total")),
            "module_total": _as_int(stats.get("module_total")),
            "role_total": _as_int(stats.get("role_total")),
            "unit_profile_total": _as_int(stats.get("unit_profile_total")),
            "history_total": _as_int(stats.get("history_total")),
        },
    }
