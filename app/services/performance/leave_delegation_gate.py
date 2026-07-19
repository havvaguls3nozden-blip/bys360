
"""BYS360 Performans İzin/Devamsızlık/Vekâlet Entegrasyon Kapısı.

Bu modül canlı davranış değiştirmez. Nihai amir kural matrisindeki izin,
devamsızlık ve vekâlet sözleşmesini statik kaynak izleri ve küçük sözleşme
simülasyonlarıyla denetler:

- İzinli/devamsız amirin görevi boşa düşmez; aynı seviyedeki vekile aktarılır.
- Görev seviyesi korunur ve denetim izi kaybolmaz.
- İzinli/raporlu personel için muafiyet, kısmi değerlendirme ve bilgi amaçlı
  kayıt modları desteklenir.
- Muafiyet modunda sahte görev üretilmez.
- Vekâlet yoksa durum uncovered/warning olarak izlenir; sessizce görev
  kaybolmaz.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable

LEAVE_DELEGATION_GATE_VERSION = "2026-04-20-performance-leave-delegation-gate-faz5"

LEAVE_DELEGATION_REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance/rules.py": (
        "LEAVE_PERFORMANCE_MODE_ALLOWED",
        "LEAVE_PERFORMANCE_MODE_DEFAULT",
        "INFO_REASON_DELEGATED_ASSIGNMENT",
        'LEAVE_PERFORMANCE_MODE_ALLOWED: Final[tuple[str, ...]] = ("exclude", "partial", "informational")',
    ),
    "app/services/performance/delegation.py": (
        "DEFAULT_PERFORMANCE_MODE",
        "VALID_PERFORMANCE_MODES",
        "REASON_EVENT_MAP",
        "EffectiveEvaluatorResult",
        "get_active_leave_for_user",
        "get_active_attendance_for_user",
        "get_active_delegate",
        "resolve_effective_evaluator",
        "resolve_employee_performance_mode",
        "blocks_manager_duties",
        "delegation.delegate_user_id",
        "reason_type=\"delegated\"",
        "reason_type=\"delegation_missing\"",
        '"exclude"',
        '"partial"',
        '"informational"',
    ),
    "app/services/performance/assignment_effective_chain.py": (
        "resolve_effective_evaluator",
        "resolve_employee_performance_mode",
        "log_assignment_decision",
        "performance_mode == \"exclude\"",
        "reason_type=\"excluded_due_leave\"",
        "for level in sorted(manager_chain.keys())",
        "ensure_evaluation_summary",
        "ensure_assignment",
        "effective_chain[level] = resolved.effective_evaluator_id",
    ),
    "app/services/performance/assignments.py": (
        "delegation_id",
        '"delegated": 0',
        '"exempted": 0',
        '"uncovered": 0',
        "build_assignment_log_summary",
        "build_assignment_unit_summary",
        "coverage_resolutions",
        "assignment_source",
        "coverage_note",
    ),
    "app/services/performance/task_management_service.py": (
        "delegated",
        "exempted",
        "uncovered",
        "build_assignment_delegation_pressure_ai_panel",
        "performance_task_management_audit_detail",
    ),
}

LEAVE_DELEGATION_OPTIONAL_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/personnel/leave_attendance.py": (
        "delegation_assignments",
        "attendance_exceptions",
        "leave_records",
    ),
    "app/models.py": (
        "DelegationAssignment",
        "PersonnelLeave",
        "AttendanceException",
    ),
}

LEAVE_DELEGATION_FORBIDDEN_PATTERNS: dict[str, tuple[str, ...]] = {
    "app/services/performance/assignment_effective_chain.py": (
        # Exclude modunda return edilmeden görev üretilmemeli.
        r"performance_mode\s*==\s*[\"']exclude[\"'][\s\S]{0,1200}?ensure_assignment\(",
        # Vekâlet seviyesi düşürülmemeli/yükseltilmemeli; level korunmalı.
        r"manager_level\s*=\s*(?:1|2|3)\s*#\s*delegated",
    ),
    "app/services/performance/delegation.py": (
        # Vekâlet eksikse info değil warning olmalı.
        r"reason_type\s*=\s*[\"']delegation_missing[\"'][\s\S]{0,250}?warning_level\s*=\s*[\"']info[\"']",
        # Delegated durumda effective evaluator boş kalmamalı.
        r"reason_type\s*=\s*[\"']delegated[\"'][\s\S]{0,250}?effective_evaluator_id\s*=\s*None",
    ),
    "app/services/performance/assignments.py": (
        # Tek bir genel warning altında delegated/exempted kaybedilmemeli.
        r"summary\s*=\s*\{\s*[\"']warning[\"']\s*:\s*0\s*\}",
    ),
}

LEAVE_DELEGATION_COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/rule_matrix_final_gate.py",
    "app/services/performance/chain_contract_gate.py",
    "app/services/performance/task_generation_gate.py",
    "app/services/performance/visibility_publication_gate.py",
    "app/services/performance/scoring_weight_gate.py",
    "app/services/performance/leave_delegation_gate.py",
    "scripts/check_performance_rule_matrix_final_gate.py",
    "scripts/check_performance_chain_contract_gate.py",
    "scripts/check_performance_task_generation_gate.py",
    "scripts/check_performance_visibility_publication_gate.py",
    "scripts/check_performance_scoring_weight_gate.py",
    "scripts/check_performance_leave_delegation_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz5_audit.py",
)


@dataclass
class LeaveDelegationFinding:
    code: str
    message: str
    severity: str = "error"


@dataclass
class LeaveDelegationReport:
    version: str = LEAVE_DELEGATION_GATE_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[LeaveDelegationFinding] = field(default_factory=list)

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
            "contracts": {
                "manager_leave": "same_level_delegate_or_uncovered_warning",
                "employee_leave_modes": ["exclude", "partial", "informational"],
                "exclude_mode": "no_assignment_and_exempted_log",
                "partial_mode": "assignment_continues_with_signal",
                "informational_mode": "assignment_continues_with_note",
                "audit_events": ["delegated", "uncovered", "exempted", "generated"],
            },
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


def _check_required_tokens(root: Path, report: LeaveDelegationReport) -> None:
    for rel, tokens in LEAVE_DELEGATION_REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.findings.append(LeaveDelegationFinding("missing_required_file", f"Eksik izin/vekâlet dosyası: {rel}"))
            continue
        content = _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"{rel} :: {token}")
            else:
                report.findings.append(LeaveDelegationFinding("missing_required_token", f"Eksik izin/vekâlet izi: {rel} :: {token}"))

    for rel, tokens in LEAVE_DELEGATION_OPTIONAL_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Opsiyonel izin/vekâlet alanı yok/kapsam dışı: {rel}")
            continue
        content = "\n".join(_read(p) for p in _iter_text_files(path)) if path.is_dir() else _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"Opsiyonel izin/vekâlet köprüsü doğrulandı: {rel} :: {token}")
            else:
                report.ok.append(f"Opsiyonel izin/vekâlet izi eksik ama canlı gate için bloklayıcı değil: {rel} :: {token}")


def _check_forbidden_patterns(root: Path, report: LeaveDelegationReport) -> None:
    for rel, patterns in LEAVE_DELEGATION_FORBIDDEN_PATTERNS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Yasak izin/vekâlet alanı yok veya kapsam dışı: {rel}")
            continue
        for file_path in _iter_text_files(path):
            content = _read(file_path)
            for pattern in patterns:
                flags = re.IGNORECASE | re.MULTILINE | re.DOTALL
                if re.search(pattern, content, flags=flags):
                    report.findings.append(LeaveDelegationFinding("forbidden_leave_delegation_pattern", f"Yasak izin/vekâlet izi: {file_path.relative_to(root)} :: {pattern}"))
                else:
                    report.ok.append(f"Yasak izin/vekâlet deseni yok: {file_path.relative_to(root)}")


def simulate_employee_performance_mode(*, has_active_leave: bool, requested_mode: str | None = None) -> dict[str, object]:
    allowed = {"exclude", "partial", "informational"}
    mode = (requested_mode or "informational").strip().lower()
    if mode not in allowed:
        mode = "informational"
    if not has_active_leave:
        mode = "informational"
    return {
        "has_active_leave": bool(has_active_leave),
        "performance_mode": mode,
        "exempted": mode == "exclude",
        "continues": mode in {"partial", "informational"},
    }


def simulate_effective_evaluator(
    evaluator_id: int | None,
    manager_level: int,
    *,
    manager_blocked: bool = False,
    delegate_user_id: int | None = None,
) -> dict[str, object]:
    if not evaluator_id:
        return {
            "manager_level": manager_level,
            "original_evaluator_id": None,
            "effective_evaluator_id": None,
            "event_type": "chain_issue",
            "severity": "error",
            "delegated": False,
        }
    if not manager_blocked:
        return {
            "manager_level": manager_level,
            "original_evaluator_id": evaluator_id,
            "effective_evaluator_id": evaluator_id,
            "event_type": "generated",
            "severity": "info",
            "delegated": False,
        }
    if delegate_user_id:
        return {
            "manager_level": manager_level,
            "original_evaluator_id": evaluator_id,
            "effective_evaluator_id": delegate_user_id,
            "event_type": "delegated",
            "severity": "info",
            "delegated": True,
        }
    return {
        "manager_level": manager_level,
        "original_evaluator_id": evaluator_id,
        "effective_evaluator_id": None,
        "event_type": "uncovered",
        "severity": "warning",
        "delegated": False,
    }


def simulate_assignment_levels(
    manager_chain: dict[int, int | None],
    *,
    employee_leave_mode: str = "informational",
    blocked_managers: dict[int, int | None] | None = None,
) -> dict[str, object]:
    employee = simulate_employee_performance_mode(
        has_active_leave=(employee_leave_mode != "informational"),
        requested_mode=employee_leave_mode,
    )
    if employee["exempted"]:
        return {"active_levels": (), "events": ("exempted",), "effective": {}}
    blocked_managers = blocked_managers or {}
    active_levels: list[int] = []
    events: list[str] = []
    effective: dict[int, int] = {}
    for level in sorted(manager_chain):
        evaluator_id = manager_chain.get(level)
        blocked = level in blocked_managers
        delegate_id = blocked_managers.get(level)
        result = simulate_effective_evaluator(evaluator_id, level, manager_blocked=blocked, delegate_user_id=delegate_id)
        events.append(str(result["event_type"]))
        if result["effective_evaluator_id"]:
            active_levels.append(level)
            effective[level] = int(result["effective_evaluator_id"])
    return {"active_levels": tuple(active_levels), "events": tuple(events), "effective": effective}


def _check_contract_simulations(report: LeaveDelegationReport) -> None:
    leave_cases = [
        (True, "exclude", True, False, "izinli personel muafiyet"),
        (True, "partial", False, True, "izinli personel kısmi değerlendirme"),
        (True, "informational", False, True, "izinli personel bilgi amaçlı kayıt"),
        (False, "exclude", False, True, "aktif izin yoksa muafiyet zorlanmaz"),
        (True, "garbage", False, True, "geçersiz mod bilgi amaçlıya düşer"),
    ]
    for active, mode, expected_exempted, expected_continues, label in leave_cases:
        result = simulate_employee_performance_mode(has_active_leave=active, requested_mode=mode)
        if result["exempted"] is expected_exempted and result["continues"] is expected_continues:
            report.ok.append(f"Personel izin modu sözleşmesi doğru: {label}")
        else:
            report.findings.append(LeaveDelegationFinding("employee_leave_mode_contract", f"Personel izin modu hatalı: {label} -> {result}"))

    delegation_cases = [
        (10, 2, False, None, 10, "generated", "aktif amir görevi korur"),
        (10, 2, True, 99, 99, "delegated", "izinli amir aynı seviyede vekile gider"),
        (10, 3, True, None, None, "uncovered", "izinli amir vekilsiz uncovered olur"),
        (None, 1, False, None, None, "chain_issue", "boş amir chain_issue olur"),
    ]
    for evaluator_id, level, blocked, delegate_id, expected_effective, expected_event, label in delegation_cases:
        result = simulate_effective_evaluator(evaluator_id, level, manager_blocked=blocked, delegate_user_id=delegate_id)
        if result["manager_level"] != level:
            report.findings.append(LeaveDelegationFinding("delegation_level_contract", f"Vekâlet seviyesi bozuldu: {label} -> {result}"))
            continue
        if result["effective_evaluator_id"] != expected_effective or result["event_type"] != expected_event:
            report.findings.append(LeaveDelegationFinding("delegation_effective_contract", f"Vekâlet çözümü hatalı: {label} -> {result}"))
            continue
        report.ok.append(f"Vekâlet çözüm sözleşmesi doğru: {label}")

    assignment_cases = [
        ({1: 10, 2: 20, 3: 30}, "exclude", {}, (), ("exempted",), "muafiyette görev yok"),
        ({1: 10, 2: 20, 3: 30}, "partial", {2: 99}, (1, 2, 3), ("generated", "delegated", "generated"), "kısmi değerlendirmede seviyeler korunur"),
        ({1: 10, 2: 20, 3: 30}, "informational", {3: None}, (1, 2), ("generated", "generated", "uncovered"), "vekil yoksa sadece ilgili seviye düşer"),
        ({1: 10, 2: None}, "informational", {}, (1,), ("generated", "chain_issue"), "boş değerlendirici görev üretmez"),
    ]
    for chain, mode, blocked, expected_levels, expected_events, label in assignment_cases:
        result = simulate_assignment_levels(chain, employee_leave_mode=mode, blocked_managers=blocked)
        if result["active_levels"] != expected_levels:
            report.findings.append(LeaveDelegationFinding("assignment_level_contract", f"Aktif seviye sözleşmesi hatalı: {label} -> {result}"))
            continue
        if result["events"] != expected_events:
            report.findings.append(LeaveDelegationFinding("assignment_event_contract", f"Olay izi sözleşmesi hatalı: {label} -> {result}"))
            continue
        report.ok.append(f"Görev/izin/vekâlet simülasyonu doğru: {label}")


def build_leave_delegation_gate_report(project_root: str | Path | None = None) -> LeaveDelegationReport:
    root = Path(project_root or Path.cwd()).resolve()
    report = LeaveDelegationReport()
    _check_required_tokens(root, report)
    _check_forbidden_patterns(root, report)
    _check_contract_simulations(report)
    return report


def format_leave_delegation_report(report: LeaveDelegationReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Performans İzin/Devamsızlık/Vekâlet Kapısı | {status}",
        f"version={report.version}",
        f"OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
        "",
        "Sözleşme özeti:",
        "- İzinli/devamsız amirin görevi aynı seviyede vekile yönlendirilir.",
        "- Vekil yoksa durum uncovered/warning olarak loglanır.",
        "- İzinli/raporlu personel için exclude/partial/informational modları desteklenir.",
        "- Exclude modunda sahte görev üretilmez; exempted iz oluşur.",
        "- Denetim olayları delegated/uncovered/exempted/generated ayrımıyla korunur.",
    ]
    if report.findings:
        lines.append("")
        lines.append("Bulgular:")
        for finding in report.findings:
            lines.append(f"- {finding.severity.upper()} | {finding.code} | {finding.message}")
    return "\n".join(lines)


__all__ = [
    "LEAVE_DELEGATION_COMPILE_TARGETS",
    "LEAVE_DELEGATION_GATE_VERSION",
    "LEAVE_DELEGATION_REQUIRED_TOKENS",
    "LeaveDelegationFinding",
    "LeaveDelegationReport",
    "build_leave_delegation_gate_report",
    "format_leave_delegation_report",
    "simulate_assignment_levels",
    "simulate_effective_evaluator",
    "simulate_employee_performance_mode",
]
