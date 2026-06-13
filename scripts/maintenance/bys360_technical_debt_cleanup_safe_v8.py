from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import py_compile
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V8"
VERSION = "V8"

EXCLUDED_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "backups", "backup",
    "releases", "release", "dist", "build", ".quarantine", "_bys360_overlay_payload",
    "htmlcov", ".tox",
}
EXCLUDED_TOP_LEVEL = {"reports", "logs", "archive", "overlays"}
APP_EXCLUDED_PARTS = {
    "scripts", "tests", "test", "migrations", "alembic", "reports", "logs",
    "backups", "releases", "docs", "documentation", "instance",
}
UI_PATH_HINTS = {"templates", "static", "mobile", "flutter", "assets", "frontend", "web", "portal"}
UI_EXTS = {".html", ".htm", ".jinja", ".jinja2", ".js", ".ts", ".tsx", ".jsx", ".dart", ".css"}
TECH_UI_TERMS = [
    "workflow state", "workflow_state", "authorized_scope", "unauthorized_scope",
    "phase sync", "faz 3 senkronu", "president_pending", "blocked_president_pending",
    "scorecard_pending", "endpoint", "traceback", "exception", "debug", "raw error",
    "stacktrace", "stack trace", "sync", "gate", "unauthorized", "forbidden",
]
SECRET_FILE_NAMES = {".env", ".flaskenv"}
LOCAL_DB_EXTS = {".sqlite", ".sqlite3", ".db"}

@dataclass
class Finding:
    kind: str
    path: str
    line: int
    detail: str


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def rel_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except Exception:
        return str(path)


def should_skip_dir(root: Path, directory: Path) -> bool:
    name = directory.name
    if name in EXCLUDED_DIR_NAMES:
        return True
    try:
        rel = directory.relative_to(root)
        if rel.parts and rel.parts[0] in EXCLUDED_TOP_LEVEL:
            return True
    except Exception:
        return False
    return False


def iter_files(root: Path, suffixes: set[str] | None = None) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dpath = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not should_skip_dir(root, dpath / d)]
        for filename in filenames:
            path = dpath / filename
            if suffixes is None or path.suffix.lower() in suffixes:
                yield path


def iter_python_files(root: Path) -> Iterable[Path]:
    yield from iter_files(root, {".py"})


def is_app_file(root: Path, path: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except Exception:
        return False
    if any(part in APP_EXCLUDED_PARTS for part in parts):
        return False
    if path.name.startswith("test_") or path.name.endswith("_test.py"):
        return False
    return True


def is_ui_file(root: Path, path: Path) -> bool:
    if path.suffix.lower() not in UI_EXTS:
        return False
    try:
        parts = set(path.relative_to(root).parts)
    except Exception:
        return False
    if not parts.intersection(UI_PATH_HINTS):
        return False
    return True


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def ast_exception_metrics(text: str) -> tuple[int, int, Counter, list[tuple[int, str]]]:
    """Return broad_count, silent_count, body_reason_counter, silent_lines."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0, 0, Counter({"syntax_error": 1}), []
    lines = text.splitlines()
    broad = 0
    silent = 0
    reasons: Counter = Counter()
    silent_lines: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        is_broad = False
        if node.type is None:
            continue
        if isinstance(node.type, ast.Name) and node.type.id == "Exception":
            is_broad = True
        elif isinstance(node.type, ast.Attribute) and node.type.attr == "Exception":
            is_broad = True
        if not is_broad:
            continue
        broad += 1
        if not node.body:
            silent += 1
            reasons["empty_body"] += 1
            silent_lines.append((node.lineno, "empty_body"))
            continue
        body_start = node.body[0].lineno
        body_end = getattr(node, "end_lineno", body_start)
        body_text = "\n".join(lines[body_start - 1: body_end])
        has_log = bool(re.search(r"\b(logger|current_app\.logger|logging)\.(exception|error|warning|info|debug)\b", body_text))
        if not has_log:
            silent += 1
            if len(node.body) > 2:
                reason = "manual_multi_statement"
            elif any(isinstance(stmt, ast.Try) for stmt in node.body):
                reason = "manual_nested_try"
            elif any(isinstance(stmt, ast.Return) and stmt.value is not None for stmt in node.body):
                reason = "manual_return_value"
            elif all(isinstance(stmt, (ast.Pass, ast.Continue, ast.Break, ast.Return)) for stmt in node.body):
                reason = "simple_but_not_auto_patched"
            else:
                reason = "manual_non_trivial_body"
            reasons[reason] += 1
            silent_lines.append((node.lineno, reason))
    return broad, silent, reasons, silent_lines


def scan_python_debt(root: Path) -> dict:
    metrics = {
        "python_files": 0,
        "python_lines": 0,
        "app_python_files": 0,
        "broad_except_count": 0,
        "app_broad_except_count": 0,
        "silent_broad_except_count": 0,
        "app_silent_broad_except_count": 0,
    }
    hotspots: Counter = Counter()
    reason_counts: Counter = Counter()
    detailed_rows: list[dict] = []
    syntax_errors: list[dict] = []
    for path in iter_python_files(root):
        metrics["python_files"] += 1
        try:
            text = read_text(path)
        except Exception:
            continue
        metrics["python_lines"] += len(text.splitlines())
        is_app = is_app_file(root, path)
        if is_app:
            metrics["app_python_files"] += 1
        broad, silent, reasons, silent_lines = ast_exception_metrics(text)
        metrics["broad_except_count"] += broad
        metrics["silent_broad_except_count"] += silent
        if "syntax_error" in reasons:
            syntax_errors.append({"path": rel_path(root, path), "reason": "syntax_error"})
        if is_app:
            metrics["app_broad_except_count"] += broad
            metrics["app_silent_broad_except_count"] += silent
            if silent:
                rel = rel_path(root, path)
                hotspots[rel] += silent
                reason_counts.update(reasons)
                for line, reason in silent_lines[:20]:
                    detailed_rows.append({"path": rel, "line": line, "reason": reason})
    return {"metrics": metrics, "hotspots": hotspots, "reason_counts": reason_counts, "rows": detailed_rows, "syntax_errors": syntax_errors}


def scan_ui_debt(root: Path) -> dict:
    findings: list[Finding] = []
    term_counts: Counter = Counter()
    file_counts: Counter = Counter()
    for path in iter_files(root, UI_EXTS):
        if not is_ui_file(root, path):
            continue
        try:
            text = read_text(path)
        except Exception:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            low = line.lower()
            for term in TECH_UI_TERMS:
                if term in low:
                    rel = rel_path(root, path)
                    findings.append(Finding("technical_ui_term", rel, idx, term))
                    term_counts[term] += 1
                    file_counts[rel] += 1
                    break
    return {"findings": findings, "term_counts": term_counts, "file_counts": file_counts}


def scan_security_hygiene(root: Path) -> dict:
    env_files = []
    env_examples = []
    local_dbs = []
    large_files = []
    for path in iter_files(root):
        rel = rel_path(root, path)
        name = path.name.lower()
        if name in SECRET_FILE_NAMES:
            env_files.append(rel)
        if name == ".env.example":
            env_examples.append(rel)
        if path.suffix.lower() in LOCAL_DB_EXTS:
            local_dbs.append(rel)
        try:
            size = path.stat().st_size
            if size >= 5 * 1024 * 1024:
                large_files.append({"path": rel, "size_mb": round(size / (1024 * 1024), 2)})
        except Exception:
            pass
    return {"env_files": env_files, "env_examples": env_examples, "local_dbs": local_dbs, "large_files": large_files[:50]}


def compile_project(root: Path, run_compile: bool) -> dict:
    if not run_compile:
        return {"compile_requested": False}
    errors = []
    checked = 0
    for path in iter_python_files(root):
        checked += 1
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append({"path": rel_path(root, path), "error": str(exc)})
            if len(errors) >= 20:
                break
    result = {"compile_requested": True, "compile_ok": not errors, "compile_detail": {"checked_python_files": checked, "error_count": len(errors), "errors": errors[:20], "ok": not errors}}
    quality_script = root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"
    if quality_script.exists():
        try:
            proc = subprocess.run([sys.executable, str(quality_script), "--project-root", str(root)], cwd=str(root), text=True, capture_output=True, timeout=120)
            result["existing_quality_gate"] = str(quality_script)
            result["quality9_run"] = {"returncode": proc.returncode, "stdout_tail": proc.stdout[-1000:], "stderr_tail": proc.stderr[-1000:]}
        except Exception as exc:
            result["quality9_run"] = {"returncode": -1, "error": str(exc)}
    return result


def write_reports(root: Path, stamp: str, python_debt: dict, ui_debt: dict, security: dict, quality: dict) -> dict:
    report_dir = root / "reports" / "technical_debt"
    report_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_dir / f"{PACKAGE}_{stamp}_REPORT.md"
    json_path = report_dir / f"{PACKAGE}_{stamp}.json"
    ui_csv_path = report_dir / f"{PACKAGE}_{stamp}_TECHNICAL_UI_TERMS.csv"
    exception_md_path = report_dir / f"{PACKAGE}_{stamp}_MANUAL_EXCEPTION_HOTSPOTS.md"
    next_plan_path = report_dir / f"{PACKAGE}_{stamp}_NEXT_ACTION_PLAN.md"

    pm = python_debt["metrics"]
    ui_count = len(ui_debt["findings"])
    finding_count = pm["app_silent_broad_except_count"] + ui_count + len(security["env_files"]) + len(security["local_dbs"])

    md_lines = [
        f"# {PACKAGE} Raporu",
        "",
        "SAFE V8 kod değiştirmez. Otomatik exception patch hattı sonrasında kalan borcu modül bazlı yönetmek için rapor üretir.",
        "",
        "## Özet",
        "",
        "| Alan | Değer |",
        "|---|---:|",
        f"| App sessiz broad except | {pm['app_silent_broad_except_count']} |",
        f"| App broad except | {pm['app_broad_except_count']} |",
        f"| UI teknik terim | {ui_count} |",
        f"| .env dosyası | {len(security['env_files'])} |",
        f"| Yerel DB dosyası | {len(security['local_dbs'])} |",
        f"| Büyük dosya | {len(security['large_files'])} |",
        "",
        "## En Yoğun Manuel Exception Dosyaları",
        "",
        "| Dosya | Sessiz broad except |",
        "|---|---:|",
    ]
    for path, count in python_debt["hotspots"].most_common(30):
        md_lines.append(f"| `{path}` | {count} |")
    md_lines += ["", "## UI Teknik Dil Hotspotları", "", "| Dosya | Terim sayısı |", "|---|---:|"]
    for path, count in ui_debt["file_counts"].most_common(30):
        md_lines.append(f"| `{path}` | {count} |")
    md_lines += ["", "## Güvenlik Hijyeni", "", "| Kontrol | Bulgu |", "|---|---|"]
    md_lines.append(f"| .env | {', '.join(security['env_files']) if security['env_files'] else 'Yok'} |")
    md_lines.append(f"| .env.example | {', '.join(security['env_examples']) if security['env_examples'] else 'Yok'} |")
    md_lines.append(f"| Yerel DB | {', '.join(security['local_dbs']) if security['local_dbs'] else 'Yok'} |")
    md_lines += ["", "## Compile / Quality", "", "```json", json.dumps(quality, ensure_ascii=False, indent=2), "```", ""]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    exception_lines = [f"# {PACKAGE} Manuel Exception Hotspotları", "", "| Dosya | Satır | Neden |", "|---|---:|---|"]
    for row in python_debt["rows"][:500]:
        exception_lines.append(f"| `{row['path']}` | {row['line']} | {row['reason']} |")
    exception_md_path.write_text("\n".join(exception_lines) + "\n", encoding="utf-8")

    next_lines = [
        f"# {PACKAGE} Sonraki Aksiyon Planı",
        "",
        "## Karar",
        "",
        "Otomatik geniş kapsamlı exception patch işlemi durdurulmalıdır. Kalan kayıtlar dosya/modül bazlı manuel refactor kapsamındadır.",
        "",
        "## Önerilen Sıra",
        "",
        "1. En çok sessiz exception içeren ilk 10 dosya manuel incelensin.",
        "2. Kullanıcıya görünen teknik terimler UI dosyalarında temizlensin.",
        "3. .env ve yerel DB kaynak pakete girmeyecek şekilde release gate'e bağlansın.",
        "4. Her modül temizliğinden sonra compile + Quality 9 çalıştırılsın.",
        "",
        "## İlk 10 Exception Hotspot",
        "",
        "| Sıra | Dosya | Sessiz broad except |",
        "|---:|---|---:|",
    ]
    for i, (path, count) in enumerate(python_debt["hotspots"].most_common(10), start=1):
        next_lines.append(f"| {i} | `{path}` | {count} |")
    next_lines += ["", "## İlk 10 UI Teknik Dil Hotspot", "", "| Sıra | Dosya | Terim sayısı |", "|---:|---|---:|"]
    for i, (path, count) in enumerate(ui_debt["file_counts"].most_common(10), start=1):
        next_lines.append(f"| {i} | `{path}` | {count} |")
    next_plan_path.write_text("\n".join(next_lines) + "\n", encoding="utf-8")

    with ui_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["kind", "path", "line", "term"])
        for item in ui_debt["findings"]:
            writer.writerow([item.kind, item.path, item.line, item.detail])

    payload = {
        "package": PACKAGE,
        "version": VERSION,
        "finding_count": finding_count,
        "python_debt": {
            "metrics": pm,
            "manual_hotspots": python_debt["hotspots"].most_common(100),
            "reason_counts": python_debt["reason_counts"].most_common(),
            "syntax_errors": python_debt["syntax_errors"],
        },
        "ui_debt": {
            "technical_ui_term_count": ui_count,
            "term_counts": ui_debt["term_counts"].most_common(),
            "file_counts": ui_debt["file_counts"].most_common(100),
        },
        "security_hygiene": security,
        "quality_gate": quality,
        "reports": {
            "audit_report": str(md_path),
            "json_report": str(json_path),
            "technical_ui_terms_csv": str(ui_csv_path),
            "manual_exception_hotspots": str(exception_md_path),
            "next_action_plan": str(next_plan_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all", choices=["audit", "all", "quality-gate"])
    parser.add_argument("--output-root", default="C:\\bys360")
    parser.add_argument("--run-compile", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    stamp = now_stamp()
    print(json.dumps({"package": PACKAGE, "version": VERSION, "mode": args.mode, "project_root": str(root)}, ensure_ascii=False))

    if args.mode == "quality-gate":
        quality = compile_project(root, True)
        print(json.dumps(quality, ensure_ascii=False, indent=2))
        ok = quality.get("compile_ok", False) and quality.get("quality9_run", {}).get("returncode", 0) == 0
        return 0 if ok else 1

    python_debt = scan_python_debt(root)
    ui_debt = scan_ui_debt(root)
    security = scan_security_hygiene(root)
    quality = compile_project(root, args.run_compile)
    result = write_reports(root, stamp, python_debt, ui_debt, security, quality)

    print(json.dumps({
        "audit_metrics": {
            **python_debt["metrics"],
            "technical_ui_term_count": len(ui_debt["findings"]),
            "env_file_count": len(security["env_files"]),
            "local_db_count": len(security["local_dbs"]),
        },
        "finding_count": result["finding_count"],
        **result["reports"],
    }, ensure_ascii=False, indent=2))

    print(json.dumps({
        "ok": (quality.get("compile_ok", True) if quality.get("compile_requested") else True) and quality.get("quality9_run", {}).get("returncode", 0) == 0,
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "quality_gate": quality,
        "reports": result["reports"],
        "top_exception_hotspots": python_debt["hotspots"].most_common(10),
        "top_ui_hotspots": ui_debt["file_counts"].most_common(10),
        "security_hygiene": security,
    }, ensure_ascii=False, indent=2))

    ok = True
    if quality.get("compile_requested") and not quality.get("compile_ok"):
        ok = False
    if quality.get("quality9_run", {}).get("returncode", 0) not in (0, None):
        ok = False
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
