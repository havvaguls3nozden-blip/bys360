# -*- coding: utf-8 -*-
"""BYS360 Teknik Borc Final Kapanis V2.17.45

Kod degistirmez. P0-P3 refactor/temizlik surecinin kapanis raporunu uretir.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

VERSION = "V2.17.45"
REPORT_BASE = "bys360_tech_debt_final_closure_v2_17_45_report"

MOBILE_FILES = [
    "app/api/mobile/routes.py",
    "app/api/mobile/performance_routes.py",
]
SERVICE_FILES = [
    "app/api/mobile/services/auth_service.py",
    "app/api/mobile/services/dashboard_service.py",
    "app/api/mobile/services/profile_service.py",
    "app/api/mobile/services/personnel_service.py",
    "app/api/mobile/services/support_service.py",
    "app/api/mobile/services/survey_service.py",
    "app/api/mobile/services/communication_service.py",
    "app/api/mobile/services/assistant_service.py",
    "app/api/mobile/services/performance_summary_service.py",
    "app/api/mobile/services/performance_task_service.py",
    "app/api/mobile/services/performance_period_service.py",
    "app/api/mobile/services/performance_evaluation_service.py",
    "app/api/mobile/services/performance_scorecard_service.py",
]

SENSITIVE_POST_KEEP = [
    "mobile_performance_task_score_submit",
    "mobile_performance_task_score_action",
    "mobile_performance_create_in_period_note_v2853",
    "mobile_performance_publish_preapproval",
    "mobile_performance_approvals",
    "mobile_performance_president_approvals_alias",
]


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 120) -> Dict[str, Any]:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout_tail": p.stdout[-5000:],
            "stderr_tail": p.stderr[-5000:],
        }
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc)}


def parse_py(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "syntax": False, "functions": [], "error": "missing"}
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {
            "exists": True,
            "syntax": False,
            "functions": [],
            "error": f"{exc.msg} line {exc.lineno}",
            "kb": round(path.stat().st_size / 1024, 1),
            "lines": text.count("\n") + 1,
        }
    funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = getattr(node, "lineno", 0)
            end = getattr(node, "end_lineno", start)
            body_text = "\n".join(text.splitlines()[start - 1 : end]) if start else ""
            funcs.append(
                {
                    "name": node.name,
                    "line": start,
                    "length": max(0, end - start + 1),
                    "delegated": ("_service" in body_text or "services." in body_text or "delegate" in body_text.lower()),
                    "legacy": node.name.startswith("_bys360_legacy"),
                }
            )
    return {
        "exists": True,
        "syntax": True,
        "functions": sorted(funcs, key=lambda x: x["line"]),
        "error": "",
        "kb": round(path.stat().st_size / 1024, 1),
        "lines": text.count("\n") + 1,
    }


def urlmap_probe(root: Path) -> Dict[str, Any]:
    code = r'''
import json
from app import create_app
app=create_app()
rules=[]
for r in app.url_map.iter_rules():
    methods=sorted([m for m in r.methods if m not in {"HEAD","OPTIONS"}])
    for m in methods:
        rules.append({"method":m,"rule":str(r),"endpoint":r.endpoint,"arguments":sorted(list(r.arguments))})
print(json.dumps({"ok":True,"blueprints":len(app.blueprints),"rule_count":len(rules),"rules":rules}, ensure_ascii=False))
'''
    p = run_cmd([sys.executable, "-c", code], cwd=root, timeout=120)
    if not p["ok"]:
        return {"ok": False, "error": p["stderr_tail"], "rule_count": 0, "mobile_count": 0, "performance_count": 0, "write_count": 0, "rules": []}
    out = p["stdout_tail"].strip().splitlines()
    data_line = out[-1] if out else "{}"
    try:
        data = json.loads(data_line)
    except Exception as exc:
        return {"ok": False, "error": f"json parse failed: {exc}", "raw": p["stdout_tail"], "rule_count": 0, "mobile_count": 0, "performance_count": 0, "write_count": 0, "rules": []}
    rules = data.get("rules", [])
    mobile = [r for r in rules if r.get("rule", "").startswith("/api/mobile")]
    perf = [r for r in mobile if "/performance" in r.get("rule", "")]
    writes = [r for r in perf if r.get("method") in {"POST", "PUT", "PATCH", "DELETE"}]
    safe_get = [r for r in perf if r.get("method") == "GET" and not r.get("arguments")]
    return {
        "ok": True,
        "blueprints": data.get("blueprints"),
        "rule_count": len(rules),
        "mobile_count": len(mobile),
        "performance_count": len(perf),
        "write_count": len(writes),
        "safe_get_count": len(safe_get),
        "writes": writes,
        "safe_get": safe_get[:50],
    }


def options_dryrun(root: Path, writes: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Use placeholders for int route args. Real write method is not invoked.
    test_paths = []
    for r in writes:
        path = r["rule"].replace("<int:assignment_id>", "1").replace("<int:period_id>", "1").replace("<int:target_id>", "1")
        test_paths.append({"rule": r["rule"], "path": path, "endpoint": r.get("endpoint", "")})
    code = """
import json
from app import create_app
app=create_app()
items = json.loads(%r)
res=[]
with app.test_client() as c:
    for item in items:
        try:
            rv = c.open(item['path'], method='OPTIONS')
            res.append({'rule':item['rule'],'endpoint':item['endpoint'],'status':rv.status_code,'ok':rv.status_code < 500})
        except Exception as exc:
            res.append({'rule':item['rule'],'endpoint':item['endpoint'],'status':0,'ok':False,'error':repr(exc)})
print(json.dumps(res, ensure_ascii=False))
""" % json.dumps(test_paths, ensure_ascii=False)
    p = run_cmd([sys.executable, "-c", code], cwd=root, timeout=120)
    if not p["ok"]:
        return {"ok": False, "items": [], "error": p["stderr_tail"]}
    try:
        items = json.loads(p["stdout_tail"].strip().splitlines()[-1])
    except Exception as exc:
        return {"ok": False, "items": [], "error": f"json parse failed: {exc}", "raw": p["stdout_tail"]}
    return {"ok": all(i.get("ok") for i in items), "items": items, "count": len(items), "ok_count": sum(1 for i in items if i.get("ok"))}


def build_report(root: Path, mode: str) -> Dict[str, Any]:
    reports_dir = root / "reports" / "quality"
    reports_dir.mkdir(parents=True, exist_ok=True)

    mobile_summaries = []
    total_functions = total_delegated = total_legacy = 0
    for rel in MOBILE_FILES:
        parsed = parse_py(root / rel)
        funcs = parsed.get("functions", [])
        total_functions += len(funcs)
        total_delegated += sum(1 for f in funcs if f.get("delegated"))
        total_legacy += sum(1 for f in funcs if f.get("legacy"))
        mobile_summaries.append({
            "path": rel,
            "exists": parsed.get("exists"),
            "syntax": parsed.get("syntax"),
            "kb": parsed.get("kb", 0),
            "lines": parsed.get("lines", 0),
            "functions": len(funcs),
            "delegated": sum(1 for f in funcs if f.get("delegated")),
            "legacy": sum(1 for f in funcs if f.get("legacy")),
            "error": parsed.get("error", ""),
        })

    service_summaries = []
    for rel in SERVICE_FILES:
        parsed = parse_py(root / rel)
        funcs = parsed.get("functions", [])
        service_summaries.append({
            "path": rel,
            "exists": parsed.get("exists"),
            "syntax": parsed.get("syntax"),
            "kb": parsed.get("kb", 0),
            "lines": parsed.get("lines", 0),
            "functions": len(funcs),
            "error": parsed.get("error", ""),
        })

    urlmap = urlmap_probe(root)
    dryrun = options_dryrun(root, urlmap.get("writes", [])) if urlmap.get("ok") else {"ok": False, "items": [], "count": 0, "ok_count": 0}

    compileall = {"ok": None}
    app_factory = {"ok": None}
    if mode in {"health", "all"}:
        compileall = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], cwd=root, timeout=180)
        app_factory = run_cmd([sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], cwd=root, timeout=120)

    overall_ok = bool((compileall.get("ok") is not False) and (app_factory.get("ok") is not False) and urlmap.get("ok") and dryrun.get("ok"))

    data = {
        "version": VERSION,
        "mode": mode,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "closure_decision": {
            "p0_repo_hygiene": "completed",
            "p1_mobile_core_api": "completed",
            "p2_mobile_performance_read_endpoints": "completed",
            "p3_mobile_performance_helpers": "completed",
            "p4_sensitive_post_endpoints": "deferred",
            "final_decision": "Stop refactor here; do not continue to P4 without authorized token smoke tests and separate rollback packages.",
        },
        "summary": {
            "mobile_target_files": len(MOBILE_FILES),
            "mobile_target_functions": total_functions,
            "delegated_functions_in_targets": total_delegated,
            "legacy_functions_in_targets": total_legacy,
            "service_files": sum(1 for s in service_summaries if s.get("exists")),
            "url_rule_count": urlmap.get("rule_count", 0),
            "mobile_rule_count": urlmap.get("mobile_count", 0),
            "performance_rule_count": urlmap.get("performance_count", 0),
            "performance_write_rule_count": urlmap.get("write_count", 0),
            "performance_safe_get_count": urlmap.get("safe_get_count", 0),
            "options_dryrun_count": dryrun.get("count", 0),
            "options_dryrun_ok_count": dryrun.get("ok_count", 0),
            "compileall_ok": compileall.get("ok"),
            "app_factory_ok": app_factory.get("ok"),
            "overall_ok": overall_ok,
        },
        "mobile_files": mobile_summaries,
        "service_files": service_summaries,
        "performance_write_rules": urlmap.get("writes", []),
        "options_dryrun": dryrun.get("items", []),
        "still_deferred_sensitive_functions": SENSITIVE_POST_KEEP,
        "health": {"compileall": compileall, "app_factory": app_factory},
    }
    return data


def md_table(headers: List[str], rows: List[List[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---" for _ in headers]) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(out)


def write_reports(root: Path, data: Dict[str, Any]) -> None:
    reports_dir = root / "reports" / "quality"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / f"{REPORT_BASE}.json"
    md_path = reports_dir / f"{REPORT_BASE}.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    s = data["summary"]
    md = []
    md.append(f"# BYS360 Teknik Borç Final Kapanış {VERSION}\n")
    md.append("Bu rapor uygulama dosyalarını değiştirmez. P0-P3 teknik borç azaltma çalışmasını güvenli noktada kapatır.\n")
    md.append("## Kapanış Kararı\n")
    md.append("- P0 repo hijyeni / temizlik: **tamamlandı**")
    md.append("- P1 mobil ana API servis delegasyonu: **tamamlandı**")
    md.append("- P2 mobil performans GET/okuma servis delegasyonu: **tamamlandı**")
    md.append("- P3 mobil performans helper servis delegasyonu: **tamamlandı**")
    md.append("- P4 hassas POST/yazma endpointleri: **ertelendi**")
    md.append("- Yeni P fazı açılmayacak; önce yetkili mobil token ile gerçek smoke test ve ayrı rollback paketi gerekir.\n")

    md.append("## Özet\n")
    md.append(md_table(
        ["Alan", "Değer"],
        [
            ["Mobil hedef dosya", s["mobile_target_files"]],
            ["Mobil hedef fonksiyon", s["mobile_target_functions"]],
            ["Delegated fonksiyon", s["delegated_functions_in_targets"]],
            ["Legacy gövde", s["legacy_functions_in_targets"]],
            ["Servis dosyası", s["service_files"]],
            ["URL rule", s["url_rule_count"]],
            ["Mobil rule", s["mobile_rule_count"]],
            ["Performans rule", s["performance_rule_count"]],
            ["Performans yazma rule", s["performance_write_rule_count"]],
            ["OPTIONS dry-run OK", f"{s['options_dryrun_ok_count']}/{s['options_dryrun_count']}"],
            ["compileall_ok", s["compileall_ok"]],
            ["app_factory_ok", s["app_factory_ok"]],
            ["overall_ok", s["overall_ok"]],
        ],
    ))
    md.append("\n## Mobil Hedef Dosyalar\n")
    md.append(md_table(["Dosya", "KB", "Satır", "Fonksiyon", "Delegated", "Legacy", "Syntax"], [[m["path"], m["kb"], m["lines"], m["functions"], m["delegated"], m["legacy"], m["syntax"]] for m in data["mobile_files"]]))
    md.append("\n## Servis Dosyaları\n")
    md.append(md_table(["Dosya", "KB", "Satır", "Fonksiyon", "Syntax"], [[m["path"], m["kb"], m["lines"], m["functions"], m["syntax"]] for m in data["service_files"]]))
    md.append("\n## P4'e Bırakılan Hassas Fonksiyonlar\n")
    for name in data["still_deferred_sensitive_functions"]:
        md.append(f"- `{name}`")
    md.append("\n## Yazma Endpointleri OPTIONS Dry-run\n")
    if data["options_dryrun"]:
        md.append(md_table(["Rule", "Endpoint", "Status", "OK"], [[x.get("rule"), x.get("endpoint"), x.get("status"), x.get("ok")] for x in data["options_dryrun"]]))
    else:
        md.append("Yazma endpointi veya dry-run sonucu bulunamadı.")
    md.append("\n## Sonuç\n")
    if s["overall_ok"]:
        md.append("**BYS360 teknik borç azaltma çalışması P3 sonrası güvenli noktada kapatılmıştır.**")
    else:
        md.append("**Kapanış raporu uyarı içeriyor. compileall/app_factory/urlmap çıktıları kontrol edilmelidir.**")
    md.append("\n## Bundan Sonra Ne Yapılmayacak?\n")
    md.append("- Yeni P6/P7/P8 fazı açılmayacak.")
    md.append("- Yetkili mobil token smoke testi olmadan puan gönderme, score-action, dönem içi not oluşturma, onay/yayın endpointleri refactor edilmeyecek.")
    md.append("- Legacy gövdeler en az bir gerçek kullanıcı smoke test turu tamamlanmadan silinmeyecek.")
    md_path.write_text("\n".join(md), encoding="utf-8")
    data["json_report"] = str(json_path.relative_to(root))
    data["md_report"] = str(md_path.relative_to(root))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default="C:/bys360/project")
    ap.add_argument("--mode", choices=["audit", "health", "all"], default="all")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    print(f"BYS360 Teknik Borc Final Kapanis {VERSION} basliyor...")
    print(f"ProjectRoot={root}")
    print(f"Mode={args.mode}")

    data = build_report(root, args.mode)
    write_reports(root, data)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "summary": data["summary"],
        "json_report": data.get("json_report"),
        "md_report": data.get("md_report"),
    }, ensure_ascii=False, indent=2))
    print("BYS360_TECH_DEBT_FINAL_CLOSURE_V2_17_45_REPORT_OK")
    if data["summary"]["overall_ok"] is False:
        print("BYS360_TECH_DEBT_FINAL_CLOSURE_V2_17_45_HEALTH_WARN")
        return 1
    print("BYS360_TECH_DEBT_FINAL_CLOSURE_V2_17_45_HEALTH_OK")
    print("BYS360_TECH_DEBT_FINAL_CLOSURE_V2_17_45_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
