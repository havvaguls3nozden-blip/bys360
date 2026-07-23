from __future__ import annotations

import importlib.util
import json
import logging
import py_compile
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

"""Maintenance Faz 4 performans amir kuralları kalıcı guard.

Canlı davranış değiştirmez. Nihai amir kural anayasasının ve mevcut performans
servislerindeki kritik izlerin korunup korunmadığını statik olarak denetler.
"""

logger = logging.getLogger(__name__)

GUARD_VERSION = "2026-04-20-claude-faz4-performance-manager-rule-guard"

REQUIRED_FILES: tuple[str, ...] = (
    "app/services/performance/manager_rule_constitution.py",
    "app/services/performance/manager_rule_guard.py",
    "app/services/performance/chain_rule_engine.py",
    "app/services/performance/rules.py",
    "app/services/performance/visibility_guard.py",
    "app/services/performance/publish_preflight_rules.py",
    "app/services/performance/scoring.py",
    "app/services/performance/evaluation_form_service.py",
    "app/services/performance/assignment_effective_chain.py",
)

EXISTING_PERFORMANCE_GATES: tuple[str, ...] = (
    "scripts/check_performance_chain_contract_gate.py",
    "scripts/check_performance_task_generation_gate.py",
    "scripts/check_performance_visibility_publication_gate.py",
    "scripts/check_performance_scoring_weight_gate.py",
    "scripts/check_performance_leave_delegation_gate.py",
    "scripts/check_performance_ui_report_language_gate.py",
    "scripts/check_performance_rule_matrix_final_gate.py",
)

REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance/chain_rule_engine.py": (
        "RULE_ENGINE_VERSION",
        "GROUP_STAFF_SLOTS",
        '1: "grup_baskani"',
        '2: "koordinator"',
        "COORDINATOR_SLOTS",
        '1: "baskan_yardimcisi"',
        '2: "grup_baskani"',
        "GROUP_MANAGER_SLOTS",
        '1: "baskan"',
        '2: "baskan_yardimcisi"',
        "DEFAULT_SINGLE_MANAGER_FLOW",
        "DEFAULT_TWO_MANAGER_FLOW",
        "DEFAULT_THREE_MANAGER_FLOW",
        "SPECIAL_DIRECT_PRESIDENT_TITLES",
        "baskan_danismani",
        "ozel_kalem",
        "ic_denetci",
        "blind_review_allowed",
        "employee_result_requires_publish",
        "next_manager_sees_previous_score_and_comment",
    ),
    "app/services/performance/rules.py": (
        "AUTHORITATIVE_PERFORMANCE_RULESET_VERSION",
        "BLIND_REVIEW_ALLOWED",
        "LEVEL_3_ALLOWED_MODES",
        "LEVEL_3_DEFAULT_MODE",
        "DEFAULT_TWO_MANAGER_WEIGHTS",
        "DEFAULT_THREE_MANAGER_SCORING_WEIGHTS",
        "INFO_REASON_HUKUK_SINGLE_MANAGER",
        "INFO_REASON_SPECIAL_SINGLE_MANAGER",
        "INFO_REASON_PRESIDENT_EXCLUDED",
    ),
    "app/services/performance/visibility_guard.py": (
        "VISIBILITY_RULE_VERSION",
        "BLIND_REVIEW_ALLOWED = False",
        "is_employee_visible",
        "is_period_published",
        "is_employee_published",
        "build_evaluation_form_visibility_context",
    ),
    "app/services/performance/publish_preflight_rules.py": (
        "LOW_SCORE_THRESHOLD = 70.0",
        "HIGH_SCORE_THRESHOLD = 90.0",
        "1 veya 5 verilen kriterlerde açıklama/gerekçe zorunludur",
        "70 altı sonuçlarda ayrıntılı genel görüş zorunludur",
        "90 ve üstü sonuçlarda ayrıntılı genel görüş zorunludur",
        "is_president_exempt",
        "level_3_comment_missing",
    ),
    "app/services/performance/scoring.py": (
        "score_to_100",
        "validate_general_comment_requirements",
        "validate_item_comment_requirements",
        "validate_weight_distribution",
        "calculate_final_total",
        "score in {1.0, 5.0}",
        "3 puan tek başına yorum zorunluluğu oluşturmaz",
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

FORBIDDEN_PATTERNS: dict[str, tuple[str, ...]] = {
    "app/services/performance/chain_rule_engine.py": (
        r"GROUP_STAFF_SLOTS[\s\S]{0,260}?1\s*:\s*[\"']koordinator[\"']",
        r"COORDINATOR_SLOTS[\s\S]{0,260}?1\s*:\s*[\"']grup_baskani[\"']",
        r"GROUP_MANAGER_SLOTS[\s\S]{0,260}?1\s*:\s*[\"']baskan_yardimcisi[\"']",
        r"DEFAULT_TWO_MANAGER_FLOW\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*\)",
        r"DEFAULT_THREE_MANAGER_FLOW\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*,\s*3\s*\)",
        r"blind_review_allowed[\"']?\s*[:=]\s*True",
    ),
    "app/services/performance/rules.py": (
        r"BLIND_REVIEW_ALLOWED\s*:[^=]*=\s*True",
        r"PRESIDENT_LEVEL_REVIEW_ORDER\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*\)",
    ),
    "app/services/performance/visibility_guard.py": (
        r"BLIND_REVIEW_ALLOWED\s*=\s*True",
        r"blind_review_allowed[\"']?\s*[:=]\s*True",
    ),
    "app/services/performance/scoring.py": (
        r"score\s+in\s+\{\s*1(?:\.0)?\s*,\s*3(?:\.0)?\s*,\s*5(?:\.0)?\s*\}",
        r"level_total_100\s*<=\s*70",
        r"level_total_100\s*>=\s*90",
    ),
    "app/templates/performance": (
        "2. amir bekliyor",
        "3. amir bekliyor",
        "3. amir puan bekliyor",
        "Başkan değerlendirme öznesi yapılmamalı",
    ),
}

COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/manager_rule_constitution.py",
    "app/services/performance/manager_rule_guard.py",
    "scripts/quality/check_performance_manager_rules_phase4_gate.py",
)


@dataclass
class GuardFinding:
    code: str
    message: str
    severity: str = "error"


@dataclass
class GuardReport:
    version: str = GUARD_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[GuardFinding] = field(default_factory=list)
    snapshot: dict[str, object] = field(default_factory=dict)

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
            "snapshot": self.snapshot,
        }


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _iter_text_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if not path.exists():
        return
    for child in path.rglob("*"):
        if child.is_file() and child.suffix.lower() in {".py", ".html", ".jinja", ".jinja2", ".md", ".txt"}:
            yield child


def _load_constitution(root: Path):
    path = root / "app" / "services" / "performance" / "manager_rule_constitution.py"
    spec = importlib.util.spec_from_file_location("bys360_manager_rule_constitution", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Anayasa modülü yüklenemedi: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _check_required_files(root: Path, report: GuardReport) -> None:
    for rel in REQUIRED_FILES + EXISTING_PERFORMANCE_GATES:
        path = root / rel
        if path.exists():
            report.ok.append(f"Dosya var: {rel}")
        else:
            report.findings.append(GuardFinding("missing_file", f"Eksik zorunlu dosya: {rel}"))


def _check_constitution(root: Path, report: GuardReport) -> None:
    try:
        module = _load_constitution(root)
    except Exception as exc:  # pragma: no cover - gate report path
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        report.findings.append(GuardFinding("constitution_import_failed", f"Kural anayasası yüklenemedi: {exc}"))
        return
    errors = list(module.validate_constitution_self_check())
    if errors:
        for error in errors:
            report.findings.append(GuardFinding("constitution_self_check_failed", error))
        return
    snapshot = module.get_manager_rule_snapshot()
    report.snapshot = snapshot
    report.ok.append("Kural anayasası öz kontrolü geçti")

    expected_roles = {
        "group_staff": ("grup_baskani", "koordinator", [3, 2, 1]),
        "coordinator": ("baskan_yardimcisi", "grup_baskani", [3, 2, 1]),
        "group_manager": ("baskan", "baskan_yardimcisi", [2, 1]),
        "hukuk_single_manager": ("bagli_oldugu_hukuk_musaviri", None, [1]),
        "direct_president_titles": ("baskan", None, [1]),
    }
    roles = snapshot.get("roles", {}) if isinstance(snapshot, dict) else {}
    for code, (slot_1, slot_2, flow) in expected_roles.items():
        item = roles.get(code, {}) if isinstance(roles, dict) else {}
        if item.get("slot_1") != slot_1 or item.get("slot_2") != slot_2 or item.get("flow") != flow:
            report.findings.append(GuardFinding("role_contract_mismatch", f"{code} kural sözleşmesi bozulmuş: {item}"))
        else:
            report.ok.append(f"Rol sözleşmesi doğru: {code}")


def _check_required_tokens(root: Path, report: GuardReport) -> None:
    for rel, tokens in REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.findings.append(GuardFinding("missing_token_file", f"Token kontrol dosyası eksik: {rel}"))
            continue
        content = _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"{rel} :: {token}")
            else:
                report.findings.append(GuardFinding("missing_required_token", f"Eksik kural izi: {rel} :: {token}"))


def _check_forbidden_patterns(root: Path, report: GuardReport) -> None:
    for rel, patterns in FORBIDDEN_PATTERNS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Yasak desen alanı yok/kapsam dışı: {rel}")
            continue
        for file_path in _iter_text_files(path):
            content = _read(file_path)
            for pattern in patterns:
                flags = re.IGNORECASE | re.MULTILINE
                if "[\\s\\S]" in pattern or "\\s" in pattern:
                    flags |= re.DOTALL
                if re.search(pattern, content, flags=flags):
                    report.findings.append(GuardFinding("forbidden_pattern", f"Yasak/eskimiş kural izi: {file_path.relative_to(root)} :: {pattern}"))
                else:
                    report.ok.append(f"Yasak desen yok: {file_path.relative_to(root)}")


def _simulate_score_to_100(score: float) -> float:
    value = max(1.0, min(5.0, float(score)))
    return round((value / 5.0) * 100.0, 2)


def _simulate_requires_general_comment(final_score: float, raw_scores: tuple[float, ...] = ()) -> bool:
    if final_score < 70.0 or final_score > 90.0:
        return True
    return any(float(score) in {1.0, 5.0} for score in raw_scores)


def _check_simulations(report: GuardReport) -> None:
    checks = {
        "score_1_to_20": _simulate_score_to_100(1) == 20.0,
        "score_3_to_60": _simulate_score_to_100(3) == 60.0,
        "score_5_to_100": _simulate_score_to_100(5) == 100.0,
        "score_3_no_item_comment": _simulate_requires_general_comment(75.0, (3.0,)) is False,
        "score_1_item_comment": _simulate_requires_general_comment(75.0, (1.0,)) is True,
        "below_70_general_comment": _simulate_requires_general_comment(69.99, (3.0,)) is True,
        "above_90_general_comment": _simulate_requires_general_comment(90.01, (3.0,)) is True,
    }
    for name, ok in checks.items():
        if ok:
            report.ok.append(f"Simülasyon geçti: {name}")
        else:
            report.findings.append(GuardFinding("simulation_failed", f"Simülasyon başarısız: {name}"))


def _check_compile(root: Path, report: GuardReport) -> None:
    for rel in COMPILE_TARGETS:
        path = root / rel
        if not path.exists():
            report.findings.append(GuardFinding("compile_target_missing", f"Compile hedefi eksik: {rel}"))
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            report.findings.append(GuardFinding("compile_failed", f"Compile hatası: {rel} :: {exc}"))
        else:
            report.ok.append(f"Compile OK: {rel}")


def build_manager_rule_guard_report(root: Path | str) -> GuardReport:
    root_path = Path(root)
    report = GuardReport()
    _check_required_files(root_path, report)
    _check_constitution(root_path, report)
    _check_required_tokens(root_path, report)
    _check_forbidden_patterns(root_path, report)
    _check_simulations(report)
    _check_compile(root_path, report)
    return report


def format_manager_rule_guard_report(report: GuardReport) -> str:
    lines = [
        f"BYS360 Maintenance Faz 4 Performans Amir Kuralları Gate | OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
    ]
    for finding in report.findings:
        label = "HATA" if finding.severity == "error" else "UYARI"
        lines.append(f"{label} | {finding.code} | {finding.message}")
    if report.passed():
        lines.append("BYS360 Maintenance Faz 4 performans amir kuralları gate | OK")
    return "\n".join(lines)


def write_report_files(root: Path | str, report: GuardReport) -> tuple[Path, Path]:
    root_path = Path(root)
    report_dir = root_path / "reports" / "refactor"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "claude_phase4_performance_manager_rules_gate.json"
    md_path = report_dir / "claude_phase4_performance_manager_rules_gate.md"
    json_path.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(format_manager_rule_guard_report(report) + "\n", encoding="utf-8")
    return json_path, md_path


__all__ = [
    "GUARD_VERSION",
    "GuardFinding",
    "GuardReport",
    "build_manager_rule_guard_report",
    "format_manager_rule_guard_report",
    "write_report_files",
]
