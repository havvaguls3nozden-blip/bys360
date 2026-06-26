param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$OutputRoot = "C:\bys360\releases",
    [ValidateSet("all", "patch-only", "build-only")]
    [string]$Mode = "all",
    [switch]$RunCompile
)

$ErrorActionPreference = "Stop"

function Write-Section([string]$Text) {
    Write-Host ""
    Write-Host "=== $Text ===" -ForegroundColor Cyan
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $dir = Split-Path -Parent $Path
    if ($dir) { New-Item -ItemType Directory -Force $dir | Out-Null }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Add-Or-ReplaceBlock([string]$Path, [string]$Begin, [string]$End, [string]$Block) {
    if (Test-Path $Path) {
        $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    } else {
        $content = ""
    }
    $pattern = "(?s)`n?# $([regex]::Escape($Begin)).*?# $([regex]::Escape($End))`r?`n?"
    if ($content -match "# $([regex]::Escape($Begin))") {
        $content = [regex]::Replace($content, $pattern, "`r`n$Block`r`n")
    } else {
        if ($content.Trim().Length -gt 0) { $content = $content.TrimEnd() + "`r`n`r`n" }
        $content = $content + $Block + "`r`n"
    }
    Write-Utf8NoBom -Path $Path -Content $content
}

if (-not (Test-Path $ProjectRoot)) {
    throw "ProjectRoot bulunamadı: $ProjectRoot"
}

$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$BuilderPath = Join-Path $ProjectRoot "scripts\release\build_bys360_safe_release.py"
$GitIgnorePath = Join-Path $ProjectRoot ".gitignore"
$BackupRoot = Join-Path $ProjectRoot "backups\release_discipline_v1"
$ReportRoot = Join-Path $ProjectRoot "reports\quality"
New-Item -ItemType Directory -Force $BackupRoot, $ReportRoot, $OutputRoot | Out-Null

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

Write-Section "BYS360 V4 Release Discipline V1"
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "OutputRoot=$OutputRoot"
Write-Host "Mode=$Mode"
Write-Host "Python=$Python"

if ($Mode -in @("all", "patch-only")) {
    Write-Section "1) build_bys360_safe_release.py güvenli/filtreli sürüme alınıyor"

    if (Test-Path $BuilderPath) {
        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        Copy-Item -LiteralPath $BuilderPath -Destination (Join-Path $BackupRoot "build_bys360_safe_release.py.$stamp.bak") -Force
    }

    $BuilderCode = @'
from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

PACKAGE = "BYS360_SAFE_RELEASE_BUILDER_PHASE1_V2_FILTERED"

FORBIDDEN_DIR_PARTS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".idea", ".vscode", ".dart_tool",
    "instance", "logs", "uploads", "reports", "backups", "backup", "archive", "releases",
    "payload", "overlay_payload", "_security_quarantine", "_cleanup_quarantine", "_local_secrets",
}
FORBIDDEN_SUFFIXES = {
    ".sqlite3", ".sqlite", ".db", ".dump", ".bak", ".backup", ".old", ".orig",
    ".log", ".pyc", ".pyo", ".key", ".pem", ".p12", ".pfx", ".ppk", ".jks", ".keystore",
}
FORBIDDEN_NAME_PATTERNS = (
    re.compile(r"(^|/|\\)\.env($|\.)", re.I),
    re.compile(r"\.gitignore\.bak", re.I),
    re.compile(r"\.bak_", re.I),
    re.compile(r"disabled_by_rollback", re.I),
    re.compile(r"clean_package_manifest.*\.json$", re.I),
)


def normalize(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def is_forbidden_archive_name(name: str) -> tuple[bool, str]:
    n = normalize(name)
    parts = [p for p in n.split("/") if p]
    lower_parts = [p.lower() for p in parts]
    for part in lower_parts:
        if part in FORBIDDEN_DIR_PARTS:
            return True, f"yasak klasor parcasi: {part}"
    suffix = Path(parts[-1] if parts else n).suffix.lower()
    if suffix in FORBIDDEN_SUFFIXES:
        return True, f"yasak dosya uzantisi: {suffix}"
    for pattern in FORBIDDEN_NAME_PATTERNS:
        if pattern.search(n):
            return True, f"yasak dosya adi deseni: {pattern.pattern}"
    return False, ""


def _git_ls_files(root: Path) -> list[str] | None:
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return [item.decode("utf-8", errors="replace") for item in result.stdout.split(b"\0") if item]
    except Exception:
        return None


def iter_source_files(root: Path) -> tuple[str, list[tuple[Path, str]], list[dict[str, str]]]:
    git_files = _git_ls_files(root)
    included: list[tuple[Path, str]] = []
    excluded: list[dict[str, str]] = []

    if git_files is not None:
        source = "git-ls-files-filtered"
        candidates = [(root / rel, normalize(rel)) for rel in git_files]
    else:
        source = "filesystem-filtered"
        candidates = []
        for path in root.rglob("*"):
            if path.is_file():
                candidates.append((path, normalize(str(path.relative_to(root)))))

    for path, rel in candidates:
        forbidden, reason = is_forbidden_archive_name(rel)
        if forbidden:
            excluded.append({"path": rel, "reason": reason})
            continue
        if not path.exists() or not path.is_file():
            continue
        included.append((path, rel))

    return source, included, excluded


def build_filtered_zip(root: Path, output: Path) -> tuple[str, int, list[dict[str, str]]]:
    source, included, excluded = iter_source_files(root)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, rel in included:
            zf.write(path, rel)
    return source, len(included), excluded


def scan_zip(zip_path: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            forbidden, reason = is_forbidden_archive_name(info.filename)
            if forbidden:
                findings.append({"path": normalize(info.filename), "reason": reason})
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--audit-only", action="store_true", help="Paketi yine uretir ve sadece paket icindeki yasakli dosyalari denetler.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    source, included_count, excluded = build_filtered_zip(root, output)
    findings = scan_zip(output)
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "BYS360_SAFE_RELEASE_BUILDER_PHASE1_REPORT.json"
    manifest_path = report_dir / "BYS360_SAFE_RELEASE_BUILDER_PHASE1_MANIFEST.json"
    result = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "output": str(output),
        "source": source,
        "included_count": included_count,
        "excluded_count": len(excluded),
        "excluded_sample": excluded[:200],
        "ok": not findings,
        "finding_count": len(findings),
        "findings": findings[:200],
        "rule": "Release paketinde instance, sqlite/db/dump/log/bak/env/keystore gibi local veya hassas dosyalar bulunamaz.",
    }
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps({"included_count": included_count, "excluded": excluded}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "output": str(output), "finding_count": len(findings), "excluded_count": len(excluded), "report": str(report_path), "manifest": str(manifest_path)}, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
'@

    Write-Utf8NoBom -Path $BuilderPath -Content $BuilderCode

    Write-Section "2) .gitignore release hijyen bloğu senkronize ediliyor"
    $IgnoreBlock = @'
# BYS360_RELEASE_DISCIPLINE_V1_BEGIN
.env
.env.*
!.env.example
!.env.*.example
instance/
logs/
uploads/
.venv/
venv/
env/
node_modules/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
backups/
backup/
archive/
releases/
payload/
overlay_payload/
_local_secrets/
_security_quarantine/
_cleanup_quarantine/
*.sqlite3
*.sqlite
*.db
*.dump
*.log
*.bak
*.backup
*.old
*.orig
*.key
*.pem
*.p12
*.pfx
*.ppk
*.jks
*.keystore
# BYS360_RELEASE_DISCIPLINE_V1_END
'@
    Add-Or-ReplaceBlock -Path $GitIgnorePath -Begin "BYS360_RELEASE_DISCIPLINE_V1_BEGIN" -End "BYS360_RELEASE_DISCIPLINE_V1_END" -Block $IgnoreBlock
}

if ($Mode -in @("all", "build-only")) {
    Write-Section "3) Temiz release zip üretiliyor"
    $Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputZip = Join-Path $OutputRoot "BYS360_RELEASE_SAFE_$Stamp.zip"
    & $Python $BuilderPath --root $ProjectRoot --output $OutputZip
    if ($LASTEXITCODE -ne 0) {
        throw "Güvenli release üretimi başarısız. Raporu kontrol edin: $ReportRoot\BYS360_SAFE_RELEASE_BUILDER_PHASE1_REPORT.json"
    }

    Write-Section "4) Bağımsız zip kirlilik kontrolü"
    $AuditCode = @'
import json, re, sys, zipfile
from pathlib import Path
zip_path = Path(sys.argv[1])
patterns = [
    (re.compile(r"(^|/)\.env($|\.)", re.I), ".env/.env.*"),
    (re.compile(r"(^|/)\.venv/", re.I), ".venv"),
    (re.compile(r"(^|/)instance/", re.I), "instance"),
    (re.compile(r"(^|/)logs/", re.I), "logs"),
    (re.compile(r"(^|/)\.git/", re.I), ".git"),
    (re.compile(r"\.(sqlite3?|db|dump|log|bak|backup|old|orig|key|pem|p12|pfx|ppk|jks|keystore)$", re.I), "forbidden_suffix"),
]
findings = []
with zipfile.ZipFile(zip_path) as zf:
    for name in zf.namelist():
        n = name.replace("\\", "/")
        for rx, label in patterns:
            if rx.search(n):
                findings.append({"path": n, "rule": label})
                break
print(json.dumps({"ok": not findings, "zip": str(zip_path), "finding_count": len(findings), "findings": findings[:100]}, ensure_ascii=False, indent=2))
sys.exit(0 if not findings else 1)
'@
    $AuditTemp = Join-Path $env:TEMP "bys360_release_zip_audit_v1.py"
    Write-Utf8NoBom -Path $AuditTemp -Content $AuditCode
    & $Python $AuditTemp $OutputZip
    if ($LASTEXITCODE -ne 0) {
        throw "Bağımsız zip kirlilik kontrolü başarısız: $OutputZip"
    }

    if ($RunCompile) {
        Write-Section "5) Compile kontrolü"
        & $Python -m compileall -q (Join-Path $ProjectRoot "scripts") (Join-Path $ProjectRoot "app")
        if ($LASTEXITCODE -ne 0) { throw "compileall başarısız." }
    }

    Write-Section "6) Git durumu"
    git -C $ProjectRoot status --short

    Write-Host ""
    Write-Host "TEMİZ RELEASE HAZIR: $OutputZip" -ForegroundColor Green
    Write-Host "RAPOR: $ReportRoot\BYS360_SAFE_RELEASE_BUILDER_PHASE1_REPORT.json" -ForegroundColor Green
    Write-Host "MANIFEST: $ReportRoot\BYS360_SAFE_RELEASE_BUILDER_PHASE1_MANIFEST.json" -ForegroundColor Green
}
