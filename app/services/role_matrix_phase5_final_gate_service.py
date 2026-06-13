
"""BYS360 Rol Matrisi Faz 5 final doğrulama servisi.

Bu servis canlı davranışı değiştirmez, veritabanına yazmaz ve migration
çalıştırmaz. Faz 1-4 çıktılarının tek final kapısından geçmesini sağlar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import subprocess
import sys


FINAL_REQUIRED_FILES = [
    Path("docs/role_matrices/README.md"),
    Path("docs/role_matrices/BYS360_MODUL_BAZLI_ROL_MATRISI.md"),
    Path("docs/project_file_addendums/README.md"),
    Path("app/admin/role_matrix_routes.py"),
    Path("app/services/role_matrix_ui_service.py"),
    Path("app/templates/admin/role_matrix_center.html"),
    Path("app/admin/route_manifest.py"),
    Path("app/templates/settings.html"),
    Path("docs/role_matrices/PHASE4_GATE.md"),
    Path("docs/role_matrices/PHASE4_CANLI_ONCESI_YETKI_KONTROL_LISTESI.md"),
    Path("docs/role_matrices/PHASE5_FINAL_GATE.md"),
    Path("docs/role_matrices/PHASE5_FINAL_CANLI_KONTROL_LISTESI.md"),
]

PHASE_CHECKS = [
    ("Faz 1 Rol Matrisi Dokümantasyon", Path("scripts/check_role_matrix_docs.py")),
    ("Faz 2 Proje Dosyası Ek Metinleri", Path("scripts/check_role_matrix_phase2_addendums.py")),
    ("Faz 3 Rol Matrisi UI", Path("scripts/check_role_matrix_phase3_ui.py")),
    ("Faz 4 Rol-Yetki-Menü Gate", Path("scripts/check_role_matrix_phase4_gate.py")),
]

FINAL_REQUIRED_TERMS = [
    "Rol Matrisi",
    "Menü Görünürlüğü",
    "En az yetki",
    "audit log",
    "Sistem Ayarları ve Yetkilendirme",
    "Personel Yönetimi",
    "Performans Yönetimi",
    "İletişim, Anket ve Destek",
    "AI Karar Destek",
    "BYS360_ROLE_MATRIX_PHASE4_GATE_OK",
]


@dataclass
class PhaseCheckOutput:
    title: str
    script: str
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass
class Phase5FinalResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    checks: list[PhaseCheckOutput] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def passed_count(self) -> int:
        return sum(1 for check in self.checks if check.ok)

    @property
    def failed_count(self) -> int:
        return sum(1 for check in self.checks if not check.ok)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def run_phase_check(project_root: Path, title: str, script_rel: Path) -> PhaseCheckOutput:
    script_path = project_root / script_rel
    if not script_path.exists():
        return PhaseCheckOutput(
            title=title,
            script=str(script_rel),
            returncode=127,
            stdout="",
            stderr=f"Kontrol scripti bulunamadi: {script_rel}",
        )

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    return PhaseCheckOutput(
        title=title,
        script=str(script_rel),
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def validate_final_files(project_root: Path, result: Phase5FinalResult) -> None:
    for rel in FINAL_REQUIRED_FILES:
        path = project_root / rel
        if not path.exists():
            result.errors.append(f"Final zorunlu dosya eksik: {rel}")
            continue
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        if size < 120:
            result.errors.append(f"Final dosyasi zayif veya bos gorunuyor: {rel}")


def validate_final_terms(project_root: Path, result: Phase5FinalResult) -> None:
    target_files = [
        project_root / "docs/role_matrices/PHASE5_FINAL_GATE.md",
        project_root / "docs/role_matrices/PHASE5_FINAL_CANLI_KONTROL_LISTESI.md",
        project_root / "docs/role_matrices/PHASE4_GATE.md",
        project_root / "app/templates/admin/role_matrix_center.html",
        project_root / "app/services/role_matrix_ui_service.py",
    ]
    combined_parts: list[str] = []
    for path in target_files:
        if path.exists():
            combined_parts.append(read_text(path))
    combined = "\n".join(combined_parts)
    for term in FINAL_REQUIRED_TERMS:
        if term not in combined:
            result.errors.append(f"Final zorunlu ifade eksik: {term}")


def run_all_phase_checks(project_root: Path, result: Phase5FinalResult) -> None:
    for title, script_rel in PHASE_CHECKS:
        check = run_phase_check(project_root, title, script_rel)
        result.checks.append(check)
        if check.ok:
            result.facts.append(f"{title}: OK")
        else:
            result.errors.append(f"{title} basarisiz: {script_rel}")
            if check.stderr:
                result.errors.append(f"{title} stderr: {check.stderr.splitlines()[0]}")


def build_phase5_final_result(project_root: Path) -> Phase5FinalResult:
    result = Phase5FinalResult()
    validate_final_files(project_root, result)
    validate_final_terms(project_root, result)
    run_all_phase_checks(project_root, result)
    return result


def render_phase5_markdown_report(result: Phase5FinalResult) -> str:
    lines: list[str] = []
    lines.append("# BYS360 Rol Matrisi Faz 5 Final Gate Raporu")
    lines.append("")
    lines.append("## Sonuç")
    lines.append("")
    lines.append(f"- HATA: {len(result.errors)}")
    lines.append(f"- UYARI: {len(result.warnings)}")
    lines.append(f"- Geçen kontrol: {result.passed_count}")
    lines.append(f"- Başarısız kontrol: {result.failed_count}")
    lines.append("")
    lines.append("## Final Gate Kapsamı")
    lines.append("")
    lines.append("- Faz 1 rol matrisi dokümantasyon çekirdeği")
    lines.append("- Faz 2 proje dosyalarına eklenecek rol matrisi metinleri")
    lines.append("- Faz 3 Ayarlar ekranı Rol Matrisi UI omurgası")
    lines.append("- Faz 4 rol-yetki-menü görünürlüğü gate kontrolü")
    lines.append("- Menü Görünürlüğü, En az yetki ve audit log ilkeleri")
    lines.append("- Sistem Ayarları ve Yetkilendirme, Personel Yönetimi, Performans Yönetimi, İletişim, Anket ve Destek, AI Karar Destek başlıkları")
    lines.append("")
    lines.append("## Faz Kontrol Çıktıları")
    lines.append("")
    for check in result.checks:
        status = "OK" if check.ok else "HATA"
        lines.append(f"### {check.title} — {status}")
        lines.append("")
        lines.append(f"- Script: `{check.script}`")
        lines.append(f"- Return code: `{check.returncode}`")
        if check.stdout:
            lines.append("")
            lines.append("```text")
            lines.append(check.stdout[-4000:])
            lines.append("```")
        if check.stderr:
            lines.append("")
            lines.append("```text")
            lines.append(check.stderr[-2000:])
            lines.append("```")
        lines.append("")
    if result.errors:
        lines.append("## Hatalar")
        lines.append("")
        for error in result.errors:
            lines.append(f"- {error}")
        lines.append("")
    if result.warnings:
        lines.append("## Uyarılar")
        lines.append("")
        for warning in result.warnings:
            lines.append(f"- {warning}")
        lines.append("")
    if result.facts:
        lines.append("## Bulgular")
        lines.append("")
        for fact in result.facts:
            lines.append(f"- {fact}")
        lines.append("")
    lines.append("## Canlıya Geçiş Notu")
    lines.append("")
    lines.append("Faz 5 final gate, veritabanına yazmaz ve uygulama davranışını değiştirmez. Bu rapor, rol matrisi dokümantasyonu, Ayarlar ekranı bağlantısı, modül bazlı yetki politikası, Menü Görünürlüğü, En az yetki ve audit log ilkelerinin birlikte doğrulandığını göstermek için hazırlanır.")
    lines.append("")
    return "\n".join(lines)
