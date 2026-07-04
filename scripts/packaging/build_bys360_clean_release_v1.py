from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    "node_modules", "backups", "backup", "archive", "logs", "reports", "releases", "instance", "uploads",
    "_local_secrets", "_security_quarantine", "_cleanup_quarantine", ".dart_tool", "build",
}
EXCLUDED_NAMES = {".env", ".env.local", ".env.production", ".env.staging"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".dump", ".log", ".bak", ".backup", ".old", ".orig", ".tmp", ".env", ".apk", ".aab", ".zip", ".7z", ".rar"}
ALLOW_PATTERNS = {".env.example", ".env.production.example", ".env.docker.example"}


def should_skip(path: Path, root: Path) -> tuple[bool, str]:
    rel = path.relative_to(root)
    parts = set(rel.parts)
    name = path.name
    if parts & EXCLUDED_DIRS:
        return True, "excluded_dir"
    if name in ALLOW_PATTERNS:
        return False, ""
    if name in EXCLUDED_NAMES or (name.startswith(".env.") and name not in ALLOW_PATTERNS):
        return True, "secret_env"
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True, "runtime_or_archive_file"
    return False, ""


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 temiz teslim paketi üretir")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-root", default="../releases")
    parser.add_argument("--name", default="BYS360_SCORE10_CLEAN_SOURCE")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = output_root / f"{args.name}_{stamp}.zip"
    manifest_path = output_root / f"{args.name}_{stamp}.manifest.json"
    sha_path = output_root / f"{args.name}_{stamp}.sha256.txt"

    included: list[dict[str, object]] = []
    excluded: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_dir():
                continue
            skip, reason = should_skip(path, root)
            rel = path.relative_to(root).as_posix()
            if skip:
                excluded.append({"path": rel, "reason": reason})
                continue
            zf.write(path, f"bys360/project/{rel}")
            included.append({"path": rel, "size": path.stat().st_size})

    digest = file_sha256(zip_path)
    manifest = {
        "name": args.name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "zip": str(zip_path),
        "sha256": digest,
        "included_count": len(included),
        "excluded_count": len(excluded),
        "excluded_reasons": sorted({row["reason"] for row in excluded}),
        "excluded_samples": excluded[:200],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    print("OK: BYS360 temiz kaynak paketi üretildi.")
    print(f"ZIP: {zip_path}")
    print(f"SHA256: {sha_path}")
    print(f"MANIFEST: {manifest_path}")
    print(f"INCLUDED: {len(included)}")
    print(f"EXCLUDED: {len(excluded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
