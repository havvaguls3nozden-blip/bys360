from __future__ import annotations

import argparse
import json
import re
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

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
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=True,
            capture_output=True,
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