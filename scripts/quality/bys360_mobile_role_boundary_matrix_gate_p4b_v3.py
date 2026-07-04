#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""BYS360 P4B V3 Mobile Role Boundary Matrix Gate.

Canlı veriye dokunmadan mobil API üzerinde rol/kimlik sınırlarını yoklar.
Amaç, rol taklidi yapan header'lar veya sahte bearer token'lar ile korumalı
mobil endpointlerde açık 2xx, 404/405 route kırılması ya da beklenmeyen 5xx
oluşmadığını standardize etmektir.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import py_compile
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P4B_MOBILE_ROLE_BOUNDARY_MATRIX_GATE_V3"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_ROLE_BOUNDARY_MATRIX_GATE_P4B_V3_REPORT.json")
ACTIVE_TEST_FILE = "test_mobile_api_role_boundary_matrix_p4b_v3.py"
OLD_ACTIVE_TEST_FILES = ["test_mobile_api_role_boundary_matrix_p4b.py", "test_mobile_api_role_boundary_matrix_p4b_v2.py"]

# Yazmasız/etkisiz test verisiyle çağrılır. POST uçlarında amaç işlem yapmak değil,
# yetki katmanının route ve role-boundary seviyesinde güvenli cevap verdiğini görmektir.
ROLE_BOUNDARY_CASES: list[dict[str, str]] = [
    {"feature": "dashboard", "method": "GET", "path": "/api/mobile/dashboard/summary"},
    {"feature": "identity", "method": "GET", "path": "/api/mobile/me"},
    {"feature": "personnel", "method": "GET", "path": "/api/mobile/personnel/all"},
    {"feature": "personnel", "method": "POST", "path": "/api/mobile/personnel/create"},
    {"feature": "kpi", "method": "GET", "path": "/api/mobile/kpi/target-management"},
    {"feature": "kpi", "method": "POST", "path": "/api/mobile/kpi/target-management"},
    {"feature": "communication", "method": "GET", "path": "/api/mobile/communication/v2/users"},
    {"feature": "communication", "method": "POST", "path": "/api/mobile/communication/v2/create-thread"},
    {"feature": "support", "method": "POST", "path": "/api/mobile/support/tickets"},
    {"feature": "survey", "method": "POST", "path": "/api/mobile/surveys/1/submit"},
    {"feature": "notifications", "method": "POST", "path": "/api/mobile/notifications/read-all"},
    {"feature": "performance", "method": "GET", "path": "/api/mobile/performance/tasks"},
    {"feature": "performance", "method": "POST", "path": "/api/mobile/performance/tasks/1/score-form"},
    {"feature": "performance", "method": "POST", "path": "/api/mobile/performance/in-period-notes/v2"},
]

SAFE_EXPECTED_STATUSES = {400, 401, 403, 422, 429}


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
    except Exception as exc:  # noqa: BLE001 - kalite raporu için hata metni gerekir
        return {"file": str(path), "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _run_subprocess(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(cmd, cwd=str(cwd), env=merged_env, text=True, capture_output=True)
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
    """Aktif mimari kapsamına P4B V3 testini ekler, eski P4B/P4B V2 testini çıkarır.

    P4B ilk sürümünde runtime route map, Flask dinamik parametrelerini
    numerik test pathleriyle eşleştirmekte fazla katıydı. Bu nedenle aktif
    kapsamda eski test kalırsa toplu mimari pytest çalıştırmasında gereksiz
    fail üretebilir. V2, eski test adını güvenli şekilde yeni test adıyla
    değiştirir.
    """
    conftest = root / "tests" / "architecture" / "conftest.py"
    if not conftest.exists():
        return {"path": str(conftest), "changed": False, "reason": "missing_conftest"}
    text = _read_text(conftest)
    original = text
    
    for old_test_file in OLD_ACTIVE_TEST_FILES:
        text = text.replace(old_test_file, ACTIVE_TEST_FILE)
    if ACTIVE_TEST_FILE not in text:
        marker = "# BYS360_P4B_V3_ACTIVE_SCOPE"
        addition = (
            f"\n{marker}\n"
            f"BYS360_ACTIVE_ARCHITECTURE_TESTS = tuple(list(globals().get('BYS360_ACTIVE_ARCHITECTURE_TESTS', ())) + ['{ACTIVE_TEST_FILE}'])\n"
        )
        text = text.rstrip() + addition + "\n"
    if text != original:
        conftest.write_text(text, encoding="utf-8")
        return {"path": str(conftest), "changed": True, "reason": "replaced_old_p4b_or_inserted_v2"}
    return {"path": str(conftest), "changed": False, "reason": "already_present"}


def _flask_rule_to_regex(rule: str) -> re.Pattern[str]:
    """Flask rule patternini gerçek test pathiyle eşleştirmek için regexe çevirir.

    Not: ``re.escape`` modern Python sürümlerinde ``<`` ve ``>`` karakterlerini
    kaçırmadığı için önce rule parçalara ayrılır; statik kısımlar escape edilir,
    ``<int:id>`` gibi dinamik Flask converter parçaları ise bilinçli regexe çevrilir.
    Bu sayede ``/tasks/<int:assignment_id>/score-form`` ile
    ``/tasks/1/score-form`` doğru eşleşir.
    """
    pattern_parts: list[str] = []
    pos = 0
    token_re = re.compile(r"<(?:(?P<converter>[^:<>]+):)?(?P<name>[^<>]+)>")
    for match in token_re.finditer(rule):
        pattern_parts.append(re.escape(rule[pos : match.start()]))
        converter = (match.group("converter") or "string").lower()
        if converter == "int":
            pattern_parts.append(r"\d+")
        elif converter == "float":
            pattern_parts.append(r"\d+(?:\.\d+)?")
        elif converter == "uuid":
            pattern_parts.append(r"[0-9a-fA-F-]+")
        elif converter == "path":
            pattern_parts.append(r".+")
        else:
            pattern_parts.append(r"[^/]+")
        pos = match.end()
    pattern_parts.append(re.escape(rule[pos:]))
    return re.compile("^" + "".join(pattern_parts) + "$")


def _runtime_rule_matches_path(rule: str, target_path: str) -> bool:
    if rule == target_path:
        return True
    suffix = target_path.replace("/api/mobile", "", 1)
    if rule.endswith(suffix):
        return True
    return bool(_flask_rule_to_regex(rule).match(target_path))

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
    duplicates: list[str] = []
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
                    duplicates.append(normalized)
                seen.add(normalized)
        total_routes += route_count
        domain_inventory.append({"path": _rel(path, root), "exists": path.exists(), "route_count": route_count, "lines": len(lines)})

    routes_text = _read_text(routes_py)
    return {
        "routes_py_lines": len(routes_text.splitlines()),
        "routes_py_route_count": sum(1 for line in routes_text.splitlines() if line.strip().startswith("@mobile_api_bp.")),
        "domains_dir_exists": domains_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": total_routes,
        "expected_contract_route_count": 28,
        "duplicate_route_decorators": duplicates,
        "route_rules_sample": sorted(route_rules)[:40],
    }


def runtime_route_map(root: Path) -> dict[str, Any]:
    _ensure_testing_env()
    sys.path.insert(0, str(root))
    try:
        from app import create_app  # type: ignore

        app = create_app()
        runtime_routes: list[dict[str, Any]] = []
        for rule in app.url_map.iter_rules():
            methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
            runtime_routes.append({"rule": str(rule.rule), "methods": methods, "endpoint": rule.endpoint})
        mobile_routes = [item for item in runtime_routes if str(item["rule"]).startswith("/api/mobile")]
        missing: list[dict[str, str]] = []
        mismatches: list[dict[str, str]] = []
        for case in ROLE_BOUNDARY_CASES:
            method = case["method"]
            path = case["path"]
            matches = [item for item in runtime_routes if _runtime_rule_matches_path(str(item["rule"]), path)]
            if not matches:
                missing.append({"method": method, "path": path})
                continue
            if not any(method in item["methods"] for item in matches):
                mismatches.append({"method": method, "path": path})
        return {
            "ok": not missing and not mismatches,
            "app_build_ok": True,
            "runtime_route_count": len(runtime_routes),
            "mobile_runtime_route_count": len(mobile_routes),
            "missing_runtime_suffixes": missing,
            "runtime_method_mismatches": mismatches,
            "sample_mobile_routes": mobile_routes[:90],
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
        try:
            sys.path.remove(str(root))
        except ValueError:
            pass


def _b64url(data: dict[str, Any]) -> str:
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unsigned_token(role: str) -> str:
    header = _b64url({"alg": "none", "typ": "JWT"})
    payload = _b64url({"sub": "bys360-quality-gate", "role": role, "roles": [role], "scope": "mobile"})
    return f"{header}.{payload}."


def _boundary_scenarios() -> list[dict[str, Any]]:
    return [
        {"name": "no_authorization", "headers": {}},
        {"name": "spoof_admin_headers", "headers": {"X-User-Role": "admin", "X-BYS360-Role": "admin", "X-Forwarded-User": "admin"}},
        {"name": "unsigned_admin_bearer", "headers": {"Authorization": "Bearer " + _unsigned_token("admin")}},
        {"name": "unsigned_personnel_bearer", "headers": {"Authorization": "Bearer " + _unsigned_token("personel")}},
        {"name": "malformed_bearer", "headers": {"Authorization": "Bearer bys360.invalid.role.boundary"}},
    ]


def _payload_for(case: dict[str, str]) -> dict[str, Any]:
    feature = case["feature"]
    return {
        "_bys360_quality_gate": True,
        "feature": feature,
        "title": "BYS360 kalite kapısı test verisi - yazma olmamalı",
        "message": "Yetki katmanı bu isteği veri yazmadan kesmelidir.",
        "progress": 1,
        "score": 1,
    }


def _call_client(client: Any, case: dict[str, str], headers: dict[str, str]) -> Any:
    method = case["method"].upper()
    path = case["path"]
    if method == "GET":
        return client.get(path, headers=headers)
    if method == "POST":
        return client.post(path, json=_payload_for(case), headers=headers)
    raise ValueError(f"Unsupported method: {method}")


def role_boundary_matrix(root: Path) -> dict[str, Any]:
    _ensure_testing_env()
    sys.path.insert(0, str(root))
    try:
        from app import create_app  # type: ignore

        app = create_app()
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        client = app.test_client()
        responses: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        scenarios = _boundary_scenarios()

        for case in ROLE_BOUNDARY_CASES:
            for scenario in scenarios:
                response = _call_client(client, case, scenario["headers"])
                status = int(getattr(response, "status_code", 0))
                no_route_break = status not in {404, 405}
                no_server_error = status < 500
                no_open_access = not (200 <= status < 300)
                status_expected = status in SAFE_EXPECTED_STATUSES or (300 <= status < 400)
                ok = no_route_break and no_server_error and no_open_access and status_expected
                item = {
                    "feature": case["feature"],
                    "method": case["method"],
                    "path": case["path"],
                    "scenario": scenario["name"],
                    "status_code": status,
                    "ok": ok,
                    "expected_statuses": sorted(SAFE_EXPECTED_STATUSES),
                }
                responses.append(item)
                if not ok:
                    failures.append(item)

        return {
            "ok": not failures,
            "mode": "flask_test_client_role_boundary_no_404_405_no_5xx_no_open_2xx",
            "case_count": len(ROLE_BOUNDARY_CASES),
            "scenario_count": len(scenarios),
            "probe_count": len(responses),
            "responses": responses,
            "failures": failures,
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "mode": "flask_test_client_role_boundary_no_404_405_no_5xx_no_open_2xx",
            "case_count": len(ROLE_BOUNDARY_CASES),
            "scenario_count": len(_boundary_scenarios()),
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
    result["mode"] = "pytest_targeted_mobile_role_boundary_matrix_p4b_v3"
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
    boundary = role_boundary_matrix(root)

    compile_targets = [
        root / "scripts" / "quality" / "bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
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
        "role_boundary_matrix_ok": bool(boundary.get("ok")),
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_smoke.get("ok")),
        "secret_gate_ok": bool(secret.get("ok")),
        "secret_gate_finding_count": int(secret.get("parsed", {}).get("finding_count", 0)) if secret.get("parsed") else 0,
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode", "unknown"),
        "inventory": inventory,
        "runtime_route_map": runtime,
        "role_boundary_matrix": boundary,
        "compile_results": compile_results,
        "app_factory_smoke": app_smoke,
        "secret_gate": secret,
        "pytest": pytest_result,
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P4B V3 temizse mobil API rol/header/token taklidi sinir matrisi dinamik route eslesmesiyle standart kalite kapisina alinmis kabul edilebilir.",
            "P4C'de fixture tabanli gercek test kullanicisi ile rol bazli pozitif/negatif senaryolar hazirlanabilir.",
        ],
    }
    result["ok"] = all(
        [
            result["direct_contract_ok"],
            result["runtime_route_map_ok"],
            result["role_boundary_matrix_ok"],
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
        "role_boundary_matrix_ok",
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
