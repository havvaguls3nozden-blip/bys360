
"""BYS360 Final Quality Faz 5 final release evidence sözleşmesi.

Bu modül yalnızca kanıt manifesti içerir. Runtime davranışı, route,
blueprint, veritabanı, migration veya template akışını değiştirmez.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

FINAL_QUALITY_FAZ5_VERSION: Final[str] = "2026-04-21-final-quality-faz5-release-evidence"


@dataclass(frozen=True)
class ReleaseEvidenceItem:
    key: str
    title: str
    category: str
    required_paths: tuple[str, ...]
    command_markers: tuple[str, ...]
    evidence_outputs: tuple[str, ...]
    release_value: str


@dataclass(frozen=True)
class ReleaseEvidenceCategory:
    key: str
    title: str
    items: tuple[str, ...]
    required_marker: str


FINAL_RELEASE_EVIDENCE_ITEMS: Final[tuple[ReleaseEvidenceItem, ...]] = (
    ReleaseEvidenceItem(
        key="core_refactor_final_lock",
        title="Core Refactor Faz 1-10 final kilidi",
        category="architecture",
        required_paths=(
            "scripts/check_core_refactor_faz10_gate.py",
            "scripts/run_core_refactor_quality_chain.py",
            "docs/refactor/CORE_REFACTOR_FAZ10.md",
        ),
        command_markers=("CORE_REFACTOR_FAZ10_GATE_OK", "CORE_REFACTOR_QUALITY_CHAIN_OK"),
        evidence_outputs=("reports/refactor/", "docs/refactor/generated/"),
        release_value="app factory, route bootstrap, schema contract, model namespace ve route registry kanıtları kilitlenir.",
    ),
    ReleaseEvidenceItem(
        key="scorecard_cleanup_lock",
        title="Scorecard 8.5 temizlik kilidi",
        category="release_hygiene",
        required_paths=(
            "scripts/check_scorecard_8_5_cleanup_gate.py",
            "scripts/cleanup_scorecard_8_5_artifacts.py",
            ".releaseignore",
        ),
        command_markers=("SCORECARD_8_5_CLEANUP_GATE_OK",),
        evidence_outputs=("ENV.md", ".releaseignore"),
        release_value="root ENV pointer ve docs/refactor/generated canlı paket dışı kuralı korunur.",
    ),
    ReleaseEvidenceItem(
        key="home_phase1_lock",
        title="Anasayfa Faz 1 ve hava durumu fallback kilidi",
        category="home_experience",
        required_paths=(
            "scripts/check_home_phase1_gate.py",
            "tests/architecture/test_home_phase1_contract.py",
        ),
        command_markers=("HOME_PHASE1_GATE_OK",),
        evidence_outputs=("docs/refactor/",),
        release_value="Gün Özeti, hava durumu önerileri ve güvenli fallback akışı doğrulanır.",
    ),
    ReleaseEvidenceItem(
        key="final_quality_faz1_services",
        title="Final Quality Faz 1 servis sözleşmeleri",
        category="service_tests",
        required_paths=(
            "scripts/run_final_quality_faz1_chain.py",
            "app/refactor/final_quality_service_contract.py",
        ),
        command_markers=("FINAL_QUALITY_FAZ1_CHAIN_OK",),
        evidence_outputs=("reports/refactor/final_quality_faz1_report.json",),
        release_value="Canlı servis sözleşmeleri, anasayfa hava durumu ve canlı kaynak testleri kanıtlanır.",
    ),
    ReleaseEvidenceItem(
        key="final_quality_faz2_performance_rules",
        title="Final Quality Faz 2 performans kural matrisi",
        category="performance_rules",
        required_paths=(
            "scripts/run_final_quality_faz2_chain.py",
            "app/refactor/final_quality_performance_rules.py",
        ),
        command_markers=("FINAL_QUALITY_FAZ2_CHAIN_OK",),
        evidence_outputs=("reports/refactor/final_quality_faz2_performance_rule_matrix.json",),
        release_value="Kör değerlendirme yasağı, yayın görünürlüğü, amir zinciri ve 3. amir modu testle korunur.",
    ),
    ReleaseEvidenceItem(
        key="final_quality_faz3_live_backbone",
        title="Final Quality Faz 3 canlı omurga entegrasyon kanıtı",
        category="live_backbone",
        required_paths=(
            "scripts/run_final_quality_faz3_chain.py",
            "app/refactor/final_quality_live_backbone_contract.py",
        ),
        command_markers=("FINAL_QUALITY_FAZ3_CHAIN_OK",),
        evidence_outputs=("reports/refactor/final_quality_faz3_live_backbone.json",),
        release_value="Kimlik, yetki, personel, performans, izin-vekalet, mesaj, anket, destek ve AI omurgası doğrulanır.",
    ),
    ReleaseEvidenceItem(
        key="final_quality_faz4_security_compliance",
        title="Final Quality Faz 4 güvenlik, KVKK ve audit kanıtı",
        category="security_compliance",
        required_paths=(
            "scripts/run_final_quality_faz4_chain.py",
            "app/refactor/final_quality_security_compliance_contract.py",
        ),
        command_markers=("FINAL_QUALITY_FAZ4_CHAIN_OK",),
        evidence_outputs=("reports/refactor/final_quality_faz4_security_compliance.json",),
        release_value="KVKK, KVKK-GDPR eşdeğeri, TS 27001, ISO 42001 ve audit izlenebilirliği kanıtlanır.",
    ),
    ReleaseEvidenceItem(
        key="clean_live_release_gate",
        title="Clean live release gate",
        category="release_hygiene",
        required_paths=("scripts/check_clean_live_release_gate.py", ".releaseignore"),
        command_markers=("CLEAN_LIVE_RELEASE_GATE_OK",),
        evidence_outputs=("reports/refactor/clean_live_release_gate.json",),
        release_value="Canlı pakete env, pycache, pytest cache, generated audit ve geliştirme kalıntıları girmemelidir.",
    ),
    ReleaseEvidenceItem(
        key="claude_10_10_gate",
        title="Maintenance 10/10 kalite gate",
        category="quality_gate",
        required_paths=(
            "scripts/check_claude_10_10_gate.py",
            "scripts/cleanup_claude_release_artifacts.py",
        ),
        command_markers=("QUALITY_GATE_OK",),
        evidence_outputs=("reports/refactor/",),
        release_value="Maintenance değerlendirmesinde tekrar eden paket/artefakt eksikleri yakalanır.",
    ),
)


FINAL_RELEASE_EVIDENCE_CATEGORIES: Final[tuple[ReleaseEvidenceCategory, ...]] = (
    ReleaseEvidenceCategory(
        key="architecture",
        title="Mimari refactor final kilidi",
        items=("core_refactor_final_lock",),
        required_marker="CORE_REFACTOR_QUALITY_CHAIN_OK",
    ),
    ReleaseEvidenceCategory(
        key="service_tests",
        title="Servis ve canlı omurga test kanıtı",
        items=("final_quality_faz1_services", "final_quality_faz3_live_backbone"),
        required_marker="FINAL_QUALITY_FAZ3_CHAIN_OK",
    ),
    ReleaseEvidenceCategory(
        key="performance_rules",
        title="Performans kural matrisi kanıtı",
        items=("final_quality_faz2_performance_rules",),
        required_marker="FINAL_QUALITY_FAZ2_CHAIN_OK",
    ),
    ReleaseEvidenceCategory(
        key="security_compliance",
        title="Güvenlik ve uyum kanıtı",
        items=("final_quality_faz4_security_compliance",),
        required_marker="FINAL_QUALITY_FAZ4_CHAIN_OK",
    ),
    ReleaseEvidenceCategory(
        key="release_hygiene",
        title="Canlı paket temizlik kanıtı",
        items=("scorecard_cleanup_lock", "clean_live_release_gate", "claude_10_10_gate"),
        required_marker="CLEAN_LIVE_RELEASE_GATE_OK",
    ),
    ReleaseEvidenceCategory(
        key="home_experience",
        title="Anasayfa ve günlük özet kanıtı",
        items=("home_phase1_lock",),
        required_marker="HOME_PHASE1_GATE_OK",
    ),
)


FINAL_RELEASE_FORBIDDEN_ACTIONS: Final[tuple[str, ...]] = (
    "runtime route registration",
    "database schema mutation",
    "migration generation",
    "external network call",
    "secret or environment file packaging",
)


def get_release_evidence_keys() -> tuple[str, ...]:
    return tuple(item.key for item in FINAL_RELEASE_EVIDENCE_ITEMS)


def get_release_evidence_category_keys() -> tuple[str, ...]:
    return tuple(category.key for category in FINAL_RELEASE_EVIDENCE_CATEGORIES)


def get_final_quality_faz5_summary() -> dict[str, object]:
    return {
        "version": FINAL_QUALITY_FAZ5_VERSION,
        "evidence_item_count": len(FINAL_RELEASE_EVIDENCE_ITEMS),
        "category_count": len(FINAL_RELEASE_EVIDENCE_CATEGORIES),
        "required_final_markers": (
            "CORE_REFACTOR_QUALITY_CHAIN_OK",
            "FINAL_QUALITY_FAZ4_CHAIN_OK",
            "FINAL_QUALITY_FAZ5_GATE_OK",
            "FINAL_QUALITY_FAZ5_RELEASE_EVIDENCE_OK",
            "CLEAN_LIVE_RELEASE_GATE_OK",
            "QUALITY_GATE_OK",
        ),
        "runtime_mutation": False,
        "database_migration": False,
        "external_network": False,
        "release_marker": "FINAL_QUALITY_FAZ5_CHAIN_OK",
    }
