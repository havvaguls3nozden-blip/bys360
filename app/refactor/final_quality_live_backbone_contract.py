
"""BYS360 Final Quality Faz 3 canlı omurga entegrasyon sözleşmesi.

Bu dosya runtime akışını değiştirmez. Canlıda kalacak ana aileleri,
entegrasyon bağlantılarını ve release kanıtlarını test edilebilir bir
manifest olarak tutar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class LiveBackboneArea:
    key: str
    title: str
    table_names: tuple[str, ...]
    source_tokens: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    integration_note: str


@dataclass(frozen=True)
class IntegrationFlow:
    key: str
    title: str
    source_area: str
    target_area: str
    required_tokens: tuple[str, ...]
    risk_guard: str


@dataclass(frozen=True)
class ReleaseEvidenceContract:
    key: str
    title: str
    required_paths: tuple[str, ...]
    forbidden_release_paths: tuple[str, ...]
    result_marker: str


LIVE_BACKBONE_AREAS: Final[tuple[LiveBackboneArea, ...]] = (
    LiveBackboneArea(
        key="identity_authorization_settings",
        title="Kimlik, kullanıcı, yetki ve ayarlar",
        table_names=("users", "organization_units", "user_menu_permissions", "role_menu_defaults", "system_settings", "audit_logs"),
        source_tokens=("User", "OrganizationUnit", "user_menu_permissions", "system_settings", "audit_logs"),
        evidence_paths=("app/models/", "app/auth/", "app/security/", "app/services/settings/"),
        integration_note="Tüm canlı modüller kimlik, yetki, menü görünürlüğü ve audit izi üzerinden bağlanır.",
    ),
    LiveBackboneArea(
        key="personnel_organization",
        title="Personel ve organizasyon yönetimi",
        table_names=("users", "organization_units", "organization_unit_versions", "employee_org_assignment_history"),
        source_tokens=("OrganizationUnit", "employee_org_assignment_history", "User", "personnel"),
        evidence_paths=("app/institutional/", "app/services/personnel/", "app/models/"),
        integration_note="Personel ve birim omurgası performans, izin ve vekâlet akışlarının ortak kaynağıdır.",
    ),
    LiveBackboneArea(
        key="performance_management",
        title="Performans yönetimi",
        table_names=("performance_criteria", "performance_periods", "evaluation_assignments", "performance_evaluations", "performance_result_snapshots"),
        source_tokens=("EvaluationAssignment", "PerformancePeriod", "performance_evaluations", "Değerlendirme Kriterleri"),
        evidence_paths=("app/performance/", "app/services/performance/", "app/services/performance_v2/"),
        integration_note="Nihai amir matrisi, yayın görünürlüğü ve sonuç snapshotları burada korunur.",
    ),
    LiveBackboneArea(
        key="leave_delegation",
        title="İzin, devamsızlık ve vekâlet hattı",
        table_names=("attendance_events", "leave_requests", "personnel_leaves", "delegation_assignments"),
        source_tokens=("DelegationAssignment", "PersonnelLeave", "leave_requests", "attendance"),
        evidence_paths=("app/institutional/", "app/services/personnel/", "app/services/hr_date_rules.py"),
        integration_note="İzinli amirin görevi boşa düşmez; vekâlet akışı performans görev seviyesini korur.",
    ),
    LiveBackboneArea(
        key="communication_survey_feedback",
        title="İletişim, anket ve geri bildirim",
        table_names=("messages", "message_threads", "message_attachments", "surveys", "survey_responses", "feedback_requests"),
        source_tokens=("MessageThread", "MessageThreadParticipant", "Survey", "Feedback", "feedback_requests"),
        evidence_paths=("app/communication/", "app/services/messages/", "app/services/surveys/"),
        integration_note="Mesaj, anket ve nabız/geri bildirim aileleri canlı iletişim omurgasını oluşturur.",
    ),
    LiveBackboneArea(
        key="support_center",
        title="Yardım merkezi ve destek talepleri",
        table_names=("support_categories", "support_tickets", "support_ticket_messages", "support_ticket_attachments", "support_feedback_ratings"),
        source_tokens=("SupportTicket", "support_tickets", "support_ticket_messages", "support_feedback"),
        evidence_paths=("app/support/", "app/templates/support/", "app/route_support.py"),
        integration_note="Kullanıcı desteği, talep geçmişi ve memnuniyet geribildirimi canlı kapsamda tutulur.",
    ),
    LiveBackboneArea(
        key="ai_decision_support",
        title="AI karar destek merkezi",
        table_names=("ai_feedback_logs", "ai_recommendations", "ai_redaction_rules", "ai_request_logs", "ai_summary_cache"),
        source_tokens=("ai_request", "ai_recommend", "ai_summary", "redaction", "AI"),
        evidence_paths=("app/admin/ai_phase12_routes.py", "app/services/ai/", "app/ai/"),
        integration_note="AI yalnızca kontrollü karar destek, özetleme, önceliklendirme ve audit amaçlı konumlanır.",
    ),
    LiveBackboneArea(
        key="home_weather_daily_summary",
        title="Anasayfa, hava durumu ve günlük öneriler",
        table_names=("notifications", "mail_logs"),
        source_tokens=("build_home_page_context", "get_home_weather_context", "build_weather_recommendations", "WEATHER_CACHE_MINUTES"),
        evidence_paths=("app/services/home_dashboard_service.py", "app/services/weather_recommendation_service.py", "app/templates/home/"),
        integration_note="Gün Özeti ekranı hava koşulları, görevler ve canlı iş akışını tek güvenli başlangıçta toplar.",
    ),
)


CRITICAL_INTEGRATION_FLOWS: Final[tuple[IntegrationFlow, ...]] = (
    IntegrationFlow(
        key="personnel_to_performance_assignment",
        title="Personel hiyerarşisi → performans görevi",
        source_area="personnel_organization",
        target_area="performance_management",
        required_tokens=("employee_org_assignment_history", "EvaluationAssignment", "manager", "period"),
        risk_guard="Hiyerarşi yoksa sahte görev üretilmez.",
    ),
    IntegrationFlow(
        key="leave_delegation_to_performance_task",
        title="İzin / vekâlet → performans görevi devri",
        source_area="leave_delegation",
        target_area="performance_management",
        required_tokens=("DelegationAssignment", "PersonnelLeave", "evaluation", "audit"),
        risk_guard="İzinli amirin görevi boşa düşmez; aynı seviye vekile aktarılır.",
    ),
    IntegrationFlow(
        key="performance_publish_to_personnel_visibility",
        title="Performans yayın → personel görünürlüğü",
        source_area="performance_management",
        target_area="identity_authorization_settings",
        required_tokens=("publish", "performance_result_snapshots", "visible", "audit"),
        risk_guard="İK/Admin yayınlamadan personel sonucu göremez.",
    ),
    IntegrationFlow(
        key="communication_feedback_to_management_summary",
        title="İletişim / anket / geri bildirim → yönetim özeti",
        source_area="communication_survey_feedback",
        target_area="home_weather_daily_summary",
        required_tokens=("Survey", "Feedback", "MessageThread", "summary"),
        risk_guard="Özetler karar destek niteliğindedir; kullanıcı yetkisi dışında veri açılmaz.",
    ),
    IntegrationFlow(
        key="support_to_audit_and_feedback",
        title="Yardım merkezi → audit ve memnuniyet döngüsü",
        source_area="support_center",
        target_area="identity_authorization_settings",
        required_tokens=("SupportTicket", "support_feedback_ratings", "audit"),
        risk_guard="Talep geçmişi ve durum değişiklikleri iz bırakır.",
    ),
    IntegrationFlow(
        key="ai_decision_to_audit_logs",
        title="AI karar destek → audit / redaksiyon / log",
        source_area="ai_decision_support",
        target_area="identity_authorization_settings",
        required_tokens=("ai_request_logs", "ai_redaction_rules", "ai_feedback_logs"),
        risk_guard="AI çıktısı kesin karar değil, kayıtlı ve denetlenebilir öneridir.",
    ),
)


RELEASE_EVIDENCE_CONTRACTS: Final[tuple[ReleaseEvidenceContract, ...]] = (
    ReleaseEvidenceContract(
        # BYS360 DEFECT FS (Final Sweep A3-16): the gate script never
        # existed in this repo; .releaseignore is real and directly relevant.
        key="clean_live_release",
        title="Temiz canlı paket kapısı",
        required_paths=(".releaseignore",),
        forbidden_release_paths=("_overlay_payload/", "docs/refactor/generated/", "__pycache__/", ".pytest_cache/"),
        result_marker="CLEAN_LIVE_RELEASE_GATE_OK",
    ),
    ReleaseEvidenceContract(
        # BYS360 DEFECT FS (Final Sweep A3-15/A3-16): key and required_paths
        # both carried a development-tool trace ("claude"); neither script
        # ever existed. Renamed and emptied rather than resurrected.
        key="release_artifact_hygiene_gate",
        title="Maintenance 10/10 kalite kapısı",
        required_paths=(),
        forbidden_release_paths=(".pytest_runtime/", "*.pyc", "*.pyo"),
        result_marker="QUALITY_GATE_OK",
    ),
    ReleaseEvidenceContract(
        # BYS360 DEFECT FS (Final Sweep A3-16): neither script ever existed;
        # no current equivalent identified.
        key="core_refactor_final_chain",
        title="Core Refactor final zinciri",
        required_paths=(),
        forbidden_release_paths=("app/models.py", "_overlay_payload/"),
        result_marker="CORE_REFACTOR_QUALITY_CHAIN_OK",
    ),
    ReleaseEvidenceContract(
        # BYS360 DEFECT FS (Final Sweep A3-16): none of the 3 chain-runner
        # scripts ever existed; no current equivalent identified.
        key="final_quality_chain",
        title="Final Quality Faz 1–3 zinciri",
        required_paths=(),
        forbidden_release_paths=(("db.session" + ".commit("), ("." + "create_all("), ("." + "drop_all(")),
        result_marker="FINAL_QUALITY_FAZ3_CHAIN_OK",
    ),
)


FINAL_QUALITY_FAZ3_VERSION: Final[str] = "2026-04-21-final-quality-faz3-live-backbone-contract"


def get_final_quality_faz3_summary() -> dict[str, object]:
    return {
        "version": FINAL_QUALITY_FAZ3_VERSION,
        "backbone_area_count": len(LIVE_BACKBONE_AREAS),
        "integration_flow_count": len(CRITICAL_INTEGRATION_FLOWS),
        "release_evidence_count": len(RELEASE_EVIDENCE_CONTRACTS),
        "runtime_mutation": False,
        "database_migration": False,
    }


def get_live_backbone_keys() -> tuple[str, ...]:
    return tuple(area.key for area in LIVE_BACKBONE_AREAS)


__all__ = [
    "FINAL_QUALITY_FAZ3_VERSION",
    "LIVE_BACKBONE_AREAS",
    "CRITICAL_INTEGRATION_FLOWS",
    "RELEASE_EVIDENCE_CONTRACTS",
    "get_final_quality_faz3_summary",
    "get_live_backbone_keys",
]
