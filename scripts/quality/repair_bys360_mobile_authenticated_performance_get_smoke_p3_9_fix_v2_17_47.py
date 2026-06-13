# -*- coding: utf-8 -*-
"""
BYS360 Mobile Authenticated Performance GET Smoke P3.9 FIX V2.17.47
Kod degistirmez. Raporu her durumda uretir.
- Token varsa Authorization: Bearer token ile GET smoke dener.
- Kullanici/sifre varsa once /api/mobile/auth/login dener, token yakalarsa onunla GET smoke dener.
- Kimlik bilgisi yoksa smoke'u SKIPPED_NO_CREDENTIALS olarak raporlar ama rapor yine uretilir.
"""
from __future__ import annotations

import argparse
import compileall
import io
import json
import os
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "V2.17.47"
REPORT_BASENAME = "bys360_mobile_authenticated_performance_get_smoke_p3_9_fix_v2_17_47_report"

PERFORMANCE_GET_PREFIX = "/api/mobile/performance/"


def safe_tail(text: str, limit: int = 4000) -> str:
    text = text or ""
    return text[-limit:]


def ensure_report_dir(root: Path) -> Path:
    d = root / "reports" / "quality"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_compileall(root: Path) -> Dict[str, Any]:
    buf_out, buf_err = io.StringIO(), io.StringIO()
    ok = False
    try:
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            ok = compileall.compile_dir(str(root / "app"), quiet=1, force=False)
            if (root / "config.py").exists():
                ok = compileall.compile_file(str(root / "config.py"), quiet=1, force=False) and ok
            if (root / "scripts").exists():
                ok = compileall.compile_dir(str(root / "scripts"), quiet=1, force=False) and ok
        return {"ok": bool(ok), "error": "", "stdout_tail": safe_tail(buf_out.getvalue()), "stderr_tail": safe_tail(buf_err.getvalue())}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "traceback_tail": safe_tail(traceback.format_exc())}


def create_app_and_urlmap(root: Path) -> Tuple[Any, Dict[str, Any]]:
    sys.path.insert(0, str(root))
    try:
        from app import create_app  # type: ignore
        app = create_app()
        rules = []
        for rule in app.url_map.iter_rules():
            methods = sorted([m for m in rule.methods if m not in {"HEAD", "OPTIONS"}])
            for method in methods:
                rules.append({
                    "method": method,
                    "rule": str(rule.rule),
                    "endpoint": str(rule.endpoint),
                    "args": sorted(list(rule.arguments)),
                })
        mobile_rules = [r for r in rules if r["rule"].startswith("/api/mobile/")]
        perf_rules = [r for r in mobile_rules if r["rule"].startswith(PERFORMANCE_GET_PREFIX)]
        safe_get_rules = [r for r in perf_rules if r["method"] == "GET" and not r["args"]]
        write_rules = [r for r in perf_rules if r["method"] in {"POST", "PUT", "PATCH", "DELETE"}]
        return app, {
            "ok": True,
            "error": "",
            "blueprint_count": len(app.blueprints),
            "url_rule_count": len(rules),
            "mobile_rule_count": len(mobile_rules),
            "performance_rule_count": len(perf_rules),
            "safe_get_candidate_count": len(safe_get_rules),
            "write_rule_count": len(write_rules),
            "safe_get_rules": safe_get_rules,
            "write_rules": write_rules,
        }
    except Exception as exc:
        return None, {"ok": False, "error": f"{type(exc).__name__}: {exc}", "traceback_tail": safe_tail(traceback.format_exc())}


def redact(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return value[:2] + "***" + value[-2:]


def extract_token_from_json(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    candidates = [
        data.get("access_token"),
        data.get("token"),
        data.get("bearer_token"),
        data.get("jwt"),
    ]
    nested_keys = ["data", "result", "auth"]
    for k in nested_keys:
        nested = data.get(k)
        if isinstance(nested, dict):
            candidates.extend([nested.get("access_token"), nested.get("token"), nested.get("bearer_token"), nested.get("jwt")])
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return ""


def login_if_needed(client: Any, username: str, password: str) -> Dict[str, Any]:
    if not username or not password:
        return {"attempted": False, "ok": False, "status": "NO_USERNAME_PASSWORD", "token_found": False, "token": ""}
    payload_variants = [
        {"email": username, "password": password},
        {"username": username, "password": password},
        {"login": username, "password": password},
    ]
    results = []
    for payload in payload_variants:
        try:
            resp = client.post("/api/mobile/auth/login", json=payload)
            text = resp.get_data(as_text=True)[:500]
            token = ""
            try:
                token = extract_token_from_json(resp.get_json(silent=True))
            except Exception:
                token = ""
            results.append({"payload_keys": list(payload.keys()), "status_code": resp.status_code, "token_found": bool(token), "body_preview": text})
            if token:
                return {"attempted": True, "ok": True, "status": "LOGIN_OK", "token_found": True, "token": token, "attempts": results}
        except Exception as exc:
            results.append({"payload_keys": list(payload.keys()), "error": f"{type(exc).__name__}: {exc}"})
    return {"attempted": True, "ok": False, "status": "LOGIN_NO_TOKEN", "token_found": False, "token": "", "attempts": results}


def smoke_gets(app: Any, token: str, safe_get_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not token:
        return {"attempted": False, "status": "SKIPPED_NO_TOKEN", "results": [], "ok_count": 0, "failure_count": 0, "server_error_count": 0}
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    server_error_count = 0
    failure_count = 0
    with app.test_client() as client:
        for r in safe_get_rules:
            rule = r["rule"]
            try:
                resp = client.get(rule, headers=headers)
                status = int(resp.status_code)
                ok = status < 500
                if status >= 500:
                    server_error_count += 1
                if not ok:
                    failure_count += 1
                body = resp.get_data(as_text=True)[:300]
                results.append({"rule": rule, "endpoint": r["endpoint"], "status": status, "ok": ok, "body_preview": body})
            except Exception as exc:
                failure_count += 1
                server_error_count += 1
                results.append({"rule": rule, "endpoint": r["endpoint"], "status": "EXCEPTION", "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return {
        "attempted": True,
        "status": "SMOKE_DONE",
        "results": results,
        "ok_count": sum(1 for x in results if x.get("ok")),
        "failure_count": failure_count,
        "server_error_count": server_error_count,
    }


def options_dryrun(app: Any, write_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = []
    with app.test_client() as client:
        for r in write_rules:
            rule = r["rule"]
            # Replace int route args with safe dummy 1 for OPTIONS path.
            path = rule.replace("<int:assignment_id>", "1").replace("<int:period_id>", "1")
            try:
                resp = client.open(path, method="OPTIONS")
                status = int(resp.status_code)
                results.append({"rule": rule, "endpoint": r["endpoint"], "status": status, "ok": status < 500})
            except Exception as exc:
                results.append({"rule": rule, "endpoint": r["endpoint"], "status": "EXCEPTION", "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return {"count": len(results), "ok_count": sum(1 for x in results if x.get("ok")), "server_error_count": sum(1 for x in results if not x.get("ok")), "results": results}


def write_reports(root: Path, report: Dict[str, Any]) -> None:
    d = ensure_report_dir(root)
    json_path = d / f"{REPORT_BASENAME}.json"
    md_path = d / f"{REPORT_BASENAME}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    urlmap = report.get("urlmap", {})
    auth = report.get("auth", {})
    smoke = report.get("smoke", {})
    options = report.get("options_dryrun", {})
    health = report.get("health_summary", {})

    lines = []
    lines.append(f"# BYS360 Mobile Authenticated Performance GET Smoke P3.9 FIX {VERSION}\n")
    lines.append("Bu rapor uygulama dosyalarını değiştirmez. Yetkili token/kullanıcı bilgisi varsa mobil performans GET endpointlerini test eder; bilgi yoksa da raporu üretir.\n")
    lines.append("## Özet\n")
    rows = [
        ("mode", report.get("mode")),
        ("generated_at", report.get("generated_at")),
        ("urlmap_ok", urlmap.get("ok")),
        ("url_rule_count", urlmap.get("url_rule_count")),
        ("mobile_rule_count", urlmap.get("mobile_rule_count")),
        ("performance_rule_count", urlmap.get("performance_rule_count")),
        ("safe_get_candidate_count", urlmap.get("safe_get_candidate_count")),
        ("write_rule_count", urlmap.get("write_rule_count")),
        ("auth_status", auth.get("status")),
        ("token_source", report.get("token_source")),
        ("smoke_attempted", smoke.get("attempted")),
        ("smoke_ok_count", smoke.get("ok_count")),
        ("smoke_failure_count", smoke.get("failure_count")),
        ("smoke_server_error_count", smoke.get("server_error_count")),
        ("options_dryrun_ok", f"{options.get('ok_count')}/{options.get('count')}"),
        ("compileall_ok", health.get("compileall_ok")),
        ("app_factory_ok", health.get("app_factory_ok")),
        ("overall_ok", health.get("overall_ok")),
    ]
    lines.append("| Alan | Değer |\n|---|---|\n")
    for k, v in rows:
        lines.append(f"| {k} | {v} |\n")

    if auth.get("status") in {"NO_USERNAME_PASSWORD", "LOGIN_NO_TOKEN"} and not report.get("bearer_token_provided"):
        lines.append("\n## Kimlik Bilgisi Durumu\n\n")
        lines.append("Token ya da kullanıcı/şifre alınamadığı için yetkili GET smoke testi atlandı. Rapor yine üretildi. Şifre/token rapora yazılmaz.\n")

    lines.append("\n## Performans Güvenli GET Adayları\n\n")
    lines.append("| Rule | Endpoint |\n|---|---|\n")
    for r in urlmap.get("safe_get_rules", []):
        lines.append(f"| `{r.get('rule')}` | `{r.get('endpoint')}` |\n")

    lines.append("\n## Yetkili GET Smoke Sonuçları\n\n")
    lines.append("| Rule | Endpoint | Status | OK | Not |\n|---|---|---:|---|---|\n")
    if smoke.get("results"):
        for r in smoke.get("results", []):
            note = (r.get("body_preview") or r.get("error") or "")[:120].replace("\n", " ")
            lines.append(f"| `{r.get('rule')}` | `{r.get('endpoint')}` | {r.get('status')} | {r.get('ok')} | {note} |\n")
    else:
        lines.append(f"| - | - | - | - | {smoke.get('status')} |\n")

    lines.append("\n## Yazma Endpointleri OPTIONS Dry-run\n\n")
    lines.append("Gerçek POST/PUT/PATCH/DELETE çağrısı yapılmaz.\n\n")
    lines.append("| Rule | Endpoint | Status | OK |\n|---|---|---:|---|\n")
    for r in options.get("results", []):
        lines.append(f"| `{r.get('rule')}` | `{r.get('endpoint')}` | {r.get('status')} | {r.get('ok')} |\n")

    lines.append("\n## Sağlık Kontrolü\n\n")
    lines.append(f"- compileall_ok: {health.get('compileall_ok')}\n")
    lines.append(f"- app_factory_ok: {health.get('app_factory_ok')}\n")
    lines.append(f"- overall_ok: {health.get('overall_ok')}\n")
    lines.append("\n## Not\n\n")
    lines.append("Bu paket kod değiştirmez. Test bittikten sonra PowerShell ortam değişkenlerini temizleyin. Paylaşılan test şifresi mutlaka değiştirilmeli.\n")
    md_path.write_text("".join(lines), encoding="utf-8")
    report["json_report"] = str(json_path.relative_to(root))
    report["md_report"] = str(md_path.relative_to(root))
    # Update JSON with report paths
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", default="all")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    os.chdir(root)
    ensure_report_dir(root)

    report: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    compile_res = run_compileall(root)
    app, urlmap = create_app_and_urlmap(root)
    report["urlmap"] = urlmap

    bearer = os.environ.get("BYS360_MOBILE_BEARER_TOKEN", "").strip()
    username = os.environ.get("BYS360_MOBILE_USERNAME", "").strip()
    password = os.environ.get("BYS360_MOBILE_PASSWORD", "").strip()
    report["bearer_token_provided"] = bool(bearer)
    report["username_provided"] = bool(username)
    report["username_redacted"] = redact(username)

    token = bearer
    token_source = "env_bearer_token" if bearer else ""
    auth = {"attempted": False, "ok": False, "status": "NOT_ATTEMPTED", "token_found": bool(token)}
    if app and not token:
        with app.test_client() as client:
            auth = login_if_needed(client, username, password)
            token = auth.get("token", "") or ""
            if token:
                token_source = "login_response"
    # Never keep token in report
    if "token" in auth:
        auth["token"] = "***" if auth.get("token_found") else ""
    report["token_source"] = token_source or "none"
    report["auth"] = auth

    if app and urlmap.get("ok"):
        smoke = smoke_gets(app, token, urlmap.get("safe_get_rules", []))
        options = options_dryrun(app, urlmap.get("write_rules", []))
    else:
        smoke = {"attempted": False, "status": "SKIPPED_APP_OR_URLMAP_ERROR", "results": [], "ok_count": 0, "failure_count": 0, "server_error_count": 0}
        options = {"count": 0, "ok_count": 0, "server_error_count": 0, "results": []}
    report["smoke"] = smoke
    report["options_dryrun"] = options

    # overall_ok means: code health ok, app/urlmap ok, no 5xx if smoke attempted, no 5xx in OPTIONS.
    app_factory_ok = bool(urlmap.get("ok"))
    smoke_ok = (not smoke.get("attempted")) or int(smoke.get("server_error_count", 0) or 0) == 0
    options_ok = int(options.get("server_error_count", 0) or 0) == 0
    overall_ok = bool(compile_res.get("ok")) and app_factory_ok and smoke_ok and options_ok
    report["health_summary"] = {
        "compileall_ok": bool(compile_res.get("ok")),
        "compileall": compile_res,
        "app_factory_ok": app_factory_ok,
        "urlmap_ok": bool(urlmap.get("ok")),
        "smoke_ok": smoke_ok,
        "options_ok": options_ok,
        "overall_ok": overall_ok,
    }

    write_reports(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "urlmap_ok": urlmap.get("ok"),
        "safe_get_candidate_count": urlmap.get("safe_get_candidate_count"),
        "write_rule_count": urlmap.get("write_rule_count"),
        "auth_status": report["auth"].get("status"),
        "token_source": report.get("token_source"),
        "smoke_attempted": report["smoke"].get("attempted"),
        "smoke_ok_count": report["smoke"].get("ok_count"),
        "smoke_server_error_count": report["smoke"].get("server_error_count"),
        "compileall_ok": report["health_summary"].get("compileall_ok"),
        "app_factory_ok": report["health_summary"].get("app_factory_ok"),
        "overall_ok": report["health_summary"].get("overall_ok"),
        "json_report": report.get("json_report"),
        "md_report": report.get("md_report"),
    }, ensure_ascii=False, indent=2))
    print("BYS360_MOBILE_AUTHENTICATED_PERFORMANCE_GET_SMOKE_P3_9_FIX_V2_17_47_REPORT_OK")
    if overall_ok:
        print("BYS360_MOBILE_AUTHENTICATED_PERFORMANCE_GET_SMOKE_P3_9_FIX_V2_17_47_HEALTH_OK")
    print("BYS360_MOBILE_AUTHENTICATED_PERFORMANCE_GET_SMOKE_P3_9_FIX_V2_17_47_OK")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
