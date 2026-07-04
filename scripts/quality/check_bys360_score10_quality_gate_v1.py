from __future__ import annotations

import argparse
import ast
import json
import os
import zipfile
from pathlib import Path
from typing import Iterable

PROJECT_MARKER = "BYS360_SCORE10_QUALITY_GATE_V1"
FORBIDDEN_PACKAGE_PARTS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    "backups",
    "backup",
    "archive",
    "logs",
    "reports",
    "releases",
    "instance",
}
FORBIDDEN_FILE_NAMES = {".env", ".env.local", ".env.production", ".env.staging"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".dump", ".log", ".bak", ".backup", ".old", ".orig", ".env"}
REQUIRED_TOKENS = {
    "app/services/cic/misc_context.py": ["from app.services.mail_core import create_mail_log, send_email", "send_email = None"],
    "app/api/mobile/services/performance_task_helpers.py": ["_DONE = {", "published"],
    "config.py": ["def _normalize_database_url", "def _portable_sqlite_url", "_normalized_database_url"],
    ".releaseignore": ["BYS360_SCORE10_RELEASE_HYGIENE_V1", ".env", ".venv/", ".git/"],
    ".env.example": ["DATABASE_URL=sqlite:///instance/bys360_local_dev.sqlite3"],
}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def check_required_tokens(root: Path) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    for name, tokens in REQUIRED_TOKENS.items():
        path = root / name
        if not path.exists():
            problems.append({"path": name, "problem": "missing_file"})
            continue
        text = read_text(path)
        for token in tokens:
            if token not in text:
                problems.append({"path": name, "problem": "missing_token", "token": token})
    return problems


def check_python_syntax(root: Path) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    for base in (root / "app", root / "tests", root / "scripts"):
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if any(part in FORBIDDEN_PACKAGE_PARTS for part in path.parts):
                continue
            try:
                ast.parse(read_text(path), filename=str(path))
            except SyntaxError as exc:
                problems.append({"path": rel(path, root), "problem": "syntax_error", "line": str(exc.lineno), "detail": exc.msg})
    return problems


def check_local_secret_files(root: Path) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    for name in FORBIDDEN_FILE_NAMES:
        path = root / name
        if path.exists():
            problems.append({"path": name, "problem": "local_secret_present", "detail": "Temiz teslim paketine dahil edilmemeli."})
    return problems


def check_package_zip(path: Path) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    if not path.exists():
        return [{"path": str(path), "problem": "zip_not_found"}]
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            parts = [p for p in info.filename.replace("\\", "/").split("/") if p]
            if not parts:
                continue
            lowered_parts = {p.lower() for p in parts}
            filename = parts[-1]
            suffix = Path(filename).suffix.lower()
            if filename in FORBIDDEN_FILE_NAMES or (filename.startswith(".env.") and filename not in {".env.example", ".env.production.example", ".env.docker.example"}):
                problems.append({"path": info.filename, "problem": "env_file_in_zip"})
            if lowered_parts & FORBIDDEN_PACKAGE_PARTS:
                problems.append({"path": info.filename, "problem": "forbidden_directory_in_zip"})
            if suffix in FORBIDDEN_SUFFIXES:
                problems.append({"path": info.filename, "problem": "forbidden_runtime_file_in_zip"})
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 score 10 kalite kapısı")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--package-zip", default="")
    parser.add_argument("--json-output", default="")
    parser.add_argument("--allow-local-env", action="store_true", help="Yerel çalışmada .env varlığını hata değil uyarı say.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    results: dict[str, object] = {"marker": PROJECT_MARKER, "project_root": str(root), "checks": {}}

    required = check_required_tokens(root)
    syntax = check_python_syntax(root)
    local_env = [] if args.allow_local_env else check_local_secret_files(root)
    package = check_package_zip(Path(args.package_zip)) if args.package_zip else []

    checks = {
        "required_tokens": required,
        "python_syntax": syntax,
        "local_secret_files": local_env,
        "package_zip": package,
    }
    results["checks"] = checks
    total_problems = sum(len(v) for v in checks.values())
    results["status"] = "PASS" if total_problems == 0 else "FAIL"
    results["problem_count"] = total_problems

    output = json.dumps(results, ensure_ascii=False, indent=2)
    print(output)
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(output + "\n", encoding="utf-8")
    return 0 if total_problems == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
