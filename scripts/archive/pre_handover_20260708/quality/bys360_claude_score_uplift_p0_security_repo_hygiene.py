from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P0_SECURITY_REPO_HYGIENE_V1"

EXAMPLE_ENV_NAMES = {
    ".env.example",
    ".env.production.example",
    ".env.docker.example",
    ".env.template",
    ".env.sample",
    ".env.local.example",
}

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "dist",
    "build",
    "htmlcov",
    "reports",
    "logs",
    "uploads",
    "instance",
    "_security_quarantine",
    "_cleanup_quarantine",
}

LOCAL_ONLY_DIRS = {
    ".venv",
    "venv",
    "env",
    "backups",
    "backup",
    "archive",
    "payload",
    "overlay_payload",
    "phase_overlay",
    "_security_quarantine",
    "_cleanup_quarantine",
}

SECRET_PATTERNS = [
    ("database_url_with_password", re.compile(r"postgres(?:ql)?(?:\+\w+)?://[^\s:@]+:[^\s:@]+@", re.I)),
    ("hardcoded_secret_key", re.compile(r"(?i)(SECRET_KEY\s*=\s*)(?!CHANGE|<|$)[^\s#]+")),
    ("hardcoded_tckn_key", re.compile(r"(?i)(TCKN_ENCRYPTION_KEY\s*=\s*)(?!CHANGE|<|$)[^\s#]+")),
    ("hardcoded_postgres_password", re.compile(r"(?i)(POSTGRES_PASSWORD\s*=\s*)(?!CHANGE|<|$)[^\s#]+")),
    ("meta_or_api_token", re.compile(r"(?i)(ACCESS_TOKEN|API_KEY|PRIVATE_KEY|CLIENT_SECRET)\s*=\s*(?!CHANGE|<|$)[^\s#]+")),
]

PIN_REPLACEMENTS = {
    "prometheus-client>=0.20.0": "prometheus-client==0.20.0",
    "Flask-Limiter>=3.5.0": "Flask-Limiter==3.5.0",
    "pip-audit>=2.7.0": "pip-audit==2.7.0",
}

GITIGNORE_BLOCK = """
# --- BYS360 Maintenance score uplift P0 security/repo hygiene V1 ---
# Real secrets and local runtime configuration must never be committed.
.env
.env.*
!.env.example
!.env.production.example
!.env.docker.example
!.env.template
!.env.sample
!.env.local.example
.flaskenv

# Local Python environments and generated caches.
.venv/
venv/
env/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.cache/

# Runtime/generated data.
logs/
reports/
uploads/
instance/
*.log
*.dump
*.db
*.sqlite
*.sqlite3

# Local backups, overlays and repair payloads.
backups/
backup/
archive/
payload/
overlay_payload/
phase*_overlay/
_security_quarantine/
_cleanup_quarantine/
*.bak
*.bak_*
*.backup
*.backup*
*.old
*.orig
*.tmp
*_before_*
*.key
*.pem
*.p12
*.pfx
*.ppk
*.jks
*.keystore
# --- /BYS360 Maintenance score uplift P0 security/repo hygiene V1 ---
""".strip()

DOCKERIGNORE_BLOCK = """
# --- BYS360 Maintenance score uplift P0 security/repo hygiene V1 ---
.env
.env.*
!.env.example
!.env.production.example
!.env.docker.example
.venv
venv
.git
.gitignore
reports
logs
uploads
instance
backups
backup
archive
payload
overlay_payload
_security_quarantine
_cleanup_quarantine
*.bak
*.backup
*.old
*.orig
*.tmp
*.dump
*.db
*.sqlite
*.sqlite3
*.key
*.pem
*.p12
*.pfx
*.ppk
*.jks
*.keystore
# --- /BYS360 Maintenance score uplift P0 security/repo hygiene V1 ---
""".strip()

@dataclass
class Report:
    package: str
    generated_at: str
    root: str
    mode: str
    changed: list[str] = field(default_factory=list)
    quarantined: list[str] = field(default_factory=list)
    findings: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


def now_slug() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p)


def is_binary(path: Path) -> bool:
    try:
        data = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\0" in data


def iter_project_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.relative_to(root).parts)
        if parts & IGNORE_DIRS:
            continue
        yield p


def ensure_block(path: Path, block: str, report: Report, marker: str) -> None:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + "\n" + block + "\n", encoding="utf-8")
    report.changed.append(rel(path.parent if path.parent != path else path, path))


def patch_requirements(root: Path, report: Report) -> None:
    req = root / "requirements.txt"
    if not req.exists():
        report.warnings.append("requirements.txt bulunamadı; pin düzeltmesi atlandı.")
        return
    text = req.read_text(encoding="utf-8", errors="replace")
    new = text
    for old, replacement in PIN_REPLACEMENTS.items():
        new = new.replace(old, replacement)
    if new != text:
        req.write_text(new, encoding="utf-8")
        report.changed.append("requirements.txt")


def patch_ci(root: Path, report: Report) -> None:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.exists():
        report.warnings.append(".github/workflows bulunamadı; CI düzeltmesi atlandı.")
        return
    for wf in workflow_dir.glob("*.yml"):
        text = wf.read_text(encoding="utf-8", errors="replace")
        new = text.replace("      - name: Dependency vulnerability audit\n        continue-on-error: true\n        run: python -m pip_audit -r requirements.txt",
                           "      - name: Dependency vulnerability audit\n        run: python -m pip_audit -r requirements.txt --progress-spinner off")
        new = new.replace("        continue-on-error: true\n        run: python -m pip_audit -r requirements.txt",
                           "        run: python -m pip_audit -r requirements.txt --progress-spinner off")
        if "BYS360 secret/repo gate" not in new:
            needle = "      - name: Compile Python source\n"
            gate = (
                "      - name: BYS360 secret/repo gate\n"
                "        run: python scripts/quality/bys360_secret_repo_gate.py --root .\n\n"
            )
            new = new.replace(needle, gate + needle)
        if new != text:
            wf.write_text(new, encoding="utf-8")
            report.changed.append(rel(root, wf))


def quarantine_path(root: Path, path: Path, quarantine_root: Path, report: Report) -> None:
    target = quarantine_root / rel(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(path), str(target))
        else:
            if target.exists():
                target.unlink()
            shutil.move(str(path), str(target))
        report.quarantined.append(rel(root, path))


def quarantine_local_only(root: Path, report: Report, apply: bool) -> None:
    quarantine_root = root.parent / "backups" / "security_repo_hygiene_quarantine" / now_slug()
    # Root-level .env and local env variants.
    candidates: list[Path] = []
    for p in root.glob(".env*"):
        if p.name not in EXAMPLE_ENV_NAMES:
            candidates.append(p)
    # Root-level generated/local directories.
    for name in LOCAL_ONLY_DIRS:
        p = root / name
        if p.exists() and p.is_dir():
            candidates.append(p)
    # Backup-like files inside source tree.
    backup_patterns = ("*.bak", "*.bak_*", "*.backup", "*.backup*", "*.old", "*.orig", "*.tmp")
    for pattern in backup_patterns:
        candidates.extend([p for p in root.rglob(pattern) if p.is_file() and ".git" not in p.parts])
    # De-duplicate and avoid moving files already under quarantine/report dirs.
    uniq: list[Path] = []
    seen: set[Path] = set()
    for p in candidates:
        if not p.exists():
            continue
        try:
            rr = p.relative_to(root)
        except ValueError:
            continue
        if rr.parts and rr.parts[0] in {"reports", "logs", "_security_quarantine", "_cleanup_quarantine"}:
            continue
        if p not in seen:
            uniq.append(p); seen.add(p)
    if not apply:
        for p in uniq:
            report.findings.append({"type": "quarantine_candidate", "path": rel(root, p), "detail": "Yerel/secret/yedek üretim artefaktı"})
        return
    for p in sorted(uniq, key=lambda x: len(x.parts), reverse=True):
        if p.exists():
            quarantine_path(root, p, quarantine_root, report)


def scan_findings(root: Path, report: Report) -> None:
    # Root secret env files
    for p in root.glob(".env*"):
        if p.name not in EXAMPLE_ENV_NAMES:
            report.findings.append({"type": "secret_env_file", "path": rel(root, p), "detail": "Gerçek ortam dosyası proje kökünde duruyor"})
    # Secret-like content in active text files.
    for p in iter_project_files(root):
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".docx", ".xlsx", ".pptx", ".zip", ".pyc"}:
            continue
        if is_binary(p):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                # Do not leak secret value in report.
                report.findings.append({"type": name, "path": rel(root, p), "detail": "Gizli değer benzeri içerik bulundu; değer rapora yazılmadı"})
                break
    # CI weak gates.
    for wf in (root / ".github" / "workflows").glob("*.y*ml") if (root / ".github" / "workflows").exists() else []:
        text = wf.read_text(encoding="utf-8", errors="replace")
        if "pip_audit" in text and "continue-on-error: true" in text:
            report.findings.append({"type": "weak_ci_security_gate", "path": rel(root, wf), "detail": "pip-audit continue-on-error ile çalışıyor"})
    # Unpinned deps.
    req = root / "requirements.txt"
    if req.exists():
        for i, line in enumerate(req.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            clean = line.strip()
            if clean and not clean.startswith("#") and (">=" in clean or "<=" in clean or "~=" in clean):
                report.findings.append({"type": "unpinned_dependency", "path": f"requirements.txt:{i}", "detail": "Bağımlılık tam sürüme sabit değil"})


def write_reports(root: Path, report: Report) -> None:
    out = root / "reports" / "quality"
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "BYS360_MAINTENANCE_SCORE_UPLIFT_P0_SECURITY_REPO_HYGIENE_V1_REPORT.json"
    md_path = out / "BYS360_MAINTENANCE_SCORE_UPLIFT_P0_SECURITY_REPO_HYGIENE_V1_REPORT.md"
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# {PACKAGE} Raporu",
        "",
        f"- mode: `{report.mode}`",
        f"- generated_at: `{report.generated_at}`",
        f"- changed_count: `{len(report.changed)}`",
        f"- quarantined_count: `{len(report.quarantined)}`",
        f"- finding_count: `{len(report.findings)}`",
        "",
        "## Değişen Dosyalar",
    ]
    lines += [f"- `{x}`" for x in report.changed] or ["- Yok"]
    lines += ["", "## Karantinaya Alınanlar"]
    lines += [f"- `{x}`" for x in report.quarantined] or ["- Yok"]
    lines += ["", "## Bulgular"]
    if report.findings:
        lines += [f"- `{f['type']}` — `{f['path']}` — {f['detail']}" for f in report.findings]
    else:
        lines += ["- Kritik bulgu yok."]
    lines += ["", "## Sonraki Zorunlu Aksiyonlar"]
    lines += [f"- {x}" for x in report.next_actions]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", choices=["audit", "all", "strict"], default="audit")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    apply = args.mode in {"all", "strict"}
    report = Report(
        package=PACKAGE,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        root=str(root),
        mode=args.mode,
    )
    if not root.exists():
        raise SystemExit(f"Project root bulunamadı: {root}")

    if apply:
        ensure_block(root / ".gitignore", GITIGNORE_BLOCK, report, "BYS360 Maintenance score uplift P0")
        ensure_block(root / ".dockerignore", DOCKERIGNORE_BLOCK, report, "BYS360 Maintenance score uplift P0")
        patch_requirements(root, report)
        patch_ci(root, report)
    quarantine_local_only(root, report, apply=apply)
    scan_findings(root, report)
    report.next_actions = [
        "Canlı veritabanı parolasını, SECRET_KEY değerini, TCKN_ENCRYPTION_KEY değerini ve tüm harici tokenları rotate edin.",
        "Git geçmişinde gerçek secret varsa docs/security/BYS360_SECRET_ROTATION_AND_HISTORY_CLEANUP_RUNBOOK.md adımlarını uygulayın.",
        "Yeni .env dosyasını sadece sunucu/local ortamda oluşturun; repoya eklemeyin.",
        "P0 gate temiz geçtikten sonra P1 mimari route konsolidasyonu ve mobile/routes.py parçalama fazına geçin.",
    ]
    write_reports(root, report)
    print(json.dumps({
        "ok": True,
        "package": PACKAGE,
        "mode": args.mode,
        "changed_count": len(report.changed),
        "quarantined_count": len(report.quarantined),
        "finding_count": len(report.findings),
        "report": str(root / "reports" / "quality" / "BYS360_MAINTENANCE_SCORE_UPLIFT_P0_SECURITY_REPO_HYGIENE_V1_REPORT.json"),
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
