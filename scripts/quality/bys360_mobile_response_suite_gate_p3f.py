from __future__ import annotations

import argparse
import importlib
import json
import os
import py_compile
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P3F_MOBILE_RESPONSE_SUITE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_RESPONSE_SUITE_GATE_P3F_REPORT.json")
TEST_NAME = "test_mobile_api_response_suite_p3f.py"
EXPECTED_CONTRACT_ROUTE_COUNT = 24

P3_GATES = [
    {
        "key": "p3a_request_scenarios",
        "label": "P3A Mobile Request Scenario Gate",
        "module": "scripts.quality.bys360_mobile_request_scenario_gate_p3a",
        "mode": "p3a",
        "script": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
        "test": "tests/architecture/test_mobile_api_request_scenarios_p3a.py",
        "features": ["all_mobile_contract_routes", "runtime_route_map"],
    },
    {
        "key": "p3b_auth_dashboard_assistant",
        "label": "P3B Auth/Dashboard/Assistant Response Gate V3",
        "module": "scripts.quality.bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3",
        "mode": "p3b_v3",
        "script": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
        "test": "tests/architecture/test_mobile_api_auth_dashboard_assistant_response_p3b_v3.py",
        "features": ["auth", "dashboard", "assistant"],
    },
    {
        "key": "p3c_personnel_kpi_communication",
        "label": "P3C Personnel/KPI/Communication Response Gate V2",
        "module": "scripts.quality.bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2",
        "mode": "p3c_v2",
        "script": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
        "test": "tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py",
        "features": ["personnel", "kpi", "communication"],
    },
    {
        "key": "p3d_support_survey_notifications",
        "label": "P3D Support/Survey/Notifications Response Gate",
        "module": "scripts.quality.bys360_mobile_support_survey_notifications_response_gate_p3d",
        "mode": "p3d",
        "script": "scripts/quality/bys360_mobile_support_survey_notifications_response_gate_p3d.py",
        "test": "tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py",
        "features": ["support", "survey", "notifications"],
    },
    {
        "key": "p3e_performance",
        "label": "P3E Performance Response Gate",
        "module": "scripts.quality.bys360_mobile_performance_response_gate_p3e",
        "mode": "p3e",
        "script": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
        "test": "tests/architecture/test_mobile_api_performance_response_p3e.py",
        "features": ["performance"],
    },
]

COMPILE_RELS = [
    "scripts/quality/bys360_mobile_response_suite_gate_p3f.py",
    "tests/architecture/test_mobile_api_response_suite_p3f.py",
    "tests/architecture/conftest.py",
    *[gate["script"] for gate in P3_GATES],
    *[gate["test"] for gate in P3_GATES],
]


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _tail(text: str, limit: int = 5000) -> str:
    return (text or "")[-limit:]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _prepare_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("APP_ENV", "testing")
    env.setdefault("FLASK_ENV", "testing")
    env.setdefault("TESTING", "1")
    env.setdefault("BYS360_TESTING", "1")
    env.setdefault("SECRET_KEY", "bys360-p3f-mobile-response-suite-test-key")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("WTF_CSRF_ENABLED", "0")
    env.setdefault("SENTRY_DSN", "")
    return env


def _run(cmd: list[str], root: Path, timeout: int = 240) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(root),
        env=_prepare_env(),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "returncode": proc.returncode,
        "stdout_tail": _tail(proc.stdout),
        "stderr_tail": _tail(proc.stderr),
        "ok": proc.returncode == 0,
        "cmd": cmd,
    }


def _parse_last_json(text: str) -> dict[str, Any]:
    if not text:
        return {}
    for idx in range(len(text) - 1, -1, -1):
        if text[idx] != "{":
            continue
        try:
            parsed = json.loads(text[idx:].strip())
        except Exception:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def _compile_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"file": str(path), "ok": False, "error": "missing"}
    try:
        py_compile.compile(str(path), doraise=True)
        return {"file": str(path), "ok": True, "error": ""}
    except Exception as exc:  # noqa: BLE001 - gate report should capture exact failure
        return {"file": str(path), "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _line_count(path: Path) -> int:
    return len(_read(path).splitlines()) if path.exists() else 0


def _count_route_decorators(root: Path) -> int:
    mobile_dir = root / "app" / "api" / "mobile"
    if not mobile_dir.exists():
        return 0
    paths = [mobile_dir / "routes.py"]
    domains_dir = mobile_dir / "domains"
    if domains_dir.exists():
        paths.extend(sorted(domains_dir.glob("*.py")))
    return sum(_read(path).count("@mobile_api_bp.") for path in paths)


def ensure_active_scope(root: Path) -> dict[str, Any]:
    conftest = root / "tests" / "architecture" / "conftest.py"
    conftest.parent.mkdir(parents=True, exist_ok=True)
    if not conftest.exists():
        conftest.write_text("", encoding="utf-8")
    text = _read(conftest)
    if TEST_NAME in text:
        return {"path": str(conftest), "changed": False, "reason": "already_present"}
    marker = "# BYS360_P3F_ACTIVE_SCOPE_MARKER"
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


def app_factory_smoke(root: Path) -> dict[str, Any]:
    return _run([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root, timeout=180)


def secret_gate(root: Path) -> dict[str, Any]:
    script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not script.exists():
        return {"ok": False, "error": "missing scripts/quality/bys360_secret_repo_gate.py", "parsed": {}}
    result = _run([sys.executable, str(script), "--root", str(root)], root, timeout=180)
    parsed = _parse_last_json(result.get("stdout_tail", ""))
    result["parsed"] = parsed
    result["ok"] = bool(parsed.get("ok", result.get("ok"))) and int(parsed.get("finding_count", 0) or 0) == 0
    return result


def _call_gate(root: Path, gate: dict[str, Any]) -> dict[str, Any]:
    missing = [rel for rel in (gate["script"], gate["test"]) if not (root / rel).exists()]
    if missing:
        return {"ok": False, "label": gate["label"], "mode": gate["mode"], "missing": missing, "error": "gate files missing"}
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    try:
        module = importlib.import_module(gate["module"])
        run_checks: Callable[..., dict[str, Any]] = getattr(module, "run_checks")
        mode = gate["mode"]
        if mode == "p3a":
            result = run_checks(root, False, False, False, False, write_report=False)
        elif mode == "p3b_v3":
            result = run_checks(root, compile_all=False, app_factory=False, secret_gate_enabled=False, pytest_gate_enabled=False, write_report=False)
        elif mode == "p3c_v2":
            result = run_checks(root, compile_all=False, app_factory=False, secret_gate=False, pytest_gate=False, write_report=False)
        else:
            result = run_checks(root, compile_all=False, app_factory=False, secret_gate_run=False, pytest_gate=False, write_report=False)
        return {
            "ok": bool(result.get("ok")),
            "label": gate["label"],
            "mode": mode,
            "features": gate.get("features", []),
            "direct_contract_ok": result.get("direct_contract_ok"),
            "request_scenario_ok": result.get("request_scenario_ok"),
            "runtime_route_map_ok": result.get("runtime_route_map_ok"),
            "response_code_smoke_ok": result.get("response_code_smoke_ok"),
            "routes_py_lines": result.get("routes_py_lines"),
            "total_mobile_route_decorator_count": result.get("total_mobile_route_decorator_count"),
            "report": result.get("report"),
        }
    except Exception as exc:  # noqa: BLE001 - gate report should capture exact failure
        return {
            "ok": False,
            "label": gate["label"],
            "mode": gate["mode"],
            "features": gate.get("features", []),
            "error": f"{type(exc).__name__}: {exc}",
        }


def run_pytest(root: Path) -> dict[str, Any]:
    test = root / "tests" / "architecture" / TEST_NAME
    if not test.exists():
        return {"ok": False, "mode": "pytest_targeted_mobile_response_suite_p3f", "error": f"missing {TEST_NAME}"}
    result = _run([sys.executable, "-m", "pytest", f"tests/architecture/{TEST_NAME}", "-q"], root, timeout=240)
    result["mode"] = "pytest_targeted_mobile_response_suite_p3f"
    return result


def run_checks(
    root: str | Path,
    *,
    compile_all: bool = False,
    app_factory: bool = False,
    secret_gate_run: bool = False,
    pytest_gate: bool = False,
    write_report: bool = True,
) -> dict[str, Any]:
    root = Path(root).resolve()
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)

    active_scope = ensure_active_scope(root)
    routes_py = root / "app" / "api" / "mobile" / "routes.py"
    routes_py_lines = _line_count(routes_py)
    total_mobile_route_decorator_count = _count_route_decorators(root)

    compile_results = [_compile_file(root / rel) for rel in COMPILE_RELS] if compile_all else []
    compile_ok = all(item.get("ok") for item in compile_results) if compile_all else True

    gate_results = [_call_gate(root, gate) for gate in P3_GATES]
    suite_ok = all(item.get("ok") for item in gate_results)

    app_result = app_factory_smoke(root) if app_factory else {"ok": True, "skipped": True}
    secret_result = secret_gate(root) if secret_gate_run else {"ok": True, "skipped": True, "parsed": {"finding_count": 0}}
    pytest_result = run_pytest(root) if pytest_gate else {"ok": True, "mode": "not_requested"}

    feature_coverage: dict[str, bool] = {}
    for gate, result in zip(P3_GATES, gate_results, strict=False):
        for feature in gate.get("features", []):
            feature_coverage[feature] = bool(result.get("ok"))

    result: dict[str, Any] = {
        "ok": bool(suite_ok and compile_ok and app_result.get("ok") and secret_result.get("ok") and pytest_result.get("ok")),
        "package": PACKAGE,
        "generated_at": _now(),
        "root": str(root),
        "active_scope": active_scope,
        "routes_py_lines": routes_py_lines,
        "routes_py_under_300_lines": routes_py_lines <= 300,
        "total_mobile_route_decorator_count": total_mobile_route_decorator_count,
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "route_contract_count_expected": total_mobile_route_decorator_count == EXPECTED_CONTRACT_ROUTE_COUNT,
        "p3_suite_ok": suite_ok,
        "p3_gate_count": len(P3_GATES),
        "p3_gates_passed": sum(1 for item in gate_results if item.get("ok")),
        "feature_coverage": feature_coverage,
        "gate_results": gate_results,
        "compile_ok": compile_ok,
        "compile_results": compile_results,
        "app_factory_ok": bool(app_result.get("ok")),
        "app_factory_smoke": app_result,
        "secret_gate_ok": bool(secret_result.get("ok")),
        "secret_gate_finding_count": int(secret_result.get("parsed", {}).get("finding_count", 0) or 0),
        "secret_gate": secret_result,
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode"),
        "pytest": pytest_result,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_mobile_response_suite_gate_p3f.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str(report_path),
        "next_actions": [
            "P3F temizse P3A-P3E mobil response kapilari tek suite runner altinda standart kabul edilebilir.",
            "P4 asamasinda mobil response suite icin oturumlu/rol bazli test kullanicisi senaryolari eklenebilir.",
        ],
    }
    if write_report:
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest-gate", action="store_true")
    args = parser.parse_args(argv)

    result = run_checks(
        args.root,
        compile_all=args.compile_all or args.mode == "all",
        app_factory=args.app_factory or args.mode == "all",
        secret_gate_run=args.secret_gate or args.mode == "all",
        pytest_gate=args.pytest_gate or args.mode == "all",
        write_report=True,
    )
    print(json.dumps({
        "ok": result["ok"],
        "package": result["package"],
        "p3_suite_ok": result["p3_suite_ok"],
        "p3_gate_count": result["p3_gate_count"],
        "p3_gates_passed": result["p3_gates_passed"],
        "routes_py_lines": result["routes_py_lines"],
        "total_mobile_route_decorator_count": result["total_mobile_route_decorator_count"],
        "compile_ok": result["compile_ok"],
        "app_factory_ok": result["app_factory_ok"],
        "secret_gate_ok": result["secret_gate_ok"],
        "secret_gate_finding_count": result["secret_gate_finding_count"],
        "pytest_ok": result["pytest_ok"],
        "pytest_mode": result["pytest_mode"],
        "report": result["report"],
    }, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
