# -*- coding: utf-8 -*-
"""
BYS360 Repo Hijyeni P0.2 Active Audit + Health V2.17.3
- Measures active project tree while excluding quarantine/cache/build folders.
- Runs compileall.
- Runs the same app factory import style that was proven manually:
  from app import create_app; app=create_app()
- Captures stdout/stderr tails so false negatives can be diagnosed safely.

This script does not modify application code.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

VERSION = "V2.17.3"
TOKEN_PREFIX = "BYS360_REPO_HYGIENE_P0_2_ACTIVE_AUDIT_HEALTH_V2_17_3"

EXCLUDE_DIR_NAMES = {
    ".git", ".hg", ".svn",
    ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".dart_tool", "build", "dist", ".idea", ".vscode",
    "_local_quarantine", "reports", "instance", "logs",
}

# A nested copied project tree was observed in earlier audit output. It is reported
# separately and excluded from active-core debt counts so numbers do not stay inflated.
DUPLICATE_TREE_TOP_LEVELS = {"project"}

TEXT_EXTENSIONS = {
    ".py", ".ps1", ".txt", ".md", ".yml", ".yaml", ".json", ".ini",
    ".cfg", ".toml", ".env", ".example", ".html", ".css", ".js", ".dart",
    ".sql", ".sh", ".bat", ".cmd",
}

SECRET_LINE_PATTERNS = [
    re.compile(r"(?i)^\s*(SECRET_KEY|JWT_SECRET|SECURITY_PASSWORD_SALT)\s*=\s*(?!$|change|changeme|example|placeholder|none|null).{8,}"),
    re.compile(r"(?i)^\s*(DATABASE_URL|SQLALCHEMY_DATABASE_URI)\s*=\s*.+://.+:.+@"),
    re.compile(r"(?i)^\s*(MAIL_PASSWORD|SMTP_PASSWORD|DB_PASSWORD|POSTGRES_PASSWORD|REDIS_PASSWORD)\s*=\s*(?!$|change|changeme|example|placeholder|none|null).{4,}"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
]

RISKY_NAME_PATTERNS = [
    re.compile(r"(?i)(^|[\\/])\.env$"),
    re.compile(r"(?i)(\.bak$|\.backup$|_backup|backup_|\.old$|\.orig$|\.tmp$)"),
    re.compile(r"(?i)(tmp_|temp_|debug_|test_secret|smtp_direct_test)"),
]

PHASE_PATTERN = re.compile(r"(?i)(phase\d+|_v\d+_\d+|resume_v\d+|fix_v\d+|repair_.*_v\d+)")
ROUTE_PATTERN = re.compile(r"(?i)(routes?\.py$|_routes?\.py$)")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_excluded_dir(path: Path, root: Path, include_duplicate_tree: bool = False) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    if not parts:
        return False
    if any(part in EXCLUDE_DIR_NAMES for part in parts):
        return True
    if not include_duplicate_tree and parts[0] in DUPLICATE_TREE_TOP_LEVELS:
        return True
    return False


def iter_files(root: Path, include_duplicate_tree: bool = False) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        # mutate dirnames to prune recursion
        keep = []
        for name in dirnames:
            candidate = d / name
            if not is_excluded_dir(candidate, root, include_duplicate_tree=include_duplicate_tree):
                keep.append(name)
        dirnames[:] = keep
        if is_excluded_dir(d, root, include_duplicate_tree=include_duplicate_tree):
            continue
        for filename in filenames:
            yield d / filename


def count_duplicate_tree(root: Path) -> int:
    total = 0
    for top in DUPLICATE_TREE_TOP_LEVELS:
        p = root / top
        if p.exists() and p.is_dir():
            for _dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
                total += len(filenames)
    return total


def read_text_sample(path: Path, max_bytes: int = 256_000) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def analyze_active_tree(root: Path) -> Dict[str, object]:
    files = list(iter_files(root, include_duplicate_tree=False))
    risky_paths: List[str] = []
    large_py: List[Tuple[str, int]] = []
    large_route_py: List[Tuple[str, int]] = []
    phase_py: List[str] = []
    possible_secret_hits: List[str] = []

    for path in files:
        r = rel(path, root)
        lower = r.lower()
        if any(p.search(r) for p in RISKY_NAME_PATTERNS):
            risky_paths.append(r)
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        if path.suffix.lower() == ".py" and size >= 50_000:
            large_py.append((r, size))
            if ROUTE_PATTERN.search(path.name):
                large_route_py.append((r, size))
        if path.suffix.lower() == ".py" and PHASE_PATTERN.search(path.name):
            phase_py.append(r)
        if path.suffix.lower() in TEXT_EXTENSIONS or path.name.lower().startswith(".env"):
            text = read_text_sample(path)
            if text:
                for i, line in enumerate(text.splitlines(), 1):
                    if any(p.search(line) for p in SECRET_LINE_PATTERNS):
                        # Do not include values; only location.
                        possible_secret_hits.append(f"{r}:{i}")
                        break

    large_py_sorted = sorted(large_py, key=lambda x: x[1], reverse=True)
    large_route_py_sorted = sorted(large_route_py, key=lambda x: x[1], reverse=True)
    phase_py_sorted = sorted(phase_py)
    risky_sorted = sorted(set(risky_paths))
    secret_sorted = sorted(set(possible_secret_hits))

    return {
        "total_active_core_files_scanned": len(files),
        "risky_path_count": len(risky_sorted),
        "large_py_count": len(large_py_sorted),
        "large_route_py_count": len(large_route_py_sorted),
        "phase_py_count": len(phase_py_sorted),
        "possible_secret_hit_count": len(secret_sorted),
        "duplicate_project_tree_count": count_duplicate_tree(root),
        "top_large_py": [{"path": p, "size_bytes": s} for p, s in large_py_sorted[:30]],
        "top_large_route_py": [{"path": p, "size_bytes": s} for p, s in large_route_py_sorted[:30]],
        "sample_phase_py": phase_py_sorted[:80],
        "sample_risky_paths": risky_sorted[:80],
        "sample_possible_secret_locations": secret_sorted[:80],
    }


def tail(text: str, max_chars: int = 6000) -> str:
    text = text or ""
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def run_cmd(root: Path, args: List[str], timeout: int) -> Dict[str, object]:
    started = datetime.now().isoformat(timespec="seconds")
    try:
        proc = subprocess.run(
            args,
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return {
            "cmd": args,
            "returncode": proc.returncode,
            "started_at": started,
            "stdout_tail": tail(proc.stdout),
            "stderr_tail": tail(proc.stderr),
            "ok": proc.returncode == 0,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": args,
            "returncode": None,
            "started_at": started,
            "stdout_tail": tail(exc.stdout if isinstance(exc.stdout, str) else ""),
            "stderr_tail": tail(exc.stderr if isinstance(exc.stderr, str) else ""),
            "ok": False,
            "error": f"timeout_after_{timeout}s",
        }
    except Exception as exc:
        return {
            "cmd": args,
            "returncode": None,
            "started_at": started,
            "stdout_tail": "",
            "stderr_tail": "",
            "ok": False,
            "error": repr(exc),
        }


def health_check(root: Path) -> Dict[str, object]:
    py = sys.executable or "python"
    compile_result = run_cmd(root, [py, "-m", "compileall", "-q", "app", "config.py", "scripts"], timeout=240)

    factory_code = r'''
import os, sys
sys.path.insert(0, os.getcwd())
factory_name = None
try:
    from app import create_app
    factory_name = "create_app"
except Exception as first_error:
    try:
        from app import create_bys360_application as create_app
        factory_name = "create_bys360_application"
    except Exception as second_error:
        print("BYS360_APP_FACTORY_IMPORT_FAIL", repr(first_error), repr(second_error))
        raise
app = create_app()
print("BYS360_APP_CREATE_OK", factory_name, len(getattr(app, "blueprints", {})))
'''.strip()
    factory_result = run_cmd(root, [py, "-c", factory_code], timeout=180)
    stdout_and_stderr = (factory_result.get("stdout_tail") or "") + "\n" + (factory_result.get("stderr_tail") or "")
    app_factory_ok = bool(factory_result.get("ok")) and "BYS360_APP_CREATE_OK" in stdout_and_stderr

    return {
        "compileall_ok": bool(compile_result.get("ok")),
        "app_factory_ok": app_factory_ok,
        "overall_ok": bool(compile_result.get("ok")) and app_factory_ok,
        "compile_result": compile_result,
        "factory_result": factory_result,
    }


def write_reports(root: Path, result: Dict[str, object]) -> Tuple[str, str]:
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    stem = "bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3_report"
    json_path = report_dir / f"{stem}.json"
    md_path = report_dir / f"{stem}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    active = result.get("active_summary") or {}
    health = result.get("health_summary") or {}
    lines: List[str] = []
    lines.append("# BYS360 Repo Hijyeni P0.2 Active Audit + Health V2.17.3")
    lines.append("")
    lines.append(f"- Version: `{VERSION}`")
    lines.append(f"- Mode: `{result.get('mode')}`")
    lines.append(f"- Project root: `{result.get('project_root')}`")
    lines.append("")
    if active:
        lines.append("## Active Core Audit")
        for key in [
            "total_active_core_files_scanned", "risky_path_count", "large_py_count",
            "large_route_py_count", "phase_py_count", "possible_secret_hit_count",
            "duplicate_project_tree_count",
        ]:
            lines.append(f"- {key}: `{active.get(key)}`")
        lines.append("")
        if active.get("top_large_route_py"):
            lines.append("### Top large route files")
            for item in active.get("top_large_route_py", [])[:20]:
                lines.append(f"- `{item['path']}` — {item['size_bytes']} bytes")
            lines.append("")
        if active.get("sample_possible_secret_locations"):
            lines.append("### Possible secret locations (values hidden)")
            for item in active.get("sample_possible_secret_locations", [])[:40]:
                lines.append(f"- `{item}`")
            lines.append("")
    if health:
        lines.append("## Health")
        lines.append(f"- compileall_ok: `{health.get('compileall_ok')}`")
        lines.append(f"- app_factory_ok: `{health.get('app_factory_ok')}`")
        lines.append(f"- overall_ok: `{health.get('overall_ok')}`")
        lines.append("")
        factory = health.get("factory_result") or {}
        if factory:
            lines.append("### Factory stdout tail")
            lines.append("```text")
            lines.append(str(factory.get("stdout_tail") or ""))
            lines.append("```")
            lines.append("")
            lines.append("### Factory stderr tail")
            lines.append("```text")
            lines.append(str(factory.get("stderr_tail") or ""))
            lines.append("```")
            lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return str(json_path.relative_to(root)), str(md_path.relative_to(root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "health", "all"], default="all")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    result: Dict[str, object] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "active_summary": {},
        "health_summary": {},
    }

    if args.mode in ("audit", "all"):
        result["active_summary"] = analyze_active_tree(root)
    if args.mode in ("health", "all"):
        result["health_summary"] = health_check(root)

    json_report, md_report = write_reports(root, result)
    result["json_report"] = json_report
    result["md_report"] = md_report

    print(json.dumps({
        "version": result["version"],
        "mode": result["mode"],
        "project_root": result["project_root"],
        "active_summary": {k: v for k, v in (result.get("active_summary") or {}).items() if not isinstance(v, list)},
        "health_summary": {k: v for k, v in (result.get("health_summary") or {}).items() if not k.endswith("_result")},
        "json_report": json_report,
        "md_report": md_report,
    }, ensure_ascii=False, indent=2))

    print(f"{TOKEN_PREFIX}_REPORT_OK")
    if args.mode in ("health", "all"):
        health = result.get("health_summary") or {}
        if health.get("overall_ok"):
            print(f"{TOKEN_PREFIX}_HEALTH_OK")
        else:
            print(f"{TOKEN_PREFIX}_HEALTH_FAIL")
            return 1
    print(f"{TOKEN_PREFIX}_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
