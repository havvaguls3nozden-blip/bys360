# -*- coding: utf-8 -*-
"""Build a BYS360 secure handover/release zip.
V1.3 excludes env templates from the zip and excludes old versioned security overlay scripts.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

OK = "BYS360_SECURE_RELEASE_BUILD_V1_3_OK"
FAIL = "BYS360_SECURE_RELEASE_BUILD_V1_3_FAIL"

EXCLUDE_DIR_NAMES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist_secure", "_upload_parts",
    "instance", "logs", "tmp", "temp", "backup", "backups",
}

EXCLUDE_SUFFIXES = {
    ".pyc", ".pyo", ".log", ".tmp", ".bak", ".zip", ".7z", ".rar", ".db", ".sqlite", ".sqlite3", ".dump",
}

EXCLUDE_NAMES = {
    ".env", ".env.example", ".env.local", ".env.production", ".env.pilot",
}

# Old overlay scripts are useful in source history but noisy in handover release.
OLD_SECURITY_SCRIPT_RE = re.compile(
    r"^(repair|check|build)_bys360_.*_v1(_1|_2)?\.(py|ps1)$",
    re.IGNORECASE,
)

# Conservative secret patterns checked on the finished zip.
SECRET_PATTERNS = [
    ("env_file", re.compile(r"(^|/|\\)\.env($|[./_\\-])", re.IGNORECASE)),
    ("sentry_placeholder", re.compile(r"SENTRY_DSN\s*=\s*https://\.\.\.", re.IGNORECASE)),
    ("hardcoded_initial_password", re.compile(r"(initial_password\s*=\s*[\"']123456[\"']|set_password\(\s*[\"']123456[\"']\s*\))", re.IGNORECASE)),
    ("known_weak_password_text", re.compile(r"(?<![A-Za-z0-9])123456(?![A-Za-z0-9])")),
]

ALLOWED_123456_PATH_PARTS = {
    "docs/", "README", "test", "tests", "sample", "example",
}


def is_excluded(project: Path, path: Path) -> bool:
    rel = path.relative_to(project).as_posix()
    parts = rel.split("/")
    if any(part in EXCLUDE_DIR_NAMES for part in parts[:-1]):
        return True
    name = path.name
    lower_name = name.lower()
    if lower_name in EXCLUDE_NAMES:
        return True
    if lower_name.startswith(".env"):
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    if rel.startswith("dist_secure/"):
        return True
    if rel.startswith("scripts/security/") and OLD_SECURITY_SCRIPT_RE.match(name):
        # Keep only current V1.3 scripts.
        if "v1_3" not in name.lower():
            return True
    if rel.startswith("scripts/windows/") and re.match(r"^build_bys360_secure_release_v1(_1|_2)?\.ps1$", name, re.IGNORECASE):
        return True
    return False


def scan_zip(zip_path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            lower = name.lower()
            if lower.endswith("/.env") or "/.env" in lower or lower.endswith(".env.example"):
                errors.append(f"release içinde env dosyası var: {name}")
                continue
            if info.file_size > 2_000_000:
                continue
            try:
                data = zf.read(info).decode("utf-8", errors="ignore")
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (scripts/security/build_bys360_secure_release_v1_3.py:88)")
                continue
            for label, pattern in SECRET_PATTERNS[1:]:
                if label == "known_weak_password_text" and any(part in name for part in ALLOWED_123456_PATH_PARTS):
                    continue
                if pattern.search(data):
                    errors.append(f"release içinde yasaklı değer bulundu: {label} -> {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project = Path(args.project_root).resolve()
    if not project.exists():
        print(FAIL)
        print(f" - ProjectRoot bulunamadı: {project}")
        return 1

    dist = project / "dist_secure"
    dist.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = dist / f"BYS360_SECURE_RELEASE_V1_3_{stamp}.zip"

    added = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in project.rglob("*"):
            if path.is_dir():
                continue
            if is_excluded(project, path):
                continue
            rel = path.relative_to(project).as_posix()
            zf.write(path, rel)
            added += 1

    errors = scan_zip(zip_path)
    if errors:
        try:
            zip_path.unlink()
        except OSError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (scripts/security/build_bys360_secure_release_v1_3.py)")
        print(FAIL)
        for err in errors:
            print(f" - {err}")
        return 1

    print(OK)
    print(f" - Dosya: {zip_path}")
    print(f" - Eklenen dosya sayısı: {added}")
    print(" - .env, .env.example, eski overlay scriptleri, log/dump/db/zip/cache dosyaları release dışı bırakıldı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
