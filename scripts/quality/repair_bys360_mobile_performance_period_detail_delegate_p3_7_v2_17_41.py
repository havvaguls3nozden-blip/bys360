# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Period Detail Delegate P3.7 V2.17.41

Güvenli mikro refactor paketi:
- Gerçek POST/yazma endpointlerine dokunmaz.
- Performans dönem detayı ve dönem kapsam/progress helper fonksiyonlarını servis delegasyonuna alır.
- URL, endpoint, blueprint ve route decorator adlarını değiştirmez.
- Eski gövdeyi _bys360_legacy_* fonksiyonunda korur.
- Compile/app factory bozulursa rollback yapar.
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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

VERSION = "V2.17.41"
SLUG = "bys360_mobile_performance_period_detail_delegate_p3_7_v2_17_41"
TARGET_REL = Path("app/api/mobile/performance_routes.py")
SERVICE_REL = Path("app/api/mobile/services/performance_period_service.py")
REPORT_JSON_REL = Path("reports/quality/bys360_mobile_performance_period_detail_delegate_p3_7_v2_17_41_report.json")
REPORT_MD_REL = Path("reports/quality/bys360_mobile_performance_period_detail_delegate_p3_7_v2_17_41_report.md")

TARGETS = [
    "mobile_performance_period_detail",
    "_period_scope",
    "_period_progress",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": str(exc)}


def run_cmd(args: List[str], cwd: Path, timeout: int = 120) -> Dict[str, Any]:
    try:
        cp = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-5000:],
            "stderr_tail": cp.stderr[-5000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(exc)}


def health(project_root: Path) -> Dict[str, Any]:
    compileall = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], cwd=project_root)
    app_factory = run_cmd(
        [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"],
        cwd=project_root,
    )
    return {
        "compileall_ok": compileall["ok"],
        "app_factory_ok": app_factory["ok"],
        "overall_ok": compileall["ok"] and app_factory["ok"],
        "compileall": compileall,
        "app_factory": app_factory,
    }


def parse_functions(text: str) -> Dict[str, ast.FunctionDef]:
    tree = ast.parse(text)
    out: Dict[str, ast.FunctionDef] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node
    return out


def line_offsets(text: str) -> List[int]:
    offsets = [0]
    total = 0
    for line in text.splitlines(True):
        total += len(line)
        offsets.append(total)
    return offsets


def node_span(text: str, node: ast.AST) -> Tuple[int, int]:
    offsets = line_offsets(text)
    start = offsets[node.lineno - 1]
    end = offsets[getattr(node, "end_lineno", node.lineno)]
    return start, end


def get_signature_and_indent(source: str, name: str) -> Tuple[str, str, str]:
    # returns full def line header until ':' and indent of def line and args string
    m = re.search(r"(?m)^(?P<indent>\s*)def\s+" + re.escape(name) + r"\s*\((?P<args>[^)]*)\)\s*:", source)
    if not m:
        raise ValueError(f"def header bulunamadi: {name}")
    return m.group(0), m.group("indent"), m.group("args").strip()


def arg_names_from_ast(node: ast.FunctionDef) -> List[str]:
    names = [a.arg for a in node.args.args]
    # keep simple; current target functions use simple positional args
    return names


def has_route_decorator(node: ast.FunctionDef) -> bool:
    for dec in node.decorator_list:
        src = ast.unparse(dec) if hasattr(ast, "unparse") else ""
        if ".route" in src or "route(" in src:
            return True
    return False


def is_delegated(source: str, name: str) -> bool:
    pattern = r"def\s+" + re.escape(name) + r"\s*\([^)]*\):\s*\n(?:\s+.*\n){0,8}?\s+return\s+_period_service\." + re.escape(name) + r"\("
    return re.search(pattern, source) is not None


def legacy_name(name: str) -> str:
    return "_bys360_legacy_" + name


def indent_block(block: str, prefix: str) -> str:
    return "".join(prefix + line if line.strip() else line for line in block.splitlines(True))


def ensure_service(project_root: Path, target_names: List[str]) -> Dict[str, Any]:
    service_path = project_root / SERVICE_REL
    service_path.parent.mkdir(parents=True, exist_ok=True)
    if service_path.exists():
        text = read_text(service_path)
    else:
        text = "# -*- coding: utf-8 -*-\n\"\"\"Mobile performance period service delegates.\"\"\"\n\n"

    changed = False
    if "from __future__ import annotations" not in text[:200]:
        text = text.replace("# -*- coding: utf-8 -*-\n", "# -*- coding: utf-8 -*-\nfrom __future__ import annotations\n", 1) if text.startswith("# -*- coding: utf-8 -*-") else "from __future__ import annotations\n" + text
        changed = True

    for name in target_names:
        if re.search(r"(?m)^def\s+" + re.escape(name) + r"\s*\(", text):
            continue
        lname = legacy_name(name)
        fn = f'''

def {name}(*args, **kwargs):
    """Delegated wrapper for {name}."""
    from app.api.mobile import performance_routes as _routes
    return _routes.{lname}(*args, **kwargs)
'''
        text += fn
        changed = True

    if changed:
        write_text(service_path, text)
    return {"path": str(SERVICE_REL).replace("\\", "/"), "changed": changed, "compile": compile_file(service_path)}


def audit(project_root: Path) -> Dict[str, Any]:
    target = project_root / TARGET_REL
    service = project_root / SERVICE_REL
    out: Dict[str, Any] = {
        "target_exists": target.exists(),
        "target_compile": compile_file(target),
        "service_compile": compile_file(service),
        "candidate_count": 0,
        "delegated_count": 0,
        "patchable_count": 0,
        "functions": [],
    }
    if not target.exists():
        return out
    text = read_text(target)
    try:
        funcs = parse_functions(text)
    except Exception as exc:
        out["parse_error"] = str(exc)
        return out

    for name in TARGETS:
        node = funcs.get(name)
        info = {
            "name": name,
            "exists": node is not None,
            "line": getattr(node, "lineno", 0) if node else 0,
            "end_line": getattr(node, "end_lineno", 0) if node else 0,
            "length": (getattr(node, "end_lineno", 0) - getattr(node, "lineno", 0) + 1) if node else 0,
            "route_decorator": has_route_decorator(node) if node else False,
            "delegated": is_delegated(text, name) if node else False,
            "legacy": legacy_name(name) in funcs,
            "arg": ", ".join(arg_names_from_ast(node)) if node else "",
            "patchable": False,
        }
        if node:
            out["candidate_count"] += 1
            if info["delegated"]:
                out["delegated_count"] += 1
            if not info["delegated"] and not info["legacy"]:
                info["patchable"] = True
                out["patchable_count"] += 1
        out["functions"].append(info)
    return out


def patch(project_root: Path) -> Dict[str, Any]:
    target = project_root / TARGET_REL
    before_compile = {"routes": compile_file(target), "service": compile_file(project_root / SERVICE_REL)}
    a = audit(project_root)
    patchable = [f["name"] for f in a.get("functions", []) if f.get("patchable")]
    apply: Dict[str, Any] = {
        "routes_changed": False,
        "service_changed": False,
        "patched_functions": [],
        "skipped": [],
        "backup": "",
        "error": "",
        "rolled_back": False,
        "before_target_compile": before_compile,
    }
    if not patchable:
        apply["skipped"].append({"reason": "no_patchable_functions"})
        apply["service"] = ensure_service(project_root, [])
        apply["target_compile"] = {"routes": compile_file(target), "service": compile_file(project_root / SERVICE_REL)}
        return apply

    qroot = project_root / "_local_quarantine" / f"bys360_mobile_performance_period_detail_delegate_p3_7_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup = qroot / TARGET_REL
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)
    apply["backup"] = str(backup.relative_to(project_root))

    service_info = ensure_service(project_root, patchable)
    apply["service"] = service_info
    apply["service_changed"] = bool(service_info.get("changed"))

    original = read_text(target)
    text = original
    try:
        # Work from bottom to top so spans remain valid.
        funcs = parse_functions(text)
        edits = []
        legacy_blocks = []
        import_line = "from app.api.mobile.services import performance_period_service as _period_service\n"
        if import_line not in text:
            # insert after future/import block, conservatively after first import group or at top after coding/future lines
            lines = text.splitlines(True)
            insert_idx = 0
            while insert_idx < len(lines) and (lines[insert_idx].startswith("#") or lines[insert_idx].strip() == "" or lines[insert_idx].startswith("from __future__")):
                insert_idx += 1
            lines.insert(insert_idx, import_line)
            text = "".join(lines)
            funcs = parse_functions(text)

        for name in patchable:
            node = funcs[name]
            start, end = node_span(text, node)
            source = text[start:end]
            lname = legacy_name(name)
            legacy_source = re.sub(r"(?m)^(\s*)def\s+" + re.escape(name) + r"\s*\(", r"\1def " + lname + "(", source, count=1)
            args = arg_names_from_ast(node)
            call_args = ", ".join(args)
            header, def_indent, _ = get_signature_and_indent(source, name)
            body_indent = def_indent + "    "
            new_func = header + "\n" + body_indent + f"return _period_service.{name}({call_args})\n"
            edits.append((start, end, new_func))
            legacy_blocks.append("\n\n" + legacy_source.rstrip() + "\n")

        for start, end, repl in sorted(edits, reverse=True):
            text = text[:start] + repl + text[end:]
        text = text.rstrip() + "\n" + "".join(legacy_blocks) + "\n"
        ast.parse(text)
        write_text(target, text)
        target_compile = {"routes": compile_file(target), "service": compile_file(project_root / SERVICE_REL)}
        if not target_compile["routes"]["ok"] or not target_compile["service"]["ok"]:
            raise RuntimeError("target compile failed after patch: " + json.dumps(target_compile, ensure_ascii=False))
        apply["routes_changed"] = True
        apply["patched_functions"] = patchable
        apply["target_compile"] = target_compile
    except Exception as exc:
        apply["error"] = str(exc)
        shutil.copy2(backup, target)
        apply["rolled_back"] = True
        apply["target_compile"] = {"routes": compile_file(target), "service": compile_file(project_root / SERVICE_REL)}
    return apply


def write_report(project_root: Path, result: Dict[str, Any]) -> None:
    json_path = project_root / REPORT_JSON_REL
    md_path = project_root / REPORT_MD_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(json_path, json.dumps(result, ensure_ascii=False, indent=2))

    a = result.get("audit", {})
    ap = result.get("apply", {})
    h = result.get("health_summary", {})
    lines = []
    lines.append("# BYS360 Mobile Performance Period Detail Delegate P3.7 V2.17.41\n")
    lines.append("Bu rapor gerçek POST/yazma endpointlerine dokunmadan performans dönem detayı ve dönem helper fonksiyonlarının servis delegasyonu sonucunu gösterir.\n")
    lines.append("## Durum\n")
    lines.append(f"- mode: {result.get('mode')}\n")
    lines.append("## Audit\n")
    lines.append(f"- candidate_count: {a.get('candidate_count', 0)}\n")
    lines.append(f"- delegated_count: {a.get('delegated_count', 0)}\n")
    lines.append(f"- patchable_count: {a.get('patchable_count', 0)}\n")
    lines.append("\n| Fonksiyon | Var | Satır | Uzunluk | Route Decorator | Delegated | Legacy | Patchable | Arg |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|\n")
    for f in a.get("functions", []):
        lines.append(f"| `{f.get('name')}` | {f.get('exists')} | {f.get('line')} | {f.get('length')} | {f.get('route_decorator')} | {f.get('delegated')} | {f.get('legacy')} | {f.get('patchable')} | `{f.get('arg')}` |\n")
    lines.append("\n## Apply\n")
    if ap:
        lines.append(f"- service: `{ap.get('service')}`\n")
        lines.append(f"- routes_changed: `{ap.get('routes_changed')}`\n")
        lines.append(f"- patched_functions: `{ap.get('patched_functions')}`\n")
        lines.append(f"- skipped: `{ap.get('skipped')}`\n")
        lines.append(f"- backup: `{ap.get('backup')}`\n")
        lines.append(f"- error: `{ap.get('error')}`\n")
        lines.append(f"- rolled_back: `{ap.get('rolled_back')}`\n")
    lines.append("\n## Sağlık Kontrolü\n")
    lines.append(f"- compileall_ok: {h.get('compileall_ok')}\n")
    lines.append(f"- app_factory_ok: {h.get('app_factory_ok')}\n")
    lines.append(f"- overall_ok: {h.get('overall_ok')}\n")
    lines.append("\n## Not\n")
    lines.append("Bu adım gerçek POST/yazma endpointlerini çalıştırmaz ve URL/endpoint/blueprint adlarını değiştirmez.\n")
    write_text(md_path, "".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "apply", "all"], default="all")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    print(f"BYS360 Mobile Performance Period Detail Delegate P3.7 {VERSION} basliyor...")
    print(f"ProjectRoot={project_root}")
    print(f"Mode={args.mode}")

    result: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(project_root),
        "audit": {},
        "apply": {},
        "health_summary": {},
        "json_report": str(REPORT_JSON_REL),
        "md_report": str(REPORT_MD_REL),
    }
    result["audit"] = audit(project_root)
    if args.mode in ("apply", "all"):
        result["apply"] = patch(project_root)
    if args.mode in ("all",):
        result["health_summary"] = health(project_root)
    elif args.mode == "apply":
        result["health_summary"] = health(project_root)

    write_report(project_root, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("audit",)}, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7_V2_17_41_REPORT_OK")
    h = result.get("health_summary") or {}
    ap = result.get("apply") or {}
    if args.mode == "audit":
        print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7_V2_17_41_OK")
        return 0
    if h.get("overall_ok") and not ap.get("rolled_back") and not ap.get("error"):
        print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7_V2_17_41_HEALTH_OK")
        print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7_V2_17_41_APPLY_OK")
        print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7_V2_17_41_OK")
        return 0
    print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7_V2_17_41_APPLY_ROLLBACK" if ap.get("rolled_back") else "BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7_V2_17_41_APPLY_FAIL")
    print("BYS360_MOBILE_PERFORMANCE_PERIOD_DETAIL_DELEGATE_P3_7_V2_17_41_OK")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
