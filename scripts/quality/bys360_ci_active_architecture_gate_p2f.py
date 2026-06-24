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

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P2F_CI_ACTIVE_ARCHITECTURE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_CI_ACTIVE_ARCHITECTURE_GATE_P2F_REPORT.json")

ACTIVE_ARCH_TESTS = [
    Path("tests/architecture/test_architecture_scope_p2e.py"),
    Path("tests/architecture/test_mobile_api_contract_p2a.py"),
    Path("tests/architecture/test_mobile_api_behavior_smoke_p2b.py"),
    Path("tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py"),
    Path("tests/architecture/test_pytest_standard_p2d.py"),
]

COMPILE_TARGETS = [
    Path("scripts/quality/bys360_ci_active_architecture_gate_p2f.py"),
    Path("scripts/quality/bys360_architecture_scope_gate_p2e.py"),
    Path("scripts/quality/bys360_mobile_behavior_smoke_p2b.py"),
    Path("scripts/quality/bys360_mobile_pytest_contract_gate_p2a_v3.py"),
    Path("scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py"),
    Path("tests/architecture/conftest.py"),
    *ACTIVE_ARCH_TESTS,
]


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _tail(value: str, limit: int = 5000) -> str:
    if not value:
        return ""
    return value[-limit:]


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 180) -> dict[str, Any]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=merged_env,
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
    matches = list(re.finditer(r"\{", text))
    for match in reversed(matches):
        fragment = text[match.start():].strip()
        try:
            parsed = json.loads(fragment)
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
    except Exception as exc:  # noqa: BLE001 - gate report should capture exact compile failure
        return {"file": str(path), "ok": False, "error": str(exc)}


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def _count_route_decorators(root: Path) -> int:
    mobile_dir = root / "app" / "api" / "mobile"
    if not mobile_dir.exists():
        return 0
    total = 0
    paths = [mobile_dir / "routes.py"]
    domains_dir = mobile_dir / "domains"
    if domains_dir.exists():
        paths.extend(sorted(domains_dir.glob("*.py")))
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        total += text.count("@mobile_api_bp.")
    return total


def _pytest_is_installed(root: Path) -> bool:
    cmd = [sys.executable, "-c", "import pytest; print(pytest.__version__)"]
    result = _run(cmd, cwd=root, timeout=60)
    return bool(result.get("ok"))


def run_gate(
    root: Path,
    mode: str,
    compile_all: bool,
    run_app_factory: bool,
    run_secret_gate: bool,
    run_pytest: bool,
) -> dict[str, Any]:
    root = root.resolve()
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)

    routes_py = root / "app" / "api" / "mobile" / "routes.py"
    pytest_installed = _pytest_is_installed(root)

    compile_results: list[dict[str, Any]] = []
    if compile_all:
        for rel in COMPILE_TARGETS:
            compile_results.append(_compile_file(root / rel))
    compile_ok = all(item.get("ok") for item in compile_results) if compile_results else True

    smoke_env = {
        "APP_ENV": "testing",
        "FLASK_ENV": "testing",
        "BYS360_TESTING": "1",
        "DATABASE_URL": os.environ.get("DATABASE_URL", "sqlite:///:memory:"),
        "SECRET_KEY": os.environ.get("SECRET_KEY", "bys360-ci-active-architecture-smoke-key"),
        "SENTRY_DSN": os.environ.get("SENTRY_DSN", ""),
    }

    app_factory_result = {"ok": True, "skipped": True}
    if run_app_factory:
        app_factory_result = _run(
            [sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"],
            cwd=root,
            env=smoke_env,
            timeout=180,
        )
    app_factory_ok = bool(app_factory_result.get("ok"))

    secret_gate_result: dict[str, Any] = {"ok": True, "skipped": True, "parsed": {}}
    if run_secret_gate:
        secret_script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
        if secret_script.exists():
            secret_gate_result = _run([sys.executable, str(secret_script), "--root", str(root)], cwd=root, timeout=180)
            parsed = _parse_last_json(secret_gate_result.get("stdout_tail", ""))
            secret_gate_result["parsed"] = parsed
            secret_gate_result["ok"] = bool(parsed.get("ok", secret_gate_result.get("ok"))) and int(parsed.get("finding_count", 0) or 0) == 0
        else:
            secret_gate_result = {"ok": False, "error": "missing scripts/quality/bys360_secret_repo_gate.py", "parsed": {}}
    secret_gate_ok = bool(secret_gate_result.get("ok"))
    secret_gate_finding_count = int(secret_gate_result.get("parsed", {}).get("finding_count", 0) or 0)

    pytest_result: dict[str, Any] = {"ok": True, "skipped": True, "mode": "not_requested"}
    if run_pytest:
        if pytest_installed:
            pytest_result = _run([sys.executable, "-m", "pytest", "tests/architecture", "-q"], cwd=root, env=smoke_env, timeout=240)
            pytest_result["mode"] = "active_architecture_scope"
        else:
            pytest_result = {
                "ok": False,
                "mode": "pytest_missing",
                "returncode": 1,
                "stdout_tail": "",
                "stderr_tail": "pytest is not installed; run python -m pip install -r requirements-dev.txt",
            }
    pytest_ok = bool(pytest_result.get("ok"))

    active_tests_missing = [str(path) for path in ACTIVE_ARCH_TESTS if not (root / path).exists()]
    active_architecture_scope_ok = not active_tests_missing
    total_route_count = _count_route_decorators(root)
    routes_py_lines = _line_count(routes_py)

    result: dict[str, Any] = {
        "ok": bool(compile_ok and app_factory_ok and secret_gate_ok and pytest_ok and active_architecture_scope_ok),
        "package": PACKAGE,
        "generated_at": _now(),
        "root": str(root),
        "mode": mode,
        "active_architecture_scope_ok": active_architecture_scope_ok,
        "active_architecture_test_count": len(ACTIVE_ARCH_TESTS),
        "active_architecture_tests_missing": active_tests_missing,
        "routes_py_lines": routes_py_lines,
        "routes_py_under_300_lines": routes_py_lines <= 300,
        "total_mobile_route_decorator_count": total_route_count,
        "expected_contract_route_count": 24,
        "route_contract_count_expected": total_route_count == 24,
        "pytest_installed": pytest_installed,
        "compile_ok": compile_ok,
        "compile_results": compile_results,
        "app_factory_ok": app_factory_ok,
        "app_factory_smoke": app_factory_result,
        "secret_gate_ok": secret_gate_ok,
        "secret_gate_finding_count": secret_gate_finding_count,
        "secret_gate": secret_gate_result,
        "pytest_ok": pytest_ok,
        "pytest_mode": pytest_result.get("mode"),
        "pytest": pytest_result,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_secret_repo_gate.py --root .",
            "python -c \"from app import create_app; app=create_app(); print('APP_FACTORY_OK')\"",
        ],
        "report": str(report_path),
        "next_actions": [
            "P2F temizse aktif mimari, pytest, app factory smoke ve secret gate tek CI kapisi altinda standartlasmis kabul edilebilir.",
            "Eski mimari sozlesme testleri BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1 ile ayrica incelenebilir.",
            "P3 asamasinda mobil API request-level testleri davranissal veri senaryolariyla genisletilebilir.",
        ],
    }
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 P2F active architecture CI gate")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    parser.add_argument("--run-pytest", action="store_true")
    args = parser.parse_args()

    result = run_gate(
        root=Path(args.root),
        mode=args.mode,
        compile_all=args.compile_all,
        run_app_factory=args.run_app_factory_smoke,
        run_secret_gate=args.run_secret_gate,
        run_pytest=args.run_pytest,
    )
    summary = {
        "ok": result["ok"],
        "package": result["package"],
        "active_architecture_scope_ok": result["active_architecture_scope_ok"],
        "routes_py_lines": result["routes_py_lines"],
        "total_mobile_route_decorator_count": result["total_mobile_route_decorator_count"],
        "compile_ok": result["compile_ok"],
        "app_factory_ok": result["app_factory_ok"],
        "secret_gate_ok": result["secret_gate_ok"],
        "secret_gate_finding_count": result["secret_gate_finding_count"],
        "pytest_ok": result["pytest_ok"],
        "pytest_mode": result.get("pytest_mode"),
        "report": result["report"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
