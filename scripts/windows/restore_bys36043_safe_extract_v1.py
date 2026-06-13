from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Iterable

VERSION = "BYS360_LIVE_RESTORE_FROM_BYS36043_V1"

EXCLUDED_DIR_NAMES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "ENV",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".quality_backup", "backup", "backups", "logs", "log", "instance",
    "node_modules", "build", "dist", ".dart_tool", ".gradle", ".idea", ".vscode",
    "htmlcov", ".coverage_data",
}
EXCLUDED_FILE_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development", ".env.test",
    "bys360.log", "waitress.log",
}
EXCLUDED_SUFFIXES = {
    ".pyc", ".pyo", ".log", ".tmp", ".temp", ".bak", ".orig", ".old",
}
PROTECTED_REL_PREFIXES = (
    "app/static/uploads/",
    "uploads/",
    "instance/",
    "logs/",
    "backups/",
)
MANAGED_TOPS = {
    "app", "config", "docs", "migrations", "mobile_flutter", "payload", "reports", "scripts",
    "seeds", "sql", "tests", "var",
}
MANAGED_ROOT_FILES = {
    "alembic.ini", "config.py", "wsgi.py", "requirements.txt", "pyproject.toml", "README.md",
    "run.py", "app.py", "gunicorn.conf.py",
}


def norm_rel(path: str) -> str:
    return path.replace("\\", "/").lstrip("/")


def strip_known_root(name: str) -> str:
    name = norm_rel(name)
    parts = [p for p in name.split("/") if p not in {"", "."}]
    if len(parts) >= 2 and parts[0].lower() == "bys360" and parts[1].lower() == "project":
        return "/".join(parts[2:])
    if len(parts) >= 1 and parts[0].lower() == "project":
        return "/".join(parts[1:])
    return "/".join(parts)


def is_excluded(rel: str) -> tuple[bool, str]:
    rel = norm_rel(rel)
    if not rel:
        return True, "empty"
    low = rel.lower()
    if any(low.startswith(prefix.lower()) for prefix in PROTECTED_REL_PREFIXES):
        return True, "protected_runtime_path"
    parts = rel.split("/")
    for part in parts:
        if part in EXCLUDED_DIR_NAMES:
            return True, f"excluded_dir:{part}"
    name = parts[-1]
    if name in EXCLUDED_FILE_NAMES or name.startswith(".env"):
        return True, "excluded_env_or_runtime_file"
    suffix = Path(name).suffix.lower()
    if suffix in EXCLUDED_SUFFIXES:
        return True, f"excluded_suffix:{suffix}"
    if any(token in name.lower() for token in ("backup_before", ".backup_", ".before_")):
        return True, "excluded_backup_file"
    top = parts[0]
    if len(parts) == 1:
        if top in MANAGED_ROOT_FILES:
            return False, "root_file"
        # root-level random files are not part of the live app sync.
        return True, "unmanaged_root_file"
    if top not in MANAGED_TOPS:
        return True, f"unmanaged_top:{top}"
    return False, "included"


def iter_source_entries(source_zip: Path) -> Iterable[tuple[zipfile.ZipInfo, str]]:
    with zipfile.ZipFile(source_zip) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            rel = strip_known_root(info.filename)
            excluded, _reason = is_excluded(rel)
            if excluded:
                continue
            yield info, rel


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def make_preflight_report(source_zip: Path) -> dict:
    total = 0
    included = 0
    excluded = 0
    reasons: dict[str, int] = {}
    roots: dict[str, int] = {}
    total_included_bytes = 0
    with zipfile.ZipFile(source_zip) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            total += 1
            rel = strip_known_root(info.filename)
            exc, reason = is_excluded(rel)
            reasons[reason] = reasons.get(reason, 0) + 1
            root = rel.split("/", 1)[0] if rel else "<empty>"
            roots[root] = roots.get(root, 0) + 1
            if exc:
                excluded += 1
            else:
                included += 1
                total_included_bytes += int(info.file_size or 0)
    return {
        "version": VERSION,
        "source_zip": str(source_zip),
        "source_zip_size_bytes": source_zip.stat().st_size,
        "total_files": total,
        "included_files": included,
        "excluded_files": excluded,
        "included_uncompressed_bytes": total_included_bytes,
        "excluded_reason_counts": dict(sorted(reasons.items())),
        "root_counts": dict(sorted(roots.items())),
    }


def copy_from_zip(source_zip: Path, project_root: Path, report_dir: Path) -> dict:
    copied = 0
    bytes_copied = 0
    copied_samples: list[str] = []
    with zipfile.ZipFile(source_zip) as zf:
        for info, rel in iter_source_entries(source_zip):
            target = project_root / Path(rel)
            # Zip-slip guard.
            try:
                target.resolve().relative_to(project_root.resolve())
            except ValueError:
                raise RuntimeError(f"Güvensiz zip yolu reddedildi: {info.filename}")
            ensure_parent(target)
            with zf.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            try:
                mtime = time.mktime(info.date_time + (0, 0, -1))
                os.utime(target, (mtime, mtime))
            except Exception:
                pass
            copied += 1
            bytes_copied += int(info.file_size or 0)
            if len(copied_samples) < 80:
                copied_samples.append(rel)
    return {"copied_files": copied, "copied_bytes": bytes_copied, "copied_samples": copied_samples}


def main() -> int:
    ap = argparse.ArgumentParser(description="Safely restore BYS360 live code from bys360 (43).zip without overwriting runtime secrets.")
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--source-zip", required=True)
    ap.add_argument("--work-dir", required=True)
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    source_zip = Path(args.source_zip).resolve()
    work_dir = Path(args.work_dir).resolve()
    report_dir = work_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    if not project_root.exists():
        raise FileNotFoundError(f"ProjectRoot bulunamadı: {project_root}")
    if not source_zip.exists():
        raise FileNotFoundError(f"Kaynak zip bulunamadı: {source_zip}")
    if not zipfile.is_zipfile(source_zip):
        raise RuntimeError(f"Geçerli zip değil: {source_zip}")

    preflight = make_preflight_report(source_zip)
    (report_dir / "preflight_report.json").write_text(json.dumps(preflight, ensure_ascii=False, indent=2), encoding="utf-8")

    # Extra guard: a full project zip must contain the expected source files.
    if preflight["included_files"] < 100:
        raise RuntimeError("Kaynak zip içinde canlıya uygulanacak yeterli proje dosyası bulunamadı.")

    result = copy_from_zip(source_zip, project_root, report_dir)
    final_report = {**preflight, **result, "project_root": str(project_root), "report_dir": str(report_dir)}
    (report_dir / "restore_report.json").write_text(json.dumps(final_report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(final_report, ensure_ascii=False, indent=2))
    print(f"{VERSION}_COPY_OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"{VERSION}_COPY_FAIL")
        print(str(exc))
        raise
