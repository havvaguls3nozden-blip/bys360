# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Period Detail Delegate P3.7B V2.17.42
- Does not call write endpoints.
- Delegates only existing period detail/read helper functions.
- Missing helper names are skipped, not treated as fatal.
- Keeps URL/endpoint/blueprint names intact.
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
from typing import Dict, List, Tuple, Any

VERSION = "V2.17.42"
TARGET_REL = Path("app/api/mobile/performance_routes.py")
SERVICE_REL = Path("app/api/mobile/services/performance_period_service.py")
REPORT_JSON_REL = Path("reports/quality/bys360_mobile_performance_period_detail_delegate_p3_7b_v2_17_42_report.json")
REPORT_MD_REL = Path("reports/quality/bys360_mobile_performance_period_detail_delegate_p3_7b_v2_17_42_report.md")

# _period_scope caused P3.7 rollback on some trees; it is diagnostic-only in this release.
PATCH_TARGETS = [
    "mobile_performance_period_detail",
    "_period_progress",
]
OPTIONAL_DIAGNOSTIC_TARGETS = ["_period_scope"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "file_missing"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": str(exc)}


def parse_tree(text: str) -> Tuple[ast.Module | None, str]:
    try:
        return ast.parse(text), ""
    except Exception as exc:
        return None, str(exc)


def function_nodes(text: str) -> Dict[str, ast.FunctionDef]:
    tree, err = parse_tree(text)
    if tree is None:
        return {}
    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}


def has_delegated_body(text: str, node: ast.FunctionDef) -> bool:
    lines = text.splitlines()
    start = node.lineno - 1
    end = node.end_lineno or node.lineno
    block = "\n".join(lines[start:end])
    return "performance_period_service" in block or "_bys360_period_service" in block


def func_signature_and_call_args(node: ast.FunctionDef) -> Tuple[str, str]:
    args = []
    for a in node.args.posonlyargs:
        args.append(a.arg)
    for a in node.args.args:
        args.append(a.arg)
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    # keyword-only args are rare here, but preserve callability conservatively
    for a in node.args.kwonlyargs:
        args.append(a.arg + "=" + a.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)

    # Use the exact textual signature from the original def line if possible is hard; ast.unparse args is OK in py3.12
    try:
        signature = ast.unparse(node.args)
    except Exception:
        signature = ", ".join([a.arg for a in node.args.args])
    call_args = ", ".join(args)
    return signature, call_args


def replace_function_with_delegate(source: str, node: ast.FunctionDef, service_rel_import: str) -> Tuple[str, str]:
    """Return modified source and legacy function name."""
    lines = source.splitlines()
    start = node.lineno - 1
    end = node.end_lineno or node.lineno
    # Include decorators in the public replacement but not in legacy copy.
    decorator_start = start
    if node.decorator_list:
        decorator_start = min(d.lineno for d in node.decorator_list) - 1
    decorators = lines[decorator_start:start]
    original_def_block = lines[start:end]
    legacy_name = f"_bys360_legacy_{node.name}"

    legacy_block = []
    for i, line in enumerate(original_def_block):
        if i == 0:
            legacy_block.append(line.replace(f"def {node.name}", f"def {legacy_name}", 1))
        else:
            legacy_block.append(line)

    signature, call_args = func_signature_and_call_args(node)
    indent = ""  # functions are top-level in this module
    public_block = []
    public_block.extend(decorators)
    public_block.append(f"{indent}def {node.name}({signature}):")
    public_block.append(f"    from app.api.mobile.services import performance_period_service as _bys360_period_service")
    if call_args.strip():
        public_block.append(f"    return _bys360_period_service.{node.name}({call_args})")
    else:
        public_block.append(f"    return _bys360_period_service.{node.name}()")
    public_block.append("")
    public_block.extend(legacy_block)

    new_lines = lines[:decorator_start] + public_block + lines[end:]
    return "\n".join(new_lines) + "\n", legacy_name


def ensure_service_delegates(service_path: Path, names: List[str]) -> Dict[str, Any]:
    service_path.parent.mkdir(parents=True, exist_ok=True)
    if service_path.exists():
        text = read_text(service_path)
    else:
        text = "# -*- coding: utf-8 -*-\n\n"
    changed = False
    additions = []
    for name in names:
        if f"def {name}(" in text:
            continue
        legacy_name = f"_bys360_legacy_{name}"
        additions.append(
            "\n"
            f"def {name}(*args, **kwargs):\n"
            f"    \"\"\"Delegate wrapper generated by P3.7B; calls preserved legacy body at runtime.\"\"\"\n"
            f"    from app.api.mobile import performance_routes as _legacy_routes\n"
            f"    return getattr(_legacy_routes, \"{legacy_name}\")(*args, **kwargs)\n"
        )
        changed = True
    if additions:
        text = text.rstrip() + "\n" + "".join(additions) + "\n"
        write_text(service_path, text)
    return {"path": str(service_path).replace('\\', '/'), "changed": changed, "delegate_count_added": len(additions), "compile": compile_file(service_path)}


def audit(project_root: Path) -> Dict[str, Any]:
    target = project_root / TARGET_REL
    service = project_root / SERVICE_REL
    target_text = read_text(target) if target.exists() else ""
    nodes = function_nodes(target_text)
    functions = []
    for name in PATCH_TARGETS + OPTIONAL_DIAGNOSTIC_TARGETS:
        node = nodes.get(name)
        legacy = f"_bys360_legacy_{name}" in nodes
        delegated = bool(node and has_delegated_body(target_text, node))
        functions.append({
            "name": name,
            "exists": bool(node),
            "line": getattr(node, "lineno", None),
            "end_line": getattr(node, "end_lineno", None),
            "length": ((getattr(node, "end_lineno", 0) or 0) - (getattr(node, "lineno", 0) or 0) + 1) if node else 0,
            "delegated": delegated,
            "legacy": legacy,
            "patchable": bool(node and not delegated and not legacy and name in PATCH_TARGETS),
            "diagnostic_only": name in OPTIONAL_DIAGNOSTIC_TARGETS,
            "arg": ast.unparse(node.args) if node else "",
        })
    return {
        "target_exists": target.exists(),
        "target_compile": compile_file(target),
        "service_exists": service.exists(),
        "service_compile": compile_file(service),
        "candidate_count": len(PATCH_TARGETS),
        "diagnostic_count": len(OPTIONAL_DIAGNOSTIC_TARGETS),
        "delegated_count": sum(1 for f in functions if f["delegated"] and not f["diagnostic_only"]),
        "patchable_count": sum(1 for f in functions if f["patchable"]),
        "functions": functions,
    }


def run_health(project_root: Path) -> Dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    def run(cmd: List[str]) -> Dict[str, Any]:
        try:
            p = subprocess.run(cmd, cwd=str(project_root), text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=120, env=env)
            return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout_tail": p.stdout[-4000:], "stderr_tail": p.stderr[-4000:]}
        except Exception as exc:
            return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(exc)}
    compileall = run([sys.executable, "-m", "compileall", "app", "config.py", "scripts"])
    app_factory = run([sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"])
    return {
        "compileall_ok": compileall["ok"],
        "app_factory_ok": app_factory["ok"],
        "overall_ok": compileall["ok"] and app_factory["ok"],
        "compileall": compileall,
        "app_factory": app_factory,
    }


def apply(project_root: Path) -> Dict[str, Any]:
    target = project_root / TARGET_REL
    service = project_root / SERVICE_REL
    before_compile = {"routes": compile_file(target), "service": compile_file(service)}
    if not before_compile["routes"]["ok"]:
        return {"routes_changed": False, "service_changed": False, "patched_functions": [], "skipped": [], "error": "target_compile_failed_before", "rolled_back": False, "before_target_compile": before_compile}

    source = read_text(target)
    nodes = function_nodes(source)
    skipped = []
    patchable_nodes: List[ast.FunctionDef] = []
    for name in PATCH_TARGETS:
        node = nodes.get(name)
        if not node:
            skipped.append({"name": name, "reason": "function_missing"})
            continue
        if f"_bys360_legacy_{name}" in nodes:
            skipped.append({"name": name, "reason": "legacy_exists_or_already_patched"})
            continue
        if has_delegated_body(source, node):
            skipped.append({"name": name, "reason": "already_delegated"})
            continue
        patchable_nodes.append(node)

    # Optional diagnostic target is never fatal.
    if "_period_scope" not in nodes:
        skipped.append({"name": "_period_scope", "reason": "diagnostic_only_missing_not_fatal"})
    else:
        skipped.append({"name": "_period_scope", "reason": "diagnostic_only_not_patched"})

    quarantine_root = project_root / "_local_quarantine" / f"bys360_mobile_performance_period_detail_delegate_p3_7b_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = quarantine_root / TARGET_REL
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup_path)

    patched = []
    new_source = source
    # Re-parse after each replacement because line numbers shift.
    try:
        for original_node in patchable_nodes:
            current_nodes = function_nodes(new_source)
            node = current_nodes.get(original_node.name)
            if not node:
                skipped.append({"name": original_node.name, "reason": "function_missing_after_reparse"})
                continue
            new_source, legacy_name = replace_function_with_delegate(new_source, node, "performance_period_service")
            # validate incrementally
            ast.parse(new_source)
            patched.append(original_node.name)
    except Exception as exc:
        shutil.copy2(backup_path, target)
        return {
            "routes_changed": False,
            "service_changed": False,
            "patched_functions": patched,
            "skipped": skipped,
            "backup": str(backup_path.relative_to(project_root)),
            "error": str(exc),
            "rolled_back": True,
            "before_target_compile": before_compile,
            "target_compile": {"routes": compile_file(target), "service": compile_file(service)},
        }

    if patched:
        write_text(target, new_source)
    service_result = ensure_service_delegates(service, patched)
    after_compile = {"routes": compile_file(target), "service": compile_file(service)}
    if not after_compile["routes"]["ok"] or not after_compile["service"]["ok"]:
        shutil.copy2(backup_path, target)
        return {
            "routes_changed": bool(patched),
            "service_changed": service_result.get("changed", False),
            "patched_functions": patched,
            "skipped": skipped,
            "backup": str(backup_path.relative_to(project_root)),
            "error": "compile_failed_after_patch",
            "rolled_back": True,
            "service": service_result,
            "target_compile": {"routes": compile_file(target), "service": compile_file(service)},
        }

    return {
        "routes_changed": bool(patched),
        "service_changed": service_result.get("changed", False),
        "patched_functions": patched,
        "skipped": skipped,
        "backup": str(backup_path.relative_to(project_root)),
        "error": "",
        "rolled_back": False,
        "service": service_result,
        "target_compile": after_compile,
    }


def write_reports(project_root: Path, report: Dict[str, Any]) -> None:
    json_path = project_root / REPORT_JSON_REL
    md_path = project_root / REPORT_MD_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))
    lines = []
    lines.append("# BYS360 Mobile Performance Period Detail Delegate P3.7B V2.17.42")
    lines.append("")
    lines.append("Bu rapor P3.7 rollback sonrasinda eksik helper adlarini hata saymadan, yalnizca mevcut donem detayi/okuma helper fonksiyonlarini servis delegasyonuna alma sonucunu gosterir.")
    lines.append("")
    lines.append("## Durum")
    lines.append(f"- mode: {report.get('mode')}")
    lines.append("")
    a = report.get("audit", {})
    lines.append("## Audit")
    lines.append(f"- candidate_count: {a.get('candidate_count')}")
    lines.append(f"- diagnostic_count: {a.get('diagnostic_count')}")
    lines.append(f"- delegated_count: {a.get('delegated_count')}")
    lines.append(f"- patchable_count: {a.get('patchable_count')}")
    lines.append("")
    lines.append("| Fonksiyon | Var | Satir | Uzunluk | Delegated | Legacy | Patchable | Not | Arg |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|---|")
    for f in a.get("functions", []):
        note = "diagnostic-only" if f.get("diagnostic_only") else ""
        lines.append(f"| `{f.get('name')}` | {f.get('exists')} | {f.get('line') or ''} | {f.get('length')} | {f.get('delegated')} | {f.get('legacy')} | {f.get('patchable')} | {note} | `{f.get('arg')}` |")
    lines.append("")
    lines.append("## Apply")
    ap = report.get("apply", {})
    if ap:
        lines.append(f"- routes_changed: `{ap.get('routes_changed')}`")
        lines.append(f"- service_changed: `{ap.get('service_changed')}`")
        lines.append(f"- patched_functions: `{ap.get('patched_functions')}`")
        lines.append(f"- skipped: `{ap.get('skipped')}`")
        lines.append(f"- backup: `{ap.get('backup')}`")
        lines.append(f"- error: `{ap.get('error')}`")
        lines.append(f"- rolled_back: `{ap.get('rolled_back')}`")
        lines.append(f"- service: `{ap.get('service')}`")
    else:
        lines.append("- apply calismadi (audit modu).")
    lines.append("")
    h = report.get("health_summary", {})
    lines.append("## Saglik Kontrolu")
    lines.append(f"- compileall_ok: {h.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {h.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {h.get('overall_ok')}")
    lines.append("")
    lines.append("## Not")
    lines.append("Bu adim gercek POST/yazma endpointlerini calistirmaz ve URL/endpoint/blueprint adlarini degistirmez. `_period_scope` eksikse hata sayilmaz; yalnizca tanisal olarak raporlanir.")
    write_text(md_path, "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "all"], default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    print("BYS360 Mobile Performance Period Detail Delegate P3.7B V2.17.42 basliyor...")
    print(f"ProjectRoot={root}")
    print(f"Mode={args.mode}")

    report: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "audit": audit(root),
        "apply": {},
        "health_summary": {},
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }
    if args.mode == "all":
        report["apply"] = apply(root)
        report["audit_after"] = audit(root)
        report["health_summary"] = run_health(root)
    write_reports(root, report)
    print(json.dumps({k: report[k] for k in ["version", "mode", "project_root", "audit", "apply", "health_summary", "json_report", "md_report"]}, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7B_V2_17_42_REPORT_OK")
    if args.mode == "all" and report.get("health_summary", {}).get("overall_ok"):
        print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7B_V2_17_42_HEALTH_OK")
    if args.mode == "all" and report.get("apply", {}).get("rolled_back"):
        print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7B_V2_17_42_APPLY_ROLLBACK")
    elif args.mode == "all" and report.get("apply", {}).get("patched_functions"):
        print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7B_V2_17_42_APPLY_OK")
    elif args.mode == "all":
        print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7B_V2_17_42_APPLY_NOOP")
    print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7B_V2_17_42_OK")
    # Success if health is OK and no rollback. No-op is acceptable.
    if args.mode == "all":
        if not report.get("health_summary", {}).get("overall_ok"):
            return 1
        if report.get("apply", {}).get("rolled_back"):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
