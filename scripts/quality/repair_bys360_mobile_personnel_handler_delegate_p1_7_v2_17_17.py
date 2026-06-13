# -*- coding: utf-8 -*-
"""BYS360 Mobile Personnel Handler Delegate P1.7 V2.17.17

Safe AST/text based delegation for selected mobile personnel handlers.
Keeps URL, endpoint and blueprint decorators intact. Old implementation is
kept as _bys360_legacy_<function> and the public function delegates to
app.api.mobile.services.personnel_service.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "V2.17.17"
SLUG = "bys360_mobile_personnel_handler_delegate_p1_7_v2_17_17"
TARGET_FUNCTIONS = [
    "mobile_personnel_all",
    "mobile_personnel_create",
    "_mobile_created_personnel_row",
]


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def parse_functions(path: Path) -> Tuple[Optional[ast.Module], str]:
    try:
        tree = ast.parse(read_text(path))
        return tree, ""
    except SyntaxError as e:
        return None, f"{e.filename}:{e.lineno}:{e.offset}: {e.msg}"
    except Exception as e:
        return None, repr(e)


def find_candidates(root: Path) -> Dict[str, Any]:
    routes = root / "app" / "api" / "mobile" / "routes.py"
    service = root / "app" / "api" / "mobile" / "services" / "personnel_service.py"
    result: Dict[str, Any] = {
        "exists": routes.exists(),
        "path": rel(root, routes),
        "service_path": rel(root, service),
        "size_kb": round(routes.stat().st_size / 1024, 1) if routes.exists() else 0,
        "line_count": 0,
        "syntax_ok": False,
        "syntax_error": "",
        "candidate_count": 0,
        "delegated_count": 0,
        "patchable_count": 0,
        "functions": [],
    }
    if not routes.exists():
        return result
    text = read_text(routes)
    lines = text.splitlines()
    result["line_count"] = len(lines)
    tree, err = parse_functions(routes)
    result["syntax_ok"] = tree is not None
    result["syntax_error"] = err
    if tree is None:
        return result
    by_name = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for name in TARGET_FUNCTIONS:
        node = by_name.get(name)
        legacy_name = f"_bys360_legacy_{name}"
        legacy = legacy_name in by_name
        delegated = False
        line = None
        end_line = None
        route_decorator = False
        arg = ""
        if node:
            line = node.lineno
            end_line = getattr(node, "end_lineno", node.lineno)
            route_decorator = any("route" in ast.unparse(d) if hasattr(ast, "unparse") else True for d in node.decorator_list)
            try:
                arg = ", ".join([a.arg for a in node.args.args])
                if node.args.vararg:
                    arg += (", " if arg else "") + "*" + node.args.vararg.arg
                if node.args.kwarg:
                    arg += (", " if arg else "") + "**" + node.args.kwarg.arg
            except Exception:
                arg = ""
            seg = "\n".join(lines[max(0, node.lineno - 1): min(len(lines), (getattr(node, "end_lineno", node.lineno)))])
            delegated = "personnel_service" in seg and legacy
        result["functions"].append({
            "name": name,
            "exists": bool(node),
            "line": line,
            "end_line": end_line,
            "route_decorator": route_decorator,
            "delegated": delegated,
            "legacy": legacy,
            "arg": arg,
            "patchable": bool(node) and not delegated and not legacy,
        })
    result["candidate_count"] = sum(1 for f in result["functions"] if f["exists"])
    result["delegated_count"] = sum(1 for f in result["functions"] if f["delegated"])
    result["patchable_count"] = sum(1 for f in result["functions"] if f["patchable"])
    return result


def get_arg_call(node: ast.FunctionDef) -> str:
    args: List[str] = []
    # positional args
    for a in getattr(node.args, "posonlyargs", []) + node.args.args:
        args.append(a.arg)
    # vararg
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    # keyword-only args
    for a in node.args.kwonlyargs:
        args.append(f"{a.arg}={a.arg}")
    # kwarg
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return ", ".join(args)


def patch_one(text: str, func_name: str) -> Tuple[str, Dict[str, Any]]:
    tree = ast.parse(text)
    lines = text.splitlines()
    node = None
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func_name:
            node = n
            break
    if node is None:
        return text, {"name": func_name, "changed": False, "reason": "not_found"}
    legacy_name = f"_bys360_legacy_{func_name}"
    if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == legacy_name for n in tree.body):
        return text, {"name": func_name, "changed": False, "reason": "legacy_exists"}
    if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func_name and "personnel_service" in ast.get_source_segment(text, n) for n in tree.body):
        return text, {"name": func_name, "changed": False, "reason": "already_delegated"}

    def_line_idx = node.lineno - 1
    end_idx = getattr(node, "end_lineno", node.lineno)  # exclusive for list slice
    dec_start_idx = def_line_idx
    if node.decorator_list:
        dec_start_idx = min(d.lineno for d in node.decorator_list) - 1
    decorators = lines[dec_start_idx:def_line_idx]
    original_def = lines[def_line_idx]
    original_body = lines[def_line_idx + 1:end_idx]
    legacy_def = re.sub(r"(def\s+)" + re.escape(func_name) + r"(\s*\()", r"\1" + legacy_name + r"\2", original_def, count=1)
    if legacy_def == original_def and original_def.lstrip().startswith("async def"):
        legacy_def = re.sub(r"(async\s+def\s+)" + re.escape(func_name) + r"(\s*\()", r"\1" + legacy_name + r"\2", original_def, count=1)
    indent = re.match(r"^(\s*)", original_def).group(1)
    body_indent = indent + "    "
    arg_call = get_arg_call(node)
    wrapper = []
    wrapper.extend(decorators)
    wrapper.append(original_def)
    wrapper.append(body_indent + "from app.api.mobile.services import personnel_service as _bys360_personnel_service")
    wrapper.append(body_indent + f"return _bys360_personnel_service.{func_name}({arg_call})")
    legacy = [legacy_def] + original_body
    new_block = ["", "# BYS360 P1.7 service delegation - legacy implementation preserved"] + legacy + [""] + wrapper
    new_lines = lines[:dec_start_idx] + new_block + lines[end_idx:]
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else ""), {"name": func_name, "changed": True, "legacy": legacy_name}


def ensure_service(root: Path, funcs: List[str]) -> Dict[str, Any]:
    service = root / "app" / "api" / "mobile" / "services" / "personnel_service.py"
    service.parent.mkdir(parents=True, exist_ok=True)
    if service.exists():
        text = read_text(service)
    else:
        text = '# -*- coding: utf-8 -*-\n"""BYS360 mobile personnel service delegation layer."""\n\n'
    changed = False
    if "def _routes_module" not in text:
        text += "\n\ndef _routes_module():\n    from app.api.mobile import routes as _mobile_routes\n    return _mobile_routes\n"
        changed = True
    for name in funcs:
        if re.search(r"^def\s+" + re.escape(name) + r"\s*\(", text, re.M):
            continue
        legacy_name = f"_bys360_legacy_{name}"
        text += f"\n\ndef {name}(*args, **kwargs):\n    return getattr(_routes_module(), '{legacy_name}')(*args, **kwargs)\n"
        changed = True
    if changed:
        write_text(service, text)
    return {"path": rel(root, service), "changed": changed, "delegate_count": len(funcs)}


def run_cmd(root: Path, cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
    try:
        p = subprocess.run(cmd, cwd=str(root), text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
        return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout_tail": p.stdout[-3000:], "stderr_tail": p.stderr[-3000:]}
    except Exception as e:
        return {"ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": repr(e)}


def health(root: Path) -> Dict[str, Any]:
    comp = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], 180)
    factory = run_cmd(root, [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], 180)
    return {"compileall_ok": bool(comp["ok"]), "app_factory_ok": bool(factory["ok"]), "overall_ok": bool(comp["ok"] and factory["ok"]), "compileall": comp, "app_factory": factory}


def make_report_md(report: Dict[str, Any]) -> str:
    audit = report.get("audit", {})
    apply = report.get("apply", {})
    h = report.get("health_summary", {})
    lines = [f"# BYS360 Mobile Personnel Handler Delegate P1.7 {VERSION}", "", "Bu rapor mobil personel fonksiyonlarının servis delegasyonu sonucunu gösterir.", "", "## Durum", f"- mode: {report.get('mode')}", "", "## Audit", f"- candidate_count: {audit.get('candidate_count')}", f"- delegated_count: {audit.get('delegated_count')}", f"- patchable_count: {audit.get('patchable_count')}", "", "| Fonksiyon | Satır | Route Decorator | Delegated | Legacy | Arg |", "|---|---:|---:|---:|---:|---|"]
    for f in audit.get("functions", []):
        lines.append(f"| `{f.get('name')}` | {f.get('line')} | {f.get('route_decorator')} | {f.get('delegated')} | {f.get('legacy')} | `{f.get('arg')}` |")
    lines += ["", "## Apply", f"- service: `{apply.get('service')}`", f"- patched_functions: {apply.get('patched_functions')}", f"- skipped: {apply.get('skipped')}", f"- backup: {apply.get('backup', '')}", f"- error: {apply.get('error', '')}", "", "## Sağlık Kontrolü", f"- compileall_ok: {h.get('compileall_ok')}", f"- app_factory_ok: {h.get('app_factory_ok')}", f"- overall_ok: {h.get('overall_ok')}"]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "all"], default="audit")
    ns = ap.parse_args()
    root = Path(ns.project_root).resolve()
    routes = root / "app" / "api" / "mobile" / "routes.py"
    report: Dict[str, Any] = {"version": VERSION, "mode": ns.mode, "project_root": str(root)}
    audit = find_candidates(root)
    report["audit"] = audit
    report["apply"] = {}
    report["health_summary"] = {}
    ok = True
    if ns.mode in ("apply", "all"):
        quarantine = root / "_local_quarantine" / ("bys360_mobile_personnel_handler_delegate_p1_7_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        apply: Dict[str, Any] = {"service": None, "patched_functions": [], "skipped": [], "backup": "", "error": ""}
        try:
            patchable = [f["name"] for f in audit.get("functions", []) if f.get("patchable")]
            if patchable:
                backup = quarantine / "app" / "api" / "mobile" / "routes.py.before_p1_7"
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(routes, backup)
                apply["backup"] = rel(root, backup)
                text = read_text(routes)
                patched = []
                skipped = []
                for name in patchable:
                    try:
                        text, info = patch_one(text, name)
                        if info.get("changed"):
                            patched.append(name)
                        else:
                            skipped.append(info)
                    except Exception as e:
                        skipped.append({"name": name, "reason": repr(e)})
                if patched:
                    write_text(routes, text)
                    apply["service"] = ensure_service(root, patched)
                    apply["patched_functions"] = patched
                apply["skipped"] = skipped
            else:
                apply["skipped"] = [{"reason": "no_patchable_functions"}]
        except Exception as e:
            apply["error"] = repr(e)
            ok = False
        report["apply"] = apply
    if ns.mode in ("apply", "all"):
        h = health(root)
        report["health_summary"] = {k: h[k] for k in ("compileall_ok", "app_factory_ok", "overall_ok")}
        report["health_detail"] = h
        if not h["overall_ok"]:
            # rollback if we made a backup
            b = report.get("apply", {}).get("backup")
            if b:
                try:
                    shutil.copy2(root / b, routes)
                    report["apply"]["rollback"] = True
                except Exception as e:
                    report["apply"]["rollback_error"] = repr(e)
            ok = False
    reports_dir = root / "reports" / "quality"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / f"{SLUG}_report.json"
    md_path = reports_dir / f"{SLUG}_report.md"
    report["json_report"] = rel(root, json_path)
    report["md_report"] = rel(root, md_path)
    write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))
    write_text(md_path, make_report_md(report))
    print(json.dumps({k: report[k] for k in ["version", "mode", "audit", "apply", "health_summary", "json_report", "md_report"] if k in report}, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERSONNEL_HANDLER_DELEGATE_P1_7_V2_17_17_REPORT_OK")
    if ns.mode in ("apply", "all"):
        if ok:
            print("BYS360_MOBILE_PERSONNEL_HANDLER_DELEGATE_P1_7_V2_17_17_HEALTH_OK")
            if report.get("apply", {}).get("patched_functions"):
                print("BYS360_MOBILE_PERSONNEL_HANDLER_DELEGATE_P1_7_V2_17_17_APPLY_OK")
            else:
                print("BYS360_MOBILE_PERSONNEL_HANDLER_DELEGATE_P1_7_V2_17_17_APPLY_NOOP")
        else:
            print("BYS360_MOBILE_PERSONNEL_HANDLER_DELEGATE_P1_7_V2_17_17_APPLY_FAIL")
            return 1
    print("BYS360_MOBILE_PERSONNEL_HANDLER_DELEGATE_P1_7_V2_17_17_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
