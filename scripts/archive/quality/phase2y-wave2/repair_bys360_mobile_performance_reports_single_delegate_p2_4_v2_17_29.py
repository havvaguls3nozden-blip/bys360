# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Reports Single Delegate P2.4 V2.17.29
- Targets only mobile_performance_reports.
- Preserves URL/endpoint/blueprint registration by keeping the public function name.
- Keeps legacy body as _bys360_legacy_mobile_performance_reports.
- Delegates the public function to performance_summary_service using a local import.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

VERSION = "V2.17.29"
TARGET_FN = "mobile_performance_reports"
LEGACY_FN = "_bys360_legacy_mobile_performance_reports"
SERVICE_FN = "delegate_mobile_performance_reports"
REL_TARGET = Path("app/api/mobile/performance_routes.py")
REL_SERVICE = Path("app/api/mobile/services/performance_summary_service.py")
REPORT_JSON = Path("reports/quality/bys360_mobile_performance_reports_single_delegate_p2_4_v2_17_29_report.json")
REPORT_MD = Path("reports/quality/bys360_mobile_performance_reports_single_delegate_p2_4_v2_17_29_report.md")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _run(cmd: List[str], cwd: Path, timeout: int = 90) -> Dict[str, Any]:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
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


def _compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "file_not_found"}
    try:
        compile(_read(path), str(path), "exec")
        return {"exists": True, "ok": True, "error": ""}
    except SyntaxError as exc:
        return {"exists": True, "ok": False, "error": f"{exc.__class__.__name__}: {exc}"}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": repr(exc)}


def _parse_functions(text: str) -> Tuple[Optional[ast.Module], str]:
    try:
        return ast.parse(text), ""
    except SyntaxError as exc:
        return None, f"{exc.__class__.__name__}: {exc}"


def _find_function(tree: ast.Module, name: str) -> Optional[ast.FunctionDef]:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _decorator_start(node: ast.FunctionDef) -> int:
    lines = [getattr(node, "lineno", 1)]
    for deco in getattr(node, "decorator_list", []) or []:
        lines.append(getattr(deco, "lineno", node.lineno))
    return min(lines)


def _function_info(path: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "target_exists": path.exists(),
        "target_compile": _compile_file(path),
        "parse_error": "",
        "function": {
            "name": TARGET_FN,
            "exists": False,
            "line": None,
            "end_line": None,
            "length": None,
            "route_decorator": False,
            "delegated": False,
            "legacy": False,
            "patchable": False,
            "arg": "",
        },
    }
    if not path.exists():
        return info
    text = _read(path)
    tree, err = _parse_functions(text)
    info["parse_error"] = err
    if not tree:
        return info
    fn = _find_function(tree, TARGET_FN)
    legacy = _find_function(tree, LEGACY_FN)
    info["function"]["legacy"] = legacy is not None
    if not fn:
        return info
    seg = ast.get_source_segment(text, fn) or ""
    args = [a.arg for a in fn.args.args]
    decorators = [ast.get_source_segment(text, d) or "" for d in fn.decorator_list]
    delegated = SERVICE_FN in seg or "performance_summary_service" in seg
    info["function"].update({
        "exists": True,
        "line": fn.lineno,
        "end_line": getattr(fn, "end_lineno", fn.lineno),
        "length": (getattr(fn, "end_lineno", fn.lineno) - fn.lineno + 1),
        "route_decorator": any("route" in d or "add_url_rule" in d for d in decorators),
        "delegated": delegated,
        "arg": ", ".join(args),
        "patchable": (not delegated and legacy is None),
    })
    return info


def _ensure_service(path: Path) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = _read(path)
    else:
        text = '"""Mobile performance summary service delegates."""\n\n'
    changed = False
    if SERVICE_FN not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += (
            "\n\ndef delegate_mobile_performance_reports(legacy_func, *args, **kwargs):\n"
            "    \"\"\"Delegate performance reports endpoint while preserving legacy behavior.\"\"\"\n"
            "    return legacy_func(*args, **kwargs)\n"
        )
        changed = True
    if changed:
        _write(path, text)
    return {"path": str(path), "changed": changed, "compile": _compile_file(path)}


def _patch_target(path: Path, service_path: Path, root: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "routes_changed": False,
        "patched_functions": [],
        "backup": "",
        "error": "",
        "rolled_back": False,
        "target_compile": {},
    }
    text = _read(path)
    tree, err = _parse_functions(text)
    if err or not tree:
        result["error"] = err or "parse_error"
        return result
    fn = _find_function(tree, TARGET_FN)
    if not fn:
        result["error"] = "target_function_not_found"
        return result
    if _find_function(tree, LEGACY_FN):
        result["error"] = "legacy_already_exists"
        return result
    seg = ast.get_source_segment(text, fn) or ""
    if SERVICE_FN in seg:
        result["error"] = "already_delegated"
        return result

    lines = text.splitlines()
    start = _decorator_start(fn) - 1
    def_start = fn.lineno - 1
    end = getattr(fn, "end_lineno", fn.lineno)
    decorator_lines = lines[start:def_start]
    function_lines = lines[def_start:end]
    if not function_lines or f"def {TARGET_FN}" not in function_lines[0]:
        result["error"] = "unexpected_function_header"
        return result

    legacy_lines = function_lines.copy()
    legacy_lines[0] = legacy_lines[0].replace(f"def {TARGET_FN}", f"def {LEGACY_FN}", 1)

    # Public wrapper keeps original decorators, signature and name.
    wrapper_lines = []
    wrapper_lines.extend(decorator_lines)
    wrapper_lines.append(function_lines[0])
    indent = " " * (len(function_lines[0]) - len(function_lines[0].lstrip()))
    body_indent = indent + "    "
    wrapper_lines.extend([
        f"{body_indent}from app.api.mobile.services.performance_summary_service import {SERVICE_FN}",
        f"{body_indent}return {SERVICE_FN}({LEGACY_FN}, user)",
    ])

    new_block = legacy_lines + [""] + wrapper_lines
    new_lines = lines[:start] + new_block + lines[end:]
    new_text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = root / "_local_quarantine" / f"bys360_mobile_performance_reports_single_delegate_p2_4_{stamp}" / REL_TARGET
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup)
    result["backup"] = str(backup.relative_to(root))

    _write(path, new_text)
    route_compile = _compile_file(path)
    service_compile = _compile_file(service_path)
    result["target_compile"] = {"routes": route_compile, "service": service_compile}
    if not (route_compile.get("ok") and service_compile.get("ok")):
        shutil.copy2(backup, path)
        result["rolled_back"] = True
        result["error"] = "target_compile_failed_after_patch"
        result["target_compile_after_rollback"] = {"routes": _compile_file(path), "service": _compile_file(service_path)}
        return result

    result["routes_changed"] = True
    result["patched_functions"] = [TARGET_FN]
    return result


def _health(root: Path) -> Dict[str, Any]:
    compileall = _run([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], root, timeout=180)
    app_factory = _run([sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], root, timeout=120)
    return {
        "compileall_ok": bool(compileall.get("ok")),
        "app_factory_ok": bool(app_factory.get("ok") and "BYS360_APP_CREATE_OK" in app_factory.get("stdout_tail", "")),
        "overall_ok": bool(compileall.get("ok") and app_factory.get("ok") and "BYS360_APP_CREATE_OK" in app_factory.get("stdout_tail", "")),
        "compileall": compileall,
        "app_factory": app_factory,
    }


def _write_reports(root: Path, report: Dict[str, Any]) -> None:
    json_path = root / REPORT_JSON
    md_path = root / REPORT_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    fn = report.get("audit", {}).get("function", {})
    apply = report.get("apply", {})
    health = report.get("health_summary", {})
    md = []
    md.append("# BYS360 Mobile Performance Reports Single Delegate P2.4 V2.17.29\n")
    md.append("Bu rapor tek ve güvenli okuma endpointi olan `mobile_performance_reports` fonksiyonunun servis delegasyonu sonucunu gösterir.\n")
    md.append("## Durum\n")
    md.append(f"- mode: {report.get('mode')}\n")
    md.append("## Audit\n")
    md.append(f"- target_exists: {report.get('audit', {}).get('target_exists')}\n")
    md.append(f"- target_compile: `{report.get('audit', {}).get('target_compile')}`\n")
    md.append("\n| Fonksiyon | Var | Satır | Uzunluk | Route Decorator | Delegated | Legacy | Patchable | Arg |\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---|\n")
    md.append(f"| `{fn.get('name')}` | {fn.get('exists')} | {fn.get('line')} | {fn.get('length')} | {fn.get('route_decorator')} | {fn.get('delegated')} | {fn.get('legacy')} | {fn.get('patchable')} | `{fn.get('arg')}` |\n")
    md.append("\n## Apply\n")
    if apply:
        md.append(f"- service: `{apply.get('service')}`\n")
        md.append(f"- routes_changed: {apply.get('routes_changed')}\n")
        md.append(f"- patched_functions: {apply.get('patched_functions')}\n")
        md.append(f"- backup: {apply.get('backup')}\n")
        md.append(f"- error: {apply.get('error', '')}\n")
        md.append(f"- rolled_back: {apply.get('rolled_back')}\n")
        md.append(f"- target_compile: `{apply.get('target_compile')}`\n")
    else:
        md.append("- apply çalıştırılmadı.\n")
    md.append("\n## Sağlık Kontrolü\n")
    md.append(f"- compileall_ok: {health.get('compileall_ok')}\n")
    md.append(f"- app_factory_ok: {health.get('app_factory_ok')}\n")
    md.append(f"- overall_ok: {health.get('overall_ok')}\n")
    md_path.write_text("".join(md), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "apply", "health", "all"], default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    target = root / REL_TARGET
    service = root / REL_SERVICE

    report: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "audit": _function_info(target),
        "apply": {},
        "health_summary": {},
        "json_report": str(REPORT_JSON),
        "md_report": str(REPORT_MD),
    }

    if args.mode in {"apply", "all"}:
        service_result = _ensure_service(service)
        apply_result = _patch_target(target, service, root)
        apply_result["service"] = service_result
        report["apply"] = apply_result

    if args.mode in {"health", "all"}:
        report["health_summary"] = _health(root)

    _write_reports(root, report)
    print(json.dumps({k: v for k, v in report.items() if k not in {"health_summary"} or args.mode != "all"}, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_REPORTS_SINGLE_DELEGATE_P2_4_V2_17_29_REPORT_OK")
    if report.get("health_summary"):
        if report["health_summary"].get("overall_ok"):
            print("BYS360_MOBILE_PERFORMANCE_REPORTS_SINGLE_DELEGATE_P2_4_V2_17_29_HEALTH_OK")
        else:
            print("BYS360_MOBILE_PERFORMANCE_REPORTS_SINGLE_DELEGATE_P2_4_V2_17_29_HEALTH_FAIL")
            return 1
    if args.mode in {"apply", "all"}:
        apply = report.get("apply", {})
        if apply.get("routes_changed") and not apply.get("rolled_back"):
            print("BYS360_MOBILE_PERFORMANCE_REPORTS_SINGLE_DELEGATE_P2_4_V2_17_29_APPLY_OK")
        elif apply.get("rolled_back"):
            print("BYS360_MOBILE_PERFORMANCE_REPORTS_SINGLE_DELEGATE_P2_4_V2_17_29_APPLY_ROLLBACK")
            return 1
        elif apply.get("error") in {"already_delegated", "legacy_already_exists"}:
            print("BYS360_MOBILE_PERFORMANCE_REPORTS_SINGLE_DELEGATE_P2_4_V2_17_29_APPLY_NOOP")
        else:
            print("BYS360_MOBILE_PERFORMANCE_REPORTS_SINGLE_DELEGATE_P2_4_V2_17_29_APPLY_FAIL")
            return 1
    print("BYS360_MOBILE_PERFORMANCE_REPORTS_SINGLE_DELEGATE_P2_4_V2_17_29_OK")
    print("Rapor dosyalari:")
    print(f"- {REPORT_MD}")
    print(f"- {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
