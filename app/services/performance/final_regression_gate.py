from __future__ import annotations

import logging

"""BYS360 Performans Amir Kural Matrisi Final Regresyon Kapısı.

Bu modül canlı davranış değiştirmez. Faz 0-6 boyunca eklenen tüm performans
amir kural matrisi kapılarını tek bir kapanış denetimi altında toplar.
"""

import importlib.util
import py_compile
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

FINAL_REGRESSION_GATE_VERSION = "2026-04-20-performance-rule-matrix-final-regression-faz7"

FINAL_PHASES: tuple[tuple[str, str, str], ...] = (
    ("Faz 0", "Final Gate envanteri ve üst kalite kapısı", "rule_matrix"),
    ("Faz 1", "Chain engine sözleşme kapısı", "chain_contract"),
    ("Faz 2", "Görev üretimi ve sahte bekleme kapısı", "task_generation"),
    ("Faz 3", "Görünürlük, yayın ve kör değerlendirme kapısı", "visibility_publication"),
    ("Faz 4", "Puanlama, ağırlık ve 3. amir modu kapısı", "scoring_weight"),
    ("Faz 5", "İzin, devamsızlık ve vekâlet entegrasyon kapısı", "leave_delegation"),
    ("Faz 6", "UI/rapor terminoloji ve statü dili kapısı", "ui_report_language"),
    ("Faz 7", "Final regresyon paketi ve kapanış raporu", "final_regression"),
)

GATE_MODULES: dict[str, tuple[str, str, str]] = {
    "rule_matrix": (
        "app/services/performance/rule_matrix_final_gate.py",
        "build_performance_rule_matrix_final_gate_report",
        "format_report",
    ),
    "chain_contract": (
        "app/services/performance/chain_contract_gate.py",
        "build_chain_contract_gate_report",
        "format_chain_contract_report",
    ),
    "task_generation": (
        "app/services/performance/task_generation_gate.py",
        "build_task_generation_gate_report",
        "format_task_generation_report",
    ),
    "visibility_publication": (
        "app/services/performance/visibility_publication_gate.py",
        "build_visibility_publication_gate_report",
        "format_visibility_publication_report",
    ),
    "scoring_weight": (
        "app/services/performance/scoring_weight_gate.py",
        "build_scoring_weight_gate_report",
        "format_scoring_weight_report",
    ),
    "leave_delegation": (
        "app/services/performance/leave_delegation_gate.py",
        "build_leave_delegation_gate_report",
        "format_leave_delegation_report",
    ),
    "ui_report_language": (
        "app/services/performance/ui_report_language_gate.py",
        "build_ui_report_language_gate_report",
        "format_ui_report_language_report",
    ),
}

FINAL_REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/check_performance_rule_matrix_final_gate.py",
    "scripts/check_performance_chain_contract_gate.py",
    "scripts/check_performance_task_generation_gate.py",
    "scripts/check_performance_visibility_publication_gate.py",
    "scripts/check_performance_scoring_weight_gate.py",
    "scripts/check_performance_leave_delegation_gate.py",
    "scripts/check_performance_ui_report_language_gate.py",
    "scripts/check_performance_final_regression_gate.py",
)

FINAL_REQUIRED_AUDITS: tuple[str, ...] = (
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz1_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz2_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz3_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz4_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz5_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz6_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz7_audit.py",
)

FINAL_COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/rule_matrix_final_gate.py",
    "app/services/performance/chain_contract_gate.py",
    "app/services/performance/task_generation_gate.py",
    "app/services/performance/visibility_publication_gate.py",
    "app/services/performance/scoring_weight_gate.py",
    "app/services/performance/leave_delegation_gate.py",
    "app/services/performance/ui_report_language_gate.py",
    "app/services/performance/final_regression_gate.py",
    "scripts/check_performance_rule_matrix_final_gate.py",
    "scripts/check_performance_chain_contract_gate.py",
    "scripts/check_performance_task_generation_gate.py",
    "scripts/check_performance_visibility_publication_gate.py",
    "scripts/check_performance_scoring_weight_gate.py",
    "scripts/check_performance_leave_delegation_gate.py",
    "scripts/check_performance_ui_report_language_gate.py",
    "scripts/check_performance_final_regression_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz1_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz2_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz3_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz4_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz5_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz6_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz7_audit.py",
)

@dataclass
class FinalRegressionFinding:
    code: str
    message: str
    severity: str = "error"

@dataclass
class FinalRegressionReport:
    version: str = FINAL_REGRESSION_GATE_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[FinalRegressionFinding] = field(default_factory=list)
    gate_summaries: dict[str, dict[str, Any]] = field(default_factory=dict)
    compile_targets: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.findings if item.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.findings if item.severity == "warning")

    def passed(self) -> bool:
        return self.error_count == 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "passed": self.passed(),
            "ok_count": len(self.ok),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "ok": list(self.ok),
            "findings": [item.__dict__.copy() for item in self.findings],
            "gate_summaries": self.gate_summaries,
            "compile_targets": list(self.compile_targets),
            "final_phases": [
                {"phase": phase, "title": title, "gate": gate}
                for phase, title, gate in FINAL_PHASES
            ],
        }


def _load_module(root: Path, rel: str, name: str):
    path = root / rel
    if not path.exists():
        raise FileNotFoundError(rel)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Servis yüklenemedi: {rel}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _check_phase_plan(report: FinalRegressionReport) -> None:
    if len(FINAL_PHASES) != 8:
        report.findings.append(FinalRegressionFinding("phase_count", "Final regresyon planı 8 faz olmalı."))
        return
    expected = tuple(f"Faz {idx}" for idx in range(8))
    actual = tuple(phase for phase, _, _ in FINAL_PHASES)
    if actual != expected:
        report.findings.append(FinalRegressionFinding("phase_order", f"Final regresyon faz sırası hatalı: {actual}"))
    else:
        report.ok.append("Final regresyon faz planı Faz 0-7 sırasıyla tamam.")


def _check_required_files(root: Path, report: FinalRegressionReport) -> None:
    for rel in FINAL_REQUIRED_SCRIPTS + FINAL_REQUIRED_AUDITS:
        if (root / rel).exists():
            report.ok.append(f"Final dosya var: {rel}")
        else:
            report.findings.append(FinalRegressionFinding("missing_final_file", f"Final dosya eksik: {rel}"))


def _run_gate_modules(root: Path, report: FinalRegressionReport) -> None:
    for gate_key, (rel, build_name, _format_name) in GATE_MODULES.items():
        try:
            module = _load_module(root, rel, f"bys360_{gate_key}_final_regression")
            build = getattr(module, build_name)
            gate_report = build(root)
        except Exception as exc:  # noqa: BLE001 - audit aracı; hata raporlanır.
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/final_regression_gate.py:198)")
            report.findings.append(FinalRegressionFinding("gate_load_or_run_failed", f"{gate_key} çalıştırılamadı: {exc}"))
            continue

        gate_dict = gate_report.as_dict() if hasattr(gate_report, "as_dict") else {
            "passed": bool(getattr(gate_report, "passed", lambda: False)()),
            "ok_count": len(getattr(gate_report, "ok", [])),
            "error_count": getattr(gate_report, "error_count", 0),
            "warning_count": getattr(gate_report, "warning_count", 0),
        }
        report.gate_summaries[gate_key] = gate_dict
        if bool(gate_report.passed()):
            report.ok.append(f"{gate_key} geçti: OK={len(getattr(gate_report, 'ok', []))}")
        for finding in getattr(gate_report, "findings", []):
            report.findings.append(
                FinalRegressionFinding(
                    f"{gate_key}.{getattr(finding, 'code', 'finding')}",
                    getattr(finding, "message", str(finding)),
                    getattr(finding, "severity", "error"),
                )
            )


def _compile_targets(root: Path, report: FinalRegressionReport) -> None:
    targets = list(dict.fromkeys(FINAL_COMPILE_TARGETS))
    report.compile_targets = targets
    for rel in targets:
        target = root / rel
        if not target.exists():
            report.findings.append(FinalRegressionFinding("missing_compile_target", f"Compile hedefi eksik: {rel}"))
            continue
        try:
            py_compile.compile(str(target), doraise=True)
            report.ok.append(f"py_compile temiz: {rel}")
        except py_compile.PyCompileError as exc:
            report.findings.append(FinalRegressionFinding("py_compile_failed", f"{rel}: {exc.msg}"))


def build_final_regression_gate_report(project_root: str | Path | None = None) -> FinalRegressionReport:
    root = Path(project_root or Path.cwd()).resolve()
    report = FinalRegressionReport()
    _check_phase_plan(report)
    _check_required_files(root, report)
    _run_gate_modules(root, report)
    _compile_targets(root, report)
    return report


def format_final_regression_report(report: FinalRegressionReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Performans Amir Kural Matrisi Final Regresyon Gate | {status}",
        f"version={report.version}",
        f"OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
        "",
        "Kapanan fazlar:",
    ]
    for phase, title, gate in FINAL_PHASES:
        summary = report.gate_summaries.get(gate, {})
        gate_status = "OK" if gate == "final_regression" or summary.get("passed") is True else "KONTROL"
        lines.append(f"- {phase}: {title} [{gate_status}]")
    if report.findings:
        lines.append("")
        lines.append("Bulgular:")
        for finding in report.findings:
            lines.append(f"- {finding.severity.upper()} | {finding.code} | {finding.message}")
    return "\n".join(lines)


__all__ = [
    "FINAL_COMPILE_TARGETS",
    "FINAL_PHASES",
    "FINAL_REGRESSION_GATE_VERSION",
    "FINAL_REQUIRED_AUDITS",
    "FINAL_REQUIRED_SCRIPTS",
    "FinalRegressionFinding",
    "FinalRegressionReport",
    "build_final_regression_gate_report",
    "format_final_regression_report",
]
