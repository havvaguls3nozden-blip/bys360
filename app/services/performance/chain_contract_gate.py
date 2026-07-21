
"""BYS360 Performans Amir Zinciri Sözleşme Kapısı.

Bu modül canlı davranış değiştirmez. Chain engine dosyasının nihai amir
matrisine uygun sabitleri ve sözleşme izlerini taşıdığını statik olarak
kontrol eder. Route, görev üretimi, puanlama veya veritabanı işlemi yapmaz.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

CHAIN_CONTRACT_GATE_VERSION = "2026-04-20-performance-chain-contract-gate-faz1"

EXPECTED_SLOT_CONTRACT: dict[str, dict[int, str]] = {
    "GROUP_STAFF_SLOTS": {
        1: "grup_baskani",
        2: "koordinator",
        3: "birim_amiri_optional",
    },
    "COORDINATOR_SLOTS": {
        1: "baskan_yardimcisi",
        2: "grup_baskani",
    },
    "GROUP_MANAGER_SLOTS": {
        1: "baskan",
        2: "baskan_yardimcisi",
    },
}

EXPECTED_FLOW_CONTRACT: dict[str, tuple[int, ...]] = {
    "DEFAULT_SINGLE_MANAGER_FLOW": (1,),
    "DEFAULT_TWO_MANAGER_FLOW": (2, 1),
    "DEFAULT_THREE_MANAGER_FLOW": (3, 2, 1),
}

EXPECTED_WEIGHT_CONTRACT: dict[str, dict[int, float]] = {
    "SINGLE_MANAGER_WEIGHTS": {1: 100.0, 2: 0.0, 3: 0.0},
    "TWO_MANAGER_WEIGHTS": {1: 50.0, 2: 50.0, 3: 0.0},
    "THREE_MANAGER_COMMENT_WEIGHTS": {1: 50.0, 2: 50.0, 3: 0.0},
    "THREE_MANAGER_SCORING_WEIGHTS": {1: 40.0, 2: 40.0, 3: 20.0},
}

EXPECTED_DIRECT_PRESIDENT_TITLES: tuple[str, ...] = (
    "baskan_danismani",
    "ozel_kalem",
    "ic_denetci",
)

CHAIN_ENGINE_REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "chain_rule_engine.py": (
        "RULE_ENGINE_VERSION",
        "AuthoritativeChain",
        "compute_flow_order",
        "resolve_authoritative_chain",
        "resolve_authoritative_desired_chain",
        "weights_for_chain",
        "get_chain_rule_matrix_snapshot",
        "assert_chain_constitution_alignment",
        "blind_review_allowed",
        "employee_result_requires_publish",
        "next_manager_sees_previous_score_and_comment",
    ),
    "rules.py": (
        "AUTHORITATIVE_PERFORMANCE_RULESET_VERSION",
        "PRESIDENT_LEVEL_REVIEW_ORDER",
        "GROUP_LEVEL_REVIEW_ORDER_WITH_LEVEL3",
        "GROUP_LEVEL_REVIEW_ORDER_DEFAULT",
        "COORDINATOR_SELF_REVIEW_ORDER",
        "LEVEL_3_ALLOWED_MODES",
        "BLIND_REVIEW_ALLOWED",
        "INFO_REASON_HUKUK_SINGLE_MANAGER",
        "INFO_REASON_SPECIAL_SINGLE_MANAGER",
        "INFO_REASON_PRESIDENT_EXCLUDED",
    ),
    "canonical_chain_service.py": (
        "get_chain_slots",
        "get_flow_order",
        "validate_chain_slots",
        "HUKUK MÜŞAVİRLİĞİ",
        "special_presidency_single_manager",
    ),
    "slot_flow_order_service.py": (
        "slot_map_from_row",
        "flow_order_for_row",
        "build_health_issues_from_slots",
        "Akış sırası slot numarası değildir",
        "HUKUK MÜŞAVİRLİĞİ",
    ),
}

CHAIN_ENGINE_FORBIDDEN_PATTERNS: dict[str, tuple[str, ...]] = {
    "chain_rule_engine.py": (
        r"GROUP_STAFF_SLOTS\s*:[\s\S]*?1\s*:\s*[\"']koordinator[\"']",
        r"COORDINATOR_SLOTS\s*:[\s\S]*?1\s*:\s*[\"']grup_baskani[\"']",
        r"GROUP_MANAGER_SLOTS\s*:[\s\S]*?1\s*:\s*[\"']baskan_yardimcisi[\"']",
        r"DEFAULT_TWO_MANAGER_FLOW\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*\)",
        r"DEFAULT_THREE_MANAGER_FLOW\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*,\s*3\s*\)",
        r"blind_review_allowed[\"']?\s*[:=]\s*True",
    ),
    "rules.py": (
        r"BLIND_REVIEW_ALLOWED\s*:[^=]*=\s*True",
        r"LEVEL_3_DEFAULT_MODE\s*:[^=]*=\s*[\"']scoring[\"']",
        r"PRESIDENT_LEVEL_REVIEW_ORDER\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*\)",
    ),
}

CHAIN_CONTRACT_COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/chain_contract_gate.py",
    "app/services/performance/rule_matrix_final_gate.py",
    "scripts/check_performance_chain_contract_gate.py",
    "scripts/check_performance_rule_matrix_final_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz1_audit.py",
)


@dataclass
class ChainContractFinding:
    code: str
    message: str
    severity: str = "error"


@dataclass
class ChainContractReport:
    version: str = CHAIN_CONTRACT_GATE_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[ChainContractFinding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.findings if item.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.findings if item.severity == "warning")

    def passed(self) -> bool:
        return self.error_count == 0

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "passed": self.passed(),
            "ok_count": len(self.ok),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "ok": list(self.ok),
            "findings": [item.__dict__.copy() for item in self.findings],
            "expected_slot_contract": EXPECTED_SLOT_CONTRACT,
            "expected_flow_contract": {key: list(value) for key, value in EXPECTED_FLOW_CONTRACT.items()},
            "expected_direct_president_titles": list(EXPECTED_DIRECT_PRESIDENT_TITLES),
        }


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _service_path(root: Path, filename: str) -> Path:
    return root / "app" / "services" / "performance" / filename


def _check_tokens(root: Path, report: ChainContractReport) -> None:
    for filename, tokens in CHAIN_ENGINE_REQUIRED_TOKENS.items():
        path = _service_path(root, filename)
        if not path.exists():
            report.findings.append(ChainContractFinding("missing_file", f"Eksik performans servis dosyası: {path.relative_to(root)}"))
            continue
        content = _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"{path.relative_to(root)} :: {token}")
            else:
                report.findings.append(ChainContractFinding("missing_required_token", f"Eksik sözleşme izi: {path.relative_to(root)} :: {token}"))


def _check_forbidden_patterns(root: Path, report: ChainContractReport) -> None:
    for filename, patterns in CHAIN_ENGINE_FORBIDDEN_PATTERNS.items():
        path = _service_path(root, filename)
        if not path.exists():
            report.findings.append(ChainContractFinding("missing_file", f"Yasak desen kontrol dosyası eksik: {path.relative_to(root)}"))
            continue
        content = _read(path)
        for pattern in patterns:
            if re.search(pattern, content, flags=re.MULTILINE):
                report.findings.append(ChainContractFinding("forbidden_chain_pattern", f"Eski/yanlış zincir deseni bulundu: {path.relative_to(root)} :: {pattern}"))
            else:
                report.ok.append(f"Yasak zincir deseni yok: {path.relative_to(root)}")


def _check_literal_contracts(root: Path, report: ChainContractReport) -> None:
    chain_path = _service_path(root, "chain_rule_engine.py")
    if not chain_path.exists():
        report.findings.append(ChainContractFinding("missing_chain_engine", "chain_rule_engine.py bulunamadı."))
        return
    content = _read(chain_path)

    for constant, mapping in EXPECTED_SLOT_CONTRACT.items():
        if constant not in content:
            report.findings.append(ChainContractFinding("missing_slot_constant", f"Eksik slot sabiti: {constant}"))
            continue
        report.ok.append(f"Slot sabiti var: {constant}")
        for slot, value in mapping.items():
            token = f'{slot}: "{value}"'
            if token not in content:
                report.findings.append(ChainContractFinding("slot_contract_mismatch", f"{constant} için beklenen slot yok: {token}"))
            else:
                report.ok.append(f"{constant} :: {token}")

    for constant, flow in EXPECTED_FLOW_CONTRACT.items():
        if constant not in content:
            report.findings.append(ChainContractFinding("missing_flow_constant", f"Eksik akış sabiti: {constant}"))
            continue
        literal = "(" + ", ".join(str(item) for item in flow) + ("," if len(flow) == 1 else "") + ")"
        if literal not in content:
            report.findings.append(ChainContractFinding("flow_contract_mismatch", f"{constant} beklenen akışla bulunamadı: {literal}"))
        else:
            report.ok.append(f"{constant} :: {literal}")

    for constant, weights in EXPECTED_WEIGHT_CONTRACT.items():
        if constant not in content:
            report.findings.append(ChainContractFinding("missing_weight_constant", f"Eksik ağırlık sabiti: {constant}"))
            continue
        total = sum(weights.values())
        if round(total, 4) != 100.0:
            report.findings.append(ChainContractFinding("invalid_expected_weight_total", f"Gate beklenen ağırlık toplamı 100 değil: {constant}"))
        else:
            report.ok.append(f"{constant} beklenen toplam=100")
        for slot, value in weights.items():
            token = f"{slot}: {value:.1f}"
            if token not in content:
                report.findings.append(ChainContractFinding("weight_contract_mismatch", f"{constant} için beklenen ağırlık yok: {token}"))
            else:
                report.ok.append(f"{constant} :: {token}")

    for title in EXPECTED_DIRECT_PRESIDENT_TITLES:
        if title not in content:
            report.findings.append(ChainContractFinding("missing_direct_president_title", f"Başkanın tek başına puanladığı rol eksik: {title}"))
        else:
            report.ok.append(f"Tek Başkan özel rolü korunuyor: {title}")


def _check_snapshot_contract(root: Path, report: ChainContractReport) -> None:
    chain_path = _service_path(root, "chain_rule_engine.py")
    if not chain_path.exists():
        return
    content = _read(chain_path)
    required_snapshot_tokens = (
        '"group_staff": dict(GROUP_STAFF_SLOTS)',
        '"coordinator": dict(COORDINATOR_SLOTS)',
        '"group_manager": dict(GROUP_MANAGER_SLOTS)',
        '"single": list(DEFAULT_SINGLE_MANAGER_FLOW)',
        '"two_manager": list(DEFAULT_TWO_MANAGER_FLOW)',
        '"three_manager": list(DEFAULT_THREE_MANAGER_FLOW)',
        '"three_manager_comment_only": dict(THREE_MANAGER_COMMENT_WEIGHTS)',
        '"three_manager_scoring": dict(THREE_MANAGER_SCORING_WEIGHTS)',
    )
    for token in required_snapshot_tokens:
        if token in content:
            report.ok.append(f"Snapshot sözleşmesi korunuyor: {token}")
        else:
            report.findings.append(ChainContractFinding("snapshot_contract_missing", f"Snapshot çıktısında eksik sözleşme izi: {token}"))


def _check_phase_one_scope(root: Path, report: ChainContractReport) -> None:
    # Faz 1 sadece zincir sözleşme kapısıdır. Görev üretimi, yayın ve puanlama
    # Faz 2-4 içinde ayrıca denetlenecek. Burada bu kapsam ayrımı bilerek yazılır.
    report.ok.append("Faz 1 kapsamı davranış değiştirmeyen chain engine sözleşme kontrolü olarak sabit.")
    for rel in (
        "app/services/performance/assignment_builder.py",
        "app/services/performance/assignment_effective_chain.py",
        "app/services/performance/publish_preflight_rules.py",
        "app/services/performance/scoring.py",
    ):
        if (root / rel).exists():
            report.ok.append(f"Sonraki faz kapsam dosyası yerinde: {rel}")
        else:
            report.findings.append(ChainContractFinding("next_phase_file_missing", f"Sonraki faz kapsam dosyası eksik: {rel}", "warning"))


def build_chain_contract_gate_report(project_root: str | Path | None = None) -> ChainContractReport:
    root = Path(project_root or Path.cwd()).resolve()
    report = ChainContractReport()
    _check_tokens(root, report)
    _check_forbidden_patterns(root, report)
    _check_literal_contracts(root, report)
    _check_snapshot_contract(root, report)
    _check_phase_one_scope(root, report)
    return report


def format_chain_contract_report(report: ChainContractReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Performans Chain Engine Sözleşme Kapısı | {status}",
        f"version={report.version}",
        f"OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
        "",
        "Denetlenen ana sözleşmeler:",
        "- Çalışma grubu personeli: 1=Grup Başkanı, 2=Koordinatör, 3=varsa birim amiri, sıra 3→2→1",
        "- Koordinatör: 1=Başkan Yardımcısı, 2=Grup Başkanı, sıra 3→2→1 / 2→1",
        "- Grup Başkanı: 1=Başkan, 2=Başkan Yardımcısı, sıra 2→1",
        "- Hukuk ve özel Başkan rolleri: tek amirli / özel istisna sözleşmesi korunur",
        "- Kör değerlendirme kapalı, yayın kapısı ve önceki amir görünürlüğü açık",
    ]
    if report.findings:
        lines.append("")
        lines.append("Bulgular:")
        for finding in report.findings:
            lines.append(f"- {finding.severity.upper()} | {finding.code} | {finding.message}")
    return "\n".join(lines)


__all__ = [
    "CHAIN_CONTRACT_COMPILE_TARGETS",
    "CHAIN_CONTRACT_GATE_VERSION",
    "CHAIN_ENGINE_FORBIDDEN_PATTERNS",
    "CHAIN_ENGINE_REQUIRED_TOKENS",
    "EXPECTED_DIRECT_PRESIDENT_TITLES",
    "EXPECTED_FLOW_CONTRACT",
    "EXPECTED_SLOT_CONTRACT",
    "EXPECTED_WEIGHT_CONTRACT",
    "ChainContractFinding",
    "ChainContractReport",
    "build_chain_contract_gate_report",
    "format_chain_contract_report",
]
