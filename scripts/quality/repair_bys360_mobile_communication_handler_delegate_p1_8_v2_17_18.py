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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

VERSION = "V2.17.18"
SLUG = "bys360_mobile_communication_handler_delegate_p1_8_v2_17_18"

TARGET_NAMES = [
    "_b46_thread_row",
    "mobile_b46_communication_create_thread",
    "mobile_b46_communication_send",
    "mobile_b46_communication_threads",
    "mobile_b46_communication_thread_detail",
    "_b48_thread_row",
    "mobile_b48_communication_v2_create_thread",
    "mobile_b48_communication_v2_send",
    "mobile_b48_communication_v2_users",
    "mobile_b48_communication_v2_threads",
    "mobile_b48_communication_v2_thread_detail",
]


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except Exception:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def safe_compile(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": str(exc)}


def run_cmd(args: List[str], cwd: Path, timeout: int = 90) -> Dict[str, object]:
    try:
        p = subprocess.run(
            args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout_tail": p.stdout[-4000:],
            "stderr_tail": p.stderr[-4000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(exc)}


def health(root: Path) -> Dict[str, object]:
    compile_res = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], root, timeout=180)
    factory_code = "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"
    app_res = run_cmd([sys.executable, "-c", factory_code], root, timeout=120)
    return {
        "compileall_ok": bool(compile_res.get("ok")),
        "app_factory_ok": bool(app_res.get("ok")) and "BYS360_APP_CREATE_OK" in str(app_res.get("stdout_tail", "")),
        "overall_ok": bool(compile_res.get("ok")) and bool(app_res.get("ok")) and "BYS360_APP_CREATE_OK" in str(app_res.get("stdout_tail", "")),
        "compileall": compile_res,
        "app_factory": app_res,
    }


def get_functions(path: Path) -> Tuple[List[Dict[str, object]], str]:
    text = read_text(path)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [], f"{exc}"
    lines = text.splitlines()
    result = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            dec_start = min([d.lineno for d in node.decorator_list], default=node.lineno)
            block_lines = lines[dec_start - 1: node.end_lineno]
            body_lines = lines[node.lineno - 1: node.end_lineno]
            block = "\n".join(block_lines)
            body = "\n".join(body_lines)
            name = node.name
            is_target = name in TARGET_NAMES or ("communication" in name and name.startswith("mobile_")) or name in {"_b46_thread_row", "_b48_thread_row"}
            if not is_target:
                continue
            delegated = "communication_service" in body or f"{name}_delegate" in body
            legacy_name = f"_bys360_legacy_{name}"
            legacy_exists = f"def {legacy_name}(" in text
            route_decorator = "@" in "\n".join(lines[dec_start - 1: node.lineno - 1])
            args = [a.arg for a in node.args.args]
            if node.args.vararg:
                args.append("*" + node.args.vararg.arg)
            if node.args.kwarg:
                args.append("**" + node.args.kwarg.arg)
            result.append({
                "name": name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "decorator_start": dec_start,
                "route_decorator": route_decorator,
                "delegated": delegated,
                "legacy": legacy_exists,
                "arg": ", ".join(args),
                "patchable": not delegated and not name.startswith("_bys360_legacy_"),
            })
    return result, ""


def make_delegate_call(name: str, arg_text: str) -> str:
    args = [a.strip() for a in arg_text.split(",") if a.strip()]
    call_args = []
    for a in args:
        if a.startswith("**"):
            call_args.append(a)
        elif a.startswith("*"):
            call_args.append(a)
        else:
            call_args.append(a)
    return ", ".join(call_args)


def patch_function(text: str, fn: Dict[str, object]) -> str:
    lines = text.splitlines()
    name = str(fn["name"])
    legacy_name = f"_bys360_legacy_{name}"
    dec_start = int(fn["decorator_start"])
    line_no = int(fn["line"])
    end_line = int(fn["end_line"])
    arg_text = str(fn.get("arg", ""))

    decorators = lines[dec_start - 1: line_no - 1]
    original_func = lines[line_no - 1: end_line]
    legacy_func = original_func[:]
    legacy_func[0] = re.sub(rf"def\s+{re.escape(name)}\s*\(", f"def {legacy_name}(", legacy_func[0], count=1)

    call_args = make_delegate_call(name, arg_text)
    wrapper = []
    wrapper.extend(decorators)
    wrapper.append(original_func[0])
    wrapper.append(f"    from app.api.mobile.services.communication_service import {name}_delegate")
    wrapper.append(f"    return {name}_delegate({call_args})")
    wrapper.append("")
    wrapper.extend(legacy_func)

    new_lines = lines[:dec_start - 1] + wrapper + lines[end_line:]
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")


def ensure_service(service_path: Path, target_fns: List[str]) -> Dict[str, object]:
    existing = read_text(service_path) if service_path.exists() else ""
    if not existing.strip():
        existing = '''"""BYS360 mobile communication service delegation layer.

This module keeps mobile route public functions thin while preserving
URL, endpoint and blueprint behavior in app/api/mobile/routes.py.
"""

from __future__ import annotations

from typing import Any


'''
    changed = False
    for name in target_fns:
        delegate = f"{name}_delegate"
        if f"def {delegate}(" in existing:
            continue
        legacy_name = f"_bys360_legacy_{name}"
        addition = f'''

def {delegate}(*args: Any, **kwargs: Any) -> Any:
    from app.api.mobile import routes as mobile_routes
    legacy = getattr(mobile_routes, "{legacy_name}", None)
    if legacy is None:
        raise RuntimeError("BYS360 communication legacy handler not found: {legacy_name}")
    return legacy(*args, **kwargs)
'''
        existing += addition
        changed = True
    if changed:
        write_text(service_path, existing)
    return {"path": str(service_path).replace("/", "\\"), "changed": changed, "delegate_count": len([n for n in target_fns if f"def {n}_delegate(" in existing])}


def build_report(root: Path, mode: str) -> Dict[str, object]:
    routes_path = root / "app" / "api" / "mobile" / "routes.py"
    service_path = root / "app" / "api" / "mobile" / "services" / "communication_service.py"
    funcs, syntax_error = get_functions(routes_path)
    audit = {
        "exists": routes_path.exists(),
        "path": rel(routes_path, root),
        "size_kb": round(routes_path.stat().st_size / 1024, 1) if routes_path.exists() else 0,
        "line_count": len(read_text(routes_path).splitlines()) if routes_path.exists() else 0,
        "syntax_ok": not syntax_error,
        "syntax_error": syntax_error,
        "candidate_count": len(funcs),
        "delegated_count": len([f for f in funcs if f["delegated"]]),
        "patchable_count": len([f for f in funcs if f["patchable"]]),
        "functions": funcs,
    }
    report = {
        "version": VERSION,
        "mode": mode,
        "audit": audit,
        "apply": {},
        "health_summary": {},
    }
    return report


def write_reports(root: Path, report: Dict[str, object]) -> None:
    reports_dir = root / "reports" / "quality"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / f"{SLUG}_report.json"
    md_path = reports_dir / f"{SLUG}_report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = []
    lines.append(f"# BYS360 Mobile Communication Handler Delegate P1.8 {VERSION}")
    lines.append("")
    lines.append("Bu rapor mobil iletisim/mesajlasma fonksiyonlarinin servis delegasyonu sonucunu gosterir.")
    lines.append("")
    lines.append("## Durum")
    lines.append(f"- mode: {report.get('mode')}")
    lines.append("")
    audit = report.get("audit", {})
    lines.append("## Audit")
    for k in ["candidate_count", "delegated_count", "patchable_count"]:
        lines.append(f"- {k}: {audit.get(k)}")
    lines.append("")
    lines.append("| Fonksiyon | Satir | Route Decorator | Delegated | Legacy | Arg |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for f in audit.get("functions", []):
        lines.append(f"| `{f.get('name')}` | {f.get('line')} | {f.get('route_decorator')} | {f.get('delegated')} | {f.get('legacy')} | `{f.get('arg')}` |")
    lines.append("")
    lines.append("## Apply")
    apply = report.get("apply", {})
    for k, v in apply.items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Saglik Kontrolu")
    hs = report.get("health_summary", {})
    for k in ["compileall_ok", "app_factory_ok", "overall_ok"]:
        lines.append(f"- {k}: {hs.get(k)}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report["json_report"] = str(json_path.relative_to(root)).replace("/", "\\")
    report["md_report"] = str(md_path.relative_to(root)).replace("/", "\\")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "apply", "all"], default="audit")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    routes_path = root / "app" / "api" / "mobile" / "routes.py"
    service_path = root / "app" / "api" / "mobile" / "services" / "communication_service.py"

    report = build_report(root, args.mode)

    if args.mode in {"apply", "all"}:
        funcs = report["audit"].get("functions", [])
        patchable = [f for f in funcs if f.get("patchable")]
        patched = []
        skipped = []
        backup = ""
        error = ""
        if patchable:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            qroot = root / "_local_quarantine" / f"bys360_mobile_communication_handler_delegate_p1_8_{ts}"
            backup_path = qroot / "app" / "api" / "mobile" / "routes.py.before_p1_8"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(routes_path, backup_path)
            backup = rel(backup_path, root)
            original = read_text(routes_path)
            new_text = original
            try:
                # Patch from bottom to top to keep line numbers stable.
                for f in sorted(patchable, key=lambda x: int(x["decorator_start"]), reverse=True):
                    before = new_text
                    new_text = patch_function(new_text, f)
                    if new_text != before:
                        patched.append(f["name"])
                write_text(routes_path, new_text)
                service_info = ensure_service(service_path, patched)
                target_compile = {"routes": safe_compile(routes_path), "communication_service": safe_compile(service_path)}
                if not target_compile["routes"]["ok"] or not target_compile["communication_service"]["ok"]:
                    shutil.copy2(backup_path, routes_path)
                    error = f"target_compile_failed: {target_compile}"
                    patched = []
                    service_info = ensure_service(service_path, [])
                else:
                    report["apply"]["target_compile"] = target_compile
                    report["apply"]["service"] = service_info
            except Exception as exc:
                shutil.copy2(backup_path, routes_path)
                error = str(exc)
                patched = []
        else:
            skipped.append({"reason": "no_patchable_functions"})
            service_info = ensure_service(service_path, [])
            report["apply"]["service"] = service_info
        report["apply"].update({
            "routes_changed": bool(patched),
            "patched_functions": patched,
            "skipped": skipped,
            "backup": backup,
            "error": error,
        })

        # refresh audit after apply
        report["audit"] = build_report(root, args.mode)["audit"]

    if args.mode in {"apply", "all"}:
        hs = health(root)
        report["health_summary"] = {k: hs[k] for k in ["compileall_ok", "app_factory_ok", "overall_ok"]}
        report["health_detail"] = hs
    elif args.mode == "audit":
        report["health_summary"] = {}

    write_reports(root, report)
    print(json.dumps({k: v for k, v in report.items() if k not in {"health_detail"}}, indent=2, ensure_ascii=False))
    print(f"BYS360_MOBILE_COMMUNICATION_HANDLER_DELEGATE_P1_8_{VERSION.replace('.', '_')}_REPORT_OK")
    if args.mode in {"apply", "all"}:
        if report["health_summary"].get("overall_ok"):
            if report["apply"].get("patched_functions"):
                print(f"BYS360_MOBILE_COMMUNICATION_HANDLER_DELEGATE_P1_8_{VERSION.replace('.', '_')}_APPLY_OK")
            else:
                print(f"BYS360_MOBILE_COMMUNICATION_HANDLER_DELEGATE_P1_8_{VERSION.replace('.', '_')}_APPLY_NOOP")
            print(f"BYS360_MOBILE_COMMUNICATION_HANDLER_DELEGATE_P1_8_{VERSION.replace('.', '_')}_HEALTH_OK")
            print(f"BYS360_MOBILE_COMMUNICATION_HANDLER_DELEGATE_P1_8_{VERSION.replace('.', '_')}_OK")
            return 0
        print(f"BYS360_MOBILE_COMMUNICATION_HANDLER_DELEGATE_P1_8_{VERSION.replace('.', '_')}_HEALTH_FAIL")
        return 1
    print(f"BYS360_MOBILE_COMMUNICATION_HANDLER_DELEGATE_P1_8_{VERSION.replace('.', '_')}_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
