#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""BYS360 P4A Mobile Auth Guard Matrix Gate.

Güvenli, yazmasız kalite kapısıdır. Mobil API'nin ana korumalı endpointlerinde
route kırılması (404/405), beklenmeyen 5xx ve yetkisiz erişimde açık 2xx cevabı
oluşmadığını test eder. Canlı veriye yazmaz; Flask test_client kullanır.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P4A_MOBILE_AUTH_GUARD_MATRIX_GATE"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_AUTH_GUARD_MATRIX_GATE_P4A_REPORT.json")
ACTIVE_TEST_FILE = "test_mobile_api_auth_guard_matrix_p4a.py"

# Sadece kimlik/oturum korumasını yoklayan ve canlı veriye yazmayan istekler.
# POST istekleri de yetkisiz durumda 401/403 gibi erken kesilmelidir.
AUTH_GUARD_CASES: list[dict[str, str]] = [
    {"feature": "auth", "method": "POST", "path": "/api/mobile/auth/login", "kind": "public_invalid_payload"},
    {"feature": "auth", "method": "POST", "path": "/api/mobile/auth/refresh", "kind": "protected"},
    {"feature": "identity", "method": "GET", "path": "/api/mobile/me", "kind": "protected"},
    {"feature": "dashboard", "method": "GET", "path": "/api/mobile/dashboard/summary", "kind": "protected"},
    {"feature": "assistant", "method": "POST", "path": "/api/mobile/assistant/v2/ask", "kind": "protected"},
    {"feature": "personnel", "method": "GET", "path": "/api/mobile/personnel/list", "kind": "protected"},
    {"feature": "personnel", "method": "GET", "path": "/api/mobile/personnel/all", "kind": "protected"},
    {"feature": "kpi", "method": "GET", "path": "/api/mobile/kpi/target-management", "kind": "protected"},
    {"feature": "communication", "method": "GET", "path": "/api/mobile/communication/v2/users", "kind": "protected"},
    {"feature": "support", "method": "GET", "path": "/api/mobile/support/tickets", "kind": "protected"},
    {"feature": "survey", "method": "GET", "path": "/api/mobile/surveys", "kind": "protected"},
    {"feature": "notifications", "method": "GET", "path": "/api/mobile/notifications", "kind": "protected"},
    {"feature": "performance", "method": "GET", "path": "/api/mobile/performance/summary", "kind": "protected"},
    {"feature": "performance", "method": "GET", "path": "/api/mobile/performance/tasks", "kind": "protected"},
    {"feature": "push", "method": "POST", "path": "/api/mobile/push/register-token", "kind": "protected"},
    {"feature": "push", "method": "POST", "path": "/api/mobile/notifications/fcm-token", "kind": "protected"},
    {"feature": "push", "method": "POST", "path": "/api/mobile/push/unregister-token", "kind": "protected"},
    {"feature": "push", "method": "GET", "path": "/api/mobile/push/status", "kind": "protected"},
]

PROTECTED_EXPECTED_STATUSES = {400, 401, 403, 422}
PUBLIC_INVALID_EXPECTED_STATUSES = {400, 401, 403, 422}


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _compile_file(path: Path) -> dict[str, Any]:
    try:
        py_compile.compile(str(path), doraise=True)
        return {"file": str(path), "ok": True, "error": ""}
    except Exception as exc:  # noqa: BLE001 - kalite raporunda hata metni gerekir
        return {"file": str(path), "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _run_subprocess(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=merged_env,
        text=True,
        capture_output=True,
    )
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-5000:],
        "stderr_tail": proc.stderr[-5000:],
        "ok": proc.returncode == 0,
        "cmd": cmd,
    }


def _ensure_testing_env() -> None:
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("APP_ENV", "testing")
    os.environ.setdefault("BYS360_TESTING", "1")
    os.environ.setdefault("BYS360_DISABLE_SCHEDULERS", "1")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("SECRET_KEY", "bys360-test-secret-key-for-quality-gates")
    os.environ.setdefault("JWT_SECRET_KEY", "bys360-test-jwt-secret-key-for-quality-gates")
    os.environ.setdefault("WTF_CSRF_ENABLED", "False")


def ensure_active_scope(root: Path) -> dict[str, Any]:
    conftest = root / "tests" / "architecture" / "conftest.py"
    if not conftest.exists():
        return {"path": str(conftest), "changed": False, "reason": "missing_conftest"}
    text = _read_text(conftest)
    if ACTIVE_TEST_FILE in text:
        return {"path": str(conftest), "changed": False, "reason": "already_present"}

    marker = "# BYS360_P4A_ACTIVE_SCOPE"
    addition = f"\n{marker}\nBYS360_ACTIVE_ARCHITECTURE_TESTS = tuple(list(globals().get('BYS360_ACTIVE_ARCHITECTURE_TESTS', ())) + ['{ACTIVE_TEST_FILE}'])\n"
    conftest.write_text(text.rstrip() + addition + "\n", encoding="utf-8")
    return {"path": str(conftest), "changed": True, "reason": "inserted_into_active_scope"}


def mobile_route_inventory(root: Path) -> dict[str, Any]:
    mobile_dir = root / "app" / "api" / "mobile"
    domains_dir = mobile_dir / "domains"
    routes_py = mobile_dir / "routes.py"
    domain_files = [routes_py]
    if domains_dir.exists():
        domain_files.extend(sorted(domains_dir.glob("*.py")))

    total_routes = 0
    domain_inventory: list[dict[str, Any]] = []
    route_rules: list[str] = []
    duplicate_candidates: list[str] = []
    seen: set[str] = set()

    for path in domain_files:
        text = _read_text(path)
        lines = text.splitlines()
        route_count = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("@mobile_api_bp."):
                route_count += 1
                normalized = stripped.replace("@mobile_api_bp.", "")
                route_rules.append(normalized)
                if normalized in seen:
                    duplicate_candidates.append(normalized)
                seen.add(normalized)
        total_routes += route_count
        domain_inventory.append(
            {
                "path": _rel(path, root),
                "exists": path.exists(),
                "route_count": route_count,
                "lines": len(lines),
            }
        )

    return {
        "routes_py_lines": len(_read_text(routes_py).splitlines()),
        "routes_py_route_count": sum(
            1 for line in _read_text(routes_py).splitlines() if line.strip().startswith("@mobile_api_bp.")
        ),
        "domains_dir_exists": domains_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": total_routes,
        "expected_contract_route_count": 28,
        "duplicate_route_decorators": duplicate_candidates,
        "route_rules_sample": sorted(route_rules)[:40],
    }


def _expected_suffixes() -> list[tuple[str, str]]:
    return [(case["method"], case["path"]) for case in AUTH_GUARD_CASES]


def runtime_route_map(root: Path) -> dict[str, Any]:
    _ensure_testing_env()
    sys.path.insert(0, str(root))
    try:
        from app import create_app  # type: ignore

        app = create_app()
        runtime_routes: list[dict[str, Any]] = []
        for rule in app.url_map.iter_rules():
            methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
            item = {"rule": str(rule.rule), "methods": methods, "endpoint": rule.endpoint}
            runtime_routes.append(item)

        mobile_routes = [item for item in runtime_routes if str(item["rule"]).startswith("/api/mobile")]
        missing: list[dict[str, str]] = []
        mismatches: list[dict[str, str]] = []
        for method, suffix in _expected_suffixes():
            expected_path = suffix if suffix.startswith("/api/mobile") else "/api/mobile" + suffix
            matches = [item for item in runtime_routes if item["rule"] == expected_path or item["rule"].endswith(suffix)]
            if not matches:
                missing.append({"method": method, "path": expected_path})
                continue
            if not any(method in item["methods"] for item in matches):
                mismatches.append({"method": method, "path": expected_path})

        return {
            "ok": not missing and not mismatches,
            "app_build_ok": True,
            "runtime_route_count": len(runtime_routes),
            "mobile_runtime_route_count": len(mobile_routes),
            "missing_runtime_suffixes": missing,
            "runtime_method_mismatches": mismatches,
            "sample_mobile_routes": mobile_routes[:80],
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001 - kalite raporunda hata metni gerekir
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
        try:
            sys.path.remove(str(root))
        except ValueError:
            pass


def _call_client(client: Any, method: str, path: str, headers: dict[str, str] | None = None) -> Any:
    payload = {"_bys360_quality_gate": True}
    method = method.upper()
    if method == "GET":
        return client.get(path, headers=headers or {})
    if method == "POST":
        return client.post(path, json=payload, headers=headers or {})
    raise ValueError(f"Unsupported method: {method}")


def auth_guard_matrix(root: Path) -> dict[str, Any]:
    _ensure_testing_env()
    sys.path.insert(0, str(root))
    try:
        from app import create_app  # type: ignore

        app = create_app()
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        client = app.test_client()
        responses: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        scenarios = [
            {"name": "no_authorization", "headers": {}},
            {"name": "malformed_bearer", "headers": {"Authorization": "Bearer bys360.invalid.test.token"}},
        ]

        for case in AUTH_GUARD_CASES:
            for scenario in scenarios:
                if case["kind"] == "public_invalid_payload" and scenario["name"] != "no_authorization":
                    continue
                response = _call_client(client, case["method"], case["path"], scenario["headers"])
                status = int(getattr(response, "status_code", 0))
                allowed = PUBLIC_INVALID_EXPECTED_STATUSES if case["kind"] == "public_invalid_payload" else PROTECTED_EXPECTED_STATUSES
                no_route_break = status not in {404, 405}
                no_server_error = status < 500
                no_open_access = not (case["kind"] == "protected" and 200 <= status < 300)
                status_expected = status in allowed or (300 <= status < 400)
                ok = no_route_break and no_server_error and no_open_access and status_expected
                item = {
                    "feature": case["feature"],
                    "method": case["method"],
                    "path": case["path"],
                    "kind": case["kind"],
                    "scenario": scenario["name"],
                    "status_code": status,
                    "ok": ok,
                    "expected_statuses": sorted(allowed),
                }
                responses.append(item)
                if not ok:
                    failures.append(item)

        return {
            "ok": not failures,
            "mode": "flask_test_client_auth_guard_matrix_no_404_405_no_5xx_no_open_2xx",
            "case_count": len(AUTH_GUARD_CASES),
            "probe_count": len(responses),
            "responses": responses,
            "failures": failures,
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "mode": "flask_test_client_auth_guard_matrix_no_404_405_no_5xx_no_open_2xx",
            "case_count": len(AUTH_GUARD_CASES),
            "probe_count": 0,
            "responses": [],
            "failures": [],
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        try:
            sys.path.remove(str(root))
        except ValueError:
            pass


def app_factory_smoke(root: Path) -> dict[str, Any]:
    return _run_subprocess(
        [sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"],
        cwd=root,
        env={
            "FLASK_ENV": "testing",
            "APP_ENV": "testing",
            "BYS360_TESTING": "1",
            "DATABASE_URL": os.environ.get("DATABASE_URL", "sqlite:///:memory:"),
            "SECRET_KEY": os.environ.get("SECRET_KEY", "bys360-test-secret-key-for-quality-gates"),
        },
    )


def secret_gate(root: Path) -> dict[str, Any]:
    gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": "secret gate script missing", "parsed": {}}
    result = _run_subprocess([sys.executable, str(gate), "--root", str(root)], cwd=root)
    parsed: dict[str, Any] = {}
    try:
        start = result["stdout_tail"].find("{")
        end = result["stdout_tail"].rfind("}")
        if start >= 0 and end >= start:
            parsed = json.loads(result["stdout_tail"][start : end + 1])
    except Exception:
        parsed = {}
    result["parsed"] = parsed
    result["ok"] = result["ok"] and bool(parsed.get("ok", False)) and int(parsed.get("finding_count", 9999)) == 0
    return result


def pytest_gate(root: Path) -> dict[str, Any]:
    test_path = root / "tests" / "architecture" / ACTIVE_TEST_FILE
    result = _run_subprocess([sys.executable, "-m", "pytest", str(test_path.relative_to(root)), "-q"], cwd=root)
    result["mode"] = "pytest_targeted_mobile_auth_guard_matrix_p4a"
    return result


def run_checks(
    root: Path,
    compile_all: bool = False,
    app_factory: bool = False,
    secret_gate_enabled: bool = False,
    pytest_gate_enabled: bool = False,
    write_report: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    active_scope = ensure_active_scope(root)
    inventory = mobile_route_inventory(root)
    runtime = runtime_route_map(root)
    guard = auth_guard_matrix(root)

    compile_targets = [
        root / "scripts" / "quality" / "bys360_mobile_auth_guard_matrix_gate_p4a.py",
        root / "tests" / "architecture" / ACTIVE_TEST_FILE,
        root / "tests" / "architecture" / "conftest.py",
    ]
    compile_results = [_compile_file(path) for path in compile_targets]
    compile_ok = all(item["ok"] for item in compile_results)

    app_smoke = app_factory_smoke(root) if app_factory else {"ok": True, "skipped": True}
    secret = secret_gate(root) if secret_gate_enabled else {"ok": True, "skipped": True, "parsed": {}}
    pytest_result = pytest_gate(root) if pytest_gate_enabled else {"ok": True, "skipped": True, "mode": "not_requested"}

    direct_contract_ok = (
        inventory["routes_py_lines"] <= 300
        and inventory["routes_py_route_count"] == 0
        and inventory["total_mobile_route_decorator_count"] == inventory["expected_contract_route_count"]
        and not inventory["duplicate_route_decorators"]
    )

    result: dict[str, Any] = {
        "ok": False,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "active_scope": active_scope,
        "routes_py_lines": inventory["routes_py_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": inventory["expected_contract_route_count"],
        "direct_contract_ok": direct_contract_ok,
        "runtime_route_map_ok": bool(runtime.get("ok")),
        "auth_guard_matrix_ok": bool(guard.get("ok")),
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_smoke.get("ok")),
        "secret_gate_ok": bool(secret.get("ok")),
        "secret_gate_finding_count": int(secret.get("parsed", {}).get("finding_count", 0)) if secret.get("parsed") else 0,
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode", "unknown"),
        "inventory": inventory,
        "runtime_route_map": runtime,
        "auth_guard_matrix": guard,
        "compile_results": compile_results,
        "app_factory_smoke": app_smoke,
        "secret_gate": secret,
        "pytest": pytest_result,
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P4A temizse mobil API yetkisiz/malformed token koruma matrisi standart kalite kapisina alinmis kabul edilebilir.",
            "P4B'de gerçek test kullanıcısı ile rol bazlı auth senaryoları, canlı veriye dokunmadan fixture üzerinden genişletilebilir.",
        ],
    }
    result["ok"] = all(
        [
            result["direct_contract_ok"],
            result["runtime_route_map_ok"],
            result["auth_guard_matrix_ok"],
            result["compile_ok"],
            result["app_factory_ok"],
            result["secret_gate_ok"],
            result["pytest_ok"],
        ]
    )

    if write_report:
        _write_json(root / REPORT_REL, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest-gate", action="store_true")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()

    result = run_checks(
        Path(args.root),
        compile_all=args.compile_all,
        app_factory=args.app_factory,
        secret_gate_enabled=args.secret_gate,
        pytest_gate_enabled=args.pytest_gate,
        write_report=not args.no_report,
    )
    summary_keys = [
        "ok",
        "package",
        "routes_py_lines",
        "total_mobile_route_decorator_count",
        "direct_contract_ok",
        "runtime_route_map_ok",
        "auth_guard_matrix_ok",
        "compile_ok",
        "app_factory_ok",
        "secret_gate_ok",
        "pytest_ok",
        "pytest_mode",
        "report",
    ]
    print(json.dumps({key: result.get(key) for key in summary_keys}, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
