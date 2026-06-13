# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Period Notes Read Delegate P3.6 V2.17.40

Güvenli mikro refactor:
- Gerçek POST/yazma endpointlerine dokunmaz.
- Dönem içi notların GET/okuma tarafındaki fonksiyonlarını servis delegasyonuna alır.
- URL, endpoint ve blueprint adlarını değiştirmez.
- Sağlık bozulursa rollback yapar.
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
from typing import Dict, List, Tuple, Any

VERSION = "V2.17.40"
REPORT_STEM = "bys360_mobile_performance_period_notes_read_delegate_p3_6_v2_17_40"
TARGETS = [
    "mobile_performance_in_period_notes",
    "mobile_performance_in_period_notes_v2853",
    "mobile_performance_note_scorecard_v2863a",
]
SERVICE_MODULE = "app.api.mobile.services.performance_period_service"
SERVICE_PATH = Path("app/api/mobile/services/performance_period_service.py")
ROUTES_PATH = Path("app/api/mobile/performance_routes.py")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    try:
        compile(read_text(path), str(path), "exec")
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_cmd(root: Path, cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        p = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout_tail": p.stdout[-4000:],
            "stderr_tail": p.stderr[-4000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}: {exc}"}


def health(root: Path) -> Dict[str, Any]:
    compileall = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=180)
    app_factory = run_cmd(
        root,
        [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"],
        timeout=120,
    )
    return {
        "compileall_ok": bool(compileall.get("ok")),
        "app_factory_ok": bool(app_factory.get("ok")),
        "overall_ok": bool(compileall.get("ok") and app_factory.get("ok")),
        "compileall": compileall,
        "app_factory": app_factory,
    }


def parse_functions(source: str) -> Dict[str, ast.FunctionDef]:
    tree = ast.parse(source)
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def has_delegation(block: str, func: str) -> bool:
    return (
        f"delegate_{func}" in block
        or f"handle_{func}" in block
        or SERVICE_MODULE in block
        or "performance_period_service" in block
    )


def legacy_name(func: str) -> str:
    return f"_bys360_legacy_{func}"


def delegate_name(func: str) -> str:
    return f"delegate_{func}"


def get_arg_names(node: ast.FunctionDef) -> List[str]:
    args: List[str] = []
    for a in node.args.posonlyargs + node.args.args:
        args.append(a.arg)
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    for a in node.args.kwonlyargs:
        args.append(a.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    # call tarafında yıldızları korumak gerekir
    return args


def call_arg_exprs(node: ast.FunctionDef) -> List[str]:
    exprs: List[str] = []
    for a in node.args.posonlyargs + node.args.args:
        exprs.append(a.arg)
    if node.args.vararg:
        exprs.append("*" + node.args.vararg.arg)
    for a in node.args.kwonlyargs:
        exprs.append(f"{a.arg}={a.arg}")
    if node.args.kwarg:
        exprs.append("**" + node.args.kwarg.arg)
    return exprs


def signature_from_def_line(line: str, func: str) -> str:
    # Tek satırlı def varsayımı. BYS360 mobil fonksiyonlarında geçerli.
    m = re.match(r"^(\s*)def\s+" + re.escape(func) + r"\s*\((.*)\)\s*:\s*(#.*)?$", line)
    if not m:
        raise ValueError(f"Tek satırlı def imzası okunamadı: {func}")
    return m.group(2)


def rename_def_line(line: str, func: str, new_name: str) -> str:
    return re.sub(r"^(\s*)def\s+" + re.escape(func) + r"\s*\(", r"\1def " + new_name + "(", line, count=1)


def make_wrapper(func: str, signature: str, call_args: List[str]) -> str:
    call = ", ".join(call_args)
    return (
        f"\n\ndef {func}({signature}):\n"
        f"    from {SERVICE_MODULE} import {delegate_name(func)}\n"
        f"    return {delegate_name(func)}({call})\n"
    )


def ensure_service_functions(service_text: str, funcs: List[str]) -> Tuple[str, bool, int]:
    changed = False
    if not service_text.strip():
        service_text = "# -*- coding: utf-8 -*-\n\"\"\"BYS360 mobil performans dönem/not servis delegasyonları.\"\"\"\n"
        changed = True
    additions = []
    for func in funcs:
        dname = delegate_name(func)
        lname = legacy_name(func)
        if re.search(r"^def\s+" + re.escape(dname) + r"\s*\(", service_text, re.M):
            continue
        additions.append(
            f"\n\ndef {dname}(*args, **kwargs):\n"
            f"    from app.api.mobile.performance_routes import {lname}\n"
            f"    return {lname}(*args, **kwargs)\n"
        )
    if additions:
        service_text = service_text.rstrip() + "\n" + "".join(additions) + "\n"
        changed = True
    delegate_count = len(re.findall(r"^def\s+delegate_", service_text, re.M))
    return service_text, changed, delegate_count


def audit(root: Path) -> Dict[str, Any]:
    routes = root / ROUTES_PATH
    service = root / SERVICE_PATH
    result: Dict[str, Any] = {
        "target_exists": routes.exists(),
        "target_path": rel(routes, root),
        "target_compile": compile_file(routes),
        "service_exists": service.exists(),
        "service_path": rel(service, root),
        "service_compile": compile_file(service),
        "parse_error": "",
        "candidate_count": 0,
        "delegated_count": 0,
        "patchable_count": 0,
        "functions": [],
    }
    if not routes.exists():
        return result
    source = read_text(routes)
    try:
        funcs = parse_functions(source)
    except Exception as exc:
        result["parse_error"] = f"{type(exc).__name__}: {exc}"
        return result
    lines = source.splitlines()
    for name in TARGETS:
        node = funcs.get(name)
        exists = node is not None
        item: Dict[str, Any] = {"name": name, "exists": exists}
        if not exists:
            item.update({"line": 0, "end_line": 0, "length": 0, "delegated": False, "legacy": legacy_name(name) in funcs, "patchable": False, "arg": ""})
            result["functions"].append(item)
            continue
        block = "\n".join(lines[node.lineno - 1 : node.end_lineno])
        delegated = has_delegation(block, name)
        legacy = legacy_name(name) in funcs
        patchable = (not delegated) and (not legacy)
        item.update({
            "line": node.lineno,
            "end_line": node.end_lineno,
            "length": node.end_lineno - node.lineno + 1,
            "delegated": delegated,
            "legacy": legacy,
            "patchable": patchable,
            "arg": ", ".join([a.replace("*", "") for a in get_arg_names(node)]),
        })
        result["functions"].append(item)
        result["candidate_count"] += 1
        if delegated:
            result["delegated_count"] += 1
        if patchable:
            result["patchable_count"] += 1
    return result


def patch(root: Path) -> Dict[str, Any]:
    routes = root / ROUTES_PATH
    service = root / SERVICE_PATH
    a = audit(root)
    patchable = [x["name"] for x in a.get("functions", []) if x.get("patchable")]
    result: Dict[str, Any] = {
        "routes_changed": False,
        "service_changed": False,
        "patched_functions": [],
        "skipped": [],
        "backup": "",
        "error": "",
        "rolled_back": False,
        "target_compile": {},
        "service": {},
    }
    if not patchable:
        result["skipped"].append({"reason": "no_patchable_functions"})
        return result

    quarantine = root / "_local_quarantine" / f"bys360_mobile_performance_period_notes_read_delegate_p3_6_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup = quarantine / ROUTES_PATH
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(routes, backup)
    result["backup"] = rel(backup, root)

    original_routes = read_text(routes)
    original_service = read_text(service) if service.exists() else ""
    try:
        funcs = parse_functions(original_routes)
        lines = original_routes.splitlines()
        replacements: List[Tuple[int, int, str]] = []
        for name in patchable:
            node = funcs[name]
            block_lines = lines[node.lineno - 1 : node.end_lineno]
            signature = signature_from_def_line(block_lines[0], name)
            legacy_lines = list(block_lines)
            legacy_lines[0] = rename_def_line(legacy_lines[0], name, legacy_name(name))
            wrapper = make_wrapper(name, signature, call_arg_exprs(node))
            replacement = "\n".join(legacy_lines) + wrapper
            replacements.append((node.lineno - 1, node.end_lineno, replacement))
        # Alttan üste değiştir, satır indeksleri bozulmasın.
        for start, end, repl in sorted(replacements, reverse=True):
            lines[start:end] = repl.splitlines()
        new_routes = "\n".join(lines) + "\n"

        new_service, service_changed, delegate_count = ensure_service_functions(original_service, patchable)
        write_text(service, new_service)
        write_text(routes, new_routes)
        result["routes_changed"] = new_routes != original_routes
        result["service_changed"] = service_changed
        result["patched_functions"] = patchable
        result["service"] = {"path": rel(service, root), "changed": service_changed, "delegate_count": delegate_count, "compile": compile_file(service)}
        result["target_compile"] = {"routes": compile_file(routes), "service": compile_file(service)}
        if not result["target_compile"]["routes"].get("ok") or not result["target_compile"]["service"].get("ok"):
            raise RuntimeError(f"Target compile failed: {result['target_compile']}")
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        write_text(routes, original_routes)
        write_text(service, original_service)
        result["rolled_back"] = True
        result["target_compile"] = {"routes": compile_file(routes), "service": compile_file(service)}
    return result


def write_reports(root: Path, payload: Dict[str, Any]) -> Tuple[Path, Path]:
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{REPORT_STEM}_report.json"
    md_path = report_dir / f"{REPORT_STEM}_report.md"
    write_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2))
    lines = []
    lines.append(f"# BYS360 Mobile Performance Period Notes Read Delegate P3.6 {VERSION}")
    lines.append("")
    lines.append("Bu rapor gerçek POST/yazma endpointlerine dokunmadan dönem içi not GET/okuma fonksiyonlarının servis delegasyonu sonucunu gösterir.")
    lines.append("")
    lines.append("## Durum")
    lines.append(f"- mode: {payload.get('mode')}")
    lines.append("")
    a = payload.get("audit", {})
    lines.append("## Audit")
    lines.append(f"- candidate_count: {a.get('candidate_count')}")
    lines.append(f"- delegated_count: {a.get('delegated_count')}")
    lines.append(f"- patchable_count: {a.get('patchable_count')}")
    lines.append("")
    lines.append("| Fonksiyon | Var | Satır | Uzunluk | Delegated | Legacy | Patchable | Arg |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for f in a.get("functions", []):
        lines.append(f"| `{f.get('name')}` | {f.get('exists')} | {f.get('line', 0)} | {f.get('length', 0)} | {f.get('delegated')} | {f.get('legacy')} | {f.get('patchable')} | `{f.get('arg','')}` |")
    lines.append("")
    ap = payload.get("apply", {})
    lines.append("## Apply")
    for k in ["routes_changed", "service_changed", "patched_functions", "skipped", "backup", "error", "rolled_back", "service", "target_compile"]:
        if k in ap:
            lines.append(f"- {k}: `{ap.get(k)}`")
    lines.append("")
    h = payload.get("health_summary", {})
    lines.append("## Sağlık Kontrolü")
    lines.append(f"- compileall_ok: {h.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {h.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {h.get('overall_ok')}")
    lines.append("")
    lines.append("## Not")
    lines.append("Bu adım gerçek POST yazma endpointlerini çalıştırmaz; dönem içi not okuma/karne görünümü tarafındaki GET fonksiyonlarını servis katmanına alır.")
    write_text(md_path, "\n".join(lines) + "\n")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=".")
    parser.add_argument("--mode", "-Mode", dest="mode", default="audit", choices=["audit", "all"])
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    payload: Dict[str, Any] = {"version": VERSION, "mode": args.mode, "project_root": str(root)}
    payload["audit"] = audit(root)
    if args.mode == "all":
        payload["apply"] = patch(root)
        payload["health_summary"] = health(root)
    else:
        payload["apply"] = {}
        payload["health_summary"] = {}
    json_path, md_path = write_reports(root, payload)
    payload["json_report"] = rel(json_path, root)
    payload["md_report"] = rel(md_path, root)
    # Raporları json_report/md_report ile tekrar yaz.
    write_reports(root, payload)
    print(json.dumps({k: v for k, v in payload.items() if k not in {"health_summary"} or args.mode == "all"}, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_PERIOD_NOTES_READ_DELEGATE_P3_6_V2_17_40_REPORT_OK")
    if args.mode == "all":
        ok = payload.get("health_summary", {}).get("overall_ok") and not payload.get("apply", {}).get("rolled_back")
        if ok:
            print("BYS360_MOBILE_PERFORMANCE_PERIOD_NOTES_READ_DELEGATE_P3_6_V2_17_40_HEALTH_OK")
            print("BYS360_MOBILE_PERFORMANCE_PERIOD_NOTES_READ_DELEGATE_P3_6_V2_17_40_APPLY_OK")
            print("BYS360_MOBILE_PERFORMANCE_PERIOD_NOTES_READ_DELEGATE_P3_6_V2_17_40_OK")
            return 0
        print("BYS360_MOBILE_PERFORMANCE_PERIOD_NOTES_READ_DELEGATE_P3_6_V2_17_40_APPLY_ROLLBACK_OR_HEALTH_FAIL")
        return 1
    print("BYS360_MOBILE_PERFORMANCE_PERIOD_NOTES_READ_DELEGATE_P3_6_V2_17_40_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
