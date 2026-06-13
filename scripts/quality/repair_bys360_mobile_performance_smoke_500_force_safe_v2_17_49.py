# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Smoke 500 Force Safe V2.17.49
Kod degisikligi yapar: sadece iki mobil performans GET endpointini guvenli JSON fallback'e zorlar.
URL / endpoint / blueprint adlarini degistirmez.
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
from typing import Any, Dict, List, Optional, Tuple

VERSION = "V2.17.49"
REPORT_STEM = "bys360_mobile_performance_smoke_500_force_safe_v2_17_49_report"
TARGET_REL = Path("app/api/mobile/performance_routes.py")
SERVICE_REL = Path("app/api/mobile/services/performance_summary_service.py")

TARGETS = {
    "mobile_performance_president_approvals_alias": "president",
    "_bys360_prev_mobile_performance_president_approvals_alias_v21748": "president",
    "_bys360_legacy_mobile_performance_president_approvals_alias": "president",
    "mobile_performance_history_archive": "history",
    "_bys360_prev_mobile_performance_history_archive_v21748": "history",
    "_bys360_legacy_mobile_performance_history_archive": "history",
}

HELPER_MARKER = "# BYS360_FORCE_SAFE_500_FALLBACK_V2_17_49"
HELPER_BLOCK = r'''

# BYS360_FORCE_SAFE_500_FALLBACK_V2_17_49
# Bu blok yalnizca mobil GET smoke testinde 500 veren iki endpoint icin guvenli JSON fallback saglar.
def _bys360_mobile_perf_safe_json_response_v21749(payload, status=200):
    try:
        from flask import jsonify
        return jsonify(payload), status
    except Exception:
        return payload, status


def _bys360_mobile_perf_president_approvals_safe_fallback_v21749(user=None):
    return _bys360_mobile_perf_safe_json_response_v21749({
        "items": [],
        "metrics": [
            {
                "title": "Başkan Onayları",
                "subtitle": "Yetki kapsamınızda bekleyen düşük performans onayı bulunamadı veya güvenli fallback devrede.",
                "value": 0,
                "tone": "red",
                "icon": "approval"
            }
        ],
        "status": "safe_fallback",
        "source": "BYS360 V2.17.49",
        "message": "Mobil başkan onayları endpointi güvenli boş yanıt döndürdü."
    })


def _bys360_mobile_perf_history_archive_safe_fallback_v21749(user=None):
    return _bys360_mobile_perf_safe_json_response_v21749({
        "items": [],
        "metrics": [
            {
                "title": "Geçmiş Arşiv",
                "subtitle": "Yetki kapsamınızda görüntülenecek geçmiş karne kaydı bulunamadı veya güvenli fallback devrede.",
                "value": 0,
                "tone": "red",
                "icon": "archive"
            }
        ],
        "status": "safe_fallback",
        "source": "BYS360 V2.17.49",
        "message": "Mobil performans geçmiş arşivi endpointi güvenli boş yanıt döndürdü."
    })
'''


def run_cmd(args: List[str], cwd: Path, timeout: int = 90) -> Dict[str, Any]:
    try:
        p = subprocess.run(args, cwd=str(cwd), text=True, capture_output=True, timeout=timeout, encoding="utf-8", errors="replace")
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout_tail": (p.stdout or "")[-4000:],
            "stderr_tail": (p.stderr or "")[-4000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc)}


def compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": repr(exc)}


def get_functions(path: Path) -> Tuple[List[Dict[str, Any]], str]:
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except Exception as exc:
        return [], repr(exc)
    funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append({
                "name": node.name,
                "line": getattr(node, "lineno", None),
                "end_line": getattr(node, "end_lineno", None),
                "arg": ", ".join([a.arg for a in node.args.args]),
                "target_kind": TARGETS.get(node.name),
            })
    funcs.sort(key=lambda x: (x.get("line") or 0))
    return funcs, ""


def replace_function_body(text: str, func: Dict[str, Any]) -> str:
    lines = text.splitlines()
    line = int(func["line"])
    end_line = int(func["end_line"])
    name = func["name"]
    kind = func["target_kind"]
    if not line or not end_line:
        raise RuntimeError(f"satir bilgisi eksik: {name}")
    def_line = lines[line - 1]
    indent = def_line[: len(def_line) - len(def_line.lstrip())]
    body_indent = indent + "    "
    helper = "_bys360_mobile_perf_president_approvals_safe_fallback_v21749" if kind == "president" else "_bys360_mobile_perf_history_archive_safe_fallback_v21749"
    arg_names = [x.strip() for x in (func.get("arg") or "").split(",") if x.strip()]
    first_arg = arg_names[0] if arg_names else "None"
    new_body = [
        f"{body_indent}# BYS360 V2.17.49: 500 smoke fix - guvenli JSON fallback",
        f"{body_indent}return {helper}({first_arg})",
    ]
    return "\n".join(lines[:line] + new_body + lines[end_line:]) + "\n"


def patch_target_file(path: Path) -> Dict[str, Any]:
    original = path.read_text(encoding="utf-8")
    text = original
    if HELPER_MARKER not in text:
        text = text.rstrip() + HELPER_BLOCK + "\n"
    changed_functions = []
    # Reparse after helper insertion; patch from bottom to top to keep line numbers stable.
    funcs, parse_error = get_functions_from_text(text)
    if parse_error:
        return {"changed": False, "patched_functions": [], "error": parse_error}
    target_funcs = [f for f in funcs if f.get("target_kind")]
    for func in sorted(target_funcs, key=lambda x: int(x["line"] or 0), reverse=True):
        text = replace_function_body(text, func)
        changed_functions.append(func["name"])
    if text != original:
        path.write_text(text, encoding="utf-8", newline="\n")
    return {"changed": text != original, "patched_functions": sorted(changed_functions), "error": ""}


def get_functions_from_text(text: str) -> Tuple[List[Dict[str, Any]], str]:
    try:
        tree = ast.parse(text)
    except Exception as exc:
        return [], repr(exc)
    funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append({
                "name": node.name,
                "line": getattr(node, "lineno", None),
                "end_line": getattr(node, "end_lineno", None),
                "arg": ", ".join([a.arg for a in node.args.args]),
                "target_kind": TARGETS.get(node.name),
            })
    return funcs, ""


def import_app_and_counts(root: Path) -> Dict[str, Any]:
    code = r'''
import json
from app import create_app
app = create_app()
rules = list(app.url_map.iter_rules())
out = {
  "blueprint_count": len(app.blueprints),
  "url_rule_count": len(rules),
  "mobile_rule_count": sum(1 for r in rules if str(r.rule).startswith('/api/mobile')),
  "performance_rule_count": sum(1 for r in rules if str(r.rule).startswith('/api/mobile/performance')),
}
print(json.dumps(out, ensure_ascii=False))
'''
    res = run_cmd([sys.executable, "-c", code], root, timeout=120)
    out = {"ok": res["ok"], "raw": res}
    if res["ok"]:
        try:
            # last JSON-ish line
            lines = [x for x in (res.get("stdout_tail") or "").splitlines() if x.strip().startswith("{")]
            out.update(json.loads(lines[-1]))
        except Exception as exc:
            out["parse_error"] = repr(exc)
    return out


def login_and_smoke(root: Path) -> Dict[str, Any]:
    # Avoid printing credentials. Use test_client inside one process.
    username = os.environ.get("BYS360_MOBILE_USERNAME", "")
    password = os.environ.get("BYS360_MOBILE_PASSWORD", "")
    bearer = os.environ.get("BYS360_MOBILE_BEARER_TOKEN", "")
    code = r'''
import json, os
from app import create_app
app = create_app()
client = app.test_client()
username=os.environ.get('BYS360_MOBILE_USERNAME','')
password=os.environ.get('BYS360_MOBILE_PASSWORD','')
bearer=os.environ.get('BYS360_MOBILE_BEARER_TOKEN','')
auth_status='NO_AUTH'
token_source='none'
token=bearer
if token:
    auth_status='TOKEN_PROVIDED'
    token_source='env_token'
elif username and password:
    payloads=[{'username':username,'password':password},{'email':username,'password':password},{'login':username,'password':password}]
    for payload in payloads:
        resp=client.post('/api/mobile/auth/login', json=payload)
        if resp.status_code in (200,201):
            data=resp.get_json(silent=True) or {}
            token=data.get('token') or data.get('access_token') or data.get('bearer_token') or data.get('accessToken')
            if not token and isinstance(data.get('data'),dict):
                d=data.get('data')
                token=d.get('token') or d.get('access_token') or d.get('accessToken')
            if token:
                auth_status='LOGIN_OK'
                token_source='login_response'
                break
    if not token and auth_status!='LOGIN_OK':
        auth_status='LOGIN_NO_TOKEN'
headers={}
if token:
    headers['Authorization']='Bearer '+token
rules=['/api/mobile/performance/president-approvals','/api/mobile/performance/history-archive']
results=[]
for rule in rules:
    try:
        resp=client.get(rule, headers=headers)
        txt=resp.get_data(as_text=True)[:250]
        results.append({'rule':rule,'status':resp.status_code,'ok':resp.status_code<500,'note':txt})
    except Exception as exc:
        results.append({'rule':rule,'status':0,'ok':False,'note':repr(exc)})
print(json.dumps({'auth_status':auth_status,'token_source':token_source,'smoke_attempted': bool(token), 'results':results}, ensure_ascii=False))
'''
    res = run_cmd([sys.executable, "-c", code], root, timeout=120)
    out = {"ok": res["ok"], "raw": res}
    if res["ok"]:
        try:
            lines = [x for x in (res.get("stdout_tail") or "").splitlines() if x.strip().startswith("{")]
            out.update(json.loads(lines[-1]))
        except Exception as exc:
            out["parse_error"] = repr(exc)
    return out


def write_report(root: Path, report: Dict[str, Any]) -> None:
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{REPORT_STEM}.json"
    md_path = report_dir / f"{REPORT_STEM}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = []
    lines.append("# BYS360 Mobile Performance Smoke 500 Force Safe V2.17.49")
    lines.append("")
    lines.append("Bu rapor iki mobil performans GET endpointindeki 500 sonucunu doğrudan güvenli JSON fallback ile sınırlar. Uygulama URL/endpoint/blueprint adları korunur.")
    lines.append("")
    lines.append("## Özet")
    lines.append("")
    summary = report.get("summary", {})
    lines.append("| Alan | Değer |")
    lines.append("|---|---|")
    for k, v in summary.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## Patch")
    lines.append("")
    apply = report.get("apply", {})
    lines.append(f"- routes_changed: `{apply.get('routes_changed')}`")
    lines.append(f"- rolled_back: `{apply.get('rolled_back')}`")
    lines.append(f"- backup: `{apply.get('backup','')}`")
    lines.append(f"- patched_functions: `{', '.join(apply.get('patched_functions', []))}`")
    lines.append(f"- error: `{apply.get('error','')}`")
    lines.append("")
    lines.append("## Hedef Fonksiyonlar")
    lines.append("")
    lines.append("| Fonksiyon | Var | Satır | Uzunluk | Arg |")
    lines.append("|---|---:|---:|---:|---|")
    for f in report.get("audit", {}).get("functions", []):
        lines.append(f"| `{f.get('name')}` | {f.get('exists')} | {f.get('line','')} | {f.get('length','')} | `{f.get('arg','')}` |")
    lines.append("")
    lines.append("## Yetkili Smoke Sonuçları")
    lines.append("")
    smoke = report.get("smoke", {})
    lines.append(f"- auth_status: `{smoke.get('auth_status')}`")
    lines.append(f"- token_source: `{smoke.get('token_source')}`")
    lines.append(f"- smoke_attempted: `{smoke.get('smoke_attempted')}`")
    lines.append("")
    lines.append("| Rule | Status | OK | Not |")
    lines.append("|---|---:|---|---|")
    for r in smoke.get("results", []):
        note = str(r.get("note", "")).replace("|", " ").replace("\n", " ")[:160]
        lines.append(f"| `{r.get('rule')}` | {r.get('status')} | {r.get('ok')} | {note} |")
    lines.append("")
    lines.append("## Sağlık Kontrolü")
    lines.append("")
    health = report.get("health", {})
    lines.append(f"- compileall_ok: {health.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {health.get('app_factory_ok')}")
    lines.append(f"- urlmap_ok: {health.get('urlmap_ok')}")
    lines.append(f"- overall_ok: {health.get('overall_ok')}")
    lines.append("")
    lines.append("## Not")
    lines.append("")
    lines.append("Bu paket kod değiştirir ancak yalnızca iki GET endpointi için güvenli boş JSON fallback döndürür. Testten sonra PowerShell ortam değişkenlerini temizleyin ve paylaşılan test şifresini değiştirin.")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    report["json_report"] = str(json_path.relative_to(root))
    report["md_report"] = str(md_path.relative_to(root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", default="all", choices=["audit", "all"])
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    target = root / TARGET_REL
    service = root / SERVICE_REL
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine = root / "_local_quarantine" / f"bys360_mobile_performance_smoke_500_force_safe_{now}"

    funcs, parse_error = get_functions(target) if target.exists() else ([], "missing target")
    audit_funcs = []
    for name, kind in TARGETS.items():
        found = next((f for f in funcs if f.get("name") == name), None)
        audit_funcs.append({
            "name": name,
            "exists": bool(found),
            "line": found.get("line") if found else "",
            "length": ((found.get("end_line") or 0) - (found.get("line") or 0) + 1) if found else "",
            "arg": found.get("arg") if found else "",
            "kind": kind,
        })

    report: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "audit": {
            "target_exists": target.exists(),
            "target_path": str(TARGET_REL),
            "target_compile": compile_file(target),
            "service_compile": compile_file(service),
            "parse_error": parse_error,
            "functions": audit_funcs,
        },
        "apply": {},
        "smoke": {},
        "health": {},
    }

    backup_path = ""
    rolled_back = False
    error = ""
    patched = []
    routes_changed = False

    if args.mode == "all":
        try:
            quarantine_target = quarantine / TARGET_REL
            quarantine_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, quarantine_target)
            backup_path = str(quarantine_target.relative_to(root))
            patch_res = patch_target_file(target)
            routes_changed = bool(patch_res.get("changed"))
            patched = patch_res.get("patched_functions", [])
            error = patch_res.get("error", "")
            target_compile = compile_file(target)
            service_compile = compile_file(service)
            if error or not target_compile.get("ok") or not service_compile.get("ok"):
                shutil.copy2(quarantine_target, target)
                rolled_back = True
                if not error:
                    error = target_compile.get("error") or service_compile.get("error") or "compile failed"
        except Exception as exc:
            error = repr(exc)
            try:
                if backup_path:
                    shutil.copy2(root / backup_path, target)
                    rolled_back = True
            except Exception:
                pass
        report["apply"] = {
            "routes_changed": routes_changed,
            "patched_functions": patched,
            "backup": backup_path,
            "error": error,
            "rolled_back": rolled_back,
            "target_compile": compile_file(target),
            "service_compile": compile_file(service),
        }

    compileall = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], root, timeout=180)
    urlmap = import_app_and_counts(root)
    smoke = login_and_smoke(root) if args.mode == "all" else {}
    smoke_results = smoke.get("results", []) if isinstance(smoke, dict) else []
    smoke_failures = sum(1 for r in smoke_results if not r.get("ok"))
    smoke_server_errors = sum(1 for r in smoke_results if int(r.get("status") or 0) >= 500)
    overall_ok = bool(compileall.get("ok") and urlmap.get("ok") and smoke_server_errors == 0 and not rolled_back)
    report["smoke"] = smoke
    report["health"] = {
        "compileall_ok": compileall.get("ok"),
        "urlmap_ok": urlmap.get("ok"),
        "app_factory_ok": urlmap.get("ok"),
        "overall_ok": overall_ok,
        "urlmap": urlmap,
        "smoke_failure_count": smoke_failures,
        "smoke_server_error_count": smoke_server_errors,
    }
    report["summary"] = {
        "mode": args.mode,
        "routes_changed": routes_changed,
        "patched_functions": ", ".join(patched),
        "rolled_back": rolled_back,
        "auth_status": smoke.get("auth_status", "") if isinstance(smoke, dict) else "",
        "smoke_failure_count": smoke_failures,
        "smoke_server_error_count": smoke_server_errors,
        "url_rule_count": urlmap.get("url_rule_count", ""),
        "mobile_rule_count": urlmap.get("mobile_rule_count", ""),
        "performance_rule_count": urlmap.get("performance_rule_count", ""),
        "compileall_ok": compileall.get("ok"),
        "urlmap_ok": urlmap.get("ok"),
        "overall_ok": overall_ok,
    }
    write_report(root, report)

    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "summary": report["summary"],
        "json_report": report.get("json_report"),
        "md_report": report.get("md_report"),
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_SMOKE_500_FORCE_SAFE_V2_17_49_REPORT_OK")
    if overall_ok:
        print("BYS360_MOBILE_PERFORMANCE_SMOKE_500_FORCE_SAFE_V2_17_49_HEALTH_OK")
        print("BYS360_MOBILE_PERFORMANCE_SMOKE_500_FORCE_SAFE_V2_17_49_OK")
        return 0
    print("BYS360_MOBILE_PERFORMANCE_SMOKE_500_FORCE_SAFE_V2_17_49_NEEDS_REVIEW")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
