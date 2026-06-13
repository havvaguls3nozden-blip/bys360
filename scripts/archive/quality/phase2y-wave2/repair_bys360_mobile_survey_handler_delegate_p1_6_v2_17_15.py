# -*- coding: utf-8 -*-
"""
BYS360 Mobile Survey Handler Delegate P1.6 V2.17.15

Güvenli mikro-refactor:
- app/api/mobile/routes.py içindeki survey/anket fonksiyonlarını URL, endpoint ve blueprint adı bozulmadan servis delegasyonuna alır.
- Eski gövdeleri _bys360_legacy_<fonksiyon> olarak routes.py içinde korur.
- app/api/mobile/services/survey_service.py içinde delegasyon fonksiyonları oluşturur.
- Hata halinde routes.py yedeğinden geri döner.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

VERSION = "V2.17.15"
PACKAGE = "BYS360_MOBILE_SURVEY_HANDLER_DELEGATE_P1_6_V2_17_15"

TARGET_NAMES = [
    "_mobile_survey_validate_answers",
    "_mobile_survey_detail_payload",
    "mobile_survey_submit",
]
# Also detect common route names without blindly patching everything.
OPTIONAL_NAME_PATTERNS = [
    re.compile(r"^mobile_survey_(list|detail|answer|answers|assigned|assignments|my|mine)$"),
    re.compile(r"^mobile_surveys(_.*)?$"),
]

IMPORT_LINE = "from app.api.mobile.services import survey_service"
SERVICE_REL = Path("app/api/mobile/services/survey_service.py")
ROUTES_REL = Path("app/api/mobile/routes.py")
REPORT_JSON_REL = Path("reports/quality/bys360_mobile_survey_handler_delegate_p1_6_v2_17_15_report.json")
REPORT_MD_REL = Path("reports/quality/bys360_mobile_survey_handler_delegate_p1_6_v2_17_15_report.md")


def _now_tag() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _run(cmd: List[str], cwd: Path, timeout: int = 120) -> Dict[str, Any]:
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
            "stdout_tail": (p.stdout or "")[-5000:],
            "stderr_tail": (p.stderr or "")[-5000:],
        }
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "returncode": -999, "stdout_tail": "", "stderr_tail": repr(exc)}


def health(project_root: Path) -> Dict[str, Any]:
    compile_res = _run([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], project_root, timeout=180)
    factory_res = _run(
        [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"],
        project_root,
        timeout=90,
    )
    return {
        "compileall_ok": bool(compile_res.get("ok")),
        "app_factory_ok": bool(factory_res.get("ok")) and "BYS360_APP_CREATE_OK" in (factory_res.get("stdout_tail") or ""),
        "overall_ok": bool(compile_res.get("ok")) and bool(factory_res.get("ok")) and "BYS360_APP_CREATE_OK" in (factory_res.get("stdout_tail") or ""),
        "compileall": compile_res,
        "app_factory": factory_res,
    }


def _get_source_segment(lines: List[str], start: int, end: int) -> str:
    # ast lineno/end_lineno are 1-based inclusive
    return "\n".join(lines[start - 1 : end]) + "\n"


def _first_block_line(node: ast.FunctionDef) -> int:
    if node.decorator_list:
        return min(d.lineno for d in node.decorator_list)
    return node.lineno


def _call_args(args: ast.arguments) -> str:
    parts: List[str] = []
    for a in list(args.posonlyargs) + list(args.args):
        parts.append(a.arg)
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    for a in args.kwonlyargs:
        parts.append(f"{a.arg}={a.arg}")
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    return ", ".join(parts)


def _signature_from_def_line(def_line: str, old_name: str, new_name: str) -> str:
    # Replace only the function name at the beginning of the def line, preserving signature and return annotation.
    return re.sub(rf"^(\s*)def\s+{re.escape(old_name)}\s*\(", rf"\1def {new_name}(", def_line, count=1)


def _is_target_name(name: str) -> bool:
    if name in TARGET_NAMES:
        return True
    return any(p.match(name) for p in OPTIONAL_NAME_PATTERNS)


def _has_survey_delegation(node: ast.FunctionDef) -> bool:
    # Simple textual / AST check: does function body call survey_service.<same_name>?
    try:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and sub.attr == node.name:
                val = sub.value
                if isinstance(val, ast.Name) and val.id == "survey_service":
                    return True
    except Exception:
        pass
    return False


def analyze_routes(project_root: Path) -> Dict[str, Any]:
    routes_path = project_root / ROUTES_REL
    if not routes_path.exists():
        return {"exists": False, "error": f"Dosya bulunamadı: {ROUTES_REL}"}
    text = routes_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
        syntax_ok = True
        syntax_error = ""
    except SyntaxError as exc:
        tree = None
        syntax_ok = False
        syntax_error = f"{exc}"
    functions = []
    if tree is not None:
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and _is_target_name(node.name):
                has_route = bool(node.decorator_list)
                delegated = _has_survey_delegation(node)
                legacy_exists = f"def _bys360_legacy_{node.name}(" in text
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "route_decorator": has_route,
                    "delegated": delegated,
                    "legacy": legacy_exists,
                    "arg": _call_args(node.args),
                    "patchable": not delegated and not legacy_exists,
                })
    return {
        "exists": True,
        "path": str(ROUTES_REL),
        "size_kb": round(routes_path.stat().st_size / 1024, 1),
        "line_count": len(lines),
        "syntax_ok": syntax_ok,
        "syntax_error": syntax_error,
        "candidate_count": len(functions),
        "delegated_count": sum(1 for f in functions if f["delegated"]),
        "patchable_count": sum(1 for f in functions if f["patchable"]),
        "functions": functions,
    }


def ensure_import(text: str) -> str:
    if IMPORT_LINE in text:
        return text
    lines = text.splitlines()
    insert_at = 0
    # After module docstring / __future__ imports / normal imports
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("from __future__") or stripped.startswith("import ") or stripped.startswith("from ") or stripped == "" or stripped.startswith("#"):
            insert_at = i + 1
            continue
        break
    lines.insert(insert_at, IMPORT_LINE)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def patch_routes(project_root: Path, analysis: Dict[str, Any], quarantine_root: Path) -> Dict[str, Any]:
    routes_path = project_root / ROUTES_REL
    text = routes_path.read_text(encoding="utf-8", errors="replace")
    original_text = text
    tree = ast.parse(text)
    lines = text.splitlines()
    nodes: Dict[str, ast.FunctionDef] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and _is_target_name(node.name):
            if not _has_survey_delegation(node) and f"def _bys360_legacy_{node.name}(" not in text:
                nodes[node.name] = node

    if not nodes:
        return {"changed": False, "patched_functions": [], "backup": "", "error": ""}

    backup_path = quarantine_root / ROUTES_REL.with_suffix(".py.before_p1_6")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(routes_path, backup_path)

    replacements: List[Tuple[int, int, str, str]] = []
    patched: List[str] = []
    for name, node in nodes.items():
        start = _first_block_line(node)
        end = int(getattr(node, "end_lineno", node.lineno))
        block = _get_source_segment(lines, start, end)
        block_lines = block.splitlines()
        # Separate decorators and def/body lines
        decorator_count = node.lineno - start
        decorator_lines = block_lines[:decorator_count]
        def_and_body = block_lines[decorator_count:]
        if not def_and_body:
            continue
        def_line = def_and_body[0]
        legacy_name = f"_bys360_legacy_{name}"
        legacy_def_line = _signature_from_def_line(def_line, name, legacy_name)
        legacy_block = "\n".join([legacy_def_line] + def_and_body[1:])
        call = _call_args(node.args)
        indent = re.match(r"^(\s*)", def_line).group(1) if re.match(r"^(\s*)", def_line) else ""
        public_lines = []
        public_lines.extend(decorator_lines)
        public_lines.append(def_line)
        public_lines.append(f"{indent}    return survey_service.{name}({call})" if call else f"{indent}    return survey_service.{name}()")
        new_block = "\n".join(public_lines) + "\n\n" + legacy_block + "\n"
        replacements.append((start, end, block, new_block))
        patched.append(name)

    # Replace from bottom to top by line numbers to avoid offset issues.
    new_text = text
    for start, end, old_block, new_block in sorted(replacements, key=lambda x: x[0], reverse=True):
        if old_block not in new_text:
            # Fallback line replacement
            cur_lines = new_text.splitlines()
            cur_lines[start - 1:end] = new_block.rstrip("\n").splitlines()
            new_text = "\n".join(cur_lines) + "\n"
        else:
            new_text = new_text.replace(old_block, new_block, 1)
    new_text = ensure_import(new_text)

    if new_text != original_text:
        routes_path.write_text(new_text, encoding="utf-8")
        return {"changed": True, "patched_functions": patched, "backup": str(backup_path.relative_to(project_root)), "error": ""}
    return {"changed": False, "patched_functions": [], "backup": str(backup_path.relative_to(project_root)), "error": "no text change"}


def patch_service(project_root: Path, patched_functions: List[str]) -> Dict[str, Any]:
    if not patched_functions:
        return {"path": str(SERVICE_REL), "changed": False, "delegate_count": 0}
    service_path = project_root / SERVICE_REL
    service_path.parent.mkdir(parents=True, exist_ok=True)
    if service_path.exists():
        text = service_path.read_text(encoding="utf-8", errors="replace")
    else:
        text = "# -*- coding: utf-8 -*-\n\"\"\"BYS360 mobile survey service delegates.\"\"\"\n\n"
    original = text
    if "def _call_legacy(" not in text:
        text += "\n\ndef _call_legacy(name, *args, **kwargs):\n    from app.api.mobile import routes as mobile_routes\n    legacy = getattr(mobile_routes, f'_bys360_legacy_{name}', None)\n    if legacy is None:\n        raise RuntimeError(f'Mobil survey legacy fonksiyonu bulunamadı: {name}')\n    return legacy(*args, **kwargs)\n"
    for name in patched_functions:
        if f"def {name}(" in text:
            continue
        # Use *args/**kwargs in service to remain robust against signature changes.
        text += f"\n\ndef {name}(*args, **kwargs):\n    return _call_legacy('{name}', *args, **kwargs)\n"
    changed = text != original
    if changed:
        service_path.write_text(text, encoding="utf-8")
    return {"path": str(SERVICE_REL), "changed": changed, "delegate_count": sum(1 for name in patched_functions if f"def {name}(" in text)}


def write_reports(project_root: Path, report: Dict[str, Any]) -> None:
    json_path = project_root / REPORT_JSON_REL
    md_path = project_root / REPORT_MD_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    a = report.get("audit", {})
    apply = report.get("apply", {})
    health_summary = report.get("health_summary", {})
    lines = [
        "# BYS360 Mobile Survey Handler Delegate P1.6 V2.17.15",
        "",
        "Bu rapor mobil anket/survey handler ve route fonksiyonlarının URL, endpoint ve blueprint adı korunarak servis delegasyonuna alınma sonucunu gösterir.",
        "",
        "## Durum",
        f"- mode: {report.get('mode')}",
        "",
        "## Audit",
        f"- candidate_count: {a.get('candidate_count')}",
        f"- delegated_count: {a.get('delegated_count')}",
        f"- patchable_count: {a.get('patchable_count')}",
        "",
        "| Fonksiyon | Satır | Route Decorator | Delegated | Legacy | Arg |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for f in a.get("functions", []):
        lines.append(f"| `{f.get('name')}` | {f.get('line')} | {f.get('route_decorator')} | {f.get('delegated')} | {f.get('legacy')} | `{f.get('arg')}` |")
    lines += [
        "",
        "## Apply",
        f"- routes_changed: {apply.get('routes', {}).get('changed')}",
        f"- service: `{apply.get('service')}`",
        f"- patched_functions: {apply.get('routes', {}).get('patched_functions')}",
        f"- backup: {apply.get('routes', {}).get('backup')}",
        f"- error: {apply.get('routes', {}).get('error')}",
        "",
        "## Sağlık Kontrolü",
        f"- compileall_ok: {health_summary.get('compileall_ok')}",
        f"- app_factory_ok: {health_summary.get('app_factory_ok')}",
        f"- overall_ok: {health_summary.get('overall_ok')}",
        "",
        "## Not",
        "Bu adım güvenli delegasyon adımıdır. Eski gövdeler legacy olarak korunur; gerçek satır azaltma daha sonraki taşıma fazında yapılmalıdır.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "all"], default="audit")
    ns = ap.parse_args()
    project_root = Path(ns.project_root).resolve()
    quarantine_root = project_root / "_local_quarantine" / f"bys360_mobile_survey_handler_delegate_p1_6_{_now_tag()}"

    audit = analyze_routes(project_root)
    report: Dict[str, Any] = {
        "version": VERSION,
        "package": PACKAGE,
        "mode": ns.mode,
        "project_root": str(project_root),
        "audit": audit,
        "apply": {},
        "health_summary": {},
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }

    exit_code = 0
    if ns.mode in ("apply", "all"):
        if not audit.get("syntax_ok", False):
            report["apply"] = {"error": "routes.py syntax_ok false; patch iptal"}
            exit_code = 1
        else:
            quarantine_root.mkdir(parents=True, exist_ok=True)
            routes_apply = patch_routes(project_root, audit, quarantine_root)
            service_apply = patch_service(project_root, routes_apply.get("patched_functions", []))
            report["apply"] = {"routes": routes_apply, "service": service_apply, "quarantine_root": str(quarantine_root.relative_to(project_root))}
            # Re-analyze after patch
            report["audit_after"] = analyze_routes(project_root)
            h = health(project_root)
            report["health_summary"] = {k: v for k, v in h.items() if k in ("compileall_ok", "app_factory_ok", "overall_ok")}
            report["health_detail"] = h
            if not h.get("overall_ok"):
                # rollback routes only if changed
                b = routes_apply.get("backup")
                if b:
                    backup_path = project_root / b
                    if backup_path.exists():
                        shutil.copy2(backup_path, project_root / ROUTES_REL)
                        report["rollback"] = {"routes_restored": True, "from": b}
                exit_code = 1
            elif not routes_apply.get("changed"):
                # No-op is not failure; it means already delegated or no safe candidate.
                exit_code = 0
    elif ns.mode == "audit":
        pass

    if ns.mode == "all" and not report.get("health_summary"):
        h = health(project_root)
        report["health_summary"] = {k: v for k, v in h.items() if k in ("compileall_ok", "app_factory_ok", "overall_ok")}
        report["health_detail"] = h
        if not h.get("overall_ok"):
            exit_code = 1

    write_reports(project_root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": ns.mode,
        "audit": report.get("audit"),
        "apply": report.get("apply"),
        "health_summary": report.get("health_summary"),
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }, ensure_ascii=False, indent=2))
    print(f"{PACKAGE}_REPORT_OK")
    if report.get("health_summary", {}).get("overall_ok"):
        print(f"{PACKAGE}_HEALTH_OK")
    if ns.mode in ("apply", "all"):
        routes_apply = report.get("apply", {}).get("routes", {}) if isinstance(report.get("apply"), dict) else {}
        if routes_apply.get("changed"):
            print(f"{PACKAGE}_APPLY_OK")
        else:
            print(f"{PACKAGE}_APPLY_NOOP")
    print(f"{PACKAGE}_OK")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
