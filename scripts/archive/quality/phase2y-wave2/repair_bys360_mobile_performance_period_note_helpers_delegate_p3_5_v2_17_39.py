# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Period Note Helpers Delegate P3.5 V2.17.39

This script delegates only small in-period note helper functions from
app/api/mobile/performance_routes.py to app/api/mobile/services/performance_period_service.py.
It does not call real POST endpoints and does not change URL/endpoint/blueprint names.
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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

VERSION = "V2.17.39"
PATCH_MARKER = "BYS360_MOBILE_PERFORMANCE_PERIOD_NOTE_HELPERS_DELEGATE_P3_5_V2_17_39"
TARGET_REL = Path("app/api/mobile/performance_routes.py")
SERVICE_REL = Path("app/api/mobile/services/performance_period_service.py")
REPORT_JSON_REL = Path("reports/quality/bys360_mobile_performance_period_note_helpers_delegate_p3_5_v2_17_39_report.json")
REPORT_MD_REL = Path("reports/quality/bys360_mobile_performance_period_note_helpers_delegate_p3_5_v2_17_39_report.md")
TARGETS = ["_v2853_note_type_label", "_v2853_note_bool"]


@dataclass
class FunctionInfo:
    name: str
    exists: bool = False
    line: int = 0
    end_line: int = 0
    length: int = 0
    route_decorator: bool = False
    delegated: bool = False
    legacy: bool = False
    patchable: bool = False
    arg: str = ""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def compile_file(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": str(exc)}


def run_cmd(args: List[str], cwd: Path, timeout: int = 120) -> Dict[str, object]:
    try:
        proc = subprocess.run(
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
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
        }
    except Exception as exc:
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


def parse_module(path: Path) -> Tuple[ast.Module | None, str, str]:
    if not path.exists():
        return None, "", "missing"
    text = read_text(path)
    try:
        return ast.parse(text), text, ""
    except Exception as exc:
        return None, text, str(exc)


def legacy_name(name: str) -> str:
    return f"_bys360_legacy_{name}"


def get_functions(tree: ast.Module | None) -> Dict[str, ast.FunctionDef]:
    if tree is None:
        return {}
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def get_arg_display(fn: ast.FunctionDef) -> str:
    names: List[str] = []
    for arg in getattr(fn.args, "posonlyargs", []) + fn.args.args:
        names.append(arg.arg)
    if fn.args.vararg:
        names.append("*" + fn.args.vararg.arg)
    for arg in fn.args.kwonlyargs:
        names.append(arg.arg)
    if fn.args.kwarg:
        names.append("**" + fn.args.kwarg.arg)
    return ", ".join(names)


def get_call_args(fn: ast.FunctionDef) -> str:
    parts: List[str] = []
    for arg in getattr(fn.args, "posonlyargs", []) + fn.args.args:
        parts.append(arg.arg)
    if fn.args.vararg:
        parts.append("*" + fn.args.vararg.arg)
    for arg in fn.args.kwonlyargs:
        parts.append(f"{arg.arg}={arg.arg}")
    if fn.args.kwarg:
        parts.append("**" + fn.args.kwarg.arg)
    return ", ".join(parts)


def has_route_decorator(fn: ast.FunctionDef) -> bool:
    for dec in fn.decorator_list:
        txt = ast.unparse(dec) if hasattr(ast, "unparse") else ""
        if ".route" in txt or "route(" in txt:
            return True
    return False


def is_delegated(fn: ast.FunctionDef) -> bool:
    try:
        body_text = "\n".join(ast.unparse(stmt) for stmt in fn.body)
    except Exception:
        body_text = ""
    return "performance_period_service" in body_text or "_bys360_performance_period_service" in body_text


def audit(project_root: Path) -> Dict[str, object]:
    target = project_root / TARGET_REL
    service = project_root / SERVICE_REL
    tree, _text, parse_error = parse_module(target)
    funcs = get_functions(tree)
    infos: List[Dict[str, object]] = []
    for name in TARGETS:
        fn = funcs.get(name)
        legacy_fn = funcs.get(legacy_name(name))
        info = FunctionInfo(name=name)
        if fn:
            info.exists = True
            info.line = int(getattr(fn, "lineno", 0) or 0)
            info.end_line = int(getattr(fn, "end_lineno", info.line) or info.line)
            info.length = max(0, info.end_line - info.line + 1)
            info.route_decorator = has_route_decorator(fn)
            info.delegated = is_delegated(fn)
            info.legacy = bool(legacy_fn)
            info.patchable = (not info.delegated) and (not info.legacy)
            info.arg = get_arg_display(fn)
        infos.append(info.__dict__)
    return {
        "target_exists": target.exists(),
        "target_path": str(TARGET_REL),
        "target_compile": compile_file(target),
        "service_exists": service.exists(),
        "service_path": str(SERVICE_REL),
        "service_compile": compile_file(service),
        "parse_error": parse_error,
        "candidate_count": len(TARGETS),
        "delegated_count": sum(1 for x in infos if x.get("delegated")),
        "patchable_count": sum(1 for x in infos if x.get("patchable")),
        "functions": infos,
    }


def first_def_line(lines: List[str], start_idx: int) -> str:
    line = lines[start_idx].rstrip("\n")
    if line.lstrip().startswith("def ") and line.rstrip().endswith(":"):
        return line
    raise RuntimeError("multi-line function signature is not supported by this safe patcher")


def make_legacy_source(original: str, name: str) -> str:
    return original.replace(f"def {name}(", f"def {legacy_name(name)}(", 1)


def make_wrapper_source(def_line: str, fn: ast.FunctionDef) -> str:
    name = fn.name
    call_args = get_call_args(fn)
    indent = def_line[: len(def_line) - len(def_line.lstrip())]
    body_indent = indent + "    "
    return (
        f"{def_line}\n"
        f"{body_indent}from app.api.mobile.services import performance_period_service as _bys360_performance_period_service\n"
        f"{body_indent}return _bys360_performance_period_service.{name}({call_args})\n"
    )


def ensure_service_delegates(service: Path, target_names: List[str]) -> bool:
    if service.exists():
        text = read_text(service)
    else:
        text = '"""Mobile performance period service delegates."""\n\n'
    changed = False
    additions: List[str] = []
    for name in target_names:
        if f"def {name}(" in text:
            continue
        additions.append(
            "\n\n"
            f"def {name}(*args, **kwargs):\n"
            f"    from app.api.mobile import performance_routes as _bys360_performance_routes\n"
            f"    return _bys360_performance_routes.{legacy_name(name)}(*args, **kwargs)\n"
        )
        changed = True
    if changed:
        write_text(service, text.rstrip() + "".join(additions) + "\n")
    return changed


def patch_routes(project_root: Path, patch_names: List[str], quarantine_root: Path) -> Dict[str, object]:
    target = project_root / TARGET_REL
    tree, text, parse_error = parse_module(target)
    if parse_error:
        return {"changed": False, "patched_functions": [], "backup": "", "error": parse_error, "rolled_back": False}
    funcs = get_functions(tree)
    lines = text.splitlines(keepends=True)
    replacements: List[Tuple[int, int, str, str]] = []
    for name in patch_names:
        fn = funcs.get(name)
        if not fn or legacy_name(name) in funcs or is_delegated(fn):
            continue
        start = fn.lineno - 1
        end = fn.end_lineno
        original = "".join(lines[start:end])
        def_line = first_def_line(lines, start)
        legacy_source = make_legacy_source(original, name)
        wrapper_source = make_wrapper_source(def_line, fn)
        replacement = legacy_source.rstrip() + "\n\n" + wrapper_source.rstrip() + "\n"
        replacements.append((start, end, replacement, name))
    if not replacements:
        return {"changed": False, "patched_functions": [], "backup": "", "error": "", "rolled_back": False}

    backup = quarantine_root / TARGET_REL
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)

    for start, end, replacement, _name in sorted(replacements, key=lambda x: x[0], reverse=True):
        lines[start:end] = [replacement]
    write_text(target, "".join(lines))

    compile_result = compile_file(target)
    if not compile_result.get("ok"):
        shutil.copy2(backup, target)
        return {
            "changed": False,
            "patched_functions": [],
            "backup": str(backup),
            "error": str(compile_result.get("error")),
            "rolled_back": True,
        }
    return {
        "changed": True,
        "patched_functions": [x[3] for x in replacements],
        "backup": str(backup),
        "error": "",
        "rolled_back": False,
    }


def apply(project_root: Path) -> Dict[str, object]:
    audit_before = audit(project_root)
    patch_names = [x["name"] for x in audit_before["functions"] if x.get("patchable")]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine_root = project_root / "_local_quarantine" / f"bys360_mobile_performance_period_note_helpers_delegate_p3_5_{stamp}"
    quarantine_root.mkdir(parents=True, exist_ok=True)

    service = project_root / SERVICE_REL
    service_changed = ensure_service_delegates(service, patch_names)
    service_compile = compile_file(service)
    if not service_compile.get("ok"):
        return {
            "service": {"path": str(SERVICE_REL), "changed": service_changed, "compile": service_compile},
            "routes": {"changed": False, "patched_functions": [], "backup": "", "error": "service compile failed", "rolled_back": False},
            "quarantine_root": str(quarantine_root),
        }

    routes_apply = patch_routes(project_root, patch_names, quarantine_root)
    target_compile = {
        "routes": compile_file(project_root / TARGET_REL),
        "service": compile_file(project_root / SERVICE_REL),
    }
    h = health(project_root)
    if routes_apply.get("changed") and not h.get("overall_ok"):
        backup_str = routes_apply.get("backup") or ""
        backup_path = Path(backup_str) if backup_str else None
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, project_root / TARGET_REL)
            routes_apply["rolled_back"] = True
            routes_apply["changed"] = False
            routes_apply["error"] = "health failed after patch; restored backup"
            h = health(project_root)
    return {
        "service": {"path": str(SERVICE_REL), "changed": service_changed, "compile": service_compile},
        "routes": routes_apply,
        "target_compile": target_compile,
        "quarantine_root": str(quarantine_root),
        "post_apply_health": h,
    }


def write_report(project_root: Path, result: Dict[str, object]) -> None:
    json_path = project_root / REPORT_JSON_REL
    md_path = project_root / REPORT_MD_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(json_path, json.dumps(result, ensure_ascii=False, indent=2))

    audit_data = result.get("audit", {})
    apply_data = result.get("apply", {})
    health_data = result.get("health_summary", {})
    lines: List[str] = []
    lines.append("# BYS360 Mobile Performance Period Note Helpers Delegate P3.5 V2.17.39\n")
    lines.append("Bu rapor gercek yazma endpointlerine dokunmadan donem ici not helper fonksiyonlarinin servis delegasyonu sonucunu gosterir.\n")
    lines.append("## Durum\n")
    lines.append(f"- mode: {result.get('mode')}\n")
    lines.append("## Audit\n")
    lines.append(f"- candidate_count: {audit_data.get('candidate_count')}\n")
    lines.append(f"- delegated_count: {audit_data.get('delegated_count')}\n")
    lines.append(f"- patchable_count: {audit_data.get('patchable_count')}\n\n")
    lines.append("| Fonksiyon | Var | Satir | Uzunluk | Delegated | Legacy | Patchable | Arg |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|\n")
    for fn in audit_data.get("functions", []):
        lines.append(
            f"| `{fn.get('name')}` | {fn.get('exists')} | {fn.get('line')} | {fn.get('length')} | {fn.get('delegated')} | {fn.get('legacy')} | {fn.get('patchable')} | `{fn.get('arg')}` |\n"
        )
    lines.append("\n## Apply\n")
    if apply_data:
        lines.append(f"- service: `{apply_data.get('service')}`\n")
        routes = apply_data.get("routes", {}) if isinstance(apply_data.get("routes"), dict) else {}
        lines.append(f"- routes_changed: `{routes.get('changed')}`\n")
        lines.append(f"- patched_functions: `{routes.get('patched_functions')}`\n")
        lines.append(f"- backup: `{routes.get('backup')}`\n")
        lines.append(f"- error: `{routes.get('error')}`\n")
        lines.append(f"- rolled_back: `{routes.get('rolled_back')}`\n")
    else:
        lines.append("- apply calistirilmadi.\n")
    lines.append("\n## Saglik Kontrolu\n")
    lines.append(f"- compileall_ok: {health_data.get('compileall_ok')}\n")
    lines.append(f"- app_factory_ok: {health_data.get('app_factory_ok')}\n")
    lines.append(f"- overall_ok: {health_data.get('overall_ok')}\n")
    lines.append("\n## Not\n")
    lines.append("Bu adim gercek POST yazma endpointlerini calistirmaz ve URL/endpoint/blueprint adlarini degistirmez.\n")
    write_text(md_path, "".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "all"], default="audit")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    os.chdir(project_root)
    audit_data = audit(project_root)
    apply_data: Dict[str, object] = {}
    if args.mode == "all":
        apply_data = apply(project_root)
    h = health(project_root) if args.mode == "all" else {}
    if args.mode == "all" and isinstance(apply_data, dict) and apply_data.get("post_apply_health"):
        h = apply_data.get("post_apply_health")  # type: ignore[assignment]
    result: Dict[str, object] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(project_root),
        "audit": audit_data,
        "apply": apply_data,
        "health_summary": h,
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }
    write_report(project_root, result)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "audit": {
            "candidate_count": audit_data.get("candidate_count"),
            "delegated_count": audit_data.get("delegated_count"),
            "patchable_count": audit_data.get("patchable_count"),
        },
        "apply": apply_data,
        "health_summary": {k: h.get(k) for k in ["compileall_ok", "app_factory_ok", "overall_ok"]} if isinstance(h, dict) else {},
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }, ensure_ascii=False, indent=2))
    print(f"{PATCH_MARKER}_REPORT_OK")
    if args.mode == "all":
        if isinstance(h, dict) and h.get("overall_ok"):
            routes = apply_data.get("routes", {}) if isinstance(apply_data.get("routes"), dict) else {}
            if routes.get("changed") and not routes.get("rolled_back"):
                print(f"{PATCH_MARKER}_APPLY_OK")
            elif not routes.get("changed") and not routes.get("error"):
                print(f"{PATCH_MARKER}_APPLY_NOOP")
            else:
                print(f"{PATCH_MARKER}_APPLY_ROLLBACK")
            print(f"{PATCH_MARKER}_HEALTH_OK")
            print(f"{PATCH_MARKER}_OK")
            return 0
        print(f"{PATCH_MARKER}_HEALTH_FAIL")
        return 1
    print(f"{PATCH_MARKER}_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
