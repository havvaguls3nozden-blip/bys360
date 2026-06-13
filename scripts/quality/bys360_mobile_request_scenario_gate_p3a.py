from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P3A_MOBILE_REQUEST_SCENARIO_GATE"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_REQUEST_SCENARIO_GATE_P3A_REPORT.json")

EXPECTED_ROUTE_SUFFIXES = {
    "auth_login": ("POST", "/auth/login"),
    "auth_refresh": ("POST", "/auth/refresh"),
    "me": ("GET", "/me"),
    "dashboard_summary": ("GET", "/dashboard/summary"),
    "notifications_read": ("POST", "/notifications/<int:notification_id>/read"),
    "notifications_read_all": ("POST", "/notifications/read-all"),
    "personnel_list": ("GET", "/personnel/list"),
    "personnel_all": ("GET", "/personnel/all"),
    "personnel_create": ("POST", "/personnel/create"),
    "personnel_add": ("POST", "/personnel/add"),
    "kpi_target_management_get": ("GET", "/kpi/target-management"),
    "kpi_target_management_post": ("POST", "/kpi/target-management"),
    "kpi_target_progress": ("POST", "/kpi/target-management/<int:target_id>/progress"),
    "communication_v1_thread": ("GET", "/communication/messages/threads/<int:thread_id>"),
    "communication_v1_send": ("POST", "/communication/messages/threads/<int:thread_id>/send"),
    "communication_v1_create": ("POST", "/communication/messages/create-thread"),
    "communication_v2_thread": ("GET", "/communication/v2/threads/<int:thread_id>"),
    "communication_v2_send": ("POST", "/communication/v2/threads/<int:thread_id>/send"),
    "communication_v2_users": ("GET", "/communication/v2/users"),
    "communication_v2_create": ("POST", "/communication/v2/create-thread"),
    "support_ticket": ("POST", "/support/tickets"),
    "support_reply": ("POST", "/support/tickets/<int:ticket_id>/reply"),
    "survey_submit": ("POST", "/surveys/<int:survey_id>/submit"),
    "assistant_v2_ask": ("POST", "/assistant/v2/ask"),
}

EXPECTED_DOMAIN_OWNERS = {
    "/auth/": "auth.py",
    "/me": "auth.py",
    "/dashboard/": "dashboard.py",
    "/notifications/": "notifications.py",
    "/personnel/list": "personnel_read.py",
    "/personnel/all": "personnel_write_all.py",
    "/personnel/create": "personnel_write_all.py",
    "/personnel/add": "personnel_write_all.py",
    "/kpi/": "kpi_target_management.py",
    "/communication/messages/": "communication_v1_write.py",
    "/communication/v2/": "communication_v2_write.py",
    "/support/": "support_survey_write.py",
    "/surveys/": "support_survey_write.py",
    "/assistant/": "assistant_chat.py",
}

COMPILE_TARGETS = [
    "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "tests/architecture/test_mobile_api_request_scenarios_p3a.py",
    "tests/architecture/conftest.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def count_lines(path: Path) -> int:
    return len(read_text(path).splitlines()) if path.exists() else 0


def decorator_rules_from_file(path: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    out: list[dict[str, Any]] = []
    pattern = re.compile(r"@mobile_api_bp\.(get|post|put|patch|delete)\(\s*([\"'])(.*?)\2", re.I)
    for match in pattern.finditer(text):
        out.append({"method": match.group(1).upper(), "suffix": match.group(3), "file": str(path)})
    return out


def static_inventory(root: Path) -> dict[str, Any]:
    routes_py = root / "app/api/mobile/routes.py"
    domain_dir = root / "app/api/mobile/domains"
    files = [routes_py] + sorted(domain_dir.glob("*.py")) if domain_dir.exists() else [routes_py]
    rules: list[dict[str, Any]] = []
    domain_inventory = []
    for path in files:
        file_rules = decorator_rules_from_file(path)
        rules.extend(file_rules)
        domain_inventory.append({
            "path": str(path.relative_to(root)).replace("\\", "/") if path.exists() else str(path),
            "exists": path.exists(),
            "route_count": len(file_rules),
            "lines": count_lines(path),
        })
    keys = [(r["method"], r["suffix"]) for r in rules]
    duplicate_keys = sorted([f"{m} {s}" for m, s in set(keys) if keys.count((m, s)) > 1])
    expected_missing = []
    wrong_owner = []
    for name, (method, suffix) in EXPECTED_ROUTE_SUFFIXES.items():
        matches = [r for r in rules if r["method"] == method and r["suffix"] == suffix]
        if not matches:
            expected_missing.append({"name": name, "method": method, "suffix": suffix})
            continue
        expected_file = None
        for prefix, file_name in EXPECTED_DOMAIN_OWNERS.items():
            if suffix.startswith(prefix) or suffix == prefix:
                expected_file = file_name
                break
        if expected_file and not any(Path(m["file"]).name == expected_file for m in matches):
            wrong_owner.append({"name": name, "method": method, "suffix": suffix, "expected_file": expected_file, "actual_files": [Path(m["file"]).name for m in matches]})
    return {
        "routes_py_lines": count_lines(routes_py),
        "routes_py_route_count": len(decorator_rules_from_file(routes_py)),
        "domains_dir_exists": domain_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": len(rules),
        "expected_contract_route_count": len(EXPECTED_ROUTE_SUFFIXES),
        "duplicate_route_decorators": duplicate_keys,
        "expected_missing_routes": expected_missing,
        "wrong_domain_owner_routes": wrong_owner,
        "route_rules_sample": [f"{r['method']} {r['suffix']}" for r in rules[:32]],
    }


def runtime_inventory(root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("FLASK_ENV", "testing")
    env.setdefault("APP_ENV", "testing")
    env.setdefault("SECRET_KEY", "testing-secret-key-for-local-smoke-only")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("SENTRY_DSN", "")
    code = """
import json
from app import create_app
app = create_app()
routes = []
for rule in app.url_map.iter_rules():
    routes.append({"rule": str(rule), "methods": sorted([m for m in rule.methods if m not in {"HEAD", "OPTIONS"}])})
print(json.dumps({"ok": True, "route_count": len(routes), "routes": routes}, ensure_ascii=False))
"""
    proc = subprocess.run([sys.executable, "-c", code], cwd=str(root), env=env, text=True, capture_output=True)
    parsed: dict[str, Any] = {}
    for line in reversed(proc.stdout.splitlines()):
        try:
            parsed = json.loads(line)
            break
        except Exception:
            continue
    routes = parsed.get("routes", []) if isinstance(parsed, dict) else []
    missing = []
    method_mismatch = []
    for name, (method, suffix) in EXPECTED_ROUTE_SUFFIXES.items():
        matches = [r for r in routes if str(r.get("rule", "")).endswith(suffix)]
        if not matches:
            missing.append({"name": name, "method": method, "suffix": suffix})
            continue
        if method not in {m for r in matches for m in r.get("methods", [])}:
            method_mismatch.append({"name": name, "method": method, "suffix": suffix, "matches": matches})
    return {
        "ok": proc.returncode == 0 and not missing and not method_mismatch,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1600:],
        "stderr_tail": proc.stderr[-1600:],
        "runtime_route_count": parsed.get("route_count"),
        "missing_runtime_suffixes": missing,
        "runtime_method_mismatches": method_mismatch,
    }


def compile_files(root: Path) -> tuple[bool, list[dict[str, str]]]:
    results = []
    ok = True
    for rel in COMPILE_TARGETS:
        path = root / rel
        if not path.exists():
            results.append({"file": str(path), "ok": False, "error": "missing"})
            ok = False
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"file": str(path), "ok": True, "error": ""})
        except Exception as exc:
            ok = False
            results.append({"file": str(path), "ok": False, "error": str(exc)})
    return ok, results


def app_factory_smoke(root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("FLASK_ENV", "testing")
    env.setdefault("APP_ENV", "testing")
    env.setdefault("SECRET_KEY", "testing-secret-key-for-local-smoke-only")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("SENTRY_DSN", "")
    proc = subprocess.run([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], cwd=str(root), env=env, text=True, capture_output=True)
    return {"returncode": proc.returncode, "stdout_tail": proc.stdout[-1200:], "stderr_tail": proc.stderr[-1200:], "ok": proc.returncode == 0 and "APP_FACTORY_OK" in proc.stdout}


def secret_gate(root: Path) -> dict[str, Any]:
    gate = root / "scripts/quality/bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": "secret gate missing", "parsed": {}}
    proc = subprocess.run([sys.executable, str(gate), "--root", str(root)], cwd=str(root), text=True, capture_output=True)
    parsed: dict[str, Any] = {}
    for line in reversed(proc.stdout.splitlines()):
        try:
            parsed = json.loads(line)
            break
        except Exception:
            pass
    if not parsed:
        try:
            parsed = json.loads(proc.stdout)
        except Exception:
            parsed = {}
    return {"returncode": proc.returncode, "stdout_tail": proc.stdout[-1200:], "stderr_tail": proc.stderr[-1200:], "parsed": parsed, "ok": proc.returncode == 0 and parsed.get("ok") is True and parsed.get("finding_count", 1) == 0}


def pytest_gate(root: Path) -> dict[str, Any]:
    files = [
        "tests/architecture/test_mobile_api_request_scenarios_p3a.py",
        "tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py",
        "tests/architecture/test_mobile_api_behavior_smoke_p2b.py",
        "tests/architecture/test_mobile_api_contract_p2a.py",
    ]
    proc = subprocess.run([sys.executable, "-m", "pytest", *files, "-q"], cwd=str(root), text=True, capture_output=True)
    return {"returncode": proc.returncode, "stdout_tail": proc.stdout[-1600:], "stderr_tail": proc.stderr[-1600:], "ok": proc.returncode == 0, "mode": "pytest_targeted_mobile_scenarios"}


def run_checks(root: Path, compile_all: bool, app_factory: bool, secret: bool, pytest_run: bool, write_report: bool = True) -> dict[str, Any]:
    inv = static_inventory(root)
    runtime = runtime_inventory(root)
    direct_contract_ok = (
        inv["routes_py_lines"] <= 300
        and inv["routes_py_route_count"] == 0
        and inv["total_mobile_route_decorator_count"] == inv["expected_contract_route_count"]
        and not inv["duplicate_route_decorators"]
        and not inv["expected_missing_routes"]
        and not inv["wrong_domain_owner_routes"]
    )
    compile_ok, compile_results = (True, [])
    if compile_all:
        compile_ok, compile_results = compile_files(root)
    app_smoke = {"ok": True}
    if app_factory:
        app_smoke = app_factory_smoke(root)
    sec = {"ok": True, "parsed": {"finding_count": 0}}
    if secret:
        sec = secret_gate(root)
    py = {"ok": True, "mode": "not_requested"}
    if pytest_run:
        py = pytest_gate(root)
    request_scenario_ok = direct_contract_ok and runtime.get("ok") is True
    result = {
        "ok": direct_contract_ok and request_scenario_ok and compile_ok and app_smoke.get("ok") is True and sec.get("ok") is True and py.get("ok") is True,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "routes_py_lines": inv["routes_py_lines"],
        "total_mobile_route_decorator_count": inv["total_mobile_route_decorator_count"],
        "expected_contract_route_count": inv["expected_contract_route_count"],
        "direct_contract_ok": direct_contract_ok,
        "request_scenario_ok": request_scenario_ok,
        "runtime_route_map_ok": runtime.get("ok") is True,
        "compile_ok": compile_ok,
        "app_factory_ok": app_smoke.get("ok") is True,
        "secret_gate_ok": sec.get("ok") is True,
        "secret_gate_finding_count": sec.get("parsed", {}).get("finding_count"),
        "pytest_ok": py.get("ok") is True,
        "pytest_mode": py.get("mode"),
        "inventory": inv,
        "runtime_route_map": runtime,
        "compile_results": compile_results,
        "app_factory_smoke": app_smoke,
        "secret_gate": sec,
        "pytest": py,
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P3A temizse mobil API endpoint senaryolari runtime route haritasiyla korunmus kabul edilebilir.",
            "P3B'de auth/dashboard/assistant icin yetki kontrollu test_client cevap kodu senaryolari eklenebilir.",
        ],
    }
    if write_report:
        report_path = root / REPORT_REL
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    result = run_checks(root, args.compile_all, args.app_factory, args.secret_gate, args.pytest, write_report=True)
    print(json.dumps({
        "ok": result["ok"],
        "package": PACKAGE,
        "routes_py_lines": result["routes_py_lines"],
        "total_mobile_route_decorator_count": result["total_mobile_route_decorator_count"],
        "direct_contract_ok": result["direct_contract_ok"],
        "request_scenario_ok": result["request_scenario_ok"],
        "runtime_route_map_ok": result["runtime_route_map_ok"],
        "compile_ok": result["compile_ok"],
        "app_factory_ok": result["app_factory_ok"],
        "secret_gate_ok": result["secret_gate_ok"],
        "pytest_ok": result["pytest_ok"],
        "pytest_mode": result["pytest_mode"],
        "report": result["report"],
    }, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
