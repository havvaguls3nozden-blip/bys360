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

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P3D_MOBILE_SUPPORT_SURVEY_NOTIFICATIONS_RESPONSE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_SUPPORT_SURVEY_NOTIFICATIONS_RESPONSE_GATE_P3D_REPORT.json")
TEST_NAME = "test_mobile_api_support_survey_notifications_response_p3d.py"
EXPECTED_CONTRACT_ROUTE_COUNT = 24

TARGET_SCENARIOS = [
    {"feature": "support", "method": "POST", "suffix": "/support/tickets", "concrete": "/api/mobile/support/tickets", "json": {"subject": "", "message": ""}},
    {"feature": "support", "method": "POST", "suffix": "/support/tickets/<int:ticket_id>/reply", "concrete": "/api/mobile/support/tickets/1/reply", "json": {"message": ""}},
    {"feature": "survey", "method": "POST", "suffix": "/surveys/<int:survey_id>/submit", "concrete": "/api/mobile/surveys/1/submit", "json": {}},
    {"feature": "notifications", "method": "POST", "suffix": "/notifications/<int:notification_id>/read", "concrete": "/api/mobile/notifications/1/read", "json": {}},
    {"feature": "notifications", "method": "POST", "suffix": "/notifications/read-all", "concrete": "/api/mobile/notifications/read-all", "json": {}},
]

OPTIONAL_RUNTIME_SCENARIOS = [
    {"feature": "support", "method": "GET", "suffix": "/support/tickets", "concrete": "/api/mobile/support/tickets"},
    {"feature": "support", "method": "GET", "suffix": "/support/tickets/<int:ticket_id>", "concrete": "/api/mobile/support/tickets/1"},
    {"feature": "survey", "method": "GET", "suffix": "/surveys", "concrete": "/api/mobile/surveys"},
    {"feature": "survey", "method": "GET", "suffix": "/surveys/<int:survey_id>", "concrete": "/api/mobile/surveys/1"},
    {"feature": "notifications", "method": "GET", "suffix": "/notifications", "concrete": "/api/mobile/notifications"},
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _line_count(path: Path) -> int:
    return len(_read(path).splitlines()) if path.exists() else 0


def _normalize_route_arg(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return raw
    try:
        import ast
        value = ast.literal_eval(raw)
        if isinstance(value, str):
            return value
    except Exception:
        pass
    return raw.strip('"\'')


def _route_decorators(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for match in re.finditer(r"@mobile_api_bp\.(get|post|put|patch|delete)\(([^\n\)]*)\)", text):
        method = match.group(1).upper()
        route = _normalize_route_arg(match.group(2).split(",", 1)[0])
        items.append({"method": method, "suffix": route, "decorator": f"{method} {route}"})
    for match in re.finditer(r"@mobile_api_bp\.route\(([^\n\)]*)\)", text):
        args = match.group(1)
        route = _normalize_route_arg(args.split(",", 1)[0])
        methods_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", args)
        if methods_match:
            for raw_method in methods_match.group(1).split(","):
                method = raw_method.strip().strip('"\'').upper()
                if method:
                    items.append({"method": method, "suffix": route, "decorator": f"{method} {route}"})
        else:
            items.append({"method": "GET", "suffix": route, "decorator": f"GET {route}"})
    return items


def build_inventory(root: Path) -> dict[str, Any]:
    mobile_dir = root / "app" / "api" / "mobile"
    domains_dir = mobile_dir / "domains"
    paths = [mobile_dir / "routes.py"]
    if domains_dir.exists():
        paths.extend(sorted(domains_dir.glob("*.py")))
    domain_inventory = []
    all_decorators: list[dict[str, str]] = []
    for path in paths:
        text = _read(path)
        decorators = _route_decorators(text)
        all_decorators.extend(decorators)
        domain_inventory.append({
            "path": str(path.relative_to(root)).replace("\\", "/") if path.exists() else str(path),
            "exists": path.exists(),
            "route_count": len(decorators),
            "lines": _line_count(path),
        })
    seen: set[str] = set()
    dupes: list[str] = []
    for item in all_decorators:
        key = f"{item['method']} {item['suffix']}"
        if key in seen:
            dupes.append(key)
        seen.add(key)
    expected_missing = []
    for scenario in TARGET_SCENARIOS:
        key = f"{scenario['method']} {scenario['suffix']}"
        if key not in seen:
            expected_missing.append(key)
    feature_smoke = {
        "support": all(f"{s['method']} {s['suffix']}" in seen for s in TARGET_SCENARIOS if s["feature"] == "support"),
        "survey": all(f"{s['method']} {s['suffix']}" in seen for s in TARGET_SCENARIOS if s["feature"] == "survey"),
        "notifications": all(f"{s['method']} {s['suffix']}" in seen for s in TARGET_SCENARIOS if s["feature"] == "notifications"),
    }
    return {
        "routes_py_lines": _line_count(mobile_dir / "routes.py"),
        "routes_py_route_count": len(_route_decorators(_read(mobile_dir / "routes.py"))),
        "domains_dir_exists": domains_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": len(all_decorators),
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "duplicate_route_decorators": dupes,
        "expected_missing_routes": expected_missing,
        "feature_smoke": feature_smoke,
        "route_rules_sample": sorted(f"{item['method']} {item['suffix']}" for item in all_decorators)[:30],
    }


def _prepare_env() -> None:
    os.environ.setdefault("APP_ENV", "testing")
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("TESTING", "1")
    os.environ.setdefault("SECRET_KEY", "local-test-key")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("WTF_CSRF_ENABLED", "0")
    os.environ.setdefault("SENTRY_DSN", "")


def _build_app(root: Path):
    _prepare_env()
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    from app import create_app  # type: ignore
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return app


def runtime_route_map(root: Path) -> dict[str, Any]:
    try:
        app = _build_app(root)
        all_rules = list(app.url_map.iter_rules())
        mobile_routes: list[dict[str, Any]] = []
        for rule in all_rules:
            rule_s = str(rule.rule)
            if not rule_s.startswith("/api/mobile"):
                continue
            methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
            mobile_routes.append({"rule": rule_s, "methods": methods, "endpoint": rule.endpoint})
        missing: list[str] = []
        mismatches: list[dict[str, str]] = []
        for scenario in TARGET_SCENARIOS:
            expected_rule = "/api/mobile" + scenario["suffix"]
            candidates = [r for r in mobile_routes if r["rule"] == expected_rule or r["rule"].endswith(scenario["suffix"])]
            if not candidates:
                missing.append(f"{scenario['method']} {expected_rule}")
                continue
            if not any(scenario["method"] in r["methods"] for r in candidates):
                mismatches.append({"method": scenario["method"], "rule": expected_rule})
        return {
            "ok": not missing and not mismatches,
            "app_build_ok": True,
            "runtime_route_count": len(all_rules),
            "mobile_runtime_route_count": len(mobile_routes),
            "missing_runtime_suffixes": missing,
            "runtime_method_mismatches": mismatches,
            "sample_mobile_routes": mobile_routes[:80],
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "app_build_ok": False,
            "runtime_route_count": 0,
            "mobile_runtime_route_count": 0,
            "missing_runtime_suffixes": [f"{s['method']} /api/mobile{s['suffix']}" for s in TARGET_SCENARIOS],
            "runtime_method_mismatches": [],
            "sample_mobile_routes": [],
            "error": f"{type(exc).__name__}: {exc}",
        }


def response_code_smoke(root: Path) -> dict[str, Any]:
    try:
        app = _build_app(root)
        client = app.test_client()
        responses: list[dict[str, Any]] = []
        scenarios = list(TARGET_SCENARIOS)
        runtime_routes = runtime_route_map(root).get("sample_mobile_routes", [])
        for opt in OPTIONAL_RUNTIME_SCENARIOS:
            expected_rule = "/api/mobile" + opt["suffix"]
            if any((r["rule"] == expected_rule or r["rule"].endswith(opt["suffix"])) and opt["method"] in r["methods"] for r in runtime_routes):
                scenarios.append(opt)
        for scenario in scenarios:
            method = scenario["method"].lower()
            path = scenario["concrete"]
            payload = scenario.get("json", {})
            if method == "get":
                resp = client.get(path)
            elif method == "post":
                resp = client.post(path, json=payload)
            else:
                continue
            ok = resp.status_code not in {404, 405}
            responses.append({
                "feature": scenario["feature"],
                "method": scenario["method"],
                "path": path,
                "status_code": resp.status_code,
                "ok": ok,
            })
        return {"ok": all(item["ok"] for item in responses), "mode": "flask_test_client_response_codes_no_404_405", "responses": responses, "error": ""}
    except Exception as exc:
        return {"ok": False, "mode": "flask_test_client_response_codes_no_404_405", "responses": [], "error": f"{type(exc).__name__}: {exc}"}


def compile_files(root: Path) -> list[dict[str, str | bool]]:
    rels = [
        "scripts/quality/bys360_mobile_support_survey_notifications_response_gate_p3d.py",
        "tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py",
        "tests/architecture/conftest.py",
    ]
    results = []
    for rel in rels:
        path = root / rel
        if not path.exists():
            results.append({"file": str(path), "ok": False, "error": "missing"})
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"file": str(path), "ok": True, "error": ""})
        except Exception as exc:
            results.append({"file": str(path), "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return results


def run_subprocess(cmd: list[str], root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("APP_ENV", "testing")
    env.setdefault("FLASK_ENV", "testing")
    env.setdefault("TESTING", "1")
    env.setdefault("SECRET_KEY", "local-test-key")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("SENTRY_DSN", "")
    proc = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True, env=env)
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "ok": proc.returncode == 0,
        "cmd": cmd,
    }


def app_factory_smoke(root: Path) -> dict[str, Any]:
    return run_subprocess([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root)


def secret_gate(root: Path) -> dict[str, Any]:
    script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not script.exists():
        return {"returncode": 1, "stdout_tail": "", "stderr_tail": "secret gate missing", "ok": False, "parsed": {}}
    result = run_subprocess([sys.executable, str(script), "--root", str(root)], root)
    parsed: dict[str, Any] = {}
    try:
        start = result["stdout_tail"].find("{")
        end = result["stdout_tail"].rfind("}")
        if start >= 0 and end >= start:
            parsed = json.loads(result["stdout_tail"][start:end+1])
    except Exception:
        parsed = {}
    result["parsed"] = parsed
    result["ok"] = bool(parsed.get("ok", result["ok"])) and int(parsed.get("finding_count", 0) or 0) == 0
    return result


def run_pytest(root: Path) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", "tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py", "-q"]
    result = run_subprocess(cmd, root)
    result["mode"] = "pytest_targeted_support_survey_notifications_response_p3d"
    return result


def ensure_active_scope(root: Path) -> dict[str, Any]:
    conftest = root / "tests" / "architecture" / "conftest.py"
    conftest.parent.mkdir(parents=True, exist_ok=True)
    if not conftest.exists():
        conftest.write_text("", encoding="utf-8")
    text = _read(conftest)
    if TEST_NAME in text:
        return {"path": str(conftest), "changed": False, "reason": "already_present"}
    marker = "# BYS360_P3D_ACTIVE_SCOPE_MARKER"
    block_lines = [
        "",
        marker,
        "try:",
        "    ACTIVE_ARCHITECTURE_TESTS",
        "except NameError:",
        "    ACTIVE_ARCHITECTURE_TESTS = set()",
        "if isinstance(ACTIVE_ARCHITECTURE_TESTS, tuple):",
        "    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS)",
        "if isinstance(ACTIVE_ARCHITECTURE_TESTS, list):",
        "    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS)",
        "try:",
        f"    ACTIVE_ARCHITECTURE_TESTS.add({TEST_NAME!r})",
        "except AttributeError:",
        f"    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS) | {{{TEST_NAME!r}}}",
    ]
    conftest.write_text(text.rstrip() + "\n" + "\n".join(block_lines) + "\n", encoding="utf-8")
    return {"path": str(conftest), "changed": True, "reason": "inserted_into_active_scope"}


def run_checks(root: Path, *, compile_all: bool = False, app_factory: bool = False, secret_gate_run: bool = False, pytest_gate: bool = False, write_report: bool = True) -> dict[str, Any]:
    root = root.resolve()
    ensure_active_scope_result = ensure_active_scope(root)
    inventory = build_inventory(root)
    runtime = runtime_route_map(root)
    response = response_code_smoke(root)
    direct_contract_ok = (
        inventory["routes_py_lines"] <= 300
        and inventory["routes_py_route_count"] == 0
        and inventory["domains_dir_exists"]
        and inventory["total_mobile_route_decorator_count"] == EXPECTED_CONTRACT_ROUTE_COUNT
        and not inventory["duplicate_route_decorators"]
        and not inventory["expected_missing_routes"]
        and all(inventory["feature_smoke"].values())
    )
    compile_results = compile_files(root) if compile_all else []
    compile_ok = all(item["ok"] for item in compile_results) if compile_all else True
    app_result = app_factory_smoke(root) if app_factory else {"ok": True}
    secret_result = secret_gate(root) if secret_gate_run else {"ok": True, "parsed": {"finding_count": 0}}
    pytest_result = run_pytest(root) if pytest_gate else {"ok": True, "mode": "not_requested"}
    result: dict[str, Any] = {
        "ok": bool(direct_contract_ok and runtime.get("ok") and response.get("ok") and compile_ok and app_result.get("ok") and secret_result.get("ok") and pytest_result.get("ok")),
        "package": PACKAGE,
        "root": str(root),
        "active_scope": ensure_active_scope_result,
        "routes_py_lines": inventory["routes_py_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "direct_contract_ok": bool(direct_contract_ok),
        "runtime_route_map_ok": bool(runtime.get("ok")),
        "response_code_smoke_ok": bool(response.get("ok")),
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_result.get("ok")),
        "secret_gate_ok": bool(secret_result.get("ok")),
        "secret_gate_finding_count": int(secret_result.get("parsed", {}).get("finding_count", 0) or 0),
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode", "not_requested"),
        "inventory": inventory,
        "runtime_route_map": runtime,
        "response_code_smoke": response,
        "compile_results": compile_results,
        "app_factory_smoke": app_result,
        "secret_gate": secret_result,
        "pytest": pytest_result,
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P3D temizse destek/anket/bildirim mobil response-code smoke kapisi runtime route haritasiyla birlikte kurulmus kabul edilebilir.",
            "P3E'de performans mobil endpointleri icin benzer response-code smoke kapisi genisletilebilir.",
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
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest", action="store_true")
    args = parser.parse_args()
    result = run_checks(
        Path(args.root),
        compile_all=args.compile_all,
        app_factory=args.app_factory,
        secret_gate_run=args.secret_gate,
        pytest_gate=args.pytest,
        write_report=True,
    )
    print(json.dumps({
        "ok": result["ok"],
        "package": result["package"],
        "routes_py_lines": result["routes_py_lines"],
        "total_mobile_route_decorator_count": result["total_mobile_route_decorator_count"],
        "direct_contract_ok": result["direct_contract_ok"],
        "runtime_route_map_ok": result["runtime_route_map_ok"],
        "response_code_smoke_ok": result["response_code_smoke_ok"],
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
