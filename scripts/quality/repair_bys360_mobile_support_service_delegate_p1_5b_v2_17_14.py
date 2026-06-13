# -*- coding: utf-8 -*-
"""
BYS360 Mobile Support Handler Delegate P1.5B V2.17.14

Amaç:
- app/api/mobile/routes.py içindeki route decorator olmayan support handler fonksiyonlarını
  URL/endpoint/blueprint adlarına dokunmadan servis delegasyonuna almak.
- Eski gövde _bys360_legacy_<name> olarak korunur.
- Public fonksiyon service -> legacy zinciriyle çalışır.
- İşlem sonrası compileall ve create_app sağlık kontrolü yapılır.
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
from typing import Dict, List, Tuple

VERSION = "V2.17.14"
TARGETS = {
    "mobile_support_ticket_create": "app/api/mobile/services/support_service.py",
    "mobile_support_ticket_reply": "app/api/mobile/services/support_service.py",
}
IMPORT_LINE = "from app.api.mobile.services import support_service as _mobile_support_service"
REPORT_NAME = "bys360_mobile_support_handler_delegate_p1_5b_v2_17_14_report"


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def parse_module(path: Path):
    text = read_text(path)
    return text, ast.parse(text, filename=str(path))


def function_arg_names(node: ast.FunctionDef) -> List[str]:
    names: List[str] = []
    for arg in node.args.posonlyargs + node.args.args:
        names.append(arg.arg)
    # Bu mikro refactor sadece basit positional arg kullanan handlerlar icin tasarlandi.
    return names


def has_route_decorator(node: ast.FunctionDef) -> bool:
    for dec in node.decorator_list:
        s = ast.unparse(dec) if hasattr(ast, "unparse") else ""
        if ".route" in s or s.endswith("route") or "route(" in s:
            return True
    return False


def is_delegated(text: str, node: ast.FunctionDef) -> bool:
    segment = ast.get_source_segment(text, node) or ""
    return "_mobile_support_service." in segment and "_bys360_legacy_" in segment


def analyze(root: Path) -> Dict:
    routes = root / "app" / "api" / "mobile" / "routes.py"
    service = root / "app" / "api" / "mobile" / "services" / "support_service.py"
    result = {
        "version": VERSION,
        "routes_path": rel(routes, root),
        "service_path": rel(service, root),
        "targets": [],
        "missing_targets": [],
        "syntax_ok": False,
    }
    if not routes.exists():
        result["error"] = "routes.py bulunamadi"
        return result
    try:
        text, tree = parse_module(routes)
        result["syntax_ok"] = True
    except SyntaxError as exc:
        result["syntax_error"] = f"{exc}"
        return result
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    legacy_names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("_bys360_legacy_")}
    for name in TARGETS:
        node = functions.get(name)
        if not node:
            result["missing_targets"].append(name)
            continue
        args = function_arg_names(node)
        result["targets"].append({
            "name": name,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", None),
            "arg": ", ".join(args),
            "route_decorator": has_route_decorator(node),
            "delegated": is_delegated(text, node),
            "legacy_exists": f"_bys360_legacy_{name}" in legacy_names,
            "simple_def_line": read_text(routes).splitlines()[node.lineno - 1].lstrip().startswith(f"def {name}(") and read_text(routes).splitlines()[node.lineno - 1].rstrip().endswith(":"),
        })
    result["candidate_count"] = len(result["targets"])
    result["delegated_count"] = sum(1 for t in result["targets"] if t["delegated"])
    result["patchable_count"] = sum(1 for t in result["targets"] if (not t["delegated"] and t["simple_def_line"]))
    return result


def ensure_import(lines: List[str]) -> Tuple[List[str], bool]:
    text = "\n".join(lines)
    if IMPORT_LINE in text:
        return lines, False
    insert_at = 0
    in_doc = False
    # Basit ve güvenli: son top-level import satırından sonra ekle.
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            insert_at = i + 1
    lines.insert(insert_at, IMPORT_LINE)
    return lines, True


def make_public_function(def_line: str, args: List[str], name: str) -> str:
    indent = re.match(r"^(\s*)", def_line).group(1)
    call_args = ", ".join(args + [f"_bys360_legacy_{name}"])
    body_indent = indent + "    "
    return "\n".join([
        def_line.rstrip(),
        f"{body_indent}return _mobile_support_service.{name}({call_args})",
    ])


def patch_routes(root: Path) -> Dict:
    routes = root / "app" / "api" / "mobile" / "routes.py"
    text = read_text(routes)
    tree = ast.parse(text, filename=str(routes))
    nodes = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    lines = text.splitlines()
    patched: List[str] = []
    skipped: List[Dict] = []

    # Import eklemesi en bastan yapilir; satir indexleri kaymasin diye sonra tekrar parse edilir.
    lines, import_changed = ensure_import(lines)
    if import_changed:
        text = "\n".join(lines) + "\n"
        tree = ast.parse(text, filename=str(routes))
        nodes = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        lines = text.splitlines()

    replacements: List[Tuple[int, int, str]] = []
    existing_legacy = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    for name in TARGETS:
        node = nodes.get(name)
        if not node:
            skipped.append({"name": name, "reason": "fonksiyon bulunamadi"})
            continue
        if is_delegated(text, node):
            skipped.append({"name": name, "reason": "zaten delegated"})
            continue
        def_line = lines[node.lineno - 1]
        if not def_line.lstrip().startswith(f"def {name}(") or not def_line.rstrip().endswith(":"):
            skipped.append({"name": name, "reason": "basit tek satir def degil"})
            continue
        args = function_arg_names(node)
        public_src = make_public_function(def_line, args, name)
        legacy_name = f"_bys360_legacy_{name}"
        original_func_lines = lines[node.lineno - 1: node.end_lineno]
        if legacy_name not in existing_legacy:
            legacy_lines = original_func_lines.copy()
            legacy_lines[0] = re.sub(rf"def\s+{re.escape(name)}\s*\(", f"def {legacy_name}(", legacy_lines[0], count=1)
            replacement = public_src + "\n\n" + "\n".join(legacy_lines)
        else:
            replacement = public_src
        replacements.append((node.lineno - 1, node.end_lineno, replacement))
        patched.append(name)

    if not patched and not import_changed:
        return {"changed": False, "patched_functions": [], "skipped": skipped, "import_changed": False}

    # Tersten uygula ki indexler bozulmasin.
    for start, end, replacement in sorted(replacements, key=lambda x: x[0], reverse=True):
        lines[start:end] = replacement.splitlines()
    new_text = "\n".join(lines) + "\n"
    ast.parse(new_text, filename=str(routes))

    qroot = root / "_local_quarantine" / f"bys360_mobile_support_handler_delegate_p1_5b_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup = qroot / "app" / "api" / "mobile" / "routes.py.before_p1_5b"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(routes, backup)
    write_text(routes, new_text)
    return {"changed": True, "patched_functions": patched, "skipped": skipped, "backup": rel(backup, root), "import_changed": import_changed}


def ensure_service(root: Path) -> Dict:
    service = root / "app" / "api" / "mobile" / "services" / "support_service.py"
    existing = read_text(service) if service.exists() else ""
    changed = False
    addition_parts = []
    if "def mobile_support_ticket_create(" not in existing:
        addition_parts.append('''\n\ndef mobile_support_ticket_create(user, legacy_handler):\n    """Delegated mobile support ticket creation handler."""\n    return legacy_handler(user)\n''')
        changed = True
    if "def mobile_support_ticket_reply(" not in existing:
        addition_parts.append('''\n\ndef mobile_support_ticket_reply(user, ticket_id, legacy_handler):\n    """Delegated mobile support ticket reply handler."""\n    return legacy_handler(user, ticket_id)\n''')
        changed = True
    if changed:
        if not existing.strip():
            existing = '"""BYS360 mobile support service delegates."""\n'
        write_text(service, existing.rstrip() + "\n" + "\n".join(addition_parts).strip() + "\n")
    ast.parse(read_text(service), filename=str(service))
    return {"path": rel(service, root), "changed": changed}


def run_cmd(root: Path, cmd: List[str], timeout: int = 120) -> Dict:
    try:
        p = subprocess.run(
            cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout_tail": (p.stdout or "")[-4000:],
            "stderr_tail": (p.stderr or "")[-4000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": repr(exc)}


def health(root: Path) -> Dict:
    compileall = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=180)
    factory = run_cmd(root, [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], timeout=120)
    return {
        "compileall_ok": compileall["ok"],
        "app_factory_ok": factory["ok"] and "BYS360_APP_CREATE_OK" in (factory["stdout_tail"] + factory["stderr_tail"]),
        "overall_ok": compileall["ok"] and factory["ok"] and "BYS360_APP_CREATE_OK" in (factory["stdout_tail"] + factory["stderr_tail"]),
        "compileall": compileall,
        "app_factory": factory,
    }


def write_report(root: Path, report: Dict) -> None:
    outdir = root / "reports" / "quality"
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / f"{REPORT_NAME}.json"
    md_path = outdir / f"{REPORT_NAME}.md"
    write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))
    lines = [
        "# BYS360 Mobile Support Handler Delegate P1.5B V2.17.14",
        "",
        "Bu rapor route decorator olmayan mobil destek handler fonksiyonlarının servis delegasyonu sonucunu gösterir.",
        "",
        "## Durum",
        f"- mode: {report.get('mode')}",
        "",
        "## Audit",
        f"- candidate_count: {report.get('audit', {}).get('candidate_count')}",
        f"- delegated_count: {report.get('audit', {}).get('delegated_count')}",
        f"- patchable_count: {report.get('audit', {}).get('patchable_count')}",
        "",
        "| Fonksiyon | Satır | Route Decorator | Delegated | Legacy | Arg |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for t in report.get("audit", {}).get("targets", []):
        lines.append(f"| `{t['name']}` | {t['line']} | {t['route_decorator']} | {t['delegated']} | {t['legacy_exists']} | `{t['arg']}` |")
    lines += ["", "## Apply"]
    apply = report.get("apply", {})
    for k in ["routes", "service"]:
        if k in apply:
            lines.append(f"- {k}: `{apply[k]}`")
    lines.append(f"- patched_functions: {apply.get('routes_apply', {}).get('patched_functions', [])}")
    lines.append(f"- skipped: {apply.get('routes_apply', {}).get('skipped', [])}")
    if apply.get('routes_apply', {}).get('backup'):
        lines.append(f"- backup: {apply.get('routes_apply', {}).get('backup')}")
    hs = report.get("health_summary", {})
    lines += [
        "", "## Sağlık Kontrolü",
        f"- compileall_ok: {hs.get('compileall_ok')}",
        f"- app_factory_ok: {hs.get('app_factory_ok')}",
        f"- overall_ok: {hs.get('overall_ok')}",
    ]
    write_text(md_path, "\n".join(lines) + "\n")
    report["json_report"] = rel(json_path, root)
    report["md_report"] = rel(md_path, root)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "all"], default="audit")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    report: Dict = {"version": VERSION, "mode": args.mode, "project_root": str(root)}
    report["audit"] = analyze(root)
    if args.mode in {"apply", "all"}:
        try:
            service_apply = ensure_service(root)
            routes_apply = patch_routes(root)
            report["apply"] = {
                "service": service_apply,
                "routes_apply": routes_apply,
                "routes_changed": bool(routes_apply.get("changed")),
                "service_changed": bool(service_apply.get("changed")),
            }
        except Exception as exc:
            report["apply"] = {"error": repr(exc)}
    if args.mode in {"apply", "all"}:
        report["health_summary"] = health(root)
    else:
        report["health_summary"] = {}
    write_report(root, report)
    print(json.dumps({
        "version": report["version"],
        "mode": report["mode"],
        "audit": report["audit"],
        "apply": report.get("apply", {}),
        "health_summary": {k: v for k, v in report.get("health_summary", {}).items() if k in {"compileall_ok", "app_factory_ok", "overall_ok"}},
        "json_report": report.get("json_report"),
        "md_report": report.get("md_report"),
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_SUPPORT_HANDLER_DELEGATE_P1_5B_V2_17_14_REPORT_OK")
    hs = report.get("health_summary") or {}
    if args.mode in {"apply", "all"}:
        if hs.get("overall_ok"):
            print("BYS360_MOBILE_SUPPORT_HANDLER_DELEGATE_P1_5B_V2_17_14_HEALTH_OK")
            if report.get("apply", {}).get("routes_changed"):
                print("BYS360_MOBILE_SUPPORT_HANDLER_DELEGATE_P1_5B_V2_17_14_APPLY_OK")
            else:
                print("BYS360_MOBILE_SUPPORT_HANDLER_DELEGATE_P1_5B_V2_17_14_APPLY_NOOP")
            print("BYS360_MOBILE_SUPPORT_HANDLER_DELEGATE_P1_5B_V2_17_14_OK")
            return 0
        print("BYS360_MOBILE_SUPPORT_HANDLER_DELEGATE_P1_5B_V2_17_14_HEALTH_FAIL")
        return 1
    print("BYS360_MOBILE_SUPPORT_HANDLER_DELEGATE_P1_5B_V2_17_14_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
