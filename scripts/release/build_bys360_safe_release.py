from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

PACKAGE = "BYS360_SAFE_RELEASE_BUILDER_PHASE1_V1"

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


def iter_files_for_fallback(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = normalize(str(path.relative_to(root)))
        forbidden, _ = is_forbidden_archive_name(rel)
        if forbidden:
            continue
        yield path


def scan_zip(zip_path: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            forbidden, reason = is_forbidden_archive_name(info.filename)
            if forbidden:
                findings.append({"path": normalize(info.filename), "reason": reason})
    return findings


def build_with_git_archive(root: Path, output: Path) -> bool:
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "archive", "--format=zip", "-o", str(output), "HEAD"], cwd=root, check=True)
        return True
    except Exception:
        return False


def build_fallback_zip(root: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in iter_files_for_fallback(root):
            zf.write(path, normalize(str(path.relative_to(root))))


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

    used_git_archive = build_with_git_archive(root, output)
    if not used_git_archive:
        build_fallback_zip(root, output)

    findings = scan_zip(output)
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "BYS360_SAFE_RELEASE_BUILDER_PHASE1_REPORT.json"
    result = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "output": str(output),
        "used_git_archive": used_git_archive,
        "ok": not findings,
        "finding_count": len(findings),
        "findings": findings[:200],
        "rule": "Release paketinde instance, sqlite/db/dump/log/bak/env/keystore gibi local veya hassas dosyalar bulunamaz.",
    }
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "output": str(output), "finding_count": len(findings), "report": str(report_path)}, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
