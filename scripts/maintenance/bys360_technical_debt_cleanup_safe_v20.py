# -*- coding: utf-8 -*-
"""BYS360 Technical Debt Cleanup SAFE V20.

Purpose:
- Patch only two SAFEISH manual exception handlers in
  app/services/corporate_information_center.py.
- Do not touch DB rollback / rollback+return / raise / continue blocks.
- Backup before change and restore automatically if compile fails.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V20"
VERSION = "V20"
TARGET_REL = Path("app/services/corporate_information_center.py")
LOGGER_LINE = '__import__("logging").getLogger(__name__).exception("BYS360 CIC kontrollü geri dönüş bloğu çalıştı")'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_display(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("/", "\\")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def backup_file(project_root: Path, backup_root: Path, target: Path) -> Path:
    rel = target.relative_to(project_root)
    dest = backup_root / "files" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, dest)
    return dest


def compile_one(path: Path) -> Tuple[bool, str]:
    cmd = [sys.executable, "-m", "py_compile", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode == 0, (proc.stderr or proc.stdout or "")[-4000:]


def compile_project(project_root: Path) -> Dict[str, Any]:
    checked = 0
    errors: List[Dict[str, str]] = []
    for path in project_root.rglob("*.py"):
        parts = set(path.parts)
        if any(x in parts for x in {".venv", "venv", "__pycache__", ".git"}):
            continue
        checked += 1
        ok, detail = compile_one(path)
        if not ok:
            errors.append({"path": rel_display(path, project_root), "error": detail})
            if len(errors) >= 25:
                break
    return {"ok": not errors, "checked_python_files": checked, "error_count": len(errors), "errors": errors}


def run_quality9(project_root: Path) -> Dict[str, Any]:
    script = project_root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"
    if not script.exists():
        return {"missing": True, "returncode": None, "stdout_tail": "", "stderr_tail": ""}
    proc = subprocess.run([sys.executable, str(script), "--project-root", str(project_root)], capture_output=True, text=True)
    return {
        "missing": False,
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-1000:],
        "stderr_tail": (proc.stderr or "")[-1000:],
    }


def has_logging_stmt(handler: ast.ExceptHandler) -> bool:
    for node in ast.walk(handler):
        text = ""
        try:
            text = ast.unparse(node)
        except Exception:
            text = ""
        low = text.lower()
        if "logger." in low or "logging." in low or ".exception(" in low or ".warning(" in low or ".error(" in low:
            return True
    return False


def body_kind(handler: ast.ExceptHandler) -> str:
    kinds = []
    for stmt in handler.body:
        if isinstance(stmt, ast.Assign):
            kinds.append("fallback_assignment")
        elif isinstance(stmt, ast.AugAssign):
            kinds.append("fallback_assignment")
        elif isinstance(stmt, ast.Expr):
            kinds.append("expression")
        elif isinstance(stmt, ast.Return):
            kinds.append("return")
        elif isinstance(stmt, ast.Raise):
            kinds.append("raise")
        elif isinstance(stmt, ast.Pass):
            kinds.append("pass")
        elif isinstance(stmt, ast.Try):
            kinds.append("try")
        else:
            kinds.append(type(stmt).__name__.lower())
    return "+".join(kinds)


def is_broad_exception(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    try:
        t = ast.unparse(handler.type)
    except Exception:
        t = ""
    return t in {"Exception", "BaseException"}


def stmt_text(stmt: ast.AST) -> str:
    try:
        return ast.unparse(stmt)
    except Exception:
        return ""


def classify_handler(handler: ast.ExceptHandler) -> Dict[str, Any]:
    first = stmt_text(handler.body[0]) if handler.body else ""
    all_text = "\n".join(stmt_text(s) for s in handler.body)
    logged = has_logging_stmt(handler)
    kind = body_kind(handler)
    category = "already_logged" if logged else "manual_review"
    can_patch = False
    skip_reason = "not_safeish"

    low_all = all_text.lower()
    if not logged:
        # V20 intentionally patches only these two non-control-flow, non-DB rollback safeish handlers.
        if 'result["ok"] = false' in low_all and 'warnings' in low_all and 'str(exc)' in low_all and 'return ' not in low_all:
            category = "manual_safeish_result_warning"
            can_patch = True
            skip_reason = ""
        elif "special_days.last_error" in all_text and "set_setting" in all_text and "return " not in low_all and "raise" not in low_all:
            category = "manual_safeish_last_error_setting"
            can_patch = True
            skip_reason = ""
        elif "db.session.rollback" in low_all:
            category = "manual_risky_db_rollback"
            skip_reason = "db_rollback_requires_manual_review"
        elif "_rollback(rollback)" in low_all:
            category = "manual_risky_rollback_return"
            skip_reason = "rollback_return_requires_manual_review"
        elif "return " in low_all or "raise" in low_all or "continue" in low_all:
            category = "manual_risky_control_flow"
            skip_reason = "control_flow_requires_manual_review"
        else:
            category = "manual_expression_review"
            skip_reason = "manual_review_required"

    return {
        "lineno": getattr(handler, "lineno", None),
        "end_lineno": getattr(handler, "end_lineno", None),
        "body_lineno": getattr(handler.body[0], "lineno", None) if handler.body else None,
        "kind": kind,
        "logged": logged,
        "category": category,
        "first_body": first[:260],
        "can_patch": can_patch,
        "skip_reason": skip_reason,
    }


def summarize_target(project_root: Path) -> Dict[str, Any]:
    target = project_root / TARGET_REL
    if not target.exists():
        return {"target": str(TARGET_REL).replace("/", "\\"), "exists": False}
    source = read_text(target)
    tree = ast.parse(source)
    broad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and is_broad_exception(node):
            broad.append(node)
    contexts = [classify_handler(h) for h in broad]
    by_category: Dict[str, int] = {}
    for c in contexts:
        by_category[c["category"]] = by_category.get(c["category"], 0) + 1
    return {
        "target": str(TARGET_REL).replace("/", "\\"),
        "exists": True,
        "broad_except_count": len(broad),
        "logged_count": sum(1 for c in contexts if c["logged"]),
        "manual_count": sum(1 for c in contexts if not c["logged"]),
        "safeish_candidate_count": sum(1 for c in contexts if c["can_patch"]),
        "risky_count": sum(1 for c in contexts if (not c["logged"] and not c["can_patch"])),
        "by_category": by_category,
        "top_manual_contexts": [c for c in contexts if not c["logged"]][:30],
    }


def patch_target(project_root: Path, output_root: Path, max_patches: int) -> Dict[str, Any]:
    target = project_root / TARGET_REL
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = output_root / "backups" / f"technical_debt_safe_v20_{stamp}"
    reports_dir = project_root / "reports" / "technical_debt"
    reports_dir.mkdir(parents=True, exist_ok=True)

    pre = summarize_target(project_root)
    actions: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    aborted = False
    abort_reason = ""
    backup_path = None

    if not target.exists():
        return {"target": str(TARGET_REL).replace("/", "\\"), "files_changed": 0, "action_count": 0, "skipped_count": 0, "aborted": True, "abort_reason": "target_missing", "pre_target_metrics": pre, "post_target_metrics": pre}

    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_file(project_root, backup_root, target)

    while len(actions) < max_patches:
        source = read_text(target)
        tree = ast.parse(source)
        candidates = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and is_broad_exception(node):
                c = classify_handler(node)
                if c["can_patch"]:
                    candidates.append((node, c))
        if not candidates:
            break

        # Patch bottom-up one-by-one and compile after each patch.
        node, ctx = sorted(candidates, key=lambda item: item[1]["body_lineno"] or 0, reverse=True)[0]
        lines = source.splitlines()
        body_lineno = ctx["body_lineno"]
        if not body_lineno or body_lineno < 1 or body_lineno > len(lines):
            ctx["action"] = "skip"
            ctx["skip_reason"] = "invalid_body_lineno"
            skipped.append(ctx)
            break
        body_line = lines[body_lineno - 1]
        indent = body_line[: len(body_line) - len(body_line.lstrip())]
        insert_line = indent + LOGGER_LINE
        if body_lineno >= 2 and LOGGER_LINE in lines[body_lineno - 2]:
            ctx["action"] = "skip"
            ctx["skip_reason"] = "already_inserted_nearby"
            skipped.append(ctx)
            break

        before_hash = sha256(target)
        new_lines = lines[: body_lineno - 1] + [insert_line] + lines[body_lineno - 1 :]
        write_text(target, "\n".join(new_lines) + ("\n" if source.endswith("\n") else ""))
        ok, detail = compile_one(target)
        if not ok:
            shutil.copy2(backup_path, target)
            aborted = True
            abort_reason = "compile_failed_after_patch: " + detail
            ctx["action"] = "rollback_after_compile_failure"
            ctx["compile_error"] = detail
            skipped.append(ctx)
            break
        after_hash = sha256(target)
        ctx["action"] = "insert_logger_exception"
        ctx["before_sha256"] = before_hash
        ctx["after_sha256"] = after_hash
        actions.append(ctx)

    post = summarize_target(project_root)
    manifest = {
        "package": PACKAGE,
        "version": VERSION,
        "target": str(TARGET_REL).replace("/", "\\"),
        "backup_root": str(backup_root),
        "backup_file": str(backup_path) if backup_path else "",
        "action_count": len(actions),
        "skipped_count": len(skipped),
        "aborted": aborted,
        "abort_reason": abort_reason,
        "actions": actions,
        "skipped": skipped,
        "pre_target_metrics": pre,
        "post_target_metrics": post,
    }
    manifest_path = reports_dir / f"{PACKAGE}_ACTIONS_{stamp}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "manifest": str(manifest_path),
        "backup_root": str(backup_root),
        "target": str(TARGET_REL).replace("/", "\\"),
        "files_changed": 1 if actions else 0,
        "action_count": len(actions),
        "skipped_count": len(skipped),
        "aborted": aborted,
        "abort_reason": abort_reason,
        "actions": actions,
        "skipped": skipped,
        "pre_target_metrics": pre,
        "post_target_metrics": post,
    }


def security_hygiene(project_root: Path) -> Dict[str, Any]:
    env_files = [p for p in [project_root / ".env"] if p.exists()]
    local_dbs = list((project_root / "instance").glob("*.sqlite3")) if (project_root / "instance").exists() else []
    gitignore = project_root / ".gitignore"
    text = read_text(gitignore) if gitignore.exists() else ""
    return {
        "env_files": [rel_display(p, project_root) for p in env_files],
        "local_dbs": [rel_display(p, project_root) for p in local_dbs],
        "gitignore_exists": gitignore.exists(),
        "gitignore_protections": {
            "has_env_rule": ".env" in text,
            "has_sqlite_rule": "*.sqlite" in text or "*.sqlite3" in text,
            "has_safe_v17_block": "BEGIN BYS360 SAFE V17" in text,
        },
    }


def write_reports(project_root: Path, result: Dict[str, Any]) -> Dict[str, str]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = project_root / "reports" / "technical_debt"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / f"{PACKAGE}_{stamp}.json"
    md_path = reports_dir / f"{PACKAGE}_{stamp}_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    patch = result.get("patch_corporate_information_center", {})
    post = patch.get("post_target_metrics", {})
    lines = [
        f"# {PACKAGE} {VERSION} Raporu",
        "",
        "## Amaç",
        "corporate_information_center.py içinde V19 tarafından safeish olarak işaretlenen iki manuel exception bloğuna log eklemek.",
        "DB rollback, raise, return, continue ve kontrol akışı içeren riskli bloklara dokunulmadı.",
        "",
        "## Sonuç",
        f"- Kod değişti: {result.get('code_changed')}",
        f"- Action count: {patch.get('action_count')}",
        f"- Skipped count: {patch.get('skipped_count')}",
        f"- Aborted: {patch.get('aborted')}",
        f"- Safeish kalan: {post.get('safeish_candidate_count')}",
        f"- Riskli kalan: {post.get('risky_count')}",
        "",
        "## Sonraki Adım",
        "Kalan riskli DB rollback / rollback-return blokları otomatik patch değil, manuel refactor planıyla ele alınmalıdır.",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json_report": str(json_path), "summary_report": str(md_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all")
    parser.add_argument("--output-root", default="C:\\bys360")
    parser.add_argument("--max-patches", type=int, default=2)
    parser.add_argument("--run-compile", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_root = Path(args.output_root).resolve()
    print(json.dumps({"package": PACKAGE, "version": VERSION, "mode": args.mode, "project_root": str(project_root)}, ensure_ascii=False))

    pre = summarize_target(project_root)
    patch = patch_target(project_root, output_root, max(0, args.max_patches))
    post = patch.get("post_target_metrics", summarize_target(project_root))

    compile_detail = {"ok": None, "checked_python_files": 0, "error_count": 0, "errors": []}
    if args.run_compile:
        compile_detail = compile_project(project_root)
    q9 = run_quality9(project_root)
    quality_gate = {
        "compile_requested": bool(args.run_compile),
        "compile_ok": bool(compile_detail.get("ok")) if args.run_compile else None,
        "compile_detail": compile_detail,
        "existing_quality_gate": str(project_root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"),
        "quality9_run": q9,
    }

    live_readiness = {
        "compile_green": bool(compile_detail.get("ok")) if args.run_compile else None,
        "quality9_green": q9.get("returncode") == 0,
        "corporate_info_safeish_remaining": post.get("safeish_candidate_count"),
        "corporate_info_risky_remaining": post.get("risky_count"),
        "effective_menu_risky_remaining_note": "V19 raporuna göre 3 rollback/return bloğu manuel kalır.",
        "blockers": [],
    }
    if post.get("safeish_candidate_count", 0):
        live_readiness["blockers"].append("safeish_manual_exception_left")
    if q9.get("returncode") != 0:
        live_readiness["blockers"].append("quality9_not_green")
    if args.run_compile and not compile_detail.get("ok"):
        live_readiness["blockers"].append("compile_not_green")

    result: Dict[str, Any] = {
        "ok": not patch.get("aborted") and not live_readiness["blockers"],
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "code_changed": bool(patch.get("action_count")),
        "target": str(TARGET_REL).replace("/", "\\"),
        "pre_target_metrics": pre,
        "post_target_metrics": post,
        "delta_target_metrics": {
            "logged_count": {"before": pre.get("logged_count"), "after": post.get("logged_count"), "delta": (post.get("logged_count") or 0) - (pre.get("logged_count") or 0)},
            "manual_count": {"before": pre.get("manual_count"), "after": post.get("manual_count"), "delta": (post.get("manual_count") or 0) - (pre.get("manual_count") or 0)},
            "safeish_candidate_count": {"before": pre.get("safeish_candidate_count"), "after": post.get("safeish_candidate_count"), "delta": (post.get("safeish_candidate_count") or 0) - (pre.get("safeish_candidate_count") or 0)},
            "risky_count": {"before": pre.get("risky_count"), "after": post.get("risky_count"), "delta": (post.get("risky_count") or 0) - (pre.get("risky_count") or 0)},
        },
        "patch_corporate_information_center": patch,
        "security_hygiene": security_hygiene(project_root),
        "live_readiness": live_readiness,
        "quality_gate": quality_gate,
        "next_step": "V21: kalan riskli rollback/db.rollback blokları için kod değiştirmeyen manuel refactor planı veya canlı final smoke kontrolü.",
    }
    reports = write_reports(project_root, result)
    result["reports"] = reports
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
