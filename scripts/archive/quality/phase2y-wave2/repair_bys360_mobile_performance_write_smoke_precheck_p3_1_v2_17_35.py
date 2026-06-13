
# -*- coding: utf-8 -*-
"""
BYS360 Mobile Performance Write Smoke Precheck P3.1 V2.17.35
Kod değiştirmez. Yazma/işlem endpointleri için Flask url_map, fonksiyon envanteri ve güvenli OPTIONS smoke ön kontrolü üretir.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "V2.17.35"
REPORT_STEM = "bys360_mobile_performance_write_smoke_precheck_p3_1_v2_17_35_report"
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SAFE_OK_STATUS_MAX = 499

WRITE_KEYWORDS = (
    "submit", "score_action", "create", "publish", "approval", "approvals",
    "preapproval", "return", "withdraw", "note", "send", "delete", "update"
)
HIGH_RISK_KEYWORDS = ("score_submit", "task_score_submit", "score-form", "score_form")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


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
            "stdout_tail": cp.stdout[-6000:],
            "stderr_tail": cp.stderr[-6000:],
        }
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc)}


def compile_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "not_found"}
    try:
        compile(path.read_text(encoding="utf-8", errors="replace"), str(path), "exec")
        return {"exists": True, "ok": True, "error": ""}
    except SyntaxError as exc:
        return {"exists": True, "ok": False, "error": f"{exc.__class__.__name__}: {exc.msg} line={exc.lineno}"}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": repr(exc)}


def parse_functions(path: Path) -> Tuple[List[Dict[str, Any]], str]:
    if not path.exists():
        return [], "not_found"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
    except Exception as exc:
        return [], repr(exc)
    funcs = []
    lines = text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            end = getattr(node, "end_lineno", node.lineno)
            body_text = "\n".join(lines[node.lineno - 1:end])
            delegated = "delegate" in body_text or "services." in body_text or "_service" in body_text
            legacy = name.startswith("_bys360_legacy_")
            route_decorator = any(
                isinstance(d, ast.Call) and getattr(getattr(d.func, "attr", None), "lower", lambda: "")() == "route"
                or isinstance(d, ast.Call) and getattr(getattr(d.func, "attr", ""), "lower", lambda: "")() in {"get", "post", "put", "patch", "delete"}
                for d in getattr(node, "decorator_list", [])
            )
            args = [a.arg for a in node.args.args]
            write_like = any(k in name.lower() for k in WRITE_KEYWORDS)
            high = any(k in name.lower() for k in HIGH_RISK_KEYWORDS)
            funcs.append({
                "name": name,
                "line": node.lineno,
                "end_line": end,
                "length": max(1, end - node.lineno + 1),
                "arg": ", ".join(args),
                "route_decorator": route_decorator,
                "delegated": delegated,
                "legacy": legacy,
                "write_like": write_like,
                "risk": "high" if high else ("medium" if write_like else "low"),
            })
    funcs.sort(key=lambda x: (not x["write_like"], -x["length"], x["name"]))
    return funcs, ""


def sample_rule(rule: str) -> str:
    # Flask converter örnekleri: <int:id>, <id>, <path:name>
    def repl(m: re.Match) -> str:
        inside = m.group(1)
        if ":" in inside:
            conv, _name = inside.split(":", 1)
            conv = conv.strip()
            if conv in {"int", "float"}:
                return "1"
            if conv == "path":
                return "sample"
            return "sample"
        return "1"
    return re.sub(r"<([^>]+)>", repl, rule)


def make_app(root: Path):
    sys.path.insert(0, str(root))
    oldcwd = os.getcwd()
    os.chdir(str(root))
    try:
        from app import create_app  # type: ignore
        app = create_app()
        return app, ""
    except Exception as exc:
        return None, repr(exc)
    finally:
        os.chdir(oldcwd)


def urlmap_probe(root: Path, mode: str) -> Dict[str, Any]:
    app, err = make_app(root)
    if app is None:
        return {"ok": False, "error": err, "rules": [], "write_rules": [], "safe_options_smoke": []}

    rules = []
    write_rules = []
    for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
        methods = sorted((set(r.methods or []) - {"HEAD", "OPTIONS"}))
        endpoint = r.endpoint
        if not r.rule.startswith("/api/mobile/performance"):
            continue
        row = {
            "rule": r.rule,
            "endpoint": endpoint,
            "methods": methods,
            "arguments": sorted(list(r.arguments or [])),
            "sample_rule": sample_rule(r.rule),
        }
        rules.append(row)
        if any(m in WRITE_METHODS for m in methods):
            wr = dict(row)
            wr["write_methods"] = [m for m in methods if m in WRITE_METHODS]
            wr["risk"] = "high" if any(x in r.rule for x in ["score-form", "score-action"]) else "medium"
            write_rules.append(wr)

    smoke = []
    if mode == "all":
        client = app.test_client()
        for wr in write_rules:
            try:
                # OPTIONS güvenlidir; gerçek POST/PUT/PATCH/DELETE çalıştırılmaz.
                resp = client.open(wr["sample_rule"], method="OPTIONS")
                status = int(getattr(resp, "status_code", 0) or 0)
                smoke.append({
                    "rule": wr["rule"],
                    "sample_rule": wr["sample_rule"],
                    "endpoint": wr["endpoint"],
                    "method": "OPTIONS",
                    "status": status,
                    "ok": status < 500,
                    "note": "OPTIONS dry-run; gerçek yazma metodu çalıştırılmadı.",
                })
            except Exception as exc:
                smoke.append({
                    "rule": wr["rule"],
                    "sample_rule": wr["sample_rule"],
                    "endpoint": wr["endpoint"],
                    "method": "OPTIONS",
                    "status": None,
                    "ok": False,
                    "note": repr(exc),
                })
    return {"ok": True, "error": "", "rules": rules, "write_rules": write_rules, "safe_options_smoke": smoke}


def write_reports(root: Path, report: Dict[str, Any]) -> Tuple[Path, Path]:
    outdir = root / "reports" / "quality"
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / f"{REPORT_STEM}.json"
    md_path = outdir / f"{REPORT_STEM}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append(f"# BYS360 Mobile Performance Write Smoke Precheck P3.1 {VERSION}")
    lines.append("")
    lines.append("Bu rapor uygulama dosyalarını değiştirmez. P3 yazma/işlem endpointlerine geçmeden önce gerçek URL haritası, risk envanteri ve güvenli OPTIONS dry-run sonucunu çıkarır.")
    lines.append("")
    s = report.get("summary", {})
    lines.append("## Özet")
    for k, v in s.items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## Performans Yazma URLMap")
    lines.append("| Method | Rule | Endpoint | Arg | Risk |")
    lines.append("|---|---|---|---|---|")
    wrs = report.get("urlmap", {}).get("write_rules", [])
    if not wrs:
        lines.append("|  | Yazma endpointi bulunamadı |  |  |  |")
    else:
        for wr in wrs:
            lines.append(f"| {','.join(wr.get('write_methods', []))} | `{wr.get('rule')}` | `{wr.get('endpoint')}` | `{', '.join(wr.get('arguments', []))}` | {wr.get('risk')} |")
    lines.append("")

    lines.append("## Güvenli OPTIONS Dry-run Sonuçları")
    lines.append("Gerçek POST/PUT/PATCH/DELETE çağrısı yapılmaz; sadece route seviyesinde 5xx/exception kontrolü için OPTIONS kullanılır.")
    lines.append("")
    lines.append("| Rule | Endpoint | Status | OK | Not |")
    lines.append("|---|---|---:|---|---|")
    smoke = report.get("urlmap", {}).get("safe_options_smoke", [])
    if not smoke:
        lines.append("|  | Çalıştırılmadı veya aday yok |  |  |  |")
    else:
        for x in smoke:
            lines.append(f"| `{x.get('rule')}` | `{x.get('endpoint')}` | {x.get('status')} | {x.get('ok')} | {x.get('note')} |")
    lines.append("")

    lines.append("## Yazma/İşlem Fonksiyon Adayları İlk 40")
    lines.append("| Fonksiyon | Satır | Uzunluk | Delegated | Legacy | Risk | Arg |")
    lines.append("|---|---:|---:|---:|---:|---|---|")
    funcs = report.get("function_inventory", {}).get("write_like_functions", [])[:40]
    if not funcs:
        lines.append("|  |  |  |  |  | Aday yok |  |")
    else:
        for f in funcs:
            lines.append(f"| `{f.get('name')}` | {f.get('line')} | {f.get('length')} | {f.get('delegated')} | {f.get('legacy')} | {f.get('risk')} | `{f.get('arg')}` |")
    lines.append("")

    lines.append("## Önerilen Güvenli P3 Sırası")
    lines.append("1. Gerçek POST/PUT/PATCH/DELETE refactor’una hemen geçme; önce helper/payload fonksiyonları servis katmanına alınmalı.")
    lines.append("2. `mobile_performance_task_score_submit` yüksek riskli olduğu için en sona yakın ve ayrı rollback paketinde ele alınmalı.")
    lines.append("3. Dönem içi not oluşturma ve onay/yayın fonksiyonları gerçek yetkili mobil token ile ayrıca smoke test edilmeden patchlenmemeli.")
    lines.append("4. OPTIONS dry-run 5xx vermiyorsa P3.2 için sadece helper delegasyonu yapılabilir.")
    lines.append("")

    h = report.get("health_summary", {})
    lines.append("## Sağlık Kontrolü")
    lines.append(f"- compileall_ok: {h.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {h.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {h.get('overall_ok')}")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", default="all", choices=["audit", "all"])
    ns = ap.parse_args()
    root = Path(ns.project_root).resolve()

    perf = root / "app" / "api" / "mobile" / "performance_routes.py"
    compileall = run_cmd([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], root, timeout=180)
    target_compile = compile_file(perf)
    urlmap = urlmap_probe(root, ns.mode)
    funcs, parse_err = parse_functions(perf)
    write_like = [f for f in funcs if f.get("write_like") and not f.get("legacy")]

    app_factory_ok = bool(urlmap.get("ok"))
    options = urlmap.get("safe_options_smoke", []) or []
    options_ok = all(x.get("ok") for x in options) if ns.mode == "all" and options else True
    overall = bool(compileall.get("ok") and app_factory_ok and target_compile.get("ok") and options_ok)

    summary = {
        "mode": ns.mode,
        "performance_file_exists": perf.exists(),
        "performance_file_kb": round(perf.stat().st_size / 1024, 1) if perf.exists() else 0,
        "performance_function_count": len(funcs),
        "parse_error": parse_err,
        "urlmap_ok": urlmap.get("ok"),
        "performance_urlmap_count": len(urlmap.get("rules", [])),
        "write_urlmap_count": len(urlmap.get("write_rules", [])),
        "options_dryrun_count": len(options),
        "options_dryrun_ok_count": sum(1 for x in options if x.get("ok")),
        "write_like_function_count": len(write_like),
        "high_risk_write_like_count": sum(1 for x in write_like if x.get("risk") == "high"),
        "compileall_ok": compileall.get("ok"),
        "app_factory_ok": app_factory_ok,
        "overall_ok": overall,
    }
    report = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "summary": summary,
        "target_compile": target_compile,
        "urlmap": urlmap,
        "function_inventory": {
            "parse_error": parse_err,
            "write_like_functions": write_like,
        },
        "health_summary": {
            "compileall_ok": compileall.get("ok"),
            "app_factory_ok": app_factory_ok,
            "options_dryrun_ok": options_ok,
            "overall_ok": overall,
            "compileall": compileall,
        },
    }
    json_path, md_path = write_reports(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": ns.mode,
        "project_root": str(root),
        "summary": summary,
        "json_report": rel(json_path, root),
        "md_report": rel(md_path, root),
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_PERFORMANCE_WRITE_SMOKE_PRECHECK_P3_1_V2_17_35_REPORT_OK")
    if overall:
        print("BYS360_MOBILE_PERFORMANCE_WRITE_SMOKE_PRECHECK_P3_1_V2_17_35_HEALTH_OK")
    print("BYS360_MOBILE_PERFORMANCE_WRITE_SMOKE_PRECHECK_P3_1_V2_17_35_OK")
    return 0 if overall else 1

if __name__ == "__main__":
    raise SystemExit(main())
