from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import ast
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
ARCH = ROOT / "reports" / "architecture"

OUT_JSON = ARCH / "BYS360_PHASE2C4_FACADE_EXCEPTION_CLOSURE_EVIDENCE.json"
OUT_MD = ARCH / "BYS360_PHASE2C4_FACADE_EXCEPTION_CLOSURE_EVIDENCE.md"

ROUTES = "app/api/mobile/routes.py"


def run_cmd(cmd, timeout=1800):
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
        },
        timeout=timeout,
    )
    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": proc.returncode,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-30000:],
    }


def parse_pytest_summary(text: str) -> dict:
    summary = {}
    pattern = r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warning|warnings)\b"

    for num, key in re.findall(pattern, text or "", flags=re.IGNORECASE):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    for key in ["failed", "passed", "errors", "skipped", "deselected", "warnings"]:
        summary.setdefault(key, 0)

    return summary


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig", errors="ignore")


def has_mobile_shared_wildcard(rel: str) -> bool:
    return bool(re.search(
        r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$",
        read_text(rel),
        flags=re.MULTILINE,
    ))


def has_mobile_shared_explicit(rel: str) -> bool:
    return bool(re.search(
        r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+(?!\*)",
        read_text(rel),
        flags=re.MULTILINE,
    ))


def app_wildcards() -> list[dict]:
    rows = []

    for path in sorted((ROOT / "app").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig", errors="ignore"), filename=str(path))
        except Exception as exc:
            rows.append({
                "file": rel,
                "line_no": None,
                "module": None,
                "error": str(exc),
            })
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
                rows.append({
                    "file": rel,
                    "line_no": node.lineno,
                    "module": node.module,
                    "level": node.level,
                })

    return rows


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)

    wildcard_rows = app_wildcards()
    by_module = Counter(str(row.get("module")) for row in wildcard_rows)

    mobile_shared_remaining = [
        row for row in wildcard_rows
        if row.get("module") == "app.api.mobile.shared"
    ]

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    compile_result = run_cmd([
        str(py), "-m", "compileall", "-q",
        "config.py", "app", "scripts", "tests", "migrations",
    ], timeout=900)

    contract = run_cmd([
        str(py), "-m", "pytest",
        "tests/architecture/test_phase2b_route_snapshot_contract.py",
        "-q", "-ra",
    ], timeout=900)

    auth_guard = run_cmd([
        str(py), "-m", "pytest",
        "tests/architecture/test_mobile_api_auth_guard_matrix_p4a.py",
        "-q", "-ra",
    ], timeout=900)

    default = run_cmd([
        str(py), "-m", "pytest",
        "-m", "not live and not realdb and not slow",
        "-q", "-ra",
    ], timeout=1800)

    phase2c1 = run_cmd([
        str(py),
        "scripts/quality/bys360_phase2c1_wildcard_import_explicit_plan.py",
    ], timeout=1800)

    contract_summary = parse_pytest_summary(contract["combined_tail"])
    auth_guard_summary = parse_pytest_summary(auth_guard["combined_tail"])
    default_summary = parse_pytest_summary(default["combined_tail"])

    tests_green = (
        compile_result["returncode"] == 0
        and contract["returncode"] == 0
        and auth_guard["returncode"] == 0
        and default["returncode"] == 0
        and contract_summary.get("failed", 0) == 0
        and contract_summary.get("errors", 0) == 0
        and auth_guard_summary.get("failed", 0) == 0
        and auth_guard_summary.get("errors", 0) == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and default_summary.get("passed", 0) >= 700
    )

    routes_exception_ok = (
        has_mobile_shared_wildcard(ROUTES)
        and not has_mobile_shared_explicit(ROUTES)
        and len(mobile_shared_remaining) == 1
        and mobile_shared_remaining[0]["file"] == ROUTES
    )

    ok = routes_exception_ok and tests_green

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C4_FACADE_EXCEPTION_CLOSURE_EVIDENCE",
        "mode": "verify_only_no_code_change",
        "ok": ok,
        "decision": "PHASE2C4_CLOSED_ROUTES_FACADE_WILDCARD_INTENTIONAL_EXCEPTION" if ok else "PHASE2C4_REVIEW_REQUIRED",
        "routes_file": ROUTES,
        "routes_has_mobile_shared_wildcard": has_mobile_shared_wildcard(ROUTES),
        "routes_has_mobile_shared_explicit": has_mobile_shared_explicit(ROUTES),
        "routes_exception_reason": "routes.py mobil facade/aggregator rolünde olduğu için app.api.mobile.shared wildcard import C4 sonunda bilinçli istisna olarak bırakıldı.",
        "app_ast_wildcard_count": len(wildcard_rows),
        "app_ast_wildcard_by_module_top_50": dict(by_module.most_common(50)),
        "mobile_shared_remaining": mobile_shared_remaining,
        "mobile_shared_remaining_count": len(mobile_shared_remaining),
        "compileall_returncode": compile_result["returncode"],
        "contract_pytest_returncode": contract["returncode"],
        "contract_pytest_summary": contract_summary,
        "auth_guard_pytest_returncode": auth_guard["returncode"],
        "auth_guard_pytest_summary": auth_guard_summary,
        "default_pytest_returncode": default["returncode"],
        "default_pytest_summary": default_summary,
        "phase2c1_rerun_returncode": phase2c1["returncode"],
        "phase2c1_tail": phase2c1["combined_tail"][-8000:],
        "tests_green": tests_green,
        "next_action": "Faz 2C5: mobil shared dışındaki sıradaki düşük riskli wildcard import paketi seçilebilir." if ok else "routes.py ve test kapıları incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C4 Facade Exception Closure Evidence",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Routes file: `{result['routes_file']}`",
        f"- Routes has mobile shared wildcard: {result['routes_has_mobile_shared_wildcard']}",
        f"- Routes has mobile shared explicit: {result['routes_has_mobile_shared_explicit']}",
        f"- App AST wildcard count: {result['app_ast_wildcard_count']}",
        f"- Mobile shared remaining count: {result['mobile_shared_remaining_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Contract pytest returncode: {result['contract_pytest_returncode']}",
        f"- Auth guard pytest returncode: {result['auth_guard_pytest_returncode']}",
        f"- Default pytest returncode: {result['default_pytest_returncode']}",
        f"- Tests green: {result['tests_green']}",
        "",
        "## İstisna Gerekçesi",
        "",
        result["routes_exception_reason"],
        "",
        "## Mobile Shared Remaining",
        "",
        "```json",
        json.dumps(mobile_shared_remaining, ensure_ascii=False, indent=2),
        "```",
        "",
        "## App Wildcard By Module Top 50",
        "",
        "```json",
        json.dumps(result["app_ast_wildcard_by_module_top_50"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Default Pytest Summary",
        "",
        "```json",
        json.dumps(default_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("PHASE2C4E_REPORT_JSON:", OUT_JSON)
    print("PHASE2C4E_REPORT_MD:", OUT_MD)
    print("PHASE2C4E_ROUTES_HAS_SHARED_WILDCARD:", result["routes_has_mobile_shared_wildcard"])
    print("PHASE2C4E_ROUTES_HAS_SHARED_EXPLICIT:", result["routes_has_mobile_shared_explicit"])
    print("PHASE2C4E_APP_AST_WILDCARD_COUNT:", result["app_ast_wildcard_count"])
    print("PHASE2C4E_MOBILE_SHARED_REMAINING_COUNT:", result["mobile_shared_remaining_count"])
    print("PHASE2C4E_CONTRACT_RETURN_CODE:", result["contract_pytest_returncode"])
    print("PHASE2C4E_AUTH_GUARD_RETURN_CODE:", result["auth_guard_pytest_returncode"])
    print("PHASE2C4E_DEFAULT_RETURN_CODE:", result["default_pytest_returncode"])
    print("PHASE2C4E_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("PHASE2C4E_TESTS_GREEN:", result["tests_green"])
    print("PHASE2C4E_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
