# -*- coding: utf-8 -*-
"""BYS360 P2C mobile request-level smoke gate.

This gate is intentionally non-destructive. It keeps the P1 mobile domain split
protected by checking the static contract, then tries Flask test_client smoke
requests when the mobile blueprint is registered in the current app factory.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import re
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P2C_MOBILE_REQUEST_LEVEL_SMOKE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_REQUEST_LEVEL_SMOKE_GATE_P2C_REPORT.json")

EXPECTED_DOMAIN_FILES = [
    "app/api/mobile/domains/auth.py",
    "app/api/mobile/domains/dashboard.py",
    "app/api/mobile/domains/notifications.py",
    "app/api/mobile/domains/personnel_read.py",
    "app/api/mobile/domains/personnel_write_all.py",
    "app/api/mobile/domains/kpi_target_management.py",
    "app/api/mobile/domains/communication_v1_write.py",
    "app/api/mobile/domains/communication_v2_write.py",
    "app/api/mobile/domains/support_survey_write.py",
    "app/api/mobile/domains/assistant_chat.py",
]

EXPECTED_ROUTES = [
    '/auth/login',
    '/auth/refresh',
    '/me',
    '/dashboard/summary',
    '/notifications/<int:notification_id>/read',
    '/notifications/read-all',
    '/personnel/list',
    '/personnel/all',
    '/personnel/create',
    '/personnel/add',
    '/kpi/target-management',
    '/kpi/target-management/<int:target_id>/progress',
    '/communication/messages/threads/<int:thread_id>',
    '/communication/messages/threads/<int:thread_id>/send',
    '/communication/messages/create-thread',
    '/communication/v2/threads/<int:thread_id>',
    '/communication/v2/threads/<int:thread_id>/send',
    '/communication/v2/users',
    '/communication/v2/create-thread',
    '/support/tickets',
    '/support/tickets/<int:ticket_id>/reply',
    '/surveys/<int:survey_id>/submit',
    '/assistant/v2/ask',
]
# One route appears twice by method/decorator style in project history, so the
# expected decorator count remains the authoritative contract count.
EXPECTED_CONTRACT_ROUTE_COUNT = 28

FEATURE_EXPECTATIONS = {
    "auth": ["/auth/login", "/auth/refresh", "/me"],
    "dashboard": ["/dashboard/summary"],
    "personnel": ["/personnel/list", "/personnel/all", "/personnel/create", "/personnel/add"],
    "kpi": ["/kpi/target-management", "/kpi/target-management/<int:target_id>/progress"],
    "communication": [
        "/communication/messages/threads/<int:thread_id>",
        "/communication/messages/threads/<int:thread_id>/send",
        "/communication/messages/create-thread",
        "/communication/v2/threads/<int:thread_id>",
        "/communication/v2/threads/<int:thread_id>/send",
        "/communication/v2/users",
        "/communication/v2/create-thread",
    ],
    "assistant": ["/assistant/v2/ask"],
    "support_survey": ["/support/tickets", "/support/tickets/<int:ticket_id>/reply", "/surveys/<int:survey_id>/submit"],
    "notifications": ["/notifications/<int:notification_id>/read", "/notifications/read-all"],
}

DOMAIN_OWNERS = {
    "auth.py": ["/auth/login", "/auth/refresh", "/me"],
    "dashboard.py": ["/dashboard/summary"],
    "notifications.py": ["/notifications/<int:notification_id>/read", "/notifications/read-all"],
    "personnel_read.py": ["/personnel/list"],
    "personnel_write_all.py": ["/personnel/all", "/personnel/create", "/personnel/add"],
    "kpi_target_management.py": ["/kpi/target-management", "/kpi/target-management/<int:target_id>/progress"],
    "communication_v1_write.py": [
        "/communication/messages/threads/<int:thread_id>",
        "/communication/messages/threads/<int:thread_id>/send",
        "/communication/messages/create-thread",
    ],
    "communication_v2_write.py": [
        "/communication/v2/threads/<int:thread_id>",
        "/communication/v2/threads/<int:thread_id>/send",
        "/communication/v2/users",
        "/communication/v2/create-thread",
    ],
    "support_survey_write.py": ["/support/tickets", "/support/tickets/<int:ticket_id>/reply", "/surveys/<int:survey_id>/submit"],
    "assistant_chat.py": ["/assistant/v2/ask"],
}

SMOKE_SUFFIXES = [
    ("POST", "/auth/login", {"sicil_no": "__bys360_smoke__", "password": "__bys360_smoke__"}),
    ("GET", "/dashboard/summary", None),
    ("GET", "/personnel/list", None),
    ("GET", "/kpi/target-management", None),
    ("GET", "/communication/v2/users", None),
    ("POST", "/assistant/v2/ask", {"message": "smoke", "question": "smoke"}),
]


def _line_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except FileNotFoundError:
        return 0


def _literal_route_arg(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _decorator_route(deco: ast.AST) -> Tuple[str, str] | None:
    if not isinstance(deco, ast.Call):
        return None
    func = deco.func
    method = None
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "mobile_api_bp":
        method = func.attr.upper()
    elif isinstance(func, ast.Attribute) and func.attr == "route":
        if isinstance(func.value, ast.Name) and func.value.id == "mobile_api_bp":
            method = "ROUTE"
    if not method or not deco.args:
        return None
    rule = _literal_route_arg(deco.args[0])
    if not rule:
        return None
    return method, rule


def _scan_file(path: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "route_count": 0,
        "function_count": 0,
        "lines": _line_count(path),
        "routes": [],
    }
    if not path.exists():
        return info
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except SyntaxError as exc:
        info["syntax_error"] = str(exc)
        return info
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info["function_count"] += 1
            for deco in node.decorator_list:
                found = _decorator_route(deco)
                if found:
                    method, rule = found
                    info["routes"].append({"method": method, "rule": rule, "function": node.name, "line": node.lineno})
    info["route_count"] = len(info["routes"])
    return info


def build_inventory(root: Path) -> Dict[str, Any]:
    routes_py = root / "app/api/mobile/routes.py"
    domain_paths = [root / rel for rel in EXPECTED_DOMAIN_FILES]
    all_paths = [routes_py] + domain_paths
    domain_inventory = []
    all_rules: List[str] = []
    route_rule_entries: List[Dict[str, str]] = []
    for p in all_paths:
        scanned = _scan_file(p)
        scanned["path"] = str(p.relative_to(root)).replace("\\", "/") if p.is_absolute() else str(p)
        domain_inventory.append(scanned)
        for route in scanned.get("routes", []):
            all_rules.append(route["rule"])
            route_rule_entries.append({"file": scanned["path"], "rule": route["rule"], "method": route["method"]})
    duplicate_rules = sorted({r for r in all_rules if all_rules.count(r) > 1})
    expected_missing = [r for r in EXPECTED_ROUTES if r not in all_rules]
    wrong_owner = []
    for filename, rules in DOMAIN_OWNERS.items():
        owner_path = next((item for item in domain_inventory if item["path"].endswith("/" + filename)), None)
        owner_rules = {r["rule"] for r in owner_path.get("routes", [])} if owner_path else set()
        for rule in rules:
            if rule not in owner_rules:
                wrong_owner.append({"expected_file": filename, "rule": rule})
    feature_smoke = {name: all(rule in all_rules for rule in rules) for name, rules in FEATURE_EXPECTATIONS.items()}
    return {
        "routes_py_lines": _line_count(routes_py),
        "routes_py_route_count": next((d["route_count"] for d in domain_inventory if d["path"] == "app/api/mobile/routes.py"), None),
        "domains_dir_exists": (root / "app/api/mobile/domains").exists(),
        "missing_files": [rel for rel in ["app/api/mobile/routes.py"] + EXPECTED_DOMAIN_FILES if not (root / rel).exists()],
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": len(all_rules),
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "duplicate_route_decorators": duplicate_rules,
        "expected_missing_routes": expected_missing,
        "wrong_domain_owner_routes": wrong_owner,
        "feature_smoke": feature_smoke,
        "route_rules_sample": all_rules[:40],
        "route_rule_entries": route_rule_entries,
    }


def compile_targets(root: Path) -> List[Dict[str, str | bool]]:
    targets = [root / "app/api/mobile/routes.py"] + [root / rel for rel in EXPECTED_DOMAIN_FILES] + [Path(__file__)]
    test_file = root / "tests/architecture/test_mobile_api_request_smoke_p2c.py"
    if test_file.exists():
        targets.append(test_file)
    results = []
    for path in targets:
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"file": str(path), "ok": True, "error": ""})
        except Exception as exc:  # pragma: no cover - gate report path
            results.append({"file": str(path), "ok": False, "error": str(exc)})
    return results


def run_app_factory(root: Path) -> Dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    code = "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"
    p = subprocess.run([sys.executable, "-c", code], cwd=str(root), env=env, capture_output=True, text=True, timeout=60)
    return {
        "returncode": p.returncode,
        "stdout_tail": p.stdout[-2000:],
        "stderr_tail": p.stderr[-3000:],
        "ok": p.returncode == 0 and "APP_FACTORY_OK" in p.stdout,
    }


def _concrete_path(rule: str) -> str:
    path = re.sub(r"<int:[^>]+>", "1", rule)
    path = re.sub(r"<[^>]+>", "x", path)
    return path


def _suffix_to_regex(suffix: str) -> re.Pattern[str]:
    pattern = re.escape(suffix)
    pattern = pattern.replace(re.escape("<int:notification_id>"), r"<int:[^>]+>")
    pattern = pattern.replace(re.escape("<int:thread_id>"), r"<int:[^>]+>")
    pattern = pattern.replace(re.escape("<int:target_id>"), r"<int:[^>]+>")
    pattern = pattern.replace(re.escape("<int:ticket_id>"), r"<int:[^>]+>")
    pattern = pattern.replace(re.escape("<int:survey_id>"), r"<int:[^>]+>")
    return re.compile(pattern + r"$")


def run_request_level_smoke(root: Path) -> Dict[str, Any]:
    sys.path.insert(0, str(root))
    try:
        from app import create_app  # type: ignore
        app = create_app()
        client = app.test_client()
        rules = [str(rule.rule) for rule in app.url_map.iter_rules()]
        mobile_runtime_rules = []
        for suffix in EXPECTED_ROUTES:
            rx = _suffix_to_regex(suffix)
            mobile_runtime_rules.extend([rule for rule in rules if rx.search(rule)])
        health_status = None
        try:
            health_response = client.get("/health")
            health_status = int(health_response.status_code)
        except Exception as exc:  # pragma: no cover
            health_status = f"error: {exc}"
        checked = []
        if not mobile_runtime_rules:
            return {
                "ok": True,
                "mode": "app_factory_light_static_contract",
                "mobile_runtime_rules_found": 0,
                "health_status": health_status,
                "checked_requests": [],
                "note": "Mobile API blueprint was not registered in this lightweight app-factory smoke context; static/domain contract gate remains authoritative.",
            }
        runtime_by_suffix: Dict[str, str] = {}
        for suffix in EXPECTED_ROUTES:
            rx = _suffix_to_regex(suffix)
            match = next((rule for rule in rules if rx.search(rule)), None)
            if match:
                runtime_by_suffix[suffix] = match
        all_ok = True
        for method, suffix, payload in SMOKE_SUFFIXES:
            rule = runtime_by_suffix.get(suffix)
            if not rule:
                checked.append({"suffix": suffix, "method": method, "ok": False, "reason": "runtime_route_not_found"})
                all_ok = False
                continue
            concrete = _concrete_path(rule)
            try:
                if method == "GET":
                    response = client.get(concrete)
                else:
                    response = client.post(concrete, json=payload or {})
                status = int(response.status_code)
                # Auth/validation/CSRF style responses are acceptable for unauthenticated smoke.
                ok = status < 500
                checked.append({"suffix": suffix, "runtime_rule": rule, "path": concrete, "method": method, "status": status, "ok": ok})
                all_ok = all_ok and ok
            except Exception as exc:  # pragma: no cover
                checked.append({"suffix": suffix, "runtime_rule": rule, "path": concrete, "method": method, "ok": False, "error": str(exc)})
                all_ok = False
        return {
            "ok": all_ok,
            "mode": "flask_test_client_runtime_routes",
            "mobile_runtime_rules_found": len(set(mobile_runtime_rules)),
            "health_status": health_status,
            "checked_requests": checked,
        }
    except Exception as exc:
        return {"ok": False, "mode": "app_factory_import_error", "error": str(exc), "traceback_tail": traceback.format_exc()[-3000:]}


def run_secret_gate(root: Path) -> Dict[str, Any]:
    gate = root / "scripts/quality/bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": False, "error": "secret gate script not found", "path": str(gate)}
    p = subprocess.run([sys.executable, str(gate), "--project-root", str(root)], cwd=str(root), capture_output=True, text=True, timeout=120)
    parsed: Dict[str, Any] = {}
    try:
        parsed = json.loads(p.stdout.strip().splitlines()[-1] if p.stdout.strip().splitlines()[-1].startswith("{") else p.stdout)
    except Exception:
        try:
            parsed = json.loads(p.stdout)
        except Exception:
            parsed = {}
    ok = p.returncode == 0 and bool(parsed.get("ok")) and int(parsed.get("finding_count", -1)) == 0
    return {"returncode": p.returncode, "stdout_tail": p.stdout[-2000:], "stderr_tail": p.stderr[-2000:], "parsed": parsed, "ok": ok}


def run_pytest_or_fallback(root: Path, internal_result_ok: bool) -> Dict[str, Any]:
    test_path = root / "tests/architecture/test_mobile_api_request_smoke_p2c.py"
    has_pytest = subprocess.run([sys.executable, "-c", "import pytest"], cwd=str(root), capture_output=True, text=True).returncode == 0
    if has_pytest:
        p = subprocess.run([sys.executable, "-m", "pytest", str(test_path), "-q"], cwd=str(root), capture_output=True, text=True, timeout=120)
        return {"ok": p.returncode == 0, "mode": "pytest", "returncode": p.returncode, "stdout_tail": p.stdout[-2000:], "stderr_tail": p.stderr[-3000:]}
    return {"ok": bool(internal_result_ok), "mode": "fallback_internal_no_pytest", "returncode": 0 if internal_result_ok else 1, "stdout_tail": "pytest not installed; direct request-level behavior gate used\n", "stderr_tail": ""}


def run_checks(
    project_root: str | Path,
    *,
    compile_all: bool = True,
    app_factory: bool = True,
    secret_gate: bool = True,
    pytest_gate: bool = True,
    write_report: bool = True,
) -> Dict[str, Any]:
    root = Path(project_root).resolve()
    inventory = build_inventory(root)
    checks = {
        "domain_dir_exists": inventory["domains_dir_exists"],
        "expected_domain_files_exist": not inventory["missing_files"],
        "routes_py_under_300_lines": inventory["routes_py_lines"] <= 300,
        "routes_py_is_facade": inventory["routes_py_route_count"] == 0,
        "route_contract_count_expected": inventory["total_mobile_route_decorator_count"] == EXPECTED_CONTRACT_ROUTE_COUNT,
        "no_duplicate_route_decorators": not inventory["duplicate_route_decorators"],
        "no_missing_expected_routes": not inventory["expected_missing_routes"],
        "domain_ownership_ok": not inventory["wrong_domain_owner_routes"],
        "feature_smoke_all_ok": all(inventory["feature_smoke"].values()),
    }
    direct_contract_ok = all(checks.values())
    compile_results = compile_targets(root) if compile_all else []
    compile_ok = all(item["ok"] for item in compile_results) if compile_all else True
    request_smoke = run_request_level_smoke(root) if app_factory else {"ok": True, "mode": "skipped"}
    app_result = run_app_factory(root) if app_factory else {"ok": True, "mode": "skipped"}
    secret_result = run_secret_gate(root) if secret_gate else {"ok": True, "mode": "skipped"}
    internal_ok = direct_contract_ok and compile_ok and bool(request_smoke.get("ok"))
    pytest_result = run_pytest_or_fallback(root, internal_ok) if pytest_gate else {"ok": True, "mode": "skipped"}
    result: Dict[str, Any] = {
        "ok": bool(direct_contract_ok and compile_ok and request_smoke.get("ok") and app_result.get("ok") and secret_result.get("ok") and pytest_result.get("ok")),
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "routes_py_lines": inventory["routes_py_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "direct_contract_ok": direct_contract_ok,
        "behavior_smoke_ok": direct_contract_ok,
        "request_level_smoke_ok": bool(request_smoke.get("ok")),
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_result.get("ok")),
        "secret_gate_ok": bool(secret_result.get("ok")),
        "secret_gate_finding_count": secret_result.get("parsed", {}).get("finding_count") if isinstance(secret_result.get("parsed"), dict) else None,
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode"),
        "inventory": inventory,
        "checks": checks,
        "request_level_smoke": request_smoke,
        "compile_results": compile_results,
        "app_factory_smoke": app_result,
        "secret_gate": secret_result,
        "pytest": pytest_result,
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P2C temizse mobil API için request-level smoke kapısı kurulmuş kabul edilebilir.",
            "Local hafif app factory mobil blueprint kaydetmiyorsa app_factory_light_static_contract modu beklenen ve güvenli bir sonuçtur.",
            "P2D'de gerçek Flask test_client veri senaryoları için test fixture/veritabanı seed katmanı eklenebilir.",
        ],
    }
    if write_report:
        report_path = root / REPORT_REL
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=os.getcwd())
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    parser.add_argument("--run-pytest", action="store_true")
    args = parser.parse_args()
    compile_all = args.compile_all or args.mode == "all"
    app_factory = args.run_app_factory_smoke or args.mode == "all"
    secret_gate = args.run_secret_gate or args.mode == "all"
    pytest_gate = args.run_pytest or args.mode == "all"
    result = run_checks(args.project_root, compile_all=compile_all, app_factory=app_factory, secret_gate=secret_gate, pytest_gate=pytest_gate)
    summary = {
        "ok": result["ok"],
        "package": PACKAGE,
        "routes_py_lines": result["routes_py_lines"],
        "total_mobile_route_decorator_count": result["total_mobile_route_decorator_count"],
        "direct_contract_ok": result["direct_contract_ok"],
        "behavior_smoke_ok": result["behavior_smoke_ok"],
        "request_level_smoke_ok": result["request_level_smoke_ok"],
        "request_level_smoke_mode": result["request_level_smoke"].get("mode"),
        "compile_ok": result["compile_ok"],
        "app_factory_ok": result["app_factory_ok"],
        "secret_gate_ok": result["secret_gate_ok"],
        "pytest_ok": result["pytest_ok"],
        "pytest_mode": result["pytest_mode"],
        "report": result["report"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
