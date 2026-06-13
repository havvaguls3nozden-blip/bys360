
"""BYS360 Performans UI/Rapor Terminoloji ve Statü Dili Kapısı.

Bu modül canlı davranış değiştirmez. Nihai performans amir kural matrisinin
kullanıcıya yansıyan dilini denetler:

- Ana terim "Değerlendirme Kriterleri" olmalıdır; "Yetkinlik" eski ana terim olarak görünmemelidir.
- Karşılaştırmalı ekran dili "Personel Analizi" olmalıdır; eski ekip kıyas dili kullanılmamalıdır.
- 3. amir yorum modunda "puan bekliyor" değil, yorum/görüş bekliyor dili kullanılmalıdır.
- Yayın/yayın ön kontrol dili personel görünürlük kilidini açık anlatmalıdır.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable

UI_REPORT_LANGUAGE_GATE_VERSION = "2026-04-20-performance-ui-report-language-gate-faz6"

UI_REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "app/templates/performance/evaluation_form.html": (
        "Performans Değerlendirme Formu",
        "Değerlendirme Kriterleri",
        "Şeffaf görünüm",
        "3. amir bu dönemde sadece yorumcudur. Puan alanı kapalıdır.",
        "3. Amir · Yorumcu",
        "1 ve 5 puanlarda açıklama",
        "Genel Görüş",
    ),
    "app/templates/performance/_workspace_shell.html": (
        "/performance/personel-analizi",
        "Personel Analizi",
        "Yayın Merkezi",
    ),
    "app/services/performance/team_compare_service.py": (
        "Personel Analizi",
        "sheet.title = \"Personel Analizi\"",
        "Yayın Durumu",
    ),
    "app/services/performance/visibility_guard.py": (
        "İK Yayın Kilidi",
        "karne görünür değil",
        "Yayın ön kontrol ekranında",
    ),
    "app/services/performance/publish_guard.py": (
        "Yayın ön kontrol",
        "Yayın için uygun",
        "Yayın ön kontrol sürümü",
    ),
}

UI_OPTIONAL_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance/export_service.py": (
        "Yayın Geçmişi",
        "Sonuç Yayını",
        "Yayın Durumu",
    ),
    "scripts/check_performance_core_health_dalga8_gate.py": (
        "Eski Ekip dili yok",
        "Personel Analizi route",
    ),
}

UI_FORBIDDEN_PATTERNS: dict[str, tuple[str, ...]] = {
    "app/templates/performance": (
        r"\bYetkinlik\b",
        r"\byetkinlik\b",
        r"Ekip\s+Kıyas",
        r"Ekip\s+Analizi",
        r"3\.\s*amir\s+puan\s+bekliyor",
        r"Başkan\s+puan\s+bekliyor",
        r"2\.\s*amir\s+bekliyor",
        r"3\.\s*amir\s+bekliyor",
    ),
    "app/templates": (
        r"\bYetkinlik\b",
        r"\byetkinlik\b",
        r"3\.\s*amir\s+puan\s+bekliyor",
        r"Başkan\s+puan\s+bekliyor",
    ),
    "app/services/performance/team_compare_service.py": (
        r"Ekip\s+Kıyas",
        r"Ekip\s+Analizi",
    ),
}

UI_REPORT_LANGUAGE_COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/ui_report_language_gate.py",
    "app/services/performance/rule_matrix_final_gate.py",
    "app/services/performance/chain_contract_gate.py",
    "app/services/performance/task_generation_gate.py",
    "app/services/performance/visibility_publication_gate.py",
    "app/services/performance/scoring_weight_gate.py",
    "app/services/performance/leave_delegation_gate.py",
    "scripts/check_performance_ui_report_language_gate.py",
    "scripts/check_performance_rule_matrix_final_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz6_audit.py",
)

@dataclass
class UiLanguageFinding:
    code: str
    message: str
    severity: str = "error"

@dataclass
class UiLanguageReport:
    version: str = UI_REPORT_LANGUAGE_GATE_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[UiLanguageFinding] = field(default_factory=list)

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
            "language_contracts": {
                "criteria_label": "Değerlendirme Kriterleri",
                "comparison_label": "Personel Analizi",
                "level_3_comment_status": "yorum/görüş bekliyor",
                "publication_success_label": "Sonuçlar yayımlandı",
                "publication_pending_label": "Yayın bekliyor",
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
        if child.is_file() and child.suffix.lower() in {".py", ".html", ".jinja", ".jinja2", ".txt", ".md", ".css", ".js"}:
            yield child

def _check_required_tokens(root: Path, report: UiLanguageReport) -> None:
    for rel, tokens in UI_REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.findings.append(UiLanguageFinding("missing_required_file", f"Eksik UI/rapor dili dosyası: {rel}"))
            continue
        content = _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"{rel} :: {token}")
            else:
                report.findings.append(UiLanguageFinding("missing_required_token", f"Eksik UI/rapor dili izi: {rel} :: {token}"))

    for rel, tokens in UI_OPTIONAL_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Opsiyonel UI/rapor dili alanı yok/kapsam dışı: {rel}")
            continue
        content = "\n".join(_read(p) for p in _iter_text_files(path)) if path.is_dir() else _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"Opsiyonel UI/rapor dili doğrulandı: {rel} :: {token}")
            else:
                report.ok.append(f"Opsiyonel UI/rapor dili izi eksik ama bloklayıcı değil: {rel} :: {token}")

def _check_forbidden_patterns(root: Path, report: UiLanguageReport) -> None:
    for rel, patterns in UI_FORBIDDEN_PATTERNS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Yasak UI/rapor dili alanı yok veya kapsam dışı: {rel}")
            continue
        for file_path in _iter_text_files(path):
            content = _read(file_path)
            for pattern in patterns:
                if re.search(pattern, content, flags=re.IGNORECASE | re.MULTILINE):
                    report.findings.append(UiLanguageFinding("forbidden_ui_language", f"Yasak/eski UI dili: {file_path.relative_to(root)} :: {pattern}"))
                else:
                    report.ok.append(f"Yasak UI dili yok: {file_path.relative_to(root)} :: {pattern}")

def normalize_performance_term(label: str) -> str:
    normalized = (label or "").strip()
    if normalized.casefold() in {"yetkinlik", "yetkinlikler", "kompetans", "competency", "competencies"}:
        return "Değerlendirme Kriterleri"
    if re.search(r"ekip\s+kıyas|ekip\s+analizi", normalized, flags=re.IGNORECASE):
        return "Personel Analizi"
    return normalized

def build_manager_status_label(*, manager_level: int, score_enabled: bool, pending: bool = True) -> str:
    if not pending:
        return "Tamamlandı"
    if manager_level == 3 and not score_enabled:
        return "3. amir yorum/görüş bekliyor"
    if manager_level == 3 and score_enabled:
        return "3. amir puanlama bekliyor"
    if manager_level in {1, 2}:
        return f"{manager_level}. amir puanlama bekliyor"
    return "Görev bekliyor"

def build_publication_status_label(*, is_published: bool, has_blocker: bool = False) -> str:
    if is_published:
        return "Sonuçlar yayımlandı"
    if has_blocker:
        return "Yayın ön kontrol blokajı"
    return "Yayın bekliyor"

def _check_language_simulations(report: UiLanguageReport) -> None:
    term_cases = [
        ("Yetkinlik", "Değerlendirme Kriterleri", "eski yetkinlik terimi dönüşür"),
        ("yetkinlikler", "Değerlendirme Kriterleri", "çoğul yetkinlik terimi dönüşür"),
        ("Ekip Kıyas", "Personel Analizi", "eski ekip kıyas terimi dönüşür"),
        ("Personel Analizi", "Personel Analizi", "doğru karşılaştırma terimi korunur"),
    ]
    for given, expected, label in term_cases:
        result = normalize_performance_term(given)
        if result == expected:
            report.ok.append(f"Terminoloji simülasyonu doğru: {label}")
        else:
            report.findings.append(UiLanguageFinding("term_normalization_contract", f"Terminoloji dönüşümü hatalı: {label} -> {result}"))

    status_cases = [
        (3, False, "3. amir yorum/görüş bekliyor", "3. amir yorum modu puan bekliyor demez"),
        (3, True, "3. amir puanlama bekliyor", "3. amir puan modu doğru statü üretir"),
        (2, True, "2. amir puanlama bekliyor", "2. amir puanlama statüsü doğru"),
        (1, True, "1. amir puanlama bekliyor", "1. amir puanlama statüsü doğru"),
    ]
    for level, score_enabled, expected, label in status_cases:
        result = build_manager_status_label(manager_level=level, score_enabled=score_enabled)
        if result == expected:
            report.ok.append(f"Statü dili simülasyonu doğru: {label}")
        else:
            report.findings.append(UiLanguageFinding("status_language_contract", f"Statü dili hatalı: {label} -> {result}"))

    publish_cases = [
        (True, False, "Sonuçlar yayımlandı", "yayın başarılı mavi buton/metin sözleşmesi"),
        (False, True, "Yayın ön kontrol blokajı", "blokaj varsa yayın engeli açık görünür"),
        (False, False, "Yayın bekliyor", "yayınlanmamış sonuç bekliyor görünür"),
    ]
    for published, blocker, expected, label in publish_cases:
        result = build_publication_status_label(is_published=published, has_blocker=blocker)
        if result == expected:
            report.ok.append(f"Yayın dili simülasyonu doğru: {label}")
        else:
            report.findings.append(UiLanguageFinding("publication_language_contract", f"Yayın dili hatalı: {label} -> {result}"))

def build_ui_report_language_gate_report(project_root: str | Path | None = None) -> UiLanguageReport:
    root = Path(project_root or Path.cwd()).resolve()
    report = UiLanguageReport()
    _check_required_tokens(root, report)
    _check_forbidden_patterns(root, report)
    _check_language_simulations(report)
    return report

def format_ui_report_language_report(report: UiLanguageReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Performans UI/Rapor Terminoloji ve Statü Dili Kapısı | {status}",
        f"version={report.version}",
        f"OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
        "",
        "Sözleşme özeti:",
        "- Ana terim: Değerlendirme Kriterleri.",
        "- Karşılaştırma ekranı: Personel Analizi.",
        "- 3. amir yorum modunda statü dili: yorum/görüş bekliyor.",
        "- Yayın sonrası görünür metin: Sonuçlar yayımlandı.",
        "- Yayın ön kontrol blokajları personel görünürlüğünü atlayamaz.",
    ]
    if report.findings:
        lines.append("")
        lines.append("Bulgular:")
        for finding in report.findings:
            lines.append(f"- {finding.severity.upper()} | {finding.code} | {finding.message}")
    return "\n".join(lines)

__all__ = [
    "UI_REPORT_LANGUAGE_COMPILE_TARGETS",
    "UI_REPORT_LANGUAGE_GATE_VERSION",
    "UI_REQUIRED_TOKENS",
    "UiLanguageFinding",
    "UiLanguageReport",
    "build_manager_status_label",
    "build_publication_status_label",
    "build_ui_report_language_gate_report",
    "format_ui_report_language_report",
    "normalize_performance_term",
]
