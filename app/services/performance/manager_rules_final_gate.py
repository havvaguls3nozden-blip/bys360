from __future__ import annotations


import logging

"""BYS360 Performans Amir Kuralları Final Gate.

Canlı davranış değiştirmez. Mevcut performans alt gate'lerini tek kapanış
raporunda toplar ve nihai amir kural sözleşmesini statik olarak denetler.
"""

from dataclasses import dataclass, field
from pathlib import Path
import json
import os
import py_compile
import re
import subprocess
import sys
logger = logging.getLogger(__name__)

FINAL_GATE_VERSION = "2026-04-21-performance-manager-rules-final-gate"

SUBGATE_SCRIPTS: tuple[tuple[str, str, str], ...] = (
    ("chain_contract", "Chain engine sözleşme kapısı", "scripts/check_performance_chain_contract_gate.py"),
    ("rule_matrix", "Kural matrisi final kapısı", "scripts/check_performance_rule_matrix_final_gate.py"),
    ("task_generation", "Görev üretimi ve sahte bekleme kapısı", "scripts/check_performance_task_generation_gate.py"),
    ("visibility_publication", "Görünürlük, yayın ve kör değerlendirme kapısı", "scripts/check_performance_visibility_publication_gate.py"),
    ("scoring_weight", "Puanlama, açıklama ve ağırlık kapısı", "scripts/check_performance_scoring_weight_gate.py"),
    ("leave_delegation", "İzin, devamsızlık ve vekâlet entegrasyon kapısı", "scripts/check_performance_leave_delegation_gate.py"),
    ("ui_report_language", "UI/rapor terminoloji ve statü dili kapısı", "scripts/check_performance_ui_report_language_gate.py"),
    ("final_regression", "Final regresyon ve kapanış raporu", "scripts/check_performance_final_regression_gate.py"),
)

COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/manager_rule_constitution.py",
    "app/services/performance/chain_rule_engine.py",
    "app/services/performance/rules.py",
    "app/services/performance/task_generation_gate.py",
    "app/services/performance/visibility_publication_gate.py",
    "app/services/performance/scoring_weight_gate.py",
    "app/services/performance/leave_delegation_gate.py",
    "app/services/performance/ui_report_language_gate.py",
    "app/services/performance/final_regression_gate.py",
    "app/services/performance/manager_rules_final_gate.py",
    "scripts/check_performance_manager_rules_final_gate.py",
)

REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance/manager_rule_constitution.py": (
        "BLIND_REVIEW_ALLOWED: bool = False",
        "NEXT_MANAGER_SEES_PREVIOUS_SCORE_AND_COMMENT: bool = True",
        "EMPLOYEE_RESULT_REQUIRES_PUBLISH: bool = True",
        "COMMENT_REQUIRED_FOR_SCORES: tuple[int, int] = (1, 5)",
        "LOW_SCORE_THRESHOLD: float = 70.0",
        "HIGH_SCORE_THRESHOLD: float = 90.0",
        "DEFAULT_TWO_MANAGER_FLOW: tuple[int, ...] = (2, 1)",
        "DEFAULT_THREE_MANAGER_FLOW: tuple[int, ...] = (3, 2, 1)",
        "LEVEL_3_ALLOWED_MODES: tuple[str, ...] = (\"off\", \"comment_only\", \"scoring\")",
        "THREE_MANAGER_COMMENT_WEIGHTS: Mapping[int, float] = {1: 50.0, 2: 50.0, 3: 0.0}",
        "THREE_MANAGER_SCORING_WEIGHTS: Mapping[int, float] = {1: 40.0, 2: 40.0, 3: 20.0}",
        "MAIN_CRITERIA_TERM = \"Değerlendirme Kriterleri\"",
        "FORBIDDEN_MAIN_TERM = \"Yetkinlik\"",
        "hukuk_single_manager",
        "hukuk_chief_exception",
        "direct_president_titles",
    ),
    "app/services/performance/chain_rule_engine.py": (
        "GROUP_STAFF_SLOTS",
        "1: \"grup_baskani\"",
        "2: \"koordinator\"",
        "COORDINATOR_SLOTS",
        "1: \"baskan_yardimcisi\"",
        "2: \"grup_baskani\"",
        "GROUP_MANAGER_SLOTS",
        "1: \"baskan\"",
        "2: \"baskan_yardimcisi\"",
        "DEFAULT_TWO_MANAGER_FLOW: tuple[int, int] = (2, 1)",
        "DEFAULT_THREE_MANAGER_FLOW: tuple[int, int, int] = (3, 2, 1)",
        "DEFAULT_SINGLE_MANAGER_FLOW: tuple[int, ...] = (1,)",
        "THREE_MANAGER_COMMENT_WEIGHTS: Mapping[int, float] = {1: 50.0, 2: 50.0, 3: 0.0}",
        "THREE_MANAGER_SCORING_WEIGHTS: Mapping[int, float] = {1: 40.0, 2: 40.0, 3: 20.0}",
        "blind_review_allowed",
        "employee_result_requires_publish",
        "next_manager_sees_previous_score_and_comment",
    ),
    "app/services/performance/rules.py": (
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
    "app/services/performance/task_generation_gate.py": (
        "2. amir bekliyor",
        "3. amir bekliyor",
        "Başkan değerlendirme öznesi yapılmamalı",
        "3. amir yorumcu modunda",
        "Başkan değerlendirme öznesi yapılmamalı",
    ),
    "app/services/performance/visibility_publication_gate.py": (
        "employee_visibility_requires",
        "previous_manager_score_visible",
        "visible_previous_levels",
        "can_see_previous_scores",
        "is_employee_published",
    ),
    "app/services/performance/scoring_weight_gate.py": (
        "simulate_requires_general_comment",
        "LOW_SCORE_THRESHOLD = 70.0",
        "HIGH_SCORE_THRESHOLD = 90.0",
        "THREE_MANAGER_COMMENT_WEIGHTS",
        "THREE_MANAGER_SCORING_WEIGHTS",
    ),
    "app/services/performance/leave_delegation_gate.py": (
        "aynı seviyedeki vekile",
        "delegated",
        "uncovered",
        "exempted",
        "simulate_assignment_levels",
    ),
    "app/services/performance/ui_report_language_gate.py": (
        "Değerlendirme Kriterleri",
        "Personel Analizi",
        "Sonuçlar yayımlandı",
        "yorum/görüş bekliyor",
    ),
}

FORBIDDEN_PATTERNS: dict[str, tuple[str, ...]] = {
    "app/services/performance/manager_rule_constitution.py": (
        r"BLIND_REVIEW_ALLOWED\s*:[^=]*=\s*True",
        r"COMMENT_REQUIRED_FOR_SCORES\s*:[^=]*=\s*\([^)]*3",
        r"DEFAULT_TWO_MANAGER_FLOW\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*\)",
        r"DEFAULT_THREE_MANAGER_FLOW\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*,\s*3\s*\)",
        r"LEVEL_3_DEFAULT_MODE\s*:[^=]*=\s*[\"']scoring[\"']",
    ),
    "app/services/performance/chain_rule_engine.py": (
        r"GROUP_STAFF_SLOTS[\s\S]{0,260}?1\s*:\s*[\"']koordinator[\"']",
        r"COORDINATOR_SLOTS[\s\S]{0,220}?1\s*:\s*[\"']grup_baskani[\"']",
        r"GROUP_MANAGER_SLOTS[\s\S]{0,220}?1\s*:\s*[\"']baskan_yardimcisi[\"']",
        r"DEFAULT_TWO_MANAGER_FLOW\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*\)",
        r"DEFAULT_THREE_MANAGER_FLOW\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*,\s*3\s*\)",
    ),
    "app/services/performance/rules.py": (
        r"BLIND_REVIEW_ALLOWED\s*:[^=]*=\s*True",
        r"PRESIDENT_LEVEL_REVIEW_ORDER\s*:[^=]*=\s*\(\s*1\s*,\s*2\s*\)",
    ),
}

REFERENCE_DOCS: tuple[str, ...] = (
    "docs/refactor/SQL_REFACTOR_FAZ8.md",
    "docs/refactor/generated/sql_refactor_faz8_final_audit.md",
    "docs/performance",
)


@dataclass
class Finding:
    code: str
    message: str
    severity: str = "error"


@dataclass
class Subgate:
    code: str
    title: str
    passed: bool
    exit_code: int
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass
class FinalReport:
    version: str = FINAL_GATE_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    subgates: list[Subgate] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.findings if item.severity == "error") + sum(0 if item.passed else 1 for item in self.subgates)

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
            "ok": self.ok,
            "findings": [item.__dict__.copy() for item in self.findings],
            "subgates": [item.as_dict() for item in self.subgates],
        }


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _one_line(text: str) -> str:
    for line in text.splitlines():
        clean = " ".join(line.split())
        if clean:
            return clean[:260]
    return ""


def _subgate_detail(stdout: str, stderr: str) -> str:
    """Alt gate çıktısını tek satırda, Windows kod sayfasına takılmadan özetler."""
    out_first = _one_line(stdout)
    err_lines = [" ".join(line.split()) for line in (stderr or "").splitlines() if " ".join(line.split())]
    if not err_lines:
        return out_first
    err_last = err_lines[-1][:260]
    if out_first:
        return f"{out_first} | stderr: {err_last}"[:520]
    return err_last


def _check_compile(root: Path, report: FinalReport) -> None:
    for rel in COMPILE_TARGETS:
        path = root / rel
        if not path.exists():
            report.findings.append(Finding("missing_compile_target", f"Derleme hedefi eksik: {rel}"))
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            report.ok.append(f"Derleme temiz: {rel}")
        except Exception as exc:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            report.findings.append(Finding("compile_error", f"{rel} derlenemedi: {exc}"))


def _check_required_tokens(root: Path, report: FinalReport) -> None:
    for rel, tokens in REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.findings.append(Finding("missing_required_file", f"Zorunlu dosya eksik: {rel}"))
            continue
        content = _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"Sözleşme izi korundu: {rel} :: {token}")
            else:
                report.findings.append(Finding("missing_required_token", f"Eksik sözleşme izi: {rel} :: {token}"))


def _check_forbidden(root: Path, report: FinalReport) -> None:
    for rel, patterns in FORBIDDEN_PATTERNS.items():
        path = root / rel
        if not path.exists():
            report.findings.append(Finding("missing_forbidden_scan_file", f"Yasak desen tarama dosyası eksik: {rel}"))
            continue
        content = _read(path)
        for pattern in patterns:
            if re.search(pattern, content, flags=re.MULTILINE):
                report.findings.append(Finding("forbidden_pattern", f"Eski/yanlış kural deseni bulundu: {rel} :: {pattern}"))
            else:
                report.ok.append(f"Yasak eski kural deseni yok: {rel} :: {pattern}")


def _check_docs(root: Path, report: FinalReport) -> None:
    for rel in REFERENCE_DOCS:
        if (root / rel).exists():
            report.ok.append(f"Referans dokümantasyon mevcut: {rel}")
        else:
            report.findings.append(Finding("missing_reference_doc", f"Referans dokümantasyon bulunamadı: {rel}", "warning"))


def _run_subgates(root: Path, report: FinalReport) -> None:
    for code, title, rel in SUBGATE_SCRIPTS:
        script = root / rel
        if not script.exists():
            report.subgates.append(Subgate(code, title, False, 127, f"Eksik alt gate: {rel}"))
            continue
        try:
            env = os.environ.copy()
            env.setdefault("PYTHONUTF8", "1")
            env.setdefault("PYTHONIOENCODING", "utf-8")
            result = subprocess.run(
                [sys.executable, "-S", str(script)],
                cwd=str(root),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=90,
                check=False,
                env=env,
            )
            detail = _subgate_detail(result.stdout, result.stderr)
            report.subgates.append(Subgate(code, title, result.returncode == 0, result.returncode, detail))
        except subprocess.TimeoutExpired:
            report.subgates.append(Subgate(code, title, False, 124, "Alt gate zaman aşımına uğradı."))


def build_performance_manager_rules_final_gate_report(project_root: str | Path | None = None) -> FinalReport:
    root = Path(project_root or Path.cwd()).resolve()
    report = FinalReport()
    _check_compile(root, report)
    _check_required_tokens(root, report)
    _check_forbidden(root, report)
    _run_subgates(root, report)
    _check_docs(root, report)
    return report


def format_performance_manager_rules_final_report(report: FinalReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Performans Amir Kuralları Final Gate | {status}",
        f"version={report.version}",
        f"OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
        "",
        "Kilitlenen nihai kurallar:",
        "- Kör değerlendirme yok; sonraki amir önceki puan ve kanaati görebilir.",
        "- Personel sonucu yayın/onay öncesi açılmaz.",
        "- Çalışma grubu personeli: 1=Grup Başkanı, 2=Koordinatör, varsa 3=Birim Amiri; işlem sırası 3→2→1.",
        "- Koordinatör: 1=Başkan Yardımcısı, 2=Grup Başkanı; işlem sırası varsa 3→2→1, yoksa 2→1.",
        "- Grup Başkanı: 1=Başkan, 2=Başkan Yardımcısı; işlem sırası 2→1.",
        "- Hukuk ve Başkan özel rolleri tek amirli/özel istisna olarak korunur; sahte bekleme üretilmez.",
        "- 1 ve 5 puanda açıklama zorunlu; 70 altı / 90 üstü genel görüş zorunlu.",
        "- 3. amir yorum modunda %0, puan modunda dinamik ağırlıkla çalışır; toplam daima %100.",
        "- Ana ekran terimi Değerlendirme Kriterleri; karşılaştırma ekranı Personel Analizi.",
        "",
        "Alt gate özeti:",
    ]
    for gate in report.subgates:
        marker = "OK" if gate.passed else "HATA"
        lines.append(f"- {marker} | {gate.code} | {gate.title} | exit={gate.exit_code}")
        if gate.detail:
            lines.append(f"  {gate.detail}")
    if report.findings:
        lines.append("")
        lines.append("Bulgular:")
        for item in report.findings:
            lines.append(f"- {item.severity.upper()} | {item.code} | {item.message}")
    if report.passed():
        lines.append("")
        lines.append("PERFORMANCE_MANAGER_RULES_FINAL_GATE_OK")
    return "\n".join(lines)


def write_performance_manager_rules_final_reports(report: FinalReport, root: str | Path | None = None) -> dict[str, str]:
    project_root = Path(root or Path.cwd()).resolve()
    report_dir = project_root / "reports" / "refactor"
    generated_dir = project_root / "docs" / "refactor" / "generated"
    report_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "performance_manager_rules_final_gate.json"
    md_path = report_dir / "performance_manager_rules_final_gate.md"
    doc_path = generated_dir / "performance_manager_rules_final_gate.md"
    json_path.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    formatted = format_performance_manager_rules_final_report(report) + "\n"
    md_path.write_text(formatted, encoding="utf-8")
    doc_path.write_text(formatted, encoding="utf-8")
    return {
        "json": str(json_path.relative_to(project_root)).replace("\\", "/"),
        "md": str(md_path.relative_to(project_root)).replace("\\", "/"),
        "doc": str(doc_path.relative_to(project_root)).replace("\\", "/"),
    }
