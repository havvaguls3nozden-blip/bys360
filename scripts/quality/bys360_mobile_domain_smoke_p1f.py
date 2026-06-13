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

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P1F_MOBILE_DOMAIN_SMOKE_CONTRACT"
ROUTE_DECORATOR_RE = re.compile(r"^\s*@mobile_api_bp\.(route|get|post|put|patch|delete)\s*\(", re.M)
ROUTE_RULE_RE = re.compile(r"^\s*@mobile_api_bp\.(?:route|get|post|put|patch|delete)\s*\(([^\n]*)", re.M)
FUNC_RE = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.M)
EXPECTED_DOMAINS = [
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


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def line_count(path: Path) -> int:
    return len(read_text(path).splitlines()) if path.exists() else 0


def compile_file(path: Path) -> dict[str, Any]:
    try:
        py_compile.compile(str(path), doraise=True)
        return {"file": str(path), "ok": True, "error": ""}
    except Exception as exc:  # pragma: no cover
        return {"file": str(path), "ok": False, "error": str(exc)}


def route_count_in(path: Path) -> int:
    return len(ROUTE_DECORATOR_RE.findall(read_text(path))) if path.exists() else 0


def route_rules_in(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [re.sub(r"\s+", " ", m.group(0).strip()) for m in ROUTE_RULE_RE.finditer(read_text(path))]


def functions_in(path: Path) -> list[str]:
    if not path.exists():
        return []
    return FUNC_RE.findall(read_text(path))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception:
        return {}


def extract_json_from_stdout(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        pass
    # PowerShell/python may print logs before the final JSON. Find balanced final object conservatively.
    candidates: list[str] = []
    starts = [i for i, ch in enumerate(text) if ch == "{"]
    for start in starts:
        depth = 0
        in_str = False
        esc = False
        for idx in range(start, len(text)):
            ch = text[idx]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidates.append(text[start : idx + 1])
                        break
    for candidate in reversed(candidates):
        try:
            return json.loads(candidate)
        except Exception:
            continue
    return {}


def run_subprocess(root: Path, args: list[str], env_extra: dict[str, str] | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("APP_ENV", "development")
    env.setdefault("FLASK_ENV", "development")
    env.setdefault("BYS360_DEV_SECRET_FALLBACK", "dev-smoke-only-secret-not-for-production")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        args,
        cwd=str(root),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }


def app_factory_smoke(root: Path) -> dict[str, Any]:
    code = "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"
    result = run_subprocess(root, [sys.executable, "-c", code])
    result["ok"] = result["returncode"] == 0 and "APP_FACTORY_OK" in result.get("stdout_tail", "")
    return result


def secret_gate(root: Path) -> dict[str, Any]:
    gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": False, "missing": str(gate)}
    result = run_subprocess(root, [sys.executable, str(gate), "--root", str(root)])
    parsed = extract_json_from_stdout(result.get("stdout_tail", ""))
    result["parsed"] = parsed
    result["ok"] = result["returncode"] == 0 and parsed.get("ok") is True and int(parsed.get("finding_count", 999999)) == 0
    return result


def load_previous_contract_count(root: Path) -> int | None:
    candidates = [
        root / "reports" / "architecture" / "BYS360_MOBILE_ROUTES_PERSONNEL_KPI_SPLIT_P1E_REPORT.json",
        root / "reports" / "architecture" / "BYS360_MOBILE_ROUTES_COMM_ASSISTANT_SPLIT_P1D_REPORT.json",
        root / "reports" / "architecture" / "BYS360_MOBILE_ROUTES_DOMAIN_SPLIT_P1C_REPORT.json",
        root / "reports" / "architecture" / "BYS360_MOBILE_ROUTES_SHARED_SPLIT_P1B_REPORT.json",
    ]
    for path in candidates:
        data = read_json(path)
        after = data.get("after") if isinstance(data.get("after"), dict) else {}
        count = after.get("mobile_contract_route_count") or data.get("mobile_contract_route_count")
        try:
            if count is not None:
                return int(count)
        except Exception:
            continue
    return None


def build_inventory(root: Path) -> dict[str, Any]:
    mobile_dir = root / "app" / "api" / "mobile"
    routes = mobile_dir / "routes.py"
    domains_dir = mobile_dir / "domains"
    files = [routes] + [domains_dir / name for name in EXPECTED_DOMAINS]
    domain_inventory: list[dict[str, Any]] = []
    total_route_count = 0
    all_rules: list[str] = []
    all_functions: list[str] = []
    missing: list[str] = []
    for path in files:
        rel = str(path.relative_to(root)) if path.exists() else str(path.relative_to(root))
        if not path.exists():
            missing.append(rel)
            domain_inventory.append({"path": rel, "exists": False, "route_count": 0, "function_count": 0, "lines": 0})
            continue
        rc = route_count_in(path)
        funcs = functions_in(path)
        rules = route_rules_in(path)
        total_route_count += rc
        all_rules.extend([f"{rel}:{rule}" for rule in rules])
        all_functions.extend([f"{rel}:{name}" for name in funcs])
        domain_inventory.append({
            "path": rel,
            "exists": True,
            "route_count": rc,
            "function_count": len(funcs),
            "lines": line_count(path),
        })
    # Duplicate rules are suspicious; keep file prefix out for exact decorator comparison and use decorator text only.
    bare_rules: list[str] = []
    for item in all_rules:
        bare_rules.append(item.split(":", 1)[1] if ":" in item else item)
    duplicate_rules = sorted({rule for rule in bare_rules if bare_rules.count(rule) > 1})
    return {
        "routes_py_lines": line_count(routes),
        "routes_py_route_count": route_count_in(routes),
        "domains_dir_exists": domains_dir.exists(),
        "missing_files": missing,
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": total_route_count,
        "duplicate_route_decorators": duplicate_rules,
        "route_rules_sample": bare_rules[:40],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", default="all", choices=["audit", "all"])
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report_path = root / "reports" / "architecture" / "BYS360_MOBILE_DOMAIN_SMOKE_CONTRACT_P1F_REPORT.json"

    inv = build_inventory(root)
    compile_targets = [root / "app" / "api" / "mobile" / "routes.py"] + [root / "app" / "api" / "mobile" / "domains" / name for name in EXPECTED_DOMAINS]
    compile_results = [compile_file(p) for p in compile_targets if p.exists()]
    previous_count = load_previous_contract_count(root)
    expected_count = previous_count or EXPECTED_ROUTE_COUNT

    checks: dict[str, Any] = {
        "domain_dir_exists": inv["domains_dir_exists"],
        "expected_domain_files_exist": len(inv["missing_files"]) == 0,
        "routes_py_under_300_lines": int(inv["routes_py_lines"]) <= 300,
        "route_contract_count_expected": int(inv["total_mobile_route_decorator_count"]) == int(expected_count),
        "route_contract_unchanged_from_p1e": previous_count is not None and int(inv["total_mobile_route_decorator_count"]) == int(previous_count),
        "no_duplicate_route_decorators": len(inv["duplicate_route_decorators"]) == 0,
        "compile_ok": all(item.get("ok") for item in compile_results),
    }

    app_smoke: dict[str, Any] | None = None
    secret: dict[str, Any] | None = None
    if args.run_app_factory_smoke:
        app_smoke = app_factory_smoke(root)
        checks["app_factory_ok"] = app_smoke.get("ok") is True
    if args.run_secret_gate:
        secret = secret_gate(root)
        checks["secret_gate_ok"] = secret.get("ok") is True
        checks["secret_gate_finding_count_zero"] = int(secret.get("parsed", {}).get("finding_count", 999999)) == 0 if isinstance(secret.get("parsed"), dict) else False

    ok = all(bool(v) for v in checks.values())
    report = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": args.mode,
        "expected_contract_route_count": expected_count,
        "previous_contract_route_count": previous_count,
        "inventory": inv,
        "checks": checks,
        "compile_results": compile_results,
        "app_factory_smoke": app_smoke,
        "secret_gate": secret,
        "report": str(report_path),
        "next_actions": [
            "P1F kapısı temizse mobil API domain split zinciri tamam kabul edilebilir.",
            "Yeni mobil endpoint eklendiğinde routes.py yerine ilgili app/api/mobile/domains/*.py dosyasına eklenmelidir.",
            "P2 aşamasında auth/dashboard/personnel/kpi/communication/assistant için davranışsal mobil smoke testleri ve pytest kapısı genişletilmelidir.",
        ],
    }
    write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({
        "ok": ok,
        "package": PACKAGE,
        "routes_py_lines": inv["routes_py_lines"],
        "total_mobile_route_decorator_count": inv["total_mobile_route_decorator_count"],
        "expected_contract_route_count": expected_count,
        "compile_ok": checks["compile_ok"],
        "app_factory_ok": checks.get("app_factory_ok"),
        "secret_gate_ok": checks.get("secret_gate_ok"),
        "report": str(report_path),
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
