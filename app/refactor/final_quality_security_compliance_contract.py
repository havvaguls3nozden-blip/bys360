
"""BYS360 Final Quality Faz 4 güvenlik, KVKK ve audit sözleşmesi.

Bu modül yalnızca test edilebilir manifest içerir. Runtime davranışı,
veritabanı, route, blueprint veya migration akışını değiştirmez.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

FINAL_QUALITY_FAZ4_VERSION: Final[str] = "2026-04-21-final-quality-faz4-security-compliance"


@dataclass(frozen=True)
class SecurityComplianceControl:
    key: str
    title: str
    standard_refs: tuple[str, ...]
    required_sources: tuple[str, ...]
    required_tokens: tuple[str, ...]
    evidence_note: str
    risk_if_missing: str


@dataclass(frozen=True)
class PersonalDataFlow:
    key: str
    title: str
    data_subject: str
    personal_data_scope: tuple[str, ...]
    storage_or_log_tables: tuple[str, ...]
    protection_controls: tuple[str, ...]
    audit_note: str


@dataclass(frozen=True)
class SecurityAuditEvidence:
    key: str
    title: str
    required_paths: tuple[str, ...]
    required_markers: tuple[str, ...]
    release_gate_marker: str


SECURITY_COMPLIANCE_CONTROLS: Final[tuple[SecurityComplianceControl, ...]] = (
    SecurityComplianceControl(
        key="kvkk_personal_data_minimization",
        title="KVKK kişisel veri minimizasyonu",
        standard_refs=("KVKK", "KVKK-GDPR eşdeğeri"),
        required_sources=("app/models/", "app/services/personnel/", "app/security/", "docs/ENV.md"),
        required_tokens=("sicil", "audit", "permission", "role", "yetki"),
        evidence_note="Personel, izin, performans ve destek akışlarında veri görünürlüğü rol/yetki ile sınırlandırılmalıdır.",
        risk_if_missing="Yetkisiz kişisel veri görünürlüğü ve izlenemez işlem riski oluşur.",
    ),
    SecurityComplianceControl(
        key="csrf_session_cookie_hardening",
        title="CSRF, oturum ve güvenli cookie sertleştirmesi",
        standard_refs=("TS 27001", "ISO 27001 uyumlu kontrol mantığı"),
        required_sources=("app/security/", "app/bootstrap/response_hardening.py", "app/bootstrap/operational_guards.py"),
        required_tokens=("CSRF", "SESSION_COOKIE", "REMEMBER_COOKIE", "security headers", "CSP"),
        evidence_note="Form, oturum ve header kontrolleri canlı kapıların parçası olmalıdır.",
        risk_if_missing="Oturum kaçırma, CSRF ve zayıf tarayıcı güvenliği riski artar.",
    ),
    SecurityComplianceControl(
        key="audit_log_traceability",
        title="Audit log ve işlem izlenebilirliği",
        standard_refs=("KVKK", "TS 27001"),
        required_sources=("app/models/", "app/services/", "reports/refactor/"),
        required_tokens=("audit_logs", "settings_change_logs", "assignment_audit_logs", "ai_request_logs"),
        evidence_note="Kimlik, ayar, performans, AI ve yayın akışları iz bırakmalıdır.",
        risk_if_missing="Yetki değişikliği, performans ataması veya AI önerisi sonradan denetlenemez.",
    ),
    SecurityComplianceControl(
        key="ai_governance_redaction",
        title="AI karar destek yönetişimi ve redaksiyon",
        standard_refs=("ISO 42001", "KVKK-GDPR eşdeğeri"),
        required_sources=("app/admin/ai_phase12_routes.py", "app/services/ai/", "app/ai/"),
        required_tokens=("ai_request_logs", "ai_redaction_rules", "ai_feedback_logs", "controlled decision support", "karar destek"),
        evidence_note="AI çıktısı kesin karar değil, kayıtlı ve redaksiyonla sınırlandırılmış karar destek olmalıdır.",
        risk_if_missing="AI çıktısı kişisel veri veya yetkisiz karar etkisi oluşturabilir.",
    ),
    SecurityComplianceControl(
        key="release_artifact_hygiene",
        title="Canlı paket artefakt temizliği",
        standard_refs=("TS 27001", "release hygiene"),
        required_sources=(".releaseignore", "scripts/check_clean_live_release_gate.py", "scripts/cleanup_claude_release_artifacts.py"),
        required_tokens=("__pycache__", ".pytest_cache", "docs/refactor/generated", "CLEAN_LIVE_RELEASE_GATE_OK"),
        evidence_note="Geliştirme çıktıları canlı pakete girmemeli, clean live gate bunu yakalamalıdır.",
        risk_if_missing="Geçici dosya, rapor veya hassas geliştirme çıktısı canlı pakete taşınabilir.",
    ),
    SecurityComplianceControl(
        key="live_backbone_access_boundaries",
        title="Canlı omurga yetki sınırları",
        standard_refs=("KVKK", "TS 27001"),
        required_sources=("app/refactor/final_quality_live_backbone_contract.py", "app/refactor/final_quality_performance_rules.py"),
        required_tokens=("identity_authorization_settings", "performance_management", "leave_delegation", "personel sonucu göremez"),
        evidence_note="Kimlik, personel, performans, izin, mesaj, anket, destek ve AI aileleri yetki sınırlarıyla korunmalıdır.",
        risk_if_missing="Canlı modüller arası veri erişim sınırları belirsizleşir.",
    ),
)


PERSONAL_DATA_FLOWS: Final[tuple[PersonalDataFlow, ...]] = (
    PersonalDataFlow(
        key="personnel_identity_flow",
        title="Personel kimlik ve sicil akışı",
        data_subject="personel",
        personal_data_scope=("ad soyad", "sicil no", "birim", "unvan", "rol/yetki"),
        storage_or_log_tables=("users", "organization_units", "employee_org_assignment_history", "audit_logs"),
        protection_controls=("rol bazlı görünürlük", "menü yetkisi", "audit izi", "TC yerine Sicil No ilkesi"),
        audit_note="Kullanıcı, birim ve yetki değişiklikleri audit_logs/settings_change_logs ile izlenebilir olmalıdır.",
    ),
    PersonalDataFlow(
        key="performance_evaluation_flow",
        title="Performans değerlendirme akışı",
        data_subject="personel ve amir",
        personal_data_scope=("puan", "kanaat", "genel görüş", "yayın durumu"),
        storage_or_log_tables=("evaluation_assignments", "performance_evaluations", "performance_evaluation_history", "performance_publish_logs"),
        protection_controls=("yayın öncesi personel görünmezliği", "kör değerlendirme yok", "amir yetkisi kadar görünürlük", "audit izi"),
        audit_note="Değerlendirme zinciri ve yayın işlemi sonradan denetlenebilir olmalıdır.",
    ),
    PersonalDataFlow(
        key="leave_delegation_flow",
        title="İzin, devamsızlık ve vekâlet akışı",
        data_subject="personel ve amir",
        personal_data_scope=("izin kaydı", "devamsızlık", "vekâlet", "görev devri"),
        storage_or_log_tables=("leave_requests", "personnel_leaves", "attendance_events", "delegation_assignments"),
        protection_controls=("görev seviyesi korunur", "vekil aktarımı", "audit denetim izi", "sahte bekleme yok"),
        audit_note="İzinli amirin görevi iptal edilmeden vekile aktarılmalı ve audit audit iz kaybı oluşmamalıdır.",
    ),
    PersonalDataFlow(
        key="communication_feedback_flow",
        title="Mesaj, anket, geri bildirim ve destek akışı",
        data_subject="kullanıcı ve personel",
        personal_data_scope=("mesaj", "ek", "anket yanıtı", "destek talebi", "geri bildirim"),
        storage_or_log_tables=("messages", "message_threads", "surveys", "survey_responses", "support_tickets", "feedback_requests"),
        protection_controls=("katılımcı bazlı erişim", "dosya kapsamı", "talep geçmişi", "audit uyumu"),
        audit_note="İletişim, anket ve destek verileri yalnızca ilgili yetki ve katılım kapsamıyla görülmelidir.",
    ),
    PersonalDataFlow(
        key="ai_decision_support_flow",
        title="AI karar destek ve redaksiyon akışı",
        data_subject="kullanıcı, personel ve işlem verisi",
        personal_data_scope=("özet", "öneri", "log", "redaksiyon kuralı", "geri bildirim"),
        storage_or_log_tables=("ai_request_logs", "ai_recommendations", "ai_redaction_rules", "ai_feedback_logs", "ai_summary_cache"),
        protection_controls=("karar destek niteliği", "redaksiyon", "audit loglama", "insan onayı"),
        audit_note="AI çıktıları kesin karar değil, audit izli, izlenebilir ve sınırlandırılmış karar destek kaydıdır.",
    ),
)


SECURITY_AUDIT_EVIDENCE: Final[tuple[SecurityAuditEvidence, ...]] = (
    SecurityAuditEvidence(
        key="clean_live_release",
        title="Clean live release gate",
        required_paths=("scripts/check_clean_live_release_gate.py", ".releaseignore"),
        required_markers=("CLEAN_LIVE_RELEASE_GATE_OK",),
        release_gate_marker="CLEAN_LIVE_RELEASE_GATE_OK",
    ),
    SecurityAuditEvidence(
        key="claude_quality_gate",
        title="Claude 10/10 kalite gate",
        required_paths=("scripts/check_claude_10_10_gate.py", "scripts/cleanup_claude_release_artifacts.py"),
        required_markers=("CLAUDE_10_10_GATE_OK",),
        release_gate_marker="CLAUDE_10_10_GATE_OK",
    ),
    SecurityAuditEvidence(
        key="final_quality_faz3_backbone",
        title="Canlı omurga entegrasyon kanıtı",
        required_paths=("scripts/run_final_quality_faz3_chain.py", "app/refactor/final_quality_live_backbone_contract.py"),
        required_markers=("FINAL_QUALITY_FAZ3_CHAIN_OK",),
        release_gate_marker="FINAL_QUALITY_FAZ3_CHAIN_OK",
    ),
    SecurityAuditEvidence(
        key="final_quality_faz4_security",
        title="Güvenlik, KVKK ve audit kanıtı",
        required_paths=("scripts/check_final_quality_faz4_gate.py", "app/refactor/final_quality_security_compliance_contract.py"),
        required_markers=("FINAL_QUALITY_FAZ4_CHAIN_OK", "FINAL_QUALITY_FAZ4_GATE_OK"),
        release_gate_marker="FINAL_QUALITY_FAZ4_CHAIN_OK",
    ),
)


SECURITY_FORBIDDEN_RUNTIME_ACTIONS: Final[tuple[str, ...]] = (
    "runtime_blueprint_registration",
    "database_schema_mutation",
    "external_network_call",
    "secret_value_hardcoding",
    "env_file_packaging",
)


def get_security_control_keys() -> tuple[str, ...]:
    return tuple(control.key for control in SECURITY_COMPLIANCE_CONTROLS)


def get_personal_data_flow_keys() -> tuple[str, ...]:
    return tuple(flow.key for flow in PERSONAL_DATA_FLOWS)


def get_final_quality_faz4_summary() -> dict[str, object]:
    return {
        "version": FINAL_QUALITY_FAZ4_VERSION,
        "security_control_count": len(SECURITY_COMPLIANCE_CONTROLS),
        "personal_data_flow_count": len(PERSONAL_DATA_FLOWS),
        "audit_evidence_count": len(SECURITY_AUDIT_EVIDENCE),
        "standards": ("KVKK", "KVKK-GDPR eşdeğeri", "TS 27001", "ISO 42001"),
        "runtime_mutation": False,
        "database_migration": False,
        "external_network": False,
        "release_marker": "FINAL_QUALITY_FAZ4_CHAIN_OK",
    }
