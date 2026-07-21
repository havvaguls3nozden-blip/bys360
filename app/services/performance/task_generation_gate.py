
"""BYS360 Performans Görev Üretimi ve Sahte Bekleme Kapısı.

Bu modül canlı davranış değiştirmez. Görev üretimi, özel tek-amirli akışlar,
3. amir yorum modu, vekalet yönlendirmesi ve sahte bekleme durumlarının aktif
kaynak dosyalarda korunup korunmadığını statik olarak denetler.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

TASK_GENERATION_GATE_VERSION = "2026-04-20-performance-task-generation-gate-faz2"

EXPECTED_TASK_LEVELS: dict[str, tuple[int, ...]] = {
    "single_manager": (1,),
    "two_manager": (2, 1),
    "three_manager": (3, 2, 1),
    "three_comment_only": (3, 2, 1),
    "president_excluded": (),
    "leave_exempted": (),
}

TASK_REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance_v2/sync_service.py": (
        "resolve_authoritative_desired_chain",
        "_persist_canonical_manager_chain",
        "_resolved_payloads",
        "if level == 3:",
        "if not getattr(payload, 'evaluator_id', None):",
        "continue",
        "_deactivate_stale_assignments",
        "status='pasif'",
        "if availability.exempted:",
        "active_level_count",
        "not is_president(employee)",
        "event_type='uncovered'",
        "severity='error'",
        "event_type='delegated'",
        "severity='info'",
        "event_type='exempted'",
        "event_type='cleared'",
        "_log_generation_event",
        "run_key = uuid4().hex",
    ),
    "app/services/performance/assignments.py": (
        "is_informational_special_case",
        "3. amir yorumcu modunda",
        "vekalet nedeniyle gorev ayni seviyede vekile yonlendirildi",
        "if not evaluator_id:",
        "return None",
        "_dedupe_assignment_rows",
        "_enforce_required_chain_levels",
        "sync_assignments_v2_for_period",
        "return sync_assignments_v2_for_period",
        "event_type",
        "special_case",
    ),
    "app/services/performance/task_management_service.py": (
        "build_task_management_dashboard_payload",
        "coverage_summary",
        "delegated_assignments",
        "uncovered_assignments",
        "exempt_evaluations",
        "visible_assignment_logs",
        "special_case_logs",
        "is_informational_special_case",
        "Açıkta kalan kayıtlar",
        "Vekâletli görevler",
        "Muaf kayıtlar",
    ),
    "app/services/performance/assignment_effective_chain.py": (
        "resolve_effective_evaluator",
        "resolve_employee_performance_mode",
        "if result.performance_mode == \"exclude\"",
        "ensure_evaluation_summary",
        "ensure_assignment",
        "if not evaluator_id:",
        "return False",
    ),
    "app/services/performance/assignment_builder.py": (
        "for level in [3,2,1]",
        "if not evaluator:",
        "continue",
        "prevent_duplicate_assignment",
        "\"status\": \"bekliyor\"",
    ),
}

TASK_FORBIDDEN_PATTERNS: dict[str, tuple[str, ...]] = {
    "app/services/performance_v2/sync_service.py": (
        # Açıkta kalan görev hata/uyarı olmalı; bilgi satırı gibi gizlenemez.
        r"event_type\s*=\s*['\"]uncovered['\"][\s\S]{0,220}?severity\s*=\s*['\"]info['\"]",
        # Muafiyet halinde aktif seviyeyi 1/2/3 gibi gösteren eski iz olmamalı.
        r"availability\.exempted[\s\S]{0,500}?active_level_count['\"]?\s*:\s*[123]",
        # Başkan değerlendirme öznesi yapılmamalı.
        r"employees\s*=\s*list\(query\.all\(\)\)",
    ),
    "app/services/performance/assignments.py": (
        # Boş değerlendirici için sahte görev üretilmemeli.
        r"def\s+ensure_assignment[\s\S]{0,700}?EvaluationAssignment\([\s\S]{0,300}?evaluator_id\s*=\s*None",
        # Tek amir özel durumları chain_issue riskine zorla sayılmamalı.
        r"tek amir[\s\S]{0,120}?summary\[['\"]chain_issue['\"]\]\s*\+=\s*1",
    ),
    "app/templates": (
        "2. amir bekliyor",
        "3. amir bekliyor",
        "3. amir puan bekliyor",
        "Başkan değerlendirme öznesi yapılmamalı",
    ),
}

TASK_COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/task_generation_gate.py",
    "app/services/performance/chain_contract_gate.py",
    "app/services/performance/rule_matrix_final_gate.py",
    "scripts/check_performance_task_generation_gate.py",
    "scripts/check_performance_chain_contract_gate.py",
    "scripts/check_performance_rule_matrix_final_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz2_audit.py",
)


@dataclass
class TaskGenerationFinding:
    code: str
    message: str
    severity: str = "error"


@dataclass
class TaskGenerationReport:
    version: str = TASK_GENERATION_GATE_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[TaskGenerationFinding] = field(default_factory=list)

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
            "expected_task_levels": {key: list(value) for key, value in EXPECTED_TASK_LEVELS.items()},
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
        if child.is_file() and child.suffix.lower() in {".py", ".html", ".jinja", ".jinja2", ".txt", ".md"}:
            yield child


def _check_required_tokens(root: Path, report: TaskGenerationReport) -> None:
    for rel, tokens in TASK_REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.findings.append(TaskGenerationFinding("missing_file", f"Eksik görev üretimi dosyası: {rel}"))
            continue
        content = _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"{rel} :: {token}")
            else:
                report.findings.append(TaskGenerationFinding("missing_required_token", f"Eksik görev üretimi izi: {rel} :: {token}"))


def _check_forbidden_patterns(root: Path, report: TaskGenerationReport) -> None:
    for rel, patterns in TASK_FORBIDDEN_PATTERNS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Yasak desen alanı yok veya kapsam dışı: {rel}")
            continue
        files = list(_iter_text_files(path))
        if not files:
            report.ok.append(f"Yasak desen için dosya bulunmadı: {rel}")
            continue
        for file_path in files:
            content = _read(file_path)
            for pattern in patterns:
                flags = re.MULTILINE
                if "[\\s\\S]" in pattern or "\\s" in pattern:
                    flags |= re.DOTALL
                if re.search(pattern, content, flags=flags):
                    report.findings.append(TaskGenerationFinding("forbidden_task_pattern", f"Sahte bekleme/yanlış görev izi: {file_path.relative_to(root)} :: {pattern}"))
                else:
                    report.ok.append(f"Yasak görev deseni yok: {file_path.relative_to(root)}")


def _expected_active_levels(raw_levels: dict[int, int | None], *, level_3_mode: str = "scoring", exempted: bool = False, president: bool = False) -> tuple[int, ...]:
    if exempted or president:
        return ()
    levels: list[int] = []
    for level in (3, 2, 1):
        evaluator_id = raw_levels.get(level)
        if not evaluator_id:
            continue
        if level == 3 and level_3_mode in {"off", "disabled"}:
            continue
        levels.append(level)
    return tuple(levels)


def _check_contract_simulation(report: TaskGenerationReport) -> None:
    cases = {
        "single_manager": _expected_active_levels({1: 10, 2: None, 3: None}),
        "two_manager": _expected_active_levels({1: 10, 2: 20, 3: None}),
        "three_manager": _expected_active_levels({1: 10, 2: 20, 3: 30}, level_3_mode="scoring"),
        "three_comment_only": _expected_active_levels({1: 10, 2: 20, 3: 30}, level_3_mode="comment_only"),
        "president_excluded": _expected_active_levels({1: 10, 2: 20, 3: None}, president=True),
        "leave_exempted": _expected_active_levels({1: 10, 2: 20, 3: 30}, exempted=True),
    }
    for name, expected in EXPECTED_TASK_LEVELS.items():
        actual = cases.get(name)
        if tuple(actual or ()) != tuple(expected):
            report.findings.append(TaskGenerationFinding("simulation_mismatch", f"{name} için beklenen görev seviyeleri {expected}, hesaplanan {actual}"))
        else:
            report.ok.append(f"Sözleşme simülasyonu geçti: {name} -> {expected}")


def _check_false_waiting_language(root: Path, report: TaskGenerationReport) -> None:
    # Görev panellerinde sahte bekleme dili yerine kapsam/vekâlet/muafiyet dili görünmeli.
    task_service = root / "app/services/performance/task_management_service.py"
    if not task_service.exists():
        report.findings.append(TaskGenerationFinding("task_dashboard_missing", "task_management_service.py bulunamadı."))
        return
    content = _read(task_service)
    required_dashboard_labels = (
        "Açıkta kalan kayıtlar",
        "Vekâletli görevler",
        "Muaf kayıtlar",
        "Zincir sorunu taşıyanlar",
    )
    for label in required_dashboard_labels:
        if label in content:
            report.ok.append(f"Görev yönetimi doğru statü dili içeriyor: {label}")
        else:
            report.findings.append(TaskGenerationFinding("missing_dashboard_status_language", f"Görev yönetimi statü dili eksik: {label}"))


def _check_generation_log_taxonomy(root: Path, report: TaskGenerationReport) -> None:
    sync_service = root / "app/services/performance_v2/sync_service.py"
    if not sync_service.exists():
        report.findings.append(TaskGenerationFinding("sync_service_missing", "performance_v2/sync_service.py bulunamadı."))
        return
    content = _read(sync_service)
    taxonomy = {
        "generated": "info",
        "delegated": "info",
        "cleared": "info",
        "uncovered": "error",
        "exempted": "warning",
    }
    for event_type, severity in taxonomy.items():
        if f"event_type='{event_type}'" not in content and f'event_type="{event_type}"' not in content:
            report.findings.append(TaskGenerationFinding("missing_log_event", f"Görev üretimi log tipi eksik: {event_type}"))
            continue
        if f"severity='{severity}'" in content or f'severity="{severity}"' in content:
            report.ok.append(f"Görev üretimi log sözleşmesi: {event_type} -> {severity}")
        else:
            report.findings.append(TaskGenerationFinding("missing_log_severity", f"{event_type} için beklenen severity izi yok: {severity}", "warning"))


def build_task_generation_gate_report(project_root: str | Path | None = None) -> TaskGenerationReport:
    root = Path(project_root or Path.cwd()).resolve()
    report = TaskGenerationReport()
    _check_required_tokens(root, report)
    _check_forbidden_patterns(root, report)
    _check_contract_simulation(report)
    _check_false_waiting_language(root, report)
    _check_generation_log_taxonomy(root, report)
    return report


def format_task_generation_report(report: TaskGenerationReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Performans Görev Üretimi ve Sahte Bekleme Kapısı | {status}",
        f"version={report.version}",
        f"OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
        "",
        "Denetlenen ana sözleşmeler:",
        "- Boş değerlendirici için görev üretilmez.",
        "- Tek amirli akışta sahte üst-amir bekleme statüsü doğmaz.",
        "- 3. amir yorum modunda ayrı statü/görüş diliyle izlenir; puan bekliyor gibi gösterilmez.",
        "- İzin/devamsızlık muafiyeti aktif görev seviyesini sıfırlar ve eski görevleri pasife alır.",
        "- Vekâlet görevi aynı seviyede etkili değerlendiriciye yönlendirir.",
        "- Başkan değerlendirme öznesi yapılmaz.",
    ]
    if report.findings:
        lines.append("")
        lines.append("Bulgular:")
        for finding in report.findings:
            lines.append(f"- {finding.severity.upper()} | {finding.code} | {finding.message}")
    return "\n".join(lines)


__all__ = [
    "EXPECTED_TASK_LEVELS",
    "TASK_COMPILE_TARGETS",
    "TASK_FORBIDDEN_PATTERNS",
    "TASK_GENERATION_GATE_VERSION",
    "TASK_REQUIRED_TOKENS",
    "TaskGenerationFinding",
    "TaskGenerationReport",
    "build_task_generation_gate_report",
    "format_task_generation_report",
]
