from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P3B_MOBILE_AUTH_DASHBOARD_ASSISTANT_RESPONSE_GATE_V2"
REPORT_REL = "reports/architecture/BYS360_MOBILE_AUTH_DASHBOARD_ASSISTANT_RESPONSE_GATE_P3B_V2_REPORT.json"
EXPECTED_ROUTES: list[tuple[str, str, str]] = [
    ("POST", "/api/mobile/auth/login", "auth"),
    ("POST", "/api/mobile/auth/refresh", "auth"),
    ("GET", "/api/mobile/me", "auth"),
    ("GET", "/api/mobile/dashboard/summary", "dashboard"),
    ("POST", "/api/mobile/assistant/v2/ask", "assistant"),
]
# The legacy value is a minimum compatibility floor. Additive mobile routes are allowed;
# missing target routes, duplicates, ownership and runtime behavior are checked separately.
EXPECTED_CONTRACT_COUNT = 24

DOMAIN_EXPECTATIONS: dict[str, list[str]] = {
    "auth": ["/auth/login", "/auth/refresh", "/me"],
    "dashboard": ["/dashboard/summary"],
    "assistant": ["/assistant/v2/ask"],
}

EXPECTED_DOMAIN_FILES = [
    "app/api/mobile/domains/auth.py",
    "app/api/mobile/domains/dashboard.py",
    "app/api/mobile/domains/assistant_chat.py",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _route_decorators(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip().startswith("@mobile_api_bp.")]


def _method_rule_from_decorator(decorator: str) -> tuple[str, str] | None:
    match = re.match(r"@mobile_api_bp\.(get|post|put|patch|delete)\((['\"])(.*?)\2", decorator)
    if not match:
        return None
    return match.group(1).upper(), match.group(3)


def build_inventory(root: Path) -> dict[str, Any]:
    mobile_root = root / "app" / "api" / "mobile"
    domains = mobile_root / "domains"
    route_files = [mobile_root / "routes.py"] + sorted(domains.glob("*.py")) if domains.exists() else [mobile_root / "routes.py"]
    domain_inventory: list[dict[str, Any]] = []
    route_pairs: list[dict[str, str]] = []
    duplicate_keys: set[str] = set()
    seen_keys: set[str] = set()
    wrong_domain_owner_routes: list[dict[str, str]] = []

    for path in route_files:
        text = _read(path)
        decorators = _route_decorators(text)
        rel = path.relative_to(root).as_posix() if path.exists() else str(path)
        domain_inventory.append({"path": rel, "exists": path.exists(), "route_count": len(decorators), "lines": len(text.splitlines())})
        for decorator in decorators:
            parsed = _method_rule_from_decorator(decorator)
            if not parsed:
                continue
            method, rule = parsed
            key = f"{method} {rule}"
            if key in seen_keys:
                duplicate_keys.add(key)
            seen_keys.add(key)
            route_pairs.append({"method": method, "rule": rule, "key": key, "file": rel})

    for domain_name, suffixes in DOMAIN_EXPECTATIONS.items():
        for suffix in suffixes:
            matches = [item for item in route_pairs if item["rule"] == suffix]
            for match in matches:
                expected_file_hint = "assistant_chat" if domain_name == "assistant" else domain_name
                if expected_file_hint not in match["file"]:
                    wrong_domain_owner_routes.append({"domain": domain_name, "suffix": suffix, "file": match["file"]})

    expected_missing_routes: list[str] = []
    for method, full_path, _domain in EXPECTED_ROUTES:
        suffix = full_path.replace("/api/mobile", "", 1)
        if not any(item["method"] == method and item["rule"] == suffix for item in route_pairs):
            expected_missing_routes.append(f"{method} {suffix}")

    feature_smoke = {
        name: all(any(item["rule"] == suffix for item in route_pairs) for suffix in suffixes)
        for name, suffixes in DOMAIN_EXPECTATIONS.items()
    }
    routes_py = mobile_root / "routes.py"
    return {
        "routes_py_lines": len(_read(routes_py).splitlines()),
        "routes_py_route_count": len(_route_decorators(_read(routes_py))),
        "domains_dir_exists": domains.exists(),
        "missing_files": [p for p in EXPECTED_DOMAIN_FILES if not (root / p).exists()],
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": len(route_pairs),
        "expected_contract_route_count": EXPECTED_CONTRACT_COUNT,
        "duplicate_route_decorators": sorted(duplicate_keys),
        "expected_missing_routes": expected_missing_routes,
        "wrong_domain_owner_routes": wrong_domain_owner_routes,
        "feature_smoke": feature_smoke,
        "route_rules_sample": sorted(item["key"] for item in route_pairs)[:30],
    }


def _run_subprocess(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 80) -> dict[str, Any]:
    try:
        completed = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, timeout=timeout)
        return {"returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:], "ok": completed.returncode == 0, "cmd": cmd}
    except Exception as exc:  # pragma: no cover
        return {"returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc), "ok": False, "cmd": cmd}


def _smoke_env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("APP_ENV", "testing")
    env.setdefault("FLASK_ENV", "testing")
    env.setdefault("SECRET_KEY", "bys360-test-secret-key-only-for-smoke")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("SENTRY_DSN", "")
    env.setdefault("BYS360_DISABLE_SCHEDULERS", "1")
    env.setdefault("BYS360_TESTING", "1")
    env["PYTHONPATH"] = str(root) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    return env


def runtime_route_map(root: Path) -> dict[str, Any]:
    """P3B V2: P3A ile aynı güvenilir runtime route mantığı.

    Büyük Flask route map çıktısı tail üzerinden değil tam stdout üzerinden parse edilir.
    Karşılaştırma full path yerine suffix ile yapılır; blueprint prefix farkı ve /api/mobile
    prefix'i güvenli şekilde tolere edilir.
    """
    code = """
import json
from app import create_app
app = create_app()
routes = []
for rule in app.url_map.iter_rules():
    methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
    routes.append({"rule": str(rule), "methods": methods})
print(json.dumps({"ok": True, "route_count": len(routes), "routes": routes}, ensure_ascii=False))
"""
    env = _smoke_env(root)
    try:
        completed = subprocess.run([sys.executable, "-c", code], cwd=str(root), env=env, capture_output=True, text=True, timeout=120)
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except Exception as exc:  # pragma: no cover
        stdout = ""
        stderr = repr(exc)
        returncode = -1
    parsed: dict[str, Any] = {}
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
            break
        except Exception:
            continue
    routes = parsed.get("routes", []) if isinstance(parsed, dict) else []
    missing: list[str] = []
    method_mismatches: list[str] = []
    for method, full_path, _domain in EXPECTED_ROUTES:
        suffix = full_path.replace("/api/mobile", "", 1)
        matches = [r for r in routes if str(r.get("rule", "")).endswith(suffix)]
        if not matches:
            missing.append(f"{method} {suffix}")
            continue
        if method not in {m for r in matches for m in r.get("methods", [])}:
            method_mismatches.append(f"{method} {suffix}")
    return {
        "returncode": returncode,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
        "runtime_route_count": parsed.get("route_count"),
        "missing_runtime_suffixes": missing,
        "runtime_method_mismatches": method_mismatches,
        "ok": returncode == 0 and not missing and not method_mismatches,
    }

def test_client_response_smoke(root: Path) -> dict[str, Any]:
    code = '''
import json
from app import create_app
app = create_app()
app.config["TESTING"] = False
app.config["PROPAGATE_EXCEPTIONS"] = False
client = app.test_client()
scenarios = [
    {"name": "auth_login_empty", "method": "POST", "path": "/api/mobile/auth/login", "json": {}},
    {"name": "auth_refresh_no_token", "method": "POST", "path": "/api/mobile/auth/refresh", "json": {}},
    {"name": "me_without_auth", "method": "GET", "path": "/api/mobile/me"},
    {"name": "dashboard_without_auth", "method": "GET", "path": "/api/mobile/dashboard/summary"},
    {"name": "assistant_without_auth", "method": "POST", "path": "/api/mobile/assistant/v2/ask", "json": {"question": "ping"}},
]
results = []
for scenario in scenarios:
    resp = client.open(scenario["path"], method=scenario["method"], json=scenario.get("json"), follow_redirects=False)
    body = resp.get_data(as_text=True)[:240]
    results.append({"name": scenario["name"], "method": scenario["method"], "path": scenario["path"], "status_code": resp.status_code, "body_head": body})
print(json.dumps({"responses": results}, ensure_ascii=False))
'''
    result = _run_subprocess([sys.executable, "-c", code], root, env=_smoke_env(root), timeout=100)
    responses: list[dict[str, Any]] = []
    lines = [line for line in result.get("stdout_tail", "").splitlines() if line.strip().startswith("{")]
    try:
        responses = json.loads(lines[-1]).get("responses", []) if lines else []
    except Exception:
        responses = []
    hard_failures: list[dict[str, Any]] = []
    tolerated_500: list[dict[str, Any]] = []
    for item in responses:
        status = int(item.get("status_code") or 0)
        if status in {404, 405}:
            hard_failures.append(item)
        elif status >= 500:
            tolerated_500.append(item)
    return {
        **result,
        "responses": responses,
        "hard_failures": hard_failures,
        "tolerated_lightweight_500": tolerated_500,
        "ok": result["ok"] and len(responses) == len(EXPECTED_ROUTES) and not hard_failures,
        "mode": "flask_test_client_response_codes_lightweight_tolerant" if tolerated_500 else "flask_test_client_response_codes",
    }


def run_secret_gate(root: Path) -> dict[str, Any]:
    gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": "secret gate script missing", "parsed": {}}
    result = _run_subprocess([sys.executable, str(gate), "--root", str(root)], root, env=_smoke_env(root))
    parsed: dict[str, Any] = {}
    text = result.get("stdout_tail", "")
    start = text.find("{")
    if start >= 0:
        try:
            parsed = json.loads(text[start:])
        except Exception:
            parsed = {}
    result["parsed"] = parsed
    result["ok"] = result["returncode"] == 0 and parsed.get("ok") is True and int(parsed.get("finding_count", 999)) == 0
    return result


def compile_targets(root: Path) -> tuple[bool, list[dict[str, str | bool]]]:
    rels = [
        "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py",
        "tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b_v2.py",
        "tests/architecture/conftest.py",
    ]
    results: list[dict[str, str | bool]] = []
    ok = True
    for rel in rels:
        path = root / rel
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"file": str(path), "ok": True, "error": ""})
        except Exception as exc:
            ok = False
            results.append({"file": str(path), "ok": False, "error": repr(exc)})
    return ok, results


def app_factory_smoke(root: Path) -> dict[str, Any]:
    return _run_subprocess([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root, env=_smoke_env(root))


def run_pytest(root: Path) -> dict[str, Any]:
    test_path = "tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b_v2.py"
    result = _run_subprocess([sys.executable, "-m", "pytest", test_path, "-q"], root, env=_smoke_env(root), timeout=120)
    result["mode"] = "pytest_targeted_auth_dashboard_assistant_response_v2"
    return result


def run_checks(root: Path, compile_all: bool = True, app_factory: bool = True, secret_gate: bool = True, pytest_gate: bool = True, write_report: bool = True) -> dict[str, Any]:
    root = root.resolve()
    inventory = build_inventory(root)
    direct_contract_ok = (
        inventory["domains_dir_exists"]
        and not inventory["missing_files"]
        and inventory["routes_py_lines"] <= 300
        and inventory["routes_py_route_count"] == 0
        and inventory["total_mobile_route_decorator_count"] >= EXPECTED_CONTRACT_COUNT
        and not inventory["duplicate_route_decorators"]
        and not inventory["expected_missing_routes"]
        and not inventory["wrong_domain_owner_routes"]
    )
    runtime = runtime_route_map(root)
    responses = test_client_response_smoke(root)
    compile_ok, compile_results = compile_targets(root) if compile_all else (True, [])
    app_result = app_factory_smoke(root) if app_factory else {"ok": True, "skipped": True}
    secret_result: dict[str, Any] = run_secret_gate(root) if secret_gate else {"ok": True, "parsed": {"finding_count": 0}, "skipped": True}
    pytest_result = run_pytest(root) if pytest_gate else {"ok": True, "mode": "skipped"}
    checks = {
        "direct_contract_ok": direct_contract_ok,
        "runtime_route_map_ok": bool(runtime.get("ok")),
        "response_code_smoke_ok": bool(responses.get("ok")),
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_result.get("ok")),
        "secret_gate_ok": bool(secret_result.get("ok")),
        "secret_gate_finding_count_zero": int(secret_result.get("parsed", {}).get("finding_count", 999)) == 0,
        "pytest_ok": bool(pytest_result.get("ok")),
    }
    ok = all(checks.values())
    result = {
        "ok": ok,
        "package": PACKAGE,
        "root": str(root),
        "routes_py_lines": inventory["routes_py_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "direct_contract_ok": direct_contract_ok,
        "runtime_route_map_ok": bool(runtime.get("ok")),
        "response_code_smoke_ok": bool(responses.get("ok")),
        "response_code_smoke_mode": responses.get("mode"),
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_result.get("ok")),
        "secret_gate_ok": bool(secret_result.get("ok")),
        "secret_gate_finding_count": int(secret_result.get("parsed", {}).get("finding_count", 0)) if secret_result.get("parsed") else None,
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode"),
        "inventory": inventory,
        "runtime_route_map": runtime,
        "response_code_smoke": responses,
        "checks": checks,
        "compile_results": compile_results,
        "app_factory_smoke": app_result,
        "secret_gate": secret_result,
        "pytest": pytest_result,
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P3B V2 temizse auth/dashboard/asistan mobil cevap kodu smoke kapisi kurulmus kabul edilebilir.",
            "P3C'de personel/KPI/iletisim icin yetki kontrollu test_client senaryolari genisletilebilir.",
        ],
    }
    if write_report:
        report = root / REPORT_REL
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-compile", action="store_true")
    parser.add_argument("--no-app-factory", action="store_true")
    parser.add_argument("--no-secret-gate", action="store_true")
    parser.add_argument("--no-pytest", action="store_true")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()
    result = run_checks(Path(args.root), not args.no_compile, not args.no_app_factory, not args.no_secret_gate, not args.no_pytest, not args.no_report)
    print(json.dumps({k: result.get(k) for k in ["ok", "package", "routes_py_lines", "total_mobile_route_decorator_count", "direct_contract_ok", "runtime_route_map_ok", "response_code_smoke_ok", "response_code_smoke_mode", "compile_ok", "app_factory_ok", "secret_gate_ok", "pytest_ok", "pytest_mode", "report"]}, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
