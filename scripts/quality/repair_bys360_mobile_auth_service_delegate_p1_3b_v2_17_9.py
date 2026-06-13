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
from typing import Dict, List, Tuple, Any

VERSION = "V2.17.9"
TARGETS = {
    "mobile_login": "delegate_mobile_login",
    "mobile_refresh": "delegate_mobile_refresh",
    "mobile_me": "delegate_mobile_me",
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


def is_delegated(text: str, public_name: str, delegate_name: str) -> bool:
    return delegate_name in text and f"_bys360_legacy_{public_name}" in text


def ensure_service_delegates(service_path: Path) -> Tuple[bool, List[str]]:
    service_path.parent.mkdir(parents=True, exist_ok=True)
    if service_path.exists():
        text = read_text(service_path)
    else:
        text = '# -*- coding: utf-8 -*-\n"""Mobile auth service delegates."""\n\n'

    appended: List[str] = []
    blocks: List[str] = []
    if "def _run_legacy_route(" not in text:
        blocks.append(textwrap.dedent('''


def _run_legacy_route(legacy_fn, *args, **kwargs):
    """Run an extracted legacy route implementation without changing endpoint behavior."""
    return legacy_fn(*args, **kwargs)
'''))
        appended.append("_run_legacy_route")

    for public_name, delegate_name in TARGETS.items():
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
        return True, appended
    return False, appended


def patch_routes(routes_path: Path, project_root: Path) -> Dict[str, Any]:
    ok, err = syntax_ok(routes_path)
    if not ok:
        return {"changed": False, "error": f"routes.py syntax is not OK before patch: {err}", "delegated": {}}

    lines = read_text(routes_path).splitlines(keepends=True)
    functions = parse_functions(routes_path)
    delegated: Dict[str, bool] = {}
    skipped: Dict[str, str] = {}
    patches: List[Tuple[int, int, List[str], str]] = []

    for public_name, delegate_name in TARGETS.items():
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
            f"{indent}from app.api.mobile.services.auth_service import {delegate_name}\n",
            f"{indent}return {delegate_name}({legacy_name}{', ' if params else ''}{params})\n",
        ]
        legacy_block = ["\n", legacy_sig] + original_body
        patches.append((first_body_idx, end_idx, wrapper_body + legacy_block, public_name))
        delegated[public_name] = True

    if not patches:
        return {"changed": False, "delegated": delegated, "skipped": skipped, "error": "no_patch_needed_or_no_supported_targets"}

    qroot = project_root / "_local_quarantine" / f"bys360_mobile_auth_delegate_p1_3b_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup = qroot / "app" / "api" / "mobile" / "routes.py.before_p1_3b"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(routes_path, backup)

    for start, end, replacement, public_name in sorted(patches, key=lambda x: x[0], reverse=True):
        lines[start:end] = replacement

    write_text(routes_path, "".join(lines))
    ok_after, err_after = syntax_ok(routes_path)
    if not ok_after:
        shutil.copy2(backup, routes_path)
        return {
            "changed": False,
            "delegated": delegated,
            "skipped": skipped,
            "error": f"syntax_failed_after_patch_rolled_back: {err_after}",
            "backup": str(backup.relative_to(project_root)),
        }
    return {
        "changed": True,
        "delegated": delegated,
        "skipped": skipped,
        "backup": str(backup.relative_to(project_root)),
        "patched_functions": [p[3] for p in patches],
    }


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 120) -> Dict[str, Any]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout_tail": (p.stdout or "")[-4000:], "stderr_tail": (p.stderr or "")[-4000:]}
    except Exception as e:
        return {"ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": f"{e.__class__.__name__}: {e}"}


def health(project_root: Path) -> Dict[str, Any]:
    compile_res = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], project_root, timeout=180)
    app_res = run_cmd([sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], project_root, timeout=180)
    app_ok = bool(app_res["ok"] and "BYS360_APP_CREATE_OK" in app_res.get("stdout_tail", ""))
    return {"compileall_ok": bool(compile_res["ok"]), "app_factory_ok": app_ok, "overall_ok": bool(compile_res["ok"] and app_ok), "compileall": compile_res, "app_factory": app_res}


def audit(project_root: Path) -> Dict[str, Any]:
    routes_path = project_root / "app" / "api" / "mobile" / "routes.py"
    service_path = project_root / "app" / "api" / "mobile" / "services" / "auth_service.py"
    data: Dict[str, Any] = {"routes_exists": routes_path.exists(), "service_exists": service_path.exists(), "routes_syntax": syntax_ok(routes_path)[0] if routes_path.exists() else False, "service_syntax": syntax_ok(service_path)[0] if service_path.exists() else False, "functions": {}}
    if routes_path.exists() and data["routes_syntax"]:
        text = read_text(routes_path)
        lines = text.splitlines(keepends=True)
        funcs = parse_functions(routes_path)
        for public_name, delegate_name in TARGETS.items():
            fn = funcs.get(public_name)
            seg = "".join(lines[fn.lineno-1:fn.end_lineno or fn.lineno]) if fn else ""
            data["functions"][public_name] = {"exists": fn is not None, "line": getattr(fn, "lineno", None), "delegated": bool(fn and is_delegated(seg, public_name, delegate_name)), "legacy_exists": f"def _bys360_legacy_{public_name}(" in text}
    return data


def write_reports(project_root: Path, result: Dict[str, Any]) -> Tuple[str, str]:
    reports = project_root / "reports" / "quality"
    reports.mkdir(parents=True, exist_ok=True)
    json_path = reports / "bys360_mobile_auth_service_delegate_p1_3b_v2_17_9_report.json"
    md_path = reports / "bys360_mobile_auth_service_delegate_p1_3b_v2_17_9_report.md"
    write_text(json_path, json.dumps(result, ensure_ascii=False, indent=2))
    audit_data = result.get("audit", {})
    apply_data = result.get("apply", {})
    health_data = result.get("health", {})
    lines = [
        "# BYS360 Mobile Auth Service Delegate P1.3B V2.17.9\n",
        "\nBu rapor route URL/endpoint/blueprint adlarını değiştirmeden auth route fonksiyonlarını servis delegasyonuna alma sonucunu gösterir.\n",
        "\n## Durum\n",
        f"- mode: {result.get('mode')}\n",
        f"- routes_changed: {apply_data.get('routes_changed', False)}\n",
        f"- service_changed: {apply_data.get('service_changed', False)}\n",
        "\n## Fonksiyon Durumu\n",
        "| Fonksiyon | Var | Satır | Delegated | Legacy |\n",
        "|---|---:|---:|---:|---:|\n",
    ]
    funcs = (audit_data.get("functions") or {}) if isinstance(audit_data, dict) else {}
    for name in TARGETS:
        f = funcs.get(name, {})
        lines.append(f"| `{name}` | {f.get('exists')} | {f.get('line')} | {f.get('delegated')} | {f.get('legacy_exists')} |\n")
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
        "Bu adım route dosyasının işleyişini korur. Gerçek satır azaltma için sonraki adımda izole helper fonksiyonları servis dosyalarına taşınmalıdır.\n",
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
    service_path = project_root / "app" / "api" / "mobile" / "services" / "auth_service.py"
    result: Dict[str, Any] = {"version": VERSION, "mode": args.mode, "project_root": str(project_root)}
    if args.mode in {"audit", "all"}:
        result["audit"] = audit(project_root)
    if args.mode in {"apply", "all"}:
        service_changed, appended = ensure_service_delegates(service_path)
        patch_result = patch_routes(routes_path, project_root)
        result["apply"] = {"service_changed": service_changed, "service_appended": appended, "routes_changed": patch_result.get("changed", False), **patch_result}
        result["audit"] = audit(project_root)
    if args.mode in {"health", "all"}:
        result["health"] = health(project_root)
    json_report, md_report = write_reports(project_root, result)
    result["json_report"] = json_report
    result["md_report"] = md_report
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3B_V2_17_9_REPORT_OK")
    if args.mode in {"health", "all"}:
        if not result.get("health", {}).get("overall_ok"):
            return 1
        print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3B_V2_17_9_HEALTH_OK")
    if args.mode in {"apply", "all"}:
        if result.get("apply", {}).get("error"):
            return 1
        print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3B_V2_17_9_APPLY_OK")
    print("BYS360_MOBILE_AUTH_SERVICE_DELEGATE_P1_3B_V2_17_9_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
