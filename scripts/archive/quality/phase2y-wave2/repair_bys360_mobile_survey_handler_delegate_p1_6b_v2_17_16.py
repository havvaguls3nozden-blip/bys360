# -*- coding: utf-8 -*-
"""
BYS360 Mobile Survey Handler Delegate P1.6B V2.17.16

Amaç:
- P1.6 sonrası oluşabilecek compileall_ok=False durumunu güvenli şekilde teşhis etmek.
- Gerekirse routes.py dosyasını son P1.6 yedeğinden geri almak.
- survey_service.py dosyasını güvenli, söz dizimi sağlam delegasyon shim'i olarak düzeltmek.
- Survey fonksiyonlarını tek tek, geri alınabilir şekilde servis delegasyonuna almak.
- URL / endpoint / blueprint adlarını değiştirmemek.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import py_compile
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "V2.17.16"
PACKAGE = "BYS360_MOBILE_SURVEY_HANDLER_DELEGATE_P1_6B_V2_17_16"
ROUTES_REL = Path("app/api/mobile/routes.py")
SERVICE_REL = Path("app/api/mobile/services/survey_service.py")
REPORT_JSON_REL = Path("reports/quality/bys360_mobile_survey_handler_delegate_p1_6b_v2_17_16_report.json")
REPORT_MD_REL = Path("reports/quality/bys360_mobile_survey_handler_delegate_p1_6b_v2_17_16_report.md")
IMPORT_LINE = "from app.api.mobile.services import survey_service"
TARGET_NAMES = [
    "_mobile_survey_detail_payload",
    "_mobile_survey_validate_answers",
    "mobile_survey_submit",
]


def now_tag() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 180) -> Dict[str, Any]:
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
            "stdout_tail": (p.stdout or "")[-6000:],
            "stderr_tail": (p.stderr or "")[-6000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -999, "stdout_tail": "", "stderr_tail": repr(exc)}


def py_compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": f"not found: {path}"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": repr(exc)}


def health(project_root: Path) -> Dict[str, Any]:
    target_compile = {
        "routes_py": py_compile_file(project_root / ROUTES_REL),
        "survey_service_py": py_compile_file(project_root / SERVICE_REL),
    }
    compile_res = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], project_root, timeout=240)
    factory_res = run_cmd(
        [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"],
        project_root,
        timeout=120,
    )
    factory_ok = bool(factory_res.get("ok")) and "BYS360_APP_CREATE_OK" in (factory_res.get("stdout_tail") or "")
    return {
        "target_compile": target_compile,
        "compileall_ok": bool(compile_res.get("ok")),
        "app_factory_ok": factory_ok,
        "overall_ok": bool(compile_res.get("ok")) and factory_ok,
        "compileall": compile_res,
        "app_factory": factory_res,
    }


def call_args(args: ast.arguments) -> str:
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


def first_block_line(node: ast.FunctionDef) -> int:
    if node.decorator_list:
        return min(d.lineno for d in node.decorator_list)
    return node.lineno


def has_delegation(node: ast.FunctionDef, service_name: str = "survey_service") -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and sub.attr == node.name:
            val = sub.value
            if isinstance(val, ast.Name) and val.id == service_name:
                return True
    return False


def function_records(project_root: Path) -> Dict[str, Any]:
    path = project_root / ROUTES_REL
    if not path.exists():
        return {"exists": False, "error": f"Dosya bulunamadı: {ROUTES_REL}", "functions": []}
    text = read_text(path)
    try:
        tree = ast.parse(text)
        syntax_ok = True
        syntax_error = ""
    except SyntaxError as exc:
        return {
            "exists": True,
            "path": str(ROUTES_REL),
            "syntax_ok": False,
            "syntax_error": str(exc),
            "functions": [],
            "size_kb": round(path.stat().st_size / 1024, 1),
            "line_count": len(text.splitlines()),
        }
    funcs: List[Dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in TARGET_NAMES:
            legacy_name = f"_bys360_legacy_{node.name}"
            funcs.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "route_decorator": bool(node.decorator_list),
                "delegated": has_delegation(node),
                "legacy": f"def {legacy_name}(" in text,
                "arg": call_args(node.args),
                "patchable": (not has_delegation(node)) and (f"def {legacy_name}(" not in text),
            })
    return {
        "exists": True,
        "path": str(ROUTES_REL),
        "syntax_ok": syntax_ok,
        "syntax_error": syntax_error,
        "size_kb": round(path.stat().st_size / 1024, 1),
        "line_count": len(text.splitlines()),
        "candidate_count": len(funcs),
        "delegated_count": sum(1 for f in funcs if f["delegated"]),
        "legacy_count": sum(1 for f in funcs if f["legacy"]),
        "patchable_count": sum(1 for f in funcs if f["patchable"]),
        "functions": funcs,
    }


def latest_p16_backup(project_root: Path) -> Optional[Path]:
    q = project_root / "_local_quarantine"
    if not q.exists():
        return None
    candidates = sorted(q.glob("bys360_mobile_survey_handler_delegate_p1_6_*/app/api/mobile/routes.py.before_p1_6"), reverse=True)
    for p in candidates:
        if p.exists():
            return p
    return None


def ensure_import(text: str) -> str:
    if IMPORT_LINE in text:
        return text
    lines = text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s == "" or s.startswith("#") or s.startswith("from __future__") or s.startswith("import ") or s.startswith("from "):
            insert_at = i + 1
            continue
        break
    lines.insert(insert_at, IMPORT_LINE)
    return "\n".join(lines) + "\n"


def sig_replace(def_line: str, old_name: str, new_name: str) -> str:
    return re.sub(rf"^(\s*)def\s+{re.escape(old_name)}\s*\(", rf"\1def {new_name}(", def_line, count=1)


def rewrite_safe_service(project_root: Path, backup_root: Path) -> Dict[str, Any]:
    path = project_root / SERVICE_REL
    old = read_text(path) if path.exists() else ""
    if path.exists():
        b = backup_root / SERVICE_REL.with_suffix(".py.before_p1_6b")
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, b)
    content = '''# -*- coding: utf-8 -*-
"""BYS360 mobile survey service delegates.

Bu dosya mobil survey handler delegasyonu için güvenli shim katmanıdır.
Route/endpoint isimleri değişmez; gerçek eski gövdeler routes.py içindeki
_bys360_legacy_* fonksiyonlarında korunur.
"""
from __future__ import annotations

from typing import Any


def _call_legacy(name: str, *args: Any, **kwargs: Any) -> Any:
    from app.api.mobile import routes as mobile_routes
    legacy = getattr(mobile_routes, f"_bys360_legacy_{name}", None)
    if legacy is None:
        raise RuntimeError(f"Mobil survey legacy fonksiyonu bulunamadı: {name}")
    return legacy(*args, **kwargs)


def _mobile_survey_detail_payload(*args: Any, **kwargs: Any) -> Any:
    return _call_legacy("_mobile_survey_detail_payload", *args, **kwargs)


def _mobile_survey_validate_answers(*args: Any, **kwargs: Any) -> Any:
    return _call_legacy("_mobile_survey_validate_answers", *args, **kwargs)


def mobile_survey_submit(*args: Any, **kwargs: Any) -> Any:
    return _call_legacy("mobile_survey_submit", *args, **kwargs)
'''
    if old != content:
        write_text(path, content)
        return {"path": str(SERVICE_REL), "changed": True, "delegate_count": 3}
    return {"path": str(SERVICE_REL), "changed": False, "delegate_count": 3}


def patch_one_function(project_root: Path, name: str) -> Dict[str, Any]:
    path = project_root / ROUTES_REL
    text = read_text(path)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"name": name, "changed": False, "error": f"routes syntax error: {exc}"}
    node: Optional[ast.FunctionDef] = None
    for item in tree.body:
        if isinstance(item, ast.FunctionDef) and item.name == name:
            node = item
            break
    if node is None:
        return {"name": name, "changed": False, "skipped": "function not found"}
    if has_delegation(node):
        return {"name": name, "changed": False, "skipped": "already delegated"}
    legacy_name = f"_bys360_legacy_{name}"
    if f"def {legacy_name}(" in text:
        return {"name": name, "changed": False, "skipped": "legacy already exists without delegation"}

    lines = text.splitlines()
    start = first_block_line(node)
    end = int(getattr(node, "end_lineno", node.lineno))
    block_lines = lines[start - 1:end]
    decorator_count = node.lineno - start
    decorators = block_lines[:decorator_count]
    def_body = block_lines[decorator_count:]
    if not def_body:
        return {"name": name, "changed": False, "error": "empty def/body block"}
    def_line = def_body[0]
    indent_match = re.match(r"^(\s*)", def_line)
    indent = indent_match.group(1) if indent_match else ""
    args = call_args(node.args)
    legacy_def = sig_replace(def_line, name, legacy_name)
    public_lines: List[str] = []
    public_lines.extend(decorators)
    public_lines.append(def_line)
    call = f"survey_service.{name}({args})" if args else f"survey_service.{name}()"
    public_lines.append(f"{indent}    return {call}")
    legacy_block = "\n".join([legacy_def] + def_body[1:])
    new_block = "\n".join(public_lines) + "\n\n" + legacy_block

    new_lines = lines[:start - 1] + new_block.splitlines() + lines[end:]
    new_text = ensure_import("\n".join(new_lines) + "\n")
    write_text(path, new_text)
    return {"name": name, "changed": True, "legacy": legacy_name}


def repair_failed_previous_state(project_root: Path, backup_root: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {"routes_restored": False, "service_rewritten": False, "notes": []}
    routes_path = project_root / ROUTES_REL
    service_path = project_root / SERVICE_REL
    routes_compile = py_compile_file(routes_path)
    service_compile = py_compile_file(service_path)
    result["before_target_compile"] = {"routes": routes_compile, "survey_service": service_compile}
    if not routes_compile.get("ok"):
        backup = latest_p16_backup(project_root)
        if backup and backup.exists():
            dest_backup = backup_root / ROUTES_REL.with_suffix(".py.before_p1_6b_restore")
            dest_backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(routes_path, dest_backup)
            shutil.copy2(backup, routes_path)
            result["routes_restored"] = True
            result["routes_restored_from"] = str(backup.relative_to(project_root)) if backup.is_relative_to(project_root) else str(backup)
        else:
            result["notes"].append("routes.py syntax hatalı ama P1.6 yedeği bulunamadı")
    # Always rewrite service to known-good shim if it is missing, broken, or contains unsafe duplicate fragments.
    if (not service_path.exists()) or (not service_compile.get("ok")) or "Mobil survey legacy fonksiyonu" not in read_text(service_path):
        svc = rewrite_safe_service(project_root, backup_root)
        result["service_rewritten"] = bool(svc.get("changed"))
        result["service"] = svc
    result["after_target_compile"] = {
        "routes": py_compile_file(routes_path),
        "survey_service": py_compile_file(service_path),
    }
    return result


def apply(project_root: Path, backup_root: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {"rescue": {}, "service": {}, "patched_functions": [], "skipped": [], "errors": []}
    backup_root.mkdir(parents=True, exist_ok=True)
    # Save state before P1.6B.
    routes_snapshot = backup_root / ROUTES_REL.with_suffix(".py.before_p1_6b")
    service_snapshot = backup_root / SERVICE_REL.with_suffix(".py.before_p1_6b")
    routes_snapshot.parent.mkdir(parents=True, exist_ok=True)
    service_snapshot.parent.mkdir(parents=True, exist_ok=True)
    if (project_root / ROUTES_REL).exists():
        shutil.copy2(project_root / ROUTES_REL, routes_snapshot)
    if (project_root / SERVICE_REL).exists():
        shutil.copy2(project_root / SERVICE_REL, service_snapshot)

    out["rescue"] = repair_failed_previous_state(project_root, backup_root)
    out["service"] = rewrite_safe_service(project_root, backup_root)

    for name in TARGET_NAMES:
        before_routes = read_text(project_root / ROUTES_REL)
        before_service = read_text(project_root / SERVICE_REL) if (project_root / SERVICE_REL).exists() else ""
        patch_res = patch_one_function(project_root, name)
        if patch_res.get("changed"):
            # Validate target files immediately. If not valid, rollback this one function only.
            r_ok = py_compile_file(project_root / ROUTES_REL).get("ok")
            s_ok = py_compile_file(project_root / SERVICE_REL).get("ok")
            if r_ok and s_ok:
                out["patched_functions"].append(name)
            else:
                write_text(project_root / ROUTES_REL, before_routes)
                write_text(project_root / SERVICE_REL, before_service)
                patch_res["rolled_back"] = True
                patch_res["target_compile_after_patch"] = {
                    "routes": py_compile_file(project_root / ROUTES_REL),
                    "survey_service": py_compile_file(project_root / SERVICE_REL),
                }
                out["errors"].append(patch_res)
        else:
            out["skipped"].append(patch_res)

    # Final full health. If full health fails, restore snapshots to protect the project.
    h = health(project_root)
    out["health_after_apply"] = {k: v for k, v in h.items() if k in ("compileall_ok", "app_factory_ok", "overall_ok", "target_compile")}
    if not h.get("overall_ok"):
        if routes_snapshot.exists():
            shutil.copy2(routes_snapshot, project_root / ROUTES_REL)
        if service_snapshot.exists():
            shutil.copy2(service_snapshot, project_root / SERVICE_REL)
        out["full_rollback"] = True
        out["health_after_full_rollback"] = {k: v for k, v in health(project_root).items() if k in ("compileall_ok", "app_factory_ok", "overall_ok", "target_compile")}
    else:
        out["full_rollback"] = False
    return out


def write_reports(project_root: Path, report: Dict[str, Any]) -> None:
    json_path = project_root / REPORT_JSON_REL
    md_path = project_root / REPORT_MD_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = report.get("audit", {})
    apply_info = report.get("apply", {})
    health_summary = report.get("health_summary", {})
    lines: List[str] = []
    lines.append("# BYS360 Mobile Survey Handler Delegate P1.6B V2.17.16")
    lines.append("")
    lines.append("Bu rapor P1.6 sonrası oluşan compile durumunu temizler ve survey delegasyonunu tek tek güvenli şekilde uygular.")
    lines.append("")
    lines.append("## Durum")
    lines.append(f"- mode: {report.get('mode')}")
    lines.append("")
    lines.append("## Audit")
    lines.append(f"- candidate_count: {audit.get('candidate_count')}")
    lines.append(f"- delegated_count: {audit.get('delegated_count')}")
    lines.append(f"- patchable_count: {audit.get('patchable_count')}")
    lines.append("")
    lines.append("| Fonksiyon | Satır | Route Decorator | Delegated | Legacy | Arg |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for f in audit.get("functions", []):
        lines.append(f"| `{f.get('name')}` | {f.get('line')} | {f.get('route_decorator')} | {f.get('delegated')} | {f.get('legacy')} | `{f.get('arg')}` |")
    lines.append("")
    lines.append("## Apply")
    if apply_info:
        lines.append(f"- rescue: `{apply_info.get('rescue')}`")
        lines.append(f"- service: `{apply_info.get('service')}`")
        lines.append(f"- patched_functions: {apply_info.get('patched_functions')}")
        lines.append(f"- skipped: {apply_info.get('skipped')}")
        lines.append(f"- errors: {apply_info.get('errors')}")
        lines.append(f"- full_rollback: {apply_info.get('full_rollback')}")
    else:
        lines.append("- uygulanmadı")
    lines.append("")
    lines.append("## Sağlık Kontrolü")
    lines.append(f"- compileall_ok: {health_summary.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {health_summary.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {health_summary.get('overall_ok')}")
    lines.append("")
    md_path = project_root / REPORT_MD_REL
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "apply", "all"], default="audit")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    backup_root = project_root / "_local_quarantine" / f"bys360_mobile_survey_handler_delegate_p1_6b_{now_tag()}"

    audit = function_records(project_root)
    report: Dict[str, Any] = {
        "version": VERSION,
        "package": PACKAGE,
        "mode": args.mode,
        "project_root": str(project_root),
        "audit": audit,
        "apply": {},
        "health_summary": {},
        "health_detail": {},
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }
    exit_code = 0

    if args.mode in ("apply", "all"):
        report["apply"] = apply(project_root, backup_root)
        report["audit_after"] = function_records(project_root)

    if args.mode in ("all", "apply"):
        h = health(project_root)
        report["health_summary"] = {k: v for k, v in h.items() if k in ("compileall_ok", "app_factory_ok", "overall_ok")}
        report["health_detail"] = h
        if not h.get("overall_ok"):
            exit_code = 1
    elif args.mode == "audit":
        h = health(project_root)
        report["health_summary"] = {k: v for k, v in h.items() if k in ("compileall_ok", "app_factory_ok", "overall_ok")}
        report["health_detail"] = {"target_compile": h.get("target_compile")}

    write_reports(project_root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "audit": report.get("audit"),
        "apply": report.get("apply"),
        "health_summary": report.get("health_summary"),
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }, ensure_ascii=False, indent=2))
    print(f"{PACKAGE}_REPORT_OK")
    if report.get("health_summary", {}).get("overall_ok"):
        print(f"{PACKAGE}_HEALTH_OK")
    if args.mode in ("apply", "all"):
        if report.get("apply", {}).get("full_rollback"):
            print(f"{PACKAGE}_APPLY_ROLLBACK")
        elif report.get("apply", {}).get("patched_functions"):
            print(f"{PACKAGE}_APPLY_OK")
        else:
            print(f"{PACKAGE}_APPLY_NOOP")
    print(f"{PACKAGE}_OK")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
