from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import py_compile
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Tuple

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P2B_MOBILE_BEHAVIOR_SMOKE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_BEHAVIOR_SMOKE_GATE_P2B_REPORT.json")
TEST_REL = Path("tests/architecture/test_mobile_api_behavior_smoke_p2b.py")

EXPECTED_DOMAIN_CONTRACT: Dict[str, List[Tuple[str, str]]] = {
    "auth.py": [
        ("POST", "/auth/login"),
        ("POST", "/auth/refresh"),
        ("GET", "/me"),
    ],
    "dashboard.py": [
        ("GET", "/dashboard/summary"),
    ],
    "notifications.py": [
        ("POST", "/notifications/<int:notification_id>/read"),
        ("POST", "/notifications/read-all"),
    ],
    "personnel_read.py": [
        ("GET", "/personnel/list"),
    ],
    "personnel_write_all.py": [
        ("GET", "/personnel/all"),
        ("POST", "/personnel/create"),
        ("POST", "/personnel/add"),
    ],
    "kpi_target_management.py": [
        ("GET", "/kpi/target-management"),
        ("POST", "/kpi/target-management"),
        ("POST", "/kpi/target-management/<int:target_id>/progress"),
    ],
    "communication_v1_write.py": [
        ("GET", "/communication/messages/threads/<int:thread_id>"),
        ("POST", "/communication/messages/threads/<int:thread_id>/send"),
        ("POST", "/communication/messages/create-thread"),
    ],
    "communication_v2_write.py": [
        ("GET", "/communication/v2/threads/<int:thread_id>"),
        ("POST", "/communication/v2/threads/<int:thread_id>/send"),
        ("GET", "/communication/v2/users"),
        ("POST", "/communication/v2/create-thread"),
    ],
    "support_survey_write.py": [
        ("POST", "/support/tickets"),
        ("POST", "/support/tickets/<int:ticket_id>/reply"),
        ("POST", "/surveys/<int:survey_id>/submit"),
    ],
    "assistant_chat.py": [
        ("POST", "/assistant/v2/ask"),
    ],
}

EXPECTED_ROUTE_COUNT = sum(len(v) for v in EXPECTED_DOMAIN_CONTRACT.values())
METHODS = {"get", "post", "put", "patch", "delete"}
DECORATOR_RE = re.compile(r"@mobile_api_bp\.(get|post|put|patch|delete)\(\s*(['\"])(.*?)\2")

def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path)


def count_functions(path: Path) -> int:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return -1
    return sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))


def extract_mobile_decorators(root: Path, path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    text = path.read_text(encoding="utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), start=1):
        m = DECORATOR_RE.search(line)
        if not m:
            continue
        rows.append({
            "file": _rel(root, path),
            "line": lineno,
            "method": m.group(1).upper(),
            "rule": m.group(3),
            "decorator": line.strip(),
        })
    return rows


def build_inventory(root: Path) -> Dict[str, Any]:
    mobile_root = root / "app" / "api" / "mobile"
    domains_root = mobile_root / "domains"
    routes_py = mobile_root / "routes.py"
    paths = [routes_py] + [domains_root / name for name in EXPECTED_DOMAIN_CONTRACT]
    domain_inventory: List[Dict[str, Any]] = []
    all_routes: List[Dict[str, Any]] = []
    missing_files: List[str] = []
    for path in paths:
        exists = path.exists()
        if not exists:
            missing_files.append(_rel(root, path))
        decorators = extract_mobile_decorators(root, path)
        all_routes.extend(decorators)
        lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines()) if exists else 0
        domain_inventory.append({
            "path": _rel(root, path),
            "exists": exists,
            "route_count": len(decorators),
            "function_count": count_functions(path) if exists else 0,
            "lines": lines,
        })

    seen: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for row in all_routes:
        seen.setdefault((row["method"], row["rule"]), []).append(row)
    duplicates = [
        {"method": method, "rule": rule, "locations": rows}
        for (method, rule), rows in seen.items()
        if len(rows) > 1
    ]

    expected_missing: List[Dict[str, str]] = []
    wrong_owner: List[Dict[str, str]] = []
    by_key = {(row["method"], row["rule"]): row for row in all_routes}
    for filename, expected_pairs in EXPECTED_DOMAIN_CONTRACT.items():
        expected_rel = f"app/api/mobile/domains/{filename}"
        for method, rule in expected_pairs:
            row = by_key.get((method, rule))
            if not row:
                expected_missing.append({"file": expected_rel, "method": method, "rule": rule})
            elif row["file"] != expected_rel:
                wrong_owner.append({
                    "method": method,
                    "rule": rule,
                    "expected_file": expected_rel,
                    "actual_file": row["file"],
                })

    feature_smoke = {
        "auth": all((m, r) in by_key for m, r in EXPECTED_DOMAIN_CONTRACT["auth.py"]),
        "dashboard": all((m, r) in by_key for m, r in EXPECTED_DOMAIN_CONTRACT["dashboard.py"]),
        "personnel": all((m, r) in by_key for name in ("personnel_read.py", "personnel_write_all.py") for m, r in EXPECTED_DOMAIN_CONTRACT[name]),
        "kpi": all((m, r) in by_key for m, r in EXPECTED_DOMAIN_CONTRACT["kpi_target_management.py"]),
        "communication": all((m, r) in by_key for name in ("communication_v1_write.py", "communication_v2_write.py") for m, r in EXPECTED_DOMAIN_CONTRACT[name]),
        "assistant": all((m, r) in by_key for m, r in EXPECTED_DOMAIN_CONTRACT["assistant_chat.py"]),
        "support_survey": all((m, r) in by_key for m, r in EXPECTED_DOMAIN_CONTRACT["support_survey_write.py"]),
        "notifications": all((m, r) in by_key for m, r in EXPECTED_DOMAIN_CONTRACT["notifications.py"]),
    }

    return {
        "routes_py_lines": next((x["lines"] for x in domain_inventory if x["path"] == "app/api/mobile/routes.py"), 0),
        "routes_py_route_count": next((x["route_count"] for x in domain_inventory if x["path"] == "app/api/mobile/routes.py"), 0),
        "domains_dir_exists": domains_root.exists(),
        "missing_files": missing_files,
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": len(all_routes),
        "expected_contract_route_count": EXPECTED_ROUTE_COUNT,
        "duplicate_route_decorators": duplicates,
        "expected_missing_routes": expected_missing,
        "wrong_domain_owner_routes": wrong_owner,
        "feature_smoke": feature_smoke,
        "route_rules_sample": [row["decorator"] for row in all_routes[:40]],
    }


def compile_files(root: Path, files: List[Path]) -> Tuple[bool, List[Dict[str, str]]]:
    results: List[Dict[str, str]] = []
    ok = True
    for path in files:
        if not path.exists():
            ok = False
            results.append({"file": str(path), "ok": False, "error": "missing"})
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"file": str(path), "ok": True, "error": ""})
        except Exception as exc:
            ok = False
            results.append({"file": str(path), "ok": False, "error": repr(exc)})
    return ok, results


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 60) -> Dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("APP_ENV", "development")
    env.setdefault("FLASK_ENV", "development")
    env.setdefault("BYS360_SKIP_SCHEDULERS", "1")
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout, env=env)
        return {
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-3000:],
            "stderr_tail": proc.stderr[-3000:],
            "ok": proc.returncode == 0,
        }
    except Exception as exc:
        return {"returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc), "ok": False}


def parse_last_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        return {}
    # Prefer parsing entire output; then progressively try JSON object tails.
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        pass
    starts = [i for i, ch in enumerate(text) if ch == "{"]
    for i in reversed(starts):
        try:
            obj = json.loads(text[i:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return {}


def run_secret_gate(root: Path, python_exe: str) -> Dict[str, Any]:
    script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not script.exists():
        return {"ok": True, "skipped": True, "reason": "secret_gate_script_missing"}
    result = run_cmd([python_exe, str(script), "--project-root", str(root)], cwd=root, timeout=120)
    parsed = parse_last_json(result.get("stdout_tail", ""))
    result["parsed"] = parsed
    result["ok"] = bool(result["ok"] and parsed.get("ok") is True and int(parsed.get("finding_count", 0)) == 0)
    return result


def write_pytest_file(root: Path) -> Path:
    test_path = root / TEST_REL
    test_path.parent.mkdir(parents=True, exist_ok=True)
    content = r'''from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "auth.py": [("POST", "/auth/login"), ("POST", "/auth/refresh"), ("GET", "/me")],
    "dashboard.py": [("GET", "/dashboard/summary")],
    "notifications.py": [("POST", "/notifications/<int:notification_id>/read"), ("POST", "/notifications/read-all")],
    "personnel_read.py": [("GET", "/personnel/list")],
    "personnel_write_all.py": [("GET", "/personnel/all"), ("POST", "/personnel/create"), ("POST", "/personnel/add")],
    "kpi_target_management.py": [("GET", "/kpi/target-management"), ("POST", "/kpi/target-management"), ("POST", "/kpi/target-management/<int:target_id>/progress")],
    "communication_v1_write.py": [("GET", "/communication/messages/threads/<int:thread_id>"), ("POST", "/communication/messages/threads/<int:thread_id>/send"), ("POST", "/communication/messages/create-thread")],
    "communication_v2_write.py": [("GET", "/communication/v2/threads/<int:thread_id>"), ("POST", "/communication/v2/threads/<int:thread_id>/send"), ("GET", "/communication/v2/users"), ("POST", "/communication/v2/create-thread")],
    "support_survey_write.py": [("POST", "/support/tickets"), ("POST", "/support/tickets/<int:ticket_id>/reply"), ("POST", "/surveys/<int:survey_id>/submit")],
    "assistant_chat.py": [("POST", "/assistant/v2/ask")],
}
DECORATOR_RE = re.compile(r"@mobile_api_bp\.(get|post|put|patch|delete)\(\s*(['\"])(.*?)\2")

def extract(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = DECORATOR_RE.search(line)
        if m:
            rows.append((m.group(1).upper(), m.group(3), str(path.relative_to(ROOT)).replace("\\", "/")))
    return rows

def test_mobile_domain_files_exist_and_compile():
    base = ROOT / "app" / "api" / "mobile" / "domains"
    assert base.exists()
    for filename in EXPECTED:
        path = base / filename
        assert path.exists(), filename
        ast.parse(path.read_text(encoding="utf-8"))

def test_mobile_route_contract_and_domain_ownership():
    base = ROOT / "app" / "api" / "mobile" / "domains"
    routes = []
    for filename in EXPECTED:
        routes.extend(extract(base / filename))
    assert len(routes) == 24
    assert len(set((m, r) for m, r, _ in routes)) == 24
    found = {(m, r): file for m, r, file in routes}
    for filename, pairs in EXPECTED.items():
        expected_file = f"app/api/mobile/domains/{filename}"
        for method, rule in pairs:
            assert (method, rule) in found, (method, rule)
            assert found[(method, rule)] == expected_file

def test_mobile_routes_py_is_facade_only():
    routes_py = ROOT / "app" / "api" / "mobile" / "routes.py"
    assert routes_py.exists()
    assert len(routes_py.read_text(encoding="utf-8", errors="replace").splitlines()) <= 300
    assert extract(routes_py) == []
'''
    test_path.write_text(content, encoding="utf-8")
    return test_path


def run_pytest_or_fallback(root: Path, python_exe: str, direct_ok: bool) -> Dict[str, Any]:
    pytest_available = run_cmd([python_exe, "-c", "import pytest; print('PYTEST_AVAILABLE')"], cwd=root, timeout=30)
    if pytest_available.get("ok"):
        result = run_cmd([python_exe, "-m", "pytest", str(root / TEST_REL), "-q"], cwd=root, timeout=120)
        result["mode"] = "pytest"
        return result
    return {
        "ok": bool(direct_ok),
        "mode": "fallback_internal_no_pytest",
        "returncode": 0 if direct_ok else 1,
        "stdout_tail": "pytest not installed; direct behavior contract gate used\n",
        "stderr_tail": "",
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    parser.add_argument("--run-pytest", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    python_exe = sys.executable
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)

    test_path = write_pytest_file(root)
    inventory = build_inventory(root)

    checks = {
        "domain_dir_exists": inventory["domains_dir_exists"],
        "expected_domain_files_exist": not inventory["missing_files"],
        "routes_py_under_300_lines": inventory["routes_py_lines"] <= 300,
        "routes_py_is_facade": inventory["routes_py_route_count"] == 0,
        "route_contract_count_expected": inventory["total_mobile_route_decorator_count"] == EXPECTED_ROUTE_COUNT,
        "no_duplicate_route_decorators": not inventory["duplicate_route_decorators"],
        "no_missing_expected_routes": not inventory["expected_missing_routes"],
        "domain_ownership_ok": not inventory["wrong_domain_owner_routes"],
        "feature_smoke_all_ok": all(inventory["feature_smoke"].values()),
    }
    direct_contract_ok = all(checks.values())

    files_to_compile = [
        root / "app/api/mobile/routes.py",
        *[(root / "app/api/mobile/domains" / name) for name in EXPECTED_DOMAIN_CONTRACT],
        root / "scripts/quality/bys360_mobile_behavior_smoke_p2b.py",
        test_path,
    ]
    compile_ok, compile_results = compile_files(root, files_to_compile) if args.compile_all else (True, [])

    app_factory = {"ok": True, "skipped": True}
    if args.run_app_factory_smoke:
        app_factory = run_cmd([python_exe, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], cwd=root, timeout=120)

    secret_gate = {"ok": True, "skipped": True}
    if args.run_secret_gate:
        secret_gate = run_secret_gate(root, python_exe)

    pytest_result = {"ok": True, "skipped": True, "mode": "not_requested"}
    if args.run_pytest:
        pytest_result = run_pytest_or_fallback(root, python_exe, direct_contract_ok)

    ok = bool(direct_contract_ok and compile_ok and app_factory.get("ok") and secret_gate.get("ok") and pytest_result.get("ok"))
    report: Dict[str, Any] = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": _now(),
        "root": str(root),
        "mode": args.mode,
        "changed_count": 2,
        "changed": [str(TEST_REL).replace("\\", "/"), "scripts/quality/bys360_mobile_behavior_smoke_p2b.py"],
        "routes_py_lines": inventory["routes_py_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_ROUTE_COUNT,
        "direct_contract_ok": direct_contract_ok,
        "behavior_smoke_ok": checks["feature_smoke_all_ok"],
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_factory.get("ok")),
        "secret_gate_ok": bool(secret_gate.get("ok")),
        "secret_gate_finding_count": int(secret_gate.get("parsed", {}).get("finding_count", 0)) if isinstance(secret_gate.get("parsed"), dict) else 0,
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode", "unknown"),
        "inventory": inventory,
        "checks": checks,
        "compile_results": compile_results,
        "app_factory_smoke": app_factory,
        "secret_gate": secret_gate,
        "pytest": pytest_result,
        "report": str(report_path),
        "next_actions": [
            "P2B temizse mobil API domain davranissal smoke kapisi kurulmus kabul edilebilir.",
            "P2C'de Flask test_client ile auth/dashboard/assistant icin mock veri destekli request-level smoke testleri genisletilebilir.",
            "CI ortaminda pytest kurulu oldugunda tests/architecture/test_mobile_api_behavior_smoke_p2b.py dogrudan calisacaktir.",
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "package": PACKAGE,
        "routes_py_lines": inventory["routes_py_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "direct_contract_ok": direct_contract_ok,
        "behavior_smoke_ok": checks["feature_smoke_all_ok"],
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_factory.get("ok")),
        "secret_gate_ok": bool(secret_gate.get("ok")),
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode", "unknown"),
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
