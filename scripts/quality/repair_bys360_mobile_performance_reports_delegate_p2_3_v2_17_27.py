# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Reports Delegate P2.3 V2.17.27

Amaç:
- app/api/mobile/performance_routes.py içindeki yalnızca okuma/rapor endpointlerini
  URL/endpoint/blueprint adlarını bozmadan servis delegasyonuna almak.
- Puanlama, onay, yayın, iade/ret veya veri değiştiren endpointlere dokunmaz.

Hedefler:
- mobile_performance_reports
- mobile_performance_risk_analysis_v2852
- mobile_performance_history_archive
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

VERSION = "V2.17.27"
TAG = "BYS360_MOBILE_PERFORMANCE_REPORTS_DELEGATE_P2_3_V2_17_27"
TARGET_ROUTE = Path("app/api/mobile/performance_routes.py")
SERVICE_PATH = Path("app/api/mobile/services/performance_summary_service.py")
SERVICE_ALIAS = "_bys360_mobile_performance_summary_service"
IMPORT_LINE = f"from app.api.mobile.services import performance_summary_service as {SERVICE_ALIAS}"
TARGET_FUNCTIONS = [
    "mobile_performance_reports",
    "mobile_performance_risk_analysis_v2852",
    "mobile_performance_history_archive",
]

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
    except Exception as exc:
        return {"exists": path.exists(), "ok": False, "error": str(exc)}


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 90) -> Dict[str, object]:
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
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(exc)}


def health(project_root: Path) -> Dict[str, object]:
    compile_res = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], project_root, timeout=180)
    app_res = run_cmd([
        sys.executable,
        "-c",
        "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))",
    ], project_root, timeout=120)
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
    # Wrapper içinde aynı argümanları pozisyonel/keyword olarak legacy fonksiyona aktarır.
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
        s = ast.unparse(dec) if hasattr(ast, "unparse") else ""
        if ".route" in s or "route(" in s or "api_route" in s:
            return True
    return False


def collect_audit(project_root: Path) -> Dict[str, object]:
    route_path = project_root / TARGET_ROUTE
    service_path = project_root / SERVICE_PATH
    funcs, parse_error, text = parse_functions(route_path)
    result_funcs: List[Dict[str, object]] = []
    for name in TARGET_FUNCTIONS:
        node = funcs.get(name)
        legacy_name = f"_bys360_legacy_{name}"
        info = FuncInfo(name=name)
        info.legacy = legacy_name in funcs
        if node:
            info.exists = True
            info.line = int(node.lineno)
            info.end_line = int(getattr(node, "end_lineno", node.lineno))
            info.length = info.end_line - info.line + 1
            info.route_decorator = route_decorator(node)
            segment = "\n".join(text.splitlines()[node.lineno-1:info.end_line]) if text else ""
            info.delegated = SERVICE_ALIAS in segment or f"performance_summary_service.{name}" in segment
            info.arg = node_args_text(node)
            info.patchable = info.exists and not info.delegated and not info.legacy and not parse_error
        result_funcs.append(info.__dict__)
    return {
        "target_exists": route_path.exists(),
        "target_path": str(TARGET_ROUTE),
        "target_compile": compile_one(route_path) if route_path.exists() else {"exists": False, "ok": False, "error": "missing"},
        "service_exists": service_path.exists(),
        "service_path": str(SERVICE_PATH),
        "service_compile": compile_one(service_path) if service_path.exists() else {"exists": False, "ok": False, "error": "missing"},
        "parse_error": parse_error or "",
        "candidate_count": len(TARGET_FUNCTIONS),
        "delegated_count": sum(1 for f in result_funcs if f.get("delegated")),
        "patchable_count": sum(1 for f in result_funcs if f.get("patchable")),
        "functions": result_funcs,
    }


def ensure_import(text: str) -> Tuple[str, bool]:
    if IMPORT_LINE in text:
        return text, False
    lines = text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            insert_at = i + 1
        elif stripped and not stripped.startswith("#") and insert_at:
            break
    lines.insert(insert_at, IMPORT_LINE)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), True


def ensure_service(service_path: Path, names: List[str]) -> Dict[str, object]:
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
    for name in names:
        if re.search(rf"^def\s+{re.escape(name)}\s*\(", text, flags=re.M):
            continue
        text += f"\n\ndef {name}(*args, legacy_func=None, **kwargs):\n"
        text += f"    return _delegate_to_legacy('{name}', legacy_func, *args, **kwargs)\n"
        changed = True
    if changed:
        write_text(service_path, text)
    return {"path": str(SERVICE_PATH), "changed": changed, "compile": compile_one(service_path)}


def make_replacement(text: str, node: ast.FunctionDef, name: str) -> str:
    lines = text.splitlines()
    def_start = node.lineno - 1
    end = int(getattr(node, "end_lineno", node.lineno))
    decor_start = def_start
    if node.decorator_list:
        decor_start = min(int(d.lineno) for d in node.decorator_list) - 1
    decorators = lines[decor_start:def_start]
    def_block = lines[def_start:end]
    # Rename only first def occurrence.
    legacy_name = f"_bys360_legacy_{name}"
    legacy_block = def_block[:]
    for idx, line in enumerate(legacy_block):
        if re.match(r"^\s*def\s+" + re.escape(name) + r"\s*\(", line):
            legacy_block[idx] = re.sub(r"def\s+" + re.escape(name) + r"\s*\(", f"def {legacy_name}(", line, count=1)
            break
    indent = re.match(r"^(\s*)", def_block[0]).group(1)
    args = node_args_text(node)
    call_args = call_args_text(node)
    call = f"{SERVICE_ALIAS}.{name}({call_args}, legacy_func={legacy_name})" if call_args else f"{SERVICE_ALIAS}.{name}(legacy_func={legacy_name})"
    wrapper = []
    wrapper.extend(decorators)
    wrapper.append(f"{indent}def {name}({args}):")
    wrapper.append(f"{indent}    return {call}")
    replacement_lines = legacy_block + [""] + wrapper
    new_lines = lines[:decor_start] + replacement_lines + lines[end:]
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")


def patch_routes(project_root: Path) -> Dict[str, object]:
    route_path = project_root / TARGET_ROUTE
    service_path = project_root / SERVICE_PATH
    audit_before = collect_audit(project_root)
    patchable = [f["name"] for f in audit_before["functions"] if f.get("patchable")]
    if not patchable:
        return {"routes_changed": False, "patched_functions": [], "skipped": [{"reason": "no_patchable_functions"}], "backup": "", "error": "", "service": ensure_service(service_path, TARGET_FUNCTIONS)}

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine = project_root / "_local_quarantine" / f"bys360_mobile_performance_reports_delegate_p2_3_{stamp}"
    backup = quarantine / TARGET_ROUTE
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(route_path, backup)

    service_res = ensure_service(service_path, patchable)
    text = read_text(route_path)
    text, import_changed = ensure_import(text)
    patched: List[str] = []
    try:
        # Her patch sonrası AST yeniden okunur; satır kaymaları güvenli yönetilir.
        for name in patchable:
            funcs, parse_error, current_text = parse_functions(route_path) if patched else parse_functions_from_text(text)
            if parse_error:
                raise RuntimeError(parse_error)
            node = funcs.get(name)
            if not node:
                continue
            text = current_text
            text = make_replacement(text, node, name)
            # hedef dosyaya yazıp derlenebilir mi bak
            write_text(route_path, text)
            comp = compile_one(route_path)
            if not comp["ok"]:
                raise RuntimeError(f"{name} patch sonrasi compile hatasi: {comp['error']}")
            patched.append(name)
        # Son hedef compile
        target_compile = {"routes": compile_one(route_path), "service": compile_one(service_path)}
        if not target_compile["routes"]["ok"] or not target_compile["service"]["ok"]:
            raise RuntimeError(str(target_compile))
        return {
            "routes_changed": bool(patched or import_changed),
            "patched_functions": patched,
            "skipped": [],
            "backup": str(backup.relative_to(project_root)),
            "error": "",
            "service": service_res,
            "target_compile": target_compile,
            "quarantine_root": str(quarantine.relative_to(project_root)),
        }
    except Exception as exc:
        shutil.copy2(backup, route_path)
        return {
            "routes_changed": False,
            "patched_functions": patched,
            "skipped": [],
            "backup": str(backup.relative_to(project_root)),
            "error": str(exc),
            "rolled_back": True,
            "service": service_res,
            "target_compile": {"routes": compile_one(route_path), "service": compile_one(service_path)},
        }


def parse_functions_from_text(text: str) -> Tuple[Dict[str, ast.FunctionDef], Optional[str], str]:
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {}, str(exc), text
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    return funcs, None, text


def report_markdown(data: Dict[str, object]) -> str:
    audit = data.get("audit", {}) or {}
    apply = data.get("apply", {}) or {}
    health_summary = data.get("health_summary", {}) or {}
    lines = []
    lines.append(f"# BYS360 Mobile Performance Reports Delegate P2.3 {VERSION}")
    lines.append("")
    lines.append("Bu rapor mobil performans rapor/analiz/arsiv okuma endpointlerinin URL, endpoint ve blueprint adi korunarak servis delegasyonuna alinma sonucunu gosterir.")
    lines.append("")
    lines.append("## Durum")
    lines.append(f"- mode: {data.get('mode')}")
    lines.append("")
    lines.append("## Audit")
    lines.append(f"- candidate_count: {audit.get('candidate_count')}")
    lines.append(f"- delegated_count: {audit.get('delegated_count')}")
    lines.append(f"- patchable_count: {audit.get('patchable_count')}")
    lines.append("")
    lines.append("| Fonksiyon | Satir | Uzunluk | Route Decorator | Delegated | Legacy | Arg |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for f in audit.get("functions", []) or []:
        lines.append(f"| `{f.get('name')}` | {f.get('line')} | {f.get('length')} | {f.get('route_decorator')} | {f.get('delegated')} | {f.get('legacy')} | `{f.get('arg')}` |")
    lines.append("")
    lines.append("## Apply")
    if apply:
        lines.append(f"- service: `{apply.get('service')}`")
        lines.append(f"- routes_changed: {apply.get('routes_changed')}")
        lines.append(f"- patched_functions: {apply.get('patched_functions')}")
        lines.append(f"- skipped: {apply.get('skipped')}")
        lines.append(f"- backup: {apply.get('backup')}")
        lines.append(f"- error: {apply.get('error')}")
        if apply.get("rolled_back"):
            lines.append(f"- rolled_back: {apply.get('rolled_back')}")
    else:
        lines.append("- apply calistirilmadi.")
    lines.append("")
    lines.append("## Saglik Kontrolu")
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

    data: Dict[str, object] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(project_root),
        "audit": collect_audit(project_root),
        "apply": {},
        "health_summary": {},
        "json_report": str(Path("reports/quality/bys360_mobile_performance_reports_delegate_p2_3_v2_17_27_report.json")),
        "md_report": str(Path("reports/quality/bys360_mobile_performance_reports_delegate_p2_3_v2_17_27_report.md")),
    }

    exit_ok = True
    if args.mode in ("apply", "all"):
        data["apply"] = patch_routes(project_root)
        # Apply sonrasi yeniden audit al.
        data["audit_after"] = collect_audit(project_root)
        if data["apply"].get("error"):
            exit_ok = False
    if args.mode in ("all",):
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
        "health_summary": data.get("health_summary"),
        "json_report": data["json_report"],
        "md_report": data["md_report"],
    }, ensure_ascii=False, indent=2))
    print(f"{TAG}_REPORT_OK")
    if args.mode in ("all",) and data.get("health_summary", {}).get("overall_ok"):
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
