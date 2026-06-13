from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P2A_MOBILE_PYTEST_CONTRACT_GATE_V2"
EXPECTED_ROUTE_COUNT = 24
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


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def line_count(text: str) -> int:
    return len(text.splitlines())


def compile_file(path: Path) -> dict[str, Any]:
    try:
        compile(read_text(path), str(path), "exec")
        return {"file": str(path), "ok": True, "error": ""}
    except Exception as exc:
        return {"file": str(path), "ok": False, "error": repr(exc)}


def extract_route_decorators(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    routes: list[dict[str, Any]] = []
    try:
        tree = ast.parse(read_text(path), filename=str(path))
    except Exception:
        return routes
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            if not isinstance(func, ast.Attribute):
                continue
            owner = func.value
            if not isinstance(owner, ast.Name) or owner.id != "mobile_api_bp":
                continue
            if func.attr not in {"get", "post", "put", "patch", "delete", "route"}:
                continue
            rule = None
            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                rule = dec.args[0].value
            routes.append({
                "file": str(path),
                "line": getattr(dec, "lineno", getattr(node, "lineno", 0)),
                "function": node.name,
                "decorator": func.attr,
                "rule": rule,
            })
    return routes


def parse_last_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass
    decoder = json.JSONDecoder()
    best: dict[str, Any] = {}
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            if isinstance(obj, dict):
                best = obj
        except Exception:
            continue
    return best


def run_cmd(args: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 180) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "args": args,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-6000:],
            "stderr_tail": proc.stderr[-6000:],
            "ok": proc.returncode == 0,
        }
    except Exception as exc:
        return {"args": args, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(exc), "ok": False}


def ensure_pytest_contract_file(root: Path) -> dict[str, Any]:
    test_dir = root / "tests" / "mobile"
    test_file = test_dir / "test_mobile_domain_contract_p2a.py"
    test_dir.mkdir(parents=True, exist_ok=True)
    content = '''from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOBILE_ROOT = ROOT / "app" / "api" / "mobile"
EXPECTED_DOMAIN_FILES = [
    "auth.py",
    "dashboard.py",
    "notifications.py",
    "personnel_read.py",
    "personnel_write_all.py",
    "kpi_target_management.py",
    "communication_v1_write.py",
    "communication_v2_write.py",
    "support_survey_write.py",
    "assistant_chat.py",
]
EXPECTED_ROUTE_COUNT = 24


def _extract_routes(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    rules: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                continue
            owner = dec.func.value
            if not isinstance(owner, ast.Name) or owner.id != "mobile_api_bp":
                continue
            if dec.func.attr not in {"get", "post", "put", "patch", "delete", "route"}:
                continue
            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                rules.append(dec.args[0].value)
    return rules


def _all_mobile_route_files() -> list[Path]:
    domain_dir = MOBILE_ROOT / "domains"
    return [MOBILE_ROOT / "routes.py", *[domain_dir / name for name in EXPECTED_DOMAIN_FILES]]


def test_mobile_routes_py_is_facade_sized():
    routes_py = MOBILE_ROOT / "routes.py"
    assert routes_py.exists()
    assert len(routes_py.read_text(encoding="utf-8-sig").splitlines()) <= 300


def test_mobile_domain_files_exist():
    domain_dir = MOBILE_ROOT / "domains"
    assert domain_dir.exists()
    for filename in EXPECTED_DOMAIN_FILES:
        assert (domain_dir / filename).exists(), filename


def test_mobile_route_contract_count():
    route_rules: list[str] = []
    for path in _all_mobile_route_files():
        assert path.exists(), str(path)
        route_rules.extend(_extract_routes(path))
    assert len(route_rules) == EXPECTED_ROUTE_COUNT
    assert len(route_rules) == len(set(route_rules))


if __name__ == "__main__":
    # Fallback runner for environments where pytest is not installed.
    test_mobile_routes_py_is_facade_sized()
    test_mobile_domain_files_exist()
    test_mobile_route_contract_count()
    print("P2A_MOBILE_CONTRACT_TEST_OK")
'''
    previous = test_file.read_text(encoding="utf-8-sig", errors="replace") if test_file.exists() else None
    changed = previous != content
    if changed:
        test_file.write_text(content, encoding="utf-8")
    return {"path": str(test_file), "changed": changed}


def build_inventory(root: Path) -> dict[str, Any]:
    routes_py = root / "app" / "api" / "mobile" / "routes.py"
    all_paths = [routes_py, *[root / path for path in EXPECTED_DOMAIN_FILES]]
    domain_inventory = []
    all_routes: list[dict[str, Any]] = []
    compile_results: list[dict[str, Any]] = []
    for path in all_paths:
        exists = path.exists()
        text = read_text(path) if exists else ""
        routes = extract_route_decorators(path) if exists else []
        all_routes.extend(routes)
        domain_inventory.append({
            "path": rel(path, root),
            "exists": exists,
            "lines": line_count(text) if exists else 0,
            "route_count": len(routes),
        })
        if exists:
            compile_results.append(compile_file(path))
    rules = [item.get("rule") for item in all_routes if item.get("rule")]
    duplicates = sorted({rule for rule in rules if rules.count(rule) > 1})
    return {
        "routes_py_lines": line_count(read_text(routes_py)) if routes_py.exists() else 0,
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": len(all_routes),
        "route_rules_sample": rules[:50],
        "duplicate_route_rules": duplicates,
        "compile_results": compile_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    parser.add_argument("--run-pytest", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    reports_dir = root / "reports" / "architecture"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "BYS360_MOBILE_PYTEST_CONTRACT_GATE_P2A_V2_REPORT.json"

    changed: list[str] = []
    test_result = ensure_pytest_contract_file(root)
    if test_result.get("changed"):
        changed.append(rel(Path(test_result["path"]), root))

    inventory = build_inventory(root)
    test_path = Path(test_result["path"])
    compile_results = inventory["compile_results"] + [compile_file(test_path)]
    compile_ok = all(item.get("ok") for item in compile_results)

    env = dict(os.environ)
    env.setdefault("APP_ENV", "development")
    env.setdefault("FLASK_ENV", "development")
    env.setdefault("BYS360_DEV_SECRET_FALLBACK", "p2a-v2-smoke-only-not-for-production")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")

    app_factory = {"ok": None}
    if args.run_app_factory_smoke:
        app_factory = run_cmd(
            [sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"],
            cwd=root,
            env=env,
        )

    secret_gate: dict[str, Any] = {"ok": None, "parsed": {}}
    if args.run_secret_gate:
        gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
        if gate.exists():
            secret_gate = run_cmd([sys.executable, str(gate), "--project-root", str(root)], cwd=root, env=env)
            parsed = parse_last_json_object(str(secret_gate.get("stdout_tail", "")))
            secret_gate["parsed"] = parsed
            secret_gate["ok"] = bool(parsed.get("ok")) and int(parsed.get("finding_count", 9999)) == 0
        else:
            secret_gate = {"ok": False, "stderr_tail": "Secret gate script bulunamadi.", "parsed": {}}

    direct_contract = run_cmd([sys.executable, str(test_path)], cwd=root, env=env)
    direct_contract_ok = bool(direct_contract.get("ok")) and "P2A_MOBILE_CONTRACT_TEST_OK" in str(direct_contract.get("stdout_tail", ""))

    pytest_result: dict[str, Any] = {"ok": None, "mode": "not_requested"}
    if args.run_pytest:
        pytest_result = run_cmd([sys.executable, "-m", "pytest", str(test_path), "-q", "--tb=short"], cwd=root, env=env)
        pytest_result["mode"] = "pytest"
        if not pytest_result.get("ok"):
            combined = (str(pytest_result.get("stdout_tail", "")) + "\n" + str(pytest_result.get("stderr_tail", ""))).lower()
            if "no module named pytest" in combined or "pytest" in combined and "module" in combined and "not" in combined:
                pytest_result["mode"] = "fallback_internal_no_pytest"
                pytest_result["fallback_contract_ok"] = direct_contract_ok
                pytest_result["ok"] = direct_contract_ok
            else:
                pytest_result["fallback_contract_ok"] = direct_contract_ok

    expected_files_ok = all((root / path).exists() for path in EXPECTED_DOMAIN_FILES)
    checks = {
        "routes_py_under_300_lines": inventory["routes_py_lines"] <= 300,
        "expected_domain_files_exist": expected_files_ok,
        "total_mobile_route_decorator_count_expected": inventory["total_mobile_route_decorator_count"] == EXPECTED_ROUTE_COUNT,
        "no_duplicate_route_rules": not inventory["duplicate_route_rules"],
        "compile_ok": compile_ok,
        "direct_contract_ok": direct_contract_ok,
        "app_factory_ok": app_factory.get("ok") is not False,
        "secret_gate_ok": secret_gate.get("ok") is not False,
        "pytest_ok": pytest_result.get("ok") is not False,
    }
    ok = all(checks.values())

    report = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": args.mode,
        "changed_count": len(changed),
        "changed": changed,
        "pytest_contract_file": test_result,
        "inventory": inventory,
        "checks": checks,
        "compile_results": compile_results,
        "direct_contract_result": direct_contract,
        "app_factory_smoke": app_factory,
        "secret_gate": secret_gate,
        "pytest_result": pytest_result,
        "report": str(report_path),
        "next_actions": [
            "P2A V2 temizse mobil domain split zinciri pytest/contract kalite kapisina baglanmis kabul edilebilir.",
            "Pytest ortamda yoksa fallback_internal_no_pytest modu ayni sozlesme kontrollerini calistirir; CI tarafinda pytest kurulu olmalidir.",
            "P2B'de test_client ile auth/dashboard/personnel/kpi/communication/assistant davranissal smoke testleri eklenmelidir.",
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "ok": ok,
        "package": PACKAGE,
        "routes_py_lines": inventory["routes_py_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "changed_count": len(changed),
        "compile_ok": compile_ok,
        "direct_contract_ok": direct_contract_ok,
        "app_factory_ok": app_factory.get("ok"),
        "secret_gate_ok": secret_gate.get("ok"),
        "pytest_ok": pytest_result.get("ok"),
        "pytest_mode": pytest_result.get("mode"),
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
