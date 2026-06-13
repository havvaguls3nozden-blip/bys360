# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance History Delegate P2.3B V2.17.28

Amaç:
- P2.3 toplu rapor/analiz patch denemesinde rollback görüldüğü için daha küçük ilerlemek.
- Sadece okuma amaçlı mobile_performance_history_archive fonksiyonunu servis delegasyonuna almak.
- URL, endpoint, blueprint ve decorator yapısını değiştirmemek.
- Route dosyasına global import eklememek; wrapper içinde lokal import kullanmak.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

VERSION = "V2.17.28"
TAG = "BYS360_MOBILE_PERFORMANCE_HISTORY_DELEGATE_P2_3B_V2_17_28"
TARGET_ROUTE = Path("app/api/mobile/performance_routes.py")
SERVICE_PATH = Path("app/api/mobile/services/performance_summary_service.py")
SERVICE_MODULE = "app.api.mobile.services.performance_summary_service"
SERVICE_ALIAS = "_bys360_mobile_performance_summary_service"
TARGET_FUNCTION = "mobile_performance_history_archive"


@dataclass
class FuncInfo:
    name: str
    exists: bool = False
    line: int = 0
    end_line: int = 0
    length: int = 0
    route_decorator: bool = False
    delegated: bool = False
    legacy: bool = False
    arg: str = ""
    patchable: bool = False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def compile_one(path: Path) -> Dict[str, object]:
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": path.exists(), "ok": True, "error": ""}
    except Exception as exc:  # noqa: BLE001
        return {"exists": path.exists(), "ok": False, "error": str(exc)}


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 180) -> Dict[str, object]:
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
            "stdout_tail": (p.stdout or "")[-4000:],
            "stderr_tail": (p.stderr or "")[-4000:],
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(exc)}


def health(project_root: Path) -> Dict[str, object]:
    compile_res = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], project_root, timeout=240)
    app_res = run_cmd([
        sys.executable,
        "-c",
        "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))",
    ], project_root, timeout=160)
    return {
        "compileall_ok": bool(compile_res["ok"]),
        "app_factory_ok": bool(app_res["ok"]),
        "overall_ok": bool(compile_res["ok"] and app_res["ok"]),
        "compileall": compile_res,
        "app_factory": app_res,
    }


def parse_functions(path: Path) -> Tuple[Dict[str, ast.FunctionDef], Optional[str], str]:
    if not path.exists():
        return {}, f"Dosya yok: {path}", ""
    text = read_text(path)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {}, str(exc), text
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    return funcs, None, text


def node_args_text(node: ast.FunctionDef) -> str:
    parts: List[str] = []
    args = list(getattr(node.args, "posonlyargs", [])) + list(node.args.args)
    parts.extend(a.arg for a in args)
    if node.args.vararg:
        parts.append("*" + node.args.vararg.arg)
    parts.extend(a.arg for a in node.args.kwonlyargs)
    if node.args.kwarg:
        parts.append("**" + node.args.kwarg.arg)
    return ", ".join(parts)


def call_args_text(node: ast.FunctionDef) -> str:
    parts: List[str] = []
    args = list(getattr(node.args, "posonlyargs", [])) + list(node.args.args)
    parts.extend(a.arg for a in args)
    if node.args.vararg:
        parts.append("*" + node.args.vararg.arg)
    for a in node.args.kwonlyargs:
        parts.append(f"{a.arg}={a.arg}")
    if node.args.kwarg:
        parts.append("**" + node.args.kwarg.arg)
    return ", ".join(parts)


def route_decorator(node: ast.FunctionDef) -> bool:
    for dec in node.decorator_list:
        try:
            s = ast.unparse(dec)
        except Exception:  # noqa: BLE001
            s = ""
        if ".route" in s or "route(" in s or "api_route" in s:
            return True
    return False


def collect_audit(project_root: Path) -> Dict[str, object]:
    route_path = project_root / TARGET_ROUTE
    service_path = project_root / SERVICE_PATH
    funcs, parse_error, text = parse_functions(route_path)
    legacy_name = f"_bys360_legacy_{TARGET_FUNCTION}"
    node = funcs.get(TARGET_FUNCTION)
    info = FuncInfo(name=TARGET_FUNCTION)
    info.legacy = legacy_name in funcs
    if node:
        info.exists = True
        info.line = int(node.lineno)
        info.end_line = int(getattr(node, "end_lineno", node.lineno))
        info.length = info.end_line - info.line + 1
        info.route_decorator = route_decorator(node)
        segment = "\n".join(text.splitlines()[node.lineno - 1:info.end_line]) if text else ""
        info.delegated = SERVICE_MODULE in segment or f"{SERVICE_ALIAS}.{TARGET_FUNCTION}" in segment or "legacy_func=" in segment
        info.arg = node_args_text(node)
        info.patchable = bool(info.exists and not info.delegated and not info.legacy and not parse_error)
    return {
        "target_exists": route_path.exists(),
        "target_path": str(TARGET_ROUTE),
        "target_compile": compile_one(route_path) if route_path.exists() else {"exists": False, "ok": False, "error": "missing"},
        "service_exists": service_path.exists(),
        "service_path": str(SERVICE_PATH),
        "service_compile": compile_one(service_path) if service_path.exists() else {"exists": False, "ok": False, "error": "missing"},
        "parse_error": parse_error or "",
        "function": info.__dict__,
    }


def ensure_service(service_path: Path) -> Dict[str, object]:
    service_path.parent.mkdir(parents=True, exist_ok=True)
    if service_path.exists():
        text = read_text(service_path)
    else:
        text = "# -*- coding: utf-8 -*-\n\"\"\"BYS360 mobile performance summary service delegates.\"\"\"\n\n"
    changed = False
    if "def _delegate_to_legacy(" not in text:
        text += "\n\ndef _delegate_to_legacy(name, legacy_func, *args, **kwargs):\n"
        text += "    if legacy_func is None:\n"
        text += "        raise RuntimeError(f'Mobil performans servis delegasyonu legacy fonksiyonu bulunamadi: {name}')\n"
        text += "    return legacy_func(*args, **kwargs)\n"
        changed = True
    if not re.search(rf"^def\s+{re.escape(TARGET_FUNCTION)}\s*\(", text, flags=re.M):
        text += f"\n\ndef {TARGET_FUNCTION}(*args, legacy_func=None, **kwargs):\n"
        text += f"    return _delegate_to_legacy('{TARGET_FUNCTION}', legacy_func, *args, **kwargs)\n"
        changed = True
    if changed:
        write_text(service_path, text)
    return {"path": str(SERVICE_PATH), "changed": changed, "compile": compile_one(service_path)}


def make_replacement(text: str, node: ast.FunctionDef) -> str:
    lines = text.splitlines()
    def_start = node.lineno - 1
    end = int(getattr(node, "end_lineno", node.lineno))
    decor_start = def_start
    if node.decorator_list:
        decor_start = min(int(getattr(d, "lineno", node.lineno)) for d in node.decorator_list) - 1
    decorators = lines[decor_start:def_start]
    def_block = lines[def_start:end]
    legacy_name = f"_bys360_legacy_{TARGET_FUNCTION}"
    legacy_block = def_block[:]
    renamed = False
    for idx, line in enumerate(legacy_block):
        if re.match(r"^\s*def\s+" + re.escape(TARGET_FUNCTION) + r"\s*\(", line):
            legacy_block[idx] = re.sub(r"def\s+" + re.escape(TARGET_FUNCTION) + r"\s*\(", f"def {legacy_name}(", line, count=1)
            renamed = True
            break
    if not renamed:
        raise RuntimeError(f"Def satiri yeniden adlandirilamadi: {TARGET_FUNCTION}")
    indent = re.match(r"^(\s*)", def_block[0]).group(1)
    args = node_args_text(node)
    call_args = call_args_text(node)
    service_call = f"{SERVICE_ALIAS}.{TARGET_FUNCTION}({call_args}, legacy_func={legacy_name})" if call_args else f"{SERVICE_ALIAS}.{TARGET_FUNCTION}(legacy_func={legacy_name})"
    wrapper: List[str] = []
    wrapper.extend(decorators)
    wrapper.append(f"{indent}def {TARGET_FUNCTION}({args}):")
    wrapper.append(f"{indent}    from {SERVICE_MODULE} import {TARGET_FUNCTION} as _bys360_service_func")
    # Lokal importta modül alias yerine fonksiyon importu kullanılır; global import kaynaklı syntax riskini kaldırır.
    service_call_local = f"_bys360_service_func({call_args}, legacy_func={legacy_name})" if call_args else f"_bys360_service_func(legacy_func={legacy_name})"
    wrapper[-1] = f"{indent}    return {service_call_local}"
    replacement_lines = legacy_block + [""] + wrapper
    new_lines = lines[:decor_start] + replacement_lines + lines[end:]
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")


def patch_routes(project_root: Path) -> Dict[str, object]:
    route_path = project_root / TARGET_ROUTE
    service_path = project_root / SERVICE_PATH
    audit_before = collect_audit(project_root)
    f = audit_before.get("function", {}) or {}
    if not f.get("patchable"):
        return {
            "routes_changed": False,
            "patched_functions": [],
            "skipped": [{"reason": "not_patchable", "function": f}],
            "backup": "",
            "error": "",
            "service": ensure_service(service_path),
            "target_compile": {"routes": compile_one(route_path), "service": compile_one(service_path)},
        }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine = project_root / "_local_quarantine" / f"bys360_mobile_performance_history_delegate_p2_3b_{stamp}"
    backup_route = quarantine / TARGET_ROUTE
    backup_service = quarantine / SERVICE_PATH
    backup_route.parent.mkdir(parents=True, exist_ok=True)
    backup_service.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(route_path, backup_route)
    if service_path.exists():
        shutil.copy2(service_path, backup_service)

    patched: List[str] = []
    try:
        service_res = ensure_service(service_path)
        funcs, parse_error, text = parse_functions(route_path)
        if parse_error:
            raise RuntimeError(parse_error)
        node = funcs.get(TARGET_FUNCTION)
        if not node:
            raise RuntimeError(f"Fonksiyon bulunamadi: {TARGET_FUNCTION}")
        new_text = make_replacement(text, node)
        write_text(route_path, new_text)
        target_compile = {"routes": compile_one(route_path), "service": compile_one(service_path)}
        if not target_compile["routes"]["ok"] or not target_compile["service"]["ok"]:
            raise RuntimeError(str(target_compile))
        patched.append(TARGET_FUNCTION)
        return {
            "routes_changed": True,
            "patched_functions": patched,
            "backup": str(backup_route.relative_to(project_root)),
            "error": "",
            "rolled_back": False,
            "service": service_res,
            "target_compile": target_compile,
            "quarantine_root": str(quarantine.relative_to(project_root)),
        }
    except Exception as exc:  # noqa: BLE001
        shutil.copy2(backup_route, route_path)
        if backup_service.exists():
            shutil.copy2(backup_service, service_path)
        return {
            "routes_changed": False,
            "patched_functions": patched,
            "backup": str(backup_route.relative_to(project_root)),
            "error": str(exc),
            "rolled_back": True,
            "service": {"path": str(SERVICE_PATH), "restored": backup_service.exists()},
            "target_compile": {"routes": compile_one(route_path), "service": compile_one(service_path)},
        }


def report_markdown(data: Dict[str, object]) -> str:
    audit = data.get("audit", {}) or {}
    apply = data.get("apply", {}) or {}
    health_summary = data.get("health_summary", {}) or {}
    f = audit.get("function", {}) or {}
    lines: List[str] = []
    lines.append(f"# BYS360 Mobile Performance History Delegate P2.3B {VERSION}")
    lines.append("")
    lines.append("Bu rapor P2.3 toplu denemesi yerine tek ve güvenli okuma endpointi olan performans geçmiş arşivi fonksiyonunun servis delegasyonu sonucunu gösterir.")
    lines.append("")
    lines.append("## Durum")
    lines.append(f"- mode: {data.get('mode')}")
    lines.append("")
    lines.append("## Audit")
    lines.append(f"- target_exists: {audit.get('target_exists')}")
    lines.append(f"- target_compile: `{audit.get('target_compile')}`")
    lines.append(f"- service_compile: `{audit.get('service_compile')}`")
    lines.append("")
    lines.append("| Fonksiyon | Var | Satır | Uzunluk | Route Decorator | Delegated | Legacy | Patchable | Arg |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    lines.append(f"| `{f.get('name')}` | {f.get('exists')} | {f.get('line')} | {f.get('length')} | {f.get('route_decorator')} | {f.get('delegated')} | {f.get('legacy')} | {f.get('patchable')} | `{f.get('arg')}` |")
    lines.append("")
    lines.append("## Apply")
    if apply:
        lines.append(f"- service: `{apply.get('service')}`")
        lines.append(f"- routes_changed: {apply.get('routes_changed')}")
        lines.append(f"- patched_functions: {apply.get('patched_functions')}")
        lines.append(f"- backup: {apply.get('backup')}")
        lines.append(f"- error: {apply.get('error')}")
        lines.append(f"- rolled_back: {apply.get('rolled_back')}")
        lines.append(f"- target_compile: `{apply.get('target_compile')}`")
    else:
        lines.append("- apply çalıştırılmadı.")
    lines.append("")
    lines.append("## Sağlık Kontrolü")
    lines.append(f"- compileall_ok: {health_summary.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {health_summary.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {health_summary.get('overall_ok')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "all"], default="all")
    args = ap.parse_args()
    project_root = Path(args.project_root).resolve()
    os.chdir(project_root)

    report_rel = Path("reports/quality/bys360_mobile_performance_history_delegate_p2_3b_v2_17_28_report")
    data: Dict[str, object] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(project_root),
        "audit": collect_audit(project_root),
        "apply": {},
        "audit_after": {},
        "health_summary": {},
        "json_report": str(report_rel.with_suffix(".json")),
        "md_report": str(report_rel.with_suffix(".md")),
    }

    exit_ok = True
    if args.mode in ("apply", "all"):
        data["apply"] = patch_routes(project_root)
        data["audit_after"] = collect_audit(project_root)
        if data["apply"].get("error"):
            exit_ok = False
    if args.mode == "all":
        data["health_summary"] = health(project_root)
        if not data["health_summary"].get("overall_ok"):
            exit_ok = False

    report_dir = project_root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = project_root / data["json_report"]
    md_path = project_root / data["md_report"]
    write_text(json_path, json.dumps(data, ensure_ascii=False, indent=2))
    write_text(md_path, report_markdown(data))

    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "audit": data.get("audit"),
        "apply": data.get("apply"),
        "audit_after": data.get("audit_after"),
        "health_summary": data.get("health_summary"),
        "json_report": data["json_report"],
        "md_report": data["md_report"],
    }, ensure_ascii=False, indent=2))
    print(f"{TAG}_REPORT_OK")
    if args.mode == "all" and data.get("health_summary", {}).get("overall_ok"):
        print(f"{TAG}_HEALTH_OK")
    if args.mode in ("apply", "all"):
        if data.get("apply", {}).get("error"):
            print(f"{TAG}_APPLY_ROLLBACK")
        elif data.get("apply", {}).get("patched_functions"):
            print(f"{TAG}_APPLY_OK")
        else:
            print(f"{TAG}_APPLY_NOOP")
    print(f"{TAG}_OK")
    print("Rapor dosyalari:")
    print(f"- {data['md_report']}")
    print(f"- {data['json_report']}")
    return 0 if exit_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
