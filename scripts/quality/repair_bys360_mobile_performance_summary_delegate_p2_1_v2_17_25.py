# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Summary Delegate P2.1 V2.17.25
Safely delegates the read-only mobile_performance_summary function to the mobile performance summary service.
Does not change URL, endpoint, blueprint registration, or function public name.
"""
from __future__ import annotations
import argparse
import ast
import json
import py_compile
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

VERSION = "V2.17.25"
SLUG = "bys360_mobile_performance_summary_delegate_p2_1_v2_17_25"
TARGET_REL = Path("app/api/mobile/performance_routes.py")
SERVICE_REL = Path("app/api/mobile/services/performance_summary_service.py")
TARGET_FUNC = "mobile_performance_summary"
LEGACY_FUNC = "_bys360_legacy_mobile_performance_summary"
DELEGATE_FUNC = "delegate_mobile_performance_summary"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def run_cmd(root: Path, args: List[str], timeout: int = 120) -> Dict[str, Any]:
    try:
        p = subprocess.run(
            args,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout_tail": (p.stdout or "")[-5000:],
            "stderr_tail": (p.stderr or "")[-5000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc)}


def compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": str(exc)}


def health(root: Path) -> Dict[str, Any]:
    compileall = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=180)
    app_factory = run_cmd(root, [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], timeout=120)
    app_ok = app_factory["ok"] and "BYS360_APP_CREATE_OK" in (app_factory.get("stdout_tail") or "")
    return {
        "compileall_ok": compileall["ok"],
        "app_factory_ok": app_ok,
        "overall_ok": compileall["ok"] and app_ok,
        "compileall": compileall,
        "app_factory": app_factory,
    }


def function_info(path: Path) -> Dict[str, Any]:
    info = {
        "exists": path.exists(),
        "path": str(path).replace("\\", "/"),
        "syntax_ok": False,
        "syntax_error": "",
        "target_exists": False,
        "target_line": None,
        "target_end_line": None,
        "target_args": "",
        "target_delegated": False,
        "legacy_exists": False,
        "legacy_line": None,
        "patchable": False,
    }
    if not path.exists():
        return info
    text = read_text(path)
    try:
        tree = ast.parse(text)
        info["syntax_ok"] = True
    except SyntaxError as exc:
        info["syntax_error"] = str(exc)
        return info
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == TARGET_FUNC:
                info["target_exists"] = True
                info["target_line"] = node.lineno
                info["target_end_line"] = getattr(node, "end_lineno", None)
                info["target_args"] = ", ".join(a.arg for a in node.args.args)
                start = node.lineno - 1
                end = getattr(node, "end_lineno", node.lineno)
                block = "\n".join(text.splitlines()[start:end])
                info["target_delegated"] = DELEGATE_FUNC in block
            if node.name == LEGACY_FUNC:
                info["legacy_exists"] = True
                info["legacy_line"] = node.lineno
    info["patchable"] = info["syntax_ok"] and info["target_exists"] and not info["target_delegated"]
    return info


def ensure_service(path: Path) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = read_text(path)
    else:
        text = '# -*- coding: utf-8 -*-\n"""Mobile performance summary service delegates."""\n\n'
    changed = False
    if DELEGATE_FUNC not in text:
        addition = '''

# P2.1 V2.17.25 - safe read-only delegation shim
def delegate_mobile_performance_summary(user, legacy_func):
    """Delegate mobile performance summary without changing route contract."""
    return legacy_func(user)
'''
        text = text.rstrip() + addition + "\n"
        changed = True
        write_text(path, text)
    return {"path": str(path).replace("\\", "/"), "changed": changed, "compile": compile_file(path)}


def patch_target(root: Path) -> Dict[str, Any]:
    target = root / TARGET_REL
    service = root / SERVICE_REL
    result: Dict[str, Any] = {
        "routes_changed": False,
        "service": {},
        "patched_functions": [],
        "skipped": [],
        "backup": "",
        "error": "",
        "target_compile_after": {},
    }
    info = function_info(target)
    if not info["exists"]:
        result["skipped"].append({"reason": "target_missing"})
        return result
    if not info["syntax_ok"]:
        result["skipped"].append({"reason": "target_syntax_error", "error": info["syntax_error"]})
        return result
    service_result = ensure_service(service)
    result["service"] = service_result
    if info["target_delegated"] and info["legacy_exists"]:
        result["skipped"].append({"reason": "already_delegated"})
        result["target_compile_after"] = {"routes": compile_file(target), "service": compile_file(service)}
        return result
    if not info["patchable"]:
        result["skipped"].append({"reason": "no_patchable_target", "info": info})
        return result

    original = read_text(target)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine = root / "_local_quarantine" / f"bys360_mobile_performance_summary_delegate_p2_1_{timestamp}" / TARGET_REL
    quarantine.parent.mkdir(parents=True, exist_ok=True)
    write_text(quarantine, original)
    result["backup"] = rel(quarantine, root)

    lines = original.splitlines()
    tree = ast.parse(original)
    target_node: Optional[ast.FunctionDef] = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == TARGET_FUNC:
            target_node = node
            break
    if target_node is None:
        result["error"] = "target_not_found_after_parse"
        return result

    dec_start = (target_node.decorator_list[0].lineno if target_node.decorator_list else target_node.lineno) - 1
    def_start = target_node.lineno - 1
    end = getattr(target_node, "end_lineno", target_node.lineno)
    decorators = lines[dec_start:def_start]
    def_line = lines[def_start]
    body = lines[def_start + 1:end]
    legacy_def_line = def_line.replace(f"def {TARGET_FUNC}", f"def {LEGACY_FUNC}", 1)

    indent = " " * (len(def_line) - len(def_line.lstrip()))
    call_args = info.get("target_args", "user") or "user"
    public_block: List[str] = []
    public_block.extend(decorators)
    public_block.append(def_line)
    public_block.append(indent + "    " + f"from app.api.mobile.services.performance_summary_service import {DELEGATE_FUNC}")
    public_block.append(indent + "    " + f"return {DELEGATE_FUNC}({call_args}, {LEGACY_FUNC})")
    public_block.append("")
    public_block.append(legacy_def_line)
    public_block.extend(body if body else [indent + "    pass"])

    new_lines = lines[:dec_start] + public_block + lines[end:]
    new_text = "\n".join(new_lines) + ("\n" if original.endswith("\n") else "")
    write_text(target, new_text)
    result["routes_changed"] = True
    result["patched_functions"].append(TARGET_FUNC)
    result["target_compile_after"] = {"routes": compile_file(target), "service": compile_file(service)}

    if not result["target_compile_after"]["routes"]["ok"] or not result["target_compile_after"]["service"]["ok"]:
        write_text(target, original)
        result["routes_changed"] = False
        result["patched_functions"] = []
        result["error"] = "target_compile_failed_after_patch_rollback_done"
        result["target_compile_after_rollback"] = {"routes": compile_file(target), "service": compile_file(service)}
    return result


def write_reports(root: Path, report: Dict[str, Any]) -> None:
    outdir = root / "reports" / "quality"
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / f"{SLUG}_report.json"
    md_path = outdir / f"{SLUG}_report.md"
    report["json_report"] = rel(json_path, root)
    report["md_report"] = rel(md_path, root)
    write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))
    audit = report.get("audit", {})
    apply = report.get("apply", {})
    h = report.get("health_summary", {})
    md = []
    md.append(f"# BYS360 Mobile Performance Summary Delegate P2.1 {VERSION}")
    md.append("")
    md.append("Bu rapor mobil performans özet endpointinin URL, endpoint ve blueprint adı korunarak servis delegasyonuna alınma sonucunu gösterir.")
    md.append("")
    md.append("## Durum")
    md.append(f"- mode: {report.get('mode')}")
    md.append("")
    md.append("## Audit")
    md.append(f"- target_exists: {audit.get('target_exists')}")
    md.append(f"- target_line: {audit.get('target_line')}")
    md.append(f"- delegated: {audit.get('target_delegated')}")
    md.append(f"- legacy_exists: {audit.get('legacy_exists')}")
    md.append(f"- patchable: {audit.get('patchable')}")
    md.append("")
    md.append("## Apply")
    md.append(f"- service: `{apply.get('service')}`")
    md.append(f"- routes_changed: {apply.get('routes_changed')}")
    md.append(f"- patched_functions: {apply.get('patched_functions')}")
    md.append(f"- skipped: {apply.get('skipped')}")
    md.append(f"- backup: {apply.get('backup')}")
    md.append(f"- error: {apply.get('error')}")
    md.append("")
    md.append("## Sağlık Kontrolü")
    md.append(f"- compileall_ok: {h.get('compileall_ok')}")
    md.append(f"- app_factory_ok: {h.get('app_factory_ok')}")
    md.append(f"- overall_ok: {h.get('overall_ok')}")
    md.append("")
    write_text(md_path, "\n".join(md))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "all"], default="audit")
    ns = ap.parse_args()
    root = Path(ns.project_root).resolve()
    target = root / TARGET_REL
    report: Dict[str, Any] = {
        "version": VERSION,
        "mode": ns.mode,
        "project_root": str(root),
        "audit": {},
        "apply": {},
        "health_summary": {},
    }
    info = function_info(target)
    report["audit"] = info
    if ns.mode in ("apply", "all"):
        apply_result = patch_target(root)
        report["apply"] = apply_result
        if ns.mode == "all":
            h = health(root)
            report["health_summary"] = h
            if not h["overall_ok"]:
                backup_rel = apply_result.get("backup")
                if apply_result.get("routes_changed") and backup_rel:
                    backup_path = root / backup_rel
                    if backup_path.exists():
                        write_text(target, read_text(backup_path))
                        report["apply"]["full_rollback"] = True
                        report["health_summary_after_rollback"] = health(root)
    if ns.mode == "all" and not report.get("health_summary"):
        report["health_summary"] = health(root)
    write_reports(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": ns.mode,
        "audit": report.get("audit", {}),
        "apply": report.get("apply", {}),
        "health_summary": report.get("health_summary", {}),
        "json_report": report.get("json_report"),
        "md_report": report.get("md_report"),
    }, ensure_ascii=False, indent=2))
    if ns.mode == "all":
        if report.get("health_summary", {}).get("overall_ok"):
            print("BYS360_MOBILE_PERFORMANCE_SUMMARY_DELEGATE_P2_1_V2_17_25_HEALTH_OK")
            print("BYS360_MOBILE_PERFORMANCE_SUMMARY_DELEGATE_P2_1_V2_17_25_APPLY_OK")
            print("BYS360_MOBILE_PERFORMANCE_SUMMARY_DELEGATE_P2_1_V2_17_25_OK")
            return 0
        print("BYS360_MOBILE_PERFORMANCE_SUMMARY_DELEGATE_P2_1_V2_17_25_HEALTH_FAIL")
        return 1
    print("BYS360_MOBILE_PERFORMANCE_SUMMARY_DELEGATE_P2_1_V2_17_25_REPORT_OK")
    print("BYS360_MOBILE_PERFORMANCE_SUMMARY_DELEGATE_P2_1_V2_17_25_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
