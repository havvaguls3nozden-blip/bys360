
"""BYS360 Performans Amir Kural Matrisi Final Gate.

Bu modül canlı davranış değiştirmez. Nihai amir matrisi, görünürlük, yayın,
3. amir modu, ağırlık ve özel istisna kurallarının aktif kaynak dosyalarda
korunduğunu statik olarak doğrulamak için kullanılır.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Iterable
import importlib.util
import sys

FINAL_GATE_VERSION = "2026-04-20-performance-rule-matrix-final-gate-faz6"

PHASE_PLAN: tuple[tuple[str, str], ...] = (
    ("Faz 0", "Final Gate envanteri ve üst kalite kapısı"),
    ("Faz 1", "Chain engine sözleşme kapısı"),
    ("Faz 2", "Görev üretimi ve sahte bekleme kapısı"),
    ("Faz 3", "Görünürlük, yayın ve kör değerlendirme kapısı"),
    ("Faz 4", "Puanlama, ağırlık ve 3. amir modu kapısı"),
    ("Faz 5", "İzin, devamsızlık ve vekalet entegrasyon kapısı"),
    ("Faz 6", "UI/rapor terminoloji ve statü dili kapısı"),
    ("Faz 7", "Final regresyon paketi ve kapanış raporu"),
)

AUTHORITATIVE_MATRIX = {
    "group_staff": {
        "slot_1": "grup_baskani",
        "slot_2": "koordinator",
        "slot_3": "birim_amiri_optional",
        "flow": (3, 2, 1),
    },
    "coordinator": {
        "slot_1": "baskan_yardimcisi",
        "slot_2": "grup_baskani",
        "flow": (3, 2, 1),
    },
    "group_manager": {
        "slot_1": "baskan",
        "slot_2": "baskan_yardimcisi",
        "flow": (2, 1),
    },
    "hukuk_single_manager": {
        "slot_1": "bagli_hukuk_musaviri",
        "slot_2": None,
        "slot_3": None,
        "flow": (1,),
        "weights": (100.0, 0.0, 0.0),
    },
    "hukuk_chief_exception": {
        "slot_1": "baskan",
        "slot_2": "baskan_yardimcisi",
        "flow": (2, 1),
    },
    "direct_president_titles": {
        "titles": ("baskan_danismani", "ozel_kalem", "ic_denetci"),
        "flow": (1,),
        "weights": (100.0, 0.0, 0.0),
    },
}

REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance/chain_rule_engine.py": (
        "RULE_ENGINE_VERSION",
        "GROUP_STAFF_SLOTS",
        '1: "grup_baskani"',
        '2: "koordinator"',
        '3: "birim_amiri_optional"',
        "COORDINATOR_SLOTS",
        '1: "baskan_yardimcisi"',
        "GROUP_MANAGER_SLOTS",
        '1: "baskan"',
        '2: "baskan_yardimcisi"',
        "SPECIAL_DIRECT_PRESIDENT_TITLES",
        "baskan_danismani",
        "ozel_kalem",
        "ic_denetci",
        "DEFAULT_THREE_MANAGER_FLOW",
        "DEFAULT_TWO_MANAGER_FLOW",
        "DEFAULT_SINGLE_MANAGER_FLOW",
        "THREE_MANAGER_COMMENT_WEIGHTS",
        "THREE_MANAGER_SCORING_WEIGHTS",
        "blind_review_allowed",
        "employee_result_requires_publish",
        "next_manager_sees_previous_score_and_comment",
    ),
    "app/services/performance/rules.py": (
        "AUTHORITATIVE_PERFORMANCE_RULESET_VERSION",
        "LEVEL_3_DEFAULT_MODE",
        "LEVEL_3_ALLOWED_MODES",
        "BLIND_REVIEW_ALLOWED",
        "DEFAULT_TWO_MANAGER_WEIGHTS",
        "DEFAULT_THREE_MANAGER_SCORING_WEIGHTS",
        "LEAVE_PERFORMANCE_MODE_ALLOWED",
        "LEAVE_PERFORMANCE_MODE_DEFAULT",
        "INFO_REASON_HUKUK_SINGLE_MANAGER",
        "INFO_REASON_SPECIAL_SINGLE_MANAGER",
        "INFO_REASON_DELEGATED_ASSIGNMENT",
    ),
    "app/services/performance/visibility_guard.py": (
        "VISIBILITY_RULE_VERSION",
        "BLIND_REVIEW_ALLOWED = False",
        "is_employee_visible",
        "is_period_published",
        "is_employee_published",
        "build_evaluation_form_visibility_context",
        "blind_review_allowed",
    ),
    "app/services/performance/publish_preflight_rules.py": (
        "LOW_SCORE_THRESHOLD = 70.0",
        "HIGH_SCORE_THRESHOLD = 90.0",
        "1 veya 5 verilen kriterlerde açıklama/gerekçe zorunludur",
        "70 altı sonuçlarda ayrıntılı genel görüş zorunludur",
        "90 ve üstü sonuçlarda ayrıntılı genel görüş zorunludur",
        "level_3_comment_required",
        "Tek amirli",
    ),
    "app/services/performance/evaluation_form_service.py": (
        "3. amir yorumcu modunda genel görüş zorunludur",
        "1 veya 5 puan için açıklama zorunludur",
        "validate_general_comment_requirements",
    ),
    "app/services/performance/assignment_effective_chain.py": (
        "resolve_effective_evaluator",
        "ensure_assignment",
        "apply_effective_chain",
    ),
}

# Preserve the complete publish-preflight token contract in one explicit tuple.
REQUIRED_TOKENS["app/services/performance/publish_preflight_rules.py"] = (
    "LOW_SCORE_THRESHOLD = 70.0",
    "HIGH_SCORE_THRESHOLD = 90.0",
    "1 veya 5 verilen kriterlerde açıklama/gerekçe zorunludur",
    "70 altı sonuçlarda ayrıntılı genel görüş zorunludur",
    "90 ve üstü sonuçlarda ayrıntılı genel görüş zorunludur",
    "level_3_comment_required",
    "Tek amirli",
    "is_president_exempt",
    "period_requires_level_3",
    "level_3_comment_missing",
)

FORBIDDEN_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance/chain_rule_engine.py": (
        '1: "koordinator"',
        '1: "grup_baskani",\n    2: "baskan_yardimcisi"',
        "BLIND_REVIEW_ALLOWED = True",
    ),
    "app/services/performance/visibility_guard.py": (
        "BLIND_REVIEW_ALLOWED = True",
        "blind_review_allowed\": True",
    ),
    "app/templates/performance": (
        "Yetkinlik",
        "yetkinlik",
    ),
}

EXISTING_GATE_SCRIPTS: tuple[str, ...] = (
    "scripts/check_performance_chain_engine_gate.py",
    "scripts/check_performance_assignment_rule_gate.py",
    "scripts/check_performance_visibility_gate.py",
    "scripts/check_performance_publish_preflight_gate.py",
)

COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/chain_rule_engine.py",
    "app/services/performance/rules.py",
    "app/services/performance/visibility_guard.py",
    "app/services/performance/publish_preflight_rules.py",
    "app/services/performance/evaluation_form_service.py",
    "app/services/performance/rule_matrix_final_gate.py",
    "app/services/performance/chain_contract_gate.py",
    "app/services/performance/task_generation_gate.py",
    "app/services/performance/visibility_publication_gate.py",
    "app/services/performance/scoring_weight_gate.py",
    "app/services/performance/leave_delegation_gate.py",
    "app/services/performance/ui_report_language_gate.py",
    "scripts/check_performance_rule_matrix_final_gate.py",
    "scripts/check_performance_chain_contract_gate.py",
    "scripts/check_performance_task_generation_gate.py",
    "scripts/check_performance_visibility_publication_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz1_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz2_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz3_audit.py",
    "scripts/check_performance_scoring_weight_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz4_audit.py",
    "scripts/check_performance_leave_delegation_gate.py",
    "scripts/check_performance_ui_report_language_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz5_audit.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz6_audit.py",
)

@dataclass
class GateFinding:
    code: str
    message: str
    severity: str = "error"


@dataclass
class GateReport:
    version: str = FINAL_GATE_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[GateFinding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "warning")

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
            "findings": [finding.__dict__.copy() for finding in self.findings],
            "phase_plan": [{"phase": phase, "title": title} for phase, title in PHASE_PLAN],
        }


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    elif path.is_dir():
        for child in path.rglob("*"):
            if child.is_file() and child.suffix in {".py", ".html", ".jinja", ".jinja2"}:
                yield child


def _check_required_tokens(root: Path, report: GateReport) -> None:
    for rel, tokens in REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.findings.append(GateFinding("missing_file", f"Eksik dosya: {rel}"))
            continue
        content = _read(path)
        for token in tokens:
            if token not in content:
                report.findings.append(GateFinding("missing_required_token", f"Eksik zorunlu ifade: {rel} :: {token}"))
            else:
                report.ok.append(f"{rel} :: {token}")


def _check_forbidden_tokens(root: Path, report: GateReport) -> None:
    for rel, tokens in FORBIDDEN_TOKENS.items():
        path = root / rel
        if not path.exists():
            # Template klasörü yoksa bu final gate için kritik değil; üstteki aktif servisler daha belirleyici.
            report.ok.append(f"Yasak ifade alanı yok veya kapsam dışı: {rel}")
            continue
        for file_path in _iter_files(path):
            content = _read(file_path)
            for token in tokens:
                if token in content:
                    report.findings.append(GateFinding("forbidden_token", f"Yasak eski ifade: {file_path.relative_to(root)} :: {token}"))
                else:
                    report.ok.append(f"Yasak ifade yok: {file_path.relative_to(root)} :: {token}")


def _check_existing_gate_scripts(root: Path, report: GateReport) -> None:
    for rel in EXISTING_GATE_SCRIPTS:
        path = root / rel
        if path.exists():
            report.ok.append(f"Mevcut gate scripti var: {rel}")
        else:
            report.findings.append(GateFinding("missing_gate_script", f"Mevcut performans gate scripti eksik: {rel}", "warning"))


def _check_phase_plan(report: GateReport) -> None:
    if len(PHASE_PLAN) != 8:
        report.findings.append(GateFinding("phase_plan_count", "Final Gate faz planı 8 faz olmalı."))
    else:
        report.ok.append("Final Gate faz planı 8 faz olarak sabit.")

def _load_chain_contract_module(root: Path):
    service_path = root / "app" / "services" / "performance" / "chain_contract_gate.py"
    if not service_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("bys360_chain_contract_gate", service_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _check_chain_contract_gate(root: Path, report: GateReport) -> None:
    module = _load_chain_contract_module(root)
    if module is None:
        report.findings.append(GateFinding("missing_chain_contract_gate", "Faz 1 chain_contract_gate.py yüklenemedi."))
        return
    chain_report = module.build_chain_contract_gate_report(root)
    if chain_report.passed():
        report.ok.append(f"Faz 1 chain contract gate geçti: OK={len(chain_report.ok)}")
    for finding in chain_report.findings:
        report.findings.append(GateFinding(f"chain_contract.{finding.code}", finding.message, finding.severity))


def _load_task_generation_module(root: Path):
    service_path = root / "app" / "services" / "performance" / "task_generation_gate.py"
    if not service_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("bys360_task_generation_gate", service_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _check_task_generation_gate(root: Path, report: GateReport) -> None:
    module = _load_task_generation_module(root)
    if module is None:
        report.findings.append(GateFinding("missing_task_generation_gate", "Faz 2 task_generation_gate.py yüklenemedi."))
        return
    task_report = module.build_task_generation_gate_report(root)
    if task_report.passed():
        report.ok.append(f"Faz 2 task generation gate geçti: OK={len(task_report.ok)}")
    for finding in task_report.findings:
        report.findings.append(GateFinding(f"task_generation.{finding.code}", finding.message, finding.severity))

def _load_visibility_publication_module(root: Path):
    service_path = root / "app" / "services" / "performance" / "visibility_publication_gate.py"
    if not service_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("bys360_visibility_publication_gate", service_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _check_visibility_publication_gate(root: Path, report: GateReport) -> None:
    module = _load_visibility_publication_module(root)
    if module is None:
        report.findings.append(GateFinding("missing_visibility_publication_gate", "Faz 3 visibility_publication_gate.py yüklenemedi."))
        return
    visibility_report = module.build_visibility_publication_gate_report(root)
    if visibility_report.passed():
        report.ok.append(f"Faz 3 visibility/publication gate geçti: OK={len(visibility_report.ok)}")
    for finding in visibility_report.findings:
        report.findings.append(GateFinding(f"visibility_publication.{finding.code}", finding.message, finding.severity))

def _load_scoring_weight_module(root: Path):
    service_path = root / "app" / "services" / "performance" / "scoring_weight_gate.py"
    if not service_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("bys360_scoring_weight_gate", service_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _check_scoring_weight_gate(root: Path, report: GateReport) -> None:
    module = _load_scoring_weight_module(root)
    if module is None:
        report.findings.append(GateFinding("missing_scoring_weight_gate", "Faz 4 scoring_weight_gate.py yüklenemedi."))
        return
    scoring_report = module.build_scoring_weight_gate_report(root)
    if scoring_report.passed():
        report.ok.append(f"Faz 4 scoring/weight gate geçti: OK={len(scoring_report.ok)}")
    for finding in scoring_report.findings:
        report.findings.append(GateFinding(f"scoring_weight.{finding.code}", finding.message, finding.severity))


def _load_leave_delegation_module(root: Path):
    service_path = root / "app" / "services" / "performance" / "leave_delegation_gate.py"
    if not service_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("bys360_leave_delegation_gate", service_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _check_leave_delegation_gate(root: Path, report: GateReport) -> None:
    module = _load_leave_delegation_module(root)
    if module is None:
        report.findings.append(GateFinding("missing_leave_delegation_gate", "Faz 5 leave_delegation_gate.py yüklenemedi."))
        return
    leave_report = module.build_leave_delegation_gate_report(root)
    if leave_report.passed():
        report.ok.append(f"Faz 5 izin/devamsızlık/vekâlet gate geçti: OK={len(leave_report.ok)}")
    for finding in leave_report.findings:
        report.findings.append(GateFinding(f"leave_delegation.{finding.code}", finding.message, finding.severity))

def _load_ui_report_language_module(root: Path):
    service_path = root / "app" / "services" / "performance" / "ui_report_language_gate.py"
    if not service_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("bys360_ui_report_language_gate", service_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _check_ui_report_language_gate(root: Path, report: GateReport) -> None:
    module = _load_ui_report_language_module(root)
    if module is None:
        report.findings.append(GateFinding("missing_ui_report_language_gate", "Faz 6 ui_report_language_gate.py yüklenemedi."))
        return
    ui_report = module.build_ui_report_language_gate_report(root)
    if ui_report.passed():
        report.ok.append(f"Faz 6 UI/rapor terminoloji gate geçti: OK={len(ui_report.ok)}")
    for finding in ui_report.findings:
        report.findings.append(GateFinding(f"ui_report_language.{finding.code}", finding.message, finding.severity))

def build_performance_rule_matrix_final_gate_report(project_root: str | Path | None = None) -> GateReport:
    root = Path(project_root or Path.cwd()).resolve()
    report = GateReport()
    _check_phase_plan(report)
    _check_required_tokens(root, report)
    _check_forbidden_tokens(root, report)
    _check_existing_gate_scripts(root, report)
    _check_chain_contract_gate(root, report)
    _check_task_generation_gate(root, report)
    _check_visibility_publication_gate(root, report)
    _check_scoring_weight_gate(root, report)
    _check_leave_delegation_gate(root, report)
    _check_ui_report_language_gate(root, report)
    return report


def format_report(report: GateReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Performans Amir Kural Matrisi Final Gate | {status}",
        f"version={report.version}",
        f"OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
        "",
        "Faz planı:",
    ]
    for phase, title in PHASE_PLAN:
        lines.append(f"- {phase}: {title}")
    if report.findings:
        lines.append("")
        lines.append("Bulgular:")
        for finding in report.findings:
            lines.append(f"- {finding.severity.upper()} | {finding.code} | {finding.message}")
    return "\n".join(lines)


__all__ = [
    "AUTHORITATIVE_MATRIX",
    "COMPILE_TARGETS",
    "EXISTING_GATE_SCRIPTS",
    "FINAL_GATE_VERSION",
    "PHASE_PLAN",
    "GateFinding",
    "GateReport",
    "build_performance_rule_matrix_final_gate_report",
    "_check_chain_contract_gate",
    "_check_task_generation_gate",
    "_check_visibility_publication_gate",
    "_check_scoring_weight_gate",
    "_check_leave_delegation_gate",
    "_check_ui_report_language_gate",
    "format_report",
]
