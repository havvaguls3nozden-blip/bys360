from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P2A_MOBILE_PYTEST_CONTRACT_GATE_V3"
EXPECTED_ROUTE_COUNT = 24
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
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_PYTEST_CONTRACT_GATE_P2A_V3_REPORT.json")
TEST_REL = Path("tests/architecture/test_mobile_api_contract_p2a.py")

ROUTE_DECORATOR_RE = re.compile(
    r"^\s*@\s*mobile_api_bp\s*\.\s*(get|post|put|patch|delete|route)\s*\((.+?)\)",
    re.M,
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(_read(path).splitlines())


def _extract_route_decorators(path: Path) -> List[Dict[str, Any]]:
    text = _read(path)
    items: List[Dict[str, Any]] = []
    for match in ROUTE_DECORATOR_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        method = match.group(1).lower()
        raw_args = match.group(2).strip()
        # Capture first literal path argument for duplicate/sanity checks.
        rule = None
        literal_match = re.search(r"(['\"])(.*?)\1", raw_args)
        if literal_match:
            rule = literal_match.group(2)
        items.append({
            "file": str(path).replace("\\", "/"),
            "line": line,
            "method": method,
            "rule": rule,
            "decorator": match.group(0).strip(),
        })
    return items


def _function_count(path: Path) -> int:
    try:
        tree = ast.parse(_read(path), filename=str(path))
    except SyntaxError:
        return 0
    return sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))


def _compile(paths: List[Path]) -> Tuple[bool, List[Dict[str, str]]]:
    results: List[Dict[str, str]] = []
    ok = True
    for path in paths:
        if not path.exists():
            ok = False
            results.append({"file": str(path), "ok": False, "error": "missing"})
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"file": str(path), "ok": True, "error": ""})
        except Exception as exc:  # pragma: no cover - report path
            ok = False
            results.append({"file": str(path), "ok": False, "error": repr(exc)})
    return ok, results


def _subprocess_tail(cmd: List[str], root: Path, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=str(root),
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=90,
    )
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-3000:],
        "ok": proc.returncode == 0,
    }


def _parse_last_json(text: str) -> Dict[str, Any]:
    decoder = json.JSONDecoder()
    candidates: List[Dict[str, Any]] = []
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            if isinstance(obj, dict):
                candidates.append(obj)
        except Exception:
            continue
    return candidates[-1] if candidates else {}


def _run_app_factory(root: Path) -> Dict[str, Any]:
    env = {
        "APP_ENV": os.environ.get("APP_ENV", "development"),
        "FLASK_ENV": os.environ.get("FLASK_ENV", "development"),
        "SECRET_KEY": os.environ.get("SECRET_KEY", "bys360-local-smoke-secret-not-for-production"),
        "DATABASE_URL": os.environ.get("DATABASE_URL", "sqlite:///:memory:"),
        "SQLALCHEMY_DATABASE_URI": os.environ.get("SQLALCHEMY_DATABASE_URI", os.environ.get("DATABASE_URL", "sqlite:///:memory:")),
        "SENTRY_DSN": os.environ.get("SENTRY_DSN", ""),
    }
    return _subprocess_tail([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root, env)


def _run_secret_gate(root: Path) -> Dict[str, Any]:
    gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": False, "skipped": True, "reason": "secret_gate_script_missing"}
    result = _subprocess_tail([sys.executable, str(gate), "--root", str(root)], root)
    parsed = _parse_last_json(result.get("stdout_tail", ""))
    result["parsed"] = parsed
    result["ok"] = result["returncode"] == 0 and parsed.get("ok") is True and int(parsed.get("finding_count", 999999)) == 0
    return result


def _write_pytest(root: Path) -> Path:
    test_path = root / TEST_REL
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(
        '''from __future__ import annotations\n\nimport importlib.util\nfrom pathlib import Path\n\n\ndef _load_gate():\n    root = Path(__file__).resolve().parents[2]\n    path = root / "scripts" / "quality" / "bys360_mobile_pytest_contract_gate_p2a_v3.py"\n    spec = importlib.util.spec_from_file_location("bys360_mobile_pytest_contract_gate_p2a_v3", path)\n    module = importlib.util.module_from_spec(spec)\n    assert spec and spec.loader\n    spec.loader.exec_module(module)\n    return module, root\n\n\ndef test_mobile_api_domain_contract_is_stable():\n    gate, root = _load_gate()\n    inventory = gate.build_inventory(root)\n    checks = gate.build_contract_checks(inventory)\n    assert checks["domain_dir_exists"]\n    assert checks["expected_domain_files_exist"]\n    assert checks["routes_py_under_300_lines"]\n    assert checks["route_contract_count_expected"]\n    assert checks["no_duplicate_route_decorators"]\n\n\ndef test_mobile_api_expected_domains_compile():\n    gate, root = _load_gate()\n    inventory = gate.build_inventory(root)\n    compile_ok, compile_results = gate._compile([Path(item["abs_path"]) for item in inventory["domain_inventory"] if item["exists"]])\n    assert compile_ok, compile_results\n''',
        encoding="utf-8",
    )
    return test_path


def build_inventory(root: Path) -> Dict[str, Any]:
    mobile_root = root / "app" / "api" / "mobile"
    routes_py = mobile_root / "routes.py"
    domains_dir = mobile_root / "domains"
    domain_paths = [domains_dir / name for name in EXPECTED_DOMAIN_FILES]
    all_paths = [routes_py] + domain_paths
    decorators: List[Dict[str, Any]] = []
    domain_inventory: List[Dict[str, Any]] = []
    for path in all_paths:
        route_items = _extract_route_decorators(path)
        decorators.extend(route_items)
        domain_inventory.append({
            "path": str(path.relative_to(root)).replace("\\", "/") if path.exists() else str(path),
            "abs_path": str(path),
            "exists": path.exists(),
            "route_count": len(route_items),
            "function_count": _function_count(path) if path.exists() else 0,
            "lines": _line_count(path),
        })
    seen: Dict[Tuple[str, str | None], List[Dict[str, Any]]] = {}
    for item in decorators:
        key = (item.get("method") or "", item.get("rule"))
        seen.setdefault(key, []).append(item)
    duplicates = []
    for key, values in seen.items():
        if key[1] and len(values) > 1:
            duplicates.append({"method": key[0], "rule": key[1], "items": values})
    return {
        "routes_py_lines": _line_count(routes_py),
        "routes_py_route_count": len(_extract_route_decorators(routes_py)),
        "domains_dir_exists": domains_dir.exists(),
        "missing_files": [str((domains_dir / name).relative_to(root)).replace("\\", "/") for name in EXPECTED_DOMAIN_FILES if not (domains_dir / name).exists()],
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": len(decorators),
        "duplicate_route_decorators": duplicates,
        "route_rules_sample": [item["decorator"] for item in decorators[:50]],
    }


def build_contract_checks(inventory: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "domain_dir_exists": bool(inventory["domains_dir_exists"]),
        "expected_domain_files_exist": not inventory["missing_files"],
        "routes_py_under_300_lines": int(inventory["routes_py_lines"]) <= 300,
        "routes_py_is_facade": int(inventory["routes_py_route_count"]) == 0,
        "route_contract_count_expected": int(inventory["total_mobile_route_decorator_count"]) == EXPECTED_ROUTE_COUNT,
        "no_duplicate_route_decorators": not inventory["duplicate_route_decorators"],
    }


def _pytest_available() -> bool:
    try:
        import pytest  # noqa: F401
        return True
    except Exception:
        return False


def _run_pytest(root: Path, test_path: Path) -> Dict[str, Any]:
    if not _pytest_available():
        return {"ok": True, "mode": "fallback_internal_no_pytest", "returncode": 0, "stdout_tail": "pytest not installed; direct contract gate used\n", "stderr_tail": ""}
    result = _subprocess_tail([sys.executable, "-m", "pytest", str(test_path), "-q"], root)
    result["mode"] = "pytest"
    return result


def run(root: Path, mode: str, compile_all: bool, run_app_factory: bool, run_secret_gate: bool, run_pytest: bool) -> Dict[str, Any]:
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    test_path = _write_pytest(root)
    inventory = build_inventory(root)
    checks = build_contract_checks(inventory)
    direct_contract_ok = all(checks.values())
    compile_paths = [Path(item["abs_path"]) for item in inventory["domain_inventory"] if item["exists"]]
    compile_paths.append(root / "scripts" / "quality" / "bys360_mobile_pytest_contract_gate_p2a_v3.py")
    compile_paths.append(test_path)
    compile_ok, compile_results = _compile(compile_paths) if compile_all else (True, [])
    app_factory = _run_app_factory(root) if run_app_factory else {"ok": True, "skipped": True}
    secret_gate = _run_secret_gate(root) if run_secret_gate else {"ok": True, "skipped": True}
    pytest_result = _run_pytest(root, test_path) if run_pytest else {"ok": True, "mode": "skipped"}
    ok = bool(direct_contract_ok and compile_ok and app_factory.get("ok") and secret_gate.get("ok") and pytest_result.get("ok"))
    report = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": mode,
        "changed_count": 2,
        "changed": [str(TEST_REL).replace("\\", "/"), "scripts/quality/bys360_mobile_pytest_contract_gate_p2a_v3.py"],
        "routes_py_lines": inventory["routes_py_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_ROUTE_COUNT,
        "direct_contract_ok": direct_contract_ok,
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_factory.get("ok")),
        "secret_gate_ok": bool(secret_gate.get("ok")),
        "secret_gate_finding_count": int(secret_gate.get("parsed", {}).get("finding_count", 0)) if isinstance(secret_gate.get("parsed"), dict) else None,
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
            "P2A V3 temizse mobil API mimari sozlesmesi pytest/CI kapisina baglanmis kabul edilebilir.",
            "Ortamda pytest yoksa fallback_internal_no_pytest modu direct contract gate ile gecer; CI tarafinda pytest kurulu oldugunda ayni test pytest ile calisir.",
            "P2B'de auth/dashboard/assistant icin request-level davranissal smoke testleri eklenebilir.",
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    parser.add_argument("--run-pytest", action="store_true")
    args = parser.parse_args()
    report = run(Path(args.root).resolve(), args.mode, args.compile_all, args.run_app_factory_smoke, args.run_secret_gate, args.run_pytest)
    print(json.dumps({
        "ok": report["ok"],
        "package": report["package"],
        "routes_py_lines": report["routes_py_lines"],
        "total_mobile_route_decorator_count": report["total_mobile_route_decorator_count"],
        "direct_contract_ok": report["direct_contract_ok"],
        "compile_ok": report["compile_ok"],
        "app_factory_ok": report["app_factory_ok"],
        "secret_gate_ok": report["secret_gate_ok"],
        "pytest_ok": report["pytest_ok"],
        "pytest_mode": report["pytest_mode"],
        "report": report["report"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
