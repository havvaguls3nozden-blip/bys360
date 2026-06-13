# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Full Summary Delegate P2.2 V2.17.26

Kapsam:
- app/api/mobile/performance_routes.py icindeki mobile_performance_full_feature_summary fonksiyonunu
  URL/endpoint/blueprint adini degistirmeden servis delegasyonuna alir.
- Eski govde _bys360_legacy_mobile_performance_full_feature_summary olarak korunur.
- Islem okuma/ozet endpointi ile sinirlidir; puan gonderme, onay, iade, not olusturma gibi yazma islemlerine dokunmaz.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

VERSION = "V2.17.26"
TARGET_FUNC = "mobile_performance_full_feature_summary"
LEGACY_FUNC = f"_bys360_legacy_{TARGET_FUNC}"
SERVICE_FUNC = "delegate_mobile_performance_full_feature_summary"
TARGET_REL = Path("app/api/mobile/performance_routes.py")
SERVICE_REL = Path("app/api/mobile/services/performance_summary_service.py")
REPORT_JSON_REL = Path("reports/quality/bys360_mobile_performance_full_summary_delegate_p2_2_v2_17_26_report.json")
REPORT_MD_REL = Path("reports/quality/bys360_mobile_performance_full_summary_delegate_p2_2_v2_17_26_report.md")


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_module(text: str) -> ast.Module:
    return ast.parse(text)


def find_func(tree: ast.Module, name: str) -> Optional[ast.FunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node  # type: ignore[return-value]
    return None


def function_args_call(node: ast.FunctionDef) -> str:
    parts: List[str] = []
    for a in node.args.posonlyargs + node.args.args:
        parts.append(a.arg)
    if node.args.vararg:
        parts.append("*" + node.args.vararg.arg)
    for a in node.args.kwonlyargs:
        parts.append(f"{a.arg}={a.arg}")
    if node.args.kwarg:
        parts.append("**" + node.args.kwarg.arg)
    return ", ".join(parts)


def compile_file(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "file not found"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:  # noqa: BLE001
        return {"exists": True, "ok": False, "error": str(exc)}


def run_cmd(args: List[str], cwd: Path, timeout: int = 90) -> Dict[str, object]:
    try:
        p = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout_tail": p.stdout[-5000:],
            "stderr_tail": p.stderr[-5000:],
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(exc)}


def health(project_root: Path) -> Dict[str, object]:
    compileall = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], project_root, timeout=180)
    app_factory = run_cmd(
        [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"],
        project_root,
        timeout=120,
    )
    return {
        "compileall_ok": bool(compileall.get("ok")),
        "app_factory_ok": bool(app_factory.get("ok")),
        "overall_ok": bool(compileall.get("ok")) and bool(app_factory.get("ok")),
        "compileall": compileall,
        "app_factory": app_factory,
    }


def inspect_target(project_root: Path) -> Dict[str, object]:
    target = project_root / TARGET_REL
    service = project_root / SERVICE_REL
    info: Dict[str, object] = {
        "target_exists": target.exists(),
        "service_exists": service.exists(),
        "target_path": str(TARGET_REL).replace("\\", "/"),
        "service_path": str(SERVICE_REL).replace("\\", "/"),
        "target_func": TARGET_FUNC,
        "legacy_func": LEGACY_FUNC,
        "service_func": SERVICE_FUNC,
    }
    if not target.exists():
        info.update({"syntax_ok": False, "patchable": False, "error": "target file not found"})
        return info
    text = read_text(target)
    info["size_kb"] = round(len(text.encode("utf-8")) / 1024, 1)
    info["line_count"] = text.count("\n") + 1
    try:
        tree = parse_module(text)
        info["syntax_ok"] = True
        info["syntax_error"] = ""
    except SyntaxError as exc:
        info.update({"syntax_ok": False, "syntax_error": str(exc), "patchable": False})
        return info
    fn = find_func(tree, TARGET_FUNC)
    legacy = find_func(tree, LEGACY_FUNC)
    info["target_found"] = fn is not None
    info["legacy_exists"] = legacy is not None
    if fn is not None:
        segment = "\n".join(text.splitlines()[fn.lineno - 1 : getattr(fn, "end_lineno", fn.lineno)])
        info["target_line"] = fn.lineno
        info["target_end_line"] = getattr(fn, "end_lineno", fn.lineno)
        info["target_length"] = getattr(fn, "end_lineno", fn.lineno) - fn.lineno + 1
        info["delegated"] = SERVICE_FUNC in segment or "performance_summary_service" in segment
        info["arg"] = function_args_call(fn)
    else:
        info["target_line"] = None
        info["delegated"] = False
        info["arg"] = ""
    service_text = read_text(service) if service.exists() else ""
    info["service_delegate_exists"] = SERVICE_FUNC in service_text
    info["patchable"] = bool(info.get("syntax_ok")) and bool(info.get("target_found")) and not bool(info.get("delegated"))
    return info


def ensure_service(project_root: Path) -> Dict[str, object]:
    service = project_root / SERVICE_REL
    if service.exists():
        text = read_text(service)
    else:
        text = "# -*- coding: utf-8 -*-\n\"\"\"BYS360 mobil performans ozet servis delegasyonlari.\"\"\"\n\n"
    changed = False
    if SERVICE_FUNC not in text:
        addition = f'''


def {SERVICE_FUNC}(legacy_func, *args, **kwargs):
    """mobile_performance_full_feature_summary icin guvenli servis delegasyonu."""
    return legacy_func(*args, **kwargs)
'''
        if not text.endswith("\n"):
            text += "\n"
        text += addition
        changed = True
    if changed:
        write_text(service, text)
    return {"path": str(SERVICE_REL).replace("\\", "/"), "changed": changed, "compile": compile_file(service)}


def patch_target(project_root: Path) -> Dict[str, object]:
    target = project_root / TARGET_REL
    text = read_text(target)
    lines = text.splitlines(keepends=True)
    tree = parse_module(text)
    fn = find_func(tree, TARGET_FUNC)
    if fn is None:
        return {"routes_changed": False, "patched_functions": [], "error": "target function not found"}
    segment_text = "".join(lines[fn.lineno - 1 : getattr(fn, "end_lineno", fn.lineno)])
    if SERVICE_FUNC in segment_text or "performance_summary_service" in segment_text:
        return {"routes_changed": False, "patched_functions": [], "already_delegated": True, "error": ""}
    if find_func(tree, LEGACY_FUNC) is not None:
        return {"routes_changed": False, "patched_functions": [], "error": "legacy function already exists but target is not delegated"}

    # Dekoratorleri ve def govdesini ayir.
    start_idx = fn.lineno - 1
    end_idx = getattr(fn, "end_lineno", fn.lineno)
    original_lines = lines[start_idx:end_idx]
    def_idx_rel = 0
    for i, line in enumerate(original_lines):
        if line.lstrip().startswith("def ") or line.lstrip().startswith("async def "):
            def_idx_rel = i
            break
    decorator_lines = original_lines[:def_idx_rel]
    def_and_body = original_lines[def_idx_rel:]
    def_line = def_and_body[0]
    base_indent = def_line[: len(def_line) - len(def_line.lstrip())]
    body_indent = base_indent + "    "

    legacy_lines = []
    legacy_def_line = def_line.replace(f"def {TARGET_FUNC}", f"def {LEGACY_FUNC}", 1)
    legacy_def_line = legacy_def_line.replace(f"async def {TARGET_FUNC}", f"async def {LEGACY_FUNC}", 1)
    legacy_lines.append(legacy_def_line)
    legacy_lines.extend(def_and_body[1:])

    call_args = function_args_call(fn)
    call_suffix = (", " + call_args) if call_args else ""
    public_lines = []
    public_lines.extend(decorator_lines)
    public_lines.append(def_line)
    public_lines.append(f"{body_indent}from app.api.mobile.services.performance_summary_service import {SERVICE_FUNC} as _bys360_delegate\n")
    public_lines.append(f"{body_indent}return _bys360_delegate({LEGACY_FUNC}{call_suffix})\n")

    replacement = legacy_lines + ["\n"] + public_lines
    new_lines = lines[:start_idx] + replacement + lines[end_idx:]
    new_text = "".join(new_lines)

    # Backup
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine_root = project_root / "_local_quarantine" / f"bys360_mobile_performance_full_summary_delegate_p2_2_{stamp}"
    backup_path = quarantine_root / TARGET_REL
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup_path)

    write_text(target, new_text)
    route_compile = compile_file(target)
    if not route_compile.get("ok"):
        shutil.copy2(backup_path, target)
        return {
            "routes_changed": False,
            "patched_functions": [],
            "backup": str(backup_path.relative_to(project_root)).replace("\\", "/") if backup_path.is_relative_to(project_root) else str(backup_path),
            "error": "route compile failed; rolled back: " + str(route_compile.get("error")),
            "target_compile": route_compile,
            "rolled_back": True,
        }
    return {
        "routes_changed": True,
        "patched_functions": [TARGET_FUNC],
        "backup": str(backup_path.relative_to(project_root)).replace("\\", "/") if backup_path.is_relative_to(project_root) else str(backup_path),
        "error": "",
        "target_compile": route_compile,
        "rolled_back": False,
    }


def write_report(project_root: Path, report: Dict[str, object]) -> None:
    json_path = project_root / REPORT_JSON_REL
    md_path = project_root / REPORT_MD_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))
    audit = report.get("audit", {}) if isinstance(report.get("audit"), dict) else {}
    apply = report.get("apply", {}) if isinstance(report.get("apply"), dict) else {}
    health_summary = report.get("health_summary", {}) if isinstance(report.get("health_summary"), dict) else {}
    service = apply.get("service", {}) if isinstance(apply.get("service"), dict) else {}
    routes = apply.get("routes", {}) if isinstance(apply.get("routes"), dict) else {}
    md = f"""# BYS360 Mobile Performance Full Summary Delegate P2.2 V2.17.26

Bu rapor mobil performans tam özellik özeti endpointinin URL, endpoint ve blueprint adı korunarak servis delegasyonuna alınma sonucunu gösterir.

## Durum
- mode: {report.get('mode')}

## Audit
- target_exists: {audit.get('target_exists')}
- target_line: {audit.get('target_line')}
- target_length: {audit.get('target_length')}
- delegated: {audit.get('delegated')}
- legacy_exists: {audit.get('legacy_exists')}
- patchable: {audit.get('patchable')}
- arg: `{audit.get('arg')}`

## Apply
- service: `{service}`
- routes_changed: {routes.get('routes_changed')}
- patched_functions: {routes.get('patched_functions')}
- backup: {routes.get('backup', '')}
- error: {routes.get('error', '')}
- rolled_back: {routes.get('rolled_back', False)}

## Sağlık Kontrolü
- compileall_ok: {health_summary.get('compileall_ok')}
- app_factory_ok: {health_summary.get('app_factory_ok')}
- overall_ok: {health_summary.get('overall_ok')}
"""
    write_text(md_path, md)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "apply", "health", "all"], default="all")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    report: Dict[str, object] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(project_root),
        "audit": {},
        "apply": {},
        "health_summary": {},
        "json_report": str(REPORT_JSON_REL).replace("\\", "/"),
        "md_report": str(REPORT_MD_REL).replace("\\", "/"),
    }

    exit_code = 0
    if args.mode in ("audit", "apply", "all"):
        report["audit"] = inspect_target(project_root)

    if args.mode in ("apply", "all"):
        audit = report["audit"] if isinstance(report["audit"], dict) else {}
        if not audit.get("patchable"):
            report["apply"] = {
                "service": {},
                "routes": {"routes_changed": False, "patched_functions": [], "error": "not patchable or already delegated"},
                "skipped": True,
            }
        else:
            service_res = ensure_service(project_root)
            routes_res = patch_target(project_root)
            report["apply"] = {"service": service_res, "routes": routes_res}

    if args.mode in ("health", "all"):
        report["health_summary"] = health(project_root)
        if not (isinstance(report["health_summary"], dict) and report["health_summary"].get("overall_ok")):
            exit_code = 1

    write_report(project_root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "audit": report.get("audit"),
        "apply": report.get("apply"),
        "health_summary": report.get("health_summary"),
        "json_report": report.get("json_report"),
        "md_report": report.get("md_report"),
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_FULL_SUMMARY_DELEGATE_P2_2_V2_17_26_REPORT_OK")
    if args.mode in ("health", "all") and exit_code == 0:
        print("BYS360_MOBILE_PERFORMANCE_FULL_SUMMARY_DELEGATE_P2_2_V2_17_26_HEALTH_OK")
    if args.mode in ("apply", "all"):
        apply = report.get("apply", {})
        routes = apply.get("routes", {}) if isinstance(apply, dict) else {}
        if isinstance(routes, dict) and routes.get("routes_changed"):
            print("BYS360_MOBILE_PERFORMANCE_FULL_SUMMARY_DELEGATE_P2_2_V2_17_26_APPLY_OK")
        else:
            print("BYS360_MOBILE_PERFORMANCE_FULL_SUMMARY_DELEGATE_P2_2_V2_17_26_APPLY_NOOP")
    print("BYS360_MOBILE_PERFORMANCE_FULL_SUMMARY_DELEGATE_P2_2_V2_17_26_OK")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
