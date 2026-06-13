
"""BYS360 Performans Görünürlük, Yayın ve Kör Değerlendirme Kapısı.

Bu modül canlı davranış değiştirmez. Nihai performans amir kural matrisinin
şu görünürlük ilkelerini kaynak kod üzerinde denetler:

- Kör değerlendirme kapalıdır.
- Sonraki amir, önceki tamamlanmış amirin puan/kanaatini görebilir.
- Personel kendi sonucunu ancak dönem yayını + personel yayını + tamamlanmış
  değerlendirme koşulları birlikte sağlandığında görebilir.
- Amir/admin kendi kişisel sonucunu yayın öncesi göremez.
- Yayın ön kontrol blokajları atlanarak personel görünürlüğü açılamaz.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Iterable

VISIBILITY_PUBLICATION_GATE_VERSION = "2026-04-20-performance-visibility-publication-gate-faz3"

VISIBILITY_REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance/visibility_guard.py": (
        "VISIBILITY_RULE_VERSION",
        "BLIND_REVIEW_ALLOWED = False",
        "is_employee_visible",
        "is_period_published",
        "is_employee_published",
        "completed and period_published and employee_published",
        "can_view_unpublished = bool(viewer_is_privileged and in_scope and completed and not same_employee)",
        "own_result_locked = bool(same_employee and not employee_visible)",
        "build_evaluation_form_visibility_context",
        "visible_previous_levels",
        "can_see_previous_scores",
        "Kör değerlendirme yok",
    ),
    "app/services/performance/publish_preflight_rules.py": (
        "PUBLISH_PREFLIGHT_RULE_VERSION",
        "validate_evaluation_for_publish",
        "is_evaluation_publishable_strict",
        "Tamamlanmamış değerlendirme yayınlanamaz",
        "Zorunlu amir adımı eksikse yayınlanamaz",
        "1 veya 5 verilen kriterlerde açıklama/gerekçe zorunludur",
        "70 altı sonuçlarda ayrıntılı genel görüş zorunludur",
        "90 ve üstü sonuçlarda ayrıntılı genel görüş zorunludur",
        "Tek amirli istisnalarda gereksiz 2./3. amir beklenmez",
        "is_president_exempt",
    ),
    "app/services/performance/publish_guard.py": (
        "build_publish_preflight_report",
        "publish_preflight_has_blockers",
        "employee_visible",
        "internal_preview",
        "published_count",
        "blocked_count",
    ),
    "app/services/performance_v2/evaluation_workspace.py": (
        "build_evaluation_form_visibility_context",
        "'form_visibility': build_evaluation_form_visibility_context",
    ),
    "scripts/check_performance_visibility_gate.py": (
        "PERFORMANS GÖRÜNÜRLÜK KAPISI",
        "Kör değerlendirme kapalı",
        "build_evaluation_form_visibility_context",
    ),
}

# Bazı kurulumlarda yayın policy köprüsü ayrı pakette bulunur. Varsa denetlenecek,
# yoksa uyarı değil bilgi olarak geçilecektir.
OPTIONAL_VISIBILITY_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/publish/policy.py": (
        "from app.services.performance.visibility_guard import",
        "get_evaluation_visibility_state",
        "can_employee_view_evaluation",
        "is_evaluation_publishable",
    ),
}

VISIBILITY_FORBIDDEN_PATTERNS: dict[str, tuple[str, ...]] = {
    "app/services/performance/visibility_guard.py": (
        r"BLIND_REVIEW_ALLOWED\s*=\s*True",
        r"blind_review_allowed[\"']?\s*[:=]\s*True",
        r"employee_visible\s*=\s*completed\s+and\s+employee_published(?!\s+and\s+period_published)",
    ),
    "app/services/performance/publish_preflight_rules.py": (
        r"return\s+PublishPreflightResult\(\s*True[\s\S]{0,200}?not_completed",
        r"level_3_comment_missing[\s\S]{0,250}?severity\s*=\s*['\"]info['\"]",
    ),
    "app/services/publish/policy.py": (
        r"def\s+get_evaluation_visibility_state\(",
        r"def\s+can_employee_view_evaluation\(",
        r"def\s+is_evaluation_publishable\(",
    ),
    "app/templates": (
        "kör değerlendirme aktif",
        "blind review active",
        "yayın öncesi personele açık",
        "personel yayın kilidi yok",
    ),
}

VISIBILITY_COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/visibility_publication_gate.py",
    "app/services/performance/rule_matrix_final_gate.py",
    "app/services/performance/chain_contract_gate.py",
    "app/services/performance/task_generation_gate.py",
    "scripts/check_performance_visibility_publication_gate.py",
    "scripts/check_performance_rule_matrix_final_gate.py",
    "scripts/check_performance_chain_contract_gate.py",
    "scripts/check_performance_task_generation_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz3_audit.py",
)


@dataclass
class VisibilityPublicationFinding:
    code: str
    message: str
    severity: str = "error"


@dataclass
class VisibilityPublicationReport:
    version: str = VISIBILITY_PUBLICATION_GATE_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[VisibilityPublicationFinding] = field(default_factory=list)

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
                "blind_review_allowed": False,
                "employee_visibility_requires": ["completed", "period_published", "employee_published"],
                "manager_preview_excludes_own_result": True,
                "previous_manager_score_visible": True,
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


def _check_tokens(root: Path, report: VisibilityPublicationReport) -> None:
    for rel, tokens in VISIBILITY_REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.findings.append(VisibilityPublicationFinding("missing_required_file", f"Eksik görünürlük/yayın dosyası: {rel}"))
            continue
        content = _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"{rel} :: {token}")
            else:
                report.findings.append(VisibilityPublicationFinding("missing_required_token", f"Eksik görünürlük/yayın izi: {rel} :: {token}"))

    for rel, tokens in OPTIONAL_VISIBILITY_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Opsiyonel görünürlük köprüsü yok/kapsam dışı: {rel}")
            continue
        content = _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"Opsiyonel köprü doğrulandı: {rel} :: {token}")
            else:
                report.ok.append(f"Opsiyonel köprü izi eksik ama canlı kapsamda zorunlu değil: {rel} :: {token}")


def _check_forbidden_patterns(root: Path, report: VisibilityPublicationReport) -> None:
    for rel, patterns in VISIBILITY_FORBIDDEN_PATTERNS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Yasak görünürlük alanı yok veya kapsam dışı: {rel}")
            continue
        for file_path in _iter_text_files(path):
            content = _read(file_path)
            for pattern in patterns:
                flags = re.IGNORECASE | re.MULTILINE
                if "[\\s\\S]" in pattern or "\\s" in pattern:
                    flags |= re.DOTALL
                if re.search(pattern, content, flags=flags):
                    report.findings.append(VisibilityPublicationFinding("forbidden_visibility_pattern", f"Yasak görünürlük/yayın izi: {file_path.relative_to(root)} :: {pattern}"))
                else:
                    report.ok.append(f"Yasak görünürlük deseni yok: {file_path.relative_to(root)}")


def simulate_employee_visibility(*, completed: bool, period_published: bool, employee_published: bool) -> bool:
    """Personel görünürlüğü için kapalı devre sözleşme simülasyonu."""
    return bool(completed and period_published and employee_published)


def simulate_manager_internal_preview(*, privileged: bool, in_scope: bool, completed: bool, same_employee: bool) -> bool:
    """Amir/admin iç görünümü kendi sonucu hariç çalışmalıdır."""
    return bool(privileged and in_scope and completed and not same_employee)


def simulate_previous_levels(current_level: int) -> tuple[int, ...]:
    """3 -> 2 -> 1 akışına göre önceki tamamlanmış seviyeler."""
    if current_level <= 0:
        return ()
    return tuple(level for level in (3, 2, 1) if level > current_level)


def _check_contract_simulations(report: VisibilityPublicationReport) -> None:
    cases = [
        (False, False, False, False),
        (True, False, False, False),
        (True, True, False, False),
        (True, False, True, False),
        (True, True, True, True),
    ]
    for completed, period_published, employee_published, expected in cases:
        got = simulate_employee_visibility(
            completed=completed,
            period_published=period_published,
            employee_published=employee_published,
        )
        if got == expected:
            report.ok.append(f"employee_visibility_contract::{completed}/{period_published}/{employee_published}={expected}")
        else:
            report.findings.append(VisibilityPublicationFinding("employee_visibility_contract", f"Personel görünürlük sözleşmesi bozuldu: {completed}/{period_published}/{employee_published}"))

    manager_cases = [
        (True, True, True, False, True),
        (True, True, True, True, False),
        (True, False, True, False, False),
        (False, True, True, False, False),
        (True, True, False, False, False),
    ]
    for privileged, in_scope, completed, same_employee, expected in manager_cases:
        got = simulate_manager_internal_preview(privileged=privileged, in_scope=in_scope, completed=completed, same_employee=same_employee)
        if got == expected:
            report.ok.append(f"manager_preview_contract::{privileged}/{in_scope}/{completed}/{same_employee}={expected}")
        else:
            report.findings.append(VisibilityPublicationFinding("manager_preview_contract", "Amir iç görünüm/kendi sonuç kilidi sözleşmesi bozuldu."))

    expected_previous = {1: (3, 2), 2: (3,), 3: (), 0: ()}
    for level, expected in expected_previous.items():
        got = simulate_previous_levels(level)
        if got == expected:
            report.ok.append(f"previous_level_contract::{level}={expected}")
        else:
            report.findings.append(VisibilityPublicationFinding("previous_level_contract", f"Önceki amir görünürlüğü sözleşmesi bozuldu: level={level}, got={got}, expected={expected}"))


def build_visibility_publication_gate_report(project_root: str | Path | None = None) -> VisibilityPublicationReport:
    root = Path(project_root or Path.cwd()).resolve()
    report = VisibilityPublicationReport()
    _check_tokens(root, report)
    _check_forbidden_patterns(root, report)
    _check_contract_simulations(report)
    return report


def format_visibility_publication_report(report: VisibilityPublicationReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Performans Görünürlük/Yayın/Kör Değerlendirme Kapısı | {status}",
        f"version={report.version}",
        f"OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
    ]
    if report.findings:
        lines.append("")
        lines.append("Bulgular:")
        for item in report.findings:
            lines.append(f"- {item.severity.upper()} | {item.code} | {item.message}")
    return "\n".join(lines)


__all__ = [
    "VISIBILITY_PUBLICATION_GATE_VERSION",
    "VISIBILITY_COMPILE_TARGETS",
    "VisibilityPublicationFinding",
    "VisibilityPublicationReport",
    "build_visibility_publication_gate_report",
    "format_visibility_publication_report",
    "simulate_employee_visibility",
    "simulate_manager_internal_preview",
    "simulate_previous_levels",
]


# BYS360_A5_P2D3_PUBLISH_PREFLIGHT_LOCK_ANCHOR_START
# Static contract anchor: 2026-04-18-publish-preflight-lock-v1
PUBLISH_PREFLIGHT_LOCK_CONTRACT_ID = "2026-04-18-publish-preflight-lock-v1"
# BYS360_A5_P2D3_PUBLISH_PREFLIGHT_LOCK_ANCHOR_END

