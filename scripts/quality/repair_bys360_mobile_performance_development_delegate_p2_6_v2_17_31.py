# -*- coding: utf-8 -*-
"""BYS360 Mobile Performance Development Delegate P2.6 V2.17.31

Tek ve güvenli okuma endpointi olan mobile_performance_development_suggestions
fonksiyonunu URL/endpoint/blueprint adlarını değiştirmeden servis delegasyonuna alır.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "V2.17.31"
TARGET_NAME = "mobile_performance_development_suggestions"
LEGACY_NAME = f"_bys360_legacy_{TARGET_NAME}"
DELEGATE_NAME = f"{TARGET_NAME}_delegate"
TARGET_REL = Path("app/api/mobile/performance_routes.py")
SERVICE_REL = Path("app/api/mobile/services/performance_summary_service.py")
REPORT_JSON_REL = Path("reports/quality/bys360_mobile_performance_development_delegate_p2_6_v2_17_31_report.json")
REPORT_MD_REL = Path("reports/quality/bys360_mobile_performance_development_delegate_p2_6_v2_17_31_report.md")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "file_not_found"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:  # pragma: no cover
        return {"exists": True, "ok": False, "error": str(exc)}


def run_cmd(root: Path, args: List[str], timeout: int = 120) -> Dict[str, Any]:
    try:
        cp = subprocess.run(
            args,
            cwd=str(root),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-5000:],
            "stderr_tail": cp.stderr[-5000:],
        }
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(exc)}


def health(root: Path) -> Dict[str, Any]:
    compileall = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=180)
    app_factory = run_cmd(
        root,
        [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"],
        timeout=180,
    )
    return {
        "compileall_ok": bool(compileall.get("ok")),
        "app_factory_ok": bool(app_factory.get("ok")),
        "overall_ok": bool(compileall.get("ok") and app_factory.get("ok")),
        "compileall": compileall,
        "app_factory": app_factory,
    }


def parse_functions(path: Path) -> Tuple[Optional[ast.Module], str]:
    text = read_text(path)
    try:
        return ast.parse(text), ""
    except SyntaxError as exc:
        return None, str(exc)


def arg_string(fn: ast.FunctionDef) -> str:
    parts: List[str] = []
    for a in fn.args.posonlyargs + fn.args.args:
        parts.append(a.arg)
    if fn.args.vararg:
        parts.append("*" + fn.args.vararg.arg)
    for a in fn.args.kwonlyargs:
        parts.append(a.arg)
    if fn.args.kwarg:
        parts.append("**" + fn.args.kwarg.arg)
    return ", ".join(parts)


def find_function(module: ast.Module, name: str) -> Optional[ast.FunctionDef]:
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def has_route_decorator(fn: ast.FunctionDef) -> bool:
    if not fn.decorator_list:
        return False
    for dec in fn.decorator_list:
        s = ast.unparse(dec) if hasattr(ast, "unparse") else ""
        if ".route" in s or "route(" in s or "add_url_rule" in s:
            return True
    return False


def is_delegated(fn: ast.FunctionDef) -> bool:
    try:
        src = ast.unparse(fn)
    except Exception:
        src = ""
    return DELEGATE_NAME in src or "performance_summary_service" in src


def audit(root: Path) -> Dict[str, Any]:
    target = root / TARGET_REL
    service = root / SERVICE_REL
    mod, parse_error = parse_functions(target) if target.exists() else (None, "file_not_found")
    fn = find_function(mod, TARGET_NAME) if mod else None
    legacy = find_function(mod, LEGACY_NAME) if mod else None
    info: Dict[str, Any] = {
        "target_exists": target.exists(),
        "target_path": str(TARGET_REL),
        "target_compile": compile_file(target),
        "service_exists": service.exists(),
        "service_path": str(SERVICE_REL),
        "service_compile": compile_file(service),
        "parse_error": parse_error,
        "function": {
            "name": TARGET_NAME,
            "exists": fn is not None,
            "line": getattr(fn, "lineno", None),
            "end_line": getattr(fn, "end_lineno", None),
            "length": (getattr(fn, "end_lineno", 0) - getattr(fn, "lineno", 0) + 1) if fn else 0,
            "route_decorator": has_route_decorator(fn) if fn else False,
            "delegated": is_delegated(fn) if fn else False,
            "legacy": legacy is not None,
            "patchable": bool(fn is not None and legacy is None and not (is_delegated(fn) if fn else False)),
            "arg": arg_string(fn) if fn else "",
        },
    }
    return info


def ensure_service_delegate(service_path: Path, fn_args: str) -> Dict[str, Any]:
    if service_path.exists():
        text = read_text(service_path)
    else:
        text = '# -*- coding: utf-8 -*-\n"""BYS360 mobile performance summary service delegates."""\n\n'

    if f"def {DELEGATE_NAME}(" in text:
        return {"path": str(SERVICE_REL), "changed": False, "compile": compile_file(service_path)}

    call_args = fn_args.strip()
    if not call_args:
        call_args = ""
    addition = f'''


def {DELEGATE_NAME}({fn_args}):
    """Delegate wrapper for {TARGET_NAME}; keeps route URL and endpoint stable."""
    from app.api.mobile import performance_routes as _legacy_routes
    return _legacy_routes.{LEGACY_NAME}({call_args})
'''
    write_text(service_path, text.rstrip() + addition + "\n")
    return {"path": str(SERVICE_REL), "changed": True, "compile": compile_file(service_path)}


def patch_target(root: Path) -> Dict[str, Any]:
    target = root / TARGET_REL
    service = root / SERVICE_REL
    text = read_text(target)
    lines = text.splitlines(keepends=True)
    mod = ast.parse(text)
    fn = find_function(mod, TARGET_NAME)
    legacy = find_function(mod, LEGACY_NAME)
    if not fn:
        return {"routes_changed": False, "patched_functions": [], "skipped": ["target_not_found"], "error": "", "rolled_back": False}
    if legacy or is_delegated(fn):
        return {"routes_changed": False, "patched_functions": [], "skipped": ["already_delegated_or_legacy_exists"], "error": "", "rolled_back": False}
    if fn.lineno is None or fn.end_lineno is None:
        return {"routes_changed": False, "patched_functions": [], "skipped": [], "error": "missing_lineno", "rolled_back": False}

    fn_args = arg_string(fn)
    if not fn_args:
        return {"routes_changed": False, "patched_functions": [], "skipped": [], "error": "empty_args_not_supported", "rolled_back": False}

    service_result = ensure_service_delegate(service, fn_args)
    if not service_result.get("compile", {}).get("ok"):
        return {"routes_changed": False, "patched_functions": [], "service": service_result, "skipped": [], "error": "service_compile_failed", "rolled_back": False}

    # Backup current files
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine = root / "_local_quarantine" / f"bys360_mobile_performance_development_delegate_p2_6_{stamp}"
    backup_target = quarantine / TARGET_REL
    backup_service = quarantine / SERVICE_REL
    backup_target.parent.mkdir(parents=True, exist_ok=True)
    backup_service.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup_target)
    if service.exists():
        shutil.copy2(service, backup_service)

    start_def_idx = fn.lineno - 1
    end_idx = fn.end_lineno
    decorator_start = min([d.lineno for d in fn.decorator_list], default=fn.lineno) - 1
    decorator_lines = lines[decorator_start:start_def_idx]
    original_def_lines = lines[start_def_idx:end_idx]

    # Validate one-line signature; this project uses one-line route/helper defs for target.
    if not original_def_lines or not original_def_lines[0].lstrip().startswith("def "):
        return {"routes_changed": False, "patched_functions": [], "backup": str(backup_target), "skipped": [], "error": "unexpected_function_signature", "rolled_back": False}

    legacy_def_lines = original_def_lines[:]
    legacy_def_lines[0] = legacy_def_lines[0].replace(f"def {TARGET_NAME}(", f"def {LEGACY_NAME}(", 1)

    indent = " " * 4
    def_line = original_def_lines[0]
    delegated_def_lines = [
        def_line,
        f"{indent}from app.api.mobile.services.performance_summary_service import {DELEGATE_NAME}\n",
        f"{indent}return {DELEGATE_NAME}({fn_args})\n",
    ]

    replacement = []
    replacement.extend(legacy_def_lines)
    if replacement and not replacement[-1].endswith("\n"):
        replacement[-1] += "\n"
    replacement.append("\n")
    replacement.extend(decorator_lines)
    replacement.extend(delegated_def_lines)

    new_lines = lines[:decorator_start] + replacement + lines[end_idx:]
    new_text = "".join(new_lines)
    write_text(target, new_text)

    target_compile = compile_file(target)
    service_compile = compile_file(service)
    if not (target_compile.get("ok") and service_compile.get("ok")):
        shutil.copy2(backup_target, target)
        if backup_service.exists():
            shutil.copy2(backup_service, service)
        return {
            "routes_changed": False,
            "patched_functions": [],
            "backup": str(backup_target),
            "error": "target_or_service_compile_failed",
            "rolled_back": True,
            "target_compile": {"routes": target_compile, "service": service_compile},
            "service": service_result,
        }

    return {
        "routes_changed": True,
        "patched_functions": [TARGET_NAME],
        "backup": str(backup_target),
        "error": "",
        "rolled_back": False,
        "target_compile": {"routes": target_compile, "service": service_compile},
        "service": service_result,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    a = report.get("audit", {})
    f = a.get("function", {})
    ap = report.get("apply", {})
    h = report.get("health_summary", {})
    return f"""# BYS360 Mobile Performance Development Delegate P2.6 {VERSION}

Bu rapor tek ve güvenli okuma endpointi olan `{TARGET_NAME}` fonksiyonunun servis delegasyonu sonucunu gösterir.

## Durum
- mode: {report.get('mode')}

## Audit
- target_exists: {a.get('target_exists')}
- target_compile: `{a.get('target_compile')}`

| Fonksiyon | Var | Satır | Uzunluk | Route Decorator | Delegated | Legacy | Patchable | Arg |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `{f.get('name')}` | {f.get('exists')} | {f.get('line')} | {f.get('length')} | {f.get('route_decorator')} | {f.get('delegated')} | {f.get('legacy')} | {f.get('patchable')} | `{f.get('arg')}` |

## Apply
- service: `{ap.get('service')}`
- routes_changed: `{ap.get('routes_changed')}`
- patched_functions: `{ap.get('patched_functions')}`
- backup: `{ap.get('backup', '')}`
- error: `{ap.get('error', '')}`
- rolled_back: `{ap.get('rolled_back', '')}`
- target_compile: `{ap.get('target_compile', '')}`

## Sağlık Kontrolü
- compileall_ok: {h.get('compileall_ok')}
- app_factory_ok: {h.get('app_factory_ok')}
- overall_ok: {h.get('overall_ok')}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "all"], default="all")
    ns = parser.parse_args()
    root = Path(ns.project_root).resolve()

    report: Dict[str, Any] = {"version": VERSION, "mode": ns.mode, "project_root": str(root)}
    report["audit"] = audit(root)
    report["apply"] = {}
    report["health_summary"] = {}

    exit_code = 0
    if ns.mode == "all":
        report["apply"] = patch_target(root)
        report["health_summary"] = health(root)
        if not report["health_summary"].get("overall_ok"):
            exit_code = 1
        if report["apply"].get("rolled_back"):
            exit_code = 1
    
    report_json = root / REPORT_JSON_REL
    report_md = root / REPORT_MD_REL
    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))
    write_text(report_md, render_markdown(report))

    print(json.dumps({
        "version": VERSION,
        "mode": ns.mode,
        "audit": report.get("audit"),
        "apply": report.get("apply"),
        "health_summary": {k: v for k, v in report.get("health_summary", {}).items() if k in ("compileall_ok", "app_factory_ok", "overall_ok")},
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_DEVELOPMENT_DELEGATE_P2_6_V2_17_31_REPORT_OK")
    if ns.mode == "all" and report.get("health_summary", {}).get("overall_ok") and not report.get("apply", {}).get("rolled_back"):
        print("BYS360_MOBILE_PERFORMANCE_DEVELOPMENT_DELEGATE_P2_6_V2_17_31_HEALTH_OK")
        print("BYS360_MOBILE_PERFORMANCE_DEVELOPMENT_DELEGATE_P2_6_V2_17_31_APPLY_OK")
    print("BYS360_MOBILE_PERFORMANCE_DEVELOPMENT_DELEGATE_P2_6_V2_17_31_OK")
    print("Rapor dosyalari:")
    print(f"- {REPORT_MD_REL}")
    print(f"- {REPORT_JSON_REL}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
