# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "V2.17.10"
REPORT_STEM = "bys360_mobile_dashboard_profile_delegate_p1_4_v2_17_10"

TARGETS: Dict[str, Dict[str, str]] = {
    # Dashboard/KPI targets from P1.1 inventory. Missing functions are skipped safely.
    "mobile_dashboard_summary": {"service": "dashboard_service", "delegate": "delegate_mobile_dashboard_summary", "group": "dashboard"},
    "mobile_kpi_target_management_v2853": {"service": "dashboard_service", "delegate": "delegate_mobile_kpi_target_management_v2853", "group": "dashboard"},
    "mobile_kpi_target_create_v2853": {"service": "dashboard_service", "delegate": "delegate_mobile_kpi_target_create_v2853", "group": "dashboard"},
    "mobile_kpi_target_progress_v2853": {"service": "dashboard_service", "delegate": "delegate_mobile_kpi_target_progress_v2853", "group": "dashboard"},
    # Profile candidates. If the project uses different names, they remain untouched.
    "mobile_profile": {"service": "profile_service", "delegate": "delegate_mobile_profile", "group": "profile"},
    "mobile_profile_update": {"service": "profile_service", "delegate": "delegate_mobile_profile_update", "group": "profile"},
    "mobile_profile_me": {"service": "profile_service", "delegate": "delegate_mobile_profile_me", "group": "profile"},
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def syntax_ok(path: Path) -> Tuple[bool, str]:
    try:
        ast.parse(read_text(path), filename=str(path))
        return True, ""
    except Exception as e:
        return False, f"{e.__class__.__name__}: {e}"


def parse_functions(path: Path) -> Dict[str, ast.FunctionDef]:
    tree = ast.parse(read_text(path), filename=str(path))
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def leading_ws(s: str) -> str:
    return s[: len(s) - len(s.lstrip(" \t"))]


def function_params(fn: ast.FunctionDef) -> List[str]:
    names: List[str] = []
    args = fn.args
    for a in list(args.posonlyargs) + list(args.args):
        names.append(a.arg)
    if args.vararg:
        names.append("*" + args.vararg.arg)
    for a in args.kwonlyargs:
        names.append(f"{a.arg}={a.arg}")
    if args.kwarg:
        names.append("**" + args.kwarg.arg)
    return names


def is_delegated(segment: str, public_name: str, delegate_name: str) -> bool:
    return bool(delegate_name in segment and f"_bys360_legacy_{public_name}" in segment)


def ensure_service_delegates(project_root: Path) -> Tuple[bool, Dict[str, List[str]]]:
    changed = False
    appended_by_service: Dict[str, List[str]] = {}
    service_root = project_root / "app" / "api" / "mobile" / "services"
    service_root.mkdir(parents=True, exist_ok=True)

    services: Dict[str, List[Tuple[str, str]]] = {}
    for public_name, meta in TARGETS.items():
        services.setdefault(meta["service"], []).append((public_name, meta["delegate"]))

    for service_name, items in services.items():
        service_path = service_root / f"{service_name}.py"
        if service_path.exists():
            text = read_text(service_path)
        else:
            text = f'# -*- coding: utf-8 -*-\n"""BYS360 mobile {service_name.replace("_", " ")} delegates."""\n\n'
        blocks: List[str] = []
        appended: List[str] = []
        if "def _run_legacy_route(" not in text:
            blocks.append(textwrap.dedent('''


def _run_legacy_route(legacy_fn, *args, **kwargs):
    """Run an extracted legacy route implementation without changing endpoint behavior."""
    return legacy_fn(*args, **kwargs)
'''))
            appended.append("_run_legacy_route")
        for public_name, delegate_name in items:
            if f"def {delegate_name}(" not in text:
                blocks.append(textwrap.dedent(f'''


def {delegate_name}(legacy_fn, *args, **kwargs):
    """Delegate wrapper for {public_name}; keeps route endpoint and URL stable."""
    return _run_legacy_route(legacy_fn, *args, **kwargs)
'''))
                appended.append(delegate_name)
        if blocks:
            text = text.rstrip() + "\n" + "".join(blocks).lstrip("\n") + "\n"
            write_text(service_path, text)
            changed = True
        appended_by_service[service_name] = appended
    return changed, appended_by_service


def patch_routes(routes_path: Path, project_root: Path) -> Dict[str, Any]:
    ok, err = syntax_ok(routes_path)
    if not ok:
        return {"changed": False, "error": f"routes.py syntax is not OK before patch: {err}", "delegated": {}}

    lines = read_text(routes_path).splitlines(keepends=True)
    functions = parse_functions(routes_path)
    delegated: Dict[str, bool] = {}
    skipped: Dict[str, str] = {}
    patches: List[Tuple[int, int, List[str], str]] = []

    for public_name, meta in TARGETS.items():
        delegate_name = meta["delegate"]
        service_name = meta["service"]
        fn = functions.get(public_name)
        if not fn:
            delegated[public_name] = False
            skipped[public_name] = "function_not_found"
            continue
        segment = "".join(lines[fn.lineno - 1 : fn.end_lineno or fn.lineno])
        if is_delegated(segment, public_name, delegate_name):
            delegated[public_name] = True
            skipped[public_name] = "already_delegated"
            continue
        if not fn.body:
            delegated[public_name] = False
            skipped[public_name] = "empty_function_body"
            continue
        first_body_idx = fn.body[0].lineno - 1
        end_idx = fn.end_lineno or first_body_idx + 1
        def_idx = fn.lineno - 1
        sig = lines[def_idx]
        if not re.search(rf"\bdef\s+{re.escape(public_name)}\s*\(", sig):
            delegated[public_name] = False
            skipped[public_name] = "unsupported_multiline_or_unexpected_signature"
            continue
        indent = leading_ws(lines[first_body_idx]) or "    "
        legacy_name = f"_bys360_legacy_{public_name}"
        legacy_sig = re.sub(rf"(\bdef\s+){re.escape(public_name)}(\s*\()", rf"\1{legacy_name}\2", sig, count=1)
        original_body = lines[first_body_idx:end_idx]
        params = ", ".join(function_params(fn))
        wrapper_body = [
            f"{indent}from app.api.mobile.services.{service_name} import {delegate_name}\n",
            f"{indent}return {delegate_name}({legacy_name}{', ' if params else ''}{params})\n",
        ]
        legacy_block = ["\n", legacy_sig] + original_body
        patches.append((first_body_idx, end_idx, wrapper_body + legacy_block, public_name))
        delegated[public_name] = True

    if not patches:
        return {"changed": False, "delegated": delegated, "skipped": skipped, "error": "no_patch_needed_or_no_supported_targets"}

    qroot = project_root / "_local_quarantine" / f"bys360_mobile_dashboard_profile_delegate_p1_4_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup = qroot / "app" / "api" / "mobile" / "routes.py.before_p1_4"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(routes_path, backup)

    for start, end, replacement, _public_name in sorted(patches, key=lambda x: x[0], reverse=True):
        lines[start:end] = replacement

    write_text(routes_path, "".join(lines))
    ok_after, err_after = syntax_ok(routes_path)
    if not ok_after:
        shutil.copy2(backup, routes_path)
        return {"changed": False, "delegated": delegated, "skipped": skipped, "error": f"syntax_failed_after_patch_rolled_back: {err_after}", "backup": str(backup.relative_to(project_root))}
    return {"changed": True, "delegated": delegated, "skipped": skipped, "backup": str(backup.relative_to(project_root)), "patched_functions": [p[3] for p in patches]}


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 180) -> Dict[str, Any]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout_tail": (p.stdout or "")[-5000:], "stderr_tail": (p.stderr or "")[-5000:]}
    except Exception as e:
        return {"ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": f"{e.__class__.__name__}: {e}"}


def health(project_root: Path) -> Dict[str, Any]:
    compile_res = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], project_root)
    app_res = run_cmd([sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], project_root)
    app_ok = bool(app_res["ok"] and "BYS360_APP_CREATE_OK" in app_res.get("stdout_tail", ""))
    return {"compileall_ok": bool(compile_res["ok"]), "app_factory_ok": app_ok, "overall_ok": bool(compile_res["ok"] and app_ok), "compileall": compile_res, "app_factory": app_res}


def audit(project_root: Path) -> Dict[str, Any]:
    routes_path = project_root / "app" / "api" / "mobile" / "routes.py"
    data: Dict[str, Any] = {"routes_exists": routes_path.exists(), "routes_syntax": syntax_ok(routes_path)[0] if routes_path.exists() else False, "functions": {}, "routes_kb": None, "routes_lines": None}
    if routes_path.exists():
        text = read_text(routes_path)
        data["routes_kb"] = round(routes_path.stat().st_size / 1024, 1)
        data["routes_lines"] = len(text.splitlines())
    if routes_path.exists() and data["routes_syntax"]:
        text = read_text(routes_path)
        lines = text.splitlines(keepends=True)
        funcs = parse_functions(routes_path)
        for public_name, meta in TARGETS.items():
            delegate_name = meta["delegate"]
            fn = funcs.get(public_name)
            seg = "".join(lines[fn.lineno-1:fn.end_lineno or fn.lineno]) if fn else ""
            data["functions"][public_name] = {"exists": fn is not None, "line": getattr(fn, "lineno", None), "group": meta["group"], "service": meta["service"], "delegated": bool(fn and is_delegated(seg, public_name, delegate_name)), "legacy_exists": f"def _bys360_legacy_{public_name}(" in text}
    return data


def write_reports(project_root: Path, result: Dict[str, Any]) -> Tuple[str, str]:
    reports = project_root / "reports" / "quality"
    reports.mkdir(parents=True, exist_ok=True)
    json_path = reports / f"{REPORT_STEM}_report.json"
    md_path = reports / f"{REPORT_STEM}_report.md"
    write_text(json_path, json.dumps(result, ensure_ascii=False, indent=2))
    audit_data = result.get("audit", {})
    apply_data = result.get("apply", {})
    health_data = result.get("health", {})
    lines = [
        "# BYS360 Mobile Dashboard/Profile Service Delegate P1.4 V2.17.10\n",
        "\nBu rapor mobil dashboard/profile aday route fonksiyonlarının URL/endpoint/blueprint bozulmadan servis delegasyonuna alınma sonucunu gösterir.\n",
        "\n## Durum\n",
        f"- mode: {result.get('mode')}\n",
        f"- routes_changed: {apply_data.get('routes_changed', False)}\n",
        f"- service_changed: {apply_data.get('service_changed', False)}\n",
        f"- routes_kb: {audit_data.get('routes_kb')}\n",
        f"- routes_lines: {audit_data.get('routes_lines')}\n",
        "\n## Fonksiyon Durumu\n",
        "| Fonksiyon | Grup | Servis | Var | Satır | Delegated | Legacy |\n",
        "|---|---|---|---:|---:|---:|---:|\n",
    ]
    funcs = (audit_data.get("functions") or {}) if isinstance(audit_data, dict) else {}
    for name in TARGETS:
        f = funcs.get(name, {})
        lines.append(f"| `{name}` | {f.get('group')} | `{f.get('service')}` | {f.get('exists')} | {f.get('line')} | {f.get('delegated')} | {f.get('legacy_exists')} |\n")
    lines += [
        "\n## Apply\n",
        f"- patched_functions: {apply_data.get('patched_functions', [])}\n",
        f"- backup: {apply_data.get('backup', '')}\n",
        f"- error: {apply_data.get('error', '')}\n",
        "\n## Sağlık Kontrolü\n",
        f"- compileall_ok: {health_data.get('compileall_ok')}\n",
        f"- app_factory_ok: {health_data.get('app_factory_ok')}\n",
        f"- overall_ok: {health_data.get('overall_ok')}\n",
        "\n## Not\n",
        "Bu adım URL/endpoint davranışını koruyarak servis delegasyonu yapar. Eksik fonksiyon adları güvenli şekilde atlanır.\n",
    ]
    write_text(md_path, "".join(lines))
    return str(json_path.relative_to(project_root)), str(md_path.relative_to(project_root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "apply", "health", "all"], default="audit")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    routes_path = project_root / "app" / "api" / "mobile" / "routes.py"
    service_apply: Dict[str, Any] = {"service_changed": False, "service_appended": {}}
    patch_apply: Dict[str, Any] = {"routes_changed": False}
    health_data: Dict[str, Any] = {}

    if args.mode in ("apply", "all"):
        svc_changed, svc_appended = ensure_service_delegates(project_root)
        service_apply = {"service_changed": svc_changed, "service_appended": svc_appended}
        patch = patch_routes(routes_path, project_root)
        patch_apply = {"routes_changed": patch.get("changed", False), **patch}
    if args.mode in ("health", "all"):
        health_data = health(project_root)

    audit_data = audit(project_root)
    result: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(project_root),
        "audit": audit_data,
        "apply": {**service_apply, **patch_apply},
        "health": health_data,
    }
    json_report, md_report = write_reports(project_root, result)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "routes_changed": result["apply"].get("routes_changed"),
        "service_changed": result["apply"].get("service_changed"),
        "patched_functions": result["apply"].get("patched_functions", []),
        "health_summary": {k: health_data.get(k) for k in ("compileall_ok", "app_factory_ok", "overall_ok")},
        "json_report": json_report,
        "md_report": md_report,
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4_V2_17_10_REPORT_OK")
    if args.mode in ("health", "all"):
        if health_data.get("overall_ok"):
            print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4_V2_17_10_HEALTH_OK")
        else:
            print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4_V2_17_10_HEALTH_FAIL")
            return 1
    if args.mode in ("apply", "all"):
        if result["apply"].get("error"):
            print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4_V2_17_10_APPLY_FAIL")
            return 1
        print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4_V2_17_10_APPLY_OK")
    print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4_V2_17_10_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
