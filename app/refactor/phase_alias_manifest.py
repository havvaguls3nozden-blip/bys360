"""BYS360 faz numaralı dosya alias sözleşmesi.

Faz 7 runtime davranışını değiştirmez ve hiçbir dosyayı yeniden adlandırmaz.
Bu manifest, faz numaralı dosyaların neye karşılık geldiğini belgelemek,
gelecekte alias-first geçiş planını güvenli yapmak ve kalite kapılarında
beklenen dosya ailelerini doğrulamak için kullanılır.
"""
from __future__ import annotations


RENAME_POLICY = "alias-first"
RUNTIME_RENAME_ALLOWED = False
PHASE_ALIAS_VERSION = "2026-04-21-core-refactor-faz8-lazy-alias-wrappers"
ALIAS_WRAPPERS_ENABLED = True
ALIAS_WRAPPER_POLICY = "lazy-wrapper"

# Bu dosyalar canlı sistemde mevcut adlarıyla kalır. Faz 7 yalnızca önerilen
# anlamlı alias adını ve risk seviyesini kayıt altına alır.
PHASE_ALIAS_MANIFEST: tuple[dict[str, str], ...] = (
    {
        "legacy_path": "app/admin/ai_phase2_routes.py",
        "proposed_alias_path": "app/admin/ai_decision_foundation_routes.py",
        "family": "admin_ai",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "AI karar destek temel yönetim rotaları; canlıda yeniden adlandırma yapılmadı.",
    },
    {
        "legacy_path": "app/admin/ai_phase5_routes.py",
        "proposed_alias_path": "app/admin/ai_decision_recommendation_routes.py",
        "family": "admin_ai",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "AI öneri/karar destek ailesi için alias adayı.",
    },
    {
        "legacy_path": "app/admin/ai_phase6_routes.py",
        "proposed_alias_path": "app/admin/ai_decision_logs_routes.py",
        "family": "admin_ai",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "AI işlem günlükleri ve izleme ailesi için alias adayı.",
    },
    {
        "legacy_path": "app/admin/ai_phase7_routes.py",
        "proposed_alias_path": "app/admin/ai_decision_policy_routes.py",
        "family": "admin_ai",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "AI politika/yönetim katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/admin/ai_phase8_routes.py",
        "proposed_alias_path": "app/admin/ai_decision_dashboard_routes.py",
        "family": "admin_ai",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "AI karar destek dashboard katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/admin/ai_phase9_routes.py",
        "proposed_alias_path": "app/admin/ai_decision_reporting_routes.py",
        "family": "admin_ai",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "AI raporlama/çıktı katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/admin/ai_phase10_routes.py",
        "proposed_alias_path": "app/admin/ai_decision_quality_routes.py",
        "family": "admin_ai",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "AI kalite kontrol/gözden geçirme ailesi için alias adayı.",
    },
    {
        "legacy_path": "app/admin/ai_phase11_routes.py",
        "proposed_alias_path": "app/admin/ai_decision_governance_routes.py",
        "family": "admin_ai",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "AI yönetişim katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/admin/ai_phase12_routes.py",
        "proposed_alias_path": "app/admin/ai_decision_advanced_routes.py",
        "family": "admin_ai",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "Faz 12 açıklaması korunur; ileri karar destek alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase1_routes.py",
        "proposed_alias_path": "app/communication/announcements_core_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "İletişim çekirdek duyuru/akış başlangıç katmanı.",
    },
    {
        "legacy_path": "app/communication/phase2_routes.py",
        "proposed_alias_path": "app/communication/notifications_core_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Bildirim akışı için alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase3_routes.py",
        "proposed_alias_path": "app/communication/messages_core_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Mesajlaşma çekirdek rotaları için alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase4_routes.py",
        "proposed_alias_path": "app/communication/messages_attachment_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Mesaj ekleri/medya akışı için alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase5_routes.py",
        "proposed_alias_path": "app/communication/messages_interaction_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Mesaj etkileşimleri ve ek davranışlar için alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase8_routes.py",
        "proposed_alias_path": "app/communication/surveys_core_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Anket yönetimi canlı kapsamda korunur; alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase9_routes.py",
        "proposed_alias_path": "app/communication/feedback_core_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Geri bildirim/nabız çekirdek rotaları için alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase9a_routes.py",
        "proposed_alias_path": "app/communication/feedback_campaign_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Geri bildirim kampanya katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase9b_routes.py",
        "proposed_alias_path": "app/communication/feedback_meeting_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Geri bildirim görüşme/randevu katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase9c_routes.py",
        "proposed_alias_path": "app/communication/feedback_action_plan_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Aksiyon planı katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/communication/phase9d_routes.py",
        "proposed_alias_path": "app/communication/feedback_analytics_routes.py",
        "family": "communication",
        "risk": "high",
        "status": "alias_wrapper_added",
        "note": "Geri bildirim analiz/rapor katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/institutional/hr_personnel_phase10_routes.py",
        "proposed_alias_path": "app/institutional/hr_personnel_reports_routes.py",
        "family": "institutional_hr",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "Personel raporları katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/institutional/hr_personnel_phase11_routes.py",
        "proposed_alias_path": "app/institutional/hr_personnel_leave_routes.py",
        "family": "institutional_hr",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "İzin/devamsızlık personel yönetimi katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/institutional/hr_personnel_phase12_routes.py",
        "proposed_alias_path": "app/institutional/hr_personnel_delegation_routes.py",
        "family": "institutional_hr",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "Vekâlet yönetimi katmanı için alias adayı.",
    },
    {
        "legacy_path": "app/institutional/hr_personnel_phase13_routes.py",
        "proposed_alias_path": "app/institutional/hr_personnel_analytics_routes.py",
        "family": "institutional_hr",
        "risk": "medium",
        "status": "alias_wrapper_added",
        "note": "Personel analiz katmanı için alias adayı.",
    },
)

# Bunlar route olmayan ama faz numarası taşıyan servis/model/refactor dosyalarıdır.
# Yeniden adlandırma daha risklidir; yalnızca envanterde izlenir.
PHASE_SUPPORT_FILE_FAMILIES = {
    "app/models/communication_phase*_models.py": "communication model ailesi",
    "app/services/communication_phase*_service.py": "communication service ailesi",
    "app/refactor/faz*.py": "geçmiş refactor yardımcıları",
    "app/config/faz6_engine_patch.py": "uyumluluk patch dosyası",
}


def get_phase_alias_manifest() -> dict[str, object]:
    """Faz numaralı dosya alias sözleşmesini döndürür."""

    entries = [dict(item) for item in PHASE_ALIAS_MANIFEST]
    families = sorted({item["family"] for item in entries})
    return {
        "version": PHASE_ALIAS_VERSION,
        "rename_policy": RENAME_POLICY,
        "runtime_rename_allowed": RUNTIME_RENAME_ALLOWED,
        "alias_wrappers_enabled": ALIAS_WRAPPERS_ENABLED,
        "alias_wrapper_policy": ALIAS_WRAPPER_POLICY,
        "entries": entries,
        "families": families,
        "support_file_families": dict(PHASE_SUPPORT_FILE_FAMILIES),
    }
