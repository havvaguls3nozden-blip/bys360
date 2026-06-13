#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BYS360 Mobile Performance Smoke Test P2.8 V2.17.33

Kod degistirmez. Flask app.url_map uzerinden mobil performans GET endpointlerini bulur,
kimliksiz test_client istekleriyle endpointlerin 5xx/exception uretmedigini kontrol eder.
401/403/302 gibi yetki/oturum cevaplari smoke icin kabul edilebilir sayilir.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "V2.17.33"
MARKER = "BYS360_MOBILE_PERFORMANCE_SMOKE_TEST_P2_8_V2_17_33"

REFACTORED_PERFORMANCE_RULES = [
    "/api/mobile/performance/summary",
    "/api/mobile/performance/full-feature-summary",
    "/api/mobile/performance/history-archive",
    "/api/mobile/performance/reports",
    "/api/mobile/performance/risk-analysis",
    "/api/mobile/performance/development-suggestions",
]

ACCEPTABLE_SMOKE_STATUSES = {200, 204, 301, 302, 304, 400, 401, 403, 404, 405, 422}


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def run_cmd(root: Path, args: List[str], timeout: int = 60) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-6000:],
            "stderr_tail": proc.stderr[-6000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": 124,
            "stdout_tail": (exc.stdout or "")[-6000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-6000:] if isinstance(exc.stderr, str) else "timeout",
        }
    except Exception as exc:
        return {"ok": False, "returncode": 1, "stdout_tail": "", "stderr_tail": repr(exc)}


def compile_target(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    try:
        compile(path.read_text(encoding="utf-8", errors="replace"), str(path), "exec")
        return {"exists": True, "ok": True, "error": ""}
    except SyntaxError as exc:
        return {"exists": True, "ok": False, "error": f"{exc.__class__.__name__}: {exc.msg} line={exc.lineno}"}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": repr(exc)}


def import_app(root: Path) -> Tuple[Optional[Any], Dict[str, Any]]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.chdir(root)
    try:
        from app import create_app  # type: ignore

        app = create_app()
        return app, {"ok": True, "error": "", "blueprint_count": len(getattr(app, "blueprints", {}))}
    except Exception as exc:
        return None, {"ok": False, "error": repr(exc), "blueprint_count": 0}


def rule_to_row(rule: Any) -> Dict[str, Any]:
    methods = sorted([m for m in getattr(rule, "methods", set()) if m not in {"HEAD", "OPTIONS"}])
    return {
        "rule": str(rule.rule),
        "endpoint": str(rule.endpoint),
        "methods": methods,
        "arguments": sorted(list(getattr(rule, "arguments", set()))),
    }


def collect_urlmap(app: Any) -> Dict[str, Any]:
    rows = [rule_to_row(rule) for rule in app.url_map.iter_rules()]
    api_rules = [r for r in rows if r["rule"].startswith("/api/")]
    mobile_rules = [r for r in rows if r["rule"].startswith("/api/mobile")]
    performance_rules = [r for r in rows if r["rule"].startswith("/api/mobile/performance")]
    safe_get = [r for r in performance_rules if "GET" in r["methods"] and not r["arguments"]]
    refactored = [r for r in performance_rules if r["rule"] in REFACTORED_PERFORMANCE_RULES]
    return {
        "url_rule_count": len(rows),
        "api_rule_count": len(api_rules),
        "mobile_rule_count": len(mobile_rules),
        "performance_rule_count": len(performance_rules),
        "safe_get_candidate_count": len(safe_get),
        "refactored_target_count": len(refactored),
        "performance_rules": performance_rules,
        "safe_get_candidates": safe_get,
        "refactored_targets": refactored,
        "missing_refactored_rules": [r for r in REFACTORED_PERFORMANCE_RULES if r not in {x["rule"] for x in refactored}],
    }


def smoke_gets(app: Any, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = app.test_client()
    headers: Dict[str, str] = {}
    token = os.environ.get("BYS360_MOBILE_SMOKE_TOKEN") or os.environ.get("BYS360_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results: List[Dict[str, Any]] = []
    for row in rules:
        rule = row["rule"]
        endpoint = row["endpoint"]
        try:
            resp = client.get(rule, headers=headers, follow_redirects=False)
            status = int(resp.status_code)
            ok = status in ACCEPTABLE_SMOKE_STATUSES and status < 500
            content_type = resp.headers.get("Content-Type", "")
            body_sample = ""
            try:
                body_sample = resp.get_data(as_text=True)[:240]
            except Exception:
                body_sample = ""
            results.append(
                {
                    "rule": rule,
                    "endpoint": endpoint,
                    "status": status,
                    "ok": ok,
                    "content_type": content_type,
                    "body_sample": body_sample.replace("\n", " ").replace("\r", " "),
                    "error": "",
                }
            )
        except Exception as exc:
            results.append(
                {
                    "rule": rule,
                    "endpoint": endpoint,
                    "status": 599,
                    "ok": False,
                    "content_type": "",
                    "body_sample": "",
                    "error": repr(exc),
                }
            )
    failures = [r for r in results if not r["ok"]]
    server_errors = [r for r in results if int(r.get("status") or 0) >= 500]
    return {
        "tested_count": len(results),
        "ok_count": len(results) - len(failures),
        "failure_count": len(failures),
        "server_error_count": len(server_errors),
        "results": results,
        "failures": failures,
    }


def write_reports(root: Path, report: Dict[str, Any]) -> None:
    out_dir = root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "bys360_mobile_performance_smoke_test_p2_8_v2_17_33_report.json"
    md_path = out_dir / "bys360_mobile_performance_smoke_test_p2_8_v2_17_33_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    urlmap = report.get("urlmap", {})
    smoke = report.get("smoke", {})
    health = report.get("health_summary", {})
    lines: List[str] = []
    lines.append("# BYS360 Mobile Performance Smoke Test P2.8 V2.17.33")
    lines.append("")
    lines.append("Bu rapor uygulama dosyalarını değiştirmez. Mobil performans refactor sonrası güvenli GET endpointlerini Flask test client ile yoklar.")
    lines.append("")
    lines.append("## Özet")
    lines.append(f"- mode: {report.get('mode')}")
    lines.append(f"- url_rule_count: {urlmap.get('url_rule_count', 0)}")
    lines.append(f"- mobile_rule_count: {urlmap.get('mobile_rule_count', 0)}")
    lines.append(f"- performance_rule_count: {urlmap.get('performance_rule_count', 0)}")
    lines.append(f"- safe_get_candidate_count: {urlmap.get('safe_get_candidate_count', 0)}")
    lines.append(f"- refactored_target_count: {urlmap.get('refactored_target_count', 0)}")
    lines.append(f"- missing_refactored_rules: {urlmap.get('missing_refactored_rules', [])}")
    lines.append(f"- smoke_tested_count: {smoke.get('tested_count', 0)}")
    lines.append(f"- smoke_ok_count: {smoke.get('ok_count', 0)}")
    lines.append(f"- smoke_failure_count: {smoke.get('failure_count', 0)}")
    lines.append(f"- smoke_server_error_count: {smoke.get('server_error_count', 0)}")
    lines.append(f"- compileall_ok: {health.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {health.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {health.get('overall_ok')}")
    lines.append("")
    lines.append("## Refactor Edilen Performans Endpointleri")
    lines.append("| Method | Rule | Endpoint | Smoke Status | Smoke OK |")
    lines.append("|---|---|---|---:|---|")
    smoke_by_rule = {r["rule"]: r for r in smoke.get("results", [])}
    for row in urlmap.get("refactored_targets", []):
        sr = smoke_by_rule.get(row["rule"], {})
        lines.append(f"| {','.join(row.get('methods', []))} | `{row['rule']}` | `{row['endpoint']}` | {sr.get('status', '')} | {sr.get('ok', '')} |")
    lines.append("")
    lines.append("## Güvenli GET Smoke Sonuçları")
    lines.append("| Rule | Endpoint | Status | OK | Not |")
    lines.append("|---|---|---:|---|---|")
    for r in smoke.get("results", []):
        note = r.get("error") or r.get("body_sample", "")[:80]
        lines.append(f"| `{r['rule']}` | `{r['endpoint']}` | {r['status']} | {r['ok']} | {note} |")
    if not smoke.get("results"):
        lines.append("| - | - | - | - | Smoke adayı bulunamadı. |")
    lines.append("")
    lines.append("## Sağlık Kontrolü")
    lines.append(f"- compileall_ok: {health.get('compileall_ok')}")
    lines.append(f"- app_factory_ok: {health.get('app_factory_ok')}")
    lines.append(f"- overall_ok: {health.get('overall_ok')}")
    lines.append("")
    lines.append("## Not")
    lines.append("401/403/302/404 gibi cevaplar smoke açısından kabul edilebilir sayılmıştır; amaç endpointlerin 5xx veya exception üretmediğini görmektir. Gerçek kullanıcı yetkili mobil test ayrıca yapılmalıdır.")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    report["json_report"] = rel(root, json_path)
    report["md_report"] = rel(root, md_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=os.getcwd())
    parser.add_argument("--mode", choices=["audit", "all"], default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    report: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "targets": {
            "performance_routes": compile_target(root / "app" / "api" / "mobile" / "performance_routes.py"),
            "performance_summary_service": compile_target(root / "app" / "api" / "mobile" / "services" / "performance_summary_service.py"),
        },
        "app_factory": {},
        "urlmap": {},
        "smoke": {},
        "health_summary": {},
    }

    app, app_info = import_app(root)
    report["app_factory"] = app_info
    if app is not None:
        report["urlmap"] = collect_urlmap(app)
    else:
        report["urlmap"] = {
            "url_rule_count": 0,
            "api_rule_count": 0,
            "mobile_rule_count": 0,
            "performance_rule_count": 0,
            "safe_get_candidate_count": 0,
            "refactored_target_count": 0,
            "performance_rules": [],
            "safe_get_candidates": [],
            "refactored_targets": [],
            "missing_refactored_rules": REFACTORED_PERFORMANCE_RULES,
        }

    if args.mode == "all" and app is not None:
        # Smoke only safe GETs, but prioritize refactored endpoints by including them first.
        urlmap = report["urlmap"]
        ordered: List[Dict[str, Any]] = []
        seen = set()
        for row in urlmap.get("refactored_targets", []):
            if "GET" in row.get("methods", []) and not row.get("arguments") and row["rule"] not in seen:
                ordered.append(row); seen.add(row["rule"])
        for row in urlmap.get("safe_get_candidates", []):
            if row["rule"] not in seen:
                ordered.append(row); seen.add(row["rule"])
        report["smoke"] = smoke_gets(app, ordered)
    else:
        report["smoke"] = {"tested_count": 0, "ok_count": 0, "failure_count": 0, "server_error_count": 0, "results": [], "failures": []}

    compileall = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=120)
    app_ok = bool(app_info.get("ok"))
    smoke_ok = int(report["smoke"].get("server_error_count", 0)) == 0 and int(report["smoke"].get("failure_count", 0)) == 0
    if args.mode == "audit":
        smoke_ok = True
    overall = bool(compileall.get("ok")) and app_ok and smoke_ok
    report["health_summary"] = {
        "compileall_ok": bool(compileall.get("ok")),
        "app_factory_ok": app_ok,
        "smoke_ok": smoke_ok,
        "overall_ok": overall,
        "compileall": compileall,
    }

    write_reports(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "urlmap_summary": {k: report["urlmap"].get(k) for k in ["url_rule_count", "mobile_rule_count", "performance_rule_count", "safe_get_candidate_count", "refactored_target_count", "missing_refactored_rules"]},
        "smoke_summary": {k: report["smoke"].get(k) for k in ["tested_count", "ok_count", "failure_count", "server_error_count"]},
        "health_summary": {k: report["health_summary"].get(k) for k in ["compileall_ok", "app_factory_ok", "smoke_ok", "overall_ok"]},
        "json_report": report.get("json_report"),
        "md_report": report.get("md_report"),
    }, ensure_ascii=False, indent=2))
    print(f"{MARKER}_REPORT_OK")
    if report["health_summary"]["overall_ok"]:
        print(f"{MARKER}_HEALTH_OK")
        print(f"{MARKER}_OK")
        return 0
    print(f"{MARKER}_HEALTH_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
