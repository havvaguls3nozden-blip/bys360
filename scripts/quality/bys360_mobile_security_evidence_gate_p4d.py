#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BYS360 P4D Mobile Security Evidence Gate

P4C V2 mobile security suite raporunu devir/CI kanıtı olarak doğrular.
Canlı veriye yazmaz; sadece rapor, sözleşme, compile/app/secret/pytest kapılarını okur.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P4D_MOBILE_SECURITY_EVIDENCE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_SECURITY_EVIDENCE_GATE_P4D_REPORT.json")
P4C_REPORT_REL = Path("reports/architecture/BYS360_MOBILE_SECURITY_SUITE_GATE_P4C_V2_REPORT.json")
P4A_REPORT_REL = Path("reports/architecture/BYS360_MOBILE_AUTH_GUARD_MATRIX_GATE_P4A_REPORT.json")
P4B_REPORT_REL = Path("reports/architecture/BYS360_MOBILE_ROLE_BOUNDARY_MATRIX_GATE_P4B_V3_REPORT.json")
EXPECTED_FEATURES = [
    "assistant", "auth", "communication", "dashboard", "identity", "kpi",
    "notifications", "performance", "personnel", "support", "survey",
]
EXPECTED_SECURITY_GATE_COUNT = 2
MIN_TOTAL_PROBE_COUNT = 97
EXPECTED_CONTRACT_ROUTE_COUNT = 24
MAX_ROUTES_PY_LINES = 300
COMPILE_FILES = [
    "scripts/quality/bys360_mobile_security_evidence_gate_p4d.py",
    "tests/architecture/test_mobile_api_security_evidence_p4d.py",
    "tests/architecture/conftest.py",
    "scripts/quality/bys360_mobile_security_suite_gate_p4c_v2.py",
    "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py",
    "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
]


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"ok": False, "error": f"missing_report:{path}"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "error": f"invalid_json:{path}:{exc}"}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _run(cmd: List[str], cwd: Path, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(cmd, cwd=str(cwd), env=merged_env, text=True, capture_output=True)
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-6000:],
        "stderr_tail": proc.stderr[-6000:],
        "ok": proc.returncode == 0,
        "cmd": cmd,
    }


def _python_exe(root: Path) -> str:
    win_py = root / ".venv" / "Scripts" / "python.exe"
    return str(win_py) if win_py.exists() else sys.executable


def _count_routes_in_file(path: Path) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8", errors="ignore")
    return len(re.findall(r"@\s*mobile_api_bp\s*\.\s*(?:get|post|put|delete|patch)\s*\(", text))


def _inventory(root: Path) -> Dict[str, Any]:
    mobile_dir = root / "app" / "api" / "mobile"
    domains_dir = mobile_dir / "domains"
    routes_py = mobile_dir / "routes.py"
    routes_py_lines = len(routes_py.read_text(encoding="utf-8", errors="ignore").splitlines()) if routes_py.exists() else 0
    total = 0
    files: List[Path] = []
    if routes_py.exists():
        files.append(routes_py)
    if domains_dir.exists():
        files.extend(sorted(domains_dir.glob("*.py")))
    domain_inventory: List[Dict[str, Any]] = []
    for path in files:
        route_count = _count_routes_in_file(path)
        total += route_count
        domain_inventory.append({
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "exists": path.exists(),
            "route_count": route_count,
            "lines": len(path.read_text(encoding="utf-8", errors="ignore").splitlines()) if path.exists() else 0,
        })
    return {
        "routes_py_lines": routes_py_lines,
        "routes_py_under_300_lines": 0 < routes_py_lines <= MAX_ROUTES_PY_LINES,
        "routes_py_route_count": _count_routes_in_file(routes_py),
        "domains_dir_exists": domains_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": total,
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "route_contract_count_expected": total == EXPECTED_CONTRACT_ROUTE_COUNT,
    }


def _compile_all(root: Path, python: str) -> Tuple[bool, List[Dict[str, Any]]]:
    results: List[Dict[str, Any]] = []
    ok = True
    for rel in COMPILE_FILES:
        path = root / rel
        if not path.exists():
            results.append({"file": str(path), "ok": False, "error": "missing"})
            ok = False
            continue
        run = _run([python, "-m", "py_compile", str(path)], root)
        results.append({"file": str(path), "ok": run["ok"], "error": (run["stderr_tail"] or run["stdout_tail"])})
        ok = ok and bool(run["ok"])
    return ok, results


def _app_factory(root: Path, python: str) -> Dict[str, Any]:
    env = {
        "FLASK_ENV": "testing",
        "APP_ENV": "testing",
        "BYS360_TESTING": "1",
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "bys360-test-secret-key",
        "WTF_CSRF_ENABLED": "0",
    }
    return _run([python, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root, env)


def _secret_gate(root: Path, python: str) -> Dict[str, Any]:
    script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not script.exists():
        return {"ok": False, "returncode": 1, "stdout_tail": "", "stderr_tail": f"missing:{script}", "parsed": {}}
    result = _run([python, str(script), "--root", str(root)], root)
    parsed: Dict[str, Any] = {}
    try:
        text = result.get("stdout_tail", "")
        start = text.rfind("{")
        if start >= 0:
            parsed = json.loads(text[start:])
    except Exception:
        parsed = {}
    result["parsed"] = parsed
    result["ok"] = bool(result["ok"] and parsed.get("ok", True) and int(parsed.get("finding_count", 0)) == 0)
    return result


def _pytest_gate(root: Path, python: str) -> Dict[str, Any]:
    test_path = root / "tests" / "architecture" / "test_mobile_api_security_evidence_p4d.py"
    if not test_path.exists():
        return {"ok": False, "returncode": 1, "stdout_tail": "", "stderr_tail": f"missing:{test_path}", "mode": "pytest_targeted_mobile_security_evidence_p4d"}
    result = _run([python, "-m", "pytest", str(test_path.relative_to(root)), "-q"], root)
    result["mode"] = "pytest_targeted_mobile_security_evidence_p4d"
    return result


def _status_counts_from_suite(p4c: Dict[str, Any]) -> Dict[str, int]:
    status_counts: Dict[str, int] = {}
    for gate in p4c.get("security_suite", {}).get("gate_results", []):
        for status, count in gate.get("summary", {}).get("status_counts", {}).items():
            status_counts[str(status)] = status_counts.get(str(status), 0) + int(count)
    return status_counts


def _evidence(root: Path) -> Dict[str, Any]:
    p4c = _read_json(root / P4C_REPORT_REL)
    p4a = _read_json(root / P4A_REPORT_REL)
    p4b = _read_json(root / P4B_REPORT_REL)
    reports_exist_ok = all((root / rel).exists() for rel in [P4C_REPORT_REL, P4A_REPORT_REL, P4B_REPORT_REL])
    p4c_ok = bool(p4c.get("ok")) and bool(p4c.get("p4_security_suite_ok"))
    p4a_ok = bool(p4a.get("ok")) and bool(p4a.get("auth_guard_matrix_ok"))
    p4b_ok = bool(p4b.get("ok")) and bool(p4b.get("role_boundary_matrix_ok"))
    suite = p4c.get("security_suite", {}) if isinstance(p4c.get("security_suite"), dict) else {}
    coverage = suite.get("feature_coverage", {}) if isinstance(suite.get("feature_coverage"), dict) else {}
    observed = set(coverage.get("observed_features", []))
    missing = sorted(set(EXPECTED_FEATURES) - observed)
    total_probe_count = int(p4c.get("total_probe_count", suite.get("total_probe_count", 0)) or 0)
    gates_passed = int(p4c.get("security_gates_passed", suite.get("security_gates_passed", 0)) or 0)
    gate_count = int(p4c.get("security_gate_count", suite.get("security_gate_count", 0)) or 0)
    secret_counts = [
        int(p4c.get("secret_gate_finding_count", 0) or 0),
        int(p4a.get("secret_gate_finding_count", 0) or 0),
        int(p4b.get("secret_gate_finding_count", 0) or 0),
    ]
    status_counts = _status_counts_from_suite(p4c)
    evidence_ok = bool(
        reports_exist_ok and p4c_ok and p4a_ok and p4b_ok
        and gate_count == EXPECTED_SECURITY_GATE_COUNT
        and gates_passed == EXPECTED_SECURITY_GATE_COUNT
        and total_probe_count >= MIN_TOTAL_PROBE_COUNT
        and not missing
        and max(secret_counts) == 0
        and int(status_counts.get("401", 0)) >= 90
    )
    return {
        "ok": evidence_ok,
        "reports_exist_ok": reports_exist_ok,
        "security_suite_report_ok": p4c_ok,
        "p4a_report_ok": p4a_ok,
        "p4b_v3_report_ok": p4b_ok,
        "security_gate_count": gate_count,
        "security_gates_passed": gates_passed,
        "total_probe_count": total_probe_count,
        "min_total_probe_count": MIN_TOTAL_PROBE_COUNT,
        "probe_count_ok": total_probe_count >= MIN_TOTAL_PROBE_COUNT,
        "feature_coverage_ok": not missing,
        "expected_features": EXPECTED_FEATURES,
        "observed_features": sorted(observed),
        "missing_features": missing,
        "secret_finding_counts": secret_counts,
        "no_secret_findings_in_evidence_reports": max(secret_counts) == 0,
        "status_counts": status_counts,
        "status_distribution_ok": int(status_counts.get("401", 0)) >= 90,
        "source_reports": {
            "p4c_v2": str((root / P4C_REPORT_REL).resolve()),
            "p4a": str((root / P4A_REPORT_REL).resolve()),
            "p4b_v3": str((root / P4B_REPORT_REL).resolve()),
        },
    }


def build_report(root: Path, args: argparse.Namespace) -> Dict[str, Any]:
    python = _python_exe(root)
    inventory = _inventory(root)
    evidence = _evidence(root)

    compile_ok = True
    compile_results: List[Dict[str, Any]] = []
    if args.compile_all:
        compile_ok, compile_results = _compile_all(root, python)

    app_factory = {"ok": True}
    if args.app_factory:
        app_factory = _app_factory(root, python)

    secret_gate = {"ok": True, "parsed": {"finding_count": 0}}
    if args.secret_gate:
        secret_gate = _secret_gate(root, python)

    pytest = {"ok": True, "mode": "not_requested"}
    if args.pytest_gate:
        pytest = _pytest_gate(root, python)

    direct_contract_ok = bool(inventory["route_contract_count_expected"] and inventory["routes_py_under_300_lines"])
    ok = bool(evidence["ok"] and direct_contract_ok and compile_ok and app_factory.get("ok") and secret_gate.get("ok") and pytest.get("ok"))
    report: Dict[str, Any] = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "security_evidence_gate_ok": evidence["ok"],
        "handover_evidence_ok": evidence["ok"],
        "reports_exist_ok": evidence["reports_exist_ok"],
        "security_suite_report_ok": evidence["security_suite_report_ok"],
        "p4a_report_ok": evidence["p4a_report_ok"],
        "p4b_v3_report_ok": evidence["p4b_v3_report_ok"],
        "security_gate_count": evidence["security_gate_count"],
        "security_gates_passed": evidence["security_gates_passed"],
        "total_probe_count": evidence["total_probe_count"],
        "probe_count_ok": evidence["probe_count_ok"],
        "feature_coverage_ok": evidence["feature_coverage_ok"],
        "no_secret_findings_in_evidence_reports": evidence["no_secret_findings_in_evidence_reports"],
        "routes_py_lines": inventory["routes_py_lines"],
        "routes_py_under_300_lines": inventory["routes_py_under_300_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "direct_contract_ok": direct_contract_ok,
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_factory.get("ok")),
        "secret_gate_ok": bool(secret_gate.get("ok")),
        "secret_gate_finding_count": int(secret_gate.get("parsed", {}).get("finding_count", 0) or 0),
        "pytest_ok": bool(pytest.get("ok")),
        "pytest_mode": pytest.get("mode"),
        "inventory": inventory,
        "security_evidence": evidence,
        "compile_results": compile_results,
        "app_factory_smoke": app_factory,
        "secret_gate": secret_gate,
        "pytest": pytest,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_mobile_security_evidence_gate_p4d.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str((root / REPORT_REL).resolve()),
        "next_actions": [
            "P4D temizse P4 mobil guvenlik kanitlari CI/devir standardi olarak kilitlenmis kabul edilebilir.",
            "P4E'de istenirse fixture tabanli imzali test tokeniyle pozitif/negatif rol senaryolari tasarlanabilir.",
        ],
    }
    return report


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest-gate", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = build_report(root, args)
    _write_json(root / REPORT_REL, report)
    print(json.dumps({
        "ok": report["ok"],
        "package": PACKAGE,
        "security_evidence_gate_ok": report["security_evidence_gate_ok"],
        "handover_evidence_ok": report["handover_evidence_ok"],
        "security_gate_count": report["security_gate_count"],
        "security_gates_passed": report["security_gates_passed"],
        "total_probe_count": report["total_probe_count"],
        "feature_coverage_ok": report["feature_coverage_ok"],
        "direct_contract_ok": report["direct_contract_ok"],
        "compile_ok": report["compile_ok"],
        "app_factory_ok": report["app_factory_ok"],
        "secret_gate_ok": report["secret_gate_ok"],
        "secret_gate_finding_count": report["secret_gate_finding_count"],
        "pytest_ok": report["pytest_ok"],
        "pytest_mode": report["pytest_mode"],
        "report": report["report"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
