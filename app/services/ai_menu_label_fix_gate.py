
"""BYS360 AI Karar Destek menü terimi düzeltme gate'i.

Bu gate canlı veri değiştirmez. Sadece ana menü ve ilgili görünür ekranlarda
"AI Karar Destek" teriminin görünür hale geldiğini doğrular.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

GATE_VERSION = "2026-04-21-ai-menu-label-fix-gate"
SUCCESS_SIGNATURE = "AI_MENU_LABEL_FIX_GATE_OK"

REQUIRED_FILES = (
    "app/menu_registry.py",
    "app/templates/base.html",
    "app/templates/admin_ai_center.html",
    "app/main_handlers/account_handlers.py",
)

REQUIRED_PATTERNS = (
    ("menu_registry.ai_section", "app/menu_registry.py", r'"key"\s*:\s*"ai"[\s\S]{0,260}?"label"\s*:\s*"AI Karar Destek Merkezi"'),
    ("base.sidebar_label", "app/templates/base.html", r"AI Karar Destek Merkezi"),
    ("admin_ai_center.title", "app/templates/admin_ai_center.html", r"AI Karar Destek Merkezi"),
    ("account_profiles.group_alias", "app/main_handlers/account_handlers.py", r"AI Karar Destek Merkezi"),
)

@dataclass
class Check:
    status: str
    key: str
    message: str
    detail: str = ""

@dataclass
class Report:
    version: str
    generated_at_utc: str
    ok: int = 0
    errors: int = 0
    warnings: int = 0
    checks: list[Check] = field(default_factory=list)

    def add(self, status: str, key: str, message: str, detail: str = "") -> None:
        self.checks.append(Check(status=status, key=key, message=message, detail=detail))
        if status == "OK":
            self.ok += 1
        elif status == "HATA":
            self.errors += 1
        else:
            self.warnings += 1

    def passed(self) -> bool:
        return self.errors == 0

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")

def build_ai_menu_label_fix_report(root: Path) -> Report:
    report = Report(version=GATE_VERSION, generated_at_utc=datetime.now(timezone.utc).isoformat())

    for rel in REQUIRED_FILES:
        path = root / rel
        if path.exists():
            report.add("OK", f"file.exists.{rel}", f"Dosya mevcut: {rel}")
        else:
            report.add("HATA", f"file.missing.{rel}", f"Dosya eksik: {rel}")

    for key, rel, pattern in REQUIRED_PATTERNS:
        path = root / rel
        if not path.exists():
            continue
        text = _read(path)
        if re.search(pattern, text, flags=re.UNICODE):
            report.add("OK", key, f"Beklenen AI Karar Destek terimi bulundu: {rel}")
        else:
            report.add("HATA", key, f"Beklenen AI Karar Destek terimi bulunamadı: {rel}")

    base = root / "app" / "templates" / "base.html"
    if base.exists():
        text = _read(base)
        if "<span>Karar Destek Merkezi</span>" in text and "<span>AI Karar Destek Merkezi</span>" not in text:
            report.add("HATA", "base.sidebar.old_label_only", "Ana menüde AI ön eki olmayan eski etiket tek başına kaldı.")
        else:
            report.add("OK", "base.sidebar.old_label_guard", "Ana menü AI Karar Destek terimini gösterecek durumda.")

    return report

def _as_dict(report: Report) -> dict[str, object]:
    return {
        "version": report.version,
        "generated_at_utc": report.generated_at_utc,
        "ok": report.ok,
        "errors": report.errors,
        "warnings": report.warnings,
        "passed": report.passed(),
        "checks": [check.__dict__ for check in report.checks],
    }

def write_ai_menu_label_fix_reports(report: Report, root: Path) -> dict[str, str]:
    report_dir = root / "reports" / "refactor"
    doc_dir = root / "docs" / "refactor" / "generated"
    report_dir.mkdir(parents=True, exist_ok=True)
    doc_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "ai_menu_label_fix_gate.json"
    md_path = report_dir / "ai_menu_label_fix_gate.md"
    doc_path = doc_dir / "ai_menu_label_fix_gate.md"

    json_path.write_text(json.dumps(_as_dict(report), ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 AI Karar Destek Menü Terimi Fix Gate",
        "",
        f"- Versiyon: `{report.version}`",
        f"- Üretim zamanı: `{report.generated_at_utc}`",
        f"- Sonuç: `{'PASS' if report.passed() else 'FAIL'}`",
        f"- OK: `{report.ok}`",
        f"- HATA: `{report.errors}`",
        f"- UYARI: `{report.warnings}`",
        "",
        "## Kontroller",
        "",
    ]
    for check in report.checks:
        lines.append(f"- **{check.status}** `{check.key}` — {check.message}")
        if check.detail:
            lines.append(f"  - {check.detail}")
    lines.append("")
    if report.passed():
        lines.append(f"`{SUCCESS_SIGNATURE}`")

    md = "\n".join(lines)
    md_path.write_text(md, encoding="utf-8")
    doc_path.write_text(md, encoding="utf-8")

    return {"json": str(json_path), "md": str(md_path), "doc": str(doc_path)}

def format_ai_menu_label_fix_report(report: Report) -> str:
    lines = [
        f"BYS360 AI Karar Destek Menü Terimi Fix Gate | {'PASS' if report.passed() else 'FAIL'}",
        f"version={report.version}",
        f"OK={report.ok} HATA={report.errors} UYARI={report.warnings}",
    ]
    if report.errors:
        lines.append("")
        lines.append("Hatalar:")
        for check in report.checks:
            if check.status == "HATA":
                lines.append(f"- HATA | {check.key} | {check.message}")
    if report.passed():
        lines.append("")
        lines.append(SUCCESS_SIGNATURE)
    return "\n".join(lines)
