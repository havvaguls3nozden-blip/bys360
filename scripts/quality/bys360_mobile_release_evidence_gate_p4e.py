# -*- coding: utf-8 -*-
"""BYS360 P4E Mobile Release Evidence Gate.

Combines P3 mobile response-suite evidence and P4 mobile security evidence into
one CI/handover-ready release evidence gate. The gate is read-only: it reads
existing reports and performs static/runtime-safe checks only.
"""
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
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P4E_MOBILE_RELEASE_EVIDENCE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_RELEASE_EVIDENCE_GATE_P4E_REPORT.json")
P3F_REPORT_REL = Path("reports/architecture/BYS360_MOBILE_RESPONSE_SUITE_GATE_P3F_REPORT.json")
P4D_REPORT_REL = Path("reports/architecture/BYS360_MOBILE_SECURITY_EVIDENCE_GATE_P4D_REPORT.json")
P4C_REPORT_REL = Path("reports/architecture/BYS360_MOBILE_SECURITY_SUITE_GATE_P4C_V2_REPORT.json")
SECRET_REPORT_REL = Path("reports/quality/BYS360_SECRET_REPO_GATE_V1_REPORT.json")
EXPECTED_CONTRACT_ROUTE_COUNT = 24
MIN_TOTAL_SECURITY_PROBE_COUNT = 97
EXPECTED_P3_GATE_COUNT = 5
EXPECTED_SECURITY_GATE_COUNT = 2
EXPECTED_FEATURES = {
    "auth",
    "identity",
    "dashboard",
    "assistant",
    "personnel",
    "kpi",
    "communication",
    "support",
    "survey",
    "notifications",
    "performance",
}

ROUTE_DECORATOR_RE = re.compile(r"@\s*mobile_api_bp\s*\.\s*(get|post|put|patch|delete)\s*\(", re.I)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"_exists": False, "_path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # pragma: no cover - defensive report detail
        return {"_exists": True, "_path": str(path), "_read_error": str(exc)}
    if isinstance(data, dict):
        data.setdefault("_exists", True)
        data.setdefault("_path", str(path))
        return data
    return {"_exists": True, "_path": str(path), "_read_error": "json root is not an object"}


def _count_route_decorators(path: Path) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8", errors="ignore")
    return len(ROUTE_DECORATOR_RE.findall(text))


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def _mobile_inventory(root: Path) -> Dict[str, Any]:
    mobile_dir = root / "app" / "api" / "mobile"
    routes_py = mobile_dir / "routes.py"
    domains_dir = mobile_dir / "domains"
    domain_inventory: List[Dict[str, Any]] = []
    total_routes = 0

    files: List[Path] = []
    if routes_py.exists():
        files.append(routes_py)
    if domains_dir.exists():
        files.extend(sorted(domains_dir.glob("*.py")))

    for file_path in files:
        route_count = _count_route_decorators(file_path)
        total_routes += route_count
        domain_inventory.append(
            {
                "path": str(file_path.relative_to(root)).replace("\\", "/"),
                "exists": file_path.exists(),
                "route_count": route_count,
                "lines": _line_count(file_path),
            }
        )

    routes_py_lines = _line_count(routes_py)
    return {
        "routes_py_lines": routes_py_lines,
        "routes_py_under_300_lines": routes_py_lines <= 300,
        "routes_py_route_count": _count_route_decorators(routes_py),
        "domains_dir_exists": domains_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": total_routes,
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "route_contract_count_expected": total_routes == EXPECTED_CONTRACT_ROUTE_COUNT,
    }


def _compile_files(files: Sequence[Path]) -> List[Dict[str, str | bool]]:
    results: List[Dict[str, str | bool]] = []
    for file_path in files:
        if not file_path.exists():
            results.append({"file": str(file_path), "ok": False, "error": "missing"})
            continue
        try:
            py_compile.compile(str(file_path), doraise=True)
            results.append({"file": str(file_path), "ok": True, "error": ""})
        except Exception as exc:
            results.append({"file": str(file_path), "ok": False, "error": str(exc)})
    return results


def _run(cmd: Sequence[str], cwd: Path, env_extra: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    env = os.environ.copy()
    env.update(
        {
            "FLASK_ENV": "testing",
            "APP_ENV": "testing",
            "BYS360_ENV": "testing",
            "DATABASE_URL": env.get("DATABASE_URL", "sqlite:///:memory:"),
            "SECRET_KEY": env.get("SECRET_KEY", "bys360-test-secret-key"),
            "WTF_CSRF_ENABLED": "0",
        }
    )
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1200:],
        "stderr_tail": proc.stderr[-1200:],
        "ok": proc.returncode == 0,
        "cmd": list(cmd),
    }


def _app_factory_smoke(root: Path) -> Dict[str, Any]:
    return _run([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root)


def _secret_gate(root: Path) -> Dict[str, Any]:
    script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not script.exists():
        return {"ok": False, "returncode": 127, "stdout_tail": "", "stderr_tail": "secret gate script missing", "parsed": {}}
    result = _run([sys.executable, str(script), "--root", str(root)], root)
    parsed: Dict[str, Any] = {}
    try:
        candidates = [line for line in result.get("stdout_tail", "").splitlines() if line.strip().startswith("{")]
        if candidates:
            parsed = json.loads("\n".join(result["stdout_tail"].splitlines()[result["stdout_tail"].splitlines().index(candidates[-1]) :]))
        else:
            parsed = json.loads(result.get("stdout_tail", "{}"))
    except Exception:
        parsed = _read_json(root / SECRET_REPORT_REL)
    result["parsed"] = parsed
    result["ok"] = bool(result.get("ok")) and bool(parsed.get("ok", True)) and int(parsed.get("finding_count", 0) or 0) == 0
    return result


def _pytest_gate(root: Path) -> Dict[str, Any]:
    test_file = root / "tests" / "architecture" / "test_mobile_api_release_evidence_p4e.py"
    if not test_file.exists():
        return {"ok": False, "returncode": 127, "stdout_tail": "", "stderr_tail": "P4E pytest file missing", "mode": "pytest_targeted_mobile_release_evidence_p4e"}
    result = _run([sys.executable, "-m", "pytest", str(test_file.relative_to(root)), "-q"], root)
    result["mode"] = "pytest_targeted_mobile_release_evidence_p4e"
    return result


def _summarize_p3f(report: Dict[str, Any]) -> Dict[str, Any]:
    feature_coverage = report.get("feature_coverage") if isinstance(report.get("feature_coverage"), dict) else {}
    gate_results = report.get("gate_results") if isinstance(report.get("gate_results"), list) else []
    passed_labels = [item.get("label") for item in gate_results if isinstance(item, dict) and item.get("ok")]
    return {
        "exists": bool(report.get("_exists")),
        "ok": bool(report.get("ok")) and bool(report.get("p3_suite_ok")),
        "p3_suite_ok": bool(report.get("p3_suite_ok")),
        "p3_gate_count": int(report.get("p3_gate_count", 0) or 0),
        "p3_gates_passed": int(report.get("p3_gates_passed", 0) or 0),
        "expected_gate_count_ok": int(report.get("p3_gate_count", 0) or 0) == EXPECTED_P3_GATE_COUNT,
        "all_gates_passed_ok": int(report.get("p3_gates_passed", 0) or 0) == EXPECTED_P3_GATE_COUNT,
        "feature_coverage": feature_coverage,
        "feature_coverage_ok": all(bool(feature_coverage.get(key, False)) for key in [
            "auth", "dashboard", "assistant", "personnel", "kpi", "communication", "support", "survey", "notifications", "performance"
        ]),
        "passed_labels": passed_labels,
        "report": report.get("_path"),
    }


def _summarize_p4d(report: Dict[str, Any]) -> Dict[str, Any]:
    evidence = report.get("security_evidence") if isinstance(report.get("security_evidence"), dict) else {}
    observed = set(evidence.get("observed_features", []) or [])
    missing = sorted(EXPECTED_FEATURES - observed)
    secret_counts = evidence.get("secret_finding_counts", []) or []
    return {
        "exists": bool(report.get("_exists")),
        "ok": bool(report.get("ok")) and bool(report.get("security_evidence_gate_ok")) and bool(report.get("handover_evidence_ok")),
        "security_evidence_gate_ok": bool(report.get("security_evidence_gate_ok")),
        "handover_evidence_ok": bool(report.get("handover_evidence_ok")),
        "reports_exist_ok": bool(report.get("reports_exist_ok")),
        "security_gate_count": int(report.get("security_gate_count", 0) or 0),
        "security_gates_passed": int(report.get("security_gates_passed", 0) or 0),
        "total_probe_count": int(report.get("total_probe_count", 0) or 0),
        "probe_count_ok": int(report.get("total_probe_count", 0) or 0) >= MIN_TOTAL_SECURITY_PROBE_COUNT,
        "feature_coverage_ok": bool(report.get("feature_coverage_ok")) and not missing,
        "missing_features": missing,
        "no_secret_findings_in_evidence_reports": bool(report.get("no_secret_findings_in_evidence_reports")) and all(int(x or 0) == 0 for x in secret_counts),
        "status_counts": evidence.get("status_counts", {}),
        "report": report.get("_path"),
    }


def run_gate(args: argparse.Namespace) -> Dict[str, Any]:
    root = Path(args.root).resolve()
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)

    inventory = _mobile_inventory(root)
    p3f_report = _read_json(root / P3F_REPORT_REL)
    p4d_report = _read_json(root / P4D_REPORT_REL)
    p4c_report = _read_json(root / P4C_REPORT_REL)
    p3f_summary = _summarize_p3f(p3f_report)
    p4d_summary = _summarize_p4d(p4d_report)

    release_evidence_ok = (
        p3f_summary["ok"]
        and p3f_summary["expected_gate_count_ok"]
        and p3f_summary["all_gates_passed_ok"]
        and p3f_summary["feature_coverage_ok"]
        and p4d_summary["ok"]
        and p4d_summary["security_gate_count"] == EXPECTED_SECURITY_GATE_COUNT
        and p4d_summary["security_gates_passed"] == EXPECTED_SECURITY_GATE_COUNT
        and p4d_summary["probe_count_ok"]
        and p4d_summary["feature_coverage_ok"]
        and p4d_summary["no_secret_findings_in_evidence_reports"]
    )

    compile_results: List[Dict[str, Any]] = []
    if args.compile_all:
        compile_results = _compile_files(
            [
                root / "scripts" / "quality" / "bys360_mobile_release_evidence_gate_p4e.py",
                root / "tests" / "architecture" / "test_mobile_api_release_evidence_p4e.py",
                root / "tests" / "architecture" / "conftest.py",
                root / "scripts" / "quality" / "bys360_mobile_response_suite_gate_p3f.py",
                root / "scripts" / "quality" / "bys360_mobile_security_evidence_gate_p4d.py",
                root / "scripts" / "quality" / "bys360_mobile_security_suite_gate_p4c_v2.py",
            ]
        )
    compile_ok = all(item.get("ok") for item in compile_results) if compile_results else True

    app_factory = _app_factory_smoke(root) if args.app_factory else {"ok": True, "skipped": True}
    secret = _secret_gate(root) if args.secret_gate else {"ok": True, "skipped": True, "parsed": {"finding_count": 0}}
    pytest = _pytest_gate(root) if args.pytest_gate else {"ok": True, "skipped": True, "mode": "not_run"}

    secret_count = int((secret.get("parsed") or {}).get("finding_count", 0) or 0)
    direct_contract_ok = (
        inventory["routes_py_under_300_lines"]
        and inventory["routes_py_route_count"] == 0
        and inventory["domains_dir_exists"]
        and inventory["route_contract_count_expected"]
    )

    output: Dict[str, Any] = {
        "ok": bool(release_evidence_ok and direct_contract_ok and compile_ok and app_factory.get("ok") and secret.get("ok") and pytest.get("ok")),
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mobile_release_evidence_gate_ok": bool(release_evidence_ok),
        "response_suite_report_ok": bool(p3f_summary["ok"]),
        "security_evidence_report_ok": bool(p4d_summary["ok"]),
        "p3_gate_count": p3f_summary["p3_gate_count"],
        "p3_gates_passed": p3f_summary["p3_gates_passed"],
        "security_gate_count": p4d_summary["security_gate_count"],
        "security_gates_passed": p4d_summary["security_gates_passed"],
        "total_probe_count": p4d_summary["total_probe_count"],
        "feature_coverage_ok": bool(p3f_summary["feature_coverage_ok"] and p4d_summary["feature_coverage_ok"]),
        "direct_contract_ok": bool(direct_contract_ok),
        "routes_py_lines": inventory["routes_py_lines"],
        "routes_py_under_300_lines": inventory["routes_py_under_300_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "compile_ok": bool(compile_ok),
        "app_factory_ok": bool(app_factory.get("ok")),
        "secret_gate_ok": bool(secret.get("ok")),
        "secret_gate_finding_count": secret_count,
        "pytest_ok": bool(pytest.get("ok")),
        "pytest_mode": pytest.get("mode", "pytest_targeted_mobile_release_evidence_p4e"),
        "inventory": inventory,
        "release_evidence": {
            "ok": bool(release_evidence_ok),
            "p3f": p3f_summary,
            "p4d": p4d_summary,
            "p4c_v2_report_exists": bool(p4c_report.get("_exists")),
            "source_reports": {
                "p3f": str(root / P3F_REPORT_REL),
                "p4d": str(root / P4D_REPORT_REL),
                "p4c_v2": str(root / P4C_REPORT_REL),
            },
        },
        "compile_results": compile_results,
        "app_factory_smoke": app_factory,
        "secret_gate": secret,
        "pytest": pytest,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_mobile_release_evidence_gate_p4e.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str(report_path),
        "next_actions": [
            "P4E temizse P3 response suite ve P4 security evidence mobil API teslim kaniti olarak tek release gate altinda standart kabul edilebilir.",
            "P5 asamasinda mobil Android responsive/UI regression ve cihaz boyutu kontrol kapilari planlanabilir.",
        ],
    }

    report_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest-gate", action="store_true")
    args = parser.parse_args(argv)
    result = run_gate(args)
    summary_keys = [
        "ok",
        "package",
        "mobile_release_evidence_gate_ok",
        "response_suite_report_ok",
        "security_evidence_report_ok",
        "p3_gate_count",
        "p3_gates_passed",
        "security_gate_count",
        "security_gates_passed",
        "total_probe_count",
        "feature_coverage_ok",
        "direct_contract_ok",
        "compile_ok",
        "app_factory_ok",
        "secret_gate_ok",
        "secret_gate_finding_count",
        "pytest_ok",
        "pytest_mode",
        "report",
    ]
    print(json.dumps({key: result.get(key) for key in summary_keys}, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
