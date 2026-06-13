# -*- coding: utf-8 -*-
"""
BYS360 Mobile Dashboard/Profile Delegate P1.4C V2.17.12

Amaç:
- P1.4B paketindeki bozuk quality scriptini güvenli karantinaya almak.
- app/api/mobile/routes.py içinde düşük riskli dashboard/KPI route fonksiyonlarını
  URL, endpoint ve blueprint adını değiştirmeden servis delegasyonuna almak.
- Eğer hedef fonksiyonlar bulunamazsa hata vermek yerine tanı raporu üretmek.

Not:
Bu paket route URL/decorator adlarını değiştirmez. Public route fonksiyon adları korunur.
Eski gövde _bys360_legacy_<fonksiyon> olarak aynı dosyada kalır; sonraki fazlarda
legacy gövdeler parça parça servis dosyalarına taşınabilir.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

VERSION = "V2.17.12"
REPORT_STEM = "bys360_mobile_dashboard_profile_delegate_p1_4c_v2_17_12"

DASHBOARD_TARGETS = [
    "mobile_dashboard_summary",
    "mobile_kpi_target_management_v2853",
    "mobile_kpi_target_create_v2853",
    "mobile_kpi_target_progress_v2853",
]

# Profile hedefleri sadece varsa ve açıkça route fonksiyonuysa alınır.
PROFILE_NAME_HINTS = ("profile",)
EXCLUDE_PROFILE_NAMES = ("_", "legacy")

BROKEN_P14B_FILES = [
    Path("scripts/quality/repair_bys360_mobile_dashboard_profile_delegate_p1_4b_v2_17_11.py"),
]

EXCLUDE_DIRS_FOR_COMPILE = {".venv", "venv", "__pycache__", "_local_quarantine", ".git", "node_modules", "build", "dist"}


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def parse_functions(path: Path) -> Tuple[ast.Module | None, List[Dict[str, Any]], str | None]:
    try:
        text = read_text(path)
        tree = ast.parse(text)
    except Exception as exc:
        return None, [], f"{type(exc).__name__}: {exc}"
    funcs: List[Dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorator_lines = []
            route_like = False
            for dec in node.decorator_list:
                try:
                    src = ast.get_source_segment(text, dec) or ""
                except Exception:
                    src = ""
                decorator_lines.append(src)
                if "route" in src or "mobile" in src or "bp" in src or "api" in src:
                    route_like = True
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            funcs.append({
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
                "start_lineno": start,
                "decorator_count": len(node.decorator_list),
                "decorators": decorator_lines,
                "route_like": route_like,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            })
    return tree, funcs, None


def function_source(lines: List[str], info: Dict[str, Any], include_decorators: bool) -> List[str]:
    start = (info["start_lineno"] if include_decorators else info["lineno"]) - 1
    end = info["end_lineno"]
    return lines[start:end]


def is_delegated(lines: List[str], info: Dict[str, Any]) -> bool:
    src = "\n".join(function_source(lines, info, include_decorators=False))
    return "_delegate(" in src and "_bys360_legacy_" in src


def select_targets(funcs: List[Dict[str, Any]], lines: List[str]) -> Tuple[List[str], List[str]]:
    names = {f["name"]: f for f in funcs}
    targets: List[str] = []
    for name in DASHBOARD_TARGETS:
        if name in names:
            targets.append(name)
    # Profile tarafında sadece bariz mobil profile public route fonksiyonlarını seç.
    for f in funcs:
        name = f["name"]
        lname = name.lower()
        if name in targets:
            continue
        if not name.startswith("mobile_"):
            continue
        if any(lname.startswith(prefix) for prefix in EXCLUDE_PROFILE_NAMES):
            continue
        if "profile" in lname and f.get("route_like"):
            targets.append(name)
    delegated_already = [name for name in targets if is_delegated(lines, names[name])]
    return targets, delegated_already


def ensure_dashboard_service(root: Path, delegate_names: List[str]) -> Dict[str, Any]:
    service = root / "app/api/mobile/services/dashboard_service.py"
    existing = read_text(service) if service.exists() else ""
    changed = False
    if not existing.strip():
        existing = "# -*- coding: utf-8 -*-\n\"\"\"BYS360 mobile dashboard service delegates.\"\"\"\n\n"
        changed = True
    if "def _call_legacy(" not in existing:
        existing += "\n\ndef _call_legacy(legacy_func, *args, **kwargs):\n    return legacy_func(*args, **kwargs)\n"
        changed = True
    for name in delegate_names:
        dname = f"{name}_delegate"
        if f"def {dname}(" not in existing:
            existing += (
                f"\n\ndef {dname}(legacy_func, *args, **kwargs):\n"
                f"    \"\"\"Delegate for {name}; keeps legacy behavior until full service extraction.\"\"\"\n"
                f"    return _call_legacy(legacy_func, *args, **kwargs)\n"
            )
            changed = True
    if changed:
        write_text(service, existing)
    return {"path": rel(service, root), "changed": changed, "delegate_count": len(delegate_names)}


def patch_routes(root: Path, mode: str) -> Dict[str, Any]:
    routes = root / "app/api/mobile/routes.py"
    if not routes.exists():
        return {"error": "app/api/mobile/routes.py bulunamadi", "routes_changed": False, "patched_functions": []}
    text = read_text(routes)
    lines = text.splitlines()
    _, funcs, parse_error = parse_functions(routes)
    if parse_error:
        return {"error": parse_error, "routes_changed": False, "patched_functions": []}
    by_name = {f["name"]: f for f in funcs}
    targets, delegated_already = select_targets(funcs, lines)
    patchable = [name for name in targets if name not in delegated_already]
    result: Dict[str, Any] = {
        "routes_path": rel(routes, root),
        "candidate_targets": targets,
        "delegated_already": delegated_already,
        "patchable_targets": patchable,
        "routes_changed": False,
        "patched_functions": [],
    }
    if mode == "audit" or not patchable:
        return result

    # Yalnızca hedef route fonksiyonlarını sonda baştan işleyerek satır indeksleri kaymasın.
    qroot = root / "_local_quarantine" / f"bys360_mobile_dashboard_profile_delegate_p1_4c_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup = qroot / "app/api/mobile/routes.py.before_p1_4c"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(routes, backup)

    changed_lines = lines[:]
    patched: List[str] = []
    for name in sorted(patchable, key=lambda n: by_name[n]["start_lineno"], reverse=True):
        info = by_name[name]
        start_idx = info["start_lineno"] - 1
        def_idx = info["lineno"] - 1
        end_idx = info["end_lineno"]
        decorators = changed_lines[start_idx:def_idx]
        original_def = changed_lines[def_idx:end_idx]
        if not original_def:
            continue
        # Legacy def: dekoratorsuz, isim değiştirilmiş orijinal gövde.
        legacy_def = original_def[:]
        first = legacy_def[0]
        if first.lstrip().startswith("async def "):
            legacy_def[0] = first.replace(f"async def {name}(", f"async def _bys360_legacy_{name}(", 1)
            async_prefix = "async "
            await_prefix = "await "
        else:
            legacy_def[0] = first.replace(f"def {name}(", f"def _bys360_legacy_{name}(", 1)
            async_prefix = ""
            await_prefix = ""
        wrapper = decorators + [
            f"{async_prefix}def {name}(*args, **kwargs):",
            f"    \"\"\"P1.4C service delegate wrapper; URL/endpoint/decorator korunur.\"\"\"",
            f"    from app.api.mobile.services.dashboard_service import {name}_delegate",
            f"    return {await_prefix}{name}_delegate(_bys360_legacy_{name}, *args, **kwargs)",
            "",
        ] + legacy_def
        changed_lines[start_idx:end_idx] = wrapper
        patched.append(name)

    new_text = "\n".join(changed_lines) + "\n"
    try:
        ast.parse(new_text)
    except Exception as exc:
        shutil.copy2(backup, routes)
        result.update({"error": f"Patch sonrası syntax hatası; rollback yapıldı: {type(exc).__name__}: {exc}", "backup": rel(backup, root)})
        return result
    write_text(routes, new_text)
    result.update({"routes_changed": True, "patched_functions": patched, "backup": rel(backup, root)})
    return result


def quarantine_broken_p14b(root: Path, mode: str) -> Dict[str, Any]:
    moved = []
    qroot = root / "_local_quarantine" / f"bys360_p1_4b_broken_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    for relp in BROKEN_P14B_FILES:
        src = root / relp
        if not src.exists():
            continue
        # Audit modunda sadece bildir.
        if mode == "audit":
            moved.append({"path": relp.as_posix(), "status": "would_move"})
            continue
        dst = qroot / relp
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        moved.append({"path": relp.as_posix(), "status": "moved", "to": rel(dst, root)})
    return {"moved": moved}


def run_cmd(root: Path, args: List[str], timeout: int = 120) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(
            args,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}: {exc}"}


def health(root: Path) -> Dict[str, Any]:
    compileall = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=180)
    app_factory = run_cmd(root, [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], timeout=180)
    return {
        "compileall_ok": bool(compileall["ok"]),
        "app_factory_ok": bool(app_factory["ok"]),
        "overall_ok": bool(compileall["ok"] and app_factory["ok"]),
        "compileall": compileall,
        "app_factory": app_factory,
    }


def write_reports(root: Path, report: Dict[str, Any]) -> None:
    rdir = root / "reports/quality"
    rdir.mkdir(parents=True, exist_ok=True)
    json_path = rdir / f"{REPORT_STEM}_report.json"
    md_path = rdir / f"{REPORT_STEM}_report.md"
    report["json_report"] = rel(json_path, root)
    report["md_report"] = rel(md_path, root)
    write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))
    lines = [
        f"# BYS360 Mobile Dashboard/Profile Delegate P1.4C {VERSION}",
        "",
        "Bu rapor P1.4B syntax hatasını temizler ve dashboard/profile mobil route delegasyonu için güvenli sonucu gösterir.",
        "",
        "## Durum",
        f"- mode: {report.get('mode')}",
        f"- p14b_cleanup: {report.get('p14b_cleanup', {}).get('moved', [])}",
        "",
        "## Route Delegasyonu",
    ]
    pr = report.get("patch_result", {})
    for key in ["candidate_targets", "delegated_already", "patchable_targets", "patched_functions", "routes_changed", "backup", "error"]:
        if key in pr:
            lines.append(f"- {key}: {pr.get(key)}")
    sv = report.get("service_result", {})
    lines += ["", "## Servis", f"- {sv}", "", "## Sağlık Kontrolü"]
    hs = report.get("health_summary", {})
    lines += [
        f"- compileall_ok: {hs.get('compileall_ok')}",
        f"- app_factory_ok: {hs.get('app_factory_ok')}",
        f"- overall_ok: {hs.get('overall_ok')}",
    ]
    write_text(md_path, "\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "all", "health"], default="audit")
    ns = ap.parse_args()
    root = Path(ns.project_root).resolve()
    mode = ns.mode
    report: Dict[str, Any] = {"version": VERSION, "mode": mode, "project_root": str(root)}

    if mode in {"audit", "apply", "all"}:
        report["p14b_cleanup"] = quarantine_broken_p14b(root, "audit" if mode == "audit" else "apply")
        patch_result = patch_routes(root, "audit" if mode == "audit" else "apply")
        report["patch_result"] = patch_result
        if mode != "audit":
            delegate_names = patch_result.get("patched_functions") or patch_result.get("delegated_already") or patch_result.get("candidate_targets") or []
            report["service_result"] = ensure_dashboard_service(root, delegate_names)
        else:
            report["service_result"] = {"changed": False, "reason": "audit mode"}

    if mode in {"health", "all", "apply"}:
        report["health_summary"] = health(root)
    else:
        report["health_summary"] = {}

    write_reports(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": mode,
        "project_root": str(root),
        "patch_result": report.get("patch_result", {}),
        "service_result": report.get("service_result", {}),
        "health_summary": {
            "compileall_ok": report.get("health_summary", {}).get("compileall_ok"),
            "app_factory_ok": report.get("health_summary", {}).get("app_factory_ok"),
            "overall_ok": report.get("health_summary", {}).get("overall_ok"),
        },
        "json_report": report.get("json_report"),
        "md_report": report.get("md_report"),
    }, ensure_ascii=False, indent=2))

    print(f"BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4C_V2_17_12_REPORT_OK")
    overall = report.get("health_summary", {}).get("overall_ok")
    if mode in {"health", "all", "apply"}:
        if overall:
            print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4C_V2_17_12_HEALTH_OK")
        else:
            print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4C_V2_17_12_HEALTH_FAIL")
            return 1
    patched = report.get("patch_result", {}).get("patched_functions", [])
    if mode in {"apply", "all"}:
        if patched:
            print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4C_V2_17_12_APPLY_OK")
        else:
            print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4C_V2_17_12_APPLY_NOOP")
    print("BYS360_MOBILE_DASHBOARD_PROFILE_DELEGATE_P1_4C_V2_17_12_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
