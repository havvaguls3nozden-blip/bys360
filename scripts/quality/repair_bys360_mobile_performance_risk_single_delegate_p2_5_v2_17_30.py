# -*- coding: utf-8 -*-
"""BYS360 Mobile Performance Risk Single Delegate P2.5 V2.17.30."""
from __future__ import annotations

import argparse
import ast
import json
import py_compile
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "V2.17.30"
TARGET_FUNC = "mobile_performance_risk_analysis_v2852"
LEGACY_FUNC = "_bys360_legacy_mobile_performance_risk_analysis_v2852"
DELEGATE_FUNC = "mobile_performance_risk_analysis_v2852_delegate"


def compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "file_not_found"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": str(exc)}


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 120) -> Dict[str, Any]:
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


def health(root: Path) -> Dict[str, Any]:
    compileall = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], root, timeout=180)
    app_factory = run_cmd([
        sys.executable,
        "-c",
        "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))",
    ], root, timeout=180)
    return {
        "compileall_ok": bool(compileall["ok"]),
        "app_factory_ok": bool(app_factory["ok"]),
        "overall_ok": bool(compileall["ok"] and app_factory["ok"]),
        "compileall": compileall,
        "app_factory": app_factory,
    }


def parse_target(path: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "target_exists": path.exists(),
        "target_compile": compile_file(path),
        "parse_error": "",
        "function": {
            "name": TARGET_FUNC,
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
    text = path.read_text(encoding="utf-8", errors="replace")
    legacy_exists = f"def {LEGACY_FUNC}" in text
    info["function"]["legacy"] = legacy_exists
    try:
        tree = ast.parse(text)
    except Exception as exc:
        info["parse_error"] = str(exc)
        return info
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == TARGET_FUNC:
            src = ast.get_source_segment(text, node) or ""
            delegated = (DELEGATE_FUNC in src) or ("performance_summary_service" in src and "delegate" in src)
            arg_names = [a.arg for a in node.args.args]
            info["function"].update({
                "exists": True,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "length": getattr(node, "end_lineno", node.lineno) - node.lineno + 1,
                "route_decorator": bool(node.decorator_list),
                "delegated": delegated,
                "legacy": legacy_exists,
                "patchable": not delegated and not legacy_exists,
                "arg": ", ".join(arg_names),
            })
            break
    return info


def ensure_delegate_service(service_path: Path) -> Dict[str, Any]:
    service_path.parent.mkdir(parents=True, exist_ok=True)
    if not service_path.exists():
        service_path.write_text("# -*- coding: utf-8 -*-\n", encoding="utf-8")
    text = service_path.read_text(encoding="utf-8", errors="replace")
    changed = False
    if f"def {DELEGATE_FUNC}" not in text:
        addition = """


def mobile_performance_risk_analysis_v2852_delegate(legacy_func, user):
    \"\"\"Servis delegasyonu: mobil performans risk analizi.

    URL, endpoint ve blueprint adi korunur; is mantigi legacy fonksiyon
    uzerinden aynen calistirilir. Legacy govde stabil olduktan sonra
    bu servis icine tasinabilir.
    \"\"\"
    return legacy_func(user)
"""
        if not text.endswith("\n"):
            text += "\n"
        text += addition
        service_path.write_text(text, encoding="utf-8")
        changed = True
    return {"path": str(service_path).replace("\\", "/"), "changed": changed, "compile": compile_file(service_path)}


def patch_function(root: Path, target_path: Path, service_path: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "routes_changed": False,
        "patched_functions": [],
        "backup": "",
        "error": "",
        "rolled_back": False,
        "service": {},
        "target_compile": {},
    }
    audit = parse_target(target_path)
    fn = audit["function"]
    if not fn.get("patchable"):
        result["skipped"] = [{"name": TARGET_FUNC, "reason": "not_patchable_or_already_delegated"}]
        result["service"] = ensure_delegate_service(service_path)
        result["target_compile"] = {"routes": compile_file(target_path), "service": compile_file(service_path)}
        return result

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    qroot = root / "_local_quarantine" / f"bys360_mobile_performance_risk_single_delegate_p2_5_{stamp}"
    backup = qroot / "app" / "api" / "mobile" / "performance_routes.py"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_path, backup)
    result["backup"] = str(backup).replace("\\", "/")

    original_text = target_path.read_text(encoding="utf-8", errors="replace")
    try:
        service_info = ensure_delegate_service(service_path)
        result["service"] = service_info
        if not service_info["compile"]["ok"]:
            raise RuntimeError("service_compile_failed: " + service_info["compile"]["error"])

        tree = ast.parse(original_text)
        target_node: Optional[ast.FunctionDef] = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == TARGET_FUNC:
                target_node = node
                break
        if target_node is None or getattr(target_node, "end_lineno", None) is None:
            raise RuntimeError("target_function_not_found_or_no_end_lineno")
        if target_node.args.args and target_node.args.args[0].arg != "user":
            raise RuntimeError("unexpected_signature")

        lines = original_text.splitlines()
        start_idx = target_node.lineno - 1
        end_idx = target_node.end_lineno
        func_block = lines[start_idx:end_idx]
        def_line_idx = None
        for i, line in enumerate(func_block):
            if re.match(r"^\s*def\s+" + re.escape(TARGET_FUNC) + r"\s*\(", line):
                def_line_idx = i
                break
        if def_line_idx is None:
            raise RuntimeError("def_line_not_found")
        func_block[def_line_idx] = re.sub(
            r"def\s+" + re.escape(TARGET_FUNC) + r"\s*\(",
            f"def {LEGACY_FUNC}(",
            func_block[def_line_idx],
            count=1,
        )

        wrapper = [
            f"def {TARGET_FUNC}(user):",
            f"    from app.api.mobile.services.performance_summary_service import {DELEGATE_FUNC}",
            f"    return {DELEGATE_FUNC}({LEGACY_FUNC}, user)",
            "",
        ]
        new_lines = lines[:start_idx] + func_block + [""] + wrapper + lines[end_idx:]
        new_text = "\n".join(new_lines) + ("\n" if original_text.endswith("\n") else "")
        target_path.write_text(new_text, encoding="utf-8")

        target_compile = {"routes": compile_file(target_path), "service": compile_file(service_path)}
        result["target_compile"] = target_compile
        if not target_compile["routes"]["ok"] or not target_compile["service"]["ok"]:
            raise RuntimeError("target_compile_failed")

        result["routes_changed"] = True
        result["patched_functions"] = [TARGET_FUNC]
        return result
    except Exception as exc:
        result["error"] = str(exc)
        try:
            shutil.copy2(backup, target_path)
            result["rolled_back"] = True
        except Exception as rb_exc:
            result["rollback_error"] = str(rb_exc)
        result["target_compile"] = {"routes": compile_file(target_path), "service": compile_file(service_path)}
        return result


def write_reports(root: Path, data: Dict[str, Any]) -> None:
    reports = root / "reports" / "quality"
    reports.mkdir(parents=True, exist_ok=True)
    json_path = reports / "bys360_mobile_performance_risk_single_delegate_p2_5_v2_17_30_report.json"
    md_path = reports / "bys360_mobile_performance_risk_single_delegate_p2_5_v2_17_30_report.md"
    data["json_report"] = str(json_path.relative_to(root)).replace("\\", "/")
    data["md_report"] = str(md_path.relative_to(root)).replace("\\", "/")
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    fn = data.get("audit", {}).get("function", {})
    apply = data.get("apply", {})
    h = data.get("health_summary", {})
    md = []
    md.append("# BYS360 Mobile Performance Risk Single Delegate P2.5 V2.17.30\n")
    md.append("Bu rapor tek ve guvenli okuma/analiz endpointi olan `mobile_performance_risk_analysis_v2852` fonksiyonunun servis delegasyonu sonucunu gosterir.\n")
    md.append("## Durum")
    md.append(f"- mode: {data.get('mode')}\n")
    md.append("## Audit")
    md.append(f"- target_exists: {data.get('audit', {}).get('target_exists')}")
    md.append(f"- target_compile: `{data.get('audit', {}).get('target_compile')}`\n")
    md.append("| Fonksiyon | Var | Satır | Uzunluk | Route Decorator | Delegated | Legacy | Patchable | Arg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    md.append(f"| `{TARGET_FUNC}` | {fn.get('exists')} | {fn.get('line')} | {fn.get('length')} | {fn.get('route_decorator')} | {fn.get('delegated')} | {fn.get('legacy')} | {fn.get('patchable')} | `{fn.get('arg')}` |\n")
    md.append("## Apply")
    if apply:
        for key in ["service", "routes_changed", "patched_functions", "backup", "error", "rolled_back", "target_compile"]:
            md.append(f"- {key}: `{apply.get(key)}`")
    else:
        md.append("- apply: `{}`")
    md.append("\n## Sağlık Kontrolü")
    md.append(f"- compileall_ok: {h.get('compileall_ok')}")
    md.append(f"- app_factory_ok: {h.get('app_factory_ok')}")
    md.append(f"- overall_ok: {h.get('overall_ok')}\n")
    md_path.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "all"], default="all")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    target_path = root / "app" / "api" / "mobile" / "performance_routes.py"
    service_path = root / "app" / "api" / "mobile" / "services" / "performance_summary_service.py"

    print("BYS360 Mobile Performance Risk Single Delegate P2.5 V2.17.30 basliyor...")
    print(f"ProjectRoot={root}")
    print(f"Mode={args.mode}")

    data: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "audit": parse_target(target_path),
        "apply": {},
        "health_summary": {},
    }

    exit_code = 0
    if args.mode in ("apply", "all"):
        data["apply"] = patch_function(root, target_path, service_path)
    if args.mode in ("apply", "all"):
        data["health_summary"] = health(root)
        if not data["health_summary"].get("overall_ok"):
            exit_code = 1
    if args.mode == "all" and (data.get("apply", {}).get("rolled_back") or data.get("apply", {}).get("error")):
        exit_code = 1

    write_reports(root, data)
    print(json.dumps({k: v for k, v in data.items() if k not in ("json_report", "md_report")}, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_RISK_SINGLE_DELEGATE_P2_5_V2_17_30_REPORT_OK")
    if data.get("health_summary") and data["health_summary"].get("overall_ok"):
        print("BYS360_MOBILE_PERFORMANCE_RISK_SINGLE_DELEGATE_P2_5_V2_17_30_HEALTH_OK")
    if data.get("apply"):
        if data["apply"].get("rolled_back"):
            print("BYS360_MOBILE_PERFORMANCE_RISK_SINGLE_DELEGATE_P2_5_V2_17_30_APPLY_ROLLBACK")
        elif data["apply"].get("patched_functions"):
            print("BYS360_MOBILE_PERFORMANCE_RISK_SINGLE_DELEGATE_P2_5_V2_17_30_APPLY_OK")
        else:
            print("BYS360_MOBILE_PERFORMANCE_RISK_SINGLE_DELEGATE_P2_5_V2_17_30_APPLY_NOOP")
    print("BYS360_MOBILE_PERFORMANCE_RISK_SINGLE_DELEGATE_P2_5_V2_17_30_OK")
    print("Rapor dosyalari:")
    print("- reports\\quality\\bys360_mobile_performance_risk_single_delegate_p2_5_v2_17_30_report.md")
    print("- reports\\quality\\bys360_mobile_performance_risk_single_delegate_p2_5_v2_17_30_report.json")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
