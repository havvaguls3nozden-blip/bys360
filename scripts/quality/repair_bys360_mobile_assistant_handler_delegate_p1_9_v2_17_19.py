from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

VERSION = "V2.17.19"
TARGET_FUNC = "mobile_b49_assistant_v2_ask"
LEGACY_FUNC = f"_bys360_legacy_{TARGET_FUNC}"
DELEGATE_FUNC = f"delegate_{TARGET_FUNC}"
ROUTES_REL = Path("app/api/mobile/routes.py")
SERVICE_REL = Path("app/api/mobile/services/assistant_service.py")
REPORT_JSON = Path("reports/quality/bys360_mobile_assistant_handler_delegate_p1_9_v2_17_19_report.json")
REPORT_MD = Path("reports/quality/bys360_mobile_assistant_handler_delegate_p1_9_v2_17_19_report.md")

@dataclass
class FuncInfo:
    name: str
    line: int = 0
    end_line: int = 0
    route_decorator: bool = False
    delegated: bool = False
    legacy: bool = False
    arg: str = ""
    patchable: bool = False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def parse_tree(path: Path) -> ast.Module | None:
    try:
        return ast.parse(read_text(path))
    except SyntaxError:
        return None


def decorator_is_route(d: ast.AST) -> bool:
    s = ast.unparse(d) if hasattr(ast, "unparse") else ""
    return ".route(" in s or s.endswith(".route") or "mobile_bp.route" in s or "bp.route" in s


def arg_names(fn: ast.FunctionDef) -> tuple[str, str]:
    parts: list[str] = []
    call: list[str] = []
    for a in list(fn.args.posonlyargs) + list(fn.args.args):
        parts.append(a.arg)
        call.append(a.arg)
    if fn.args.vararg:
        parts.append("*" + fn.args.vararg.arg)
        call.append("*" + fn.args.vararg.arg)
    for a in fn.args.kwonlyargs:
        parts.append(a.arg)
        call.append(f"{a.arg}={a.arg}")
    if fn.args.kwarg:
        parts.append("**" + fn.args.kwarg.arg)
        call.append("**" + fn.args.kwarg.arg)
    return ", ".join(parts), ", ".join(call)


def analyze_routes(root: Path) -> dict[str, Any]:
    routes = root / ROUTES_REL
    info = FuncInfo(name=TARGET_FUNC)
    exists = routes.exists()
    syntax_ok = False
    syntax_error = ""
    size_kb = 0.0
    line_count = 0
    if exists:
        text = read_text(routes)
        size_kb = round(len(text.encode("utf-8", errors="ignore")) / 1024, 1)
        line_count = len(text.splitlines())
        try:
            tree = ast.parse(text)
            syntax_ok = True
            legacy_exists = any(isinstance(n, ast.FunctionDef) and n.name == LEGACY_FUNC for n in tree.body)
            for n in tree.body:
                if isinstance(n, ast.FunctionDef) and n.name == TARGET_FUNC:
                    info.line = n.lineno
                    info.end_line = getattr(n, "end_lineno", n.lineno)
                    info.route_decorator = any(decorator_is_route(d) for d in n.decorator_list)
                    src = "\n".join(text.splitlines()[n.lineno-1:info.end_line])
                    info.delegated = DELEGATE_FUNC in src or "assistant_service" in src
                    info.legacy = legacy_exists
                    info.arg = arg_names(n)[0]
                    info.patchable = (not info.delegated) and (not legacy_exists)
                    break
        except SyntaxError as e:
            syntax_error = f"{e.filename}:{e.lineno}:{e.msg}"
    return {
        "exists": exists,
        "path": str(ROUTES_REL),
        "size_kb": size_kb,
        "line_count": line_count,
        "syntax_ok": syntax_ok,
        "syntax_error": syntax_error,
        "candidate_count": 1 if info.line else 0,
        "delegated_count": 1 if info.delegated else 0,
        "patchable_count": 1 if info.patchable else 0,
        "functions": [asdict(info)] if info.line else [],
    }


def target_compile(root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, rel in [("routes", ROUTES_REL), ("assistant_service", SERVICE_REL)]:
        p = root / rel
        item = {"exists": p.exists(), "ok": False, "error": ""}
        if p.exists():
            try:
                py_compile.compile(str(p), doraise=True)
                item["ok"] = True
            except Exception as e:
                item["error"] = str(e)
        out[key] = item
    return out


def ensure_service(root: Path) -> dict[str, Any]:
    service = root / SERVICE_REL
    existing = read_text(service) if service.exists() else ""
    if DELEGATE_FUNC in existing:
        return {"path": str(SERVICE_REL), "changed": False, "delegate_count": existing.count("def delegate_")}
    addition = f'''

# P1.9 V2.17.19 - mobil asistan route servis delegasyonu.
def {DELEGATE_FUNC}(*args, **kwargs):
    """Mevcut davranışı koruyarak asistan route işlemini legacy gövdeye devreder."""
    from app.api.mobile import routes as mobile_routes
    legacy = getattr(mobile_routes, "{LEGACY_FUNC}")
    return legacy(*args, **kwargs)
'''
    if not existing.strip():
        existing = '"""BYS360 mobil asistan servis delegasyonlari."""\nfrom __future__ import annotations\n'
    write_text(service, existing.rstrip() + addition)
    return {"path": str(SERVICE_REL), "changed": True, "delegate_count": (existing + addition).count("def delegate_")}


def patch_routes(root: Path) -> dict[str, Any]:
    routes = root / ROUTES_REL
    text = read_text(routes)
    tree = ast.parse(text)
    fn: ast.FunctionDef | None = None
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == TARGET_FUNC:
            fn = n
            break
    if fn is None:
        return {"changed": False, "patched_functions": [], "backup": "", "error": "target_not_found"}
    if any(isinstance(n, ast.FunctionDef) and n.name == LEGACY_FUNC for n in tree.body):
        return {"changed": False, "patched_functions": [], "backup": "", "error": "legacy_already_exists"}
    src = "\n".join(text.splitlines()[fn.lineno-1:getattr(fn, "end_lineno", fn.lineno)])
    if DELEGATE_FUNC in src or "assistant_service" in src:
        return {"changed": False, "patched_functions": [], "backup": "", "error": "already_delegated"}
    lines = text.splitlines()
    deco_start = min([d.lineno for d in fn.decorator_list], default=fn.lineno)
    start_idx = deco_start - 1
    end_idx = getattr(fn, "end_lineno", fn.lineno)
    decorators = lines[start_idx:fn.lineno-1]
    func_lines = lines[fn.lineno-1:end_idx]
    if not func_lines or not func_lines[0].lstrip().startswith("def "):
        return {"changed": False, "patched_functions": [], "backup": "", "error": "unsupported_signature"}
    sig_args, call_args = arg_names(fn)
    public = []
    public.extend(decorators)
    public.append(f"def {TARGET_FUNC}({sig_args}):")
    public.append(f"    from app.api.mobile.services.assistant_service import {DELEGATE_FUNC}")
    if call_args:
        public.append(f"    return {DELEGATE_FUNC}({call_args})")
    else:
        public.append(f"    return {DELEGATE_FUNC}()")
    legacy = func_lines[:]
    legacy[0] = legacy[0].replace(f"def {TARGET_FUNC}", f"def {LEGACY_FUNC}", 1)
    replacement = public + [""] + legacy
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = root / "_local_quarantine" / f"bys360_mobile_assistant_handler_delegate_p1_9_{stamp}" / ROUTES_REL.with_suffix(".py.before_p1_9")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(routes, backup)
    new_lines = lines[:start_idx] + replacement + lines[end_idx:]
    write_text(routes, "\n".join(new_lines) + "\n")
    # Quick syntax validation; rollback on failure.
    comp = target_compile(root)
    if not comp["routes"]["ok"]:
        shutil.copy2(backup, routes)
        return {"changed": False, "patched_functions": [], "backup": str(backup.relative_to(root)), "error": comp["routes"]["error"], "rolled_back": True}
    return {"changed": True, "patched_functions": [TARGET_FUNC], "backup": str(backup.relative_to(root)), "error": ""}


def run_cmd(root: Path, cmd: list[str]) -> dict[str, Any]:
    try:
        p = subprocess.run(cmd, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=90)
        return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout_tail": p.stdout[-4000:], "stderr_tail": p.stderr[-4000:]}
    except Exception as e:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(e)}


def health(root: Path) -> dict[str, Any]:
    compileall = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"])
    app_factory = run_cmd(root, [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"])
    return {
        "compileall_ok": compileall["ok"],
        "app_factory_ok": app_factory["ok"],
        "overall_ok": compileall["ok"] and app_factory["ok"],
        "compileall": compileall,
        "app_factory": app_factory,
    }


def write_reports(root: Path, result: dict[str, Any]) -> None:
    json_path = root / REPORT_JSON
    md_path = root / REPORT_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(json_path, json.dumps(result, ensure_ascii=False, indent=2))
    audit = result.get("audit", {})
    apply = result.get("apply", {})
    health_summary = result.get("health_summary", {})
    funcs = audit.get("functions", [])
    rows = []
    for f in funcs:
        rows.append(f"| `{f.get('name')}` | {f.get('line')} | {f.get('route_decorator')} | {f.get('delegated')} | {f.get('legacy')} | `{f.get('arg')}` |")
    md = f"""# BYS360 Mobile Assistant Handler Delegate P1.9 {VERSION}

Bu rapor mobil asistan endpointinin URL, endpoint ve blueprint adı korunarak servis delegasyonuna alınma sonucunu gösterir.

## Durum
- mode: {result.get('mode')}

## Audit
- candidate_count: {audit.get('candidate_count')}
- delegated_count: {audit.get('delegated_count')}
- patchable_count: {audit.get('patchable_count')}

| Fonksiyon | Satır | Route Decorator | Delegated | Legacy | Arg |
|---|---:|---:|---:|---:|---|
{os.linesep.join(rows)}

## Apply
- service: `{apply.get('service')}`
- routes: `{apply.get('routes')}`
- target_compile: `{apply.get('target_compile')}`

## Sağlık Kontrolü
- compileall_ok: {health_summary.get('compileall_ok')}
- app_factory_ok: {health_summary.get('app_factory_ok')}
- overall_ok: {health_summary.get('overall_ok')}
"""
    write_text(md_path, md)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "all"], default="audit")
    ns = ap.parse_args()
    root = Path(ns.project_root).resolve()
    result: dict[str, Any] = {"version": VERSION, "mode": ns.mode, "project_root": str(root)}
    result["audit"] = analyze_routes(root)
    result["apply"] = {}
    result["health_summary"] = {}
    if ns.mode in {"apply", "all"}:
        service = ensure_service(root)
        routes = patch_routes(root)
        result["apply"] = {"service": service, "routes": routes, "target_compile": target_compile(root)}
    if ns.mode == "all":
        result["health_summary"] = health(root)
    result["json_report"] = str(REPORT_JSON)
    result["md_report"] = str(REPORT_MD)
    write_reports(root, result)
    print(json.dumps({k:v for k,v in result.items() if k not in {"health_summary"} or ns.mode=="all"}, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_ASSISTANT_HANDLER_DELEGATE_P1_9_V2_17_19_REPORT_OK")
    if ns.mode == "all" and result["health_summary"].get("overall_ok"):
        print("BYS360_MOBILE_ASSISTANT_HANDLER_DELEGATE_P1_9_V2_17_19_HEALTH_OK")
    apply_routes = result.get("apply", {}).get("routes", {})
    if ns.mode in {"apply", "all"}:
        if apply_routes.get("changed") or result.get("audit", {}).get("delegated_count"):
            print("BYS360_MOBILE_ASSISTANT_HANDLER_DELEGATE_P1_9_V2_17_19_APPLY_OK")
        else:
            print("BYS360_MOBILE_ASSISTANT_HANDLER_DELEGATE_P1_9_V2_17_19_APPLY_NOOP")
    print("BYS360_MOBILE_ASSISTANT_HANDLER_DELEGATE_P1_9_V2_17_19_OK")
    if ns.mode == "all" and not result["health_summary"].get("overall_ok"):
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
