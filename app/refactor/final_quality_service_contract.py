
"""BYS360 Final Quality Faz 1 canlı servis sözleşmesi.

Runtime akışını değiştirmez. Canlı omurga, performans amir matrisi ve
anasayfa/hava durumu güvenlik sözleşmesini test edilebilir hale getirir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ServiceAreaContract:
    key: str
    title: str
    required_tokens: tuple[str, ...]
    evidence_paths: tuple[str, ...]


@dataclass(frozen=True)
class PerformanceChainContract:
    key: str
    title: str
    first_manager: str
    second_manager: str | None
    third_manager: str | None
    process_order: tuple[str, ...]
    note: str


LIVE_SERVICE_AREAS: Final[tuple[ServiceAreaContract, ...]] = (
    ServiceAreaContract("identity_authorization_settings", "Kimlik, kullanıcı, yetki ve ayarlar", ("User", "user_menu_permissions", "system_settings", "audit_logs"), ("app/models/", "app/services/settings/", "app/security/")),
    ServiceAreaContract("personnel_organization", "Personel ve organizasyon yönetimi", ("organization_units", "employee_org_assignment_history", "User"), ("app/models/", "app/services/personnel/", "app/institutional/")),
    ServiceAreaContract("performance_management", "Performans yönetimi", ("EvaluationAssignment", "PerformancePeriod", "performance_evaluations"), ("app/services/performance/", "app/services/performance_v2/", "app/performance/")),
    ServiceAreaContract("leave_delegation", "İzin ve vekâlet hattı", ("PersonnelLeave", "DelegationAssignment", "leave_requests"), ("app/services/personnel/", "app/services/hr_date_rules.py", "app/institutional/")),
    ServiceAreaContract("communication_survey_feedback", "İletişim, anket ve geri bildirim", ("MessageThread", "Survey", "Feedback"), ("app/communication/", "app/services/messages/", "app/services/surveys/")),
    ServiceAreaContract("ai_decision_support", "AI karar destek merkezi", ("ai_request_logs", "ai_recommendations", "ai_summary_cache"), ("app/admin/ai_phase12_routes.py", "app/services/ai/", "app/ai/")),
    ServiceAreaContract("support_center", "Yardım merkezi ve destek talepleri", ("SupportTicket", "support_tickets", "support_ticket_messages"), ("app/support/", "app/templates/support/", "app/services/")),
    ServiceAreaContract("home_weather_summary", "Anasayfa, hava durumu ve günlük öneriler", ("WeatherSettings", "build_home_page_context", "build_weather_recommendations"), ("app/services/home_dashboard_service.py", "app/services/weather_recommendation_service.py")),
)


PERFORMANCE_CHAIN_CONTRACTS: Final[tuple[PerformanceChainContract, ...]] = (
    PerformanceChainContract("calisma_grubu_personeli", "Çalışma grubu personeli", "grup_baskani", "koordinator", "koordinatore_bagli_birim_amiri_opsiyonel", ("third", "second", "first"), "Nihai üst amir Grup Başkanıdır; Koordinatör ikinci seviyedir."),
    PerformanceChainContract("koordinator", "Koordinatör", "baskan_yardimcisi", "grup_baskani", "opsiyonel", ("third", "second", "first"), "Koordinatör için 1. amir Başkan Yardımcısı, 2. amir Grup Başkanıdır."),
    PerformanceChainContract("grup_baskani", "Grup Başkanı", "baskan", "baskan_yardimcisi", None, ("second", "first"), "Önce Başkan Yardımcısı, sonra Başkan değerlendirir."),
    PerformanceChainContract("hukuk_musavirine_bagli_personel", "Hukuk müşavirine bağlı hukuk personeli", "bagli_oldugu_hukuk_musaviri", None, None, ("first",), "Tek amirli özel akış; sahte 2. amir bekleme durumu üretilmez."),
    PerformanceChainContract("hukuk_musaviri_sorumlu", "Hukuk müşaviri / sorumlu hukuk müşaviri", "baskan", "baskan_yardimcisi", None, ("second", "first"), "Genel hukuk tek-amir kuralından ayrı üst rol istisnası."),
    PerformanceChainContract("baskan_tek_degerlendirici_ozel_roller", "Başkan danışmanı / Özel Kalem / İç Denetçi", "baskan", None, None, ("first",), "Sadece Başkan tarafından puanlanan tek amirli akış."),
)


WEATHER_HOME_CONTRACT: Final[dict[str, object]] = {
    "provider": "open_meteo",
    "api_key_required": False,
    "must_have_fallback": True,
    "cache_minutes_default": 60,
    "decision_support_disclaimer": "Bu öneriler bilgilendirme amaçlıdır; nihai saha kararı yetkili sorumlular tarafından verilir.",
    "expected_recommendation_risks": ("wind", "rain", "heat", "cold", "fog", "storm"),
}

FINAL_QUALITY_FAZ1_VERSION: Final[str] = "2026-04-21-final-quality-faz1-service-contract"


def get_contract_summary() -> dict[str, object]:
    return {
        "version": FINAL_QUALITY_FAZ1_VERSION,
        "service_area_count": len(LIVE_SERVICE_AREAS),
        "performance_chain_count": len(PERFORMANCE_CHAIN_CONTRACTS),
        "weather_provider": WEATHER_HOME_CONTRACT["provider"],
        "runtime_mutation": False,
    }


__all__ = ["FINAL_QUALITY_FAZ1_VERSION", "LIVE_SERVICE_AREAS", "PERFORMANCE_CHAIN_CONTRACTS", "WEATHER_HOME_CONTRACT", "get_contract_summary"]
