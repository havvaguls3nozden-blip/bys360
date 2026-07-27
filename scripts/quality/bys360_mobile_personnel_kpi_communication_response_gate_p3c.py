from __future__ import annotations

import argparse
import contextlib
import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P3C_MOBILE_PERSONNEL_KPI_COMMUNICATION_RESPONSE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_PERSONNEL_KPI_COMMUNICATION_RESPONSE_GATE_P3C_REPORT.json")
TEST_FILE = "test_mobile_api_personnel_kpi_communication_response_p3c.py"
EXPECTED_CONTRACT_ROUTE_COUNT = 24

EXPECTED_ROUTE_SUFFIXES: list[tuple[str, str]] = [
    ("GET", "/personnel/list"),
    ("GET", "/personnel/all"),
    ("POST", "/personnel/create"),
    ("POST", "/personnel/add"),
    ("GET", "/kpi/target-management"),
    ("POST", "/kpi/target-management"),
    ("POST", "/kpi/target-management/<int:target_id>/progress"),
    ("GET", "/communication/messages/threads/<int:thread_id>"),
    ("POST", "/communication/messages/threads/<int:thread_id>/send"),
    ("POST", "/communication/messages/create-thread"),
    ("GET", "/communication/v2/threads/<int:thread_id>"),
    ("POST", "/communication/v2/threads/<int:thread_id>/send"),
    ("GET", "/communication/v2/users"),
    ("POST", "/communication/v2/create-thread"),
]

RESPONSE_SCENARIOS: list[dict[str, Any]] = [
    {"feature": "personnel", "method": "GET", "path": "/api/mobile/personnel/list", "json": None},
    {"feature": "personnel", "method": "GET", "path": "/api/mobile/personnel/all", "json": None},
    {"feature": "personnel", "method": "POST", "path": "/api/mobile/personnel/create", "json": {}},
    {"feature": "personnel", "method": "POST", "path": "/api/mobile/personnel/add", "json": {}},
    {"feature": "kpi", "method": "GET", "path": "/api/mobile/kpi/target-management", "json": None},
    {"feature": "kpi", "method": "POST", "path": "/api/mobile/kpi/target-management", "json": {}},
    {"feature": "kpi", "method": "POST", "path": "/api/mobile/kpi/target-management/1/progress", "json": {}},
    {"feature": "communication", "method": "GET", "path": "/api/mobile/communication/messages/threads/1", "json": None},
    {"feature": "communication", "method": "POST", "path": "/api/mobile/communication/messages/threads/1/send", "json": {}},
    {"feature": "communication", "method": "POST", "path": "/api/mobile/communication/messages/create-thread", "json": {}},
    {"feature": "communication", "method": "GET", "path": "/api/mobile/communication/v2/threads/1", "json": None},
    {"feature": "communication", "method": "POST", "path": "/api/mobile/communication/v2/threads/1/send", "json": {}},
    {"feature": "communication", "method": "GET", "path": "/api/mobile/communication/v2/users", "json": None},
    {"feature": "communication", "method": "POST", "path": "/api/mobile/communication/v2/create-thread", "json": {}},
]

EXPECTED_DOMAIN_FILES = [
    "app/api/mobile/domains/personnel_read.py",
    "app/api/mobile/domains/personnel_write_all.py",
    "app/api/mobile/domains/kpi_target_management.py",
    "app/api/mobile/domains/communication_v1_write.py",
    "app/api/mobile/domains/communication_v2_write.py",
]

ROUTE_DECORATOR_RE = re.compile(r"@mobile_api_bp\.(get|post|put|patch|delete)\(\s*([\"'])(.*?)\2")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _line_count(path: Path) -> int:
    return len(_read(path).splitlines()) if path.exists() else 0


def _compile(path: Path) -> dict[str, Any]:
    try:
        py_compile.compile(str(path), doraise=True)
        return {"file": str(path), "ok": True, "error": ""}
    except Exception as exc:  # noqa: BLE001 - quality gate reports exact failure
        return {"file": str(path), "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def collect_inventory(root: Path) -> dict[str, Any]:
    mobile_dir = root / "app" / "api" / "mobile"
    routes_py = mobile_dir / "routes.py"
    domains_dir = mobile_dir / "domains"
    files = []
    if routes_py.exists():
        files.append(routes_py)
    if domains_dir.exists():
        files.extend(sorted(domains_dir.glob("*.py")))

    route_entries: list[dict[str, str]] = []
    domain_inventory = []
    for file_path in files:
        text = _read(file_path)
        entries = []
        for method, _quote, suffix in ROUTE_DECORATOR_RE.findall(text):
            entry = {
                "method": method.upper(),
                "suffix": suffix,
                "path": file_path.relative_to(root).as_posix(),
                "decorator": f"{method.upper()} {suffix}",
            }
            entries.append(entry)
            route_entries.append(entry)
        domain_inventory.append({
            "path": file_path.relative_to(root).as_posix(),
            "exists": file_path.exists(),
            "route_count": len(entries),
            "lines": _line_count(file_path),
        })

    seen: set[tuple[str, str]] = set()
    duplicates = []
    for entry in route_entries:
        key = (entry["method"], entry["suffix"])
        if key in seen:
            duplicates.append(entry)
        seen.add(key)

    missing_expected = []
    for method, suffix in EXPECTED_ROUTE_SUFFIXES:
        if (method, suffix) not in seen:
            missing_expected.append({"method": method, "suffix": suffix})

    return {
        "routes_py_lines": _line_count(routes_py),
        "routes_py_route_count": sum(1 for e in route_entries if e["path"] == "app/api/mobile/routes.py"),
        "domains_dir_exists": domains_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": len(route_entries),
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "duplicate_route_decorators": duplicates,
        "expected_missing_routes": missing_expected,
        "route_rules_sample": [f"{e['method']} {e['suffix']}" for e in route_entries[:40]],
    }


def _prepare_env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("FLASK_ENV", "testing")
    env.setdefault("APP_ENV", "testing")
    env.setdefault("SECRET_KEY", "bys360-test-secret-key-not-for-production")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("SENTRY_DSN", "")
    env.setdefault("BYS360_DISABLE_SCHEDULERS", "1")
    env.setdefault("BYS360_TESTING", "1")
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def runtime_route_map_check(root: Path) -> dict[str, Any]:
    previous = os.getcwd()
    sys_path_added = False
    try:
        os.chdir(root)
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
            sys_path_added = True
        os.environ.setdefault("FLASK_ENV", "testing")
        os.environ.setdefault("APP_ENV", "testing")
        os.environ.setdefault("SECRET_KEY", "bys360-test-secret-key-not-for-production")
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        os.environ.setdefault("SENTRY_DSN", "")
        os.environ.setdefault("BYS360_DISABLE_SCHEDULERS", "1")
        from app import create_app

        app = create_app()
        routes = []
        for rule in app.url_map.iter_rules():
            if str(rule.rule).startswith("/api/mobile"):
                methods = sorted(m for m in (rule.methods or ()) if m not in {"HEAD", "OPTIONS"})
                routes.append({"rule": str(rule.rule), "methods": methods, "endpoint": rule.endpoint})

        missing = []
        method_mismatches = []
        for method, suffix in EXPECTED_ROUTE_SUFFIXES:
            full_suffix = "/api/mobile" + suffix
            match = next((r for r in routes if r["rule"].endswith(full_suffix)), None)
            if not match:
                missing.append({"method": method, "suffix": suffix, "expected_runtime_suffix": full_suffix})
            elif method not in match["methods"]:
                method_mismatches.append({"method": method, "suffix": suffix, "runtime_methods": match["methods"]})

        return {
            "ok": not missing and not method_mismatches,
            "app_build_ok": True,
            "runtime_route_count": len(list(app.url_map.iter_rules())),
            "mobile_runtime_route_count": len(routes),
            "missing_runtime_suffixes": missing,
            "runtime_method_mismatches": method_mismatches,
            "sample_mobile_routes": routes[:60],
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "app_build_ok": False,
            "runtime_route_count": 0,
            "mobile_runtime_route_count": 0,
            "missing_runtime_suffixes": [],
            "runtime_method_mismatches": [],
            "sample_mobile_routes": [],
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        os.chdir(previous)
        if sys_path_added:
            with contextlib.suppress(ValueError):
                sys.path.remove(str(root))


def response_code_smoke(root: Path) -> dict[str, Any]:
    previous = os.getcwd()
    sys_path_added = False
    try:
        os.chdir(root)
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
            sys_path_added = True
        os.environ.setdefault("FLASK_ENV", "testing")
        os.environ.setdefault("APP_ENV", "testing")
        os.environ.setdefault("SECRET_KEY", "bys360-test-secret-key-not-for-production")
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        os.environ.setdefault("SENTRY_DSN", "")
        os.environ.setdefault("BYS360_DISABLE_SCHEDULERS", "1")
        from app import create_app

        app = create_app()
        client = app.test_client()
        responses = []
        for scenario in RESPONSE_SCENARIOS:
            kwargs: dict[str, Any] = {}
            if scenario.get("json") is not None:
                kwargs["json"] = scenario["json"]
            response = client.open(scenario["path"], method=scenario["method"], **kwargs)
            status = int(response.status_code)
            # This smoke gate catches routing regressions. Auth/schema failures may legitimately return 4xx/5xx in sqlite test mode.
            ok = status not in {404, 405}
            responses.append({
                "feature": scenario["feature"],
                "method": scenario["method"],
                "path": scenario["path"],
                "status_code": status,
                "ok": ok,
            })
        return {
            "ok": all(item["ok"] for item in responses),
            "mode": "flask_test_client_response_codes_no_404_405",
            "responses": responses,
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "mode": "flask_test_client_response_codes_no_404_405",
            "responses": [],
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        os.chdir(previous)
        if sys_path_added:
            with contextlib.suppress(ValueError):
                sys.path.remove(str(root))


def run_subprocess(cmd: list[str], root: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(root), env=env or _prepare_env(root), capture_output=True, text=True)
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "ok": proc.returncode == 0,
        "cmd": cmd,
    }


def parse_last_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {}
    starts = [idx for idx, char in enumerate(stripped) if char == "{"]
    for idx in reversed(starts):
        try:
            return json.loads(stripped[idx:])
        except Exception:
            continue
    return {}


def run_secret_gate(root: Path) -> dict[str, Any]:
    gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": False, "returncode": 1, "stdout_tail": "", "stderr_tail": "secret gate not found", "parsed": {}}
    result = run_subprocess([sys.executable, str(gate), "--root", str(root)], root)
    parsed = parse_last_json(result.get("stdout_tail", ""))
    result["parsed"] = parsed
    result["ok"] = result["returncode"] == 0 and parsed.get("ok") is True and int(parsed.get("finding_count", 1)) == 0
    return result


def run_app_factory(root: Path) -> dict[str, Any]:
    return run_subprocess([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root)


def ensure_active_test_registered(root: Path) -> dict[str, Any]:
    conftest = root / "tests" / "architecture" / "conftest.py"
    if not conftest.exists():
        return {"path": str(conftest), "changed": False, "reason": "missing"}
    text = _read(conftest)
    if TEST_FILE in text:
        return {"path": str(conftest), "changed": False, "reason": "already_present"}
    lines = text.splitlines()
    inserted = False
    for idx, line in enumerate(lines):
        if line.strip() in {")", "]", "}", ")  # active", "]  # active"} and any("ACTIVE_ARCHITECTURE" in prev for prev in lines[max(0, idx-25):idx]):
            indent = "    "
            lines.insert(idx, f'{indent}"{TEST_FILE}",')
            inserted = True
            break
    if inserted:
        conftest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"path": str(conftest), "changed": True, "reason": "inserted_into_active_scope"}
    conftest.write_text(text.rstrip() + f"\n# P3C active test candidate: {TEST_FILE}\n", encoding="utf-8")
    return {"path": str(conftest), "changed": True, "reason": "appended_comment_fallback"}


def run_pytest(root: Path) -> dict[str, Any]:
    test_path = root / "tests" / "architecture" / TEST_FILE
    if not test_path.exists():
        return {"ok": False, "returncode": 1, "stdout_tail": "", "stderr_tail": f"missing {test_path}", "mode": "pytest_targeted_personnel_kpi_communication_response_p3c"}
    result = run_subprocess([sys.executable, "-m", "pytest", str(test_path.relative_to(root)), "-q"], root)
    result["mode"] = "pytest_targeted_personnel_kpi_communication_response_p3c"
    return result


def run_checks(root: Path, compile_all: bool = True, app_factory: bool = True, secret_gate: bool = True, pytest_gate: bool = True, write_report: bool = True) -> dict[str, Any]:
    root = root.resolve()
    inventory = collect_inventory(root)
    runtime_map = runtime_route_map_check(root)
    response_smoke = response_code_smoke(root)

    compile_targets = [
        root / "scripts" / "quality" / "bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
        root / "tests" / "architecture" / TEST_FILE,
        root / "tests" / "architecture" / "conftest.py",
    ]
    compile_results = [_compile(path) for path in compile_targets if path.exists()] if compile_all else []
    compile_ok = all(item["ok"] for item in compile_results) if compile_all else True

    app_factory_smoke = run_app_factory(root) if app_factory else {"ok": True, "skipped": True}
    secret_result: dict[str, Any] = run_secret_gate(root) if secret_gate else {"ok": True, "skipped": True, "parsed": {"finding_count": 0}}
    pytest_result = run_pytest(root) if pytest_gate else {"ok": True, "skipped": True, "mode": "skipped"}

    direct_contract_ok = (
        inventory["routes_py_lines"] <= 300
        and inventory["routes_py_route_count"] == 0
        and inventory["domains_dir_exists"]
        and inventory["total_mobile_route_decorator_count"] >= EXPECTED_CONTRACT_ROUTE_COUNT
        and not inventory["duplicate_route_decorators"]
        and not inventory["expected_missing_routes"]
    )

    result: dict[str, Any] = {
        "ok": False,
        "package": PACKAGE,
        "root": str(root),
        "routes_py_lines": inventory["routes_py_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "direct_contract_ok": direct_contract_ok,
        "runtime_route_map_ok": runtime_map.get("ok") is True,
        "response_code_smoke_ok": response_smoke.get("ok") is True,
        "compile_ok": compile_ok,
        "app_factory_ok": app_factory_smoke.get("ok") is True,
        "secret_gate_ok": secret_result.get("ok") is True,
        "secret_gate_finding_count": int(secret_result.get("parsed", {}).get("finding_count", 0)) if isinstance(secret_result.get("parsed"), dict) else 0,
        "pytest_ok": pytest_result.get("ok") is True,
        "pytest_mode": pytest_result.get("mode", "pytest_targeted_personnel_kpi_communication_response_p3c"),
        "inventory": inventory,
        "runtime_route_map": runtime_map,
        "response_code_smoke": response_smoke,
        "compile_results": compile_results,
        "app_factory_smoke": app_factory_smoke,
        "secret_gate": secret_result,
        "pytest": pytest_result,
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P3C temizse personel/KPI/iletisim mobil response-code smoke kapisi runtime route haritasiyla birlikte kurulmus kabul edilebilir.",
            "P3D'de destek/anket/bildirim endpointleri icin response-code smoke kapisi genisletilebilir.",
        ],
    }
    result["ok"] = all([
        result["direct_contract_ok"],
        result["runtime_route_map_ok"],
        result["response_code_smoke_ok"],
        result["compile_ok"],
        result["app_factory_ok"],
        result["secret_gate_ok"],
        result["secret_gate_finding_count"] == 0,
        result["pytest_ok"],
    ])

    if write_report:
        report = root / REPORT_REL
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", default="all")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    parser.add_argument("--run-pytest", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    conftest_patch = ensure_active_test_registered(root)
    print(conftest_patch)
    result = run_checks(
        root,
        compile_all=args.compile_all or args.mode == "all",
        app_factory=args.run_app_factory_smoke or args.mode == "all",
        secret_gate=args.run_secret_gate or args.mode == "all",
        pytest_gate=args.run_pytest or args.mode == "all",
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
