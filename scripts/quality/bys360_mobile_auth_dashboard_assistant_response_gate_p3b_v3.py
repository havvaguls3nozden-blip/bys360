from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P3B_MOBILE_AUTH_DASHBOARD_ASSISTANT_RESPONSE_GATE_V3"
REPORT_REL = Path("reports/architecture/BYS360_MOBILE_AUTH_DASHBOARD_ASSISTANT_RESPONSE_GATE_P3B_V3_REPORT.json")
EXPECTED_CONTRACT_ROUTE_COUNT = 24
EXPECTED_TARGET_ENDPOINTS = [
    {"feature": "auth", "method": "POST", "suffix": "/api/mobile/auth/login", "status_ok": [200, 400, 401, 403, 422, 500]},
    {"feature": "auth", "method": "POST", "suffix": "/api/mobile/auth/refresh", "status_ok": [200, 400, 401, 403, 422, 500]},
    {"feature": "dashboard", "method": "GET", "suffix": "/api/mobile/dashboard/summary", "status_ok": [200, 302, 401, 403, 500]},
    {"feature": "assistant", "method": "POST", "suffix": "/api/mobile/assistant/v2/ask", "status_ok": [200, 400, 401, 403, 422, 500]},
]
DOMAIN_EXPECTATIONS = {
    "auth": ["/auth/login", "/auth/refresh"],
    "dashboard": ["/dashboard/summary"],
    "assistant": ["/assistant/v2/ask"],
}
EXPECTED_DOMAIN_FILES = [
    "app/api/mobile/domains/auth.py",
    "app/api/mobile/domains/dashboard.py",
    "app/api/mobile/domains/assistant_chat.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return len(read_text(path).splitlines())


def route_decorators(text: str) -> list[dict[str, str]]:
    # Matches @mobile_api_bp.get("/x"), @mobile_api_bp.post('/x'), @mobile_api_bp.route('/x', methods=[...])
    rows: list[dict[str, str]] = []
    pat = re.compile(r"@mobile_api_bp\.(get|post|put|patch|delete)\(\s*([\'\"])(.*?)\2", re.I)
    for method, _quote, rule in pat.findall(text):
        rows.append({"method": method.upper(), "rule": rule})
    route_pat = re.compile(r"@mobile_api_bp\.route\(\s*([\'\"])(.*?)\1\s*,\s*methods\s*=\s*\[(.*?)\]", re.I | re.S)
    for _quote, rule, methods_blob in route_pat.findall(text):
        methods = re.findall(r"[\'\"]([A-Z]+)[\'\"]", methods_blob.upper()) or ["GET"]
        for method in methods:
            rows.append({"method": method.upper(), "rule": rule})
    return rows


def inventory(root: Path) -> dict[str, Any]:
    routes_py = root / "app/api/mobile/routes.py"
    domains_dir = root / "app/api/mobile/domains"
    files = [routes_py]
    if domains_dir.exists():
        files.extend(sorted(domains_dir.glob("*.py")))
    domain_inventory = []
    all_routes: list[dict[str, str]] = []
    for file in files:
        text = read_text(file)
        routes = route_decorators(text)
        rel = file.relative_to(root).as_posix() if file.exists() else str(file)
        domain_inventory.append({
            "path": rel,
            "exists": file.exists(),
            "route_count": len(routes),
            "lines": count_lines(file),
        })
        for row in routes:
            row = dict(row)
            row["source"] = rel
            all_routes.append(row)
    duplicate_keys = sorted({(r["method"], r["rule"]) for r in all_routes if sum(1 for x in all_routes if x["method"] == r["method"] and x["rule"] == r["rule"]) > 1})
    expected_missing: list[str] = []
    wrong_domain_owner: list[dict[str, str]] = []
    for feature, fragments in DOMAIN_EXPECTATIONS.items():
        for frag in fragments:
            matches = [r for r in all_routes if r["rule"].endswith(frag)]
            if not matches:
                expected_missing.append(f"{feature}:{frag}")
            else:
                for m in matches:
                    if feature == "assistant" and not m["source"].endswith("assistant_chat.py"):
                        wrong_domain_owner.append({"feature": feature, "rule": m["rule"], "source": m["source"]})
                    if feature == "dashboard" and not m["source"].endswith("dashboard.py"):
                        wrong_domain_owner.append({"feature": feature, "rule": m["rule"], "source": m["source"]})
                    if feature == "auth" and not m["source"].endswith("auth.py"):
                        wrong_domain_owner.append({"feature": feature, "rule": m["rule"], "source": m["source"]})
    return {
        "routes_py_lines": count_lines(routes_py),
        "routes_py_route_count": len(route_decorators(read_text(routes_py))),
        "domains_dir_exists": domains_dir.exists(),
        "missing_files": [p for p in EXPECTED_DOMAIN_FILES if not (root / p).exists()],
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": len(all_routes),
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "duplicate_route_decorators": [f"{m} {r}" for m, r in duplicate_keys],
        "expected_missing_routes": expected_missing,
        "wrong_domain_owner_routes": wrong_domain_owner,
        "route_rules_sample": [f"{r['method']} {r['rule']}" for r in all_routes[:40]],
    }


def ensure_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("FLASK_ENV", "testing")
    env.setdefault("APP_ENV", "testing")
    env.setdefault("SECRET_KEY", "test-secret-key-for-smoke-only")
    env.setdefault("BYS360_DEV_SECRET_FALLBACK", "test-secret-key-for-smoke-only")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("SENTRY_DSN", "")
    env.setdefault("AI_PROVIDER_MODE", "stub")
    env.setdefault("WTF_CSRF_ENABLED", "0")
    return env


def build_app_and_runtime_routes(root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root))
    old_env = os.environ.copy()
    os.environ.update(ensure_env())
    try:
        from app import create_app  # type: ignore
        app = create_app()
        rows = []
        for rule in app.url_map.iter_rules():
            methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
            rows.append({"rule": str(rule.rule), "methods": methods, "endpoint": rule.endpoint})
        return {"ok": True, "app": app, "routes": rows, "error": ""}
    except Exception as exc:  # noqa: BLE001 - diagnostic gate
        return {"ok": False, "app": None, "routes": [], "error": repr(exc)}
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        try:
            sys.path.remove(str(root))
        except ValueError:
            pass


def runtime_route_map_check(root: Path) -> dict[str, Any]:
    built = build_app_and_runtime_routes(root)
    rows = built.get("routes") or []
    missing: list[str] = []
    method_mismatches: list[dict[str, Any]] = []
    for exp in EXPECTED_TARGET_ENDPOINTS:
        suffix = exp["suffix"]
        method = exp["method"]
        matches = [r for r in rows if str(r["rule"]).endswith(suffix)]
        if not matches:
            missing.append(suffix)
            continue
        if not any(method in r.get("methods", []) for r in matches):
            method_mismatches.append({"suffix": suffix, "method": method, "matches": matches})
    return {
        "ok": bool(built.get("ok")) and not missing and not method_mismatches,
        "app_build_ok": bool(built.get("ok")),
        "runtime_route_count": len(rows),
        "missing_runtime_suffixes": missing,
        "runtime_method_mismatches": method_mismatches,
        "sample_mobile_routes": [r for r in rows if str(r["rule"]).startswith("/api/mobile")][:50],
        "error": built.get("error", ""),
    }


def response_code_smoke(root: Path) -> dict[str, Any]:
    built = build_app_and_runtime_routes(root)
    app = built.get("app")
    if not built.get("ok") or app is None:
        return {"ok": False, "mode": "app_build_failed", "responses": [], "error": built.get("error", "")}
    responses = []
    ok = True
    with app.test_client() as client:
        for exp in EXPECTED_TARGET_ENDPOINTS:
            suffix = exp["suffix"]
            method = exp["method"].lower()
            payload = {}
            if suffix.endswith("/auth/login"):
                payload = {"sicil_no": "__smoke__", "password": "__smoke__"}
            elif suffix.endswith("/auth/refresh"):
                payload = {"refresh_token": "__smoke__"}
            elif suffix.endswith("/assistant/v2/ask"):
                payload = {"message": "smoke"}
            try:
                if method == "get":
                    resp = client.get(suffix)
                else:
                    resp = getattr(client, method)(suffix, json=payload)
                status = int(resp.status_code)
                row_ok = status not in {404, 405}
                ok = ok and row_ok
                responses.append({"method": exp["method"], "path": suffix, "status_code": status, "ok": row_ok})
            except Exception as exc:  # noqa: BLE001 - diagnostics only
                ok = False
                responses.append({"method": exp["method"], "path": suffix, "status_code": None, "ok": False, "error": repr(exc)})
    return {"ok": ok, "mode": "flask_test_client_response_codes", "responses": responses, "error": ""}


def run_cmd(cmd: list[str], root: Path, env: dict[str, str] | None = None, timeout: int = 120) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(root), env=env or ensure_env(), capture_output=True, text=True, timeout=timeout)
    return {"returncode": proc.returncode, "stdout_tail": proc.stdout[-4000:], "stderr_tail": proc.stderr[-4000:], "ok": proc.returncode == 0, "cmd": cmd}


def compile_files(root: Path) -> tuple[bool, list[dict[str, Any]]]:
    rels = [
        "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
        "tests/architecture/test_mobile_api_auth_dashboard_assistant_response_p3b_v3.py",
        "tests/architecture/conftest.py",
    ]
    results = []
    ok = True
    for rel in rels:
        path = root / rel
        if not path.exists():
            results.append({"file": str(path), "ok": False, "error": "missing"})
            ok = False
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"file": str(path), "ok": True, "error": ""})
        except Exception as exc:  # noqa: BLE001
            results.append({"file": str(path), "ok": False, "error": repr(exc)})
            ok = False
    return ok, results


def app_factory_smoke(root: Path) -> dict[str, Any]:
    return run_cmd([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root)


def secret_gate(root: Path) -> dict[str, Any]:
    gate = root / "scripts/quality/bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": False, "returncode": 127, "stdout_tail": "", "stderr_tail": "secret gate missing", "parsed": {}}
    res = run_cmd([sys.executable, str(gate), "--root", str(root)], root, timeout=180)
    parsed = {}
    try:
        start = res["stdout_tail"].find("{")
        end = res["stdout_tail"].rfind("}")
        if start >= 0 and end >= start:
            parsed = json.loads(res["stdout_tail"][start:end+1])
    except Exception:
        parsed = {}
    res["parsed"] = parsed
    res["ok"] = res["returncode"] == 0 and bool(parsed.get("ok", res["returncode"] == 0)) and int(parsed.get("finding_count", 0) or 0) == 0
    return res


def pytest_gate(root: Path, run_pytest: bool) -> dict[str, Any]:
    if not run_pytest:
        return {"ok": True, "mode": "skipped", "returncode": 0, "stdout_tail": "", "stderr_tail": ""}
    test = "tests/architecture/test_mobile_api_auth_dashboard_assistant_response_p3b_v3.py"
    res = run_cmd([sys.executable, "-m", "pytest", test, "-q"], root, timeout=180)
    res["mode"] = "pytest_targeted_auth_dashboard_assistant_response_v3"
    return res


def run_checks(root: str | Path, *, compile_all: bool = True, app_factory: bool = True, secret_gate_enabled: bool = True, pytest_gate_enabled: bool = True, write_report: bool = True) -> dict[str, Any]:
    root = Path(root).resolve()
    inv = inventory(root)
    direct_contract_ok = (
        inv["routes_py_lines"] <= 300
        and inv["routes_py_route_count"] == 0
        and inv["domains_dir_exists"]
        and not inv["missing_files"]
        and inv["total_mobile_route_decorator_count"] == EXPECTED_CONTRACT_ROUTE_COUNT
        and not inv["duplicate_route_decorators"]
        and not inv["expected_missing_routes"]
        and not inv["wrong_domain_owner_routes"]
    )
    runtime = runtime_route_map_check(root)
    response = response_code_smoke(root)
    compile_ok, compile_results = compile_files(root) if compile_all else (True, [])
    app_res = app_factory_smoke(root) if app_factory else {"ok": True, "returncode": 0, "stdout_tail": "", "stderr_tail": ""}
    secret_res = secret_gate(root) if secret_gate_enabled else {"ok": True, "returncode": 0, "stdout_tail": "", "stderr_tail": "", "parsed": {"finding_count": 0}}
    pytest_res = pytest_gate(root, pytest_gate_enabled)

    result: dict[str, Any] = {
        "ok": False,
        "package": PACKAGE,
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "routes_py_lines": inv["routes_py_lines"],
        "total_mobile_route_decorator_count": inv["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "direct_contract_ok": direct_contract_ok,
        "runtime_route_map_ok": bool(runtime["ok"]),
        "response_code_smoke_ok": bool(response["ok"]),
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_res.get("ok")),
        "secret_gate_ok": bool(secret_res.get("ok")),
        "secret_gate_finding_count": int((secret_res.get("parsed") or {}).get("finding_count", 0) or 0),
        "pytest_ok": bool(pytest_res.get("ok")),
        "pytest_mode": pytest_res.get("mode", "unknown"),
        "inventory": inv,
        "runtime_route_map": runtime,
        "response_code_smoke": response,
        "compile_results": compile_results,
        "app_factory_smoke": app_res,
        "secret_gate": secret_res,
        "pytest": pytest_res,
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P3B V3 temizse auth/dashboard/asistan mobil response-code smoke kapisi runtime route haritasiyla birlikte kurulmus kabul edilebilir.",
            "P3C'de personel/KPI/iletisim endpointleri icin benzer response-code smoke kapisi genisletilebilir.",
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest-gate", action="store_true")
    args = parser.parse_args()
    result = run_checks(
        args.root,
        compile_all=args.compile_all,
        app_factory=args.app_factory,
        secret_gate_enabled=args.secret_gate,
        pytest_gate_enabled=args.pytest_gate,
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
