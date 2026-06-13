from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V7"
VERSION = "V7"

EXCLUDED_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "backups", "backup",
    "releases", "release", "dist", "build", ".quarantine", "_bys360_overlay_payload",
    "htmlcov", ".tox",
}
EXCLUDED_TOP_LEVEL = {
    "reports", "logs", "archive", "overlays",
}
APP_EXCLUDED_PARTS = {
    "scripts", "tests", "test", "migrations", "alembic", "reports", "logs",
    "backups", "releases", "docs", "documentation", "instance",
}
TECH_UI_TERMS = [
    "workflow state", "workflow_state", "authorized_scope", "unauthorized_scope",
    "phase sync", "Faz 3 senkronu", "president_pending", "blocked_president_pending",
    "scorecard_pending", "endpoint", "traceback", "exception", "debug", "raw error",
    "stacktrace", "stack trace", "sync", "gate",
]

PASS_LIKE = {"pass", "continue", "break", "return", "return None", "return False", "return True"}

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


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dpath = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not should_skip_dir(root, dpath / d)]
        for filename in filenames:
            if filename.endswith(".py"):
                yield dpath / filename


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


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def count_prints(text: str) -> int:
    return len(re.findall(r"(?<![\w.])print\s*\(", text))


def ast_except_metrics(text: str) -> tuple[int, int, list[tuple[int, int, bool, str]]]:
    """Return broad_count, silent_count, candidates.

    candidates: (lineno, end_lineno, is_simple_patchable, reason)
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0, 0, []
    broad = 0
    silent = 0
    candidates: list[tuple[int, int, bool, str]] = []
    lines = text.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        is_broad = False
        if node.type is None:
            # bare except is intentionally not patched by this tool
            continue
        if isinstance(node.type, ast.Name) and node.type.id == "Exception":
            is_broad = True
        elif isinstance(node.type, ast.Attribute) and node.type.attr == "Exception":
            is_broad = True
        if not is_broad:
            continue
        broad += 1
        body_start = node.body[0].lineno if node.body else node.lineno
        body_end = getattr(node, "end_lineno", body_start)
        body_text = "\n".join(lines[body_start - 1: body_end])
        has_log = bool(re.search(r"\b(logger|current_app\.logger|logging)\.(exception|error|warning|info|debug)\b", body_text))
        if not has_log:
            silent += 1
            simple, reason = is_simple_silent_handler(node, lines)
            candidates.append((node.lineno, body_end, simple, reason))
    return broad, silent, candidates


def is_simple_silent_handler(node: ast.ExceptHandler, lines: list[str]) -> tuple[bool, str]:
    if not node.body:
        return False, "empty_body"
    # Skip nested handlers or larger/complex bodies; those deserve manual review.
    if len(node.body) > 2:
        return False, "multi_statement"
    allowed = (ast.Pass, ast.Continue, ast.Break, ast.Return)
    if not all(isinstance(stmt, allowed) for stmt in node.body):
        return False, "non_trivial_body"
    # Do not patch return with concrete values other than None/False/True/list/dict empty? keep strict.
    for stmt in node.body:
        if isinstance(stmt, ast.Return):
            val = stmt.value
            if val is None:
                continue
            if isinstance(val, ast.Constant) and val.value in (None, False, True, ""):
                continue
            if isinstance(val, (ast.List, ast.Dict, ast.Tuple)) and not getattr(val, 'elts', None) and not getattr(val, 'keys', None):
                continue
            return False, "return_value_complex"
    body_start = node.body[0].lineno
    body_end = getattr(node.body[-1], "end_lineno", body_start)
    body_text = "\n".join(lines[body_start - 1: body_end]).strip()
    if "# nosec" in body_text or "pragma:" in body_text:
        return False, "special_comment"
    return True, "simple_control_flow"


def find_technical_ui_terms(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    exts = {".html", ".jinja", ".jinja2", ".js", ".ts", ".tsx", ".jsx", ".dart", ".css", ".py"}
    for dirpath, dirnames, filenames in os.walk(root):
        dpath = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not should_skip_dir(root, dpath / d)]
        for filename in filenames:
            path = dpath / filename
            if path.suffix.lower() not in exts:
                continue
            if not is_app_file(root, path) and path.suffix.lower() == ".py":
                continue
            try:
                text = read_text(path)
            except Exception:
                continue
            lower_lines = text.splitlines()
            for idx, line in enumerate(lower_lines, start=1):
                low = line.lower()
                for term in TECH_UI_TERMS:
                    if term.lower() in low:
                        findings.append(Finding("technical_ui_term", rel_path(root, path), idx, term))
                        break
    return findings


def audit(root: Path, report_dir: Path, stamp: str, phase: str) -> dict:
    findings: list[Finding] = []
    metrics = {
        "package": PACKAGE,
        "version": VERSION,
        "project_root": str(root),
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "files_scanned": 0,
        "python_files": 0,
        "python_lines": 0,
        "app_python_files": 0,
        "broad_except_count": 0,
        "app_broad_except_count": 0,
        "silent_broad_except_count": 0,
        "app_silent_broad_except_count": 0,
        "patchable_simple_silent_except_count": 0,
        "technical_ui_term_count": 0,
    }
    patchable_rows = []
    manual_counter = Counter()

    for path in iter_python_files(root):
        metrics["files_scanned"] += 1
        metrics["python_files"] += 1
        try:
            text = read_text(path)
        except Exception:
            continue
        lines = text.splitlines()
        metrics["python_lines"] += len(lines)
        is_app = is_app_file(root, path)
        if is_app:
            metrics["app_python_files"] += 1
        broad, silent, candidates = ast_except_metrics(text)
        metrics["broad_except_count"] += broad
        metrics["silent_broad_except_count"] += silent
        if is_app:
            metrics["app_broad_except_count"] += broad
            metrics["app_silent_broad_except_count"] += silent
            for lineno, end_lineno, simple, reason in candidates:
                if simple:
                    metrics["patchable_simple_silent_except_count"] += 1
                    patchable_rows.append({
                        "path": rel_path(root, path),
                        "line": lineno,
                        "end_line": end_lineno,
                        "reason": reason,
                    })
                else:
                    manual_counter[rel_path(root, path)] += 1

    ui_findings = find_technical_ui_terms(root)
    metrics["technical_ui_term_count"] = len(ui_findings)
    findings.extend(ui_findings)

    finding_count = metrics["app_silent_broad_except_count"] + metrics["technical_ui_term_count"]

    md_path = report_dir / f"{PACKAGE}_{stamp}_{phase}.md"
    json_path = report_dir / f"{PACKAGE}_{stamp}_{phase}.json"
    csv_path = report_dir / f"{PACKAGE}_{stamp}_{phase}.csv"
    patch_md = report_dir / f"{PACKAGE}_{stamp}_{phase}_PATCHABLE_SIMPLE_EXCEPTS.md"
    manual_md = report_dir / f"{PACKAGE}_{stamp}_{phase}_MANUAL_EXCEPTION_HOTSPOTS.md"

    md_lines = [
        f"# {PACKAGE} {phase} Raporu",
        "",
        "## Metrikler",
        "",
        "| Metrik | Değer |",
        "|---|---:|",
    ]
    for k, v in metrics.items():
        md_lines.append(f"| {k} | {v} |")
    md_lines += ["", "## Not", "", "Bu rapor sadece güvenli teknik borç temizliği için üretilmiştir. Broad except tipini değiştirmez; sessiz kalan basit bloklara log eklenmesini hedefler."]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    json_path.write_text(json.dumps({"metrics": metrics, "finding_count": finding_count, "patchable": patchable_rows, "manual_hotspots": manual_counter.most_common(50)}, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["kind", "path", "line", "detail"])
        for item in findings:
            writer.writerow([item.kind, item.path, item.line, item.detail])

    patch_lines = [f"# {PACKAGE} Patch Edilebilir Basit Sessiz Except Adayları", "", "| Dosya | Satır | Bitiş | Neden |", "|---|---:|---:|---|"]
    for row in patchable_rows[:500]:
        patch_lines.append(f"| `{row['path']}` | {row['line']} | {row['end_line']} | {row['reason']} |")
    patch_md.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")

    manual_lines = [f"# {PACKAGE} Manuel İnceleme Exception Hotspotları", "", "| Dosya | Kalan karmaşık/sessiz aday |", "|---|---:|"]
    for path, count in manual_counter.most_common(100):
        manual_lines.append(f"| `{path}` | {count} |")
    manual_md.write_text("\n".join(manual_lines) + "\n", encoding="utf-8")

    return {
        "metrics": metrics,
        "finding_count": finding_count,
        "reports": {
            "audit_report": str(md_path),
            "json_report": str(json_path),
            "csv_report": str(csv_path),
            "patchable_simple_excepts": str(patch_md),
            "manual_exception_hotspots": str(manual_md),
        },
        "patchable_rows": patchable_rows,
    }


def ensure_backup(backup_root: Path, root: Path, path: Path) -> None:
    target = backup_root / path.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)


def patch_file(root: Path, path: Path, max_for_file: int | None = None) -> int:
    text = read_text(path)
    lines = text.splitlines(keepends=True)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    # Patch bottom-up by handler line to preserve positions.
    handlers: list[ast.ExceptHandler] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.type is None:
            continue
        is_broad = isinstance(node.type, ast.Name) and node.type.id == "Exception"
        if not is_broad:
            continue
        body_start = node.body[0].lineno if node.body else node.lineno
        body_end = getattr(node, "end_lineno", body_start)
        body_text = "".join(lines[body_start - 1: body_end])
        has_log = bool(re.search(r"\b(logger|current_app\.logger|logging)\.(exception|error|warning|info|debug)\b", body_text))
        if has_log:
            continue
        simple, _ = is_simple_silent_handler(node, [l.rstrip("\r\n") for l in lines])
        if simple:
            handlers.append(node)
    if max_for_file is not None:
        handlers = handlers[:max_for_file]
    if not handlers:
        return 0
    patched = 0
    for node in sorted(handlers, key=lambda n: n.lineno, reverse=True):
        if not node.body:
            continue
        insert_idx = node.body[0].lineno - 1
        body_line = lines[insert_idx]
        indent = re.match(r"^(\s*)", body_line).group(1)
        log_line = f'{indent}import logging\n{indent}logging.getLogger(__name__).warning("BYS360 teknik borc: sessiz hata yakalandi.", exc_info=True)\n'
        lines.insert(insert_idx, log_line)
        patched += 1
    path.write_text("".join(lines), encoding="utf-8")
    return patched



def compile_single_file(root: Path, path: Path) -> dict:
    try:
        py_compile.compile(str(path), doraise=True)
        return {"ok": True, "path": rel_path(root, path)}
    except Exception as exc:
        return {"ok": False, "path": rel_path(root, path), "error": str(exc)}


def compile_all_quick(root: Path, limit_errors: int = 5) -> dict:
    errors = []
    checked = 0
    for path in iter_python_files(root):
        checked += 1
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append({"path": rel_path(root, path), "error": str(exc)})
            if len(errors) >= limit_errors:
                break
    return {"ok": not errors, "checked_python_files": checked, "error_count": len(errors), "errors": errors}


def patch_simple_excepts(root: Path, output_root: Path, stamp: str, max_patches: int) -> dict:
    """Patch simple silent handlers with per-file compile validation.

    V7 is intentionally more defensive than V6:
    - baseline project syntax must already be clean;
    - each changed file is compiled immediately after patching;
    - if one file fails, only that file is restored and recorded as skipped;
    - accepted files continue to the final full compile/quality gate.
    """
    backup_root = output_root / "backups" / f"technical_debt_safe_v7_{stamp}"
    report_dir = root / "reports" / "technical_debt"
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = report_dir / f"{PACKAGE}_ACTIONS_{stamp}.json"
    actions = []
    skipped = 0
    remaining = max_patches
    files_changed = 0

    baseline = compile_all_quick(root)
    if not baseline["ok"]:
        manifest = {
            "package": PACKAGE,
            "version": VERSION,
            "backup_root": str(backup_root),
            "files_changed": 0,
            "action_count": 0,
            "skipped_count": 0,
            "aborted": True,
            "reason": "baseline_compile_failed",
            "baseline_compile": baseline,
            "actions": [],
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"manifest": str(manifest_path), "backup_root": str(backup_root), "files_changed": 0, "action_count": 0, "skipped_count": 0, "aborted": True, "baseline_compile": baseline}

    scored = []
    for path in iter_python_files(root):
        if not is_app_file(root, path):
            continue
        try:
            text = read_text(path)
        except Exception:
            continue
        _, _, candidates = ast_except_metrics(text)
        score = sum(1 for _lineno, _end, simple, _reason in candidates if simple)
        if score:
            scored.append((score, rel_path(root, path), path))
    scored.sort(key=lambda x: (-x[0], x[1]))

    accepted_count = 0
    for score, _rel, path in scored:
        if remaining <= 0:
            break
        rel = rel_path(root, path)
        try:
            ensure_backup(backup_root, root, path)
            before_text = read_text(path)
            patched = patch_file(root, path, max_for_file=remaining)
            if not patched:
                continue
            check = compile_single_file(root, path)
            if not check["ok"]:
                # Roll back only this file, keep other accepted files.
                backup_file = backup_root / path.relative_to(root)
                if backup_file.exists():
                    shutil.copy2(backup_file, path)
                else:
                    path.write_text(before_text, encoding="utf-8")
                skipped += 1
                actions.append({"action": "rollback_file_after_compile_error", "path": rel, "attempted_count": patched, "compile_error": check.get("error")})
                continue
            files_changed += 1
            accepted_count += patched
            actions.append({"action": "add_logging_to_simple_silent_except", "path": rel, "count": patched, "file_compile_ok": True})
            remaining -= patched
        except Exception as exc:
            skipped += 1
            actions.append({"action": "skip", "path": rel, "reason": str(exc)})
    manifest = {
        "package": PACKAGE,
        "version": VERSION,
        "backup_root": str(backup_root),
        "files_changed": files_changed,
        "action_count": accepted_count,
        "skipped_count": skipped,
        "aborted": False,
        "baseline_compile": baseline,
        "actions": actions,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"manifest": str(manifest_path), "backup_root": str(backup_root), "files_changed": files_changed, "action_count": accepted_count, "skipped_count": skipped, "aborted": False}

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


def delta(pre: dict, post: dict) -> dict:
    keys = [
        "broad_except_count", "app_broad_except_count", "silent_broad_except_count",
        "app_silent_broad_except_count", "patchable_simple_silent_except_count",
        "technical_ui_term_count",
    ]
    out = {}
    for key in keys:
        before = pre.get(key)
        after = post.get(key)
        out[key] = {"before": before, "after": after, "delta": (after - before) if isinstance(before, int) and isinstance(after, int) else None}
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all", choices=["audit", "patch", "all", "quality-gate"])
    parser.add_argument("--output-root", default="C:\\bys360")
    parser.add_argument("--max-patches", type=int, default=100)
    parser.add_argument("--run-compile", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    output_root = Path(args.output_root).resolve()
    report_dir = root / "reports" / "technical_debt"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_stamp()

    print(json.dumps({"package": PACKAGE, "version": VERSION, "mode": args.mode, "project_root": str(root)}, ensure_ascii=False))

    if args.mode == "quality-gate":
        print(json.dumps(compile_project(root, args.run_compile or True), ensure_ascii=False, indent=2))
        return 0

    pre = audit(root, report_dir, stamp, "PRE")
    print(json.dumps({"pre_audit_metrics": pre["metrics"], "pre_finding_count": pre["finding_count"], **pre["reports"]}, ensure_ascii=False, indent=2))

    patch_result = None
    if args.mode in {"patch", "all"}:
        patch_result = patch_simple_excepts(root, output_root, stamp, max(0, args.max_patches))
        print(json.dumps(patch_result, ensure_ascii=False, indent=2))

    post = audit(root, report_dir, stamp, "POST")
    diff = delta(pre["metrics"], post["metrics"])
    print(json.dumps({"post_audit_metrics": post["metrics"], "post_finding_count": post["finding_count"], "delta": diff, **post["reports"]}, ensure_ascii=False, indent=2))

    quality = compile_project(root, args.run_compile)
    print(json.dumps(quality, ensure_ascii=False, indent=2))

    ok = True
    if quality.get("compile_requested") and not quality.get("compile_ok"):
        ok = False
    if quality.get("quality9_run", {}).get("returncode", 0) not in (0, None):
        ok = False

    final = {
        "ok": ok,
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "pre_audit_metrics": pre["metrics"],
        "pre_finding_count": pre["finding_count"],
        "pre_reports": pre["reports"],
        "patch_simple_excepts": patch_result,
        "post_audit_metrics": post["metrics"],
        "post_finding_count": post["finding_count"],
        "post_reports": post["reports"],
        "delta": diff,
        "quality_gate": quality,
    }
    print(json.dumps(final, ensure_ascii=False, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
